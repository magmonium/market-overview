import type {ReactNode} from 'react';
import type {FactsBundle} from '../bundle';
import {Columns, Particles, Rings, Tiles} from './primitives';
import {BACKDROP} from './theme';

/**
 * The stations — issue 12's "one continuous world, eleven camera stations", minus the one 0085_08 cut
 * with the heat map. Ten stations for twelve blocks, because the pre-roll shares the cold open's shot.
 *
 * ⚠️ **The camera is a single closed rail, not twelve independent set-ups.** Each station's `from` *is*
 * the previous station's `to`, so the camera never jumps and the continuity is structural rather than
 * something a transition has to hide. The rail is one orbit that ends at the azimuth it began at, so the
 * close returns to the establishing wide — **the brief ends where it started**.
 *
 * ⚠️ **Block 0, the disclosure pre-roll, has no station of its own** (issue 12). It holds still in the
 * cold open's establishing shot, which is why its `from` and `to` are identical and its settle is zero.
 */

export type Vec3 = [number, number, number];
export type Primitive = 'terrain' | 'column' | 'tile' | 'ring' | 'particle' | 'rig';

type Camera = {position: Vec3; target: Vec3};

export type Station = {
  /** Which of the six shapes this scene is built from. Nothing outside the set may appear. */
  primitives: Primitive[];
  from: Camera;
  to: Camera;
  /** ⚠️ Seconds the single establishing move takes. Issue 12: it must complete **inside** the reading
   * window rather than consume it, and ~1.5 s is the ceiling. */
  settle: number;
  /** ⚠️ Takes a **seed**, not a random generator, so the scene is a pure function of its inputs and the
   * frame stays deterministic (ADR 0003). */
  scene: (bundle: FactsBundle, seed: string) => ReactNode;
};

/** The rail, in polar terms about the world's centre. Modest radius changes keep each move short enough
 * that a 1.4 s settle reads as a drift rather than a whip-pan.
 *
 * ⚠️ **Every station aims at the same low point in the world.** The camera orbits and rises; the world
 * stays the subject. That is what keeps the world inside the frame's lower band *for every station at
 * once* — and it is the honest version of the design, since the one thing the ten stations share is the
 * world they are looking at.
 *
 * The value is measured, not chosen. Aiming at the world's own centre put geometry across the middle of the
 * sector table. Aiming a fixed offset *above the camera* (`y + 1.7`) worked at eye level but pushed the
 * world out of frame entirely from the two high stations — the crane-up and the calendar — whose cameras sit
 * nearly six units above the floor tiles; the world simply fell below the frame and the sparse cards went
 * empty again. A fixed aim point has no such height dependence. */
const AIM_Y = 1.4;

const rail = (azimuthDeg: number, radius: number, y: number): Camera => {
  const a = (azimuthDeg * Math.PI) / 180;
  return {position: [Math.sin(a) * radius, y, Math.cos(a) * radius], target: [0, AIM_Y, 0]};
};

/** Magnitudes scaled into world height. Percentages run 0.1–18, which as raw units would be a city. */
const heightOf = (percent: number | null | undefined, gain = 0.26) =>
  0.5 + Math.min(Math.abs(percent ?? 0) * gain, 5.5);

/** Rows that carry a six-window record — indices, sectors, the broader set. */
const windowRise = (rows: {window?: Record<string, number | null>}[] | undefined) =>
  (rows ?? []).map((row) => heightOf(row.window?.change));

/** ⚠️ `Quote` rows carry their day change at the **top level**, not in a `window` — leaders and the most
 * active stock are quotes, not scoreboards, so the two cannot share one accessor. */
const quoteRise = (rows: {change?: number | null}[] | undefined) =>
  (rows ?? []).map((row) => heightOf(row.change));

/** The establishing wide, and the azimuth the orbit closes on. */
const WIDE = rail(0, 26, 3.2);
const OPEN_WIDE = rail(0, 30, 3.6);

const STATIONS: Record<string, Station> = {};

const define = (key: string, station: Station) => {
  STATIONS[key] = station;
};

/** Block 1 — establishing wide, slow push in. */
define('cold_open', {
  primitives: ['terrain', 'tile', 'rig'],
  from: OPEN_WIDE,
  to: WIDE,
  settle: 1.4,
  scene: (bundle) => (
    <Tiles count={(bundle.indexes?.length ?? 5) * 2} columns={6} spacing={2.6} z={-6} size={1.6} />
  ),
});

/** Block 2 — truck along the ridge, one tile per index. */
define('indexes', {
  primitives: ['terrain', 'tile', 'rig'],
  from: WIDE,
  to: rail(25, 17, 2.6),
  settle: 1.4,
  scene: (bundle) => (
    <Tiles count={bundle.indexes?.length ?? 5} columns={bundle.indexes?.length ?? 5} spacing={3.4} size={2.6} />
  ),
});

