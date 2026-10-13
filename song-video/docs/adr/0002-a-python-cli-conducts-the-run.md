# 0002 — A Python CLI conducts the run

- Status: accepted
- Date: 2026-10-13

## Context

The product needs two runtimes. Remotion can draw a frame and cannot decide *what* to draw from a folder of
operator files; Python can decide and does not draw. The question is where the decisions live, and the ask is
specific: the menu, the record, the theme catalogue and the guard are all policy.

The brief answered this once (its ADR 0002) and the reel inherits the answer rather than reopening it.

## Decision

**Python collects, records, guards, stages and drives. The JS layer only renders.**

`sv build` discovers the song, asks or takes the four answers, guards the master's digest, writes the record,
stages the master into `public/`, renders every thumbnail, renders every reel, and assembles the packages. The
render layer is pointed at a **props file** and never fetches, never asks and never reads a clock.

## Consequences

- **Every decision is reachable from pytest.** The frame count's ceiling rule, the digest, the catalogue, the
  package names, the staging copy, the ordering of the renders — all of it is Python, and the suite is the reason
  the expensive mistakes are caught before a frame.
- ⚠️ **The catalogue is read, never mirrored.** The menu must offer exactly what the renderer can draw, and the
  renderer owns that list, so Python asks it: node strips the types off `remotion/themes.ts` and returns it as
  JSON. A mirrored *formatter* drifts visibly; a mirrored **menu** drifts invisibly — a theme the operator simply
  cannot tick — so this trades a subprocess for a menu that cannot lie.
- ⚠️ **The render's working directory is the reel's own tree.** `remotion/index.ts` is relative, and the parent has
  a file by the same name: run from the repository and Remotion bundles the *brief's* root and reports a missing
  composition, helpfully listing `MarketBrief, Thumbnail, IndexCard`. Found by running it, pinned by a test that
  reads this tree's `Root.tsx` and asserts the ids this side invokes are registered there.
- ⚠️ **Nothing here calls the toolchain directly.** The bundled `ffprobe` dies with `SIGABRT` unless the loader
  path is applied, which `market_overview.audio` exists to do.
- ⚠️ **The sound is not Python's.** Unlike the brief — which normalises a bed and muxes it in — the composition
  plays the staged master and Remotion encodes it once, at one pinned bitrate, into the video that ships. A song
  that is *analysed* but never *heard* is the one defect every still in this project looks perfect through.
- **Two private helpers are borrowed from the brief** (`_stream`, `_browser_flag`) rather than re-implemented: one
  keeps a long render from looking hung, the other encodes a browser trap this machine already taught once. A
  rename breaks the reel loudly, at import; a second copy would break it silently, on the operator's machine.
