import {AbsoluteFill} from 'remotion';
import {Typeface} from '../../../remotion/fonts.ts';
import {Collage} from './Collage.tsx';
import {Mark as MarkPlate} from './Mark.tsx';
import {tableFor} from './copy.ts';
import {chartFor, useBundle, useMark} from './facts.ts';
import {isoMondayLabel} from './format.ts';
import {BG} from './palette.ts';
import type {BooksBriefProps} from './props.ts';

/**
 * **`BooksThumbnail` — the still that travels with one chart's video** (ticket 16).
 *
 * ⚠️ **A dedicated composition, never a frame grabbed from the video.** A grabbed frame is composed for *motion* — it
 * may be caught half-settled, and the entrance means the first frames are a fade — so the still has its own camera with
 * no entrance at all, which is what makes `--frame=0` **the settled state** rather than a frame chosen to be past one.
 *
 * ⚠️ **Four thumbnails, no master.** A thumbnail fronts the video it belongs to, and *"a week thumbnail would front
 * nothing"* (tickets 13, 16) — so this composition takes the same `{chart, week}` props the video does, and each
 * chart's collage rides with that chart's package.
 *
 * ⚠️ **Its props are the video's, because a render is given one props file** — the still simply ignores the timeline,
 * having no clock. That is the reel's own arrangement, kept for the same reason.
 */
export const BooksThumbnail = ({chart, week}: BooksBriefProps) => {
  const bundle = useBundle(week);
  const mark = useMark();

  // ⚠️ The font wait matters here **more** than in the video, not less: a still is the one artefact that outlives the
  // run, so a fallback face would be frozen into it permanently.
  if (!bundle) {
    return (
      <AbsoluteFill style={{background: BG}}>
        <Typeface />
      </AbsoluteFill>
    );
  }

  const facts = chartFor(bundle, chart);

  return (
    <AbsoluteFill style={{background: BG}}>
      <Typeface />
      {/* ⚠️ The date comes off the **week key**, never a clock — see `isoMondayLabel`. A still whose date was *when it
          was rendered* would disagree with the video beside it the moment either was re-run. */}
      <Collage facts={facts} copy={tableFor(facts.language)} week={week} published={isoMondayLabel(week)} />
      <MarkPlate mark={mark} />
    </AbsoluteFill>
  );
};
