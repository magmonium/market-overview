/**
 * The reel's time line — `৪:০০` under the title, counting.
 *
 * ⚠️ The assertions that matter are the two ends: frame **0** is `০:০০` (a clock that started at `১:০০` would be a
 * claim about the song that is false), and the **last frame equals the caption** — the same string the still prints.
 * Everything else is the middle of a monotone run.
 */
import assert from 'node:assert/strict';
import {test} from 'node:test';
import {clockAt, clockFor} from './clock.ts';

test('the numerals are the caption’s own, and so is the shape', () => {
  assert.equal(clockAt(0, 'bn'), '০:০০');
  assert.equal(clockAt(42, 'bn'), '০:৪২');
  assert.equal(clockAt(242, 'bn'), '৪:০২');
  assert.equal(clockAt(42, 'en'), '0:42');
});

test('past the hour it keeps counting minutes — there is no hours field on either side', () => {
  // ⚠️ `caption.duration_at`'s rule exactly: a song is minutes long, so `61:01` on the still and `61:01` here.
  assert.equal(clockAt(3661, 'en'), '61:01');
});

test('the last frame writes the caption, because the caption is what the still prints', () => {
  // Their song: 5462 frames at 30 fps, which Python measured as 182.040 s and wrote as `৩:০২`.
  assert.equal(clockAt((5462 - 1) / 30, 'bn'), '৩:০২');
  assert.equal(clockFor(5462 - 1, 30, 'bn', '৩:০২'), '৩:০২ / ৩:০২');
});

test('the elapsed half ticks, and the total is never recomputed here', () => {
  assert.equal(clockFor(0, 30, 'bn', '৩:০২'), '০:০০ / ৩:০২');
  assert.equal(clockFor(1260, 30, 'bn', '৩:০২'), '০:৪২ / ৩:০২');
  // ⚠️ Whatever Python formatted is what shows — a language this table has never heard of still prints its total.
  assert.equal(clockFor(0, 30, 'fr', '3:02'), '0:00 / 3:02');
});
