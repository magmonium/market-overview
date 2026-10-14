# 0006 — The envelope is the only clock

- Status: accepted
- Date: 2026-10-13

## Context

The ask wanted the picture to move with the music. The available ways to do that are a spectrum, and the loud end
of it is well-trodden: detect onsets, estimate a tempo, cut on beats, build a grid.

None of those describe this product. A four-minute piece with no voice, no lyrics, no captions and no sections is
one continuous landscape; a beat grid would impose a rhythm the song may not have, and a section analysis would
reformat the picture into an argument the operator never asked it to make.

## Decision

**One amplitude per frame, and nothing else.** The envelope *is* the timeline:

- analysed **inside the renderer** (Remotion's audio API), sampled at the render's own frame rate, so frame →
  amplitude is a pure lookup;
- the analysis **waits or refuses** — a render never draws a wave made of nothing;
- the piece's length is **Python's** measurement (`master.frames` over the ffprobe duration), and the envelope is
  **indexed against that length and never the reverse**, so a decoder that is one frame out of step cannot feed
  `undefined` into a coordinate;
- ⚠️ **`beat` is not in this vocabulary.** There is no beat grid, no onset detection and nothing cuts on a beat —
  the word would describe a product this is not, so it is struck rather than qualified.

## Consequences

- ⚠️ **Peak normalisation crushed the song's shape, and the fix lives in the themes.** The first real frame rendered
  as a near-solid block with its texture squeezed into the top fifth: one loud moment owned the whole scale, and the
  song's landscape — the thing this product exists to show — became a rectangle. The clock must stay physically
  honest, so every theme owns a **curve** that lifts the middle and pins both ends (0 stays 0, 1 stays 1), asserted
  as a property rather than admired in a still.
- ⚠️ **Determinism comes for free and must be kept**: no wall clock, no `Date.now()`, no unseeded randomness. The
  notes' scatter is low-discrepancy irrational sequences (`φ`, `√2`, `√3`) rather than a PRNG, which is why nothing
  in this project ever draws a different picture from the same props.
- **The audio analysis is reduced once per change, not once per frame** (`useMemo`), and the decode is pinned to
  48 kHz: the landscape is frame-independent by construction, so re-deriving it 7201 times would be work for
  nothing.
- **A reader in a year should read this ADR twice.** It is the decision that gives the product its calm and its
  reproducibility at once, and it is the one most likely to be reopened by somebody who wants the visuals to hit
  harder — which is a different product, and a legitimate one, and not this.
