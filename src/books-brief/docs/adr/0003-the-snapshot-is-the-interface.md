# 0003 — The snapshot is the interface, and a failed chart is an absent key

- Status: accepted
- Date: 2026-10-14

## Context

The host repo's `docs/adr/0003` makes `facts.json` the **sole interface** to the render layer: display strings live in
the renderer's label tables, so a string appearing in the bundle is a bug. It also makes the per-date snapshot the
rebuild path — *"a re-render reads this instead of fetching."* This product inherits both.

What it does **not** inherit is the bundle's *shape*, and the reason is worth recording because the brief's own
arrangement looks like it should transfer and does not.

⚠️ The brief writes **one bundle per date**, with the variant — the language — read from **Remotion input props**, not
from the bundle. `Furniture.tsx` gives the reason: *"the bundle stays language-neutral so both editions read the
identical file, which is what makes it impossible for them to disagree about a number."*

⚠️ **That reasoning is about two editions of the same data.** Four charts are **different data**.

## Decision

**One bundle per week, four chart keys**, with the chart id read from **input props** exactly as `lang` is.

```
store/2026-W41/
├── raw/*.json      every source response, verbatim, written before parsing
└── facts.json      { "meta": {…}, "charts": { "bengali": {…}, "comics": {…} } }
```

⚠️ **A chart whose vendors did not answer is an absent key, not an empty one.** The brief's rule — *"a missing strip is
an absent key, never an empty card full of zeros pretending the world was flat"* — buys **partial delivery**: three
charts ship, the fourth refuses, and nothing is fabricated to fill the gap.

⚠️ **The key is the ISO week** — `2026-W41` — not a date. It is zero-padded, so it sorts as a string, and it needs no
state to derive.

⚠️ **`meta.chart_logic` is versioned**, because a change to the ranking rule changes the chart: a re-run of an old week
must reproduce the **old** chart, not the new one. `meta.window_weeks` rides beside it, because the six-month window is
*accumulated* and an early run must state the window it **has**.

## Consequences

- ⚠️ **An absent key is the whole failure model.** A chart is never partially built and never rendered from a
  half-gathered week; the conductor refuses only when *every* key would be absent, and then it **writes nothing** —
  because a week written empty would be read back later as a real week containing no charts.
- ⚠️ **The raw responses are written before parsing**, so *"if the parser is what broke, the evidence of what it was
  given is already on disk."*
- ✅ **`store/` is committed and never pruned** (ADR 0006), because the accumulated window is built from it — so the
  snapshot is evidence *and* input.
