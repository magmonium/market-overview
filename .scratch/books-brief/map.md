# Wayfinder — the Books Brief

`wayfinder:map` · local-markdown tracker · `.scratch/books-brief/`

## Destination

A **build-ready spec** for a new sibling product, **`books-brief`**: a weekly report carrying **four** Top-100
charts — **Bengali**, **English**, **Indian all-language**, and **Comics** (ticket 12) — each built by
**corroborating** several bestseller sources (a title is admitted only when the sources agree it exists — ticket 17),
then ranking through a documented **chart logic**, and diffing against a previous period to derive
**up / down / NEW** (at most 10 NEW **per chart**), and rendered as beautiful slides — cover, best price, publisher,
author, rank, Δ, NEW badge, publication month and date — over a market-brief background with a logo — and each
shipped with an SEO title (`Top 100 Bengali Books | Week 10 | <date>, <year>`), a description carrying the **full
list**, optimised tags, and a **cover-collage thumbnail** (tickets 15, 16). It reuses the market-overview toolchain
(Python CLI → `facts.json` → Remotion → bundled ffmpeg).

⚠️ **Amended — the chart set is still four, but two charts are no longer India-market.** The brief now asks the Bengali
chart to **include Bangladeshi titles** (its market is the Bengali-language market across **India and Bangladesh**), the
comics chart to be **worldwide**, and all of them to **mention country, language and genre**. That reopens **ticket 12**, ⚠️ **breaks
ticket 14's superset** — an all-language *Indian* chart cannot contain a Bangladeshi title — and adds **ticket 20** (the
dimensions: **labels, not charts**), **ticket 21** (the Bangladeshi sources) and **ticket 22** (the worldwide comics
sources, where a weekly ranking has only **one** vendor). The count stays **four**; the *markets* are what moved.

⚠️ **And the basis moved too.** Every chart now ranks on **sales over the last six months together with user reviews**
(ticket 23) — not on a weekly list — which separates the **ranking window** (six months) from the **Δ window** (weekly),
and makes the first 26 weeks a **ramp** rather than a baseline.

⚠️ **Decisions, not deliverables.** This map writes no code. The pull to scaffold the product is the edge of the map,
and reaching it is a hand-off.

## Notes

- **Domain:** publishing / bestsellers. The host repo is a weekly-video factory with an India focus and a
  Bengali + English habit.
- **Reuse, don't reinvent** — these constraints are already recorded and are binding on every ticket:
  - `docs/adr/0002` — a Python CLI conducts the run
  - `docs/adr/0003` — `facts.json` is the **sole** interface to the render layer; display strings live in the
    renderer's label tables, so a string in `facts.json` is a bug
  - `docs/adr/0007` — the data lives **outside** the repository, namespaced per product
  - `store/<date>/raw/*.json` is written **before** parsing and `store/<date>/facts.json` is committed — the
    rebuild evidence, and the reason a week can be re-rendered without re-fetching
