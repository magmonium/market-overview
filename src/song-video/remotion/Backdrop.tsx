/**
 * The backdrop — **the field, lit.** (Drawn from `backdrop.ts`'s pure geometry.)
 *
 * ⚠️ **The vignette is not decoration, it is what keeps the type readable.** A drifting light behind a title is a
 * contrast accident waiting to happen, so the light is always damped toward the theme's own `field` at the edges —
 * which means the worst case for a title is the theme's own field, the thing every palette in the catalogue was
 * authored against.
 *
 * ⚠️ **The cover is deliberately absent here, and that reverses a rule.** The map says the cover, when supplied, is
 * drawn as *the field behind the type, through the palette's scrim* — and it was, at four fifths and then at seven
 * hundredths. Both were wrong, and the second one proved it: **a music cover very often carries its own title art**,
 * and a title printed at 7% is still a title — the frames had two of them, one of which lied about the song's name.
 * A field may take a photograph's *colour*; it cannot take its lettering, and nothing here can tell the two apart.
 * So the cover lives where it can be seen and read on its own terms: the **record's face**, on the disc, turning.
 *
 * ⚠️ **Hex alpha, not `rgba()`** — the house habit (`${ink}14`), and it keeps one colour one string.
 */
import {AbsoluteFill} from 'remotion';
import {blobs} from './backdrop.ts';
import type {Theme} from './themes.ts';

/** How many pools of light. Three is a field; five is weather. */
const COUNT = 3;

/** The most of the frame one blob may own, before the vignette. Light *in* a field, not a lamp — but light.
 *
 * ⚠️ Lowered from `0.5`, and it is the single biggest "eye-soothing" number in the composition: three pools at half
 * strength each is a *weather*, and what the frame needs is a warmth behind the artwork. The light is also what the
 * vignette is measured against, so a quieter one means the corners settle sooner. */
const MAX_ALPHA = 0.42;

/** A `0..1` strength as the two hex digits a CSS colour takes. ⚠️ Clamped, because `255` would otherwise round up. */
const alpha = (strength: number): string => {
  const byte = Math.max(0, Math.min(255, Math.round(strength * MAX_ALPHA * 255)));

  return byte.toString(16).padStart(2, '0');
};

export const Backdrop = ({
  theme,
  tint,
  seed,
  travelled,
  amplitude,
}: {
  readonly theme: Theme;
  /** The accent's own colour — one of the theme's authored four, chosen per piece. */
  readonly tint: string;
  readonly seed: string;
  readonly travelled: number;
  readonly amplitude: number;
}) => (
  <>
    {blobs(travelled, amplitude, {count: COUNT, seed}).map((blob, index) => (
      <AbsoluteFill
        key={index}
        style={{
          // A blob is a wide, soft ellipse rather than a circle: circles read as objects, and this is light.
          background: `radial-gradient(${Math.round(blob.radius * 100)}% ${Math.round(blob.radius * 70)}% at ` +
            `${(blob.x * 100).toFixed(2)}% ${(blob.y * 100).toFixed(2)}%, ${tint}${alpha(blob.strength)}, transparent 70%)`,
          opacity: 0.85,
        }}
      />
    ))}

    {/* ⚠️ The theme's own `glow` gets one pool of its own, so the accent never *replaces* the theme's light — and
        the frame is never lit by one colour. It rides its own slow diagonal, and it swells with the music — ⚠️ with
        the **settled** amplitude, since the caller hands one in: a pool that snapped to every peak would pulse at
        frame rate, which is a strobe rather than a swell. */}
    <AbsoluteFill
      style={{
        background:
          `radial-gradient(58% 42% at ${(34 + 30 * travelled).toFixed(2)}% ${(82 - 22 * travelled).toFixed(2)}%, ` +
          `${theme.palette.glow}${alpha(0.2 + 0.22 * amplitude)}, transparent 74%)`,
      }}
    />

    {/* The vignette: light falls off toward the field the palette was authored against — which is what keeps the
        title readable whatever the cover underneath is doing. ⚠️ Reaching further in than it did (46% rather than
        52%): the corners are where a long video tires the eye, and here they settle back into the theme's own field. */}
    <AbsoluteFill
      style={{
        background: `radial-gradient(140% 115% at 50% 46%, transparent 46%, ${theme.palette.field}cc 100%)`,
      }}
    />
  </>
);
