# The thumbnail collage

Type: prototype
Status: resolved
Blocked by: 05, 13

## Question

The thumbnail is a **collage of the covers of all the books** in the chart — "beautiful", and built from 100 covers.

The hard part is not beauty, it is **legibility at 320×180**: a 10×10 grid of 100 covers turns every cover into a
smudge. So this ticket settles the composition rule:

- **How many covers** make the collage — all 100, or the top N (say 12–25) arranged large with the rest as a mosaic
  beneath? *"All books"* is the brief's ask; legibility is the constraint, and the two must be reconciled explicitly.
- **Grid** — a clean grid, a hero + mosaic, a fan/spiral, or a cover-flow?
- **Where the title sits** — `TOP 100 BENGALI BOOKS`, the week and the date, over the collage.
- ⚠️ **Missing covers** — ticket 05 will find that some of the 100 have no cover at all. What fills the gap: a
  typographic placeholder, a branded blank, or exclusion from the collage?
- ⚠️ **"Is there a master thumbnail for the whole week?" — NO (settled by ticket 13).** There are **four videos**, one
  per chart, so there are **four thumbnails** — a thumbnail fronts the video it belongs to, and a "week thumbnail"
  would front nothing. Each chart's collage rides with that chart's package in
  `output/books/<week>/<chart>/`.

Reuses `remotion/Thumbnail.tsx` and the `logo.load` data-URI habit for the mark.

## Answer

### ⚠️ First, the number this ticket got wrong

It asks about legibility at *"320×180"*. The brief's own thumbnail has the real figure, and it is **measured**: *"200 px
renders at ~33 px at the **210 px a feed shows it at** — not merely legible, unmistakable."* The frame is 1280×720; the
**feed shows it at 210 px wide**. That is the size every decision below is judged at.

### ⚠️ The arithmetic of "all books"

At 210 px, a 10×10 grid of 100 covers gives each cover **21 px**. That is a colour swatch, not a cover — no title, no
author, nothing recognisable. So the brief's ask and the medium's limit genuinely conflict, and the resolution is not to
drop either:

> **All 100 covers appear; only the top few are legible.**

```
┌──────────────────────────────────────────────────────────────┐
│ TOP 100 BENGALI BOOKS                    ┌─────────────────┐ │
│ WEEK 41 · 14 OCT 2026                    │  mark @ 128 px  │ │
│                                          └─────────────────┘ │
│    ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐              │
│    │  1   │ │  2   │ │  3   │ │  4   │ │  5   │   ← hero row │
│    └──────┘ └──────┘ └──────┘ └──────┘ └──────┘              │
│                                                              │
│  ░░░ mosaic of the remaining 95, dimmed to a texture ░░░░░░  │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
│                       [ duration badge ] [ progress bar ]    │
└──────────────────────────────────────────────────────────────┘
```

- **The hero row** — the top **5** covers, large enough that each is still an *image* at 210 px rather than a dot.
- **The mosaic** — the other 95, in the lower band, **deliberately dimmed to a colour field**. It is the *texture*, not
  the content: it is what makes the thumbnail read as a chart of many books, and it is honest, because every one of the
  hundred is genuinely in it.

⚠️ The mosaic takes the lower band the video's **backdrop** occupies — and keeps its degrade behaviour: where the layer
misbehaves, the still falls back to type over a flat field. *"A plainer thumbnail, not a missing one."*

### The rules it inherits, unchanged

- ⚠️ **A dedicated composition, never a frame grabbed from the video** — *"a grabbed frame is composed for motion… and
  it may be caught half-settled."*
- ⚠️ **3–6 words and one idea.** `TOP 100 BENGALI BOOKS` + `WEEK 41 · 14 OCT 2026` is that idea. The collage is the
  image; the text does not compete with it.
- ⚠️ **YouTube owns the bottom-right (duration badge) and the bottom strip (progress bar).** The mosaic ends above them,
  and the mark stays **top-right at 128 px** — issue 21's *still* size, not the video's.
- ⚠️ **The four thumbnails render before the four videos** (ticket 13 makes four of each). The reel's rule: *"N
  one-frame stills cost seconds; a theme that reads badly should be seen and killed before an hour of frames is spent on
  it."*
- ⚠️ **Nothing lands in a package until it is whole** — a dot-prefixed sibling, moved into place once it exists and
  passes its checks, so a failed run leaves the previous week's thumbnail untouched.

### ⚠️ Missing covers — and the count that makes it safe

Ticket 05 hands this ticket a **cover-coverage count** per chart, so the rule has a number rather than a surprise. A
missing cover is filled by the **same branded tile as the slide** (ticket 07) — the book's initial on `BG` with a `RULE`
border — so the two surfaces agree instead of each inventing a placeholder. ⚠️ Never a blank box, never a stock "no
image" glyph.

⚠️ And if a chart's coverage is low enough that the hero row is mostly placeholder, the thumbnail is not
representative — so the count is **reported**, and a chart below a stated floor is one to look at before publishing.

### ⚠️ The byte ceiling

100 covers in one still is a real size problem, and the brief already has the constant: **`MAX_STILL_BYTES`**, with a
pinned `JPEG_QUALITY`. The mosaic tiles are downscaled hard — they are 21 px of texture and need no more — and the fit
is **checked, not hoped for**.
