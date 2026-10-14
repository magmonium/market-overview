/**
 * This product's palette and metrics — **mirrored from the brief, deliberately not imported** (ticket 07).
 *
 * ⚠️ **This looks like the wrong call and it is the right one.** The brief's `remotion/theme.ts` is *right there*, and
 * importing it would be one line. But a nested product is a **separate product**: the brief's palette is tuned to the
 * brief's own animated backdrop, and the day someone re-tunes it for a new brief, a books chart would change colour
 * without anyone touching this project. The reel made the same call — it carries its own `themes.ts` and imports
 * nothing from the brief's theme.
 *
 * ⚠️ **What is *not* mirrored is the typeface.** The vendored `.woff2` bytes and the wait for them are imported from
 * the brief's own `fonts.ts` (ticket 27), because those are *assets with a licence* — a second copy of nine font files
 * would be a second thing to keep in step, and the drift would show as a **passing** copy budget, since the measuring
 * browser and the renderer would be measuring different faces.
 *
 * ⚠️ **The mirroring is of *values*, not of components.** `Card`, `enter()` and `Brand.tsx` are not imported either —
 * `enter()` is a *rule* worth re-implementing with ticket 07's span ceiling, and the shell is a different shape (four
 * registers, not a header/main/footer with a block title).
 */

// ── The typeface ─────────────────────────────────────────────────────────────────────────────────────────────
/**
 * ⚠️ **The one thing this product imports from the brief, and it is imported on purpose** (ticket 07).
 *
 * The nine vendored `.woff2` files, the family, and the **wait for them** are the brief's, because they are *assets with
 * a licence* and a second copy would be a second thing to keep in step — and the drift would show as a **passing** copy
 * budget, since the measuring browser and the renderer would be measuring different faces.
 *
 * ⚠️ **`useFonts` loads all nine faces and waits against a sample spanning Bengali *and* Latin**, which is exactly
 * ticket 27's trap: the Bengali subset carries **no Latin**, so a Bengali slide printing `WEEK 41`, `₹399` and the
 * ticker would ship half its glyphs in a fallback face. Reusing the brief's hook is what makes that impossible rather
 * than merely unlikely — and ⚠️ it **refuses** the render rather than falling back.
 *
 * ⚠️ Only `FONT` is re-exported, not the `Typeface` component: the family is a *style*, which every surface needs, while
 * the wait is a **tree element** and belongs where the composition mounts it.
 */
export {FONT} from '../../../remotion/fonts.ts';

// ── The palette ──────────────────────────────────────────────────────────────────────────────────────────────
// ⚠️ Transcribed from `remotion/theme.ts`. The up/down pair is a vivid emerald and a vivid rose on purpose: the
// figures have to hold their own against a loud animated background, and the two are distinct in **lightness** as
// well as hue, so a colour-blind viewer can still tell them apart.
export const INK = '#f5f7ff';
export const MUTED = '#9aa6c2';
export const GREEN = '#2be39a';
export const RED = '#ff5470';
export const BG = '#0b0e13';
export const RULE = '#232b3d';

/**
 * ⚠️ **The dense scrim, and this product has no `SCRIM_OPEN`.** The brief keeps two because a sparse card leaves the
 * lower frame to its backdrop; a chart slide is dense by definition — a cover, five data lines, a ticker band and a
 * footer run to the bottom edge — so there is no region where a backdrop could live. One scrim, and the ticker band
 * is what sits in the thin part of it.
 */
export const SCRIM =
  'linear-gradient(180deg, rgba(11,14,19,0.97) 0%, rgba(11,14,19,0.94) 44%, ' +
  'rgba(11,14,19,0.82) 68%, rgba(11,14,19,0.72) 74%, rgba(11,14,19,0.91) 88%, rgba(11,14,19,0.97) 100%)';

// ── The shell's metrics ──────────────────────────────────────────────────────────────────────────────────────
/**
 * ⚠️ **The brief's own `Card` numbers, kept so the two products' frames agree** — `padding: 64px 96px 88px`, a 46 px
 * title, a 24 px footer. Ticket 07 anchors the slide's type scale to them rather than inventing a second system.
 */
export const CARD = {padding: '64px 96px 88px', title: 46, footer: 24, rule: 1} as const;

/**
 * ⚠️ **The mark's reserved region, from issue 21's verdict table — `260 × 160` at `x ≥ 1660, y ≤ 160`.** It is
 * anchored to the **frame corner**, not to the padded content box, and that distinction is easy to get wrong: a
 * measurement built from the paddings once reported a collision that did not exist.
 */
export const RESERVED = {width: 260, height: 160, left: 1660, top: 0} as const;
export const BUG = {size: 96, inset: 48} as const;
/** ⚠️ The still's mark, at issue 21's *still* size rather than the video's — a larger share of a smaller frame. */
export const STILL = {size: 128, inset: 40} as const;

// ── The slide's own scale (ticket 07) ────────────────────────────────────────────────────────────────────────
/**
 * ⚠️ **One dominant element, and it is the rank numeral.** The brief's cards carry a 46 px title and nothing larger;
 * a slide whose whole subject is *one book's position in a chart* has to say that position loudest, so 220 is the
 * anchor everything else defers to.
 *
 * ⚠️ **The title clamps rather than shrinking without limit.** 72 → 60 → 52, then an ellipsis: a title that will not
 * fit is a title to shorten, and ⚠️ the **full** title survives in the description (ticket 15), so nothing is lost —
 * which is what makes clamping honest rather than lossy.
 */
export const SLIDE = {
  header: 34,
  rank: 220,
  /** The rank's own weight, heavier than anything else on the frame. */
  rankWeight: 700,
  title: 72,
  titleSteps: [72, 60, 52] as const,
  titleLines: 2,
  author: 40,
  detail: 34,
  label: 26,
  cover: 0.34,
} as const;
