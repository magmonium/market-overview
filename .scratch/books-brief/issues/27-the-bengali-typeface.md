# The Bengali typeface

Type: task
Status: resolved

## Question

*"bengali one will be created on bengali font make sure"* — the Bengali chart must render in a Bengali face. ⚠️ The
host repo already has exactly this, and its own history **is about Bengali** — so this ticket is mostly about **not
re-solving it**, and about one trap that is easy to walk into.

## Answer

### ✅ The face already exists, vendored, in this repository

`remotion/fonts/` holds **nine committed `.woff2` files** — three weights × three subsets — described once in
`remotion/fonts.json`:

| Subset | Weights | Carries |
|---|---|---|
| **bengali** | 400 / 600 / 700 | Bengali **and `₹`** — ⚠️ **and no Latin** |
| **latin** | 400 / 600 / 700 | the digits, the slugs, and the `−` (U+2212) |
| **latin-ext** | 400 / 600 / 700 | accented Latin |

- **Noto Sans Bengali**, chosen for a reason that matters here: it is **SIL OFL 1.1**, so the bytes may live in the
  repo, and it is *the* reference Bengali face — which makes *"what does this look like elsewhere"* answerable.
- ⚠️ **Vendored, not fetched.** `@remotion/google-fonts` would fetch at render time, and both the suite and the
  re-render promise are meant to need no network.
- ⚠️ **The weights are baked, not interpolated** (`fonts/instance.py`): leaving the browser to instance `wght` was
  *measured* to shift the 200 px figure by ~100 pixels at ±2/255 between a cold and a warm cache — which broke
  byte-for-byte rebuilds and nothing else.

### ⚠️ The trap: the Bengali subset has **no Latin**, and this chart needs both

⚠️ **This is the thing to make sure of.** A Bengali chart's slide prints, on one frame:

- the **book title, author and publisher** — Bengali ✅
- ⚠️ the **rank numeral** (`7`), the **price digits** (`399`), the **`₹`**, the **`−`** in a negative Δ, `WEEK 41`, and
  the whole **ticker** (`NIFTY 24,812`) — **Latin**

So the Bengali chart must load **both** subsets. ⚠️ A `books-brief/remotion/` that vendored *only* the Bengali subset —
the natural mistake, since it is the Bengali chart — would render **every digit, the `₹`, and the entire header in a
fallback face**, which is exactly what `fonts.ts` warns about: *"Dropping either leaves half of an edition in a fallback
face — the failure this module exists to prevent."*

⚠️ And the wait is not optional. `useFonts` loads against a **`SAMPLE` that spans both subsets**, because
`document.fonts.load` with no text argument resolves against the face covering a *space* — Latin — leaving every Bengali
glyph to load lazily **after the first frame was captured**. The chart would ship the fallback face while every test
passed.

### ⚠️ And it **refuses** rather than falls back

`useFonts` calls `cancelRender` on failure, not a quiet `system-ui`: *"a brief set in the wrong face is the same 'looks
right here and different elsewhere' defect the logo's outline check refuses for."* ⚠️ A missing face is therefore a
**refused run**, not a slightly-wrong video — the correct failure for a product whose whole point is being trustworthy.

### Where the bytes come from: **the brief's**, not a copy

⚠️ The bytes are read through `shared_remotion()` (ticket 09) — *"the brief's `remotion/` — vendored fonts and the
seeded PRNG"* — and **`fonts.json` is the single manifest both sides read**. A second copy of the ranges would drift,
and the drift would present as a **passing** budget: `copybudget.py` opens a browser *"because only the browser knows
the face's metrics"*, so the measuring browser and the renderer must measure the **same** face. ⚠️ That is also what
makes ticket 07's title clamp (72 → 60 → 52) a real measurement rather than a guess.

### ⚠️ One decision this surfaces: **numerals**

⚠️ **Both digit sets exist in the vendored face** — Latin `0123456789` (U+0030–0039) and Bengali `০১২৩৪৫৬৭৮৯`
(U+09E6–09EF) — so the question is open, and it had not been asked before now.

**Decided: the Bengali chart renders its data numerals in Bengali.** Rank, price, Δ and the week number use
`০১২৩৪৫৬৭৮৯`, matching `song-video`'s `caption.DIGITS`, which already fixes `০` as U+09E6 in one place for the reel's
caption. ⚠️ The **YouTube title stays Latin** (`Top 100 Bengali Books | Week 41 | …`, ticket 15), because that string is
for **search**, not for reading.

⚠️ The split is deliberate: **the title is the product's; the slide is the reader's.**

### What it means for the other three charts

Nothing. They are Latin-only, so they load the latin and latin-ext subsets — the case `fonts.ts` already handles — and
⚠️ the **same** vendored face serves them, so a re-render of any chart is byte-for-byte reproducible (ADR 0003,
`test_frame_identity.py`).
