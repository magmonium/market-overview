/**
 * The 3D layer's own palette and metrics — issue 12's "colour semantics that survive 3D lighting".
 *
 * ⚠️ **This is a separate palette from `theme.ts`, on purpose.** The flat cards and the lit world have
 * different constraints, and sharing one set of hex values would force one of them to compromise.
 */

/**
 * ⚠️ **Pinned**, so the same value looks the same on every run and a re-render matches. An
 * auto-exposed scene drifts with whatever is brightest in it, which is the opposite of deterministic.
 */
export const EXPOSURE = 1.05;

/** ⚠️ Fixed focal length. Issue 12's first camera rule: depth changes come from moving the camera,
 * never from zooming — zoom plus motion is what disorients. Every station shares this. */
export const FOCAL_LENGTH = 34;

/**
 * ⚠️ **Red and green differ in *lightness*, not only hue.** 3D shading collapses hue differences, so a
 * red/green pair that reads fine flat on a 2D chart can become indistinguishable once lit. Dark red
 * against bright green survives the lighting — and helps colour-blind viewers for free.
 */
export const UP = '#3ce07f';
export const DOWN = '#b8383a';

/** Terrain and background are desaturated neutrals, so the only saturated things in frame are figures. */
export const TERRAIN = '#232c3a';
export const HORIZON = '#0b0e13';
export const RIM = '#4a5a73';

/**
 * ⚠️ **Tiles are backdrop, not figures, so they are neutral.**
 *
 * `Tiles` first used the up/down green and the result was a saturated wedge across the lower frame that
 * read as a graphical artifact and, on the sector table, competed with the heat cells' own colour. Issue
 * 12 is explicit that terrain and background stay desaturated neutrals precisely so that "the only
 * saturated things in frame are figures" — and a scoreboard backdrop is not a figure.
 */
export const TILE = '#41526e';

/**
 * ⚠️ **The thumbnail's column colour, and it is deliberately brighter than anything in the video. (0085_12)**
 *
 * Not a new hue — the same desaturated slate family as `TILE` and `RIM`, which issue 12 requires so that "the only
 * saturated things in frame are figures". It is a **lighter value** of that family, because the constraint is
 * different: in the video a column sits over a scrim the *cards* control, while on the still the columns are the
 * subject's backdrop and had nothing between them and the frame.
 *
 * The first still proved it. `TILE` behind the number produced a shape nobody could read as a grid — dark slate,
 * then a scrim on top of it, on a background that is `#0b0e13` too. The figure was legible and the *world* was
 * absent, which fails issue 14's "over a lit 3D grid" and costs the still its daily variety.
 */
export const BACKDROP = '#6b7d99';

/**
 * The reserved top-right mark area, **260 x 160**, matching `Card`'s own box: `padding` puts the card's
 * frame at 96 px from the side and 64 px from the top. Issue 21's region, and issue 12's rule that 3D
 * respects reserved regions the same way.
 */
export const LOGO_SAFE = {left: 1920 - 96 - 260, top: 64, width: 260, height: 160} as const;

/**
 * ⚠️ **The atmosphere bands — where the world is allowed to be seen.**
 *
 * Issue 12: "The 3D layer may only occupy the frame regions the card's layout marks as **atmosphere**."
 * The cards are text-first and fill the upper and middle frame, so the world lives **low**, on a horizon
 * that sits below the dense content, plus a far background. Anything the mind reads as a shape stays out
 * of the band the tables occupy.
 *
 * This is also why 0085_08's finding and this task agree: the re-cut concentrated 70 % of the brief on the
 * cards with the emptiest lower halves, which is precisely where the world now is.
 */
export const ATMOSPHERE = {top: 720, bottom: 945} as const;

/** Deterministic PRNG. `Math.random()` would make two renders of the same bundle differ, which breaks
 * the frame-determinism promise ADR 0003 rests on. */
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

/** −1..1 from a percentage, saturating at `saturate` — for leaning geometry off a fact's sign. Used so
 * the world's character follows the day's direction without anyone authoring a scene for it. */
export const lean = (percent: number | null | undefined, saturate = 5) =>
  Math.max(-1, Math.min(1, (percent ?? 0) / saturate));
