/**
 * Which of a theme's accents a piece is drawn in — **pure, and testable, which is why it is not in `themes.ts`.**
 *
 * ⚠️ **A colour per song, without a random number anywhere.** The operator's ask was that different videos look
 * different; the house's own rule is that two renders of the same props are byte-identical (ADR 0003), so a
 * `Math.random()` here would end the only promise this pipeline never trades. The answer is to make the choice a
 * **pure function of something already recorded** — the master's `sha256` — which gives different songs different
 * colours and gives one song the same colour on every rebuild, for ever.
 *
 * ⚠️ **The digest is not recorded for this.** It is recorded because a swapped master must be refused (issue 09);
 * the accent simply *is* a function of it, exactly as the caption's numerals are a function of the recorded
 * duration. Nothing new is written down, and a record written before accents existed replays into its own colour.
 */

/** One of a theme's accents. ⚠️ **Authored, never generated** — a generated palette is the map's own fog. */
export type Accent = {
  /** What the colour is called. Unused by the drawing, and the thing a human says out loud — `amber`, not `#e8a13c`. */
  readonly name: string;
  /** The colour the backdrop's light is made of. */
  readonly tint: string;
};

/** FNV-1a, 32-bit. ⚠️ Chosen because it is **stable across machines and versions** — a `Map`'s ordering or a
 * `Math.random()` would make the same song pick differently in a future run, which is the defect, not the feature. */
const digest = (seed: string): number => {
  let hash = 2166136261;
  for (let index = 0; index < seed.length; index += 1) {
    hash = Math.imul(hash ^ seed.charCodeAt(index), 16777619);
  }
  return hash >>> 0;
};

/** How a seed reads as a value in `0..1` — the same string always gives the same number. */
export const accentAt = (seed: string): number => digest(seed) / 4294967296;

/**
 * The accent this piece is drawn in.
 *
 * ⚠️ **An empty seed is a supported state**, and it lands on the theme's **first** accent rather than throwing: the
 * Studio's `EMPTY` props have no seed, and a composition that refused to list itself would be a worse failure than
 * a default colour. A *render* always has one, because Python passes the recorded digest.
 */
export const accentFor = (accents: readonly Accent[], seed: string): Accent => {
  if (seed === '') {
    return accents[0];
  }
  return accents[Math.floor(accentAt(seed) * accents.length) % accents.length];
};
