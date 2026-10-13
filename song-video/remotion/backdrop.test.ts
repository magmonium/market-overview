/**
 * 0087_12 — the light: **a slow arc that is also the amplitude's own breath.**
 *
 * ⚠️ Ticket 11 asks that a theme's grammar have its own slow arc, and this is where that rule is checked instead of
 * admired: nothing rests, nothing travels far, and no value that reaches a style is ever `NaN` — the one failure
 * that would erase the layer with nothing anywhere to explain it.
 */
import assert from 'node:assert/strict';
import {test} from 'node:test';

import {blobs} from './backdrop.ts';

const DIGEST = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855';

const at = (travelled: number, amplitude = 0, seed = DIGEST) => blobs(travelled, amplitude, {count: 3, seed});

test('nothing in the field rests, and nothing takes a lap of the frame', () => {
  const first = at(0);
  const later = at(0.5);

  for (const [index, blob] of first.entries()) {
    const moved = Math.abs(blob.x - later[index].x) + Math.abs(blob.y - later[index].y);

    assert.ok(moved > 0, `blob ${index} did not move — a resting field is a screensaver`);
    assert.ok(moved < 0.5, `blob ${index} moved ${moved.toFixed(3)} of the frame — that is weather, not light`);
  }
});

test('a loud moment widens the light', () => {
  // ⚠️ Scale is this reel's metaphor for loudness — the disc breathes, the pulse widens — and a brightness that
  // tracked the music would read as a fault in the encode rather than as the song.
  const quiet = at(0.4, 0);
  const loud = at(0.4, 1);

  for (const [index, blob] of quiet.entries()) {
    assert.ok(loud[index].radius > blob.radius, `blob ${index} did not widen on a loud moment`);
    assert.ok(loud[index].strength >= blob.strength, `blob ${index} dimmed on a loud moment`);
  }
});

test('every value is finite and in range, and the same props paint the same frame', () => {
  for (const travelled of [0, 0.25, 0.5, 0.75, 1]) {
    for (const blob of at(travelled, 0.9)) {
      for (const value of [blob.x, blob.y, blob.radius, blob.strength]) {
        assert.ok(Number.isFinite(value), `a NaN in a style erases the layer silently — got ${value}`);
        assert.ok(value >= 0 && value <= 1.2, `a blob coordinate outside the frame's own range: ${value}`);
      }
    }
  }

  assert.deepEqual(at(0.3, 0.3), at(0.3, 0.3), 'two renders of one song must place the light identically');
});

test('the seed moves the light as well as choosing its colour', () => {
  const one = at(0.2, 0.5, 'a'.repeat(64));
  const two = at(0.2, 0.5, 'b'.repeat(64));

  assert.notDeepEqual(one, two, 'two songs in one accent must not drift identically');
});

test('an empty seed is a supported state, because the Studio lists the composition before props arrive', () => {
  assert.doesNotThrow(() => blobs(0, 0, {count: 3, seed: ''}));
});
