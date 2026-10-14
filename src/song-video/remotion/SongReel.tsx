/**
 * `SongReel` — one full-length piece: **the artwork on the left, the song written on the right, its landscape
 * beneath them.**
 *
 * ⚠️ **The layout is shared by every theme, deliberately.** The map says a theme is *a skin over one shared
 * structure, never a different film*; the operator then asked for the disc left and the text right, and that is now
 * the structure rather than a theme's taste. What a theme changes is its palette, its type treatment, its motif and
 * how its colour moves — never where the eye goes. Someone who has watched one reel can read the next one's shape
 * instantly, which is the whole reason to have a structure at all.
 *
 * ⚠️ **And the artwork turns in every theme, which it once did not.** The `disc`/`notes` split decides the theme's
 * *motif* — a record it turns, or glyphs drifting in the field — and nothing else. `neon` and `aurora` used to draw the
 * artwork as a card that only floated, and a round thing with a centre label **is** a record on screen whatever the
 * code calls it: so the one difference the card produced was a disc standing still, which the operator reported as a
 * fault, twice, and read exactly right both times. What separates the themes is the palette, the type and the drifting
 * notes — not withheld motion.
 *
 * ⚠️ **The mark is the artwork's centre, not a corner badge.** It used to sit top-right on the brief's chip; it is
 * now the record's **label** and turns with the disc, which is why the disc lost its spindle hole — a hole punched
 * through somebody's logo is a hole punched through their logo.
 *
 * ⚠️ **Nothing here reads a clock or a random number.** The motion is `frame` and the envelope; the one *choice*
 * this file makes — which of the theme's authored accents lights the field — is a pure function of the recorded
 * digest, so two renders of one song match and two songs do not.
 * ⚠️ **The line under the title is the piece's *time*, and it changes.** The still carries the length as a caption —
 * a fact a still can hold — so the reel, which has a clock, counts through that same number instead: `০:৪২ / ৩:০২`,
 * derived from the frame and never from the machine's clock (ADR 0003).
 */
import {useMemo} from 'react';
import {useAudioData} from '@remotion/media-utils';
import {AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Typeface} from '../../../remotion/fonts.ts';
import {FONT} from '../../../remotion/theme.ts';
import {accentFor} from './accent.ts';
import {Backdrop} from './Backdrop.tsx';
import {clockFor} from './clock.ts';
import {envelopeFromAudio} from './envelope.ts';
import {Disc, Notes} from './Motif.tsx';
import {turnedAt} from './motif.ts';
import type {SongReelProps} from './props.ts';
import {themeFor} from './themes.ts';
import {bars, playhead, smoothed} from './waves.ts';

/** How the landscape is resolved. A theme will own this once themes exist; the geometry does not care. */
const COLUMNS = 96;
const WAVE_HEIGHT = 250;
const INSET = 96;

/**
 * The art column, and the artwork inside it.
 *
 * ⚠️ **Fixed pixels, never fractions of the frame.** A composition that rescaled itself for a long title would move
 * the eye from reel to reel, which is the one thing a shared structure exists to prevent. A title that will not fit
 * its column is a title to shorten, not a layout to bend.
 */
const ART = 560;
const DISC = 430;
/** Everything right of the artwork — where the title lives now. */
const TEXT_LEFT = INSET + ART + 80;
/** The band the artwork and the title share, above the landscape. */
const BAND = 560;

