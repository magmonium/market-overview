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

The reel lives at **`market-overview/src/song-video/`** — a **nested uv project**: its own `pyproject.toml`,
`song_video/`, `tests/`, `store/` and `public/`, with the brief's own project untouched. ⚠️ It sits **inside the
brief's `src/`**, so both products' code is under one `src/` at the top of the repository. ⚠️ Its `resource/` and
`output/` are not here at all: they moved to the shared data root with the brief's own — see
[ADR 0007](../../../../docs/adr/0007-the-data-lives-outside-the-repository.md).

It **imports the brief's resources rather than copying them**: `market_overview.logo` for the mark,
`market_overview.audio` for the toolchain and its loader-path trap, the brief's vendored fonts, and the parent's
installed `node_modules` for Remotion — no second runtime.

It is **still outside the `ideas` workspace**, and still not a submodule: nothing in `ideas/` points at this code,
and the wayfinder map and the task plan are the only link between them.

## Consequences

- ⚠️ **The reel inherits the brief's dependency tree**, `curl_cffi` included, because it depends on
  `market-overview` as an editable path dependency. That is the accepted price of not re-implementing ~250 tested
  lines of mark handling and toolchain discovery, and it is written down rather than discovered.
- ⚠️ **The parent's `.gitignore` did not reach in here, and the paths that needed the reel's own file are gone.**
  A pattern containing a slash is anchored to its own directory, so `market-overview`'s rules never covered this
  folder — which is why the reel had its own. ⚠️ **ADR 0007 then removed the media from the tree altogether**: the
  songs and the packages live under the shared data root, outside the repository, so the reel's `.gitignore` no
  longer has media to ignore. What remains of it is `public/` and build noise.
- ⚠️ **The nested project owns its own pytest options.** pytest resolves `rootdir` *upward*, so a second
  `testpaths` fixes a collection collision and prevents the reel's suite from inheriting the brief's `addopts`.
- **There are three seams now, and the difference is load-bearing** (ADR 0007 split the first one in two):
  `paths.data_root()` is the **data** — `resource/reel/song/` and `output/reel/` — and is the one a fixture
  relocates; `paths.project_root()` is the reel's own tree, which still holds the **recorded run** (`store/`) and
  the **staging** (`public/`); and `paths.repo_root()` is where `node_modules` live. ⚠️ A fixture may relocate the
  first two; nothing may relocate the third, and the mark now comes from the data root rather than beside the code.
- ⚠️ **Moving the project under the brief's `src/` cost `repo_root()` its assumption.** It was
  `project_root().parent` — *one level up* — which was true only while the project sat directly in the repository.
  One level up is now `src/`, where there is no `node_modules` and no `remotion/`. It is now the brief's own
  `store.root()`, so the repository is **asked for rather than inferred from a folder depth** — one definition of
  where the repository is, and a move that cannot silently break the toolchain lookup again.
- **The render's working directory is the reel's tree, not the repository's** — because both projects have a
  `remotion/index.ts`, and only one of them registers the reel's compositions.
