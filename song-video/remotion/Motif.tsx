/**
 * The motif — **the theme's own moving object, drawn.** (Map issue 05)
 *
 * ⚠️ **Rotation is invisible without an asymmetric feature.** A label that is uniform turns about its own centre
 * without anything on screen changing, so the disc carries a **sheen** that turns with it. With a cover supplied,
 * the cover does that job instead — and with neither, the rotation would be decoration nobody could see.
 *
 * ⚠️ **The pulse is scale, never speed.** The baseline turn is the traversal; the amplitude only makes the disc
 * *breathe*. Making it spin faster on loud moments would read as a glitch rather than as music.
 *
 * ⚠️ **The motif is drawn from shapes, not glyphs.** A musical `♪` in a title would resolve out of the brief's
 * vendored Noto subsets into whatever face the host happens to own — the exact non-determinism the vendored
 * typeface exists to prevent, and it would fail silently rather than loudly.
 */
import {Img} from 'remotion';
import {discAngle, noteAt} from './motif.ts';
import type {Mark} from './props.ts';
import type {Theme} from './themes.ts';

/** How many whole turns the disc makes across the piece. Slow on purpose: this is a record, not a fidget. */
const TURNS = 6;

/** How much a loud moment swells the disc. Small, because a heartbeat is small. */
const PULSE = 0.05;

/** The label's diameter, as a fraction of the disc. A 12-inch single's label is about this. */
const LABEL = 0.34;

/**
 * The operator's mark, as a record's **label** — the centre of the motif, turning with it.
 *
 * ⚠️ **The plate is not the old corner chip rescued.** A mark drawn raw on a turning cover is a legibility accident:
 * the artwork passes behind it, and a mark whose ink matches whatever is under it at that moment has no edge. The
 * plate is the colour the brief's loader already computed from the mark's own ink polarity — the same decision the
 * video used to wear in a corner — worn here as a circle, which is what makes it read as a record's label rather
 * than as a sticker. The **still** keeps the raw mark: nothing behind it moves, so nothing needs the plate.
 *
 * ⚠️ It is centred and it turns with the disc, deliberately: a label that counter-rotated to stay upright would be
 * the one part of the record that was not part of the record.
 */
export const MarkLabel = ({
  mark,
  size,
  amplitude = 0,
}: {
  readonly mark: Mark;
  /** The plate's diameter, in pixels. */
  readonly size: number;
  readonly amplitude?: number;
}) => {
  if (!mark) {
    return null;
  }

  return (
    <div
      style={{
        position: 'absolute',
        left: '50%',
        top: '50%',
        width: size,
        height: size,
        marginLeft: -size / 2,
        marginTop: -size / 2,
        borderRadius: '50%',
        background: mark.chip,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        // ⚠️ The ring is the label's edge, and it brightens with the music — the one thing on the disc that says
        // *this moment* rather than *this piece*.
        boxShadow: `0 0 0 2px ${mark.chip}, 0 0 ${14 + amplitude * 30}px ${mark.chip}`,
      }}
    >
      <Img
        src={mark.src}
        style={{
          // ⚠️ Bounded by **height**, never by width: a mark is whatever shape the operator drew, and a wide one
          // must not run past its own label.
          height: size * 0.56,
          maxWidth: size * 0.8,
          objectFit: 'contain',
          display: 'block',
        }}
      />
    </div>
  );
};

