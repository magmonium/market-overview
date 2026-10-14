# The six-month sales and review basis

Type: grilling
Status: resolved

## Question

*"make sure all this chart will only focus based on sell for last 6 month and user review together"* — ⚠️ **this changes
what the chart ranks, not just how it ranks.** Everything below follows from it.

### ⚠️ Finding 1 — the sources do not sell a six-month figure

Ticket 02's sources publish **weekly ranks**, not six-month sales. Amazon.in's list is *current*; Anandabazar's and
NYT's are weekly. A six-month sales total is a **Nielsen BookScan** product, and Nielsen is ruled out of scope.

**But three things give a window anyway:**

1. ⚠️ **Our own committed snapshots.** Ticket 10 keeps `store/<iso-week>/` for **every** week, and ticket 01 keeps them
   all. Twenty-six of them **are** a six-month window — and the aggregate of a title's weekly positions (plus units where
   a source gives them) is a six-month signal we can compute **and defend**.
2. **PW / Circana publishes `units sold` and `YTD`** per title — a real sales figure, in the one source that carries it.
3. **Cumulative popularity signals** — Amazon.in's **rating count**, Google Books' `ratingsCount` — which are not
   six-month sales, but are long-window and free.

### ⚠️ Finding 2 — the bootstrap: a six-month ranking needs six months of running

If the window is built from our own snapshots, then **weeks 1–25 have no six-month window**. That is not a detail — it
decides whether the product publishes in week 1 or week 27.

### ⚠️ Finding 3 — reviews are cumulative, and a raw mean is a trap

Reviews accumulate over a book's **whole life**, so they measure *popularity*, not recent sales — fine, as long as the
chart says so. ⚠️ But **a rating without its count is meaningless**: 5.0 from 3 reviews must not outrank 4.6 from 50,000.
The review term must be **credibility-weighted** — a Bayesian average shrinking a thin rating toward the global mean —
or the chart rewards obscurity.

⚠️ And reviews are gameable in a way sales are not (review bombing, incentivised reviews). That is ticket 17's problem,
and it is worth naming here rather than discovering it later.

### What this does to the rest of the map

- ⚠️ **Ticket 03's score is no longer a weekly-rank aggregate** — it gains a **six-month sales term** and a
  **credibility-weighted review term**.
- ⚠️ **Ticket 01's two windows separate.** The **ranking window** is six months; the **Δ window** stays weekly. They
  were one thing and are now two.
- ⚠️ **Ticket 18's "week one" becomes a 26-week ramp**, not a single baseline week.
- ⚠️ **Ticket 11's ≤10 NEW cap gets easier** — a six-month basis is far stickier than a weekly one — which is worth
  knowing *before* the cap is tuned.
- ⚠️ **Ticket 15's title and description must state the basis** — `Top 100 Bengali Books` no longer says what it ranks.
- **Ticket 02** gains a question: which of the three window sources is authoritative, and what happens when they
  disagree.

## Deliverable

The ranking formula — sales term, review term, and their weights — and the **bootstrap rule**.

## Answer

**The basis is a rolling six-month window mixing sales and reviews — and the *collection* is what changes to serve it.**

### What the brief clarified

*"my intention was mix review plus sales data for longer duration, not one month."* So this is neither a monthly chart
nor a weekly one: the ranking asks **what has sold, and how well it has been reviewed, over the last six months**.

### ⚠️ The collection rule — the part that actually changes

The sources publish a **current** snapshot, so a six-month window **cannot be fetched — it has to be accumulated**.
Which means every run must record, per title, **the signal and the date it was observed**:

```
store/2026-W41/facts.json
  └── bengali → [ { isbn, rank, units?, rating, ratings_count, observed: "2026-10-14" }, … ]
```

⚠️ **That is the "collect data that way."** The snapshot is no longer just *this week's chart*; it is **this week's
evidence for a six-month window**. Ticket 10 already keeps every week and ticket 01 already keeps them all — this ticket
is what gives that habit a purpose **beyond** the Δ diff.

### The two signals, and where each comes from

| Signal | Source | Window | Caveat |
|---|---|---|---|
| **Sales** | PW / Circana `units sold` and **`YTD`** | the one genuinely multi-month sales figure | © Circana; US-skewed |
| **Sales** (proxy) | our own weekly ranks + units, accumulated | six months once 26 weeks exist | a *rank* aggregate, not units |
| **Reviews** | Amazon.in **rating + rating count**; Google Books `averageRating` + `ratingsCount` | cumulative, whole life | ⚠️ popularity, not recent sales |

### ⚠️ The review term must be credibility-weighted

A raw mean is a trap: **5.0 from 3 reviews must not outrank 4.6 from 50,000.** So the review term is a **Bayesian
average** — a thin rating is shrunk toward the global mean by its count, and has to earn its distance.

⚠️ And reviews are **cumulative over a book's whole life**, so they measure *popularity*, not the six months. That is
acceptable **only because the chart states it** — which ticket 15 now does.

### ⚠️ The bootstrap: weeks 1–25 ship, stating the window they have

Because the window is accumulated, **weeks 1–25 cannot have six months of it**. The decision is to **ship from week 1
and state the window actually used** — *"based on 7 weeks of sales and reviews"* — growing into a true six-month chart
by week 26.

⚠️ Holding until week 26 is truer to the brief and publishes **nothing for half a year**. And PW's `YTD` is used **where
it exists** rather than as a substitute, because `YTD` is a **calendar-year** figure, not a rolling six months.

⚠️ **This bootstrap was not explicitly chosen** — the recommended option is taken, and it is reversible: the chart's
stated window is a data value, so switching to a hold costs one condition.

### What it does to the rest of the map

- **Ticket 03** — the score gains a six-month sales term and a credibility-weighted review term *(amended)*.
- **Ticket 01** — the ranking window (six months) and the Δ window (weekly) are now two things *(amended)*.
- **Ticket 18** — week one is a **26-week ramp**, and the chart states its window *(amended)*.
- **Ticket 15** — the title and description state the basis *(amended)*.
- **Ticket 11** — a six-month basis is far stickier than a weekly one, so the ≤10 NEW cap gets **easier** — worth
  knowing *before* it is tuned.
- **Ticket 02** — gains a question: which window source is authoritative when PW's `YTD` and our own accumulated ranks
  disagree.
