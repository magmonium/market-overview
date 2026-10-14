# 0006 — Nothing is pruned: the chart is rebuilt from kept evidence

- Status: accepted
- Date: 2026-10-14

## Context

The brief asks each chart to rank on **sales over the last six months together with user reviews**. ⚠️ **No source
sells a six-month figure.** Amazon.in's list is *current*; Anandabazar's and NYT's are weekly; a six-month sales total
is a Nielsen BookScan product, and Nielsen is ruled out of scope.

So the window cannot be **fetched** — it has to be **accumulated**, from our own committed snapshots. That single fact
turns three things that would otherwise be housekeeping into correctness:

- **retention** — pruning a snapshot silently *shrinks* the ranking window, and nothing would say so;
- **the cover cache** — keyed by ISBN rather than by week, so the superset's repetition is fetched once;
- **the ranking rule** — which changes the chart, and therefore has to be versioned.

## Decision

**Every week is kept, the chart logic is versioned, and covers are cached by ISBN.**

- ⚠️ **`store/` is never pruned.** It is the *evidence* (the host repo's `docs/adr/0007`: *"`store/` never was
  gitignored, and that is the difference between the tool's evidence and its data"*), **and** it is the input the
  six-month window is built from.
- ⚠️ **Covers are cached by ISBN** under `resource/books/covers/<isbn13>.jpg`, because a cover is immutable per ISBN —
  and the **source URL and a hash ride in the snapshot**, so a rebuild works without committing hundreds of images a
  week.
- ⚠️ **`meta.chart_logic` is a version**, so a re-run of an old week reproduces the **old** chart rather than the new
  rule applied to old data.
- ⚠️ **A re-run overwrites a snapshot, and `git` is the version history** — which is what makes overwriting safe rather
  than destructive.

## Consequences

- ⚠️ **The stated window is data, not a claim.** Weeks 1–25 cannot have six months of history, so the bundle carries
  the window it actually has and the chart says so — a chart claiming six months while holding seven weeks would be
  stating something untrue.
- ⚠️ **The cost is stated rather than implied**: `store/` grows every week, committed — the same price the brief already
  pays, per day rather than per week. If it ever must be bounded, the bound is **"the window the chart claims"**, not
  "N weeks".
- ✅ **PW's `YTD` units are used where they exist**, never as a substitute — `YTD` is a *calendar-year* figure, not a
  rolling six months.
- ⚠️ **`facts.json` is the only thing a re-render reads.** That is what makes a past week rebuildable without touching
  a vendor, and it is why the snapshot is the interface rather than a cache.