export const Disc = ({
  theme,
  cover,
  mark,
  travelled,
  amplitude,
  size = 340,
}: {
  readonly theme: Theme;
  readonly cover: string | null;
  readonly mark: Mark;
  readonly travelled: number;
  readonly amplitude: number;
  readonly size?: number;
}) => {
  const turn = discAngle(travelled, {turns: TURNS});
  const breathe = 1 + amplitude * PULSE;

  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        transform: `scale(${breathe})`,
        // The disc sits *in* the field rather than on it: a soft shadow keeps it from reading as a sticker.
        // ⚠️ **And a rim, because a flat disc reads as a blob.** `muted` on `field` is a dark circle on a dark panel
        // — the sheen and the spindle were the only things visible in a still. A hairline ring in the theme's own
        // ink keeps the edge crisp whatever the field does.
        boxShadow: `0 40px 120px rgba(0, 0, 0, 0.45), inset 0 0 0 2px ${theme.palette.ink}1f`,
      }}
    >
      <div
        style={{
          position: 'relative',
          width: '100%',
          height: '100%',
          borderRadius: '50%',
          overflow: 'hidden',
          // ⚠️ **Grooves say *record* at a glance.** Fine concentric rings, a hair lighter than the face, plus a
          // soft wash of light at the top left — a record catching the light, and the texture a plain circle lacks.
          // They are radially symmetric, so they do **not** show the turn: the sheen is still what makes rotation
          // visible, and this is only depth.
          background: [
            `radial-gradient(circle at 34% 26%, ${theme.palette.ink}14, transparent 60%)`,
            `repeating-radial-gradient(circle at 50% 50%, ${theme.palette.ink}0a 0 1px, transparent 1px 10px)`,
            theme.palette.muted,
          ].join(', '),
          transform: `rotate(${turn}deg)`,
        }}
      >
        {cover ? (
          <Img
            src={cover}
            style={{width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%', opacity: 0.92}}
          />
        ) : null}

        {/* ⚠️ **The sheen, and it is load-bearing.** It is the asymmetry that lets the eye see the turn; without
            it, or a cover, a plain circular label would rotate invisibly for the whole song. */}
        <div
          style={{
            position: 'absolute',
            left: '50%',
            top: 0,
            width: size * 0.07,
            height: '50%',
            marginLeft: -size * 0.035,
            background: `linear-gradient(180deg, ${theme.palette.glow}, transparent)`,
            opacity: 0.55,
          }}
        />

        {/* ⚠️ **A record's centre is a label or a hole, never both.** The mark goes *on* the label and turns with the
            disc — so the spindle that used to be here is gone when there is a mark, because a hole punched through
            the operator's own logo is the one thing this centre cannot be. With no mark, the disc keeps its hole. */}
        {mark ? (
          <MarkLabel mark={mark} size={size * LABEL} amplitude={amplitude} />
        ) : (
          <div
            style={{
              position: 'absolute',
              left: '50%',
              top: '50%',
              width: size * 0.09,
              height: size * 0.09,
              marginLeft: -size * 0.045,
              marginTop: -size * 0.045,
              borderRadius: '50%',
              background: theme.palette.field,
            }}
          />
        )}
      </div>
    </div>
  );
};

/**
 * One note, **drawn rather than typed.**
 *
 * ⚠️ A musical `♪` in the brief's vendored subsets would resolve out of the face into whatever the host has —
 * the exact silent non-determinism the vendored typeface exists to prevent. A head, a stem and a flag are three
 * shapes that render the same everywhere, and they scale.
 */
const Note = ({theme}: {readonly theme: Theme}) => (
  <svg width="86" height="118" viewBox="0 0 86 118" fill="none" xmlns="http://www.w3.org/2000/svg">
    {/* The flag first, so the stem's cap sits over it. */}
    <path d="M50 8 C 78 24, 80 46, 58 66 C 72 42, 68 24, 50 18 Z" fill={theme.palette.glow} />
    <rect x="44" y="8" width="7" height="88" rx="3.5" fill={theme.palette.wave} />
    <ellipse cx="26" cy="94" rx="25" ry="19" transform="rotate(-18 26 94)" fill={theme.palette.wave} />
  </svg>
);

/**
 * The flowing notes — the motif for the two themes that own it.
 *
 * ⚠️ **The pulse is brightness and a little scale, never the drift speed.** A note that sped up on a loud moment
 * would read as a stutter; the drift is the traversal's, and the amplitude only decides how *present* a note is.
 */
export const Notes = ({
  theme,
  travelled,
  amplitude,
  seed,
  count = 7,
}: {
  readonly theme: Theme;
  readonly travelled: number;
  readonly amplitude: number;
  readonly seed: string;
  readonly count?: number;
}) => (
  <div style={{position: 'absolute', inset: 0}}>
    {Array.from({length: count}, (_, index) => {
      const note = noteAt(index, travelled, {seed, count});
      return (
        <div
          key={index}
          style={{
            position: 'absolute',
            left: `${note.x * 100}%`,
            top: `${note.y * 100}%`,
            transform: `translate(-50%, -50%) scale(${note.size * (1 + amplitude * 0.2)})`,
            opacity: 0.22 + amplitude * 0.55,
          }}
        >
          <Note theme={theme} />
        </div>
      );
    })}
  </div>
);