/** Block 9 — lateral tracking past the day's movers. */
define('leaders', {
  primitives: ['terrain', 'column', 'rig'],
  from: rail(25, 17, 2.6),
  to: rail(48, 15, 2.4),
  settle: 1.3,
  scene: (bundle) => (
    <Columns
      values={[...quoteRise(bundle.leaders?.gainers), ...quoteRise(bundle.leaders?.losers)]}
      spacing={1.25}
      z={-3}
    />
  ),
});

/** Block 13 — the one stock where the most happened: a single column, settling low and slow. */
define('most_active', {
  primitives: ['terrain', 'column', 'rig'],
  from: rail(48, 15, 2.4),
  to: rail(60, 11, 2.0),
  settle: 1.1,
  scene: (bundle) => (
    <Columns values={[heightOf(bundle.most_active?.relative_volume, 0.012)]} spacing={2} width={1.6} z={-2} />
  ),
});

/** Block 3 — settle over the sector cluster. */
define('sectors', {
  primitives: ['terrain', 'column', 'rig'],
  from: rail(60, 11, 2.0),
  to: rail(80, 14, 3.0),
  settle: 1.4,
  scene: (bundle) => <Columns values={windowRise(bundle.sectors)} spacing={1.15} z={-4} />,
});

/** Block 7 — pull back to a wide, symmetric shot: the market's two halves, side by side. */
define('breadth', {
  primitives: ['terrain', 'column', 'rig'],
  from: rail(80, 14, 3.0),
  to: rail(100, 24, 3.6),
  settle: 1.2,
  scene: (bundle) => (
    <Columns
      values={[heightOf(bundle.breadth?.rising, 0.01), heightOf(bundle.breadth?.falling, 0.01)]}
      spacing={5}
      width={1.8}
    />
  ),
});

/** Block 8 — slow orbit of the ring structure. */
define('dma', {
  primitives: ['terrain', 'ring', 'rig'],
  from: rail(100, 24, 3.6),
  to: rail(130, 13, 2.6),
  settle: 1.4,
  scene: () => <Rings />,
});

/** Block 10 — FII against DII: two banks, because the DOM carries the diverging bar. */
define('flows', {
  primitives: ['terrain', 'column', 'rig'],
  from: rail(130, 13, 2.6),
  to: rail(155, 11, 2.2),
  settle: 1.1,
  scene: (bundle) => (
    <Columns
      values={[heightOf(bundle.flows?.fii?.net, 0.004), heightOf(bundle.flows?.dii?.net, 0.004)]}
      spacing={4.5}
      width={1.6}
    />
  ),
});

/** Block 5 — drift through the particle field, with a marker per dependency. */
define('dependencies', {
  primitives: ['terrain', 'particle', 'tile', 'rig'],
  from: rail(155, 11, 2.2),
  to: rail(185, 12, 2.0),
  settle: 1.4,
  scene: (bundle, seed) => (
    <>
      <Particles count={480} seed={`${seed}:dependencies`} spread={[30, 7, 20]} />
      <Tiles count={bundle.dependencies?.length ?? 6} columns={3} spacing={3.2} z={-9} size={1.7} />
    </>
  ),
});

/** Block 6 — crane up over the broader indices. */
define('broader', {
  primitives: ['terrain', 'column', 'rig'],
  from: rail(185, 12, 2.0),
  to: rail(210, 16, 5.4),
  settle: 1.4,
  scene: (bundle) => <Columns values={windowRise(bundle.broader)} spacing={3.2} z={-5} width={1.4} />,
});

/** Block 11 — slow drift. Deliberately the cheapest scene: issue 12's render-budget relief valve, and
 * text-led, so it must not compete with its own sub-cards. */
define('calendar', {
  primitives: ['terrain', 'tile', 'particle', 'rig'],
  from: rail(210, 16, 5.4),
  to: rail(235, 15, 4.4),
  settle: 1.4,
  scene: (_bundle, seed) => (
    <>
      <Tiles count={18} columns={6} spacing={2.4} z={-8} size={1.3} />
      <Particles count={220} seed={`${seed}:calendar`} spread={[24, 5, 18]} />
    </>
  ),
});

/** Block 12 — pull out to the establishing wide, closing the orbit where it opened. */
define('close', {
  primitives: ['terrain', 'tile', 'rig'],
  from: rail(235, 15, 4.4),
  to: WIDE,
  settle: 1.4,
  scene: (bundle) => (
    <Tiles count={(bundle.indexes?.length ?? 5) * 2} columns={6} spacing={2.6} z={-6} size={1.6} />
  ),
});

/**
 * ⚠️ **The pre-roll has no station of its own** (issue 12). Same camera as the cold open's opening frame,
 * no move, zero settle — so the piece opens on the world before it says anything, and the pre-roll's
 * render cost stays at nothing.
 */
define('disclosure', {
  primitives: ['terrain', 'tile', 'rig'],
  from: OPEN_WIDE,
  to: OPEN_WIDE,
  settle: 0,
  scene: STATIONS.cold_open.scene,
});

