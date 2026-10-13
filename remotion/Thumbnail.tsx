import {AbsoluteFill} from 'remotion';
import {Backdrop} from './Backdrop';
import {ThumbnailMark, type Mark} from './Brand';
import {copy} from './Furniture';
import {Typeface} from './fonts';
import {headline} from './headline';
import {longDate} from './dates';
import type {FactsBundle} from './bundle';
import type {Language} from './copy';
import {BG, FONT, INK, MUTED, SCRIM_STILL, percent, tone} from './theme';

/**
 * The thumbnail still. (0085_12)
 *
 * Issue 14: a **dedicated composition, never a frame grabbed from the video.** A grabbed frame is composed for
 * motion — the backdrop is drifting because the drift reads well in motion — and it may be caught half-settled,
 * which is exactly the arbitrary outcome this pipeline exists to avoid. This composition reuses the video's own
 * *backdrop* (`Backdrop.tsx`), rendered at frame 0 where every drift term is zero, so the still is unmistakably
 * the same product while its own layout is composed for one frame.
 *
 * **What it shows is the same figure the video opens on** — `headline()`, the day's Nifty 50 move — because issue 13's
 * rule is one bundle, three surfaces: video, thumbnail and metadata cannot disagree about the day's number, and the
 * thumbnail promising something the video does not lead with would be the product contradicting itself.
 *
 * ## The text: what moved, by how much, and on what day
 *
 * Issue 14 allows 3-6 words and one idea, and the idea here is the three things a viewer needs before deciding to
 * watch: **what** moved (`Nifty 50`), **by how much** (the figure), and **when** (the date). A bare `−0.70%` says
 * none of the three, so the label and the date each earn their place and nothing else does.
 *
 * ⚠️ **The date was deliberately absent until it was asked for, and the argument against it is kept on the record.**
 * At the 210 px a feed shows this at, a line sized to be part of the design reads at a few px — which is exactly why
 * issue 21 sizes the mark at 128 px, so that the one thing that *must* survive the shrink does. The date is here
 * **by decision, not drift**: it is set at the smallest size that still reads at feed scale and sits below the
 * figure, where the composition's own hierarchy keeps the number dominant.
 *
 * ## The reserved regions
 *
 * YouTube covers the **bottom-right** (duration badge) and the **bottom strip** (progress bar). So the figure sits
 * upper-centre — `paddingBottom` lifts it clear of the strip — and the mark stays in the top-right corner, at issue
 * 21's still size rather than the video's.
 */
export type ThumbnailProps = {bundle: FactsBundle; lang: Language; backdrop?: boolean; mark?: Mark | null};

export const Thumbnail = ({bundle, backdrop = true, mark = null}: ThumbnailProps) => {
  const featured = headline(bundle.indexes);
  return (
    <AbsoluteFill style={{background: BG, color: INK, fontFamily: FONT}}>
      {/* ⚠️ The still is a *static* composition, so a fallback face would be frozen into the one artefact that
          outlives the video. The wait matters here at least as much as it does in the brief. */}
      <Typeface />
      {/* ⚠️ The same backdrop the video uses, at frame 0 — so the still is the settled field rather than a
          snapshot of it mid-move. `backdrop` is a prop for the same reason the video's is: on a machine where the
          layer misbehaves the still degrades to type over a flat field — a plainer thumbnail, not a missing one. */}
      {backdrop ? <Backdrop bundle={bundle} /> : null}

      {/* ⚠️ `SCRIM_STILL`, not `SCRIM_OPEN` — see the note on it in theme.ts. The card scrims are built to bury the
          world behind text; a thumbnail that buries it loses the day's terrain, which is where its variety lives. */}
      <AbsoluteFill style={{background: SCRIM_STILL}} />

      <AbsoluteFill
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          // ⚠️ **Anchored to the top, not centred — the third render is what settled it.** Centred, the 280 px number
          // sat exactly on top of the backdrop and hid it: the field flattened to a sliver of one lobe, peeking
          // through the gap between the `−` and the `0` like a rendering fault. The video already had the answer and
          // I had ignored it — issue 12 gives the backdrop the **lower band** and nothing else competes for it. So
          // the figure takes the upper frame and the backdrop is left the strip below it, which is the same division
          // of the frame the cards use.
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
            // descenders reached down into the backdrop's band and the field ran up behind the digits, which read as
            // a rectangle glitching out from behind them. Sizing the figure to *end above the backdrop* is what makes
            // the lower third a clean band. The hierarchy issue 14 asks for survives easily — the figure is still
            // twice the label and four times anything else in the frame.
            fontSize: 200,
            fontWeight: 700,
            lineHeight: 1,
            color: tone(featured?.change ?? null),
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          {percent(featured?.change ?? null)}
        </div>
        {/* ⚠️ The day, spelled out. `dates.ts` holds why the *order* lives in the label table and why the parse is
            UTC; here it is only a muted line under the figure, so the number keeps the hierarchy issue 14 asks for. */}
        <div style={{fontSize: 34, color: MUTED, marginTop: 12, textAlign: 'center'}}>
          {longDate(bundle.meta.date, copy.dates)}
        </div>
      </AbsoluteFill>

      <ThumbnailMark mark={mark} />
    </AbsoluteFill>
  );
};
