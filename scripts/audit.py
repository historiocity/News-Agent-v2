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
from collections import defaultdict

PRIMARY_DOMAINS = {
    "whitehouse.gov", "congress.gov", "supremecourt.gov", "sec.gov", "bls.gov",
    "eia.gov", "treasury.gov", "census.gov", "federalregister.gov", "govinfo.gov",
    "cbo.gov", "gao.gov", "federalreserve.gov", "fdic.gov", "occ.gov",
    "nytimes.com",  # not primary; example of how to keep the list short
}
# Real primary/near-primary domains (extend as needed)
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
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h3":
            if self.current:
                self._finish_story()
            self.current = {"title": "", "html": "", "links": [], "marker": None, "is_continuation": False, "divergence": False}
            self.in_lead = True
            self.capture = []
        if tag == "a" and "href" in attrs and self.current is not None:
            href = attrs["href"]
            domain = self._domain(href)
            if domain:
                self.current["links"].append(domain)
        if tag == "details" and self.current is not None:
            # rough flag for dig-deeper or divergence
            pass

    def handle_data(self, data):
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

    # Divergence boxes (rough: presence of the word + three part keywords)
    if "divergence" in html.lower():
        if not all(k in html.lower() for k in ["dispute", "vantage", "means for"]):
            # soft for now; tighten once HTML structure is stable
            warnings.append("Divergence language present but three-part structure not clearly detected")

    # Process log
    if len(sys.argv) > 2:
        log_path = Path(sys.argv[2])
        if log_path.exists():
            try:
                log = json.loads(log_path.read_text())
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

    # Self-report consistency (very light: look for provenance numbers)
    prov = re.search(r"(\d+)\s+sources", html, re.I)
    if prov:
        # could cross-check against log if present
        pass

    # Layout presence
    for section in ["Also today", "Also noted"]:
        if section.lower() not in html.lower():
            warnings.append(f"Section '{section}' not found (may be optional)")

    print(f"Stories parsed: {len(stories)}")
    print(f"Continuations: {len(continuations)}")
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
