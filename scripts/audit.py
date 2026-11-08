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
        self.pending_article_id = None
        self.all_element_ids = set()
        self.summary_text = None
        self.in_summary = False
        self.summary_buf = []
        self.nav_html_parts = []
        self.in_nav = False
        self.nav_depth = 0
        self.saw_in_this_issue = False
        self.nav_links = []  # list of {href, text}
        self.in_nav_a = False
        self.nav_a_href = None
        self.nav_a_buf = []
        self.in_nav_heading = False
        self.nav_heading_buf = []
        self.first_story_started = False

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
        if "id" in attrs:
            self.all_element_ids.add(attrs["id"])
        if tag == "article":
            self.pending_article_id = attrs.get("id")
        if tag == "p" and "summary" in (attrs.get("class") or "").split():
            self.in_summary = True
            self.summary_buf = []
        if tag == "nav" and not self.first_story_started:
            self.in_nav = True
            self.nav_depth = 1
        elif self.in_nav:
            if tag == "nav":
                self.nav_depth += 1
        if self.in_nav and tag in ("h2", "h3", "strong", "b") and not self.saw_in_this_issue:
            self.in_nav_heading = True
            self.nav_heading_buf = []
        if self.in_nav and tag == "a":
            self.in_nav_a = True
            self.nav_a_href = attrs.get("href", "")
            self.nav_a_buf = []
        if tag == "h3":
            self.first_story_started = True
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
                "id": self.pending_article_id,
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
        if self.in_summary and data:
            self.summary_buf.append(data)
        if self.in_nav_heading and data:
            self.nav_heading_buf.append(data)
        if self.in_nav_a and data:
            self.nav_a_buf.append(data)
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
        if tag == "p" and self.in_summary:
            self.in_summary = False
            self.summary_text = unescape(re.sub(r"\s+", " ", "".join(self.summary_buf))).strip()
            self.summary_buf = []
        if self.in_nav_heading and tag in ("h2", "h3", "strong", "b"):
            self.in_nav_heading = False
            heading = unescape(re.sub(r"\s+", " ", "".join(self.nav_heading_buf))).strip()
            if "in this issue" in heading.lower():
                self.saw_in_this_issue = True
            self.nav_heading_buf = []
        if tag == "a" and self.in_nav_a:
            self.in_nav_a = False
            link_text = unescape(re.sub(r"\s+", " ", "".join(self.nav_a_buf))).strip()
            self.nav_links.append({"href": self.nav_a_href or "", "text": link_text})
            self.nav_a_href = None
            self.nav_a_buf = []
        if tag == "nav" and self.in_nav:
            self.nav_depth -= 1
            if self.nav_depth <= 0:
                self.in_nav = False
                self.nav_depth = 0
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

    # --- Summary gate ---
    NUMBER_WORDS = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
        "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
        "nineteen": 19, "twenty": 20,
    }

    def _parse_count_near(text, patterns):
        """Return first integer found near any of the patterns, else None."""
        lower = text.lower()
        for pat in patterns:
            for m in re.finditer(pat, lower):
                window = lower[max(0, m.start() - 25): m.end() + 25]
                # digit immediately before pattern word, e.g. "3 leads"
                mdig = re.search(r"(\d+)\s+" + re.escape(m.group(0).split()[0]), window)
                if mdig:
                    return int(mdig.group(1))
                # number word before
                for word, val in NUMBER_WORDS.items():
                    if re.search(rf"\b{word}\s+" + re.escape(m.group(0).split()[0]), window):
                        return val
                # digit after, e.g. "leads: 3"
                mdig2 = re.search(re.escape(m.group(0)) + r"\D{0,10}(\d+)", window)
                if mdig2:
                    return int(mdig2.group(1))
        return None

    leads = [s for s in stories if s.get("tier") == "lead"]
    alsos = [s for s in stories if s.get("tier") == "also"]
    n_leads = len(leads)
    n_also = len(alsos)

    summary = parser.summary_text
    if not summary:
        failures.append(
            "Summary missing: require <p class=\"summary\"> before the nav "
            "(modeled on original News Bot meta line: lead count, Also-today count, and a one-line dek)"
        )
    else:
        words = re.findall(r"[A-Za-z0-9']+", summary)
        if len(words) < 25:
            failures.append(
                f"Summary too short: {len(words)} words (need at least ~25), modeled on original meta line"
            )
        lead_count_in_summary = _parse_count_near(
            summary,
            [r"leads?", r"lead stor(?:y|ies)", r"at length"],
        )
        also_count_in_summary = _parse_count_near(
            summary,
            [r"also today", r"below the line", r"shorts?", r"in brief", r"short items?"],
        )
        # Also accept patterns like "three leads, six below the line" / "six shorts"
        if lead_count_in_summary is None:
            m = re.search(
                r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+leads?\b",
                summary,
                re.I,
            )
            if m:
                g = m.group(1).lower()
                lead_count_in_summary = int(g) if g.isdigit() else NUMBER_WORDS.get(g)
        if also_count_in_summary is None:
            m = re.search(
                r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+"
                r"(?:below the line|shorts?|short items?|also[- ]today items?|in brief)\b",
                summary,
                re.I,
            )
            if m:
                g = m.group(1).lower()
                also_count_in_summary = int(g) if g.isdigit() else NUMBER_WORDS.get(g)
        if lead_count_in_summary is None:
            failures.append(
                "Summary must state the lead count (digit or number word, e.g. 'three leads')"
            )
        elif lead_count_in_summary != n_leads:
            failures.append(
                f"Summary lead count {lead_count_in_summary} != parsed lead stories {n_leads}"
            )
        if also_count_in_summary is None:
            failures.append(
                "Summary must state the Also-today count (digit or number word, e.g. 'six below the line')"
            )
        elif also_count_in_summary != n_also:
            failures.append(
                f"Summary Also-today count {also_count_in_summary} != parsed Also-today stories {n_also}"
            )

    # --- Article list / nav gate ---
    # Require a <nav> before the first story with 'In this issue' and links for every story + Also noted.
    if not parser.nav_links and not parser.saw_in_this_issue:
        failures.append(
            "Article list missing: require a <nav> before the first story with an "
            "'In this issue' heading and an <ol> listing every lead and Also-today item"
        )
    else:
        if not parser.saw_in_this_issue:
            failures.append("Nav must contain an 'In this issue' heading")
        # Collect fragment targets
        story_ids = {s.get("id") for s in stories if s.get("id")}
        lead_ids = {s.get("id") for s in leads if s.get("id")}
        also_ids = {s.get("id") for s in alsos if s.get("id")}
        if len(story_ids) != len(stories):
            failures.append(
                "One or more stories are missing an article id= attribute required for the nav list"
            )
        nav_story_targets = []
        has_also_noted = False
        broken = []
        empty_text = []
        extras = []
        allowed_non_story = {"also-noted", "also-today", "also"}
        for link in parser.nav_links:
            href = (link.get("href") or "").strip()
            text = (link.get("text") or "").strip()
            if not text:
                empty_text.append(href or "(no href)")
            if not href.startswith("#"):
                broken.append(f"{href!r} (not an in-page #id)")
                continue
            target = href[1:]
            if target == "also-noted" or target == "also_noted":
                has_also_noted = True
                if target not in parser.all_element_ids:
                    broken.append(f"#{target} (Also noted target missing)")
                continue
            if target in allowed_non_story:
                if target not in parser.all_element_ids and target != "also":
                    # also-today must exist as section id
                    if target == "also-today" and target not in parser.all_element_ids:
                        broken.append(f"#{target} (section missing)")
                continue
            if target not in parser.all_element_ids:
                broken.append(f"#{target} (no element with that id)")
            if target in story_ids:
                nav_story_targets.append(target)
            else:
                extras.append(f"#{target}")
        if empty_text:
            failures.append(
                "Nav has link(s) with empty text: " + ", ".join(empty_text[:8])
            )
        if broken:
            failures.append(
                "Nav has broken link(s): " + "; ".join(broken[:8])
            )
        if not has_also_noted:
            failures.append("Nav must include a link to Also noted (#also-noted)")
        missing_leads = sorted(lead_ids - set(nav_story_targets))
        missing_also = sorted(also_ids - set(nav_story_targets))
        if missing_leads:
            failures.append(
                "Nav missing lead link(s): " + ", ".join("#" + x for x in missing_leads)
            )
        if missing_also:
            failures.append(
                "Nav missing Also-today link(s): " + ", ".join("#" + x for x in missing_also)
                + " (list each item, or put them in a second sub-list)"
            )
        # Extra story-looking targets already handled; flag duplicate story links
        from collections import Counter
        counts = Counter(nav_story_targets)
        dups = [f"#{i}×{c}" for i, c in counts.items() if c > 1]
        if dups:
            failures.append("Nav lists the same story more than once: " + ", ".join(dups))
        # Extra non-allowed targets
        if extras:
            failures.append(
                "Nav has extra entry(ies) that are not lead/Also-today/Also-noted: "
                + ", ".join(extras[:8])
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

    print(f"Stories parsed: {len(stories)} (leads={n_leads}, also={n_also})")
    print(f"Continuations: {len(continuations)}")
    print(f"Radio groups: {len(radio_groups)}")
    print(f"Summary present: {bool(summary)}")
    print(f"Nav links: {len(parser.nav_links)}; In this issue: {parser.saw_in_this_issue}")
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
