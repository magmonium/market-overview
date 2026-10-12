import type {IndexFacts} from './bundle';

/**
 * The day's headline figure — **one rule, three surfaces.** (0085_12)
 *
 * Issue 14 is explicit that the thumbnail does not get to invent its own notion of "most clickable": the featured
 * figure is the *headline* figure, the same one the cold open states and the same one the metadata leads with. That
 * is issue 13's "one bundle, three surfaces" and it is an anti-fabrication rule, not a design preference — a
 * thumbnail picking a different number from the video would be the video contradicting itself.
 *
 * ⚠️ **It lives here, not inline in `ColdOpen`, because "the same rule" has to be one piece of code.** Two copies
 * that happen to agree today are two copies that can drift, and the drift would be invisible: both still render,
 * both still show a real number, and only a viewer comparing the thumbnail to the video would see it.
 *
 * The rule: **the largest absolute move in the index scoreboard.** Absolute, not largest fall — a +2.1% day is as
 * much the day's story as a −2.1% one, and the pipeline has no view about direction.
 */
export type Headline = {
  /** A label key, never a display string — the language rides beside the bundle (see `copy.ts`). */
  labelKey: string;
  change: number | null;
};

export const headline = (indexes: IndexFacts[] | undefined): Headline | null => {
  const rows = indexes ?? [];
  // ⚠️ Guarded, where the inlined version was not. `cold_open` is only scheduled when `indexes` is present, so this
  // could never throw in the video — but a still is rendered by a *different* command against whatever props it is
  // handed, and a `reduce` over an empty array throws. Cheaper to be total than to rely on the caller.
  if (rows.length === 0) {
    return null;
  }
  const hardest = rows.reduce((worst, row) =>
    Math.abs(row.window?.change ?? 0) > Math.abs(worst.window?.change ?? 0) ? row : worst
  );
  return {labelKey: hardest.label_key, change: hardest.window?.change ?? null};
};
