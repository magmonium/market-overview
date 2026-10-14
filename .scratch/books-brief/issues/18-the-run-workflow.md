# The run's workflow

Type: task
Status: resolved
Blocked by: 02, 17

## Question

The end-to-end shape of one weekly run — and, the consequential part, **what happens when a source is down**.

The host repo's conductor already has the shape (ADR 0002, ADR 0003):

```
fetch every source  →  store/<week>/raw/*.json   (written BEFORE parsing — the evidence)
                    →  corroborate + score + rank  (tickets 17, 03)
                    →  store/<week>/facts.json     (the sole interface to the renderer, committed)
                    →  render slides  →  mux audio  →  thumbnail  →  package  →  publish
```

What has to be decided:

1. ⚠️ **A source is down.** The brief's rule is *degrade to omission* — a missing block is omitted, never rendered as
   zeros. But a **chart** is different: a chart missing one of its five sources is not "degraded", it is **wrong** —
   and it will still be diffed against last week's chart as if nothing had happened. So: **abort the run**, **ship
   with the source list stated**, or **hold the week**?
2. ⚠️ **A source publishes late.** Ticket 10 says the union's slowest member sets the run day — but a source can slip
   *after* that. Is a late source waited for, or does the run proceed without it, and how is that recorded?

   ⚠️ **Ticket 10 hands you the guard, not the mechanism.** It fixed that a **freshness guard per source** must exist —
   each source verified to have published **for the week being built**, never trusted because the calendar says it is
   Tuesday. A books chart has no session clock to check against, so a stale scrape yields a chart that is quietly last
   week's, and the week-over-week diff (ticket 01) reports **zero movement** — silent, plausible and wrong. Decide here
   what the guard does when it trips: refuse the run, drop the source, or ship with the staleness stated.
3. **The first run.** With no previous week to diff against, every title reads as NEW — which breaks the ≤10 cap
   (ticket 11). Does week one ship without Δ, or against a stated baseline?
4. **Re-runs.** `facts.json` is the only thing a re-render reads (ADR 0003), so a re-render must not re-fetch — but a
   *re-run* that **does** re-fetch must not silently produce a different chart. Is a week **frozen** once its snapshot
   is committed?
5. **Retries and rate limits.** The sources have different limits (NYT 1,000/day; Open Library 100/IP per 5 min), so a
   retry policy that respects them is part of the workflow, not an afterthought.

## Answer

### ⚠️ The brief already has this shape, and it maps onto the corroboration rule exactly

`cli.py` splits every fetch into **the spine** and **everything else**: the spine is **fatal** — *"a degraded brief is
a wrong one"* — while everything else goes through `_degrade()`, whose docstring is the rule:

> *"A failure here is **never** an abort: a missing corporate-action card is a smaller failure than a brief that refuses
> to publish because a secondary feed was down."*

⚠️ **For a chart product, the spine is the corroboration set.** Ticket 17 admits a title only when its declared vendors
agree, so **the vendors a chart declares *are* its spine**. The mapping is exact:

| The brief | books-brief |
|---|---|
| the index scoreboard — **fatal** | **the chart's required vendors** — a missing one makes the chart **absent** |
| a missing sector card — **omitted** | **the ticker** (ticket 08), a **cover** (branded tile), a **price** (`—`), a **pub date** (omitted) |

⚠️ **A degraded chart is a wrong chart** — the same sentence, one level down. A chart built from one vendor instead of
two is precisely what the gate exists to prevent, so losing a vendor must **not** produce a smaller chart. It produces
**no** chart.

### 1 — A source is down

**The chart goes absent; the other charts ship.** That is ticket 13's partial delivery and it needs no special case: a
chart is an **absent key** in `facts.json` while its siblings render normally.

⚠️ **If every chart is absent, the run refuses and writes nothing** — the brief's own all-or-nothing case, generalised
from one artefact to four.

### 2 — A source publishes late

⚠️ **A stale source is a missing source for that week** (ticket 10's freshness guard), so it takes the same path: the
chart needing it goes absent.

⚠️ This **narrows ticket 10's wording**. Ticket 10 said *"a failure refuses and writes nothing"* — true for the brief,
where there is one artefact. Here the refusal is **per chart**, because a comics chart that is ready should not be held
hostage to a Bengali list that is late. The run writes nothing **only** when nothing can be built.

⚠️ **Week one is now a 26-week ramp** (ticket 23): if the six-month ranking is built from our own committed snapshots,
then **weeks 1–25 have no six-month window**. The "stated baseline" below is therefore not one week but a **ramp**, and
the chart must **state the window it actually has**.

### 3 — Week one

**It ships as a stated baseline, and it says so.** With no previous chart there is nothing to diff against, so:

- ⚠️ **every row carries no Δ and no NEW badge** — otherwise every title reads as NEW, which is true and useless;
- ⚠️ **the ≤10 admission cap is bypassed** (ticket 03), or the "Top 100" ships as **ten books**;
- ⚠️ and **the run's warnings say all of this** — a baseline that looked like a normal week would be indistinguishable
  from one.

### 4 — Re-runs: the snapshot's existence is the switch

The brief's rule, verbatim: *"The snapshot's **existence** is the switch… A snapshot is only ever written after the
session guard admits the date, so finding one means the day was already established as final, and the guard is
deliberately skipped on this path."*

So `books-brief build --week 2026-W41` with `store/2026-W41/facts.json` present **replays and does not fetch** (ADR
0003). A re-run that must re-fetch says so explicitly (`--refetch`), and then:

- the bundle hash changes;
- ⚠️ the **publish refuses** for a week already published (ADR 0006's rule), rather than putting two different charts
  under one title;
- ⚠️ and the overwritten snapshot is **recoverable from git**, because `store/` is committed. That is what makes
  overwriting safe rather than destructive.

### 5 — Retries, rate limits, and being a good citizen

- **Bounded retries with backoff**, honouring `Retry-After` — never a retry storm.
- ⚠️ **A per-source budget**, because the limits differ wildly: NYT **1,000/day**, Open Library **100 req/IP per 5 min**.
- ⚠️ **Polite scraping**: no parallelism against a single host, a delay between requests, a real User-Agent. Amazon.in
  and Anandabazar are being *read*, not harvested.
- ⚠️ **`curl_cffi`** for the Akamai-protected Bengali source — the host repo already carries the dependency and
  `fetch/bse.py` already demonstrates the pattern.

### 6 — Two habits inherited verbatim

- ⚠️ **The raw response is snapshotted even when parsing fails** — *"at that point the evidence of what was actually
  received is exactly what is needed."* `store/<week>/raw/*.json` is written **before** parsing.
- ⚠️ **Warnings go to stderr and are not swallowed.** The brief prints `published.warnings` as `warning: …`; a run whose
  warnings vanish is a run that silently shipped a second-best chart.
