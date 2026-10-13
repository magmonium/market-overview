/**
 * The brief's typeface — the bytes, the family, and the wait for both.
 *
 * ⚠️ **The face used to be the machine's.** `theme.ts` named macOS's own *Kohinoor Bangla* and let the system
 * font directory resolve it. That made the rendered pixels a property of the host: the same `facts.json`
 * rendered different glyphs on Linux, where Kohinoor Bangla does not exist and the stack silently supplies
 * something else. Two guarantees die with that — ADR 0003's "a re-render from the snapshot is a guaranteed
 * match", and `test_frame_identity.py`, which would have compared a macOS baseline against a server render.
 * So the three `.woff2` subsets in `fonts/` are **committed**, and every machine renders the same glyphs.
 *
 * ⚠️ **One face per weight, and the instances are baked rather than interpolated.** Google serves this family
 * as a single **variable** font, and leaving the browser to instance `wght` 400/600/700 at render time was
 * measured not to be stable: the large figure — 200 px at weight 700 — moved by a couple of anti-aliasing
 * levels along its glyph edges between a cold and a warm browser cache, which is invisible but is enough to
 * break a byte-for-byte rebuild. `fonts/instance.py` bakes the three weights out of the variable file, and the
 * results are committed, so the browser is handed a static face and never touches an axis. That also takes a
 * browser capability out of the determinism story, which is the real point: a Chromium on a Linux server has
 * to produce the same glyphs as one on the operator's laptop, and a static face leaves it nothing to decide.
 *
 * ⚠️ **The subsets are not interchangeable.** The face is split by script: the Bengali subset carries Bengali
 * and `₹` but **no Latin**, and the Latin subset carries the digits, the index slugs, `DII` and the `−`
 * (U+2212) the brief prints. Dropping either leaves half of an edition in a fallback face — the failure this
 * module exists to prevent — and that is why the split is **data**, in `fonts.json`.
 *
 * ⚠️ **`fonts.json` is the single source, and `copybudget.py` reads the same file.** The copy-budget gate
 * measures in a browser "because only the browser knows the face's metrics", so the measuring browser and the
 * renderer must be measuring the *same* face. Two hand-maintained copies of the ranges would drift, and the
 * drift would present as a *passing* budget.
 */
import {useEffect, useState, type FC} from 'react';
import {cancelRender, continueRender, delayRender} from 'remotion';
import bengali400 from './fonts/NotoSansBengali-bengali-400.woff2';
import bengali600 from './fonts/NotoSansBengali-bengali-600.woff2';
import bengali700 from './fonts/NotoSansBengali-bengali-700.woff2';
import latin400 from './fonts/NotoSansBengali-latin-400.woff2';
import latin600 from './fonts/NotoSansBengali-latin-600.woff2';
import latin700 from './fonts/NotoSansBengali-latin-700.woff2';
import latinExt400 from './fonts/NotoSansBengali-latin-ext-400.woff2';
import latinExt600 from './fonts/NotoSansBengali-latin-ext-600.woff2';
import latinExt700 from './fonts/NotoSansBengali-latin-ext-700.woff2';
import spec from './fonts.json';

/** The family every surface names. Read from `fonts.json` so the data and the code cannot disagree. */
export const FONT_FAMILY = spec.family;

/** ⚠️ The fallbacks cover a **missing glyph**, never a missing face — `useFonts` refuses the render instead. */
export const FONT = `"${FONT_FAMILY}", system-ui, -apple-system, sans-serif`;

/**
 * ⚠️ Keyed by the basename `fonts.json` names, so the data and the imports cannot disagree about *which* files
 * are in play. `tests/test_fonts.py` pins that every face has an import and every import has a face — a subset
 * declared in the CSS with no URL behind it renders as nothing at all, which is the quietest possible defect.
 */
const SUBSET_URLS: Record<string, string> = {
  'NotoSansBengali-bengali-400.woff2': bengali400,
  'NotoSansBengali-bengali-600.woff2': bengali600,
  'NotoSansBengali-bengali-700.woff2': bengali700,
  'NotoSansBengali-latin-ext-400.woff2': latinExt400,
  'NotoSansBengali-latin-ext-600.woff2': latinExt600,
  'NotoSansBengali-latin-ext-700.woff2': latinExt700,
  'NotoSansBengali-latin-400.woff2': latin400,
  'NotoSansBengali-latin-600.woff2': latin600,
  'NotoSansBengali-latin-700.woff2': latin700,
};

