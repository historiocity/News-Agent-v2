# Brief config — News Bot 2.0

Edit this file to retune weighting and settled preferences. Applied before each run when brief-feedback issues exist. Nothing here is permanent — the point is that it is cheap to change.

## Weighting categories

**Weighting aids only. They do not define what to search or what to cover; see NEWSBOT_2.0.md Daily method.**

Cast a wide net first. Build today’s candidate list from what people are talking about and acting on. Use the categories below only to break ties and nudge weight. A story needs no category to make it. A category with nothing big that day gets nothing. Do not dig a fixed beats list every morning.

Categories marked **Core** get the benefit of the doubt in a close call. Everything else is secondary and has to earn its slot against them — see *Altitude bar*.

| Category | Scope |
|---|---|
| **Core** — AI & tech industry | Model releases, agent tooling, capex and the physical constraints on it, the business and policy fights around them |
| **Core** — Macro & markets | Fed path, rates, inflation, employment, market-moving earnings |
| World economy | US, EU, China, Middle East — **only through the lens of US policy toward and interaction with each** |
| **Core** — US debt & fiscal | Deficit, Treasury issuance and buybacks, debt service, CBO projections, the long end of the curve |
| **Core** — US financials | Top US banks, asset managers, payments. JPMorgan and its direct competitors get standing attention |
| **Core** — US politics & policy | Legislation, courts, regulation. Substance only |
| Geopolitics | Conflicts and rivalries with real second-order consequences **for the US**. A foreign conflict with no US channel is not this brief’s business |
| Science & public health | Research that changes how something works |
| **Core** — UAP disclosure | Government disclosure, implementing guidance, credible releases, new imagery from state or public sources. Track the paperwork, not just the imagery |
| Energy & grid | Generation, transmission, interconnection, transformers, retail power prices — where AI capex becomes a household bill |
| Elections and electoral process | Certification fights, voting rules, map fights, state AG and secretary-of-state races when material *(v2 addition)* |
| Broader domestic institutions | Structural moves inside agencies, courts, Congress, and the executive beyond a single bill *(v2 addition)* |
| International with US channel | Foreign items that clear the altitude bar because a US policy, market, ally, or security channel is clear *(v2 addition; overlaps Geopolitics / World economy)* |
| Florida / Tampa Bay | New Port Richey, Pasco, Pinellas, Tampa, state-level FL — local bar, not national *(v2 addition; see Local section)* |
| Data centers / power / AI infrastructure | Campus filings, interconnection, tax/land deals, local power-bill and opposition fights *(v2 addition; overlaps Energy & grid and AI & tech)* |
| AI and financial services | AI in banks/asset managers/payments; financial-services regulation and market structure that touches AI or this reader’s work *(v2 addition)* |

## Altitude bar

1. **Foreign stories need a US channel.** Ask what changes for this reader — a price they pay, a rate they borrow at, a policy their government must answer, a company they own. If the answer is “it is interesting”, it does not run.
2. **Disruption is not consequence.** Cancelled flights, a factory’s headcount, a single arrest — events, not developments, unless something structural moves behind them.

## Local section

Judged on a local bar rather than a national one. Leave the name blank to omit the section entirely. Empty is fine.

| Field | Value |
|---|---|
| Section name | Florida & Tampa Bay |
| Scope | New Port Richey, Pasco, Pinellas, Tampa, state-level FL |

## Anti-topics

*Defaults. Edit freely.*

- Sports results and transfers
- Celebrity and entertainment industry news
- Crime blotter without policy consequence
- Horse-race polling and campaign tactics
- Personnel churn with no policy effect
- Product launches that are only marketing
- “New study finds” pieces with no accessible study
- Foreign corporate restructuring with no US channel
- Natural-disaster disruption — flights, closures, transit — with no US effect
- Individual acts of political violence with no policy consequence
- Foreign elections, unless the result changes a US relationship

## Settled preferences

*From reader feedback. Do not re-ask these in the per-story questions. Radio answers that change lasting weight get recorded here; they do not build a fixed daily search list.*

