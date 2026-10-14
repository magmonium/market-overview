/**
 * The envelope — **the only clock the picture has.** (ADR 0006)
 *
 * There is no beat grid here and no onset detection. The song's own amplitude *is* the timeline, reduced to
 * **one amplitude per frame**, so `envelope[frame]` is a lookup: no interpolation at draw time, no smoothing
 * against a wall clock, nothing that can drift between a render and its re-render.
 *
 * ⚠️ **The peak of a frame's window, never its mean.** A visualiser that averages flattens precisely the
 * transients the eye is following, and "matching the music" is mostly those. Any smoothing the design wants
 * belongs to a **theme** — taste may vary per theme, the clock may not.
 *
 * ⚠️ **The length is this side's copy of a rule the Python side also owns** (`master.frames`): a length that is
 * already a whole number of frames must not gain one to float noise, so the product is rounded to microseconds
 * before the ceiling. If the two sides ever disagree, the video and its envelope differ in length by a frame —
 * a silent drift with no error anywhere.
 */

/** One amplitude per frame, in playing order. Values are absolute, in `[0, 1]`. */
export type Envelope = number[];

//: The mirror of `master.MICROSECONDS` (6 decimal places). Named for what it does, not for what it holds.
const MICROSECOND_SCALE = 1e6;

/** How many frames this much audio occupies at `fps` — rounded up, immune to float noise. */
const framesFor = (samples: number, sampleRate: number, fps: number): number =>
  Math.ceil(Math.round((samples / sampleRate) * fps * MICROSECOND_SCALE) / MICROSECOND_SCALE);

/**
 * The loudest absolute sample in `[from, to)`, or `0` for a window with no samples in it.
 *
 * `0` rather than an exception, because a window past the end of the audio is a frame of silence — the last
 * frames of a master that decoded a hair shorter than its own duration.
 */
export const peakOf = (channel: ArrayLike<number>, from: number, to: number): number => {
  let peak = 0;
  for (let index = Math.max(0, from); index < Math.min(channel.length, to); index += 1) {
    peak = Math.max(peak, Math.abs(channel[index]));
  }
  return peak;
};

/**
 * Reduce a decoded channel to one amplitude per frame.
 *
 * @param channel raw amplitudes, as the renderer's audio API hands them over
 * @param sampleRate the rate `channel` is sampled at, which is the file's — not the frame rate
 * @param fps the render's frame rate, which is what the envelope is quantised to
 */
export const sampleEnvelope = (
  channel: ArrayLike<number>,
  {sampleRate, fps}: {readonly sampleRate: number; readonly fps: number},
): Envelope => {
  const frames = framesFor(channel.length, sampleRate, fps);
  const envelope: Envelope = [];

  for (let frame = 0; frame < frames; frame += 1) {
    const from = Math.round((frame * sampleRate) / fps);
    // ⚠️ At least one sample wide: a sample rate below the frame rate would otherwise leave empty windows and
    // an envelope of zeroes, which looks like a broken render rather than a coarse one.
    const to = Math.max(Math.round(((frame + 1) * sampleRate) / fps), from + 1);
    envelope.push(peakOf(channel, from, to));
  }

  return envelope;
};

/**
 * Scale an envelope so the song's loudest frame reaches 1 — **the song's own shape, at full height.**
 *
 * ⚠️ **Why this exists.** A master sits at whatever level the artist left it at, and this pipeline never touches
 * the audio ([the master is never touched](issues/09-the-master-is-never-touched.md)). Unnormalised, a
 * quietly-mastered song would draw a timid little wave in the middle of a large empty frame — the picture
 * reporting the *mastering* rather than the *performance*. Dividing by the song's own peak removes the level
 * and keeps the shape, which is the entire claim of the design: **the song's own shape is the narrative.**
 *
 * ⚠️ **Peak, not RMS.** The loudest moment of the song is what has to reach the edge of the frame. An RMS scale
 * would make the picture depend on how densely the loud passages are packed rather than on the song's own
 * dynamic range.
 *
 * ⚠️ **A silent song stays flat, because `0 / 0` is `NaN`** — and a `NaN` in a path's coordinates draws
 * *nothing at all*, so the wave would vanish with no error anywhere. Silence is returned as silence.
 *
 * Always returns a fresh array, so a caller can scale or clip it without touching the clock.
 */
export const normaliseEnvelope = (envelope: readonly number[]): Envelope => {
  const peak = peakOf(envelope, 0, envelope.length);

  if (peak === 0) {
    return [...envelope];
  }
  return envelope.map((amplitude) => amplitude / peak);
};

/**
 * What this module needs from the renderer's audio analysis — **structural**, so the arithmetic can be tested
 * with no browser and no Remotion in the room.
 *
 * ⚠️ **The field names are Remotion's** (`channelWaveforms`, plural, of `Float32Array`), because the object this
 * receives is the one its hook returns. A wrong name here does not throw — it produces an envelope of silence,
 * which is the failure mode this pipeline is built to refuse.
 */
export type DecodedAudio = {
  readonly channelWaveforms: readonly Float32Array[];
  readonly sampleRate: number;
};

/**
 * The decoded song, reduced to **the clock** — the whole reason the renderer analyses its own audio.
 *
 * ⚠️ **One pass, no large intermediate array.** The obvious implementation mixes the channels into a
 * per-sample array first; a four-minute stereo master is eleven million samples, and materialising that as a
 * JavaScript number array costs tens of megabytes for a result nine thousand numbers long. So the peak across
 * channels is taken **inside** each frame's window, where the window is the only thing that needs the samples.
 *
 * ⚠️ **The rate is the decoder's, not the master's.** Remotion's decoder runs at a pinned rate, so the frame
 * windows come out identical on every machine whatever the master was recorded at. That is a determinism the
 * product needs and, unusually, did not have to arrange for itself.
 *
 * ⚠️ **Normalised here, not by the caller.** "The song's own shape at full height" is part of what the clock
 * *is*; a caller who forgot it would ship a timid wave in the middle of a large empty frame.
 */
export const envelopeFromAudio = (
  audio: DecodedAudio,
  {fps}: {readonly fps: number},
): Envelope => {
  const {channelWaveforms, sampleRate} = audio;
  const samples = channelWaveforms[0]?.length ?? 0;
  const frames = framesFor(samples, sampleRate, fps);
  const envelope: Envelope = [];

  for (let frame = 0; frame < frames; frame += 1) {
    const from = Math.round((frame * sampleRate) / fps);
    const to = Math.max(Math.round(((frame + 1) * sampleRate) / fps), from + 1);

    let peak = 0;
    for (const channel of channelWaveforms) {
      peak = Math.max(peak, peakOf(channel, from, to));
    }
    envelope.push(peak);
  }

  return normaliseEnvelope(envelope);
};
