# The chart logic

Type: grilling
Status: resolved
Blocked by: 01, 02

## Question

How do N heterogeneous lists — different lengths, different vendors, different currencies of prestige — become **one
ranked Top 100**?

This is the user's *"slide logic to pick up 100 from them and rank"*: a selection rule, written down, not an
implicit concatenation.

It needs a rule for each of:

1. **Normalisation** — a #1 in a 10-book list and a #1 in a 100-book list must not score the same raw rank.
   *(Proposal: `points = (size + 1 − rank) / size`, so both score ≈ 1.0.)*
2. **Weights** — does Circana's units-sold authority outrank NYT's editorial list? *(Proposal: a per-source weight,
   configurable, recorded in `facts.json`.)*
3. **Dedupe key** — ISBN-13 primary; normalised title + author as the fallback.
4. **Tie-breaks** — *(proposal: weeks-on-chart desc, then units desc, then title asc)* — and the ordering must be
   deterministic, or the same week renders differently twice.
5. **Output** — the ranked chart, written to `store/<week>/facts.json` and committed, so next period can diff it.
6. ⚠️ **The new-entry cap** — at most **10** titles may be new (ticket 11). This is a constraint the rule must
   *satisfy*, not a display setting applied afterwards: a churny merge and a ten-entry cap cannot both hold unless
   incumbency is part of the ranking.

⚠️ **Nothing reaches the ranking that has not passed the corroboration gate** (ticket 17). The chart logic ranks an
already-authenticated candidate set; it authenticates nothing itself.

⚠️ The chart logic and the comparison window (ticket 01) are one design: the snapshot the diff reads is the
snapshot this rule writes. It is also one design with the new-entry cap (ticket 11) — the cap is what makes the
ranking stable enough to diff at all.

## Answer

The rule, in order. Every step is **deterministic** — ⚠️ the same inputs must always produce the same chart.

### 0 — Before ranking: the gate
The candidate set has already passed the **corroboration gate** (ticket 17). The chart logic ranks authenticated
candidates; it authenticates nothing itself.

### 1 — Normalise each source to a comparable *position*
```
points(s, rank) = (n_s + 1 − rank) / n_s          # (0, 1]
```
A #1 in a 10-book list and a #1 in a 100-book list both score 1.0. Position, not prestige.

### 2 — Weight a source by its *depth*
⚠️ A #1 in a shallow list is a weaker signal than a #1 in a deep one, and this matters most in the **all-language**
chart, where Amazon.in's per-language categories have wildly different depths (ticket 02).

```
weight(s) = w_source × min(1, n_s / N_ref)        # N_ref = 100
```
A 100-deep list counts fully; a 20-deep list counts a fifth. `w_source` is **per source and recorded in
`facts.json`** — so the weights are auditable, not folklore.

### 3 — Sum, which *is* the corroboration bonus
```
score(book, chart) = Σ over every source carrying it of ( weight(s) × points(s, rank) )
```
A title carried by three lists accumulates three terms; a title carried by one accumulates one. ⚠️ **No separate
"corroboration multiplier" is needed — corroboration is what the sum measures.** It also means a single-source title
can never out-rank a three-source title at the same position, which is precisely what *authentic* should mean.

### 4 — Incumbency, so the chart is stable and not merely correct
```
final_score = score × (1 + γ · min(weeks_on_chart, W_cap))        # γ ≈ 0.15, W_cap = 8
```
An incumbent is harder to dislodge than a newcomer at the same raw score.

### 5 — ⚠️ The ≤10 NEW cap is an **admission rule**, not a multiplier
A multiplier makes churn *unlikely*; only a rule makes it *bounded*. So:

```
1. Incumbents (titles in last week's chart) keep their places, in final_score order.
2. Newcomers are admitted in final_score order — at most 10 per chart.
3. Every further newcomer is held on the watchlist until a slot frees.
4. Remaining slots are filled from incumbents, in final_score order.
```

⚠️ This is the honest reading of *"not more than 10"*: the incumbency multiplier (step 4) is what makes the cap
**rarely bite**; the admission rule (step 5) is what makes it **true**. Ticket 11's options 2 and 3 are therefore not
alternatives — they are the *preference* and the *guarantee*, and the rule needs both.

### 6 — Tie-breaks, so the order is total
1. higher `final_score`
2. carried by **more sources**
3. longer `weeks_on_chart`
4. lower best-ever rank
5. **ISBN ascending** ← a total order; **never** a coin flip

### 7 — Applied **per chart**
The rule runs four times, once per chart (ticket 12). For the all-language chart the "sources" are the per-language
categories, so step 2 does the heavy lifting. Dedupe is **chart + ISBN** (ticket 14) — a Bengali title may appear in
both the Bengali and the all-language chart, with a **different rank in each**.

### 8 — Output: the committed snapshot
`store/<week>/facts.json`, committed (ADR 0003), carrying **per chart**:
`rank` · `rank_last_week` · `delta` · `is_new` · `weeks_on_chart` · `score` · **the source ids that carried it** ·
plus the **source list, the weights, and `chart_logic: 1`**.

⚠️ The `chart_logic` version matters: a change to the rule changes the chart, so a re-run of an old week must
reproduce the **old** chart, not the new one.

### ⚠️ Amended — the score is no longer a weekly-rank aggregate

The brief now asks every chart to rank on **sales over the last six months together with user reviews** (ticket 23). So
the sum above is **not** the whole score any more: it gains a **six-month sales term** and a **credibility-weighted
review term**, and the weekly lists become *inputs to a longer-window signal* rather than the ranking itself.

⚠️ And the two windows **separate** — the **ranking window is six months**, while the **Δ window stays weekly**
(ticket 01). They were one thing and are now two.

⚠️ The step order above survives; only the score changes. Normalisation, depth-weighting, the corroboration bonus, the
incumbency multiplier and the admission rule all still apply to whatever the score becomes.
With no previous chart there are no incumbents — **every** title is a newcomer, so step 5 would admit only ten and the
chart would be 10 books, not 100. Week one must therefore **bypass the admission cap** and ship as a stated baseline
(carried into ticket 18).