- **Corrections** go in a box at the top of the affected story, not the footer.
- **When an earlier framing turns out wrong**, say so prominently — it earns space.
- **Single-sourced stories** are wanted, run with the `Single-sourced` label rather than held.
- **Trade stories**: both the legal-mechanism half and the market-effect half.
- **Ukraine**: current balance is right for a US-centred brief — do not increase or cut.
- **Florida section**: no target size. Only what clears a real local bar; empty is fine.
- **Oil strikes and the pump price** run as one causal chain, not two stories. (Asked again 11 Sep, because the Bab el-Mandeb is a different strait — answer pending.)
- **Charts**: wanted. Prefer the official series with a record line, not decoration.
- **Fed**: actual prints and the decision only. No state-of-play item on a quiet day.
- **Underreported finds**: current balance is right. Do not increase at the cost of a headline story.
- **Lab safety disclosures** and **state AI legislation**: both confirmed as standing threads.
- **Feedback radios (v2):** one condition-based question per lead; options name concrete follow-on conditions (local energy costs, political deals/money, salacious detail, public reaction, dated decisions) — not stock keep/drop, and not price for its own sake.
- **Chat ping (v2):** live Pages link and commit SHA only (or audit failure output).

**Standing discipline note, added 13 Sep after an error.** Never carry a weekday label (“Monday”, “this Friday”) forward between issues. Re-derive the day of the week from the date every run. The 11 and 12 Sep issues both called 15 September “Monday”; it is a Tuesday, and the wrong label was attached to two separate threads (duration of status, Canada duty-list modifications). Dates were right throughout; only the weekday was wrong. Corrected in the 13 Sep second edition.

**Standing discipline note, added 18 Sep after a worse error.** A market LEVEL printed to the basis point must come from the issuer’s own published series, not from a vendor quote and never from a search-engine summary of one. On 14–17 September this brief printed the 10-year Treasury yield as 5.00, 5.041, 5.016 and 4.943 and built a lead around the 10-year going “through 5%” for the first time since July 2007. Treasury’s own Daily Par Yield Curve — reached on the first attempt on 18 September — shows 4.88, 4.91, 4.94 and 4.86. **The 5% crossing did not happen in the series of record.** The sourcing caveat was disclosed each day; the number was still wrong, and it was the number the story turned on. Corrected as the second lead on 18 September. The generalisable rule: **when a vendor page is blocked, check whether the issuer publishes the number before falling back to a summary of the blocked page.** See the Treasury entry under *Sources*.

**Standing discipline note, added 22 Sep after a wrong turn call.** **Do not call a trend turn off a daily series when a weekly official series exists for the same quantity.** The 21 Sep issue called “the top of a move” in diesel off three shrinking daily AAA increases (5.2c, 1.8c, 0.6c); on 22 Sep AAA rose 1.69c and undid it. The deceleration was real — it is visible in the EIA weekly increments (+36.8c, +31.8c, +24.4c) — and it was read off the wrong instrument. The generalisable form: **a daily card average measures today; a weekly survey measures the trend; a weekly average cannot re-accelerate on a Tuesday and a daily average cannot decelerate over three weeks.** Use the daily series for the level and the fastest honest signal, the weekly official series for direction. This is a cousin of the 18 Sep rule about issuer series versus vendor quotes, and of the standing caution about never pooling daily and weekly transit counts.

## Interest tags (Also noted)

Weighting aids for near-misses only — not a search list.

- AI infrastructure & consulting-relevant trends
- Financial-services regulation / market structure
- Data centers & power
- Florida / Tampa Bay
- Elections / electoral process when material

## Sources

**Reliably reachable:** Reuters · AP · BBC · Guardian · NPR · Al Jazeera · CNBC · ProPublica · SEC EDGAR · Federal Register · BLS · Federal Reserve · court dockets · company IR pages · trade press · Politico · Axios · The Hill · Fox News (as one viewpoint among others)

