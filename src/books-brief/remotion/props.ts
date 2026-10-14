/**
 * What a render is given — **the whole input, and nothing else.**
 *
 * ⚠️ **Two strings, and deliberately not the bundle.** The brief puts its whole facts file in `--props`; here the
 * bundle is **staged into `public/`** and fetched (`facts.ts`), because *one* bundle serves **four** renders and the
 * chart id is the only thing that varies (ticket 13). That is what makes *"four independent renders from one snapshot"*
 * literally true — and it keeps this shape small enough that `render.command` can pin it, which is the thing that stops
 * a render bundling the **brief's** root by mistake.
 *
 * ⚠️ **Neither field is parsed.** `week` is a key, not a date: nothing here derives a previous week from it, because
 * ticket 01's window is Python's (`delta.previous_week`) and a second implementation would be a second answer.
 */
export type BooksBriefProps = {
  /** ⚠️ An id from `charts.ALL`. An unknown one is **refused** by `chartFor`, never defaulted — a chart that fell back
   * to another chart's data is indistinguishable from one that did not. */
  readonly chart: string;
  /** The ISO week, e.g. `2026-W41` — the staged bundle's folder, and nothing else. */
  readonly week: string;
};
