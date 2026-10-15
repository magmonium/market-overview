# 0001 — The four charts, and the markets they actually cover

- Status: accepted
- Date: 2026-10-14
- Amended: **2026-10-15** — the English chart's market moved from **US** to **Worldwide**. See the [Amendment](#amendment-2026-10-15) at the end.

## Context

The brief asked for four Top-100 charts — **Bengali**, **English**, **Indian all-language** and **Comics** — and the
natural first reading is that all four are *India-market*. That reading survived until the sources were actually
looked at.

Three findings killed it:

- ⚠️ **Almost nothing Indian is weekly.** Amazon.in's bestseller lists are the workhorse; Anandabazar Patrika publishes
  the *only* weekly Bengali chart; the Nielsen India list is on sabbatical; Dainik Jagran's Hindi list is **quarterly**;
  ICv2 is **monthly**. A weekly product and an India-only scope are in tension, and the tension had to be resolved
  rather than absorbed.
- ⚠️ **India-market English cannot be built at all.** It has exactly **one** weekly vendor, and ADR 0004 requires two.
  The chart would be permanently absent — not weak, *absent*.
- **The brief then moved two boundaries itself**: the Bengali chart was asked to include **Bangladeshi** titles, and
  the comics chart to be **worldwide**.

## Decision

Four charts, and each one's market is what its sources can honestly support:

| Chart | Market | Why |
|---|---|---|
| **Bengali** | **Bangladesh** | one Bangladeshi list; the Indian half could not be declared (ticket 29) |
| **English** | **Worldwide** | NYT, Indie and the **four Amazon stores** — ⚠️ **amended 2026-10-15** |
| **Indian all-language** | **India** | Amazon.in's one mixed-language ranking, which is one vendor |
| **Comics** | **Worldwide** | NYT's `graphic-books-and-manga` (**monthly**) plus **eight Amazon storefronts** — the US, the UK, Canada, Germany, France, Italy, Spain and India — ⚠️ **amended 2026-10-15**, tickets 33 and 34 |

⚠️ **And every chart states its scope** — the **footer's source list** and the **description's attribution** name the
vendors, so a reader can see what was and was not consulted.

## Consequences

- ⚠️ **Three charts carry a scope caveat, and that is the product's honest shape rather than three defects.** A weekly
  chart built from free sources is a **US-and-India view of the world**; saying so is what makes it trustworthy.
- ⚠️ **"Global" is never claimed without the sources to back it.** ⚠️ **Superseded for the English chart on 2026-10-15**:
  it was *US* English, and is now genuinely **worldwide** across four English-speaking countries' stores — see the
  Amendment. ⚠️ The rule that produced the old sentence still holds, and is the reason the move was allowed: a market is
  claimed only where the **sources** support it.
- ⚠️ **The all-language superset holds over the Indian portion only.** A Bangladeshi Bengali title sits in the Bengali
  chart and **not** in the all-language chart, so the Bengali chart carries an **overhang** — and the dedupe key is
  **chart + ISBN**, never ISBN alone.
