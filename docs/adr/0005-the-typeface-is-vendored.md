# 0005 — The typeface is vendored, not the platform's

- Status: accepted
- Date: 2026-12-12

## Context

The renderer named the font in CSS and let the host resolve it:

```ts
export const FONT = '"Kohinoor Bangla", system-ui, -apple-system, sans-serif';
```

*Kohinoor Bangla* is an **Apple-bundled** macOS face. It is also the face the copy budget measures against —
`copybudget.py` opens a browser precisely because "only the browser knows the face's metrics", and Bengali
conjuncts make width-per-character nothing like English's.

That arrangement is indistinguishable from correct on the machine it was written on, and wrong everywhere else.
On Linux the name resolves to nothing, `system-ui` silently supplies a different face, and:

- **ADR 0003's promise breaks.** "A re-render from the snapshot is a guaranteed match" is about *frames*, and
  the frames now depend on the host's font directory.
- **`test_frame_identity.py` becomes meaningless.** It compares renders for equality; if the face is the
  machine's, so is the answer.
- **The copy-budget gate measures a face the render may not use.** It would keep reporting a comfortable,
  correct-looking budget for a *different* typeface.
- The README's one check that has no proxy — *"The Bengali reads as Bengali, not as translated English"* — is
  still true, but the pixels underneath it are not.

The second fact is what forced the change: **the brief is going to render on a Linux server** (`docs/adr/0006`).
There is no version of that in which the face can stay the platform's.

## Decision

**The face is Noto Sans Bengali, vendored into `remotion/fonts/` and committed, one file per subset per weight,
described once in `remotion/fonts.json` and loaded by both the renderer and the measuring browser.**

- **Noto Sans Bengali**, because it is **SIL OFL 1.1** — redistributable, so the bytes can live in the repo — and
  it is the reference Bengali face, which makes "what does this look like elsewhere" answerable.
- **Vendored, not fetched.** `@remotion/google-fonts` would fetch at render time, and the suite and the
  re-render promise are both meant to need no network. Committing 185 KB keeps both true.
- **One file per subset per weight, baked rather than interpolated.** Google serves the family as a single
  *variable* font (`wght` 100–900) and returns the same file for `400`, `600` and `700`. Leaving the browser to
  instance that axis was **measured** to be unstable: the large figure — 200 px at weight 700 — moved by ~100
  pixels at ±2/255 along its glyph edges between a cold and a warm browser cache, which broke the still's
  byte-for-byte rebuild and nothing else. `remotion/fonts/instance.py` bakes the weights; the browser is handed
  a static face and never touches an axis.
- **The `unicode-range` split is data, in `fonts.json`.** The Bengali subset carries Bengali and `₹` and *no
  Latin*; the Latin subset carries the digits, the index slugs and the `−` (U+2212). Both sides read the same
  manifest, and `tests/test_fonts.py` pins the manifest against the imports in both directions.

## Consequences

- **A render no longer depends on the host's fonts.** The same `facts.json` gives the same glyphs on macOS and
  on a Linux server, which is what makes ADR 0006 possible at all.
- **`test_frame_identity.py`'s still assertion is a real check again**, and it now measures the *vendored* face.
- **The copy budget measures the renderer's own bytes**, by construction rather than by convention.
- ⚠️ **The delivered artefacts for `2026-10-12` were re-rendered.** The still and the video in `output/` are
  gitignored and were rebuilt from the snapshot, so nothing was fetched to do it — which is ADR 0003 working.
- ⚠️ **A face update is now a commit.** Google's `unicode-range`s must be refreshed from its CSS at the same
  time as the files, and the README's typeface section says how.
- **Cost:** 185 KB of committed binary, and the brief's Bengali is set in a different face than it was for the
  first two deliveries. That is a visible change to the product, taken deliberately, in exchange for the same
  face everywhere.
