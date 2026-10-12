/** The palette and the shared metric rules.
 *
 * Everything a viewer reads is decided here, so a card cannot invent its own conventions.
 */

export const INK = '#f4f6fa';
export const MUTED = '#8b95a7';
export const GREEN = '#37d67a';
export const RED = '#ff5c5c';
export const BG = '#0b0e13';
export const RULE = '#1e2531';

/**
 * ⚠️ **Two scrim strengths, because the cards do not all have an atmosphere region.**
 *
 * Issue 12: "The 3D layer may only occupy the frame regions the card's layout marks as **atmosphere**."
 * A sparse card — the calendar holds eight rows in its top third — leaves the lower frame empty, so the
 * world belongs there and the scrim can be thin. A **dense table has no such region**: its rows run to the
 * bottom edge, so on those cards the world must be a hint and nothing more.
 *
 * That is not a taste call. The first render proved it: a thin scrim under the sector table put the world's
 * geometry behind the heat cells, where it competed with the cells' own colour and made the right half of
 * the table look grubby. The heat map's tint *is* its meaning, so nothing may sit behind it.
 *
 * So `SCRIM_OPEN` is for the cards that leave the lower frame empty — most_active, breadth, dma, flows,
 * dependencies, calendar — plus the three framing blocks, where the world is the content. Everything else
 * takes the dense `SCRIM`; the mapping is asserted in `tests/test_world.py` rather than left to judgement.
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
 * The first still used `SCRIM_OPEN` and the world vanished: that scrim is 0.90 opaque through the middle, and the
 * world's palette is deliberately dark (`TILE #41526e` on `BG #0b0e13`), so keeping 10 % of it is keeping nothing.
 * The still came out as a number on a black field.
 *
 * That is a defect against issue 14, not a taste call. The ticket asks for the figure **"over a lit 3D grid"** and
 * says the day's terrain — *"the terrain behind the figure"* — is where a feed of daily thumbnails stops looking
 * like the same image every day. A crushed world costs the thumbnail its daily variety, which is the whole payoff
 * of choosing one data-driven world over eleven authored scenes.
 *
 * So this one leans the other way: dense at the very top where the mark sits, thin across the middle where the
 * figure has its own saturated colour to carry the contrast, **thinnest at ~74 % where the terrain actually is**,
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

/** ⚠️ The dependency strip only. `*INR` **up** means the rupee is *weaker*, so colouring by sign
 * would invert the meaning. Ticket 05's rule is "coloured by meaning, not by sign", and the strip is
 * left neutral: the direction is carried by the number and its arrow, never by a colour that would
 * say the opposite. */
export const NEUTRAL = INK;

export const quote = (value: number | null, digits = 2): string =>
  value === null ? '—' : value.toLocaleString('en-IN', {maximumFractionDigits: digits});
