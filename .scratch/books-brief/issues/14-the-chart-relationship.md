# The chart relationship

Type: grilling
Status: resolved

## Question

How do the Bengali, English and Indian all-language charts relate — specifically, may one book appear in more than
one chart?

## Answer

**SUPERSET.** *"Indian all-language" is the whole Indian market.* It is the **overall view**, and the Bengali and
English charts are its **per-language breakdowns** — so a title may legitimately appear in two charts.

Consequences that bind the rest of the map:

- The three book charts can **share one source set**: the all-language chart is the union of everything, and the
  Bengali and English charts are **filters over it**. That is *one* fetch feeding three charts — not three unrelated
  pipelines.
- ⚠️ A book's **rank is chart-local**. A title can be #7 in the Bengali chart and #44 in the all-language chart, and
  those are two different facts. Δ and NEW (tickets 01, 03) must therefore be computed **per chart**, not per book.
- The ≤10 NEW cap (ticket 11) is **per chart**, and the same title can be NEW in one chart while an incumbent in
  another — which is not a contradiction, it is the superset working.
- ⚠️ Dedupe (ticket 03) must **not** collapse a title across charts. The dedupe key is **chart + ISBN**, never ISBN
  alone, or the all-language chart would silently lose every title that is already in a language chart.

### ⚠️ In doubt — the Bengali chart is no longer India-only

The brief has asked the Bengali chart to **include Bangladeshi titles** (ticket 20). ⚠️ **A superset cannot contain what
its own subset excludes**: if the all-language chart is *Indian*, a Bangladeshi Bengali title sits in the Bengali chart
and **not** in it — so the superset holds only over the Indian portion. Either the all-language chart stops being Indian,
or the relationship becomes *"superset over the Indian market, plus a Bengali overhang"*. Settled in ticket 20.
