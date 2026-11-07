# News Bot 2.0 Specification

## Executable pre-publish gates
An audit script must exit 0 before any publication. It verifies:

- Continuing leads ≤ 4, each with an explicit trigger (new verifiable fact, threshold event, reversal, or material connection).
- Every story has exactly one confidence marker; every lead’s citations match the marker claimed.
- Every divergence box contains the three required parts (dispute type, source vantage/interests/access/timing, implications for the reader).
- Independence: Claude’s edition (or prior) opened only after the draft exists; excessive lead overlap flagged.
- Self-report consistency: provenance line and chat ping match the script’s independent counts.
- Layout completeness against the Issue 10 template; “Dig deeper” only where substance exists.
- Process log present and complete: outside-watchlist-first gathering, broad sweeps, negative-check result, and a beat-coverage entry for each standing beat.
- Feedback freshness: recent brief-feedback issues applied to config.md or the watchlist.
- Source thoroughness: no fixed minimum count. Verify process evidence of sufficient independent accounts and a real negative check. Soft warning only if total is unusually low and the paper is heavy on continuations; does not block.

The audit report is included in the morning chat ping.

## Process rules
- Gather by source, starting outside the watchlist.
- Open any comparison edition only after the draft is finished; use it only for count comparison and error catching.
- Emit a structured process log the audit script consumes.
- Apply radio-button feedback before the next run starts.

## Selection
Absolute bar unchanged: consequence, proximity to beats, changes the picture, and verifiable.

Standing beats expanded to include:
- Elections and electoral process
- Broader domestic institutional developments
- International items with clear US consequences
- Florida / Tampa Bay
- Data centers / power / AI infrastructure

Each run must produce a short beat-coverage log entry for every beat (sources checked, strongest candidate, why it cleared or failed the bar). This does not force a story into the leads.

## Per-article sourcing
For each article (lead or short item), list the number of independent sources used and include inline links in the text so the reader can see where the point of view comes from.

## Single-file “Also noted” section
At the bottom of the same HTML file, after the footer, a collapsible `<details>` section headed “Also noted.” Closed by default.

Contains only short (1–2 sentence) pointers to items that matched standing interest tags but did not clear the main bar or length limits. Cap at 8–12 items. No markers, boxes, or long write-ups.

Interest tags (starter list, editable in config.md):
- AI infrastructure & consulting-relevant trends
- Financial-services regulation / market structure
- Data centers & power
- Florida / Tampa Bay
- Elections / electoral process when material

## Output and delivery
Publish under a distinct filename such as `issues/YYYY-MM-DD-v2.html` so it does not overwrite any original edition.

Chat ping includes the link, dek, leads with key numbers, audit summary, marker/box counts, and source notes.

## Implementation notes
- Place the audit script(s) in the repo (e.g. scripts/audit.py).
- The routine or skill must treat a non-zero audit exit as a hard failure.
- Keep natural-language rules high-salience; let the code enforce the details.
- Share the same audit scripts with any parallel version so both editions are held to identical quantitative standards where possible.