export const FONT_CSS = spec.faces
  .map(({file, weight, unicode_range}) => {
    const url = SUBSET_URLS[file.replace(/^fonts\//, '')];
    return (
      `@font-face{font-family:'${FONT_FAMILY}';font-style:normal;font-weight:${weight};` +
      `font-display:block;src:url('${url}') format('woff2');unicode-range:${unicode_range};}`
    );
  })
  .join('');

/** Marks the injected `<style>`, so a remount does not add a second copy of the same rules. */
const STYLE_ID = 'market-brief-typeface';

/**
 * ⚠️ **The text is load-bearing, not illustrative.** `document.fonts.load(font)` with no text argument resolves
 * against the face that covers a *space* — which is the **Latin** subset. Every Bengali glyph would then load
 * lazily, *after* the first frame had been captured, and the brief would ship the fallback face while every
 * test passed. Text spanning both subsets is what makes the wait cover what the brief actually prints.
 */
const SAMPLE =
  'অআইঈউঊকখগঘঙচছজঝটঠডঢণতথদধনপফবভমযরলশষসহািীুূৃেৈোৌ্ংঁৎ০১২৩৪৫৬৭৮৯₹ABC NIFTY 50 1234567890 %+,·−—';

/** The weights the block components set, so the wait covers each instance rather than just the default. Taken
 * from `fonts.json` for the same reason the ranges are: the copy budget loads the identical list, and a weight
 * that rendered but was never waited for is the exact race this module exists to close. */
const WEIGHTS: readonly number[] = [...new Set(spec.faces.map((face) => face.weight))].sort(
  (a, b) => a - b,
);

/**
 * Block the render until the typeface is present. Call once, at the top of a composition.
 *
 * ⚠️ **It refuses rather than falls back.** An unloadable face is `cancelRender`, not a quiet `system-ui`:
 * a brief set in the wrong face is the same "looks right here and different elsewhere" defect the logo's
 * outline check refuses for (`logo.py`), and shipping it silently is worse than not shipping.
 */
export const useFonts = (): void => {
  const [handle] = useState(() => delayRender(`Loading ${FONT_FAMILY}`));

  useEffect(() => {
    if (!document.getElementById(STYLE_ID)) {
      const style = document.createElement('style');
      style.id = STYLE_ID;
      style.textContent = FONT_CSS;
      document.head.appendChild(style);
    }

    const load = (weight: number) => document.fonts.load(`${weight} 64px "${FONT_FAMILY}"`, SAMPLE);

    Promise.all(WEIGHTS.map(load))
      // ⚠️ `fonts.ready` as well as the individual loads, and it is not belt-and-braces: the loads resolve when
      // each face has *decoded*, while the layout that swaps the fallback out for the real face lands on the
      // next style pass.
      .then(() => document.fonts.ready)
      // ⚠️ **And two frames of real time before continuing.** `fonts.ready` says the faces have *decoded*; it
      // does not say that the layout using them has landed. A frame composed at that seam sits every glyph a
      // fraction of a pixel out — invisible, and enough to break a byte-for-byte rebuild. Baking the weights
      // is what removed the measured variance; this is the other half of the same guarantee, that the face is
      // not merely loaded but **laid out**, and it costs two frames.
      .then(
        () =>
          new Promise<void>((resolve) => {
            requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
          }),
      )
      .then(() => continueRender(handle))
      .catch((error: unknown) => {
        cancelRender(
          new Error(
            `${FONT_FAMILY} could not be loaded, so the brief would render in a fallback face: ` +
              `${error instanceof Error ? error.message : String(error)}`,
          ),
        );
      });
  }, [handle]);
};

/**
 * The declarative form of `useFonts`, for a composition that would rather mount a child than call a hook at
 * its top — `MarketBrief` returns its tree from an arrow expression, and this keeps that shape intact.
 *
 * Renders nothing. Its only job is to be *inside* the composition tree so the wait is registered.
 */
export const Typeface: FC = () => {
  useFonts();
  return null;
};
