import {AbsoluteFill} from 'remotion';
import {ThumbnailMark, type Mark} from './Brand';
import {copy} from './Furniture';
import {headline} from './headline';
import type {FactsBundle} from './bundle';
import type {Language} from './copy';
import {BG, FONT, INK, MUTED, SCRIM_STILL, percent, tone} from './theme';
import {World} from './world/World';
import {THUMBNAIL} from './world/stations';

/**
 * The thumbnail still. (0085_12)
 *
 * Issue 14: a **dedicated composition, never a frame grabbed from the video.** A grabbed frame is composed for
 * motion — the camera is mid-move because the move reads well in motion — and it may be caught half-settled, which
 * is exactly the arbitrary outcome this pipeline exists to avoid. This composition reuses the video's *world*
 * (palette, lighting rig, primitives, at 0085_09's cost of nothing) so the still is unmistakably the same product,
 * while its own camera station is at rest and its own layout is composed for one frame.
 *
 * **What it shows is the same figure the video opens on** — `headline()`, the day's largest absolute index move —
 * because issue 13's rule is one bundle, three surfaces: video, thumbnail and metadata cannot disagree about the
 * day's number, and the thumbnail promising something the video does not lead with would be the product
 * contradicting itself.
 *
 * ## The text is one word and one number, and that is the whole text budget
 *
 * Issue 14 allows 3-6 words and one idea. The idea here is *"this index moved this much"*: a bare `−0.70%` does not
 * say **what** fell, and naming it is the minimum that makes the figure mean anything, so the label earns its place
 * and nothing else does.
 *
 * ⚠️ **The date is deliberately absent, because it fails the ticket's own test.** A date large enough to be part of
 * the design would read at ~6 px at the 210 px a feed shows this at — dead weight that costs frame space. Issue 14
 * offers "the series name *or* the date", and the answer here is **neither**: the mark is the series identity, and
 * issue 21 sizes it at 128 px precisely so that it still reads at feed scale. Text that cannot survive the shrink
 * test has no claim on the frame.
 *
 * ## The reserved regions
 *
 * YouTube covers the **bottom-right** (duration badge) and the **bottom strip** (progress bar). So the figure sits
 * upper-centre — `paddingBottom` lifts it clear of the strip — and the mark stays in the top-right corner, at issue
 * 21's still size rather than the video's.
 */
export type ThumbnailProps = {bundle: FactsBundle; lang: Language; webgl?: boolean; mark?: Mark | null};

export const Thumbnail = ({bundle, webgl = true, mark = null}: ThumbnailProps) => {
  const featured = headline(bundle.indexes);
  return (
    <AbsoluteFill style={{background: BG, color: INK, fontFamily: FONT}}>
      {/* ⚠️ The same world, from a station that is not on the video's rail. `webgl` is a prop here for 0085_09's
          reason: on a machine that cannot do WebGL the still degrades to type over a flat field — a plainer
          thumbnail, not a missing one. */}
      {webgl ? <World bundle={bundle} station={THUMBNAIL} /> : null}

      {/* ⚠️ `SCRIM_STILL`, not `SCRIM_OPEN` — see the note on it in theme.ts. The card scrims are built to bury the
          world behind text; a thumbnail that buries it loses the day's terrain, which is where its variety lives. */}
      <AbsoluteFill style={{background: SCRIM_STILL}} />

      <AbsoluteFill
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          // ⚠️ **Anchored to the top, not centred — the third render is what settled it.** Centred, the 280 px number
          // sat exactly on top of the columns and hid them: seven bars flattened to a sliver of one, peeking through
          // the gap between the `−` and the `0` like a rendering fault. The video already had the answer and I had
          // ignored it — issue 12 gives the world the **lower band** and nothing else competes for it. So the figure
          // takes the upper frame and the world is left the strip below it, which is the same division of the frame
          // the cards use.
          justifyContent: 'flex-start',
          paddingTop: 48,
        }}
      >
        <div style={{fontSize: 88, color: MUTED, marginBottom: 10, textAlign: 'center'}}>
          {featured ? (copy.indexes[featured.labelKey] ?? featured.labelKey) : '—'}
        </div>
        <div
          style={{
            // ⚠️ The largest element in the frame, as issue 14 requires: identifiable from its shape alone at feed
            // scale. 200 px renders at ~33 px at the 210 px a feed shows it at — not merely legible, unmistakable.
            // Bengali and English share this line: it is numerals, so it never needs translating.
            //
            // ⚠️ **200, not 240, and the size is a composition decision rather than a taste one.** At 240 the number's
            // descenders reached down into the world's band and the columns ran up behind the digits, which read as a
            // rectangle glitching out from behind them. Sizing the figure to *end above the world* is what makes the
            // lower third a clean band. The hierarchy issue 14 asks for survives easily — the figure is still twice
            // the label and four times anything else in the frame.
            fontSize: 200,
            fontWeight: 700,
            lineHeight: 1,
            color: tone(featured?.change ?? null),
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          {percent(featured?.change ?? null)}
        </div>
      </AbsoluteFill>

      <ThumbnailMark mark={mark} />
    </AbsoluteFill>
  );
};