- ⚠️ **The country and language labels render only where they vary** (ADR 0005's sibling rule). ⚠️ As of 2026-10-15 the
  English chart shows the **country** — four of them — and still not the language.

## Amendment (2026-10-15)

⚠️ ⚠️ **The English chart's market changed from *US* to *Worldwide*, because the operator asked for an English chart that
spans the English-speaking countries.** ⚠️ The decision above was right about the evidence it had — NYT and Indie are US
lists, and calling a US-list chart *global* would have been exactly the overclaim this ADR exists to prevent. **What
changed is the sources, not the rule.**

⚠️ **The only free, weekly, per-country English bestseller lists that exist are Amazon's own stores.** The other two
candidates were checked and are **paywalled**: **Books+Publishing** (Australia) and **The Bookseller** (UK — and only its
top five is free). So the chart reads the four Amazon *Books* bestsellers — `amazon.com`, `amazon.co.uk`, `amazon.ca` and
`amazon.com.au` — beside NYT and Indie, and its rows now carry `us`, `gb`, `ca` and `au`.

⚠️ ⚠️ **And that needed one rule change, which is recorded here because it is a change to a guarantee.** An Amazon
bestseller page carries **no date**, so `freshness.guard` — whose rule is *"undated is stale"* — discarded every Amazon
row and made **every chart declaring one absent**. ⚠️ That is why `comics` and `all-language` never shipped, and why the
English chart could not have gained an international list at all. The distinction is now explicit in `charts.LIVE`: a
**live ranking** has no stale version to catch, so it is exempt from the *date* check — while a live store that returns
**nothing** is still a missing source, and its chart is still **absent** (ticket 18's spine). ⚠️ The exemption is opt-in
and defaults off, so every other caller keeps the old rule exactly.

⚠️ **What this does not change.** The country and language labels still render only where they vary; a market is still
claimed only where the sources support it; and every declared list still has to say where it is. ⚠️ The English chart is
`Worldwide` because four countries' lists are in it — not because "worldwide" reads better than "US".

## Amendment (2026-10-15, ticket 33) — the comics chart's monthly half

⚠️ ⚠️ **The comics row above was built on a cadence that is not true.** Ticket 22 named NYT's `graphic-books-and-manga`
**weekly** — *"the one weekly ranking vendor"* — and the chart's source set rests on that reading; the recorded payload
says `"updated": "MONTHLY"` with `bestsellers_date: 2026-10-03`, the first Saturday of the month. ⚠️ Measured against a
ten-day week, a monthly list is fresh for **one week in four**, and ticket 18's absent-not-smaller rule then made the
chart **absent** — which is why `comics` was missing from `2026-W41` while Amazon.in had answered it thirty rows.

⚠️ **A list now declares its `cadence`** (`charts.CADENCES`), and a monthly one is fresh for **the month it was published
in**. ⚠️ A *previous* month is still stale, so the freshness guarantee is **narrowed rather than removed** — and the
declaration is refused if it is not a cadence we know, because a misspelt `"monthly"` would otherwise keep the weekly rule
silently.

⚠️ **And the chart gained a vendor rather than losing one.** Amazon.com's **print** Comics & Graphic Novels bestsellers
(node `4366`: 30 ranked cards, **22 real ISBN-13s**) joins NYT and Amazon.in, so the US half is covered by a **live**
ranking *and* by an editor's **monthly** one. ⚠️ **The market stays `Worldwide`**, and for the reason this ADR gives
everywhere else: the sources span the US and India, which is what the claim rests on — ⚠️ and Amazon.in's node carries
children's and activity books beside comics, so the chart's *scope* is honest while its *content* is the vendor's own.

⚠️ **One consequence for the market claim, recorded rather than tidied.** A chart that ships every week from a monthly
list repeats that list's ranking for the rest of the month, so its week-over-week Δ reads **zero** for three weeks in
four. ⚠️ That is ticket 10's own named symptom — *"the week-over-week diff would report zero movement, which reads as
nothing happened"* — and it is accepted here because the alternative is no comics chart at all. ⚠️ The live vendors are
what make the movement real; the monthly list is the editor's view, not the weekly signal.

## Amendment (2026-10-15, ticket 34) — and it is eight storefronts, not two

⚠️ ⚠️ **The operator asked for *"different counrty europe amerika uk india and create list"*, and the answer is one list
per country** — so the comics chart reads **eight live storefronts** beside NYT: the US, the UK, Canada, Germany,
France, Italy, Spain and India. ⚠️ **This is the first time `worldwide` has been more than a two-country claim**, and it
is earned the way this ADR requires: by the **sources**, each fetched before it was declared.

⚠️ ⚠️ **It also broke two things that were invisible until the list was widened**, and both are recorded because the
product's history is a list of exactly this shape:

- ⚠️ **A store the currency table does not name prints an unsigned number.** `MARKETPLACES` is what supplies a row's
  currency, and the four European stores were missing from it — so their prices arrived with `currency=""`, the
  documented *unknown* degrade, in which the amount is **kept** and printed bare. ⚠️ Measured: `amazon.de` would have
  shipped **`5711.66`** with no symbol, which is ticket 19's failure one step further from being visible. ⚠️ The rule was
  correct and tested; the **table** fell behind, and the invariant is now asserted in one test that reads both.
- ⚠️ **Eight requests in a burst get one throttled, and one empty store costs the whole chart.** `amazon.de` answered
  `200`, a valid title and **no cards** while the same address gave 30 cards seconds later. ⚠️ By ticket 18's spine rule
  that is not "one country missing" — it is **no comics chart** — so `amazon.fetch` now pauses between storefronts. ⚠️ A
  **pause, not a retry**: a retry would hide a genuine outage behind a second attempt.

⚠️ **And what the market claim still owes the reader.** Three of the eight stores (`amazon.com`, `.co.uk`, `.de`) price
*this viewer* in **HUF**, so their rows carry **no price** — a chart whose captions are present for five countries and
absent for three, which is the honest degrade rather than a wrong sign. ⚠️ The **language** label also draws here for the
first time: five values, because a storefront ranks its own country's editions (*Gregs Tagebuch*, *Lou ! Sonata*,
*One Piece*, *Policán*).
