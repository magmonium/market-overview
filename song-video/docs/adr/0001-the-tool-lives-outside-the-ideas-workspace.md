# 0001 — The tool lives inside `market-overview`, outside the `ideas` workspace

- Status: accepted
- Date: 2026-10-13

## Context

The Song Reel was specified in the `ideas/` planning workspace, at `ideas/.scratch/song-video/`, which per
`SUBMODULES.md` **"only tracks pointers + planning docs — never source code."**

The first answer to that was the obvious one: the reel is not an `nx/` or `api/` feature, so it gets its **own
repository** at `~/Documents/magmonium/song-video`, a sibling of `ideas/`. Then the operator reversed it, for one
reason: the two products belong in **one** repository, and the brief already owns most of what the reel needs.

## Decision

The reel lives at **`market-overview/song-video/`** — a **nested uv project**: its own `pyproject.toml`,
`src/song_video/`, `tests/`, `resource/`, `store/` and `output/`, with the brief's own project untouched.

It **imports the brief's resources rather than copying them**: `market_overview.logo` for the mark,
`market_overview.audio` for the toolchain and its loader-path trap, the brief's vendored fonts, and the parent's
installed `node_modules` for Remotion — no second runtime.

It is **still outside the `ideas` workspace**, and still not a submodule: nothing in `ideas/` points at this code,
and the wayfinder map and the task plan are the only link between them.

## Consequences

- ⚠️ **The reel inherits the brief's dependency tree**, `curl_cffi` included, because it depends on
  `market-overview` as an editable path dependency. That is the accepted price of not re-implementing ~250 tested
  lines of mark handling and toolchain discovery, and it is written down rather than discovered.
- ⚠️ **The parent's `.gitignore` does not reach in here.** A pattern containing a slash is anchored to its own
  directory, so `market-overview`'s `output/*` and `resource/*` rules do not cover this folder — the reel owns its
  own `.gitignore`, or its media would be committed by accident.
- ⚠️ **The nested project owns its own pytest options.** pytest resolves `rootdir` *upward*, so a second
  `testpaths` fixes a collection collision and prevents the reel's suite from inheriting the brief's `addopts`.
- **There are two roots, and the difference is load-bearing**: `paths.project_root()` is the reel's own tree (the
  data — `resource/`, `store/`, `output/`), while `paths.repo_root()` is where `node_modules` and the brief's
  `resource/logo.png` live. A fixture may relocate the first; nothing may relocate the second.
- **The render's working directory is the reel's tree, not the repository's** — because both projects have a
  `remotion/index.ts`, and only one of them registers the reel's compositions.
