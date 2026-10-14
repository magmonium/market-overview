# The new-entry cap

Type: grilling
Status: resolved
Blocked by: 01, 02

## Question

⚠️ **A hard constraint from the brief: the chart shows at most 10 NEW entries.**

A multi-source union is *volatile* — several lists of different lengths disagree week to week, and a naive merge can
churn dozens of titles in and out. Ten is therefore not a display setting; it is a property the **chart logic**
(ticket 03) has to be built to guarantee.

The question is *how* it is guaranteed, and what becomes of the eleventh newcomer.

## Options

1. **Presentation cap** — the chart may contain any number of new titles, but only the ten highest-scoring wear the
   NEW badge; the rest render with a plain Δ. Honest to the data, but fifteen genuinely-new books then sit in the
   list looking old.
2. **Stability rule (incumbency)** — the ranking itself guarantees it: an incumbent carries a persistence bonus, and
   a newcomer must out-score the weakest incumbent by a margin to displace it. At most ten can be new **by
   construction**. *(recommended — the cap becomes a property of the chart, not of the badge)*
3. **Hard admission cap** — only ten newcomers are admitted per week; further newcomers are held in a **watchlist**
   and cannot enter the 100 until a slot frees.
4. **Rollover queue** — newcomers beyond ten are admitted the following week, first-come-first-served.

⚠️ **Settled by ticket 03.** The chart logic resolved this ticket's mechanism rather than choosing between its options:
the **incumbency multiplier** (option 2) is the *preference* that keeps the chart stable, and the **admission rule**
(option 3) is the *guarantee* that bounds newcomers at ten. A multiplier alone makes churn unlikely, not impossible —
and "not more than 10" needs a bound. This ticket now only needs to confirm that pairing.

⚠️ **Per chart.** The cap applies to each of the four charts (ticket 12) — ten NEW in the Bengali chart, ten in the
English chart, and so on — unless ticket 13 makes the four into one.

⚠️ Whatever is chosen must be **deterministic** and must survive a replay: the same week, re-rendered, must produce
the same ten.

## Answer

**Confirmed: the pairing from ticket 03 stands — and this ticket's own options 2 and 3 were never alternatives.**

The brief's constraint is *"new entry should not be more than 10"*. Ticket 03 satisfies it with **two** mechanisms, and
each does a different job:

| Mechanism | Job | Where |
|---|---|---|
| **Incumbency multiplier** — `final_score = score × (1 + γ·min(weeks_on_chart, W_cap))` | makes churn **unlikely** | ticket 03, step 4 |
| **Admission rule** — newcomers admitted in score order, **at most 10 per chart**, the rest watchlisted | makes the cap **true** | ticket 03, step 5 |

⚠️ **Why both, and why neither alone suffices.** A multiplier alone is a *preference*: a week where twenty newcomers
each out-score every incumbent would still produce twenty new entries. The constraint is a **hard number**, so it needs
a **bound**, and only an explicit rule supplies one. Conversely, the rule alone would admit ten newcomers every week
even in a stable market — churn for churn's sake. The multiplier is what keeps the watchlist empty in a normal week.

### The three properties this ticket asked for

- ⚠️ **Deterministic.** Tie-breaks end in **ISBN ascending** (ticket 03, step 6), so the order is *total* — there is no
  coin flip that can land differently on a second run.
- ⚠️ **Replay-stable.** The committed `facts.json` carries `chart_logic: 1`, so re-rendering a week reproduces the same
  ten; and re-running the *rule* on the same inputs cannot differ, because nothing in it reads a clock, a random
  number, or dict iteration order.
- ⚠️ **Per chart.** Ten in Bengali, ten in English, ten in all-language, ten in comics (ticket 12). ⚠️ And because
  all-language is a **superset** (ticket 14), the *same title* can be NEW in one chart and an incumbent in another —
  that is the superset working, not a contradiction.

### ⚠️ Week one bypasses it

With no previous chart there are no incumbents, so **every** title is a newcomer and the rule would admit ten —
producing a **10-book chart labelled "Top 100"**. Week one ships as a stated baseline instead (ticket 03); what the run
*does* with that is ticket 18's.

### ⚠️ What the watchlist is — and it unifies with ticket 17

The admission rule's overflow has to *go* somewhere rather than vanish. It is held as the **watchlist**: newcomers that
qualified but were not admitted, recorded in the snapshot so next week's run can see them.

⚠️ That makes the watchlist the natural home of the **single-source titles** the corroboration gate parks (ticket 17) —
both are *"real, but not yet admitted"*, so **one list serves both**. Two mechanisms that each needed a holding pen
turn out to need the same one.
