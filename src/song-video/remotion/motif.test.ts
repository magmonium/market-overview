/**
 * 0087_10 — the motif: the rotating disc.
 *
 * ⚠️ **Ticket 11's rule as a property, not a promise.** "The motif must never rest" is the difference between a
 * design and a screensaver, so it is asserted here between *consecutive* frames: a disc that parks, or that
 * turns backwards, fails — it does not merely disappoint.
 *
 * ⚠️ **And it turns at a rate, not across the traversal — the correction the operator asked for.** Six turns spread
 * over a whole piece is ~11° a second, which is motion nobody can see, so "the disc is not rotating" was a fair
 * reading of a disc that was. A record has a *speed*: the tests below assert the speed, the angle it produces, and the
 * one-degree-per-frame smoothness that picking twelve seconds buys at 30 fps.
 *
 * ⚠️ The angle is still a function of the **frame**, never of a wall clock. Two renders of the same song put the disc
 * in exactly the same place, which is the one promise this pipeline never trades away (ADR 0006).
 */
import assert from 'node:assert/strict';
import {test} from 'node:test';

import {NOTE_SWAY, SECONDS_PER_TURN, discAngle, noteAt, turnedAt} from './motif.ts';

test('the disc turns forward, never rests, and never runs backwards', () => {
  for (let frame = 0; frame < 200; frame += 1) {
    const before = discAngle(turnedAt(frame, 30));
    const after = discAngle(turnedAt(frame + 1, 30));

    assert.ok(after > before, `the disc must have moved between frames ${frame} and ${frame + 1}`);
  }
});

test('the rate is a turntable, so a longer song simply gets more revolutions', () => {
  assert.equal(discAngle(0), 0, 'the first frame is the disc at rest');
  assert.equal(discAngle(turnedAt(30, 30)), 360 / SECONDS_PER_TURN, 'one second of a 30 fps render');
  assert.equal(discAngle(turnedAt(30 * SECONDS_PER_TURN, 30)), 360, 'and one revolution after twelve of them');

  // ⚠️ Twice the song, twice the turning — the property the traversal-bound version could not have.
  assert.equal(turnedAt(6000, 30), 2 * turnedAt(3000, 30));
});

test('twelve seconds a turn is exactly one degree per frame at 30 fps', () => {
  // ⚠️ Not a coincidence: it is the finest step a 30 fps render can draw, so the turn is as smooth as this pipeline
  // can make it. A rate that did not divide evenly would judder, however slowly it turned.
  assert.equal(discAngle(turnedAt(1, 30)), 1);
  assert.equal(discAngle(turnedAt(30, 30)) / 30, 1);
});

test('the notes flow: each one moves every frame, and none of them leaves the frame', () => {
  const count = 7;
  const at = (travelled: number) =>
    Array.from({length: count}, (_, index) => noteAt(index, travelled, {seed: 'neon', count}));

  for (const note of at(0)) {
    assert.ok(note.x >= 0 && note.x <= 1, 'a note is always inside the frame');
    assert.ok(note.y >= 0 && note.y <= 1, 'and inside it vertically');
    assert.ok(note.size > 0, 'a note has a size');
  }

  // ⚠️ Ticket 11's rule again, and this is the one that decides whether the motif is a design or a decoration:
  // between *any* two consecutive frames every note must have moved. One that hovers is a sticker.
  for (let step = 0; step < 100; step += 1) {
    const before = at(step / 100);
    const after = at((step + 1) / 100);
    for (let index = 0; index < count; index += 1) {
      assert.notEqual(after[index].x, before[index].x, `note ${index} must have moved between two frames`);
    }
  }

  assert.ok(
    new Set(at(0).map((note) => Math.round(note.y * 100))).size > 1,
    'more than one lane, or this is one note drawn seven times',
  );
});

test('the notes fill the frame evenly, and two neighbours can never swap places', () => {
  // ⚠️ **The fix the stills asked for, as a property rather than a hope.** The first version drew each note's
  // position from the same sequence as its lane and its speed: in motion it read as scattered, and in a *still* it
  // clumped — three notes against the left edge, three mid-frame, the right half empty. Even columns fix that at
  // every instant, and the bound on the sway is what stops the fix from undoing itself.
  const count = 5;
  const pitch = 1 / count;
  const closest = pitch - 2 * NOTE_SWAY;

  for (let step = 0; step <= 60; step += 1) {
    const notes = Array.from({length: count}, (_, index) => noteAt(index, step / 60, {seed: 'neon', count}));
    const xs = notes.map((note) => note.x).sort((a, b) => a - b);

    assert.ok(xs[0] > 0 && xs[count - 1] < 1, `no note is off the edge at ${step}`);
    for (let index = 1; index < count; index += 1) {
      const gap = xs[index] - xs[index - 1];
      assert.ok(gap >= closest - 1e-9, `notes ${index - 1} and ${index} closed to ${gap.toFixed(4)} at ${step}`);
    }
  }
});
