# News Bot 2.0 Specification

## Daily method: how the day's topics are chosen (binding)

Follow these steps every run. There is no perfect answer. Make choices. Do not over-index on any list, watchlist, or category table.

1. **Cast the net before consulting any category.** Sweep a broad, viewpoint-diverse set of sources. Examples: AP, Reuters, NPR text (`text.npr.org`), BBC, Al Jazeera, Fox News, WSJ/FT/Bloomberg/NYT headlines as signal only (stand facts up elsewhere), Politico, Axios, The Hill, Federal Register public inspection, major court dockets, Tampa Bay outlets, and X trends/news when reachable. Do **not** start from yesterday's stories or the watchlist. Build a candidate list of **30–50** items people are actually talking about or acting on today.

2. **Weigh each candidate with plain questions.** Does it change something for this reader (money, policy, their region, their work in AI/consulting and financial services)? Is it moving (a decision, deal, fight, deadline)? Is it underplayed relative to its consequence? Do credible sources disagree in a way worth showing? Is there behind-the-scenes politics/money, notable public reaction, or salacious detail that makes it worth attention? Categories in `config.md` only break ties and nudge weight; a story needs no category to make it, and a category with nothing big that day gets nothing. Do **not** carry a story forward just because it ran yesterday; carry it only if it has a new development that clears the same weighing.

3. **Choose and position.** Select roughly **10–15** stories total (leads plus Also today), aiming for at least **10**; fewer only if the day genuinely lacks them, with the reason stated in the brief and the log. For each: why it matters to this reader, what the different sides/sources say (divergence box where they disagree), what to watch next. Near-misses go to Also noted with a one-line reason they missed.

4. **Learn.** Radio answers adjust weighting over time, recorded in `config.md` settled preferences; they do **not** build a fixed search list or a fixed agenda of stories to dig every day.

**Logging.** The process log records the full candidate list with a keep/cut reason for each, and which sources were swept **before** any category was consulted. It also keeps a `beat_coverage` entry for each weighting category (the current audit requires that field): treat each entry as a short weighting note (strongest candidate seen, why it cleared or failed), not as proof that the category was searched as a beat list.

**Audit note.** Enforcement of the candidate-list log and a hard 10-story floor is **proposed and pending the user's approval of an `audit.py` change**. The current audit does **not** enforce those two items. Do not claim that it does.

## Executable pre-publish gates
An audit script must exit 0 before any publication. It verifies:

- Continuing leads ≤ 4, each with an explicit trigger (new verifiable fact, threshold event, reversal, or material connection).
- Every story has exactly one confidence marker; every lead’s citations match the marker claimed.
- Every divergence box contains the three required parts (dispute type, source vantage/interests/access/timing, implications for the reader).
- Independence: Claude’s edition (or prior) opened only after the draft exists; excessive lead overlap flagged.
- Self-report consistency: provenance line matches the script’s independent counts.
- Layout completeness against the Issue 10 template; “Dig deeper” only where substance exists; required summary paragraph and full In-this-issue nav (see below).
- Process log present and complete: outside-first gathering evidence, broad sweeps, negative-check result, and a `beat_coverage` weighting note for each weighting category in `config.md`.
- Feedback freshness: recent brief-feedback issues applied to `config.md` settled preferences / weighting notes.
- Source thoroughness: no fixed minimum count. Verify process evidence of sufficient independent accounts and a real negative check. Soft warning only if total is unusually low and the paper is heavy on continuations; does not block.
- Feedback radios: one condition-based question per lead; no stock/reused option text (see Feedback radios).

The morning chat ping is **only** the live Pages link and the commit SHA. If the audit blocks publication, send the failure output instead. Do **not** put the audit report, dek, lead recap, marker counts, or source notes in the ping.

## Process rules
- Follow **Daily method** above every run: cast the net first, then weigh, then choose.
- Open any comparison edition only after the draft is finished; use it only for count comparison and error catching.
- Emit a structured process log the audit script consumes (including the candidate list with keep/cut reasons, even though the candidate-list shape is not yet an audit hard gate).
- Apply radio-button feedback before the next run starts; record lasting weight changes in `config.md` settled preferences.

## Selection
Absolute bar: consequence for this reader, changes the picture, and verifiable. “Proximity to a category” is a weighting nudge only — never a search brief and never a reason to invent coverage.

**Weighting categories** live in `config.md` (original Core/secondary table plus v2 additions). They break ties and nudge; they do not define what to search or what must appear. A category with nothing consequential that day gets nothing.

