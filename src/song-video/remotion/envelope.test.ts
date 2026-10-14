/**
 * 0087_06 — the envelope: **one amplitude per frame**. (ADR 0006)
 *
 * ⚠️ **This is the clock.** There is no beat grid and no onset detection: the picture *is* the song's
 * amplitude, sampled on the clock the frames are already on. Two properties turn that from a sentence in a
 * document into a fact, and both are asserted here — **one amplitude per frame**, so frame → envelope is a
 * pure lookup rather than an interpolation, and **the partial tail still gets its frame**, so the envelope is
 * exactly as long as the piece and no longer.
 *
 * ⚠️ And one trap, carried across the runtime boundary on purpose. `1.1 s × 30` is `33.000000000000004`, so a
 * naive ceiling buys the piece a frame nobody asked for. Python applies the same microsecond rounding before
 * its own ceiling (`master.frames`), because the two sides must agree about how long the piece is — this test
 * pins the same answer from this side of the boundary.
 */
import assert from 'node:assert/strict';
import {test} from 'node:test';

import {envelopeFromAudio, normaliseEnvelope, sampleEnvelope} from './envelope.ts';

test('one peak per frame, and the partial tail still gets its frame', () => {
  // 8 samples at 8 Hz: one second, four frames of two samples each.
  const channel = [0.1, 0.9, 0.2, 0.4, 0.3, 0.7, 0.5, 0.6];

  const envelope = sampleEnvelope(channel, {sampleRate: 8, fps: 4});

  assert.equal(envelope.length, 4);
  assert.deepEqual(envelope, [0.9, 0.4, 0.7, 0.6]);
});

test('a length that is already a whole number of frames does not gain one to float noise', () => {
  const channel = new Array(11000).fill(0.5);

  const envelope = sampleEnvelope(channel, {sampleRate: 10000, fps: 30});

  assert.equal(envelope.length, 33, 'ceil(1.1 × 30) is 33, not 34');
});

test('a quietly-mastered song fills the frame exactly as a loud one does', () => {
  // ⚠️ Amplitudes chosen as exact binary fractions, so this asserts the *rule* rather than a float tolerance:
  // 0.8 / 10 is not 0.08 in binary, and a comparison that needed a tolerance would be hiding that.
  const shape = [0.125, 1, 0.25, 0.5];
  const quieter = shape.map((value) => value / 8);

  const loud = normaliseEnvelope(shape);
  const quiet = normaliseEnvelope(quieter);

  assert.deepEqual(quiet, loud, 'the same performance at a lower level is the same picture');
  assert.equal(Math.max(...loud), 1, 'the loudest moment reaches the edge of the frame');
});

test('a silent song stays flat instead of turning into NaN', () => {
  const envelope = normaliseEnvelope([0, 0, 0, 0]);

  // ⚠️ The trap is silent: `0 / 0` is NaN, and a NaN in a path's coordinates draws *nothing* — the wave simply
  // disappears from the frame with no error anywhere.
  assert.deepEqual(envelope, [0, 0, 0, 0]);
  assert.ok(
    envelope.every((value) => Number.isFinite(value)),
    'every amplitude must be a number, not a NaN',
  );
});

test('the decoded audio becomes the clock, and both channels are heard', () => {
  // ⚠️ `Float32Array`, exactly as the renderer's own audio API hands it over — not a plain array, which is the
  // difference a `readonly number[]` signature could not survive.
  //
  // ⚠️ And dyadic amplitudes throughout, so all three steps — the peak across channels, the reduction to frames,
  // and the normalisation — are exact. A comparison that needed a tolerance would be hiding which of the three
  // the tolerance was covering up.
  const audio = {
    sampleRate: 8,
    channelWaveforms: [
      Float32Array.from([0.5, 1, 0.25, 0.75]),
      Float32Array.from([0.25, 0.5, 0.5, 0.125]),
    ],
  };

  const envelope = envelopeFromAudio(audio, {fps: 4});

  assert.deepEqual(envelope, [1, 0.75]);
});
