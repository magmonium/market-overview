import {Composition} from 'remotion';
import {BooksBrief} from './BooksBrief.tsx';
import {BooksThumbnail} from './BooksThumbnail.tsx';
import {bundleUrl, chartFor} from './facts.ts';
import type {BooksBriefProps} from './props.ts';

/**
 * ⚠️ **Valid before a bundle exists**, so the composition can be listed — and so a missing props file fails on the
 * render's own terms rather than as an import error. The brief's own `Root.tsx` keeps an `EMPTY` for the same reason.
 *
 * ⚠️ `week: ''` rather than a real one: a default that *looked* like a week would render a real chart's data under a
 * wrong key, where an empty one fails at the fetch. A default should be obviously wrong rather than plausible.
 */
const EMPTY: BooksBriefProps = {chart: 'bengali', week: ''};

export const RemotionRoot = () => (
  <>
    {/* ⚠️ **The length is the chart's own, fetched rather than declared.** `calculateMetadata` is async, so it reads the
        staged bundle and hands back `timeline.total_frames` — which is why this layer holds no dwell table at all. A
        hard-coded `durationInFrames` would be a second opinion about how long the run is, and the one that fell behind
        would truncate the outro. */}
    <Composition
      id="BooksBrief"
      component={BooksBrief}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={EMPTY}
      calculateMetadata={async ({props}) => {
        const response = await fetch(bundleUrl(props.week));
        if (!response.ok) {
          throw new Error(`${props.week}: the snapshot could not be read (${response.status})`);
        }
        const bundle = await response.json();
        const facts = chartFor(bundle, props.chart);
        return {
          durationInFrames: Math.max(1, facts.timeline.total_frames),
          fps: facts.timeline.fps,
          width: 1920,
          height: 1080,
        };
      }}
    />

    {/* ⚠️ **1280×720 and one frame long** — YouTube's still size, and `--frame=0` is the whole of it (ticket 16). */}
    <Composition
      id="BooksThumbnail"
      component={BooksThumbnail}
      fps={30}
      width={1280}
      height={720}
      durationInFrames={1}
      defaultProps={EMPTY}
    />
  </>
);
