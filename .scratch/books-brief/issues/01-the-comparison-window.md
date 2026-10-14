# The comparison window

Type: grilling
Status: resolved

## Question

Up/down and NEW are derived by diffing this period's chart against an **earlier** chart. Which earlier one?

The brief has said both *"change from last week"* and *"compare with last month"*, so this has to be settled before
the chart logic can be written: the window decides what `store/` keeps, what the Δ column means, and what counts as
a NEW entry.

## Options

1. **Week over week** — Δ against the previous committed week's chart; NEW = an ISBN absent from it. Matches a weekly
   cadence. *(recommended)*
2. **Month over month** — Δ against the chart from the same week one month earlier.
3. **Both** — week-over-week as the headline, month-over-month as a secondary badge.
4. **Rolling best** — Δ against the book's own highest rank ever recorded, rather than a fixed period.

## Answer

**Week over week — and every week is kept, which is what makes this question cheap either way.**

- **Δ** is the change in rank against the **previous committed week's chart**, computed **per chart** (Bengali,
  English, all-language, comics). Positive = moved up.
- **NEW** = the ISBN is absent from the previous week's chart *for that chart*.
- ⚠️ **Comparison is per chart** (ticket 14). Rank is chart-local, so a title can move *up* in the Bengali chart and
  *down* in the all-language chart in the same week — that is the superset working, not a contradiction.

⚠️ **Why "week", when the brief said both week and month.** The report is weekly, and the brief's first phrasing was
"change from last week". But the real tie-breaker is that **a weekly snapshot serves both readings**: month-over-month
is the *same diff taken against the chart four weeks back*, because `store/<week>/facts.json` is kept for **every**
week. The **storage** decision — keep every week — is therefore identical under either reading; only the **display
offset** differs. So this resolution is safe even if the headline should turn out to be monthly.

### ⚠️ Amended — there are now **two** windows, and this ticket only owned one

Ticket 23 gives the chart a **six-month ranking window** (sales + reviews). That is a different thing from this ticket's
**Δ window**, which stays **weekly**: the chart asks *"what sold most over six months?"* and reports *"how has that
ranking moved since last week?"*

⚠️ Keeping them apart matters, because a six-month basis is far stickier than a weekly one — which is what makes the
≤10 NEW cap (ticket 11) easier to hold than it looked when this ticket was resolved.

### ⚠️ What this ticket's answer still buys

The resolution above is unchanged in substance: **every week is kept**, Δ is the diff against the previous committed
week, and month-over-month is the same diff four weeks back. The six-month ranking window simply reads **more** of those
snapshots than the diff does.
