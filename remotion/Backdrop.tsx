import {useMemo} from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import type {FactsBundle} from './bundle';
import {seeded} from './theme';

/**
 * The backdrop — **a vibrant, animated, fully DOM background.**
 *
 * ⚠️ **This replaces the three.js world** (`remotion/world/`, deleted). The 3D layer bought depth at real
 * cost: a WebGL canvas, an ANGLE-only Chromium flag, a hard dependency on `three` / `@react-three/fiber`, and
 * a determinism caveat (`test_frame_identity.py` measured subpixel rasterisation drift *because* the world
 * moved). None of that is needed to put motion and colour behind the cards. This component is plain CSS: no
 * canvas, no extra dependency, and — being a pure function of the frame and the seed — bit-for-bit reproducible
 * where the old world was only reproducible in the limit.
 *
 * ⚠️ **Everything here is frame-derived, never wall-clock.** The lobes drift on `Math.sin(frame / fps)`, the
 * grid scrolls on the same clock, and every starting position comes from `seeded(seed)`. So the same bundle
 * gives the same frame on any machine — the promise ADR 0003 rests on — and the day's direction only chooses
 * *which* palette, never *where* anything lands.
 *
 * ⚠️ **The still and the video share it, at frame 0.** `Thumbnail.tsx` mounts this too: at frame 0 every drift
 * term is zero, so the still is the settled backdrop rather than a snapshot of it mid-move. That is what lets
 * `test_frame_identity.py` keep asserting bit-exactness for the still while the video animates.
 */

/** A drifting aurora lobe. Placed once from the seed; its *motion* comes from the frame. */
type Blob = {color: string; size: number; x: number; y: number; drift: number; speed: number; phase: number};
/** A rising speck of light. `y` is a 0..1 start that wraps as the clock advances. */
type Speck = {x: number; y: number; size: number; speed: number; phase: number};

/**
 * ⚠️ **Two palettes, chosen by the day's direction and nothing else.** A rising session bathes the frame in
 * emerald, cyan and violet; a falling one in rose, amber and pink. This is the whole of "the backdrop differs
 * daily on its own" — the composition never varies, only the light does.
 */
const RISING = ['#2be39a', '#22d3ee', '#38bdf8', '#a78bfa', '#34d399'];
const FALLING = ['#ff5470', '#fb923c', '#f472b6', '#c084fc', '#f43f5e'];

/** ⚠️ A **seed string**, not a generator, so the field is a pure function of its inputs. */
const lobes = (seed: string, rising: boolean): Blob[] => {
  const random = seeded(seed);
  const colors = rising ? RISING : FALLING;
  return Array.from({length: 6}, (_, index) => ({
    color: colors[index % colors.length],
    size: 40 + random() * 46,
    x: 6 + random() * 88,
    y: 2 + random() * 88,
    drift: 7 + random() * 13,
    // ⚠️ Cycles per second, kept low (periods of ~11-25 s) so the motion reads as a slow breathe rather than
    // as something the eye tracks. Faster reads as a lava lamp, which competes with the figures.
    speed: 0.04 + random() * 0.05,
    phase: random() * Math.PI * 2,
  }));
};

/** ⚠️ A **seed string**, not a generator, for the same reason as `lobes`. */
const specks = (seed: string): Speck[] => {
  const random = seeded(seed);
  return Array.from({length: 46}, () => ({
    x: random() * 100,
    y: random() * 100,
    size: 1.4 + random() * 3.4,
    speed: 0.02 + random() * 0.05,
    phase: random() * 100,
  }));
};

/** Wrap into 0..1 so a rising speck leaves the top and re-enters at the bottom rather than piling up. */

