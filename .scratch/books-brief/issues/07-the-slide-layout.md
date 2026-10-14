# The slide layout

Type: prototype
Status: resolved
Blocked by: 06

## Question

The one slide, designed. Every requested field has to sit on it **beautifully**:

> cover · best price · publisher · author · rank · Δ against the comparison window · NEW badge ·
> publication month and date

…over a background carrying the **misc** (a stock brief) and the **logo**.

## Deliverable

A layout sketch — a static mock, or a Remotion prototype driven by a hand-written `facts.json` — plus the rules for
the awkward cases: a very long title, a very long author list, a missing price, a missing cover, and a rank with no
previous period (which must read as NEW, not as a blank Δ).

Reuses `remotion/theme.ts`, `Brand.tsx`, `Furniture.tsx`, the vendored fonts, and the label-table habit from
`copy.bn.json` / `copy.en.json`.

## Answer

⚠️ Per the map's Notes (*decisions, not deliverables*), this is the **layout decision**; the visual mock belongs to
implementation and stays out of scope.

### Two regions the host repo has already reserved

- ⚠️ **The mark owns the top-right `260 × 160`** at `x ≥ 1660, y ≤ 160` (issue 21's verdict table, asserted by
  `tests/safe_area.py`). `Brand.tsx` renders it **once above the whole run**, not per slide.
