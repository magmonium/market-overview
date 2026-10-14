# The snapshot retention

Type: grilling
Status: resolved

## Question

This sat in the fog as housekeeping — *"how many weeks of `store/<week>/` are kept, and whether old weeks are pruned."*
⚠️ **Ticket 23 stopped it being housekeeping.**

The six-month ranking window is **accumulated from our own committed snapshots**, because the sources publish only a
current view. So:

⚠️ **Pruning is not storage management — it silently shrinks the ranking window.** Keep 12 weeks and the "six-month"
chart can never look back further than twelve, and **nothing anywhere would say so.** The window would simply stop
growing — which is the exact failure ticket 18's *"stated baseline"* and ticket 23's *"state the window"* rules exist to
prevent.

## Answer

**Keep every week. There is no pruning.**

Three reasons, and the first is now load-bearing rather than tidy:

1. ⚠️ **The ranking depends on it.** Ticket 23's six-month window is built from `store/<week>/facts.json`, so a pruned
   snapshot is a **shorter chart** — and the chart would have to say so. There is no reason to accept that.
2. ⚠️ **`store/` is the evidence, not the cache.** ADR 0007 is explicit — *"`store/` never was gitignored, and that is
   the difference between the tool's evidence and its data"* — and the brief keeps **every date** for the same reason.
   A week's raw responses are the only record of what a source actually said, and *"the raw responses are the only
   evidence if a figure is ever disputed."*
3. ⚠️ **A re-run overwrites a snapshot** (ticket 18), so **git is the version history**. Pruning would delete the only
   copy of the week before last.

⚠️ **What this costs, stated rather than implied:** `store/` grows by roughly **four charts × 100 rows plus the raw
source responses** every week, committed. That is the price of a chart that can be rebuilt, audited and diffed — and it
is the same price the brief already pays, **per day** rather than per week.

⚠️ **If it ever must be bounded**, the bound is **not "N weeks"** but **"the window the chart claims"** — 26 weeks
minimum — and shrinking below it is a **change to the product**, not to storage.