export const stationFor = (key: string): Station | undefined => STATIONS[key];

/**
 * The thumbnail's viewpoint. (0085_12)
 *
 * ⚠️ **Deliberately not in `STATIONS`, and that is a contract rather than an oversight.** `STATIONS` is the video's
 * rail: one entry per rendered block, each station's `from` equal to the previous station's `to`. `tests/test_world.py`
 * asserts both properties — that no station exists for a block that never renders, and that the count is exactly the
 * order plus the pre-roll. A thumbnail viewpoint is **not a cut in the video**, so putting it in that table would
 * make both assertions false and, worse, would put a camera nobody ever cuts to on a rail whose whole point is that
 * it is continuous.
 *
 * **Issue 14's "rest state", taken literally:** `from` *is* `to` and `settle` is 0, so the camera never moves and
 * **every frame is the settled one**. That is a stronger guarantee than rendering "at a frame after the entrance
 * finished" — there is no entrance, so there is no frame the still could be caught mid-way through.
 *
 * ⚠️ The **same azimuth as the establishing wide**, a little closer. Same azimuth because issue 14 wants the still to
 * read as the same product as the video; closer because a still has no reading window competing for the frame, so it
 * can afford more presence than the shot the cards sit on top of.
 */
export const THUMBNAIL: Station = {
  primitives: ['terrain', 'tile', 'rig'],
  /**
   * ⚠️ **The video's own establishing wide, then down and in — and the second part is what the renders settled.**
   * Three earlier attempts failed before this one:
   *
   * 1. `rail(0, 21, 2.8)` with tiles — the video's own distance. Seen from ~2.6 units above the ground, a flat quad
   *    foreshortens to a ~20 px sliver and the still came out as a number on a black field.
   * 2. `rail(0, 21, 2.8)` with **columns** — vertical mass, so it survived the angle, but `Columns` lays bars in a
   *    **single row**: from any camera that is a row of slabs, and at scale it read as a grey rectangle glitching out
   *    from beside the number.
   * 3. `rail(0, 13, 2.6)` — closing in made it worse, not better: a grey wedge in the corner, which reads as a
   *    rendering fault rather than as a world.
   *
   * The lesson is that **neither distance nor brightness was the variable**: a "lit 3D grid" needs a primitive that
   * *is* a grid (`Tiles`, a real `count` × `columns` field) **and** a camera high enough to see its surface. From
   * `WIDE` the view angle onto the ground is about 10°; from here it is about 34°, so the tiles read as a floor of
   * quads. It is still the same world, the same rig, the same six primitives and the same shared `AIM_Y` — a seat on
   * the video's world rather than a second one.
   */
  from: rail(0, 11, 5.2),
  to: rail(0, 11, 5.2),
  settle: 0,
  /**
   * ⚠️ **A grid of `Tiles`, seen from high enough to show its surface — and this is the one the renders settled.**
   *
   * `Columns` was the first choice and it was wrong. It lays bars in a **single row**, so from any camera it is a row
   * of slabs: at scale it read as a grey rectangle glitching out from beside the number. A "lit grid" needs a
   * primitive that *is* a grid, and `Tiles` — a real `count` × `columns` field — is that primitive, used by four of
   * the video's own stations.
   *
   * Its problem was never the shape but the **angle**: a tile is a flat quad, and from the video's eye-level rail —
   * only ~2.6 units above the ground at 26 out — it foreshortens to a sliver, which is exactly what the first
   * attempt looked like. So the camera comes down and in (`rail(0, 11, 5.2)`), which lifts the view angle onto the
   * ground from about 10° to about 34°. The tiles then read as a floor of quads rather than a smear.
   *
   * ⚠️ It is still the same world — same rig, same palette, same six primitives, same fog — and still aimed at the
   * one shared `AIM_Y`, so it is a seat on the video's own world rather than a second one.
   *
   * ⚠️ `color={BACKDROP}` for the reason on `Columns` in the same breath: on a still the figure is the *number*, so
   * issue 12's "the only saturated things in frame are figures" lands on the type instead of on the geometry. The
   * value is also lighter than the video's `TILE`, because nothing sits between the grid and the frame here.
   */
  scene: (bundle) => (
    <Tiles
      count={(bundle.indexes?.length ?? 5) * 4}
      columns={6}
      spacing={3}
      z={-3}
      size={2.4}
      color={BACKDROP}
    />
  ),
};

/** The closed set. A seventh shape would make the world read as separate demos, which is what the closed
 * set prevents — so it is listed here for the test to check against, not just asserted in prose. */
export const PRIMITIVES: readonly Primitive[] = ['terrain', 'column', 'tile', 'ring', 'particle', 'rig'];

/** Issue 12's ceiling on the establishing move. */
export const SETTLE_CEILING = 1.5;

export {STATIONS};


