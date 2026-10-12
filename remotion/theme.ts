/** The palette and the shared metric rules.
 *
 * Everything a viewer reads is decided here, so a card cannot invent its own conventions.
 */

/**
 * ⚠️ **The palette was brightened deliberately.** The old `GREEN #37d67a` / `RED #ff5c5c` were tuned to sit
 * quietly over a dark, desaturated 3D world. With the world replaced by a vibrant animated backdrop (see
 * `Backdrop.tsx`) the figures have to hold their own against a much louder background, so the up/down pair
 * moved to a **vivid emerald and a vivid rose** — brighter, more saturated, and still clearly distinct in
 * lightness as well as hue, so a colour-blind viewer can tell them apart.
 */
export const INK = '#f5f7ff';
export const MUTED = '#9aa6c2';
export const GREEN = '#2be39a';
export const RED = '#ff5470';
export const BG = '#0b0e13';
export const RULE = '#232b3d';

/**
 * ⚠️ **Two scrim strengths, because the cards do not all have an atmosphere region.**
 *
 * The backdrop layer may only occupy the frame regions the card's layout marks as **atmosphere**. A sparse card
 * — the calendar holds eight rows in its top third — leaves the lower frame empty, so the backdrop belongs there
 * and the scrim can be thin. A **dense table has no such region**: its rows run to the bottom edge, so on those
 * cards the backdrop must be a hint and nothing more.
 *
 * That is not a taste call. An early render proved it: a thin scrim under the sector table put the backdrop
 * behind the heat cells, where it competed with the cells' own colour and made the right half of the table look
 * grubby. The heat map's tint *is* its meaning, so nothing may sit behind it.
 *
 * So `SCRIM_OPEN` is for the cards that leave the lower frame empty — most_active, breadth, dma, flows,
 * dependencies, calendar — plus the three framing blocks, where the backdrop is the content. Everything else
 * takes the dense `SCRIM`; the mapping is asserted in `tests/test_backdrop.py` rather than left to judgement.
 */
export const SCRIM =
  'linear-gradient(180deg, rgba(11,14,19,0.97) 0%, rgba(11,14,19,0.94) 44%, ' +
  'rgba(11,14,19,0.82) 68%, rgba(11,14,19,0.72) 74%, rgba(11,14,19,0.91) 88%, rgba(11,14,19,0.97) 100%)';

export const SCRIM_OPEN =
  'linear-gradient(180deg, rgba(11,14,19,0.96) 0%, rgba(11,14,19,0.90) 44%, ' +
  'rgba(11,14,19,0.52) 68%, rgba(11,14,19,0.34) 74%, rgba(11,14,19,0.88) 88%, rgba(11,14,19,0.96) 100%)';

/**
 * ⚠️ **The still's own scrim, and it is much thinner than either card scrim — measured, not guessed.**
 *
 * The first still used `SCRIM_OPEN` and the backdrop vanished: that scrim is 0.90 opaque through the middle, and
 * the backdrop's palette is deliberately dark, so keeping 10 % of it is keeping nothing. The still came out as a
 * number on a black field.
 *
 * That is a defect against issue 14, not a taste call. The ticket asks for the figure **"over a lit grid"** and
 * says the day's field — *"the terrain behind the figure"* — is where a feed of daily thumbnails stops looking
 * like the same image every day. A crushed backdrop costs the thumbnail its daily variety, which is the whole
 * payoff of one data-driven animated field over eleven authored scenes.
 *
 * So this one leans the other way: dense at the very top where the mark sits, thin across the middle where the
 * figure has its own saturated colour to carry the contrast, **thinnest at ~74 % where the field actually is**,
 * and dense again at the bottom for the strip the platform draws on.
 */
export const SCRIM_STILL =
  'linear-gradient(180deg, rgba(11,14,19,0.86) 0%, rgba(11,14,19,0.62) 38%, ' +
  'rgba(11,14,19,0.28) 56%, rgba(11,14,19,0.06) 74%, rgba(11,14,19,0.40) 88%, rgba(11,14,19,0.72) 100%)';

/** "Kohinoor Bangla" is the system Bengali face and must be named explicitly — a fallback face
 * silently changes the shaping, and the copy is the one thing the two editions differ in. */
export const FONT = '"Kohinoor Bangla", system-ui, -apple-system, sans-serif';

/** U+2212 for the sign, so a minus is not a hyphen sitting next to a digit. */
export const percent = (value: number | null, digits = 2): string =>
  value === null ? '—' : `${value >= 0 ? '+' : '\u2212'}${Math.abs(value).toFixed(digits)}%`;

export const number = (value: number | null, digits = 2): string =>
  value === null ? '—' : value.toLocaleString('en-IN', {maximumFractionDigits: digits});

export const crore = (value: number | null): string =>
  value === null ? '—' : `₹${Math.round(value).toLocaleString('en-IN')}`;

/** Colour by the sign of a value. Never used on the dependency strip — see NEUTRAL. */
export const tone = (value: number | null): string =>
  value === null ? MUTED : value >= 0 ? GREEN : RED;

/** ⚠️ The **`*INR` rows of the dependency strip** only. For a currency pair, up means the rupee is *weaker*, so
 * colouring by sign would invert the meaning. Ticket 05's rule is "coloured by meaning, not by sign", so those rows
 * stay neutral — the direction is carried by the number and its arrow, never by a colour that would say the
 * opposite. The strip's other rows (VIX, metals, crude) are coloured normally. */
export const NEUTRAL = INK;

export const quote = (value: number | null, digits = 2): string =>
  value === null ? '—' : value.toLocaleString('en-IN', {maximumFractionDigits: digits});

/**
 * Deterministic PRNG. `Math.random()` would make two renders of the same bundle differ, which breaks the
 * frame-determinism promise ADR 0003 rests on.
 *
 * ⚠️ **Moved here from the 3D layer's own theme** when the world was replaced by `Backdrop.tsx`. The backdrop
 * places its particles and blobs the same way the world did — from a **seed string**, never a shared stateful
 * generator — so scrubbing, a re-render or a second edition cannot place them somewhere else.
 */
export const seeded = (seed: string) => {
  let h = 2166136261;
  for (let i = 0; i < seed.length; i += 1) {
    h = Math.imul(h ^ seed.charCodeAt(i), 16777619);
  }
  return () => {
    h = Math.imul(h ^ (h >>> 15), 2246822507);
    h = Math.imul(h ^ (h >>> 13), 3266489909);
    h ^= h >>> 16;
    return (h >>> 0) / 4294967296;
  };
};

/** −1..1 from a percentage, saturating at `saturate` — used so the backdrop's character follows the day's
 * direction without anyone authoring a scene for it. */
export const lean = (percent: number | null | undefined, saturate = 5) =>
  Math.max(-1, Math.min(1, (percent ?? 0) / saturate));
