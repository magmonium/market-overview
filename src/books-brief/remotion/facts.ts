/**
 * Reading the staged snapshot — **the only fetch in this layer**, and it is a local one.
 *
 * ⚠️ **The URL is the Python side's, mirrored once, and that is a documented cost.** `books_brief/stage.py` writes the
 * file *and* owns `url_for`; this file is the other half of that subprocess boundary, exactly like `render.ENTRY`.
 * They cannot be made to share a constant across a language, so `tests/test_stage.py` asserts the two agree **on the
 * Python side** — which is the only place the assertion can be made. A disagreement surfaces as a fetch that fails
 * inside Remotion, so the test is worth more than it looks.
 *
 * ⚠️ **A render blocks until the bundle is present** (`delayRender`), and **refuses** if it cannot be read. A chart
 * rendered against a missing snapshot is a video of blank slides, and the failure mode this product exists to avoid is
 * a plausible-looking artefact built from nothing.
 */
import {useEffect, useState} from 'react';
import {cancelRender, continueRender, delayRender, staticFile} from 'remotion';
import type {ChartFacts, FactsBundle, Mark} from './bundle.ts';

/** ⚠️ Mirrors `stage.WEEKS`. */
const WEEKS = 'weeks';
/** ⚠️ Mirrors `store.FACTS` — the file is called `facts.json` on both sides, so a fetch path is traceable to a snapshot. */
const FACTS = 'facts.json';
/** ⚠️ Mirrors `stage.MARK`. Staged **always**, as an explicit `null` when the operator has no asset, because a fetch
 * that 404s is a failed render rather than a chart without branding. */
const MARK = 'mark.json';

/** ⚠️ Exported so `Root.tsx`'s `calculateMetadata` fetches the **same** URL this module's hook does — one literal, one
 * boundary. */
export const bundleUrl = (week: string): string => staticFile(`${WEEKS}/${week}/${FACTS}`);
const markUrl = (): string => staticFile(MARK);

/** The one hook both loaders share: block the render, fetch, and refuse rather than continue on failure. */
const useJson = <T,>(url: string, label: string): T | null => {
  const [value, setValue] = useState<T | null>(null);
  const [handle] = useState(() => delayRender(label));

  useEffect(() => {
    let live = true;
    fetch(url)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`${response.status} ${response.statusText}`);
        }
        return response.json() as Promise<T>;
      })
      .then((body) => {
        if (!live) {
          return;
        }
        setValue(body);
        continueRender(handle);
      })
      .catch((error: unknown) => {
        // ⚠️ **`cancelRender`, never a quiet empty bundle.** A chart built from a bundle that never arrived renders
        // perfectly — as a hundred blank slides under a title claiming a Top 100 — and nothing downstream could tell.
        cancelRender(
          new Error(
            `${label} could not be read from ${url}: ${error instanceof Error ? error.message : String(error)}`,
          ),
        );
      });
    return () => {
      live = false;
    };
  }, [url, label, handle]);

  return value;
};

/** The week's staged bundle, or `null` while the render waits for it. */
export const useBundle = (week: string): FactsBundle | null =>
  useJson<FactsBundle>(bundleUrl(week), `The ${week} snapshot`);

/** The operator's mark, or `null` — and `null` is a **valid brief**, not a broken one. */
export const useMark = (): Mark => useJson<Mark>(markUrl(), 'The mark') ?? null;

/**
 * One chart's facts, **or a refusal**.
 *
 * ⚠️ **An unknown chart is refused rather than defaulted.** A chart that silently fell back to another chart's data
 * is indistinguishable from one that did not — the failure is a Bengali video full of English books, which looks
 * completely normal. The same rule `charts.get` keeps in Python.
 *
 * ⚠️ **An absent key is also a refusal**, and for a different reason: `facts.build` omits a chart whose sources failed
 * (ticket 13), so the run should never have asked for a render. If it did, the render stops rather than producing a
 * video of nothing.
 */
export const chartFor = (bundle: FactsBundle, chart: string): ChartFacts => {
  const facts = bundle.charts[chart];
  if (!facts) {
    const known = Object.keys(bundle.charts).join(', ') || 'none';
    throw new Error(
      `no chart ${chart} in the ${bundle.meta.week} snapshot — it holds ${known}`,
    );
  }
  return facts;
};

/** ⚠️ Mirrors `stage.COVERS`. */
const COVERS = 'covers';

/**
 * A cover's staged path — **and the row's own `cover` is what says whether to ask for one at all.**
 *
 * ⚠️ A row with `cover: null` has no staged file, and `stage.covers` writes one only for a row that has a cover. So
 * this is called **only** when `book.cover !== null`: asking for a file that is not there is a broken image, and a
 * broken image is exactly the *"blank white box"* ticket 07 forbids. The branded tile is the documented answer instead.
 */
export const coverUrl = (isbn: string): string => staticFile(`${COVERS}/${isbn}.jpg`);

