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
 * ## The rule is **Nifty 50**
 *
 * ⚠️ The brief leads on the index a reader means by *"the market"*, not on whichever row moved most. The earlier
 * rule was *the largest absolute move in the scoreboard*, and it made the day's headline an accident of which index
 * happened to be busiest — a session where the mid-caps ran led the whole product on `Nifty Next 50`. A reader
 * opening a brief about the Indian market expects **Nifty 50** first, whatever else moved.
 *
 * ⚠️ **The largest-absolute-move rule survives only as the fallback**, for a bundle with no Nifty 50 row at all — a
 * hand-written props file, or a vendor that renamed the symbol. A fallback rather than `null`, because the
 * alternative is a blank cold open and a thumbnail of dashes on a day whose data was otherwise fine. It stays
 * *absolute*: a +2.1 % day is as much the story as a −2.1 % one, and the pipeline has no view about direction.
 */
export type Headline = {
  /** A label key, never a display string — the language rides beside the bundle (see `copy.ts`). */
  labelKey: string;
  change: number | null;
};

/** The label key the brief leads on. Mirrored by `HEADLINE_KEY` in `display.py` for the metadata (0085_13). */
export const HEADLINE_KEY = 'nifty50';

/** The fallback rule — the largest **absolute** move. Only ever called on a scoreboard with rows in it. */
const biggestMove = (rows: IndexFacts[]): IndexFacts =>
  rows.reduce((worst, row) =>
    Math.abs(row.window?.change ?? 0) > Math.abs(worst.window?.change ?? 0) ? row : worst
  );

export const headline = (indexes: IndexFacts[] | undefined): Headline | null => {
  const rows = indexes ?? [];
  // ⚠️ Guarded, where the inlined version was not. `cold_open` is only scheduled when `indexes` is present, so this
  // could never throw in the video — but a still is rendered by a *different* command against whatever props it is
  // handed, and a `reduce` over an empty array throws. Cheaper to be total than to rely on the caller.
  if (rows.length === 0) {
    return null;
  }
  const featured = rows.find((row) => row.label_key === HEADLINE_KEY) ?? biggestMove(rows);
  return {labelKey: featured.label_key, change: featured.window?.change ?? null};
};
