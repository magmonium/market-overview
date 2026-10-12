import {Composition} from 'remotion';
import {IndexCard} from './IndexCard';
import {MarketBrief, type MarketBriefProps, metadata} from './MarketBrief';
import {Thumbnail, type ThumbnailProps} from './Thumbnail';
import type {FactsBundle} from './bundle';

/**
 * Empty props, so the compositions are valid before a bundle exists. `--props=<file>` replaces this at
 * render time — which is how a re-render from `store/<date>/` is guaranteed to match (ADR 0003).
 */
const EMPTY: FactsBundle = {
  meta: {schema: 1, date: '', source: ''},
  indexes: [],
  timeline: {
    fps: 30,
    build_seconds: 175,
    cap_seconds: 180,
    total_frames: 0,
    blocks: [],
  },
};

export const RemotionRoot = () => {
  return (
    <>
      {/* The brief itself. Its length and frame rate are read from the bundle (see metadata). The
          language rides beside the bundle, never inside it. */}
      <Composition
        id="MarketBrief"
        component={MarketBrief}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{bundle: EMPTY, lang: 'bn'} as MarketBriefProps}
        calculateMetadata={metadata}
      />

      {/* 0085_12 — the still, as its own composition at the still's own size. ⚠️ **One frame**, and rendered
          with `remotion still --frame=0`: the animated backdrop's drift terms are all zero at frame 0 (see
          `Backdrop.tsx`), so any frame is the settled one and the still cannot be caught mid-move. 1280×720 is
          YouTube's. */}
      <Composition
        id="Thumbnail"
        component={Thumbnail}
        durationInFrames={1}
        fps={30}
        width={1280}
        height={720}
        defaultProps={{bundle: EMPTY, lang: 'bn'} as ThumbnailProps}
      />

      {/* 0085_02's walking skeleton, kept as a smoke test: one card, no timeline, trivially fast to
          render — which makes it the right thing to reach for when something larger breaks. */}
      <Composition
        id="IndexCard"
        component={IndexCard}
        durationInFrames={180}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={EMPTY}
      />
    </>
  );
};

