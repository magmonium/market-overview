# The enrichment pipeline

Type: research
Status: resolved
Blocked by: 02

## Question

Three things the chart sources do not reliably give, and each needs a rule:

1. **Cover art** — download-and-embed, or hotlink? The free options are Open Library
   (`https://covers.openlibrary.org/b/isbn/<isbn>-L.jpg`; **100 req/IP per 5 min**, a blank image when the cover is
   missing, `?default=false` to get a 404 instead) and Google Books `imageLinks`. Covers are copyrighted — what
   attribution is shown on the slide, and does the renderer embed a data URI (as `logo.load` does for the mark) or
   read from the data root?
2. **Publication month and date** — NYT carries no per-book pub date; Google Books `volumeInfo.publishedDate` does,
   sometimes as `YYYY` alone. What renders for a year-only or absent date?
3. **Identity** — the ISBN that keys dedupe, the Δ diff, and the cover lookup. What happens to a title that has no
   ISBN at all?

## Answer

### 1 — Covers: download-and-embed, cached by ISBN

⚠️ **Not hotlinked.** The host repo's precedent is unambiguous: `logo.load` inlines the mark as a **data URI**, the
music bed is muxed, `public/` is explicitly *preview scaffolding only*, and `store/` exists so that *"a video has to be
rebuildable without re-fetching"*. A renderer that reaches the network for 100 covers per chart breaks all three.

**The cache is keyed by ISBN, not by week** — a cover is immutable per ISBN, so it is fetched once and reused forever.
Location: the **data root** (ADR 0007 — binary assets do not belong in the repository):

```
$MARKET_OVERVIEW_DATA/resource/books/covers/<isbn13>.jpg
```

⚠️ **But the snapshot records where the cover came from** — the source URL and a content hash, in
`store/<week>/facts.json`. That is what keeps a rebuild possible **without committing 400 images a week**: the
*evidence* is committed, the *bytes* are cached.

**Source order:** **Google Books `imageLinks`** first (the volume is already in hand from the identity lookup), then
**Open Library** (`covers.openlibrary.org/b/isbn/<isbn>-L.jpg`) as the fallback.

Three normalisations that matter:
- ⚠️ **`http://` → `https://`**, and **strip `edge=curl`** from the Google Books URL — it adds a decorative
  curled-page-edge effect that is wrong for a clean cover.
- ⚠️ Raise `zoom` for a print-quality image — the default thumbnail is too small to sit on a slide.
- ⚠️ On Open Library, append **`?default=false`** so a missing cover returns **404** instead of a **blank image**. A
  blank that renders silently is exactly the failure this pipeline must not have. (Respect 100 req/IP per 5 min.)

**Attribution.** Covers are copyrighted. One credit line — *"Covers: Google Books / Open Library"* — goes in the
**description**, which already carries the full list (ticket 15), with Open Library's courtesy link back.

### 2 — Publication month and date: render the precision that exists

Google Books `volumeInfo.publishedDate` arrives at three precisions:

| Source gives | The slide renders |
|---|---|
| `2026-10-14` | **14 Oct 2026** |
| `2026-10` | **Oct 2026** |
| `2026` | **2026** |
| nothing | the field is **omitted** — never blank-filled, never guessed |

⚠️ **Trap:** NYT's list response carries a `published_date` that is the **list's** date, not the book's. Using it would
stamp every book on the chart with the same publication date. Google Books is the source for this field; PW's pub date
can corroborate.

### 3 — Identity: the finding that shapes this whole ticket

⚠️ **The primary chart source does not give ISBNs.** Amazon.in's bestseller listing carries title, author, rating,
format and price — **no ISBN**. But the dedupe key is **chart + ISBN** (ticket 14), and the cover lookup needs an ISBN.

**So the enrichment pipeline is also the identity-resolution step:**

```
title + author  →  Google Books (q=intitle:…+inauthor:…)  →  ISBN-13
```

- Normalise **ISBN-10 → ISBN-13** before it is ever used as a key.
- ⚠️ **Identity resolution can be wrong**, and a mis-match cascades: the wrong cover, the wrong pub date, and a
  corrupted week-over-week diff. So an identity must pass the **same corroboration discipline as the chart** (ticket
  17) — a match confirmed by **two** sources, never a single fuzzy title search.
- **No ISBN at all** → fall back to normalised `title + author` as the identity key and mark the entry
  **`identity: unresolved`** in the snapshot, so the weakness is visible rather than silent.

### 4 — What this hands to the thumbnail collage (ticket 16)

⚠️ Some of the 100 will have **no cover**. The pipeline must therefore publish a **coverage count per chart**
(*"97/100 covers"*) in `facts.json`, so ticket 16's missing-cover rule has a number to work with rather than a
surprise.

### Bonus — the superset pays for itself

Because the cache is keyed by ISBN, a title in both the Bengali and the all-language chart (ticket 14) is fetched
**once**. The duplication the superset creates lives in the *chart*, not in the *fetch*.
