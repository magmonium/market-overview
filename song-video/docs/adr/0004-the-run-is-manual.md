# 0004 — The run is manual

- Status: accepted
- Date: 2026-10-13

## Context

Someone has to look at the thumbnails. The reel's quality is a judgement — does this theme read, does this title
fit, does the motif sit with the wave — and no guard in this codebase can make it.

The brief's own ADR 0004 made the same call for the same kind of reason, and the reel inherits it: a run is a
decision to publish, made by a person, in front of the stills.

## Decision

**One command, by hand, by a human.** `sv build` asks the four questions, prints the ledger, renders **every
thumbnail before any video**, then renders the reels and assembles the packages.

Interactivity is a **default, not a trap**: every question has a flag, so the same run is scriptable, and
`--replay` makes a rebuild a flag rather than a menu. There is no scheduler and no upload step.

## Consequences

- ⚠️ **The thumbnails come first, and they are the quality gate.** A full-length reel is about **twenty minutes**
  (7201 frames of a four-minute song, at Remotion's default concurrency); a thumbnail is seconds. The order is the
  whole reason a manual run is safe, and it is asserted rather than remembered: every still before any reel, in the
  recorded order.
- ⚠️ **A failed theme fails the run.** Exit code 1, no summary, and nothing half-written: each render writes a
  dot-prefixed sibling and is moved into place only once it exists and passes its own checks, because Remotion's
  `--overwrite` unlinks its target. A render that dies at 90% costs a run, never a delivery.
- ⚠️ **A menu nobody can answer is refused once, up front** — with every missing flag named — rather than at the
  third question, after the operator has typed the first two.
- ⚠️ **There is no resume, and no retry.** A re-run repeats themes that are already complete. That is the honest
  current state rather than a decision: it is flagged here because a late failure at twenty minutes a theme is the
  cost, and a `--only <theme>` is the obvious answer when somebody wants it.
- **The stills also catch a transient failure.** Remotion's browser dies sporadically (observed once in roughly
  seven renders here, as `Target closed`). Thumbnails-first means that costs seconds rather than a render.
