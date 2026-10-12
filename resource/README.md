# resource/ — operator-supplied assets

Drop licensed assets here. **The tool reads this folder and never fetches or generates these** — they are
inputs, not outputs. Everything here is gitignored except this file, because committing a music bed
publishes it.

## Expected files

| File | Purpose | Used by |
|---|---|---|
| `logo.svg` | the product mark | **both** the video and the thumbnail |
| `music.*` | the background bed | the video |

**`logo.svg` is preferred over PNG** — deliberate, not a preference. The mark is rendered at two very
different scales: a corner bug inside a 1920×1080 frame, and a thumbnail seen at roughly **210 px** in a
feed. A raster that looks right at one of those softens at the other; a vector holds both. If only a raster
exists, supply **≥1024 px with transparency**.

⚠️ **All text inside the SVG must be outlined to paths.** A mark depending on an embedded webfont renders
differently wherever that font is absent, which breaks the determinism every other element is held to. If
outlining is impossible, supply a **2× PNG** and treat that as the asset.

**`music.*` may be any container or codec `ffmpeg` reads.** The pipeline normalises rather than demanding a
format, so there is no right answer to guess at.

⚠️ **Where the toolchain comes from.** There is **no system `ffmpeg` prerequisite** — the tool uses the build
Remotion already ships in `node_modules/@remotion/compositor-*/ffmpeg`, which is present on any machine that can
render. To use a different one, set `MARKET_OVERVIEW_FFMPEG=/path/to/ffmpeg`.

⚠️ **Supply the longest master you have.** A track at least as long as the brief (currently ~175 s) is used as
supplied and simply faded out. Anything shorter has to be **looped**, and a loop point is audible in a way a fade
is not — the bundled build has no `acrossfade` filter, so the join cannot be smoothed. If you can only supply a
short bed, supply one that is written to loop.

## What the pipeline does to the bed

| Step | Value | Why |
|---|---|---|
| trim | to the brief's real length, from its own frame count | the music ends with the picture, not at the track's mercy |
| loudness | **−14 LUFS**, single-pass `loudnorm` | YouTube's own reference level — it turns loud down and never turns quiet up, so hitting it means the level shipped is the level heard |
| true peak | −1.5 dBTP | headroom for the AAC encode; clipping is unrecoverable |
| fade in | 1.5 s | |
| fade out | 4 s | the bed leaves before the music does — the long tail keeps the close card from sounding cut off |
| output | 48 kHz stereo, AAC 192 kbps | |

**One file, both editions.** The normalised bed is written once, above `bn/` and `en/`, and both editions mux from
it. So "both editions carry the same bed" is a fact about one file rather than a claim about two encodes matching.
It is removed when the run ends — it is scratch, and it lives in the folder a human opens to find the day's
deliverable.

To raise or lower the bed, change `TARGET_LUFS` in `src/market_overview/audio.py`.

## No variant is needed

The mark is drawn on a **chip whose fill the pipeline controls**, so it is never composited over arbitrary
card colours or the raw 3D scene. **One asset serves every card, both editions, the video and the still.**

The mark's **ink polarity is auto-detected** — there is nothing to declare up front:

| | |
|---|---|
| auto-detection | reads the SVG's dominant `fill` (or a gradient's `stop-color`) and takes its luminance |
| override | `MARKET_OVERVIEW_LOGO_INK=light` or `=dark` — needed only for a **raster**, whose ink cannot be read |

A light mark gets a dark chip and a dark mark gets a light chip, so contrast is computed rather than judged.
**Nothing needs declaring** unless you supply a PNG.

## Absent is a supported state

With no `logo.svg` (or `logo.png`) and no `music.*`, **the brief still renders** — no mark, no music. That is
deliberate: the assets are yours to drop in, and a missing one is a brief without branding, or a silent one,
rather than a failed run. Adding either later changes nothing else about the output.

The day the music lands, the run starts printing what it did — `music: music.wav → .bed.wav (-14 LUFS, 175s,
fade 1.5/4s)` — because a bed at the wrong level is the one defect that is invisible in a still and in a diff.

## Rules

- **Never modified in place.** The pipeline reads, normalises and writes derived audio into the run's temp
  directory. The supplied file is the master.
- **Language-neutral.** Both editions use the same bed and the same mark — no per-language variants. This is
  what keeps the bilingual pair honest at the branding layer.
- **Licence is the operator's.** The pipeline records no licence metadata and enforces nothing. The operator
  declares these assets are licensed for this product **including publication**.
- **Determinism.** The bed's start offset is a **constant**, and the trim, the level and the fades are all pure
  functions of (master, run length) — no clock and no randomness — so a re-render lands the music identically.
  Measured, not assumed: two normalisations of the same master are compared byte for byte in `tests/test_audio.py`.