- **Standing preferences (the user's calls, already made):**
  - **multi-source** — no single vendor's list is the chart
  - **our own committed snapshot is the source of truth for Δ and NEW**, never a vendor's `rank_last_week`
  - the union is reduced to 100 by an **explicit, documented ranking rule** — not by concatenation
  - ⚠️ **at most 10 NEW entries** in the Top 100 — a hard cap the chart logic must satisfy (ticket 11), which means
    incumbency has to be part of the ranking rather than a badge applied afterwards
  - ⚠️ **four charts** — Bengali, English, Indian all-language, and Comics (ticket 12). The union, the chart logic
    and the ≤10 NEW cap all apply **per chart**, unless ticket 13 makes the four into one
  - ⚠️ **the all-language chart is a superset** — it may contain Bengali and English titles, so a title can appear in
    more than one chart, and **rank is chart-local** (ticket 14)
  - ⚠️ **genuine and authentic** — a title is admitted to a chart only when **corroborated** across as many sources as
    possible, with every claim traceable to a raw response (ticket 17)
- **Skills every session should consult:** `/grilling`, `/domain-modeling`, `/research`.
- **Reuse candidates in the host repo:** `remotion/` (`theme.ts`, `Brand.tsx`, `Furniture.tsx`, `Thumbnail.tsx`,
  the vendored fonts, the `copy.<lang>.json` label tables), `src/market_overview/fetch/tradingview.py`,
  `src/market_overview/audio.py`, and `deploy/`.

## Decisions so far

- [The declarations the sources do not support](issues/29-the-declarations-the-sources-do-not-support.md) — ✅ **resolved:
  correct the declarations to what exists, and make the *address* the thing a scraped list must state.** ⚠️ `english`
  drops PW (`indie/national` in its place), `all-language` reads **one** mixed Amazon list instead of nine, `bengali`
  loses Anandabazar **and** Amazon.in and keeps **Rokomari alone**, and `comics` is unchanged. ⚠️ **Two charts ship and
  two do not** — `english` (NYT + Indie) and `comics` (NYT + Amazon.in) reach ticket 17's gate, while `all-language` has
  one vendor and `bengali`'s one list is **undated**, so the freshness guard refuses it. ⚠️ **The mechanism is a
  constructor, not a comment**: `charts.Listing` gained an `address` and refuses a scraped list without one, which is what
  removed `anandabazar/bengali`. ⚠️ **Two of the ticket's own findings were wrong** — `/list/38927` holds no records while
  the Best Seller category holds 60, and `indie/national` is a real dated list whose date the client was deriving wrongly.
  ⚠️ And the registry followed: `amazon-in` and `indie` are now **registered**, which is what actually gives `english` and
  `comics` their second vendor; `rokomari` stays out, because its list carries no date.
- [The snapshot retention](issues/28-the-snapshot-retention.md) — **keep every week; there is no pruning.** ⚠️ This was
  fog until **ticket 23 made it load-bearing**: the six-month ranking window is **accumulated from our own snapshots**,
  so pruning is not storage management — it **silently shrinks the ranking window**, and nothing would say so. Three
  reasons: the ranking depends on it; ⚠️ **`store/` is the evidence, not the cache** (ADR 0007 — *"`store/` never was
  gitignored, and that is the difference between the tool's evidence and its data"*), and the raw responses are the only
  record if a figure is disputed; and ⚠️ **a re-run overwrites a snapshot** (18), so **git is the version history**.
  Cost stated: `store/` grows every week, committed — the same price the brief pays **per day**. If ever bounded, the
  bound is **"the window the chart claims"**, not "N weeks".
- [The operator prerequisites](issues/25-the-operator-prerequisites.md) — the checklist, and the column that matters is
  **what happens without each item**. ⚠️ **Amazon.in is the single point of failure**: it is in *every* chart's source
  set — the Indian ranking vendor, the Bangladeshi bridge **and** the price source — and it has **no API**, is a scrape
  contrary to its own terms, and is the very list HWR says *"can be gamed"*. **The most load-bearing prerequisite is
  the one with no contract** — which is *why* the corroboration gate (17), the freshness guard (10) and the footer's
  scope caveat (19, 21, 22) are load-bearing rather than decorative. Blockers: the **browser** (every render) and
  **Amazon.in** (every chart). ⚠️ **Two different answers for one item**: no **NYT key** means English **degrades** to
  PW + Indie (still two vendors) while **comics goes absent** (NYT is its only weekly ranker). Degradations: **Flipkart**
  (price becomes Amazon-only, and says so) and the **music bed** (ship silent — a deliberate divergence from the brief).
  `build` needs **no** YouTube token. And a **pre-flight check** runs before the render is spent.
- [The Bengali typeface](issues/27-the-bengali-typeface.md) — ✅ **the face already exists, vendored, in this repo**:
  **Noto Sans Bengali** (SIL OFL 1.1, so the bytes may live here) in `remotion/fonts/` as **nine committed `.woff2`** —
  3 weights × 3 subsets — described once in `fonts.json`. ⚠️ **The trap: the Bengali subset carries Bengali and `₹` but
  NO Latin**, and a Bengali chart's slide also prints the **rank, the price digits, `WEEK 41` and the whole ticker** in
  Latin — so it must load **both** subsets, or *"half of an edition"* renders in a fallback face. ⚠️ And the wait is not
  optional: `useFonts` loads against a `SAMPLE` spanning both, because `document.fonts.load` with no text resolves
  against the face covering a *space* (Latin), leaving Bengali glyphs to load **after the first frame was captured**.
  ⚠️ It **refuses** (`cancelRender`) rather than falling back. The bytes are the **brief's**, via `shared_remotion()`
  (09), and **`fonts.json` is the single manifest both sides read** — which is what makes ticket 07's title clamp a real
  measurement. ⚠️ **Decided: the Bengali chart renders its data numerals in Bengali** (`০১২৩৪৫৬৭৮৯`), matching
  `song-video`'s `caption.DIGITS`, while the **YouTube title stays Latin** for search (15) — *the title is the
  product's; the slide is the reader's.*
- [The genre vocabulary](issues/26-the-genre-vocabulary.md) — the third label (*"type of book poem novel fiction non
  fiction business etc"*), and ⚠️ **the first that always varies**, so its slot always draws. ⚠️ **Genre is not a field
  the sources hand over but a *classification*, and five sources use five taxonomies** (NYT list names, Amazon browse
  nodes, PW/Indie category lists, Google Books BISAC-ish `categories`, Rokomari's own tree) — so it is a
  **normalisation problem**: **14 stable slugs** (`poetry · novel · fiction · non-fiction · business · self-help ·
  biography · history · religion · children · comics · academic · reference · other`) with the words in the renderer's
  label table (ADR 0003). ⚠️ **The ranking source wins** over Google Books, because the vendor is *why* the title is on
  that chart; the mapping is an **explicit table**, never a runtime guess, or the label could not be replayed. **One
  primary genre on the slide, the full array in the snapshot.** ⚠️ **Not in the description** — the rows are already at
  ≈4,600 of 5,000 (ticket 15).
- [The publish targets](issues/24-the-publish-targets.md) — **YouTube, one video per chart, `private` by default** — the
  brief's own pattern, and everything already pointed there: ticket 15's metadata is **YouTube-shaped** (100-char title,
  5,000-char description, 500-*character* tags, 3 hashtags), ticket 10's idempotence key **exists because a publish
  needs it**, `--privacy` is a YouTube concept, and the brief's shape is **two commands and one wrapper** (`build` then
  `publish`, ADR 0006's *"the upload is part of the run"*). ⚠️ **`private` for ADR 0006's own reason** — *"the reason a
  human runs it"* — and the books check is exactly what this map built: is the Bengali chart actually Bengali, are the
  covers right, is the rank plausible, does the footer name the right sources. **One channel**, but per-chart packages
  make a regional channel a **configuration change**. ⚠️ **The carousel is deferred**: 400 stills a week with no social
  target is waste, so the stills are not rendered until one exists — and the composition already produces them when it
  does. Package = **four files**, mirroring `output/brief/<date>/<lang>/`.
- [The Bangladeshi Bengali market](issues/21-the-bangladeshi-bengali-market.md) — ⚠️ **Bangladesh has no *weekly
  editorial* Bengali chart**: **Rokomari** is a *retailer's own popularity ordering* (and 403 to plain fetchers), Boi
  Mela is annual, **BookVandar is not a chart at all**, and Prothom Alo / New Age only *report on* bestsellers. ⚠️ **The
  vendors do not overlap**, so the merged chart works in **one direction**: an Indian Bengali title has Anandabazar +
  Amazon.in, while a **Bangladeshi title has Rokomari alone → watchlist** unless Amazon.in also stocks it — and
  **Rokomari is worth adding precisely because it is that bridge**. ⚠️ So the chart's **Bangladeshi portion is thin by
  construction** and the chart **must state the boundary** — the third scope caveat, beside comics (22) and English
  (19). ⚠️ **It also discharges ticket 19's reversal trigger**: no second Indian ranking vendor was found, so the
  US-English flip **stands**.
- [The English chart's market, revisited](issues/19-the-english-charts-market-revisited.md) — **flipped to global, and
  honestly named US English**. ⚠️ India-market English **cannot be built** — ticket 17 needs two vendors and ticket 02
  found one — and ticket 12's coherence argument collapsed once the Bengali chart spanned India + Bangladesh (20) and
  comics went worldwide (22). Global English has **three** weekly vendors (NYT + PW + Indie Bestsellers), the richest set
  on the map, so the spine rule is met with room to spare. ⚠️ **But "global" is an overclaim** — all three are **US**
  lists, so the footer and description must name the sources. ⚠️ **Neither new label renders here** (country constant,
  language in the header), which is ticket 20's rule working. **Reversible**: a second Indian ranking vendor surfacing in
  ticket 21 would restore the India-market option.
- [The six-month sales and review basis](issues/23-the-six-month-sales-and-review-basis.md) — every chart ranks on
  **sales + reviews over a rolling six-month window** (*"mix review plus sales data for longer duration, not one
  month"*). ⚠️ **The sources publish only a *current* snapshot, so the window cannot be fetched — it must be
  accumulated**, which changes the *collection*: every run records, per title, the signal **and the date it was
  observed**, so a week's snapshot is *evidence for a six-month window* rather than just that week's chart. Signals:
  **sales** from PW/Circana `units sold` + **`YTD`** (the one genuinely multi-month figure, © Circana) and from our own
  accumulated ranks; **reviews** from Amazon.in rating + count and Google Books `ratingsCount`. ⚠️ The review term is
  **credibility-weighted (Bayesian)** — 5.0 from 3 reviews must not outrank 4.6 from 50,000 — and measures
  **popularity, not the six months**, which is acceptable only because the chart says so. ⚠️ **Weeks 1–25 ship stating
  the window they actually have** (a 26-week ramp); `YTD` is used where it exists, never as a substitute, because it is
  a *calendar-year* figure. Separates the **ranking window** (six months) from the **Δ window** (weekly), and makes the
  ≤10 NEW cap **easier** than it looked.
- [The worldwide comics market](issues/22-the-worldwide-comics-market.md) — ⚠️ **a worldwide *weekly* comics ranking has
  almost no vendors**: NYT `graphic-books-and-manga` is **weekly** (the one ranking vendor), **ICv2 is monthly** and
  cannot rank a week, and Amazon.in is **India**. One weekly vendor cannot corroborate itself (ticket 17), so as
  specified the chart would be **permanently absent**. ⚠️ **The rescue is separating ranking from corroboration** —
  ranking comes from the weekly vendors, while **corroboration only has to know the title**, so ICv2's monthly chart
  counts as evidence of existence. That is the same *existence vs freshness* split ticket 18 makes. ⚠️ Consequences: the
  chart **skews US** and must say so (the footer's source list); **Indian-only comics drop to the watchlist**; and the
  **country and language labels genuinely earn their place**.
- [The country, state and language dimensions](issues/20-the-country-state-and-language-dimensions.md) — **labels, not
  charts** (*"in chart just mention country language"*): the set stays four and no new videos appear, so the dimensions
  are two more **optional fields** in the slide's data column, landing in ticket 07. ⚠️ The rule that stops a label
  becoming noise is **show it where it varies** — the **country** on the Bengali chart (India / Bangladesh), the
  **language** on the all-language and comics charts — and no new layout rule is needed, because ticket 07 already omits
  an empty field without leaving a hole. ⚠️ **Not added to the description**, which already sits at ≈4,600 of 5,000
  characters (ticket 15, unchanged). **The Bangladeshi boundary:** the Bengali chart spans India *and* Bangladesh while
  the all-language chart stays Indian, so the superset is **amended, not abandoned** — all-language ⊇ every *Indian*
  title, and the Bengali chart carries a **Bangladeshi overhang**. ⚠️ **State** was raised and not confirmed; the field
  slot absorbs it if wanted.
- [The run's workflow](issues/18-the-run-workflow.md) — ⚠️ the brief's **spine vs everything-else** split maps exactly
  onto the corroboration rule: **the vendors a chart declares *are* its spine**, so a missing vendor makes the chart
  **absent** — *"a degraded chart is a wrong chart"*, one level down from *"a degraded brief is a wrong one"*. Everything
  else **degrades to omission** (ticker, cover, price, pub date). **A stale source is a missing source**, so the refusal
  is **per chart**, not per run — which **narrows ticket 10's wording**; the run writes nothing only when nothing can be
  built. **Week one ships as a stated baseline**: no Δ, no NEW, the ≤10 cap **explicitly bypassed**, and the warnings say
  so. ⚠️ **The snapshot's existence is the switch** (replay, no fetch); `--refetch` changes the hash and the publish
  **refuses** for an already-published week, while git makes the overwrite safe. Retries are **bounded with backoff**,
  with a **per-source budget** and **polite scraping**; and two habits are inherited verbatim — **the raw response is
  snapshotted even when parsing fails**, and **warnings go to stderr, never swallowed**.
- [The corroboration gate](issues/17-the-corroboration-gate.md) — ⚠️ ⚠️ **REVERSED 2026-10-15: the gate is *reported*,
  not required** — every title any declared list carries is admitted, and corroboration rides on the row. ⚠️ The rule was
  **unsatisfiable**: a two-vendor chart could rank only their *intersection* (**16 rows** for `english`) and a one-vendor
  chart nothing at all. Replaying 2026-W41's own responses gives **134 titles** where the gate admitted 16. ⚠️ Full
  amendment in **ADR 0004**. ⚠️ What still holds — **corroboration counts *vendors*, not lists**:
  Amazon.in's nine language categories are **one** source, so counting them as two would be "a lie told in
  arithmetic". **Admission needs two vendors**, raw responses committed; a single-vendor title is **parked on the
  watchlist**, not discarded — the real risk is Amazon's own gaming warning (a #1 in a deep subcategory is not a #1). ⚠️
  **A chart whose whole source set is one vendor cannot satisfy the rule — the all-language chart is the live case** — so
  it either finds an independent vendor, ships **marked single-source**, or does not ship; and the **footer's source
  list** is what makes that honest on screen. A **per-field priority** (title/author, publisher, price, pub date, cover,
  ISBN) is **recorded, never chosen at runtime**. Identity is ISBN-13 confirmed by **two** sources, else
  `identity: unresolved`. ⚠️ **Recording only the winner is not auditability** — each row carries the source ids that
  carried it **and the disagreements** (who said what, which rule picked). And **report, never silently drop**.
- [The thumbnail collage](issues/16-the-thumbnail-collage.md) — ⚠️ **the ticket's own premise was wrong**: the brief's
  thumbnail is judged at the **210 px a feed shows it at** (measured), not 320×180. At that size a 10×10 grid gives each
  cover **21 px** — a colour swatch — so the resolution is *"**all 100 covers appear; only the top few are legible**"*:
  a **hero row of 5** large covers, and the other 95 as a **deliberately dimmed mosaic** in the lower band (taking the
  backdrop's band, and its degrade behaviour). Inherits: a **dedicated composition, never a grabbed frame**; **3–6 words
  and one idea**; ⚠️ **YouTube owns the bottom-right (duration badge) and bottom strip (progress bar)**, and the mark
  stays **top-right at 128 px**; ⚠️ **the four thumbnails render before the four videos**; and **nothing lands in a
  package until it is whole**. Missing covers use the **same branded tile as the slide**, and a low **coverage count** is
  reported. The **`MAX_STILL_BYTES`** ceiling is checked, not hoped for.
- [The title, description and tags](issues/15-the-title-description-and-tags.md) — title is the brief's scheme,
  `Top 100 <Chart> | Week <ISO week> | <d MMM, yyyy>` (longest 64 chars vs YouTube's 100), and **no chart is primary**.
  ⚠️ **The description cannot hold the full list with all the fields** — `1. Title — Author — Publisher — ₹399` is
  ~6,800 characters against a **5,000** limit — so the rows **mirror the video's dwell weighting**: full rows for ranks
  1–10, compact (`Title — Author`) for 11–100, ≈4,600 characters with ~400 headroom. ⚠️ The fit is **checked, not
  hoped for**: if it will not fit the run **refuses** (the reel's rule), because "the full list" is the promise. The
  description carries its **own attribution** (sources + cover credit). Tags obey a **500-*character* budget, not a tag
  count** — appended while they fit, never "the first N". **Exactly 3 hashtags** (15 is a cliff, not a budget). Output
  is `metadata-<chart>.txt` **and** `.json`, mirroring the brief; the JSON names the video/thumbnail explicitly and
  carries the `bundle_hash`; the TXT is **plain text only**. The copy is a **pure function of the bundle** — and
  **authored, not translated**.
- [One report or four](issues/13-one-report-or-four.md) — ⚠️ the arithmetic decides it: 2 m 49 s per chart × 4 ≈ **11
  min** against a **3-minute cap**, so **four videos**, one per chart — which is also the only shape the title scheme
  (`Top 100 Bengali Books | Week 41 | …`) can express. ⚠️ **One bundle per week, four chart keys**
  (`store/<week>/facts.json`), with the **chart id read from input props** exactly as `lang` is — the brief's
  language-parity argument does *not* transfer, because four charts are **different data**, not the same data twice. ⚠️
  **A chart whose sources failed is an absent key** — the brief's own rule — which buys **partial delivery**: three ship,
  the fourth refuses, nothing is fabricated. Cap per chart; one ticker fetch for all four; **one** `store/<week>/`, not
  four; **four thumbnails, no master**; output at `output/books/<week>/<chart>/` mirroring
  `output/brief/<date>/<lang>/`; **idempotence per chart**. One run, four videos, and a chart waits only for **its own**
  sources.
- [The new-entry cap](issues/11-the-new-entry-cap.md) — **confirmed as the pairing from ticket 03**, not a choice
  between its own options: the **incumbency multiplier** makes churn *unlikely*, the **admission rule** (≤10 newcomers
  per chart, in score order) makes the cap *true*. ⚠️ A multiplier alone is a preference — twenty newcomers could still
  out-score every incumbent — so a hard number needs a bound. Deterministic (tie-breaks end in ISBN ascending) and
  replay-stable (`chart_logic: 1`); **per chart**; ⚠️ **week one bypasses it** or the "Top 100" would be 10 books. ⚠️
  The overflow lands on the **watchlist** — which is also where ticket 17 parks its single-source titles, so one list
  serves both.
- [The cadence and the trigger](issues/10-the-cadence-and-trigger.md) — **manual first, scheduled later** (ADR 0004's
  *"the command is already the interface"*): `books-brief build --week 2026-W41` by hand on the Mac, then a Linux timer
  (`Tue 09:00 IST`, `Persistent=true`). A week is keyed by the **ISO week** — `store/2026-W41/raw/*.json` and
  `facts.json` — which also settles ticket 15's *"Week 10"*: it is the ISO week, so October reads *Week 41*. ⚠️ ADR
  0004's lesson transfers as a **freshness guard per source** — each verified to have published **for the week being
  built**, never trusted because it is Tuesday; a stale scrape would yield a chart that is quietly last week's with a
  **zero-movement** diff (silent, plausible, wrong). ⚠️ **No holiday calendar, ever**; a refusal exits non-zero and
  writes nothing; the fire time is a **configured value, not arithmetic**. Re-render **replays** (ADR 0003); the upload
  is **idempotent on the bundle hash**, so a rebuilt week refuses rather than posting twice; `output/books/` must
  persist; privacy defaults to `private`.
- [Where it lives](issues/09-where-it-lives.md) — a **third nested product at `src/books-brief/`**, following
  `song-video` exactly: its own `pyproject.toml` (depending on `market-overview` as an **editable path source**), its
  own `uv.lock` / `package.json` / `remotion/` / `public/` / `tests/` / `docs/adr/`, and ⚠️ its own **committed
  `store/`** as the rebuild evidence. The package sits **directly** in the project (no inner `src/`), and the five
  seams are copied from `song-video/paths.py`: `project_root()` = `parents[1]`; `repo_root()` = **`store.root()` asked
  for, not assumed**; `data_root()` = the brief's resolver (**one env var for every product**); `shared_remotion()` =
  the brief's `remotion/` for fonts and the seeded PRNG; `mark_dir()` = the brief's `resource/brief/`, **one licensed
  mark for every product**. Namespaces: `resource/books/` (incl. the cover cache) and `output/books/<week>/<chart>/`.
  ⚠️ Three repo-wide consequences: the **README says "two products"**, **`./build` is the front door over both**, and
  **`testpaths` must be declared** or a bare `pytest` walks into the nested suite. Six ADRs listed.
- [The background ticker](issues/08-the-background-ticker.md) — ⚠️ **depend on the library, not on another product's
  artefact**: fetch the index scoreboard through `market_overview.fetch.tradingview` (the client), **not** the brief's
  committed `store/<date>/facts.json` — which would make the run conditional on the brief having run. Raw response
  committed to `store/<week>/raw/tradingview.json`. Rows = the brief's index scoreboard; label keys are **slugs in
  `facts.json`, strings in the renderer's tables**; `*INR` rows must use `NEUTRAL`, never `tone()`. The band carries
  the **session clock** so a stale ticker cannot masquerade as live. ⚠️ **Missing data degrades, it does not abort** —
  a deliberate divergence from the brief, where a short scoreboard *is* fatal because it is the content; here it is
  decoration, so the band is omitted entirely.
- [The slide layout](issues/07-the-slide-layout.md) — the frame keeps the host repo's two reserved regions: the mark
  owns the **top-right 260×160** (⚠️ rendered from the brief's **mark file** via `mark_dir()`, not by importing
  `Brand.tsx` — ticket 09) and the **footer is the disclosure register**.
  Registers: header = *which chart*; main = *the book* (cover left 34 %, data right); ticker band = *the world*;
  footer = *how we know*. Type scale anchored to `Card`'s own numbers with **one dominant element — the rank at 220**.
  ⚠️ **NEW must not be green** — `GREEN`/`RED` mean up/down, and a new entry has no direction, so NEW is an inverted
  chip from neither half of the pair. ⚠️ **`enter()`'s 0.4 s default would eat 40 % of a 1.0 s tail slide** — span
  becomes `min(0.4, dwell × 0.15)`. Fallbacks ruled: title 2-line clamp then ellipsis (full title survives in the
  description), author 1 line, missing price `—`, missing cover a **branded initial tile**, NEW replaces Δ (never
  `▲0`), missing pub date omitted without leaving a hole.
- [The video format](issues/06-the-video-format.md) — **one composition, two outputs**: a **16:9 video** primary, with
  the slides renderable as **stills** (4:5/1:1 carousel) for free from the same component. **One book per slide, all
  100, every field present** — the time problem solved by **rank-weighted dwell** (1–10 at 3.5 s … 61–100 at 1.0 s),
  totalling **2 m 49 s** against the brief's **3-minute cap**. **Music-backed, no voiceover** — reuse the bed contract;
  narration would be a separate product decision. ⚠️ **Below ~rank 50 a slide is a glance, not a read** — which is why
  the description must carry the full list. ⚠️ **400 slides ≈ 11 min**, so the 3-minute cap and four charts cannot
  both hold in one artefact → flagged into ticket 13.
- [The enrichment pipeline](issues/05-the-enrichment-pipeline.md) — covers are **download-and-embed, never hotlinked**,
  **cached by ISBN** in the data root (`resource/books/covers/<isbn13>.jpg`) with the **source URL + hash recorded in
  `facts.json`** so a rebuild works without committing 400 images a week. Google Books first, Open Library fallback
  (⚠️ `http`→`https`, strip `edge=curl`, raise `zoom`; Open Library needs `?default=false` so a missing cover 404s
  rather than rendering blank). Pub date renders **only the precision that exists** (`14 Oct 2026` / `Oct 2026` /
  `2026` / omitted) — ⚠️ NYT's `published_date` is the **list's** date, not the book's. ⚠️ **Amazon.in gives no ISBN**,
  so the pipeline is also **identity resolution** (`title + author` → ISBN-13, ISBN-10 normalised), which must be
  corroborated by two sources or marked `identity: unresolved`. Publishes a **cover-coverage count** for ticket 16.
- [The best price strategy](issues/04-the-best-price-strategy.md) — **"best price" = the lowest verified offer across
  the retailers we can legitimately reach, with the retailer named** — and ⚠️ **never labelled "best" unless it was
  actually compared**. Primary: **Amazon.in's "N offers from ₹X"**, which arrives **free with the chart source**
  (no extra fetch). Second retailer: the **Flipkart Affiliate API** (⚠️ needs affiliate approval — an operator
  prerequisite), which is what makes "best" mean something. Fallbacks: Google Books `retailPrice` (ebooks only), then
  the publisher list price **labelled MRP**. INR always; the **format is named on the slide**; a missing price is a
  **dash, never ₹0**; and **price never affects rank**. ⚠️ Honest limit: "best" means Amazon + Flipkart, not every
  Indian retailer.
- [The chart logic](issues/03-the-chart-logic.md) — a deterministic, four-step rule: normalise each source to a
  **position** (`(n+1−rank)/n`), weight it by **depth** (`min(1, n/100)` × a recorded per-source weight), **sum** —
  which *is* the corroboration bonus, so a single-source title can never out-rank a three-source title — then apply an
  **incumbency multiplier** (`1 + 0.15·min(weeks_on_chart, 8)`). ⚠️ The ≤10 NEW cap is an **admission rule** (newcomers
  admitted in score order, ≤10 per chart, the rest watchlisted), because a multiplier makes churn unlikely but only a
  rule makes it bounded. Tie-breaks end in **ISBN ascending**, so the order is total. Versioned as `chart_logic: 1`.
  ⚠️ **Week one must bypass the cap** or the chart would be 10 books, not 100.
- [The source union](issues/02-the-source-union.md) — ⚠️ **almost nothing Indian is weekly**: Amazon.in ("updated
  frequently") is the workhorse, Anandabazar Patrika is the *only* weekly Bengali chart, the Nielsen India list is on
  sabbatical, Dainik Jagran Hindi is **quarterly**, ICv2 is **monthly**. Bengali ✅ (Anandabazar + Amazon.in, both
  scraped — Anandabazar needs `curl_cffi`), Comics ✅ (Amazon.in + NYT `graphic-books-and-manga` weekly), all-language
  ⚠️ (Amazon.in ×N languages, **no authoritative list**), English ⚠️ **conditional** — India-market is single-source,
  which contradicts the brief's "as many sources as possible" → raised as ticket 19. **Most of the product is
  scraping**, so the corroboration gate is load-bearing.
- [The four charts](issues/12-the-four-charts.md) — all four are **Top 100, India-market**: Bengali (Bengali-language),
  English (*India-market*, ⚠️ flagged call), Indian all-language (the superset, incl. Bengali and English), and Comics
  (*as India buys them* — Indian + manga + global, ⚠️ flagged call). Bengali renders in Bengali, the rest in English.
  ⚠️ A weekly Bengali chart **does** exist (Anandabazar Patrika, but 403-protected); the Nielsen India all-language
  list is **on sabbatical**, so that chart has no authoritative source.
- [The comparison window](issues/01-the-comparison-window.md) — **week over week**, diffed against the previous
  committed week's chart **per chart**; NEW = an ISBN absent from it. Every week is kept, so month-over-month is the
  *same diff four weeks back* — the storage decision is identical either way, and only the display offset differs.
- [The chart relationship](issues/14-the-chart-relationship.md) — *"Indian all-language"* is a **superset** of the
  Bengali and English charts (an overall view beside its per-language breakdowns), so a title may appear in more than
  one chart — which makes **rank chart-local**, makes the ≤10 NEW cap per chart, and makes the dedupe key
  **chart + ISBN**.

## Not yet specified

<!-- in-scope fog: real, but not yet sharp enough to be a ticket -->

- **A second weekly Bengali ranking.** ⚠️ `bengali` has **one** vendor (Rokomari), and one vendor cannot corroborate
  anything — so the chart ships **absent**. ⚠️ Anandabazar's weekly list was never located, and ticket 29 left that as a
  **search** rather than a correction: it is the one thing that would bring the chart back.
- **A date for Rokomari.** The list parses (60 rows) and its address is settled (ticket 29); only its **vintage** is
  unknown, which is what makes `freshness.guard` refuse it. ⚠️ Finding a date is not a parser change.
- Retention — how many weeks of `store/<week>/` snapshots are kept, and whether old weeks are pruned
- Genre sub-charts (fiction / non-fiction / children's) *within* each of the four charts — a *possible* feature, not a
  decision implementation needs

⚠️ **Graduated out of the fog:** the **publish targets** are **ticket 24**, the **operator prerequisites** are **ticket
25**, and **snapshot retention** is **ticket 28** — retention because ticket 23 made it **load-bearing rather than
tidy**.

⚠️ **And one item left the fog by being answered:** the price layer's refresh cadence — ticket 04 established that the
price **arrives with the chart source**, so it refreshes **per run**, and there is nothing to decide.

### ⚠️ Reopened, then closed — the frontier was not empty (2026-10-14)

⚠️ **This map said *"the frontier is empty — the map is done"*, and that was wrong.** The claim rested on every ticket
being *resolved*, which is not the same as every ticket being **checkable** — and three of them were decided from
assumption about sources nobody had fetched.

The implementations' own recordings settled it, and **three of the four charts declared source lists their vendors do not
publish**:

| Chart | Declared | What the vendor publishes |
|---|---|---|
| **All-language** | `amazon-in/hindi`, `…/bengali`, `…/tamil`, … ×9 | ⚠️ **one** mixed-language list, `…/gp/bestsellers/books/86946561031/` |
| **Bengali** | `amazon-in/bengali` | ⚠️ **no list exists** — only an unordered search, with no rank badges at all |
| **English** | `pw/fiction`, `pw/nonfiction` | ⚠️ PW is **paywalled**; its free pages are a 2012 archive |

⚠️ **This is the map's own rule applied to itself.** Ticket 02 wrote *"a chart with no source is a **finding**, not a
failure — and the honest outcome may be that only some of the four charts are buildable."* ⚠️ The finding arrived, and
**ticket 29** is what consumed it.

⚠️ **What did *not* change:** every design decision holds. `charts.Listing`, the corroboration gate, the freshness guard,
the `Page` contract and the render layer are all correct — and ⚠️ **none of the drifts fails silently**, because a vendor
that produces nothing is a missing source and a chart missing a source is absent. The map's design was right; three of its
**source tables** were not.

⚠️ **And this map's closing claim — that writing `src/books-brief/` is *past* the destination — was overtaken.** The
product was built, and its own failing suite is what turned the three source tables from a suspicion into a list. ⚠️ That
is the last thing the map got wrong, and the correction is recorded here rather than deleted.

## Out of scope

- **Implementing the product.** The destination is a spec; writing `src/books-brief/` is past it, and belongs to a
  fresh effort that consumes this map.
- **Paid data.** A Nielsen BookScan subscription is ruled out — only sources that are free, or licensed for reuse,
  are in play.
