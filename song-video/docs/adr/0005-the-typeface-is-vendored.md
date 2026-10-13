# 0005 — The typeface is vendored

- Status: accepted
- Date: 2026-10-13

## Context

A render that resolves fonts from the host produces a video that looks right on the machine that made it and
different everywhere else — and nothing downstream would ever notice, because both videos are "correct".

The brief settled this in its own ADR 0005 and vendored the weights it draws with. The reel needs the same
guarantee and, more unusually, needs it for **pictures** as well as text.

## Decision

**The committed faces are the only faces a render may use**, and the reel imports the brief's vendored set rather
than vendoring a second one: one licensed collection, one place to change it.

Text is drawn through the brief's `Typeface` component, which waits for the faces and **refuses rather than
substituting**. The reel's own iconography — the notes — is drawn as **shapes**, never as glyphs.

## Consequences

- ⚠️ **The notes motif is geometry, not a character.** A `🎵` would be a request to whatever emoji font the host
  happens to have: legible on the operator's laptop, tofu on a server, and a different drawing on every platform —
  in a motif whose whole job is to be the same moving object on every render.
- **A still is not exempt.** The thumbnail waits for the same faces, because the still is the one artefact a human
  looks at *before* hearing the song, and a wrong typeface there is the most visible failure in the product.
- **The icons inherit the theme's palette** for free, which a glyph cannot: a note is drawn in the theme's own ink
  and accent, so `neon` and `aurora` scatter notes that belong to their palettes rather than a system font's idea of
  a musical note.
- **One consequence is a constraint on future themes**: a new motif is *new code*, not a new emoji, and that is the
  intent rather than the cost — the catalogue is hand-authored on purpose.