export const SongReel = ({title, song, theme: themeId, cover, mark, seed, lang, duration}: SongReelProps) => {
  const frame = useCurrentFrame();
  const {durationInFrames, fps} = useVideoConfig();

  // ⚠️ **Refuses rather than defaults** — see `themeFor`. A reel rendered in the wrong theme is not
  // distinguishable, by eye, from a reel rendered in the right one.
  const theme = themeFor(themeId);

  // ⚠️ The one choice this composition makes, and it is a function of the record rather than of chance.
  const accent = accentFor(theme.accents, seed);
  const art = cover ? staticFile(cover) : null;

  // ⚠️ **The gate is the hook's own.** `useAudioData` calls `delayRender()` and resolves only once the song has
  // decoded — and `cancelRender()` if it cannot — so a render **waits or refuses**, exactly as the map requires,
  // and never draws a wave made of nothing. The `null` branch below is therefore a studio artefact: no render
  // emits it.
  const audio = useAudioData(staticFile(song));

  // ⚠️ Reduced once per change, never once per frame: the landscape is frame-independent by design.
  const clock = useMemo(() => (audio ? envelopeFromAudio(audio, {fps}) : null), [audio, fps]);
  const bands = useMemo(() => (clock ? bars(clock, {columns: COLUMNS}) : []), [clock]);

  // ⚠️ **Indexed against the piece's length, never the reverse.** A decoder and a container can disagree by a
  // frame, so a frame past the envelope's end reuses its last amplitude rather than feeding `undefined` into a
  // coordinate — which is how a NaN gets into a style and the wave disappears.
  //
  // ⚠️ **And it is the *settled* envelope that drives the pulse and the light.** The landscape keeps the peaks — it is
  // the song's shape and has to stay honest — but a halo fed a true peak changes by tens of pixels between one frame
  // and the next, which is a strobe rather than a swell. `theme.smooth` is how long a theme wants that average, so
  // the calm themes breathe and `neon` still moves.
  const settled = useMemo(() => (clock ? smoothed(clock, {window: theme.smooth}) : null), [clock, theme.smooth]);
  const amplitude = settled?.[Math.min(frame, settled.length - 1)] ?? 0;
  const travelled = playhead(frame, durationInFrames);

  return (
    <AbsoluteFill style={{background: theme.palette.field, color: theme.palette.ink, fontFamily: FONT}}>
      {/* ⚠️ The wait for the vendored face, exactly as the brief does it: the render refuses rather than
          falling back to whatever face the host happens to have. */}
      <Typeface />

      {/* ⚠️ **The song itself, and there is no second audio step.** Unlike the brief — which normalises a bed and
          muxes it in with ffmpeg — the reel's audio is the master, encoded once by the renderer at one pinned
          bitrate, in the same file as the picture (issue 09). A song that is analysed but never *heard* would be
          the one defect every still in this project looks perfectly good through. */}
      <Audio src={staticFile(song)} />

      {/* The field, lit: three pools of the accent's light, drifting their own slow arc, widened by the amplitude.
          Everything above this layer is composed against it. */}
      <Backdrop theme={theme} tint={accent.tint} seed={seed} travelled={travelled} amplitude={amplitude} />

      {/* ⚠️ The notes themes keep their motif **across the whole frame**, behind the type: it is their grammar
          (issue 11: the motif must never rest), and confining it to the art column would leave the right half of a
          `neon` reel dead. It is held back with opacity — atmosphere here, because the artwork is the subject. */}
      {theme.motif === 'notes' ? (
        <div style={{position: 'absolute', inset: 0, opacity: 0.45}}>
          <Notes theme={theme} travelled={travelled} amplitude={amplitude} seed={seed || theme.id} count={9} />
        </div>
      ) : null}

      {/* ⚠️ **The mark is no longer here.** It was a chip in this corner; it is now the artwork's centre — the
          record's label, turning with the disc. A corner badge *and* a label would be the same mark twice in one
          frame, and no corner is worth that. */}

      {/* ── the artwork, left ───────────────────────────────────────────────────────────────────────────────── */}
      <div
        style={{
          position: 'absolute',
          left: INSET,
          top: 130,
          width: ART,
          height: BAND,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {/* ⚠️ **The theme's own object (issue 05) — and in every theme it is the record.** The `disc`/`notes` split
            decides the theme's *motif* (a record it turns, or glyphs drifting in the field); it no longer decides
            whether the artwork moves. ⚠️ **`turnedAt`, not `travelled`**: a record turns at a *rate*, so a long song
            simply gets more revolutions — where the old traversal-bound spin made six turns across the whole piece,
            about eleven degrees a second, and read as a disc standing still. */}
        <Disc theme={theme} cover={art} mark={mark} turned={turnedAt(frame, fps)} amplitude={amplitude} size={DISC} />
      </div>

      {/* ── the song, right ─────────────────────────────────────────────────────────────────────────────────── */}
      <div
        style={{
          position: 'absolute',
          left: TEXT_LEFT,
          right: INSET,
          top: 130,
          height: BAND,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
        }}
      >
        <div style={{fontSize: 104, fontWeight: 700, lineHeight: 1.15, letterSpacing: '-0.01em'}}>{title}</div>
        {/* ⚠️ The rule, in **the accent** rather than the theme's `glow`: it is the one element that belongs to this
            song's colour, and the halo makes it read as a lit edge rather than as a line of type. */}
        <div
          style={{
            width: 128,
            height: 6,
            borderRadius: 3,
            background: accent.tint,
            marginTop: 36,
            // ⚠️ A halo rather than a bar: it is the one element of the frame that belongs to *this song's* colour, and
            // the glow makes it read as a lit edge. Softer than it was — a 34-pixel halo behind a 6-pixel rule is a
            // highlight, and the frame already has a sun in it.
            boxShadow: `0 0 22px ${accent.tint}`,
          }}
        />
        {/* ⚠️ **The piece's time, changing** — what the still prints as a caption, here counting. A still can carry
            the length as a fact; a reel has a clock, so it walks through that same number instead, in the caption's
            own numerals, with the total exactly as Python formatted it (so the two artefacts can never disagree).

            ⚠️ Frame-derived, never `Date.now()` (ADR 0003): `tabular-nums` keeps the digits from jittering as they
            tick, and a rebuild ticks the same way. */}
        <div
          style={{
            fontSize: 34,
            fontWeight: 500,
            letterSpacing: '0.06em',
            opacity: 0.82,
            marginTop: 26,
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          {clockFor(frame, fps, lang, duration)}
        </div>
        {/* ⚠️ **The rail is not in this column any more.** It became a *radio dial* — a thin white line with a red
            needle — and a needle that travels a different line from the landscape's own playhead is two progress marks
            pointing at two different x's. It now sits directly above the landscape, spanning the same width, so the
            needle and the playhead are the same vertical line seen twice. */}
      </div>

      {/* The wave region. The inset is the composition's business, not the geometry's: the landscape and the
          playhead both live in `0..1`, and nothing in `waves.ts` knows what a pixel is.

          ⚠️ Drawn only once the clock exists — before that the frame is the title and the mark and nothing
          else, a *partial* frame that no render emits because the hook has already paused it. */}
      {clock ? (
        <>
          {/* ⚠️ **The radio dial.** The operator's words, as they typed them: *"white line … progress is with red bar"* —
              and then the correction that settled it: *"the bar will be vertical and thin like radio indicator"*, which
              is precisely what a tuning needle is. So the track is a hairline of the theme's own ink, and the progress
              is a narrow red needle that travels along it.

              ⚠️ **It spans the landscape's own width and sits just above it, deliberately.** The needle's position and
              the landscape's playhead are the same number (`travelled`), so giving them the same x makes the frame read
              as **one instrument** — a dial over the song's shape — instead of two progress marks pointing at different
              places.

              ⚠️ **And it is not on the still.** A thumbnail has no progress to report: a needle frozen a third of the
              way along would be a small lie about a song nobody has heard yet. */}
          <div style={{position: 'absolute', left: INSET, right: INSET, bottom: 120 + WAVE_HEIGHT + 30, height: 2}}>
            <div style={{position: 'absolute', inset: 0, background: `${theme.palette.ink}30`, borderRadius: 999}} />
            {/* The needle: taller than the track it reads, which is what makes it an indicator rather than a tick. */}
            <div
              style={{
                position: 'absolute',
                left: `${travelled * 100}%`,
                top: -9,
                width: 3,
                height: 20,
                borderRadius: 999,
                background: theme.palette.progress,
                transform: 'translateX(-50%)',
              }}
            />
          </div>

          <div style={{position: 'absolute', left: INSET, right: INSET, bottom: 120, height: WAVE_HEIGHT}}>
            {bands.map((band, index) => {
              const played = band.at <= travelled;
              return (
                <div
                  key={index}
                  style={{
                    position: 'absolute',
                    left: `${band.at * 100}%`,
                    bottom: 0,
                    width: `${100 / COLUMNS}%`,
                    // ⚠️ Through the theme's curve: the clock stays honest, and the picture still has to read.
                    height: theme.curve(band.height) * WAVE_HEIGHT,
                    transform: 'translateX(-50%)',
                    // ⚠️ **Graded, not switched** — but only the *strengths* moved. The played half used to arrive at
                    // almost full strength against a flat grey, and what a long video needs is the two halves closer
                    // together: the amber still reads as progress, and the road ahead is still a road. ⚠️ The unplayed
                    // half is **not** faded to nothing — the landscape ahead of the playhead is the design's own claim
                    // (*the song's own shape is the narrative*), and a shape nobody can see is not a narrative.
                    background: played ? theme.palette.wave : theme.palette.muted,
                    opacity: played ? 0.84 : 0.4,
                    borderRadius: 4,
                  }}
                />
              );
            })}
  
            {/* ⚠️ **The pulse.** The playhead brightens and widens with the amplitude at *this* frame, so the picture
                reports the music's present moment and not only its overall shape. It reads the frame's own envelope
                value, so it is as deterministic as the landscape is. */}
            <div
              style={{
                position: 'absolute',
                left: `${travelled * 100}%`,
                top: -28,
                bottom: 0,
                // ⚠️ **A breath, not a cursor.** Softer and narrower than it was, with a smaller halo: the pulse is the
                // music's present moment and it should *swell*, which is also why the amplitude feeding it is the
                // settled one (`theme.smooth`) rather than the frame's raw peak.
                width: 2 + amplitude * 3,
                background: theme.palette.ink,
                opacity: 0.7,
                boxShadow: `0 0 ${18 + amplitude * 30}px ${accent.tint}`,
              }}
            />
          </div>
        </>
      ) : null}
    </AbsoluteFill>
  );
};
