# The publish targets

Type: grilling
Status: resolved

## Question

Every package is built to be handed to an uploader — ticket 15 writes `metadata-<chart>.json` carrying the
**`bundle_hash`** and naming the video and thumbnail explicitly, *"self-contained by construction."* But **which
uploader** has never been decided, and it changes real things:

- ⚠️ **The metadata schema's consumer.** YouTube takes a title, a description, tags and a thumbnail; Instagram takes a
  caption and a carousel; a file-only drop takes nothing.
- ⚠️ **The idempotence key** (ticket 10) exists *because* a publish needs it. File-only delivery does not.
- ⚠️ **`--privacy`, defaulting to `private`** (ticket 10), is a YouTube concept.
- ⚠️ **The carousel** — ticket 06's stills render for free — needs a social target to be worth producing.

The brief already has the shape: `publish.py` with a deferred, hash-keyed, idempotent upload, and `song-video`'s
`seo.py` for the text.

## Options

1. **File-only** — the package is the deliverable; a human uploads it.
2. **YouTube**, one video per chart, `private` by default — the brief's own pattern.
3. **YouTube + a social carousel** built from the same composition (ticket 06's stills).
4. **Several, per chart** — e.g. the Bengali chart to a regional channel, English to another.

## Answer

### **YouTube, one video per chart, `private` by default** — the brief's own pattern

Everything already points there, and none of it is a coincidence:

- ⚠️ **Ticket 15's metadata is YouTube-shaped** — a 100-character title, a 5,000-character description, a
  500-*character* tag budget, exactly 3 hashtags. Those are YouTube's numbers, taken from the brief's own `metadata.py`.
- ⚠️ **Ticket 10's idempotence key exists *because* a publish needs it** — *"a re-run of the same week posts nothing,
  and a rebuilt week refuses rather than putting two different charts under one title."* File-only delivery has no such
  problem and needs no such key.
- ⚠️ **`--privacy` is a YouTube concept**, and the brief already defaults it to `private` for a reason that transfers
  exactly (below).
- ⚠️ **The brief's shape is two commands and one wrapper**: `daily-brief.sh` runs `build` then `publish`, and ADR 0006
  says *"the upload is part of the run."* So books-brief gets `build --week` and `publish --week`, and the weekly timer
  runs both.

### ⚠️ And `private` by default, for the brief's own reason

ADR 0006's sharpest line: *"ADR 0004's real protection was never the window server; it is the README's 'Before you
publish' list… **the reason a human runs it**. Uploading straight to `public` on a timer deletes that check without
saying so."*

⚠️ The books equivalent is exactly the check this map has been building toward: **is the Bengali chart actually
Bengali, are the covers the right books, is the rank plausible, and does the footer name the right sources.** So
`private` until the operator decides otherwise — and the switch is **one environment variable**, not a code change.

### One channel by default — and the per-chart packages make that a setting

⚠️ **One channel**, not four. But the packages are already **per chart** (ticket 13) and the metadata is
**self-contained** (ticket 15), so routing the Bengali chart to a regional channel later is a **configuration change,
not a redesign** — the brief's own reasoning about `--lang`: *"the schedule must not rely on a default that was chosen
to keep a re-cut cheap."*

### ⚠️ The carousel is **deferred**, not built

Ticket 06 noted the stills render from the same composition *"for the price of a loop."* ⚠️ **That price is not free at
this scale**: 100 slides × 4 charts is **400 stills a week**, and with no social target they have nowhere to go.

So **the stills are not rendered until a social account exists.** When one does, the composition already produces them —
which is what *"one composition, two outputs"* bought, and it is worth having bought it **before** needing it.

### What the package must therefore contain

Mirroring the brief's `output/brief/<date>/<lang>/` — four files and nothing else:

```
output/books/2026-W41/bengali/
├── top-100-bengali-books-2026-W41.mp4      the video
├── thumbnail-2026-W41-bengali.jpg          the collage (ticket 16)
├── metadata-bengali.txt                    for a human to paste
└── metadata-bengali.json                   for the uploader: title, description,
                                            tags, hashtags, video, thumbnail, bundle_hash
```

⚠️ **Named explicitly**, so an uploader needs nothing but the chart folder — ticket 15's *"self-contained by
construction."*
