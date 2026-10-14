/**
 * 0087_09 — the catalogue: four identities, and the one mapping they must all agree about the *shape* of.
 *
 * ⚠️ Two properties here, and neither is a taste call.
 *
 * The registry must not be able to disagree with the ids the record stores and the menu offers — those ids are
 * in `run.json`, so a rename is a data migration, not a refactor.
 *
 * And every theme must **lift the quiet parts**. That one was learned from a real frame rather than imagined:
 * peak-normalised, the brief's own level-consistent bed rendered as a near-solid block with its texture crushed
 * into the top fifth, because one loud moment owned the whole scale. The clock must stay physically honest —
 * it *is* the amplitude — so the correction lives here, in how the picture maps it.
 */
import assert from 'node:assert/strict';
import {test} from 'node:test';

import {FORMS, THEME_IDS, THEMES, themeFor} from './themes.ts';

test('the catalogue is the four documented ids, and every theme is a whole identity', () => {
  assert.deepEqual(THEMES.map((theme) => theme.id), [...THEME_IDS], 'the registry and the ids cannot diverge');
  assert.deepEqual([...FORMS], ['bars', 'ribbon', 'ring', 'bloom']);

  for (const theme of THEMES) {
    assert.ok(theme.name.length > 0, `${theme.id} needs a name the menu can show`);
    assert.ok(['disc', 'notes'].includes(theme.motif), `${theme.id} must own a motif`);

    // ⚠️ Every slot the drawings read. A missing one paints `undefined`, which React drops **silently** — so a
    // theme with a hole in it renders as a black rectangle with no error anywhere to explain it.
    for (const slot of ['field', 'ink', 'muted', 'wave', 'glow'] as const) {
      assert.match(theme.palette[slot], /^#[0-9a-f]{6}$/i, `${theme.id}.palette.${slot}`);
    }
  }
});

test('every theme lifts the quiet parts and pins the ends', () => {
  for (const theme of THEMES) {
    assert.equal(theme.curve(0), 0, `${theme.id}: silence stays silence`);
    assert.equal(theme.curve(1), 1, `${theme.id}: the loudest moment still reaches the edge`);
    assert.ok(theme.curve(0.25) > 0.25, `${theme.id}: a quiet passage must gain height, or the song loses texture`);

    let previous = -Infinity;
    for (let step = 0; step <= 20; step += 1) {
      const value = theme.curve(step / 20);
      assert.ok(value >= previous, `${theme.id}: a louder moment must never be drawn shorter`);
      previous = value;
    }
  }
});

test('an unknown theme id is refused, and the refusal names the catalogue', () => {
  assert.throws(
    () => themeFor('vynil'),
    /unknown theme "vynil".*vinyl, neon, parchment, aurora/,
    'a silent fallback would render a reel in a theme nobody chose',
  );
});
