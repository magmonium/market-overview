import {AbsoluteFill, Sequence} from 'remotion';
import {Typeface} from '../../../remotion/fonts.ts';
import {EndCard} from './EndCard.tsx';
import {Mark as MarkPlate} from './Mark.tsx';
import {Slide} from './Slide.tsx';
import {Ticker} from './Ticker.tsx';
import type {FactsBundle, Mark} from './bundle.ts';
import {tableFor} from './copy.ts';
import {chartFor, useBundle, useMark} from './facts.ts';
import {varies} from './format.ts';
import {BG, INK} from './palette.ts';
import type {BooksBriefProps} from './props.ts';

/**
 * **`BooksBrief` — one chart, one video, 2 m 49 s.**
 *
 * ⚠️ **The running order comes from the bundle, not from this file.** Each slot's start, length and entrance are in
 * `facts.timeline.blocks`, computed by `books_brief/timeline.py` — the brief's own rule, quoted in its `MarketBrief.tsx`:
 * *"the timeline comes from `props.timeline`, not from this file."* A renderer holding a second copy of the dwell table
 * would be a second copy of the interest curve, and the copy that fell behind would be the one that shipped.
 *
 * ⚠️ **A slot whose rank is `null` is not a book** — the intro and the outro carry none — and the renderer keys off
 * that rather than off the slot's index, because an index would silently show the *first* book on the outro the moment
 * the schedule grew a slot.
 *
 * ⚠️ **One composition, four charts** (ticket 13). The chart id is a prop, exactly as the brief passes `lang` — so the
 * bundle is fetched once and four renders read it, which is what makes *"four independent renders from one snapshot"*
 * literally true.
 */
export const BooksBrief = ({chart, week}: BooksBriefProps) => {
  const bundle = useBundle(week);
  const mark = useMark();

  // ⚠️ Mounted **first**, so the render blocks before a single frame is captured. A chart set in a fallback face is the
  // one failure nothing else can see — and ⚠️ ticket 27's trap lives here: the Bengali subset carries **no Latin**, so a
  // slide printing `WEEK 41`, `₹399` and the ticker needs **both** subsets. `fonts.ts` loads all nine faces and waits
  // against a sample spanning both, which is exactly why this is the brief's `useFonts` rather than a copy of it.
  return (
    <AbsoluteFill style={{background: BG, color: INK}}>
      <Typeface />
      {bundle ? <Body bundle={bundle} mark={mark} chart={chart} week={week} /> : null}
    </AbsoluteFill>
  );
};

const Body = ({
  bundle,
  mark,
  chart,
  week,
}: {
  bundle: FactsBundle;
  mark: Mark;
  chart: string;
  week: string;
}) => {
  // ⚠️ Refuses an unknown or absent chart rather than defaulting — see `chartFor`. A Bengali video full of English
  // books looks completely normal, which is what makes a silent fallback the worst possible answer here.
  const facts = chartFor(bundle, chart);
  const copy = tableFor(facts.language);
  const ticker = <Ticker ticker={bundle.ticker ?? null} copy={copy} lang={facts.language} />;

  // ⚠️ **Ticket 20's rule is a property of the *chart*, so it is decided once here rather than once per slide.**
  //
  // ⚠️ Every slide can see `facts.ranked`, so computing this inside `Slide` would work — and would rescan a hundred rows
  // a hundred times to reach the same two booleans. ⚠️ The real reason is the one that matters: *whether the country
  // varies* is a fact about the run, not about the row, and a per-row computation invites a chart where one slide
  // prints *India* and the next does not.
  const labels = {
    country: varies(facts.ranked.map((row) => row.country)),
    language: varies(facts.ranked.map((row) => row.language)),
  };

  return (
    <>
      {facts.timeline.blocks.map((block) => {
        // ⚠️ A rank with no row is a **gap in the chart**, not a slide to invent. It cannot happen while the schedule is
        // built from the chart's own length — and drawing a blank slide for it would hide the day it stopped being true.
        const book = block.rank === null ? null : (facts.ranked[block.rank - 1] ?? null);
        if (block.rank !== null && !book) {
          return null;
        }

        return (
          <Sequence key={block.id} from={block.start} durationInFrames={block.duration} name={block.id}>
            {book ? (
              <Slide
                book={book}
                facts={facts}
                copy={copy}
                lang={facts.language}
                week={week}
                enterFrames={block.enter_frames}
                ticker={ticker}
                labels={labels}
              />
            ) : (
              <EndCard block={block} facts={facts} copy={copy} week={week} />
            )}
          </Sequence>
        );
      })}

      {/* ⚠️ **Last, so the mark sits above every slide.** It is present throughout the run, and it is one element rather
          than a hundred — see the note in `Mark.tsx`. */}
      <MarkPlate mark={mark} />
    </>
  );
};

