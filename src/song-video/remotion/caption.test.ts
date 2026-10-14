/**
 * The caption: the word over the number, and the refusal that stops a language nobody chose. (Map issue 08)
 *
 * ⚠️ The halves come from two runtimes, and these tests pin the seam: the *value* is Python's (already written in
 * the script's numerals), the *word* is this side's. A test that formatted the duration here would be a second
 * implementation of it, which is exactly what the split avoids.
 */
import assert from 'node:assert/strict';
import {test} from 'node:test';

import {LANGS, captionFor} from './caption.ts';

test('the caption is the word and the duration, in the scripts the table covers', () => {
  // ⚠️ The duration arrives already written: these are the characters, not a font applied to `4:00`.
  assert.equal(captionFor('bn', '৪:০০'), 'সংগীত · ৪:০০');
  assert.equal(captionFor('en', '4:00'), 'Music · 4:00');
});

test('every language in the table has a word, and there are exactly the two', () => {
  assert.deepEqual([...LANGS].sort(), ['bn', 'en'], 'the languages Python may ask for');
  for (const lang of LANGS) {
    assert.ok(captionFor(lang, '0:00').length > 0, `${lang} needs a word`);
  }
});

test('an unknown caption language is refused rather than written in a language nobody chose', () => {
  assert.throws(() => captionFor('fr', '4:00'), /unknown caption language "fr".*bn, en/);
});