- ⚠️ **The footer is the disclosure register** — `Card` puts `copy.disclosure` left and the attribution right.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  TOP 100 BENGALI BOOKS · WEEK 41                ┌───────────────────────────┐  │
│                                                 │   reserved mark area      │  │
│                                                 │   260 × 160 (Brand.tsx)   │  │
│                                                 └───────────────────────────┘  │
│   ┌────────────────────┐                                                       │
│   │                    │        7      ▲ 3                                    │
│   │                    │    ──────────────────────────────                     │
│   │       COVER        │    Ekti Shonar Boi                                   │
│   │                    │    Sunil Gangopadhyay                                │
│   │    (left, 34 %)    │                                                      │
│   │                    │    Ananda Publishers                                 │
│   │                    │    ₹399 · Amazon · Paperback                         │
│   │                    │    Oct 2026                                          │
│   └────────────────────┘                                                       │
│                                                                                │
│  ──────────────────────────────────────────────────────────────────────────    │
│  NIFTY 24,812 ▲0.42   SENSEX 81,004 ▲0.31   USDINR 83.21 ▼0.08   ← ticket 08  │
│  ──────────────────────────────────────────────────────────────────────────    │
│  Sources: Amazon.in · Anandabazar · NYT      Ranked by weekly sales    Week 41 │
└────────────────────────────────────────────────────────────────────────────────┘
```

**One idea per register:** header = *which chart*; main = *the book*; ticker band = *the world*; footer = *how we know*.

### Type scale — anchored to `Card`'s own numbers

`Card` uses `fontSize: 46` for a block title, `24` for the footer, `padding: 64px 96px 88px`. The slide keeps those
anchors and adds **one dominant element**:

| Element | Size | Colour | Note |
|---|---|---|---|
| Chart header | 34 | `INK`, letter-spaced | `TOP 100 BENGALI BOOKS · WEEK 41` |
| **Rank numeral** | **220** | `INK` | the slide is *about* this number |
| Δ | 44 | `GREEN`/`RED` via `tone()` | |
| **NEW** | 44 | ⚠️ **neither** | see below |
| Book title | 72 → 60 → 52 | `INK` | clamped |
| Author | 42 | `MUTED` | |
| Publisher | 34 | `MUTED` | |
| Price | 52 | `INK`, tabular | reuse `crore()` — already `₹` in `en-IN` |
| Pub date | 32 | `MUTED` | |
| Ticker | 26 | `MUTED`, tabular | |
| Footer | 24 | `MUTED` | inherited |

### ⚠️ NEW must not be green

`GREEN`/`RED` mean **up/down**, and a new entry has *no* direction — a NEW badge in `GREEN` would read as *"it rose"*,
which is false. **NEW is an inverted chip against `BG`**, drawn from neither half of the pair. That also keeps the
palette's colour-blind promise intact (the pair is separable by lightness as well as hue; a third colour would muddy
it).

### ⚠️ The motion rule — the brief's own comment predicts the failure

`enter()` defaults to `span = 0.4 s`, and its comment says: *"an entrance that runs for a fifth of a card eats a fifth
of the time there is to read a number."* At ticket 06's dwell a tail slide is **1.0 s**, so that default would eat
**40 %** of the only time there is to read a publisher:

```
span = min(0.4, dwell_seconds × 0.15)      # ceiling: 15 % of the dwell, never more
```
3.5 s → 0.4 s (capped). **1.0 s → 0.15 s.**

### The awkward cases, ruled

1. **Long title** — 2-line clamp; 72 → 60 → 52; then ellipsis. ⚠️ The full title survives in the **description**.
2. **Long author list** — 1 line, ellipsis. ⚠️ Amazon.in really does say *"Multiple Writers"* — a live case.
3. **Missing price** — `—`. ⚠️ Never `₹0`. `percent()`/`number()` already return `'—'` for null; reuse, don't re-decide.
4. **Missing cover** — a **branded tile**: the book's initial, `BG` fill, `RULE` border. ⚠️ Never a blank white box.
5. **NEW** — replaces the Δ slot. ⚠️ **Never a blank Δ, and never `▲0`.**
6. **Missing pub date** — omitted; the price line moves up, leaving no hole.
7. **Unresolved identity** — invisible on screen; flagged in the snapshot (ticket 05).

### What it reuses

`theme.ts` — `INK` `MUTED` `GREEN` `RED` `BG` `RULE`, the `SCRIM*` family, `FONT`, and the formatters `crore()`
(`₹` + `en-IN`), `percent()` (U+2212 minus, `'—'` for null), `tone()`, `seeded()`.
`Furniture.tsx` — the `Card` shell and `enter()`, with the span rule above.
`Brand.tsx` — the mark, once per run. `Backdrop.tsx` — the layer the ticker sits in (ticket 08).

### ⚠️ Three optional label slots, arrived from tickets 20 and 26

The brief asked the charts to *"mention country language"* and then to *"also mention type of book"*. They are
**labels, not charts**, so they are three more fields in the data column — **country**, **language** and **genre** — and
⚠️ **they render only where they vary** (ticket 20):

- the **country** on the Bengali chart (India / Bangladesh);
- the **language** on the all-language and comics charts;
- ⚠️ and the **genre** (ticket 26) on **every** chart — it is the one label that **always** varies, so its slot always
  draws.

⚠️ **No new layout rule is needed**, and that is the point: ticket 07 already rules that a field with no value is
**omitted without leaving a hole**, and a *constant* label is the same case. The slot simply does not render.

⚠️ A third slot — **state** — was raised and not confirmed (ticket 20). It costs one more optional field if it is ever
wanted, and nothing if it is not.

### ⚠️ Correction, arrived from ticket 09

Ticket 09 established that a nested product has its **own `remotion/`**. `song-video` carries its own components and
does **not** import the brief's `theme.ts`; what it genuinely shares is reached through
`song_video.paths.shared_remotion()` — *"the brief's `remotion/` — vendored fonts and the seeded PRNG the reel draws
with"*.

So this slide does **not** import `theme.ts`, `Furniture.tsx` or `Brand.tsx`. Precisely:

- **Copied conventions** — the palette values and the `Card` metrics (padding, the header/footer registers, the
  reserved top-right region) are **mirrored into books-brief's own module**, exactly as the reel has its own
  `themes.ts` instead of importing the brief's.
- **Shared by import** — the **vendored fonts** and the **seeded PRNG** through `shared_remotion()`, and the
  **licensed mark file** through `mark_dir()` (the brief's `resource/brief/`), so one mark serves every product.
  ⚠️ **The Bengali chart's font requirements are ticket 27** — and the short version is that it must load **both** the
  Bengali *and* Latin subsets, because the Bengali subset carries no Latin.
- ⚠️ `enter()` is a **rule** worth re-implementing with the span ceiling above — not a component to import.
