# One report or four

Type: grilling
Status: resolved
Blocked by: 14

## Question

Four charts — but how many artefacts?

⚠️ **A hard constraint arrived from ticket 06, and it decides most of this.** One book per slide, all 100, with
rank-weighted dwell, totals **2 m 49 s per chart**. So:

- **Four charts × 100 slides ≈ 11 minutes** — which does **not** fit the 3-minute cap the brief uses.
- **Four separate videos** fit it exactly (each ~2 m 49 s, each with its own title, description, tags and thumbnail).
- **One long video** (~11 min) is possible, but the 3-minute identity is gone and the title scheme gets muddier.

So the real choice below is **four videos vs one long one** — not a free one.

1. **One report, four sections** — a single video and package with a Bengali block, an English block, an
   all-language block and a comics block. One render, one publish, one thumbnail.
2. **Four reports** — four independent videos, four packages, four publish events. Cleaner to schedule, because each
   chart's sources publish on different days, but four times the plumbing.
3. **One video, four charts interleaved** — the charts woven together, or as four carousels in one deliverable.

Also to settle:

- Does the ≤10 NEW cap (ticket 11) apply **per chart**? (It must, unless the four are really one chart.)
- Does each chart carry its **own** background ticker, or is there one shared background?
- Does the four-chart run share one `store/<week>/facts.json`, or one per chart?
- What does the **thumbnail** show when there are four charts?

## Answer

### ⚠️ The arithmetic decides it: **four videos**, one per chart

Ticket 06 left a hard number: one book per slide with rank-weighted dwell is **2 m 49 s per chart**. Four charts × 100
slides is **≈11 minutes** — and the brief's cap is **3**. So one artefact cannot hold both, and the option that keeps
the cap is the option that keeps the *shape*.

**Four reports** — four videos, each ~2 m 49 s, each with its own title, description, tags and thumbnail (tickets 15,
16). It is also the only option that matches the title scheme the brief already asked for: `Top 100 Bengali Books |
Week 41 | …` names **one** chart, so one title per chart needs one video per chart.

⚠️ The cost is stated rather than hidden: **four renders, four packages, four uploads** per week.

### ⚠️ One bundle per week, one key per chart — and a failed chart is an **absent key**

The brief's bundle is **one file per date**, with the *variant* (language) read from **Remotion input props** rather
than from the bundle — and `Furniture.tsx` says why: *"the bundle stays language-neutral so both editions read the
identical file, which is what makes it impossible for them to disagree about a number."*

⚠️ **That reasoning does not transfer, and the distinction matters.** Two language editions are the *same data* twice;
four charts are **different data**. So:

```
store/2026-W41/
├── raw/*.json      every source response, verbatim, written before parsing
└── facts.json      { "bengali": {…}, "english": {…}, "all-language": {…}, "comics": {…} }
```

**One file, four chart keys** — the week's whole state in one committed place — with the **chart id read from input
props**, exactly as `lang` is. Four independent renders from one snapshot.

⚠️ **A chart whose sources failed is simply an absent key.** That is the brief's own rule — *"a missing strip is an
absent key, never an empty card full of zeros pretending the world was flat"* — and here it buys **partial delivery**:
three charts ship, the fourth refuses, and nothing is fabricated to fill the gap. What the *run* does about it is ticket
18's.

### The four sub-questions this ticket inherited

- **The ≤10 NEW cap is per chart** — settled (ticket 11). ⚠️ And with the superset (ticket 14), the same title can be
  NEW in one chart and an incumbent in another.
- **Each chart carries its own ticker band, from one fetch** — the index scoreboard is not chart-specific, so it is
  fetched once and rendered into all four (ticket 08).
- **One `store/<week>/` snapshot, not four.** The week is the key; the chart is the variant. A per-chart store would
  force the week-over-week diff (ticket 01) to know which folder to read.
- ⚠️ **Four thumbnails, no master.** A thumbnail fronts the video it belongs to, so each chart's collage (ticket 16)
  rides with that chart's video. A "week thumbnail" would front nothing.

### The output shape

```
output/books/2026-W41/
├── bengali/        a package: video · thumbnail · title · description
├── english/
├── all-language/
└── comics/
```

⚠️ Mirroring the brief's `output/brief/<date>/<lang>/` — a **period, then a variant** — for the same reason: a package
is *"hand this folder to its own uploader"*, so the variant has to be a folder.

⚠️ **Idempotence becomes per chart** (ticket 10): the published-marker is keyed on **that chart's** hash, so re-running
a week whose Bengali chart is unchanged posts nothing, while a rebuilt comics chart still refuses rather than posting
twice.

### ⚠️ One run, four videos — and a chart waits for its *own* sources

The run fires **once a week** (ticket 10), not four times. But the charts' sources do not share a publication day, so
the freshness guard (ticket 10) is applied **per chart**: each chart ships only if *its* sources are fresh for the week.
A chart that is not ready is an **absent key**, not a held-up run.

⚠️ Per-chart scheduling stays available later without moving anything — ADR 0004's *"the command is already the
interface"* — and `--chart` is then a flag, not a redesign.
