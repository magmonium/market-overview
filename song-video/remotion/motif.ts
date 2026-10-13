/**
 * The motif's **geometry** — pure, and deliberately in a `.ts` beside its `.tsx`.
 *
 * ⚠️ Not a style choice: **JSX is not erasable TypeScript**, so `node --test` cannot load a `.tsx` file at all.
 * Anything a test must be able to see therefore lives here, and only the drawing lives next door.
 *
 * ⚠️ And the angle is a function of the **traversal**, never of a wall clock: two renders of the same song place
 * the disc identically, which is ADR 0006's promise in its smallest possible form.
 */

/**
 * How far the disc has turned, in degrees, at a point in the piece.
 *
 * ⚠️ **`turns` is never zero and never fractional-at-the-end.** Ticket 11's rule is that the motif must never
 * rest — a disc that parks is a screensaver's prop — and a whole number of turns means the last frame is a clean
 * angle rather than a disc left mid-wobble.
 */
export const discAngle = (travelled: number, {turns}: {readonly turns: number}): number =>
  travelled * turns * 360;

/**
 * Irrational steps, one per property, so nothing lines up: the start positions, lanes, sizes and paces of the
 * notes are all driven by different irrationals and come out scattered rather than evenly spaced.
 */
const GOLDEN = 0.6180339887498949;
const SILVER = 1.4142135623730951;
const BRONZE = 1.7320508075688772;

/** Folded into `0..1` — the wrap that keeps a note inside the frame for the whole piece. */
const wrapped = (value: number): number => ((value % 1) + 1) % 1;

/**
 * How far a note may drift from its column, in frame widths.
 *
 * ⚠️ **Bounded on purpose, and the bound is what keeps the frame readable.** At ±0.06 against a column pitch of
 * `1/count`, two neighbours can close to `1/count - 0.12` — still apart, at every instant, for every count this
 * project draws. A note that swept the whole frame would be back to the clumping this replaced.
 */
export const NOTE_SWAY = 0.06;

/** Where one note sits, and how big it is. All three values are relative, so no drawing knows a pixel. */
export type NotePlacement = {
  readonly x: number;
  readonly y: number;
  readonly size: number;
};

/**
 * Where a note is at a point in the piece — **and it is always moving.**
 *
 * ⚠️ **The columns are even, and that is a fix the stills asked for.** The first version drew each note's position
 * from the same low-discrepancy sequence as its lane and its speed, which read as scattered in motion and clumped
 * badly in a still: three notes against the left edge, three mid-frame, the right half empty. One note per band
 * fixes it at *every* instant, and the motion — a sway plus a rise, both around the column — is what makes it
 * flow rather than sit.
 *
 * ⚠️ **The scatter is still a low-discrepancy sequence, not a PRNG.** The map says these lanes are drawn from the
 * brief's `seeded()`, and that is what this would have used — except `seeded` lives in the brief's `theme.ts`,
 * which re-exports `FONT` from `fonts.ts`, so importing it drags **nine `.woff2` assets and Remotion itself** into
 * every `node --test` run, and node can load neither. Irrational steps are deterministic by construction, need no
 * dependency, and scatter as evenly as a random number would without being one.
 *
 * ⚠️ **No note ever rests, and no two move together.** Two sines of different frequencies drive the sway, so it
 * cannot stall at a turning point — which is the one way a *deterministic* drift stops looking like drift. And
 * every pace is different, because notes that moved in lockstep would read as one object drawn several times.
 */
export const noteAt = (
  index: number,
  travelled: number,
  {seed, count}: {readonly seed: string; readonly count: number},
): NotePlacement => {
  // The seed only shifts *where in the sequence* a theme's notes begin, so two themes with the same count still
  // scatter their notes differently — with no random number anywhere in sight.
  const step = index + (seed.length % 7);
  const square = step * step;
  const phase = wrapped(square * GOLDEN);

  const sway = (frequency: number, offset: number): number =>
    Math.sin(2 * Math.PI * (travelled * frequency + offset));

  return {
    x: wrapped(
      // ⚠️ The column first: `index` places the note, and nothing else does.
      (index + 0.5) / count + NOTE_SWAY * (0.6 * sway(1 + phase, phase) + 0.4 * sway(2 - phase, phase * SILVER)),
    ),
    // The lane, and its own slow rise — wrapping at the top, which vertical motion can do without ever bunching.
    y: 0.1 + 0.8 * wrapped(phase + travelled * (0.35 + 0.5 * wrapped(step * BRONZE))),
    size: 0.55 + 0.75 * wrapped(square * SILVER),
  };
};