export const Backdrop = ({bundle}: {bundle: FactsBundle}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const seconds = frame / fps;

  // ⚠️ The day's own direction, from the headline index — the same field the old world's terrain leaned off.
  // An absent row is a neutral (rising) day rather than an error: the backdrop is decor and never a claim.
  const change = bundle.indexes?.[0]?.window?.change ?? 0;
  const rising = change >= 0;

  const seed = `${bundle.meta?.date ?? 'brief'}:backdrop`;
  const blobs = useMemo(() => lobes(seed, rising), [seed, rising]);
  const dust = useMemo(() => specks(`${seed}:dust`), [seed]);

  return (
    <AbsoluteFill style={{overflow: 'hidden', background: '#07060f'}}>
      {/* The base gradient — indigo through violet into deep teal. Saturated on purpose: the cards sit over a
          dark scrim, so the only place this reads at full strength is the lower "atmosphere" band and the two
          framing blocks, which is exactly where a vibrant field is wanted. */}
      <AbsoluteFill
        style={{background: 'linear-gradient(140deg, #1b1040 0%, #2a0f57 40%, #0b2f4d 74%, #071a2b 100%)'}}
      />

      {/* The aurora lobes. `screen` blending keeps overlapping lobes bright rather than muddy — the failure
          mode of stacking translucent gradients over a dark base. */}
      {blobs.map((blob, index) => {
        const angle = seconds * blob.speed * Math.PI * 2 + blob.phase;
        const x = blob.x + Math.sin(angle) * blob.drift;
        const y = blob.y + Math.cos(angle * 0.8) * blob.drift;
        const scale = 1 + Math.sin(seconds * 0.3 + blob.phase) * 0.12;
        return (
          <div
            key={index}
            style={{
              position: 'absolute',
              left: `${x}%`,
              top: `${y}%`,
              width: `${blob.size}%`,
              height: `${blob.size}%`,
              transform: `translate(-50%, -50%) scale(${scale})`,
              background: `radial-gradient(closest-side, ${blob.color}cc, ${blob.color}00 72%)`,
              opacity: 0.5,
              mixBlendMode: 'screen',
            }}
          />
        );
      })}

      {/* The day's tint, pooled at the top of the frame. */}
      <AbsoluteFill
        style={{
          background: rising
            ? 'radial-gradient(120% 80% at 50% 0%, rgba(16,185,129,0.20), transparent 70%)'
            : 'radial-gradient(120% 80% at 50% 0%, rgba(244,63,94,0.20), transparent 70%)',
        }}
      />

      {/* A slowly scrolling grid, so the field reads as a place rather than as a blur. */}
      <AbsoluteFill
        style={{
          backgroundImage:
            'repeating-linear-gradient(0deg, rgba(255,255,255,0.05) 0px, rgba(255,255,255,0.05) 1px, transparent 1px, transparent 64px), ' +
            'repeating-linear-gradient(90deg, rgba(255,255,255,0.05) 0px, rgba(255,255,255,0.05) 1px, transparent 1px, transparent 64px)',
          backgroundPosition: `${-seconds * 22}px ${-seconds * 22}px`,
          opacity: 0.6,
        }}
      />

      {/* Rising specks — the layer's own fine motion, and the reason the field never looks frozen between the
          lobes' slower cycles. */}
      {dust.map((speck, index) => {
        const y = wrap(speck.y / 100 - seconds * speck.speed) * 100;
        const x = speck.x + Math.sin(seconds * 0.4 + speck.phase) * 1.6;
        return (
          <div
            key={index}
            style={{
              position: 'absolute',
              left: `${x}%`,
              top: `${y}%`,
              width: speck.size,
              height: speck.size,
              borderRadius: '50%',
              background: '#ffffff',
              opacity: 0.32,
            }}
          />
        );
      })}

      {/* ⚠️ A vignette, so text always has something dark to sit on. Without it the bright lobe centres sit
          behind the type and a number loses its edge — the one thing a background is never allowed to cost. */}
      <AbsoluteFill
        style={{
          background: 'radial-gradient(120% 90% at 50% 45%, transparent 38%, rgba(6,6,16,0.78) 100%)',
        }}
      />
    </AbsoluteFill>
  );
};

const wrap = (value: number) => ((value % 1) + 1) % 1;
