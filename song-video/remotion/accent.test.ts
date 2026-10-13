/**
 * 0087_12 — the accent: **a colour per song, decided by nothing but the record.**
 *
 * ⚠️ The property that matters is not "the colours differ" — it is that they differ **and are reproducible**. A
 * `Math.random()` would satisfy the first half of that sentence and destroy the second, which is why almost
 * everything here is an assertion about *sameness*, and why the seed is the master's digest rather than a title or
 * a timestamp.
 */
import assert from 'node:assert/strict';
import {test} from 'node:test';

import {accentAt, accentFor, type Accent} from './accent.ts';
import {THEME_IDS, THEMES} from './themes.ts';

const ACCENTS: readonly Accent[] = [
  {name: 'one', tint: '#111111'},
  {name: 'two', tint: '#222222'},
  {name: 'three', tint: '#333333'},
  {name: 'four', tint: '#444444'},
];

/** Sixty-four digests, which is what a run actually hands over: `sha256` in hexadecimal. */
const SEEDS = Array.from({length: 64}, (_, index) => `${index.toString(16).repeat(16)}${index}`);

test('the same seed always lands on the same accent, whatever it is asked twice', () => {
  const digest = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855';

  assert.equal(accentFor(ACCENTS, digest).name, accentFor(ACCENTS, digest).name);
  assert.equal(accentAt(digest), accentAt(digest));
});

test('different songs land on different accents, and every authored accent is reachable', () => {
  const chosen = new Set(SEEDS.map((seed) => accentFor(ACCENTS, seed).name));

  assert.equal(
    chosen.size,
    ACCENTS.length,
    'an accent no digest ever reaches is dead code, and the operator asked for variety',
  );
});

test('no single accent takes the field, so the variety is real rather than three-of-a-kind', () => {
  const counts = new Map<string, number>();
  for (const seed of SEEDS) {
    const name = accentFor(ACCENTS, seed).name;
    counts.set(name, (counts.get(name) ?? 0) + 1);
  }

  const most = Math.max(...counts.values());
  assert.ok(most < SEEDS.length / 2, `one accent took ${most} of ${SEEDS.length} songs`);
});

test("a Studio's empty seed is the theme's first accent rather than a crash", () => {
  // ⚠️ The composition must be *listable* before props arrive (`Root.tsx`'s `EMPTY`), and a throw there is an
  // import error rather than a render failure — the one shape of failure this project keeps out of Remotion.
  assert.equal(accentFor(ACCENTS, '').name, 'one');
  assert.equal(accentAt('') >= 0 && accentAt('') < 1, true, 'and the phase stays in its own range');
});

test('every theme owns a set of accents, and they are the theme\'s own', () => {
  assert.deepEqual(THEMES.map((theme) => theme.id), [...THEME_IDS]);

  for (const theme of THEMES) {
    assert.ok(theme.accents.length >= 2, `${theme.id}: one accent is not a choice`);
    for (const accent of theme.accents) {
      assert.match(accent.tint, /^#[0-9a-f]{6}$/i, `${theme.id}.${accent.name}: a tint the browser can paint`);
      assert.ok(accent.name.length > 0, `${theme.id}: an accent nobody can name is an accent nobody can discuss`);
    }
    assert.equal(
      new Set(theme.accents.map((accent) => accent.name)).size,
      theme.accents.length,
      `${theme.id}: two accents with one name is a list nobody can act on`,
    );
  }
});
