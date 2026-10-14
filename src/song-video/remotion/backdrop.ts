/**
 * The light in the field — **pure, so a test can see it** (the same split `motif.ts` explains).
 *
 * ⚠️ Ticket 11's third rule is that *the theme's grammar must have its own slow arc*. The wave traverses and the
 * motif never rests; without something here, the field behind them is the one thing in the film that is a
 * photograph.
 *
 * ⚠️ **Nobody is watching a lava lamp.** Each blob drifts a *fifth* of the frame across the whole piece around its
 * own anchor — at any one moment the change is nearly invisible, and after three minutes the light is somewhere
 * else. That is what "slow arc" means, and it is the opposite of motion for its own sake, which is the failure
 * mode this project names in its own map.
 *
 * ⚠️ **The amplitude widens the light; it does not brighten it.** Scale is this reel's metaphor for loudness — the
 * disc breathes, the pulse widens — and a brightness flicker at 30 fps reads as a fault in the encode rather than
 * as the music.
 *
 * ⚠️ **Bounded, never wrapped.** The first version folded the drift through `wrapped()`, which is right for the
 * notes (they cross the whole frame and *should* return at the other edge) and wrong for a pool of light: at the
 * fold it teleports from one edge to the other, once per blob per song, and a pop is precisely what a slow arc may
 * not have. Here the anchor is placed inside a margin and the drift cannot leave it, so nothing ever jumps. A test
 * asserts the distance travelled rather than the path taken, which is how this was caught rather than shipped.
 */
import {accentAt} from './accent.ts';

/** Irrational steps, as in `motif.ts`: nothing lines up, and no random number is involved. */
const GOLDEN = 0.6180339887498949;
const SILVER = 1.4142135623730951;
const BRONZE = 1.7320508075688772;

/** Folded into `0..1` — a blob that wanders off the frame would simply stop lighting anything. */
const wrapped = (value: number): number => ((value % 1) + 1) % 1;

/** One pool of light: where its centre sits, how wide it is, and how much of the field it owns. All `0..1`. */
export type Blob = {
  readonly x: number;
  readonly y: number;
  readonly radius: number;
  readonly strength: number;
};

/**
 * The pools of light at a point in the piece.
 *
 * ⚠️ **The seed moves the light as well as choosing its colour.** Two songs in the same theme and the same accent
 * should not drift identically — otherwise the colour varies and the *picture* does not, which is half of what
 * "different videos look different" asks for.
 *
 * ⚠️ `0.2` and `0.16` are the whole of the drift, and they are deliberately small. Everything else is anchored,
 * so the frame is composed rather than stirred.
 */
export const blobs = (
  travelled: number,
  amplitude: number,
  {count, seed}: {readonly count: number; readonly seed: string},
): readonly Blob[] => {
  const start = accentAt(seed === '' ? 'seed' : seed);

  return Array.from({length: count}, (_, index) => {
    const step = index + Math.floor(start * 7);
    const anchor = wrapped(start + step * GOLDEN);

    return {
      // ⚠️ The drift is centred on the anchor and cannot leave its margin: `travelled` moves the light *around* where
      // it was placed, and the frame's own edges are never crossed.
      x: 0.15 + 0.7 * wrapped(anchor * 0.6 + 0.2) + 0.2 * (travelled - 0.5),
      y: 0.12 + 0.62 * wrapped(anchor * SILVER) + 0.16 * (0.5 - travelled),
      radius: 0.4 + 0.1 * wrapped(step * BRONZE) + 0.08 * amplitude,
      strength: (0.35 + 0.4 * wrapped(step * GOLDEN * SILVER)) * (0.6 + 0.4 * amplitude),
    };
  });
};
