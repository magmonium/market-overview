# song-video — the Song Reel

One supplied song in → **a full-length 16:9 music video** and **its own thumbnail** out, in one or more of a
predefined set of visual themes, driven entirely by the song's own **amplitude envelope**.

**The tool is `song-video`. The product is the Song Reel.** Output filenames carry the product's name:
`song-reel-<song>-<theme>.mp4`.

## Where this lives, and what it reuses

⚠️ **A nested sub-project of `market-overview`, not a sibling repository** — reversed from the original
design by decision, so both products live in one repository. This folder is its **own uv project** with its
own `resource/`, `store/` and `output/`, and the brief's own project is untouched.

It **imports the brief's resources rather than copying them**:

| Reused | From |
|---|---|
| the operator's mark (the same `logo.png`) | `market_overview.logo`, reading the **parent's** `resource/` |
| the bundled `ffmpeg`/`ffprobe` discovery and its loader-path trap | `market_overview.audio` |
| the vendored fonts and the seeded PRNG | `market-overview/remotion/` |
| Remotion itself | the **parent's `node_modules`** — no second runtime is installed |

The cost is explicit: `song-video` depends on the `market-overview` package, so it inherits its dependency
tree. The alternative was re-implementing ~250 lines of tested mark handling.

## Status

**The pipeline is built end to end.** `sv build` discovers the song, takes or asks the four answers, guards the
master's digest, records the run, prints the ledger — and then renders **every thumbnail before any video** and
assembles one self-contained package per theme under `output/<song>/<theme>/`. A failed theme fails the run, and
nothing lands at a package path until it is whole.

⚠️ **A full-length reel is ~20 minutes** (7201 frames for a 4-minute song, at Remotion's default concurrency), which
is exactly why the thumbnails come first: a theme that reads badly costs seconds to find and an hour to discover
otherwise.

The specification is `ideas/.scratch/song-video/map.md` (11 tickets, 11 decisions, 0 open), with build order in
`ideas/tasks/0087_song-video_plan.md`.

## Vocabulary and decisions

- `CONTEXT.md` — the glossary: run, song, master, staging, title, cover, recorded run, theme, motif, wave form,
  catalogue, envelope, ledger, quality gate, package, thumbnail.
- `docs/RUNBOOK.md` — **every step and every command**: setup, both test suites, the menu, the refusals, how to
  look at a theme without spending twenty minutes, how to read back what was made, and the traps.
- `docs/adr/` — the six load-bearing decisions: **0001** where the tool lives (and the reversal it records) ·
  **0002** a Python CLI conducts the run · **0003** the recorded run is the interface · **0004** the run is manual ·
  **0005** the typeface is vendored · **0006** the envelope is the only clock.
- ⚠️ `beat` and `variant` are **not** in the vocabulary: there is no beat grid (ADR 0006), and N videos are
  N *themes*.

## Where the song goes

Drop the master into **`resource/song/`**. ⚠️ **The folder *is* the interface** — no manifest, no index and no
sidecar JSON, so adding a song is dropping a file in:

```
song-video/
└── resource/song/
    ├── dure-kothay.mp3      ← the master. At least one, or the run refuses
    └── dure-kothay.jpg      ← the optional cover, sharing the master's basename
```

⚠️ **The filename stem is the song's *id*, not its title.** The id is the menu entry, the `store/<id>/` folder and
the `<song>` segment of every output filename — nothing displays it. The title is a separate thing, **typed at run
time** (or passed with `--title`), which is why `dure-kothay_128kbps_final_mix.mp3` never becomes a title:

```bash
cd song-video
cp ~/Music/dure-kothay.mp3 resource/song/     # the whole of "adding a song"
uv run sv build                               # it appears in the menu as `dure-kothay`
```

⚠️ **Any audio format the bundled toolchain reads** (when two encodes of one song are present, the lossless one is
chosen as the master), and **no cover is a designed state** rather than a hole — the disc gets a plain label and the
thumbnail is composed from the mark, the title and the **caption**: the word *music* and the piece's length,
`সংগীত · ৩:০২`, written in the script the title is typed in.

⚠️ **The mark is not here.** The logo is the brief's own operator asset at
`market-overview/resource/logo.png`, read through the brief's loader, so one licensed file serves both products.

⚠️ **This folder is read, never written, and gitignored** — committing a master publishes it, and by dropping a
file in you declare it licensed for this product including publication. The full contract, including the
no-normalisation rule and what happens when the folder is empty, is [`resource/README.md`](resource/README.md).

## Requirements

Python ≥ 3.14 and [`uv`](https://docs.astral.sh/uv/). Node ≥ 24 for the render layer — supplied by the
parent. **No system `ffmpeg`.**

## Run

```bash
cd song-video
uv run sv build                                    # asks the four questions, records the answers
uv run sv build --song music --title "Dure Kothay" \
                --theme vinyl --theme neon --wave ribbon   # the same run, scriptable
uv run sv build --replay                           # re-runs the recorded answers; asks nothing
```

⚠️ **A recorded song replays rather than re-asks**, and a master whose `sha256` has changed is **refused** — the
recorded title, themes and wave form describe the take that was approved. To answer again, remove
`store/<song>/run.json`.

One command, by hand, no scheduler and no upload step (ADR 0004).
