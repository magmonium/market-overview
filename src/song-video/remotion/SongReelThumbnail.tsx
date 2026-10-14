/**
 * `SongReelThumbnail` — the still that travels with the reel (issue 08).
 *
 * ⚠️ **Its own composition, never a frame grabbed from the video.** A grabbed frame is composed for motion —
 * mid-move, possibly half-faded, and always at the mercy of which frame was picked — so issue 14's rule is kept
 * here as it was in the brief: the still has its own camera, and that camera has no entrance at all, which is what
 * makes `--frame=0` **the settled state** rather than a frame chosen to be past one.
 *
 * ⚠️ **No audio, and no envelope.** A thumbnail is not a measurement, and a decorative landscape that looked like
 * the song's shape would be a small lie on the one artefact looked at *before* the song is heard. What it carries
 * is what issue 08 asks for: the mark, the title, and the cover art when there is one.
 *
 * ⚠️ **The missing cover is a designed state, not a hole.** The theme's own motif takes the art panel, which is
 * why this composition reads as composed with no cover at all — and also why it never needs `useAudioData`, so it
 * cannot fail on a decode.
 */
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {Typeface} from '../../../remotion/fonts.ts';
import {FONT} from '../../../remotion/theme.ts';
import {accentFor} from './accent.ts';
import {Backdrop} from './Backdrop.tsx';
import {Disc, Notes} from './Motif.tsx';
import {captionFor} from './caption.ts';
import type {SongReelProps} from './props.ts';
import {themeFor} from './themes.ts';

/** ⚠️ The still's geometry in pixels, and fixed: a still has no entrance to animate out of. */
const MARGIN = 64;
/** ⚠️ **Bigger than the reel's `72`.** This file is looked at *as* a thumbnail, on someone else's page, and a mark
 * that reads at 1920×1080 disappears at 320 px wide. */
const MARK = 132;
const ART = 400;

/**
 * A fixed pose for the decorative motif.
 *
 * ⚠️ Deliberately **not** a frame of the reel: the amplitude here is a constant, so the motif is a still life
 * rather than a claim about what the song does at any moment. The disc's sheen sits at the angle this rotation
 * puts it on, which is the whole reason the pose is a named number rather than `0`.
 */
const POSE = {
  travelled: 0.34,
  /**
   * ⚠️ **The disc's pose, in revolutions — and it is the angle the traversal used to land on.** The old still drew the
   * disc at `discAngle(0.34, {turns: 6})` = 14.4°, so `0.04` revolutions reproduces the thumbnail exactly while the
   * *reel* stops quoting the traversal and starts quoting a turntable. A still has no rate; it has one pose.
   */
  turned: 0.04,
  amplitude: 0.62,
} as const;

export const SongReelThumbnail = ({title, theme: themeId, cover, mark, seed, lang, duration}: SongReelProps) => {
  // ⚠️ Refuses rather than defaults, like the reel: a thumbnail in the wrong theme is indistinguishable from one
  // in the right theme, and this is the file an uploader picks by eye.
  const theme = themeFor(themeId);
  // ⚠️ The **word** is this layer's, the **number** is Python's — see `caption.ts`. Neither side invents the other.
  const caption = captionFor(lang, duration);
  // ⚠️ **The same accent the reel is lit by**, from the same recorded digest: the still is the reel's own thumbnail,
  // and a still in a different colour from the film beside it is the sort of thing nobody can name and everybody can
  // see. Both are frame 0 of the same light.
  const accent = accentFor(theme.accents, seed);

  return (
    <AbsoluteFill style={{background: theme.palette.field, color: theme.palette.ink, fontFamily: FONT}}>
      <Typeface />

      {/* ⚠️ **The same light the reel opens on** — the accent's pools at `travelled: 0` with a resting amplitude, so
          the still is literally frame 0 of the film's own field rather than a lookalike. A still has no clock, so
          nothing in this layer can disagree with the song. */}
      <Backdrop theme={theme} tint={accent.tint} seed={seed} travelled={0} amplitude={0} />

      {/* The art panel: the cover, or the theme's own motif when there is none. */}
      <div
        style={{
          position: 'absolute',
          left: MARGIN,
          top: MARGIN + MARK + 36,
          width: ART,
          height: ART,
          borderRadius: 36,
          overflow: 'hidden',
          // ⚠️ Slanted rather than flat: a panel of solid `muted` reads as a placeholder at thumbnail size.
          background: `linear-gradient(150deg, ${theme.palette.muted}, ${theme.palette.field})`,
          boxShadow: `0 30px 70px rgba(0, 0, 0, 0.42), inset 0 0 0 1px ${theme.palette.ink}14`,
        }}
      >
        {cover ? (
          <Img src={staticFile(cover)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
        ) : (
          <AbsoluteFill style={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            {theme.motif === 'disc' ? (
              <Disc
                theme={theme}
                cover={null}
                // ⚠️ **No label on this disc, deliberately.** In the reel the mark rides the record because the
                // record *turns* and the label is part of it; here it is drawn raw, once, in the corner above — and
                // twice in one frame is a mark that looks like a mistake rather than a signature.
                mark={null}
                turned={POSE.turned}
                amplitude={POSE.amplitude}
                size={ART * 0.82}
              />
            ) : (
              <div style={{position: 'absolute', left: 0, right: 0, top: 84, height: ART - 168}}>
                <Notes
                  theme={theme}
                  travelled={POSE.travelled}
                  amplitude={POSE.amplitude}
                  seed={theme.id}
                  count={5}
                />
              </div>
            )}
          </AbsoluteFill>
        )}
      </div>

      {/* ⚠️ The title, the rule, and the caption — the three things read in a thumbnail's first second, stacked in
          one column so nothing has to be hunted for. */}
      <div
        style={{
          position: 'absolute',
          left: MARGIN + ART + 64,
          right: MARGIN,
          top: 0,
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
        }}
      >
        {/* ⚠️ The reel's own leading (`SongReel.tsx`), not a tighter one: Bengali sets matras above *and* below the
            baseline, so a two-line title needs the room Latin would not ask for. */}
        <div style={{fontSize: 92, fontWeight: 700, lineHeight: 1.15, letterSpacing: '-0.01em'}}>{title}</div>
        {/* The rule: the theme's own glow, and the only ornament in the composition. */}
        <div style={{width: 104, height: 6, borderRadius: 3, background: accent.tint, margin: '30px 0 22px'}} />
        {/* ⚠️ A caption in Bengali cannot be upper-cased — the script has no case — so it is letter-spaced instead.
            ⚠️ And its digits are the script's own (`৪:০০`), which is why the value is not formatted here. */}
        <div style={{fontSize: 32, fontWeight: 500, letterSpacing: '0.06em', opacity: 0.88}}>{caption}</div>
      </div>

      {/* ⚠️ **The operator's mark, drawn raw — no chip, no box.** Their instruction, and it is a real trade: the
          chip exists so that *any* mark reads on *any* field, and dropping it means a mark whose ink matches a
          theme's field will read weakly — the answer to which is another theme, not a box that at thumbnail size
          reads as a sticker stuck on the artwork. The shadow is what keeps a mid-tone mark off the background. */}
      {mark ? (
        <Img
          src={mark.src}
          style={{
            position: 'absolute',
            left: MARGIN,
            top: MARGIN,
            height: MARK,
            display: 'block',
            filter: 'drop-shadow(0 16px 38px rgba(0, 0, 0, 0.5))',
          }}
        />
      ) : null}
    </AbsoluteFill>
  );
};