Each run still produces a short `beat_coverage` log entry for every weighting category (sources that happened to touch it, strongest candidate, why it cleared or failed). That satisfies the current audit’s process-log field. It is a weighting note after the net was cast — not evidence that the day was searched category-by-category.

## Per-article sourcing
For each article (lead or short item), list the number of independent sources used and include inline links in the text so the reader can see where the point of view comes from.

## Single-file “Also noted” section
At the bottom of the same HTML file, after the footer, a collapsible `<details>` section headed “Also noted.” Closed by default.

Contains only short (1–2 sentence) pointers to near-misses — items that were in the candidate net but did not clear the main bar or length limits — each with a one-line reason it missed. Cap at 8–12 items. No markers, boxes, or long write-ups.

Interest tags (starter list, editable in `config.md`; weighting aids for Also noted only):
- AI infrastructure & consulting-relevant trends
- Financial-services regulation / market structure
- Data centers & power
- Florida / Tampa Bay
- Elections / electoral process when material

## Output and delivery
Publish under a distinct filename such as `issues/YYYY-MM-DD-v2.html` (or `…-b-v2.html`, `…-c-v2.html` for same-day redos) so it does not overwrite any prior edition.

**Chat ping:** only the live Pages link and the commit SHA. On audit failure: the failure output only. No dek, no lead recap, no audit summary in chat.

## Implementation notes
- Place the audit script(s) in the repo (e.g. `scripts/audit.py`).
- The routine or skill must treat a non-zero audit exit as a hard failure.
- Keep natural-language rules high-salience; let the code enforce the details.
- Share the same audit scripts with any parallel version so both editions are held to identical quantitative standards where possible.
- Proposed (not yet implemented) audit gates: require the process log’s full candidate list with keep/cut reasons, and a soft/hard floor near 10 stories unless the log states why the day lacked them. Await user approval before editing `audit.py`.

## Feedback radios (binding)

Modelled on the original News Bot’s earliest issues (Sept 5–Oct 1, 2026), not the later generic keep/drop pattern.

**Per lead — exactly one question.**
- One `<div class="fb">` with one radio group (unique `name`), 2–3 options.
- The block must include a question in a `<p>` that ends with `?`.
- The question asks **under what conditions** the reader should keep following the story — what would make the next development worth their attention.
- Each option is a distinct, concrete angle or trigger specific to that story. Prefer: local energy costs / utility rate cases; political deals or money behind the scenes; who lobbies or benefits; salacious or scandalous details; notable public or local reaction/opposition; a dated decision, vote, filing, or ruling; a named official’s next move.
- Price or market moves for their own sake are **not** a relevant reason (e.g. data-center coverage is about local power bills, tax/land deals, and public reaction — not wholesale pricing).
- One option may narrow or close the thread, but must name a **specific condition** (e.g. “Only if the state PSC rejects the rate filing”).
- **Banned:** stock option text such as “Keep it at this level”, “Drop it”, “The mix is right”, “No opinion”, “Stop following”, “Not interested”, “Keep following”, “Follow it”, bare “Yes” / “No”.
- **Banned:** reusing the same option wording across stories (or across a lead and the Also-today tier block).

**Also today — no per-item radios.**
- After the Also today items, exactly one block: `<p><b>On the items below the line.</b></p>` plus one question with 2–3 options, each naming a specific item/angle the reader might want promoted to a lead.

The audit (`scripts/audit.py`) enforces: max one radio group per story; ≥1 group on each lead; no stock phrases; no reused option text; 2–3 options per group; lead fb blocks must contain a question ending in `?`.

## Header summary and article list (binding)

Modeled on the original News Bot (`p.meta` dek + “In this issue” nav), e.g. `issues/2026-11-07.html` in historiocity/News-Agent.

**Summary.** Before the nav, include `<p class="summary">…</p>` of at least ~25 words. It must state the lead count and the Also-today count (as digits or number words, e.g. “Three leads, six below the line”) and those counts must match the stories actually in the file. Follow with a one-line dek of what the issue covers, in the spirit of the original meta line.

**Article list.** A `<nav>` before the first story must contain an “In this issue” heading and an ordered list with:
- one link per lead story (`href="#id"`, non-empty link text);
- one link per Also-today item (same rules; may sit in a second sub-list);
- a link to Also noted (`#also-noted`).

Every `#id` must resolve to an element in the file. Every lead and Also-today story must appear exactly once. No broken, empty, or stray story entries.

The audit enforces both gates.
