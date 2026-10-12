# market-overview

Builds the **Market Brief** — one day's silent, music-backed, ≤3 min, 16:9 video about the Indian market, in
two language editions (Bengali and English), each with its own metadata and thumbnail.

**The tool is `market-overview`. The product is the Market Brief.** Output filenames carry the product's
name: `market-brief-<date>-<lang>.mp4`.

## Status

**End to end, both editions, rebuildable.** A run fetches, computes the bundle, renders the video and the thumbnail
for each language, and assembles `output/<date>/<lang>/`. Re-running a date re-renders from the snapshot without
touching the network, so a delivery can be reproduced and verified after the numbers have moved on. The design is
fully specified, and the specification is the source of truth for **what** to build:
`ideas/.scratch/market-brief/map.md` — 25 tickets, 24 decisions, none open. Build
order lives in `ideas/tasks/0085_market-brief_plan.md`. ⚠️ **Those two files are the only link to this repo** — it is
not a submodule, so nothing in `ideas/` points here (see `docs/adr/0001`).

## Vocabulary and decisions

- `CONTEXT.md` — the glossary: run, session date, facts bundle, label table, card, edition, package,
  snapshot, spine, degrade-to-omission.
- `docs/adr/` — the four load-bearing decisions.

## Requirements

Python ≥ 3.14 and [`uv`](https://docs.astral.sh/uv/). Node ≥ 24 for the render layer.

✅ **No system `ffmpeg` is required, and that question is settled.** Remotion ships its own build in
`node_modules/@remotion/compositor-*/ffmpeg`, and the pipeline uses that one — so the music mux, the thumbnail and the
loudness normalisation all work on a machine that has never installed ffmpeg. To use a different build, set
`MARKET_OVERVIEW_FFMPEG=/path/to/ffmpeg`.

⚠️ Two consequences worth knowing. The bundled binary is **`--enable-shared`**, so it will not start without
`DYLD_LIBRARY_PATH` pointing at its own directory — `audio.binary_env` supplies that, and anything invoking it
directly must too (run bare, it **aborts with nothing on stdout**, which is a silent failure if the exit code is
ignored). And it is a **stripped** build: `--disable-filters` with an allow-list, so `afade`, `acrossfade`,
`volumedetect` and `astats` are all **absent** — the obvious way to fade a bed, and the obvious way to check you
faded it, are exactly the two that are missing. `tests/test_audio.py` asserts the allow-list, and the absence.

## Run

```bash
uv run market-overview build --date YYYY-MM-DD
```

One command, by hand — there is no scheduler, deliberately (`docs/adr/0004`).

⚠️ **Run it in the foreground, and expect it to take a long time.** A full brief is ~4,500 frames per edition plus
a still, so a two-edition run is well over an hour of rendering — and **you will see no progress while it works**,
for two independent reasons. Python buffers stdout when it is redirected to a file, and Remotion's own output is
**captured rather than forwarded** (deliberately — 0085_06: a render that dies has to keep its reason, and a
buffer discarded on death takes it along). So a run that is working looks exactly like a run that has hung.

Prefix `PYTHONUNBUFFERED=1` to get the tool's own lines as they happen, which is enough to see *which edition* is
in flight:

```bash
PYTHONUNBUFFERED=1 uv run market-overview build --date YYYY-MM-DD > /tmp/run.log 2>&1 &
```

Interrupting is safe: every write is atomic or staged, so a killed run leaves the previous delivery intact and the
date folder visibly unfinished.

What a run does: **fetch or re-render** → compute the facts bundle → render both editions → assemble the
packages.

- **Bengali renders first**, so the primary edition is never hostage to the secondary.
- **A failed spine aborts and writes nothing.** Prices are the spine; every other source degrades to
  omission, dropping its own card.
- **A failed edition fails the run** — a half-populated date folder would look complete.
- **Writes are atomic** and run-scoped temporary directories are cleaned only on success.
- **A package is complete when `metadata-<lang>.json` exists**, and that file is written last. It is removed before
  the rest of the package is written, so a run that dies leaves a folder that visibly is not finished, rather than
  one that merely looks small. See the note in `src/market_overview/package.py`.

### Fetch, or re-render

**If `store/<date>/facts.json` exists, the run re-renders from it and never touches the network.** That is the
whole rebuild promise (`04-data-ownership.md`: *"a video must be rebuildable without re-fetching — the numbers will
have moved by the time anyone looks at it"*), and the log says which path it took:

```
re-render: reading store/2026-10-12/facts.json — not fetching
```

Two consequences worth knowing, because both are deliberate:

- **A past date can only be rebuilt, never re-fetched.** The session guard compares the date asked for against the
  *newest* session, which has moved on by definition — so on the fetch path Tuesday's date refuses on Wednesday.
  The snapshot is what makes yesterday reachable at all.
- **A re-publish cannot silently change the numbers.** Rendering the same date again reads what was published,
  not what the market looks like now. To force a fresh fetch, **delete the snapshot first**:

```bash
rm -rf store/2026-10-12 && uv run market-overview build --date 2026-10-12
```

That is the only way to refetch a date, and it is not reversible — `store/<date>/raw/` is the only evidence of
what the sources actually returned.

### Refusal cases

A run can legitimately refuse, and refusing is the correct outcome. ⚠️ **Every refusal exits non-zero and writes
nothing** — `1` for a refusal, `2` for a malformed `--date`.

| Case | Exit | Why it refuses |
|---|---|---|
| **Holiday**, weekend, or a mistyped date | 1 | *"asked for X but the newest session is Y"*. A holiday produces no error at all — only *yesterday's* numbers, which would publish under today's date. |
| **Mid-session** | 1 | *"session X has not finished printing"*. The india feed is ~15 min delayed, so "final" is the close plus 16:00 IST. Before that the numbers are still moving. |
| **Spine down** | 1 | The india scan is the spine. A brief with no market in it is not a degraded brief, it is a wrong one. |
| **Unusable mark** | 1 | `resource/logo.svg` has text that is not outlined, so it depends on a font being installed. Rendering it would look right here and different elsewhere (0085_10). |
| **Unmixable bed** | 1 | `resource/music.*` is not a container the tool's `ffmpeg` can read (0085_11). |
| **Incomplete package** | 1 | An artefact is missing. Assembly refuses to write metadata for a folder that would *look* complete (0085_13). |
| **Over a limit** | 0 | ⚠️ Reported, not refused. A title two characters long is truncated by YouTube and loses the move — bad, but not a reason to publish nothing. The run prints `warning: …` and carries on. |

Missing `logo.svg` or `music.*` is **not** a refusal: no mark and a silent brief are supported states. See Assets.

### Verifying a delivery

`tests/test_frame_identity.py` proves the property on the committed snapshot by rendering ten mid-brief frames
twice and comparing them — cheap enough to run in the default suite. To check an actual delivered file:

```bash
cp output/2026-10-12/bn/market-brief-2026-10-12-bn.mp4 /tmp/delivered.mp4
uv run market-overview build --date 2026-10-12      # re-renders from the snapshot
cmp /tmp/delivered.mp4 output/2026-10-12/bn/market-brief-2026-10-12-bn.mp4
```

⚠️ **Frame-identity is the requirement; byte-identity is the bonus.** A re-render that decodes to the same frames
is correct even if the container differs by a byte, because what an audience and a platform see are frames. If
`cmp` reports a difference, compare decoded frames before treating it as a fault:

```bash
D=node_modules/@remotion/compositor-darwin-arm64
DYLD_LIBRARY_PATH=$D $D/ffmpeg -i /tmp/delivered.mp4 -vsync 0 /tmp/a/%03d.png   # and the same for the new file
```

### Before you publish

The run cannot judge these, and they are the reason a human runs it:

- **The Bengali reads as Bengali, not as translated English.** The label tables are written per language, but
  *native phrasing* is not something a test can assert. This applies to the labels, the metadata and the
  description — three surfaces.
- **The music is audible at the right level.** The bed is normalised to −14 LUFS, which is a measurement, not a
  judgement about how it sits under nothing.
- **The cold open and the close carry the mark once `resource/logo.svg` is supplied.**
- **Numeral consistency** — the brief's Bengali numerals against the figures quoted from the sources.
- **The whole thing looks like a market brief**, which is the one check that has no proxy.

## Layout

```
resource/   operator-supplied licensed assets (logo, music) — never committed
output/     generated packages, output/<date>/<lang>/ — never committed
store/      per-date snapshots: raw source responses + facts.json — rebuild a day from these
src/        the Python package
docs/adr/   decisions
tests/      tests
```

A run writes to exactly two places, and neither is ever committed:

```
store/<date>/raw/*.json        the source responses, verbatim — written *before* parsing, so if the
                               parser is what broke, the evidence of what it was given is already on disk
store/<date>/facts.json        the computed bundle — the sole interface to the render layer, and the
                               only thing a re-render reads
output/<date>/<lang>/          the deliverable, four files and nothing else:
                               market-brief-<date>-<lang>.mp4 · metadata-<lang>.txt ·
                               metadata-<lang>.json · thumbnail-<date>-<lang>.jpg
```

⚠️ The snapshot lives **outside** `output/`, so a package contains exactly what a viewer should see and no
plumbing. The raw responses are the only evidence if a figure is ever disputed, which is the second reason they
exist — the first being that a video has to be rebuildable without re-fetching.

## Tests

```bash
uv run pytest -q
```

No network, no ffmpeg, and the tests that would need a browser stub it — so the suite is hermetic and fast. The
exceptions are deliberate and skip themselves when they cannot mean anything.

`tests/test_frame_identity.py` is the one that renders for real: ten mid-brief frames, twice, decoded and compared
frame by frame. It is the guard on the product's central claim, so it runs by default rather than behind an
environment variable — and it is why the suite needs Chrome present to be at full strength.

## Assets

Two files are dropped into `resource/` when they are available — **both optional**, see below:

- `logo.svg` — the product mark. **One asset, no light/dark variant needed.**
- `music.*` — the background bed. Any container `ffmpeg` reads.

See `resource/README.md`. The licence is yours; the pipeline records nothing and enforces nothing.

⚠️ **Both are optional, and the tool runs without them** — a markless, silent brief is a supported state, not a
degraded one, so a missing asset is never a refusal. What *is* a refusal is an asset the tool cannot use:
a `logo.svg` whose text is not outlined, or a `music.*` in a container the bundled `ffmpeg` cannot read. Both
are listed in the refusal table above.
