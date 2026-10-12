import {useThree} from '@react-three/fiber';
import {ThreeCanvas} from '@remotion/three';
import {useLayoutEffect} from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import type {FactsBundle} from '../bundle';
import {Rig, Terrain} from './primitives';
import {type Station, type Vec3, stationFor} from './stations';
import {EXPOSURE, FOCAL_LENGTH, lean} from './theme';

/**
 * The world — **one canvas for the whole brief.**
 *
 * ⚠️ Mounting a canvas per block would give thirteen WebGL contexts and thirteen separate environments,
 * which is both the render budget's worst case and the exact opposite of "one continuous world". So this
 * component sits behind the DOM for the entire composition and resolves *which station the camera is at*
 * from the global frame. The continuity is then structural: there is only ever one world.
 */

/** Issue 12's third camera rule: every move is eased **in and out**, so the camera never starts or stops
 * abruptly. A move that starts at full speed is the other way this reads as amateur. */
const ease = (t: number) => {
  const c = Math.min(Math.max(t, 0), 1);
  return c < 0.5 ? 4 * c * c * c : 1 - Math.pow(-2 * c + 2, 3) / 2;
};

const lerp3 = (a: Vec3, b: Vec3, t: number): Vec3 => [
  a[0] + (b[0] - a[0]) * t,
  a[1] + (b[1] - a[1]) * t,
  a[2] + (b[2] - a[2]) * t,
];

const CameraRig = ({from, to, progress}: {from: {position: Vec3; target: Vec3}; to: {position: Vec3; target: Vec3}; progress: number}) => {
  const {camera} = useThree();
  useLayoutEffect(() => {
    const position = lerp3(from.position, to.position, progress);
    const target = lerp3(from.target, to.target, progress);
    camera.position.set(position[0], position[1], position[2]);
    // ⚠️ `lookAt` with the default up vector: **no roll, ever** (issue 12's second rule). Rotation about
    // the viewer's own axis is the single strongest nausea trigger there is.
    camera.lookAt(target[0], target[1], target[2]);
    // ⚠️ The focal length is never written. Depth comes from moving the camera, never from zooming —
    // zoom plus motion is what disorients (issue 12's first rule).
    camera.updateMatrixWorld();
  }, [camera, from, to, progress]);
  return null;
};

/** ⚠️ Exposure is pinned, so the same value looks the same on every run and a re-render matches. */
const Pinned = () => {
  const {gl} = useThree();
  useLayoutEffect(() => {
    gl.toneMappingExposure = EXPOSURE;
  }, [gl]);
  return null;
};

const blockAt = (bundle: FactsBundle, frame: number) =>
  bundle.timeline?.blocks?.find((b) => frame >= b.from && frame < b.from + b.duration);

/**
 * ⚠️ `station` **overrides** the rail. 0085_12's thumbnail renders this same world from `THUMBNAIL`, which is not on
 * the rail at all — so the still reuses the palette, lighting rig and primitive set (issue 14's whole reason for
 * choosing a composition over a screenshot) without pretending to be a frame of the video.
 *
 * Omitted, this behaves exactly as before: the station is resolved from the block the frame falls in.
 */
export const World = ({bundle, station: override}: {bundle: FactsBundle; station?: Station}) => {
  const frame = useCurrentFrame();
  const {width, height, fps} = useVideoConfig();

  // ⚠️ Outside every slot — before the first block or in a gap — the world holds the opening shot rather
  // than disappearing. A blank frame here would read as a glitch.
  const block = blockAt(bundle, frame) ?? bundle.timeline?.blocks?.[0];
  const station = override ?? (block ? stationFor(block.key) : undefined);
  if (!station) {
    return null;
  }

  const local = block ? frame - (block.from ?? 0) : 0;
  const progress = station.settle <= 0 ? 1 : ease(local / (station.settle * fps));

  // The day's own direction, from the headline index — this is the whole of the "data-driven variation
  // so the terrain differs daily on its own" requirement. The camera never varies (issue 12: the 3D is one
  // animation for both editions); only what is in the world does.
  const leanPercent = bundle.indexes?.[0]?.window?.change ?? 0;
  // ⚠️ An overridden station has no block, so it needs a name of its own for the seed — otherwise every seed in the
  // still would end in the empty string and the particle field would be identical day to day.
  const seed = `${bundle.meta?.date ?? 'brief'}:${override ? 'thumbnail' : block?.key ?? ''}`;

  return (
    <ThreeCanvas
      width={width}
      height={height}
      camera={{fov: FOCAL_LENGTH, position: station.from.position}}
      style={{position: 'absolute', inset: 0}}
      gl={{antialias: true}}
    >
      <Rig />
      <Pinned />
      <CameraRig from={station.from} to={station.to} progress={progress} />
      <Terrain leanPercent={lean(leanPercent)} />
      {station.scene(bundle, seed)}
    </ThreeCanvas>
  );
};
