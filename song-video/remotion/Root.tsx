import {Composition} from 'remotion';
import {SongReel} from './SongReel.tsx';
import {SongReelThumbnail} from './SongReelThumbnail.tsx';
import type {SongReelProps} from './props.ts';

/**
 * ⚠️ **Valid before props arrive**, so the composition can be listed — and so a missing props file fails on
 * the render's own terms rather than as an import error.
 */
const EMPTY: SongReelProps = {
  title: '',
  song: '',
  theme: 'vinyl',
  cover: null,
  frames: 1,
  mark: null,
  seed: '',
  lang: 'bn',
  duration: '',
};

export const RemotionRoot = () => (
  <>
    {/* ⚠️ **The length is derived from the master's own measurement, not from the audio decoded here.** It is
        `master.frames` over the ffprobe duration — Python's tested rule — so the piece is exactly as long as
        the song, and this side does not get a second opinion about it. */}
    <Composition
      id="SongReel"
      component={SongReel}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={EMPTY}
      calculateMetadata={({props}) => ({
        durationInFrames: Math.max(1, props.frames),
        fps: 30,
        width: 1920,
        height: 1080,
      })}
    />

    {/* ⚠️ **The still's own composition** (issue 08), at the size YouTube asks for and one frame long — so
        `--frame=0` is the whole of it. Its props are the reel's, because a render is given one props file and
        the still simply ignores `song` and `frames`: it has no clock, so it has nothing to measure. */}
    <Composition
      id="SongReelThumbnail"
      component={SongReelThumbnail}
      fps={30}
      width={1280}
      height={720}
      durationInFrames={1}
      defaultProps={EMPTY}
    />
  </>
);
