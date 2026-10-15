# The covers were the card's thumbnail

Type: task
Status: resolved
Found by: 34

## Question

> comics cover image quality is not good please find good quality image

⚠️ *"Find a better image"* is a search, so the first move is to measure what the chart actually holds rather than to look
for new sources — the images may already be the right ones, fetched at the wrong size.

## Answer

### ⚠️ Every comics cover was a 300×200 thumbnail — and the wrong shape

Measured on the committed week, all **99** of the comics chart's covers:

```
n=99  min=240  median=300  max=300      ← every one 300×200
narrower than 400px: 99
```

⚠️ **300×200 is the *grid's* box, not a cover's shape** — a landscape 3:2 thumbnail of a portrait book — and the cause is
one URL suffix. `amazon.parse` took the card's `<img src>`, which is Amazon's own transformation:

```
…/images/I/71eJk7GtUOL._AC_UL300_SR300,200_.jpg     ← what the card's src says
```

⚠️ Measured on the **same asset**, four variants:

| URL | Dimensions | Bytes |
|---|---|---|
| `…UL300_SR300,200_.jpg` (the card's `src`) | **300 × 200** | 6 KB |
| `…UL900_SR900,600_.jpg` (the largest the card declares) | 900 × 600 | 30 KB |
| **`….jpg` (the token stripped)** | **1600 × 2155** | **201 KB** |
| `…UL1500_.jpg` | 1114 × 1500 | 104 KB |

⚠️ So the cover that reached the collage was **twenty-five times fewer pixels, in the aspect ratio of a card and not of a
book**. ⚠️ The token is a transformation the CDN applies, not a different file: stripping it asks for **what the card is a
thumbnail *of***.

### ✅ What changed

1. ⚠️ **`amazon.parse` strips the size token** (`_IMAGE_TOKEN` / `_cover_url`), matched on **Amazon's own path shape**,
   `/images/I/<id>._<token>.<ext>` — ⚠️ **not** on any dot-underscore, because a bookshop's `My._Book.jpg` is a real URL
   and stripping it would 404 the vendor the Bengali chart depends on.
2. ⚠️ ⚠️ **And the bytes had to move with the record.** The cover cache is keyed by **ISBN** and answers **before the
   network** (ticket 05's quota decision), so a fixed parser does not retroactively improve a cached cover — the row
   would keep pointing at a thumbnail URL while the cache held a thumbnail's bytes. ⚠️ A one-off migration (modelled on
   ticket 32's) re-downloaded the originals, replaced the cached bytes, and rewrote each row's **`url` and `sha256`**:

   ```
   2026-W41: replaced 195 covers, left 117 alone, 0 failed
   ```

   ⚠️ **Left alone** = the URL carries no token: Open Library, BoiChitro, Bangabani, Shopify — vendors whose URLs are
   already the original.
3. ✅ **Re-staged and re-rendered** (`--chart comics`): the same 99 covers now measure **min 645, median 1524, max
   2400**, in the books' own portrait shapes. ⚠️ The artefact grew with the detail — video **31.3 MB → 39.1 MB**,
   thumbnail **144 KB → 172 KB** — which is the extra information arriving rather than a change of encoding.

### ⚠️ What is still small, and why it is not the same problem

Of 378 staged covers, **42** remain under 600px:

| Source | Count | Why it stays |
|---|---|---|
| `boichitro.in` | 24 | ⚠️ **the bookseller's own upload is ~300px** — there is no larger copy of that image to ask for |
| `bangabani.in` | 1 | same |
| `covers.openlibrary.org` (`-L`) | 16 | ⚠️ Open Library's *large* is genuinely small for old paperbacks — and these rows are the ones where **Google Books answered `429`**, so the fallback is what ran |
| `images-eu…amazon.com` | 1 | ⚠️ `english #87` — its **original is 530px**; the tokenless URL *is* the ceiling, so nothing was lost |

⚠️ **So *"find a good quality image"* had two answers, and they are different facts**: where the image existed at a larger
size, we were asking for the wrong rendition (the comics chart, fixed); where it does not, the vendor's own upload is the
best that exists (the Bengali chart, unchanged).

### ⚠️ A latent defect this exposed, recorded rather than fixed

⚠️ **The cache is keyed by ISBN and shared across weeks, so the recorded URL and the cached bytes can disagree.** A week
that cached a *thumbnail* leaves those bytes in place for a later week that records the *original* URL — and
`download()` answers from the cache, so the later week silently gets the worse image under the better URL. ⚠️ It is the
same shape as the rest of this week's findings: two places holding one fact. ⚠️ Keying the cache by URL (or verifying the
recorded hash) is the fix, and it is a change to ticket 05's design rather than a repair.
