# The typeface — Noto Sans Bengali, vendored

**These files are the brief's face, committed, because the alternative is a face that belongs to the machine.**

Until `docs/adr/0005`, the renderer named macOS's own *Kohinoor Bangla* and let the system font directory
resolve it. That made the rendered pixels a property of the host: the same `facts.json` rendered different
glyphs on Linux, where the name resolves to nothing and the stack quietly supplies something else. It broke two
guarantees at once — ADR 0003's "a re-render from the snapshot is a guaranteed match", and
`tests/test_frame_identity.py`.

## What is here

| File | What it is |
|---|---|
| `NotoSansBengali-<subset>-<weight>.woff2` | The face, **one file per subset per weight** — 3 subsets × 3 weights |
| `instance.py` | How the nine were produced. A record, not a pipeline step |
| `../fonts.json` | The manifest: family, every face, its weight and its `unicode-range` |
| `OFL.txt` | SIL Open Font License 1.1, Copyright 2022 The Noto Project Authors |

The manifest is read by **both** sides — `../fonts.ts` builds the renderer's `@font-face` rules from it and
`src/market_overview/copybudget.py` builds the measuring browser's from the same file — because the copy-budget
gate's whole premise is that it measures the face the brief is *set* in. `tests/test_fonts.py` pins the manifest
against the imports.

## The three subsets, and why they are three

Google ships the family split by script, and **the split is not decorative**:

- `bengali` carries Bengali and `₹` — and **no Latin at all**.
- `latin` carries the digits, the index slugs, `DII`, and the `−` (U+2212) the brief prints.
- `latin-ext` carries the European diacritics the copy does not currently use, kept so a missing glyph is never
  the reason a future string renders in a different face.

Dropping either of the first two leaves half of an edition in a fallback face, on some machines and not others.

## Why the weights are baked rather than interpolated

Google serves this family as one **variable** font with a `wght` axis of 100–900, and the `wght@400;600;700`
query returns the *same file* three times. Letting the browser instance that axis at render time was measured
**not to be stable**: the large figure — 200 px at weight 700 — moved by about a hundred pixels at ±2/255 along
its glyph edges between a cold and a warm browser cache. Nothing a viewer could see, and enough to break a
byte-for-byte rebuild.

`instance.py` bakes the three weights out of the variable file, so the browser is handed a static face and never
touches an axis. That also removes a browser capability from the determinism story, which is the point: a
Chromium on a Linux server has to produce the same glyphs as one on the operator's laptop, and a static face
leaves it nothing to decide.

## Regenerating

```bash
uv run --with fonttools --with brotli python remotion/fonts/instance.py
```

⚠️ Run `instance.py` **before** deleting the variable files it reads — it takes
`NotoSansBengali-<subset>.woff2` as input, and those are no longer committed now that the instances are.

To move version, change the URL in `instance.py`'s source fetch (see the file) and re-bake every subset; the
`unicode-range`s in `../fonts.json` come from Google's own CSS and must be refreshed from it at the same time.
