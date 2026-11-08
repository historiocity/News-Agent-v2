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

PRIMARY_DOMAINS = {
    "whitehouse.gov", "congress.gov", "supremecourt.gov", "sec.gov", "bls.gov",
    "eia.gov", "treasury.gov", "census.gov", "federalregister.gov", "govinfo.gov",
    "cbo.gov", "gao.gov", "federalreserve.gov", "justice.gov", "state.gov",
    "defense.gov", "energy.gov", "epa.gov", "fda.gov", "cdc.gov",
}

WIRE_DOMAINS = {"reuters.com", "apnews.com", "bloomberg.com"}

class StoryExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stories = []
        self.current = None
        self.in_lead = False
        self.capture = []
        self.in_h3 = False
        self.in_h2 = False
        self.tier = "lead"

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
                "tier": self.tier,
            }
            self.in_lead = True
            self.in_h3 = True
            self.capture = []
        if tag == "h2":
            self.in_h2 = True
        if tag == "a" and "href" in attrs and self.current is not None:
            href = attrs["href"]
            domain = self._domain(href)
            if domain:
                self.current["links"].append(domain)
        if tag == "input" and attrs.get("type") == "radio" and self.current is not None:
            name = attrs.get("name", "")
            if name:
                self.current["radio_names"].add(name)

    def handle_data(self, data):
        if self.in_h2 and "also today" in data.lower():
            self.tier = "also"
        if self.in_h3 and data.strip():
            self.capture.append(data.strip())
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
        if tag == "h3" and self.current is not None:
            self.current["title"] = " ".join(self.capture).strip()
            self.capture = []

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

def check_marker_vs_links(story):
    marker = story.get("marker")
    domains = set(story.get("links", []))
    if not marker:
        return "missing confidence marker"
    primary_hits = domains & PRIMARY_DOMAINS
    newsroom_hits = domains - PRIMARY_DOMAINS - WIRE_DOMAINS
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

    # Per-lead radio buttons (hard gate)
    # Original News Bot format: each lead has exactly ONE feedback question (one radio group,
    # typically 3 options). Stories after the "Also today" heading need no per-item radio;
    # the tier gets one overall question. No story may carry more than one question.
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

    # Source count target (~40). Hard fail only if extremely low and no underreported judgment noted.
    # Prefer process log; fall back to provenance text.
    sources_total = None
    underreported_judgment = False
    if len(sys.argv) > 2:
        log_path = Path(sys.argv[2])
        if log_path.exists():
            try:
                log = json.loads(log_path.read_text())
                sources_total = log.get("sources_checked_total")
                # Look for explicit underreported judgment
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