**Viewpoint-diverse sweep set (Daily method Step 1):** AP · Reuters · `text.npr.org` · BBC · Al Jazeera · Fox News · WSJ/FT/Bloomberg/NYT headlines as signal only · Politico · Axios · The Hill · Federal Register public inspection · major court dockets · Tampa Bay outlets · X trends/news when reachable

**Non-English, reachable:** Le Monde · El País · Folha de S.Paulo · Nikkei Asia · SCMP · Haaretz · Yle · Handelsblatt and FAZ (partial)

**Paywalled, headline-only:** WSJ · FT · Bloomberg · NYT · The Economist. Treat as signal that a story exists; stand it up elsewhere before using it.

**Local:** Tampa Bay Times · Suncoast News · WFLA · WUSF · Fox 13 Tampa Bay tag feeds · Pasco and Pinellas county agendas and minutes

**Not reachable / fragile:** X/Twitter often behind a login wall. YouTube gives titles, descriptions, and sometimes transcripts — never assume a video was watched. Reuters, AP, BBC, Guardian, Le Monde and El País often refuse direct front-page fetches; reach their stories through search instead. CNN returns 451. GAO’s reports index has returned 403. Tampa Bay Times is paywalled beyond the lede. `congress.gov` often 403s. CNBC article pages often 403.

**Operational notes that save a run:**
- **federalregister.gov blocks page fetches** and redirects to an unblock page. Use the JSON API instead — it works and is better: `https://www.federalregister.gov/api/v1/documents.json?conditions[publication_date][is]=YYYY-MM-DD&conditions[type][]=RULE&conditions[type][]=PRORULE&per_page=60&fields[]=title&fields[]=agencies&fields[]=type`. Add `&conditions[term]=…` to pull an abstract, docket, comment-close and effective date for one document. Caveat: this gives abstracts, not preambles — say so when it matters. Also sweep `PRESDOCU` and `NOTICE` types; presidential documents are not RULE/PRORULE. Full text: `https://www.federalregister.gov/documents/full_text/text/YYYY/MM/DD/DOC-NUM.txt`.
- **The Federal Register public-inspection list is offline from midnight Eastern** and returns Monday at 8:45am. On a Sunday run there is no view of Monday’s documents — say so rather than implying the list was empty.
- **EIA’s PDF releases cannot be parsed.** Use the weekly data tables at `eia.gov/dnav/pet/pet_pri_gnd_dcus_nus_w.htm` — same series, readable.
- **`text.npr.org` is the best general wire sweep available here.** It fetches cleanly and lists ~20 current headlines. Caveat: an NPR story syndicated across member-station sites is **one** source, not dozens.
- **Treasury’s Daily Par Yield Curve fetches cleanly and is the series of record** for dated yield levels: `home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value_month=YYYYMM`. A ticker or newspaper may be used for direction only.
- **Handelsblatt’s front page does fetch**, and is the most useful non-English source for European central banking and the global bond market.
- **apnews.com often refuses direct fetches.** Reach AP through search or a syndicating outlet.
- **Al Jazeera’s `/news/` index and live blogs often fetch**, and are a fast same-morning headline sweep when AP/Reuters fronts are unavailable.
- **BLS release pages fetch cleanly** for CPI/PPI component tables. Use the primary release, never a wire summary, for those numbers.
- **`clerk.house.gov/Votes/<year><rollcall>` fetches cleanly** when you already have the roll-call number; do not guess the number.
- **PDFs are often unparseable here.** If a story’s load-bearing document is a PDF, assume it may not be readable and find who has read it; say when the document was not read.
- **Wikipedia’s current-events portal** is useful as a negative-check *list* of what happened that you have not seen; publish nothing on it alone.
- More dated operational notes live in the original News-Agent `config.md`; copy forward only rules that still save a run.

## Watchlist

Empty on purpose for News Bot 2.0’s daily method. Do not rebuild a fixed dig-list here. Threads that radio answers ask to follow may be noted as **weighting reminders with a wake condition**, never as the morning search agenda. Yesterday’s stories return only when a new development clears Daily method Step 2.
