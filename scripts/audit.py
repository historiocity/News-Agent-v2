#!/usr/bin/env python3
"""
News Bot 2.0 pre-publish audit.
Parses the generated HTML and optional process log.
Exits 0 only if all hard gates pass.
Soft warnings do not fail the run.
"""

import sys
import re
import json
from pathlib import Path
from html.parser import HTMLParser
from html import unescape
from collections import defaultdict

PRIMARY_DOMAINS = {
    "whitehouse.gov", "congress.gov", "supremecourt.gov", "sec.gov", "bls.gov",
    "eia.gov", "treasury.gov", "census.gov", "federalregister.gov", "govinfo.gov",
    "cbo.gov", "gao.gov", "federalreserve.gov", "justice.gov", "state.gov",
    "defense.gov", "energy.gov", "epa.gov", "fda.gov", "cdc.gov",
    "house.gov", "senate.gov", "centcom.mil", "iaea.org",
}

WIRE_DOMAINS = {"reuters.com", "apnews.com", "bloomberg.com"}

STOCK_OPTION_PHRASES = {
    "keep it at this level",
    "drop it",
    "no opinion",
    "the mix is right",
    "stop following",
    "not interested",
    "keep following",
    "follow it",
    "yes",
    "no",
}


def normalize_option(text: str) -> str:
    """Lowercase, collapse punctuation/whitespace for stock/uniqueness checks."""
    t = unescape(text or "").lower()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


class StoryExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stories = []
        self.current = None
        self.capture = []
        self.in_h3 = False
        self.in_h2 = False
        self.tier = "lead"
        # Radio / feedback capture
        self.in_fb = False
        self.in_label = False
        self.in_p = False
        self.label_buf = []
        self.p_buf = []
        self.pending_radio_name = None
        self.fb_questions = []  # questions seen in current fb block
        self.radio_groups = {}  # name -> {options: [...], questions: [...], story_title, tier, also_tier_block}
        self.also_tier_block = False
        self._saw_also_below_line = False

    def _ensure_group(self, name):
        if name not in self.radio_groups:
            self.radio_groups[name] = {
                "options": [],
                "questions": [],
                "story_title": (self.current or {}).get("title", "") if self.current else "",
                "tier": self.tier,
                "also_tier_block": False,
            }
        return self.radio_groups[name]

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h3":
            if self.current:
                self._finish_story()
            self.current = {
                "title": "",
                "html": "",
                "links": [],
                "marker": None,
                "is_continuation": False,
                "divergence": False,
                "radio_names": set(),
                "radio_options": {},  # name -> [option texts]
                "fb_has_question": False,
                "tier": self.tier,
            }
            self.in_h3 = True
            self.capture = []
        if tag == "h2":
            self.in_h2 = True
        if tag == "div" and "fb" in (attrs.get("class") or "").split():
            self.in_fb = True
            self.fb_questions = []
            self.also_tier_block = attrs.get("id") == "also-tier-fb"
        if tag == "a" and "href" in attrs and self.current is not None:
            href = attrs["href"]
            domain = self._domain(href)
            if domain:
                self.current["links"].append(domain)
        if tag == "input" and attrs.get("type") == "radio":
            name = attrs.get("name", "")
            if name:
                if self.current is not None:
                    self.current["radio_names"].add(name)
                self.pending_radio_name = name
                self._ensure_group(name)
                if self.also_tier_block or self._saw_also_below_line:
                    self.radio_groups[name]["also_tier_block"] = True
        if tag == "label":
            self.in_label = True
            self.label_buf = []
        if tag == "p" and self.in_fb:
            self.in_p = True
            self.p_buf = []

    def handle_data(self, data):
        if self.in_h2 and "also today" in data.lower():
            self.tier = "also"
        if self.in_h3 and data.strip():
            self.capture.append(data.strip())
        if self.in_p and data:
            self.p_buf.append(data)
        if self.in_label and data:
            self.label_buf.append(data)
        if "on the items below the line" in data.lower():
            self._saw_also_below_line = True
            self.also_tier_block = True
        if self.current is not None:
            text = data.strip()
            if text:
                self.current["html"] += " " + text
                if "continuation" in text.lower() or "continuing" in text.lower():
                    self.current["is_continuation"] = True
                for marker in ["Primary source", "Independent corroboration", "Single-sourced", "Unconfirmed"]:
                    if marker in text:
                        self.current["marker"] = marker
                if "divergence" in text.lower() or "dispute" in text.lower():
                    self.current["divergence"] = True

    def handle_endtag(self, tag):
        if tag == "h2":
            self.in_h2 = False
        if tag == "h3":
            self.in_h3 = False
            if self.current is not None:
                self.current["title"] = " ".join(self.capture).strip()
                self.capture = []
        if tag == "p" and self.in_p:
            self.in_p = False
            ptext = unescape("".join(self.p_buf)).strip()
            self.p_buf = []
            # Strip surrounding bold markers for question check
            plain = re.sub(r"\s+", " ", ptext).strip()
            if plain.endswith("?"):
                self.fb_questions.append(plain)
                if self.current is not None:
                    self.current["fb_has_question"] = True
                # Attach to any radio groups opened in this fb that we know about later;
                # also stash on pending for groups that appear after the question.
                for g in self.radio_groups.values():
                    if not g["questions"] and (
                        (self.current and g["story_title"] == self.current.get("title", ""))
                        or g.get("also_tier_block")
                        or self.also_tier_block
                    ):
                        # Prefer attaching only when we finish the fb; keep for now
                        pass
                self._last_fb_question = plain
        if tag == "label" and self.in_label:
            self.in_label = False
            label_text = unescape("".join(self.label_buf)).strip()
            self.label_buf = []
            # Option text is the label content (radio itself contributes no text)
            if self.pending_radio_name and label_text:
                name = self.pending_radio_name
                g = self._ensure_group(name)
                g["options"].append(label_text)
                if self.current is not None:
                    self.current["radio_options"].setdefault(name, []).append(label_text)
                    if not g["story_title"]:
                        g["story_title"] = self.current.get("title", "")
                if getattr(self, "_last_fb_question", None) and not g["questions"]:
                    g["questions"].append(self._last_fb_question)
                if self.also_tier_block or self._saw_also_below_line:
                    g["also_tier_block"] = True
                self.pending_radio_name = None
        if tag == "div" and self.in_fb:
            # End of fb block: attach questions to groups that appeared in this block
            qlist = list(self.fb_questions)
            if qlist:
                # Groups whose options were just filled and still lack questions
                for name, g in self.radio_groups.items():
                    if not g["questions"]:
                        # Heuristic: if this group belongs to current story or also-tier
                        if self.also_tier_block or g.get("also_tier_block"):
                            g["questions"].extend(qlist)
                        elif self.current and (
                            name in self.current.get("radio_names", set())
                            or g["story_title"] == self.current.get("title", "")
                        ):
                            g["questions"].extend(qlist)
            self.in_fb = False
            self.fb_questions = []
            self.also_tier_block = False
            self._last_fb_question = None

    def _finish_story(self):
        if self.current:
            self.stories.append(self.current)
            self.current = None

    def _domain(self, href):
        m = re.search(r"https?://(?:www\.)?([^/]+)", href)
        return m.group(1).lower() if m else None

    def close(self):
        self._finish_story()
        super().close()


