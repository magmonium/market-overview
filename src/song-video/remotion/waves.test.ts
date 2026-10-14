/**
 * 0087_07 — `bars`: the whole song as a landscape, and the playhead that traverses it.
 *
 * ⚠️ **Two properties, each answering a different failure.**
 *
 * The landscape is **frame-independent** — it is the whole song's shape, reduced once — so the composition can
 * memoise it instead of re-reducing a nine-thousand-frame envelope on every frame. It also means the viewer can
 * see where the song is going, which is the *"the song's own shape is the narrative"* claim made visible rather
 * than asserted.
 *
 * The playhead is the **traversal**: ticket 11's rule that the wave must *pass*. Height alone is not enough —
 * a visualiser that pulses in place without travelling is precisely the screensaver the map exists to avoid.
 */
import assert from 'node:assert/strict';
import {test} from 'node:test';

import {normaliseEnvelope, sampleEnvelope} from './envelope.ts';
import {bars, playhead, ripple, smoothed} from './waves.ts';

test('the bars are the whole song, laid out once and read by every frame', () => {
  // Four frames of song, reduced to two columns: the peak of [0,1] and the peak of [2,3].
  const envelope = [0.1, 0.9, 0.2, 0.4];

  const bands = bars(envelope, {columns: 2});

  assert.deepEqual(bands, [
    {at: 0.25, height: 0.9},
    {at: 0.75, height: 0.4},
  ]);
});

test('the playhead starts at the near edge, ends at the far one, and never goes backwards', () => {
  const frames = 100;
  const positions = Array.from({length: frames}, (_, frame) => playhead(frame, frames));

  assert.equal(positions[0], 0, 'the first frame is the near edge');
  assert.equal(positions[frames - 1], 1, 'the last frame is the far edge, exactly');
  assert.deepEqual(positions, [...positions].sort((a, b) => a - b), 'the traversal is monotonic');

  // ⚠️ A one-frame piece — which is what the *still* is — has nowhere to travel, and `0 / 0` would erase the
  // wave as a NaN rather than leaving it at the near edge.
  assert.equal(playhead(0, 1), 0);
});

test('the bloom is a ripple: the newest ring is innermost and the oldest has travelled out', () => {
  // ⚠️ `bloom` is the one form that is **not** a coordinate transform of the profile. Everything else draws the
  // whole song at once; this draws a *history* — the newest ring at the centre, older rings expanding outward —
  // which is why it is the only form that needs the frame as well as the envelope.
  const envelope = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8];

  const rings = ripple(envelope, 6, {ringCount: 4, stride: 2});

  assert.deepEqual(rings, [
    {radius: 0.25, strength: 0.7},
    {radius: 0.5, strength: 0.5},
    {radius: 0.75, strength: 0.3},
    {radius: 1, strength: 0.1},
  ]);

  // ⚠️ Before the song there is **silence, not a wrap-around**: a ring reaching back past frame 0 must never
  // borrow the song's ending, which would put the loudest moment of the piece in its opening frames.
  assert.deepEqual(ripple(envelope, 1, {ringCount: 3, stride: 2}), [
    {radius: 1 / 3, strength: 0.2},
    {radius: 2 / 3, strength: 0},
    {radius: 1, strength: 0},
  ]);
});

/**
 * A tone built from known movements — no file, no decoder, and **exact**.
 *
 * ⚠️ The frequency is a quarter of the sample rate, so the samples land on `0, ±1, 0, ∓1` and every peak is
 * exactly the movement's amplitude. A fixture that introduced rounding of its own could make the pipeline look
 * right (or wrong) for a reason that has nothing to do with the pipeline.
 */
const buildTone = (
  movements: readonly {readonly seconds: number; readonly amplitude: number}[],
  sampleRate: number,
): Float32Array => {
  const samples = new Float32Array(
    Math.round(movements.reduce((total, movement) => total + movement.seconds, 0) * sampleRate),
  );
  let at = 0;

  for (const movement of movements) {
    for (let index = 0; index < Math.round(movement.seconds * sampleRate) && at < samples.length; index += 1) {
      samples[at] = Math.sin((Math.PI / 2) * at) * movement.amplitude;
      at += 1;
    }
  }

  return samples;
};

test('the landscape follows the song: quiet, loud and mid come out at three different heights', () => {
  // ⚠️ **This is the test the product needs and a still cannot give.** "Does the wave match the music?" cannot be
  // answered by looking at a picture of a song nobody measured — so the song here is three movements whose
  // amplitudes are known to the digit, and the assertion is that the landscape's shape *is* those movements.
  const sampleRate = 8000;
  const tone = buildTone(
    [
      {seconds: 2, amplitude: 0.1},
      {seconds: 2, amplitude: 0.9},
      {seconds: 2, amplitude: 0.5},
    ],
    sampleRate,
  );

  const envelope = sampleEnvelope(tone, {sampleRate, fps: 10});
  assert.equal(envelope.length, 60, 'six seconds at ten frames a second');

  const landscape = bars(normaliseEnvelope(envelope), {columns: 3});

  // One column per movement: a tenth of the peak, then the peak, then five ninths of it. Rounded to three
  // places because a tenth of nine tenths is not a binary fraction, and the *shape* is what is being asserted.
  assert.deepEqual(
    landscape.map((band) => Math.round(band.height * 1000) / 1000),
    [0.111, 1, 0.556],
  );
});

test('the settle averages the frames around one, never the ones after it', () => {
  // ⚠️ A one-sided filter would make the picture *anticipate* the music, which an audience cannot name and can feel.
  const spike = [0, 0, 1, 0, 0];

  assert.deepEqual(smoothed(spike, {window: 3}), [0, 1 / 3, 1 / 3, 1 / 3, 0]);
});

test('a transient becomes a swell: it survives, but not as tall as it was', () => {
  const once = [0, 0, 0, 1, 0, 0, 0];

  const settled = smoothed(once, {window: 5});

  assert.ok(Math.max(...settled) < 1, 'spread rather than repeated — the whole point of settling');
  assert.ok(Math.max(...settled) > 0.15, '…but not erased: this is a filter, not a mute');
  assert.equal(settled.length, once.length, 'one value per frame, exactly like the clock');
});

test('the window shrinks at the ends rather than wrapping', () => {
  // ⚠️ The wrap in `backdrop.ts` once teleported a pool of light across the frame, so the middle of this one has to
  // stay **empty**: an edge that borrowed the song's other end would light it up.
  const ends = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1];

  const settled = smoothed(ends, {window: 5});

  assert.equal(settled[5], 0, 'the middle borrows from neither end');
  assert.ok(settled[0] > 0, 'the opening still leans on the opening');
  assert.ok(settled[11] > 0, 'and the close on the close');
});

test('a quiet song stays quiet, and a window of one is the envelope itself', () => {
  assert.deepEqual(smoothed([0.5, 0.5, 0.5], {window: 7}), [0.5, 0.5, 0.5], 'settling must not invent loudness');
  assert.deepEqual(smoothed([0.2, 0.9, 0.4], {window: 1}), [0.2, 0.9, 0.4], '…and `1` is the clock, untouched');
});

test('a theme that settles more moves less — one song, two tastes', () => {
  const once = [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0];

  const punchy = Math.max(...smoothed(once, {window: 3}));
  const calm = Math.max(...smoothed(once, {window: 15}));

  assert.ok(punchy > calm, 'neon flickers where aurora breathes');
});
