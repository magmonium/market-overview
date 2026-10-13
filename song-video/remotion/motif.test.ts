/**
 * 0087_10 — the motif: the rotating disc.
 *
 * ⚠️ **Ticket 11's rule as a property, not a promise.** "The motif must never rest" is the difference between a
 * design and a screensaver, so it is asserted here between *consecutive* frames: a disc that parks, or that
 * turns backwards, fails — it does not merely disappoint.
 *
 * ⚠️ And the angle is driven by the **traversal**, not by a wall clock. Two renders of the same song put the
 * disc in exactly the same place, which is the one promise this pipeline never trades away (ADR 0006).
 */
import assert from 'node:assert/strict';
import {test} from 'node:test';

import {NOTE_SWAY, discAngle, noteAt} from './motif.ts';

test('the disc turns forward, never rests, and lands on whole turns at the end', () => {
  const turns = 6;

  assert.equal(discAngle(0, {turns}), 0, 'the first frame is the disc at rest');
  assert.equal(discAngle(1, {turns}), turns * 360, 'the last frame is a whole number of turns, not a stray angle');

  for (let step = 0; step < 200; step += 1) {
    const before = discAngle(step / 200, {turns});
    const after = discAngle((step + 1) / 200, {turns});
    assert.ok(after > before, `the disc must have moved between frames ${step} and ${step + 1}`);
  }
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