def _is_primary_domain(domain):
    if domain in PRIMARY_DOMAINS:
        return True
    # Subdomains of primary roots (e.g. chinaselectcommittee.house.gov)
    for root in PRIMARY_DOMAINS:
        if domain.endswith("." + root):
            return True
    return False

def check_marker_vs_links(story):
    marker = story.get("marker")
    domains = set(story.get("links", []))
    if not marker:
        return "missing confidence marker"
    primary_hits = {d for d in domains if _is_primary_domain(d)}
    newsroom_hits = {d for d in domains if d not in WIRE_DOMAINS and not _is_primary_domain(d)}
    if marker == "Primary source" and not primary_hits:
        return "Primary source claimed but no primary-domain link"
    if marker == "Independent corroboration" and len(newsroom_hits) < 2:
        return "Independent corroboration claimed but fewer than 2 distinct newsroom domains"
    if marker == "Single-sourced" and len(domains) == 0:
        return "Single-sourced claimed but no links"
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: audit.py <path-to-html> [path-to-process-log.json]")
        sys.exit(2)

    html_path = Path(sys.argv[1])
    if not html_path.exists():
        print(f"FAIL: HTML not found: {html_path}")
        sys.exit(1)

    html = html_path.read_text(encoding="utf-8", errors="ignore")
    parser = StoryExtractor()
    parser.feed(html)
    parser.close()
    stories = parser.stories
    radio_groups = parser.radio_groups

    failures = []
    warnings = []

    # Continuation cap
    continuations = [s for s in stories if s.get("is_continuation")]
    if len(continuations) > 4:
        failures.append(f"Continuation cap exceeded: {len(continuations)} > 4")

    # Marker vs links
    for s in stories:
        err = check_marker_vs_links(s)
        if err:
            failures.append(f"Story '{s.get('title','')[:60]}': {err}")

    # Per-lead radio buttons (hard gate) — max 1 group per story; leads need ≥1
    leads_missing_radios = []
    too_many_radios = []
    for s in stories:
        radio_count = len(s.get("radio_names", set()))
        title = s.get("title", "")[:50]
        if radio_count > 1:
            too_many_radios.append(f"{title} ({radio_count})")
        if s.get("tier") == "lead" and s.get("marker") and len(s.get("html", "")) > 200:
            if radio_count < 1:
                leads_missing_radios.append(title)
    if leads_missing_radios:
        failures.append(
            f"Lead feedback question missing on {len(leads_missing_radios)} lead(s): "
            + "; ".join(leads_missing_radios)
        )
    if too_many_radios:
        failures.append(
            f"More than one feedback question on {len(too_many_radios)} story(ies) (max 1): "
            + "; ".join(too_many_radios)
        )

    # --- NEW radio quality gates ---
    # (1) Stock option phrases
    stock_hits = []
    for name, g in radio_groups.items():
        for opt in g["options"]:
            norm = normalize_option(opt)
            if norm in STOCK_OPTION_PHRASES:
                stock_hits.append(f"{name}: '{opt.strip()}'")
    if stock_hits:
        failures.append(
            "Stock feedback option text banned ("
            + str(len(stock_hits))
            + "): "
            + "; ".join(stock_hits[:12])
            + ("…" if len(stock_hits) > 12 else "")
        )

    # (2) Same normalized option text in more than one story/group
    # Include the single 'On the items below the line' block.
    norm_to_groups = defaultdict(list)
    for name, g in radio_groups.items():
        seen_in_group = set()
        for opt in g["options"]:
            norm = normalize_option(opt)
            if not norm or norm in seen_in_group:
                continue
            seen_in_group.add(norm)
            label = name
            if g.get("also_tier_block"):
                label = f"{name}[also-tier]"
            elif g.get("story_title"):
                label = f"{name}[{g['story_title'][:40]}]"
            norm_to_groups[norm].append(label)
    reused = {n: gs for n, gs in norm_to_groups.items() if len(gs) > 1}
    if reused:
        parts = []
        for n, gs in sorted(reused.items(), key=lambda x: -len(x[1]))[:8]:
            parts.append(f"'{n}' in {len(gs)} groups ({', '.join(gs[:4])})")
        failures.append(
            "Reused feedback option text across stories/groups: " + "; ".join(parts)
        )

    # (3) Each radio group must have 2–3 options
    bad_counts = []
    for name, g in radio_groups.items():
        n = len(g["options"])
        if n < 2 or n > 3:
            bad_counts.append(f"{name} has {n} option(s)")
    if bad_counts:
        failures.append(
            "Radio group must have 2–3 options: " + "; ".join(bad_counts)
        )

    # (4) Lead fb blocks need a question ending with '?'
    leads_missing_q = []
    for s in stories:
        if s.get("tier") != "lead":
            continue
        if not (s.get("marker") and len(s.get("html", "")) > 200):
            continue
        if not s.get("radio_names"):
            continue  # already caught by missing-radios
        # Check via radio_groups for this story's names
        has_q = s.get("fb_has_question")
        if not has_q:
            # Also check groups
            for name in s.get("radio_names", set()):
                g = radio_groups.get(name)
                if g and g.get("questions"):
                    has_q = True
                    break
        if not has_q:
            leads_missing_q.append(s.get("title", "")[:50])
    if leads_missing_q:
        failures.append(
            "Lead feedback block missing a question ending with '?': "
            + "; ".join(leads_missing_q)
        )

    # Source count target (~40). Hard fail only if extremely low and no underreported judgment noted.
    sources_total = None
    underreported_judgment = False
    if len(sys.argv) > 2:
        log_path = Path(sys.argv[2])
        if log_path.exists():
            try:
                log = json.loads(log_path.read_text())
                sources_total = log.get("sources_checked_total")
                neg = log.get("negative_check", {})
                if isinstance(neg, dict) and "underreported" in str(neg).lower():
                    underreported_judgment = True
                required = ["outside_watchlist_first", "broad_sweeps", "negative_check", "beat_coverage"]
                for r in required:
                    if r not in log:
                        failures.append(f"Process log missing field: {r}")
            except Exception as e:
                failures.append(f"Process log unreadable: {e}")
        else:
            warnings.append("No process log supplied")
    else:
        warnings.append("No process log supplied")

    if sources_total is None:
        m = re.search(r"(\d+)\s+sources checked", html, re.I)
        if m:
            sources_total = int(m.group(1))

    if sources_total is not None:
        if sources_total < 15 and not underreported_judgment:
            failures.append(
                f"Source count {sources_total} is far below target (~40) and no underreported-judgment note found. "
                "Gather more or explicitly record why significant thin stories were still included."
            )
        elif sources_total < 30:
            warnings.append(
                f"Source count {sources_total} is below the ~40 target. Acceptable only if further sources could not be found "
                "or thin coverage was judged underreported-but-significant."
            )
    else:
        warnings.append("Could not determine total sources checked")

    # Divergence (still warning)
    if "divergence" in html.lower():
        if not all(k in html.lower() for k in ["dispute", "vantage", "means for"]):
            warnings.append("Divergence language present but three-part structure not clearly detected")

    # Layout
    for section in ["Also today", "Also noted"]:
        if section.lower() not in html.lower():
            warnings.append(f"Section '{section}' not found (may be optional)")

    print(f"Stories parsed: {len(stories)}")
    print(f"Continuations: {len(continuations)}")
    print(f"Radio groups: {len(radio_groups)}")
    print(f"Sources checked: {sources_total}")
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  - {w}")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print("All hard gates passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
