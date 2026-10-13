/**
 * The wave forms — **geometry only, in unit space.** (Map ticket 06)
 *
 * A form says *where the marks are*; the theme says what they look like. That split is what makes the catalogue
 * a real cross-product — four forms × four themes, every combination authored — while each form stays **one**
 * implementation instead of four. Coordinates are `0..1` on both axes, so no form knows what a pixel is.
 *
 * ⚠️ **A form may not read a clock, call `Math.random()`, or fetch.** Anything of the sort would end the
 * re-render matching the render, which is the one promise this pipeline never trades away.
 */
import {peakOf} from './envelope.ts';

/** One column of a landscape: where its centre sits across the frame, and how tall it is. Both `0..1`. */
export type Band = {readonly at: number; readonly height: number};

/**
 * The whole song as a fixed landscape of columns — **identical for every frame**, which is the point.
 *
 * ⚠️ Frame-independent deliberately. It is reduced **once** and memoised by the composition, rather than
 * re-reducing a nine-thousand-frame envelope on each of nine thousand frames; and it shows the viewer the
 * song's shape *ahead* of the playhead, which is *"the song's own shape is the narrative"* made visible
 * instead of merely claimed.
 */
export const bars = (
  envelope: readonly number[],
  {columns}: {readonly columns: number},
): readonly Band[] => {
  const bands: Band[] = [];

  for (let column = 0; column < columns; column += 1) {
    const from = Math.round((column * envelope.length) / columns);
    // ⚠️ At least one frame wide: more columns than frames would otherwise leave empty bands at zero height,
    // which reads as a broken landscape rather than a coarse one.
    const to = Math.max(Math.round(((column + 1) * envelope.length) / columns), from + 1);
    bands.push({at: (column + 0.5) / columns, height: peakOf(envelope, from, to)});
  }

  return bands;
};

/**
 * The envelope, **settled** — a centred moving average, for the things the eye follows rather than the clock.
 *
 * ⚠️ **The clock stays the clock.** `envelope.ts` is emphatic that the amplitude *is* the timeline and that any
 * smoothing the design wants belongs to a theme. This is that smoothing, and it is deliberately a *separate array*:
 * the landscape keeps the peaks (`bars` reads the raw envelope), while the pulse and the light — the two things that
 * move on every single frame — are read from here.
 *
 * ⚠️ **Why it is worth a function.** A true peak shifts by tens of pixels from one frame to the next, so a halo or a
 * pool of light driven by the raw amplitude strobes at frame rate. That is the difference between *watching a song*
 * and *watching numbers move*: averaging over a window a theme chooses turns transients into swells, which is what an
 * eye reads as music.
 *
 * ⚠️ **Centred, so it cannot look ahead of the song.** Frame `f` is the mean of the frames around it, never of the
 * frames after it — a one-sided filter would make the picture anticipate the music, and an audience cannot name that
 * and can feel it. ⚠️ And the window **shrinks at the ends** rather than wrapping (the wrap in `backdrop.ts` once
 * teleported a pool of light across the frame, which is why the habit here is bounded or nothing).
 */
export const smoothed = (envelope: readonly number[], {window}: {readonly window: number}): readonly number[] => {
  if (window <= 1) {
    return [...envelope];
  }

  const half = Math.floor(window / 2);
  return envelope.map((_, frame) => {
    const from = Math.max(0, frame - half);
    const to = Math.min(envelope.length, frame + half + 1);

    let total = 0;
    for (let index = from; index < to; index += 1) {
      total += envelope[index];
    }
    return total / (to - from);
  });
};

/**
 * How far the piece has travelled: `0` on the first frame, `1` on the last — **the traversal.**
 *
 * ⚠️ This is ticket 11's *"the wave must traverse"* rule written as arithmetic, so that the rule is
 * checkable rather than trusted. A wave whose geometry does not move with the playhead is a screensaver,
 * however good its colour is.
 *
 * ⚠️ A one-frame piece returns `0` rather than `0 / 0`. The **still is one frame**, and a NaN playhead would
 * erase the wave from the thumbnail instead of leaving it parked at the near edge.
 */
export const playhead = (frame: number, frames: number): number => {
  if (frames <= 1) {
    return 0;
  }
  return frame / (frames - 1);
};

/** One ring of a bloom: how far out it sits, and how loud the moment it carries was. Both `0..1`. */
export type Ring = {readonly radius: number; readonly strength: number};

/**
 * The bloom — **the one form that draws a history rather than the whole song.**
 *
 * Every other form lays the song out across the frame and lets the playhead traverse it; a bloom is emitted
 * outward from the centre, the newest ring innermost and the oldest already travelled. That makes it the only
 * form needing the frame *as well as* the envelope, and the only one whose traversal is carried by its own
 * geometry instead of by a shared playhead.
 *
 * ⚠️ **Before the song: silence, never a wrap-around.** A ring reaching back past frame 0 must not borrow the
 * song's *ending* — that would drop the loudest moment of the piece into its opening seconds, and it would look
 * like a flourish rather than a defect while it did it.
 */
export const ripple = (
  envelope: ArrayLike<number>,
  frame: number,
  {ringCount, stride}: {readonly ringCount: number; readonly stride: number},
): readonly Ring[] => {
  const rings: Ring[] = [];

  for (let age = 0; age < ringCount; age += 1) {
    const at = frame - age * stride;
    rings.push({
      radius: (age + 1) / ringCount,
      strength: at < 0 ? 0 : (envelope[at] ?? 0),
    });
  }

  return rings;
};
