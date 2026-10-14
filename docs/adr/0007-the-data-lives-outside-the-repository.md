# 0007 — The data lives outside the repository, namespaced by product

- Status: accepted
- Date: 2026-10-14

## Context

Two tools are built from this repository — the **brief** (at the root) and the **reel** (nested at
`src/song-video/`) —
and both write the same two kinds of thing: the operator's licensed assets, and the packages they produce.

Until now each owned its own copy of that space, derived from where its code sits:

| | brief | reel |
|---|---|---|
| assets | `resource/` (`logo.*`, `music.*`) | `resource/song/` |
| packages | `output/<date>/<lang>/` | `output/<song>/<theme>/` |
| rebuild evidence | `store/<date>/` | `store/<song>/run.json` |

Three things went wrong with that, and only the third was visible.

1. **One licensed asset was already being shared by reaching across a folder boundary.** The reel read the brief's
   mark out of the parent's `resource/` through the brief's own loader, because two marks would be two answers to
   the ink-polarity question.
2. **The two output layouts were disjoint by accident, not by construction.** A song's id is its filename stem, so
   a song called `2026-10-13` would have landed in the brief's run directory and beside the brief's
   `.published-<lang>.json`.
3. **A reel takes about twenty minutes and a brief about an hour**, so the operator's real question was never
   "where do these live" but "may I start one while the other is running". Nothing in either tool answered it.

A fourth fact decided the boundaries: `store/` is **committed**. It is the rebuild evidence — the brief's per-date
snapshot, the reel's recorded run — and it is deliberately not gitignored. `output/` and `resource/` are data.

## Decision

**One data root outside the repository, shared by both products, namespaced per product.**

```
~/.local/share/market-overview/          ← MARKET_OVERVIEW_DATA overrides; never in the repository
├── resource/
│   ├── brief/{logo.*, music.*}
│   └── reel/song/{<name>.<audio>, <name>.<image>}
└── output/
    ├── brief/<date>/<lang>/   + .published-<lang>.json
    └── reel/<song>/<theme>/
```

- The root is `market_overview.paths.data_root()`: `MARKET_OVERVIEW_DATA`, else
  `~/.local/share/market-overview` — the XDG data directory, partner to the credentials in
  `~/.config/market-overview/` (`publish.credentials_dir`), and not `~/Documents`, which a laptop may be syncing.
- **Each product names its own namespace.** The brief's package defines only `data_root()` and its own `brief`
  half; the reel spells `reel` itself. The brief never learns the word *reel*, because the dependency runs
  `song-video → market-overview` and a brief that could name the reel's folders is one import away from needing to
  build a product it must not depend on.
- **`store/` does not move.** It is evidence rather than data: it is committed so a clone can rebuild a day
  without re-fetching, and moving it out would quietly drop those files out of version control and out of the
  Docker build context.
- **`public/` does not move.** It is staging for a render that runs from the project's own tree, not data.

## Consequences

- ⚠️ **Two runs may overlap without a lock.** The guarantee is a property of the layout: a brief writes
  `output/brief/**` and a reel writes `output/reel/**`, the resources are read-only, and `store/` is disjoint. Two
  runs of the *same* tool pointed at the *same* date or song still target identical paths and remain unguarded —
  they always were, and guarding them would mean a lockfile with a stale-lock story of its own. The reel is manual
  by decision (ADR 0004) and the brief is scheduled once a day (ADR 0006).
- ⚠️ **`store.root()` changed meaning, and so did the test seam that rested on it.** It still means the repository
  — code, `node_modules`, the committed snapshot — but it no longer redirects `output/`. A single patch of
  `store.root` used to redirect both the snapshot and the packages; tests that wrote packages now patch
  `paths.data_root` as well. A suite that kept only the old patch would pass while writing into the operator's real
  `output/brief/`.
- ⚠️ **The container must be told.** Inside an image `Path.home()` is `/root`, so the default data root is a path
  in the container's writable layer: the day's deliverable and its publish record would vanish with the container
  and the next scheduled run would re-upload the same day. `MARKET_OVERVIEW_DATA=/data` (Dockerfile) pins it to
  the mount, and `MARKET_OVERVIEW_ROOT=/app` stays what it always was — the repository, read only by the shell
  wrapper.
- ⚠️ **The two `resource/` READMEs had to leave the folders they describe.** They are committed documents, and the
  folders they document are not in the repository any more, so both were folded into the repository's single
  README, as the two asset contracts.
- ⚠️ **The move is one-time and manual.** `mv`-ing four folders is documented in the README rather than coded: a
  legacy fallback would make "where does output live?" answerable two ways, which is the ambiguity the namespacing
  exists to remove. Nothing is unrecoverable in any case — `store/` stayed put, so both existing dates and every
  song can be rebuilt.
- The reel's `catalogue.where()` note — that "the data root" and "the code it is part of" are two different ideas —
  is now literally true rather than merely careful, and `paths.repo_root()` remains the toolchain's home.
