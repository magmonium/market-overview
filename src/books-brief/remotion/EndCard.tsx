import {AbsoluteFill} from 'remotion';
import type {Block, ChartFacts} from './bundle.ts';
import type {Copy} from './copy.ts';
import {digits} from './format.ts';
import {CARD, FONT, INK, MUTED, RULE, SCRIM, SLIDE} from './palette.ts';

/**
 * The intro and the outro — **the chart introducing itself**, and the only slots that show no book.
 *
 * ⚠️ **They exist so the video can say what it is before it says a hundred things.** A viewer arriving mid-feed has six
 * seconds to learn which chart this is, which week, and which market — and ticket 20's rule is that the market is
 * **stated**, not implied: the Bengali chart spans India *and* Bangladesh, which no viewer could infer from the header
 * alone.
 *
 * ⚠️ **Week one says so.** Ticket 18 — *"a baseline that looked like a normal week would be indistinguishable from
 * one"* — so a run with no previous chart carries the footnote, and its rows carry no Δ and no NEW badge (which the
 * slide handles by itself: `move` is `null` for every row).
 */
export const EndCard = ({
  block,
  facts,
  copy,
  week,
}: {
  block: Block;
  facts: ChartFacts;
  copy: Copy;
  week: string;
}) => {
  // ⚠️ Week one is the run where **no row has a move at all** — not "some rows", every row — because `delta.ranks`
  // returns `None` when the previous week was never built. Checking it here rather than threading a flag means the
  // footnote cannot disagree with the rows beneath it.
  const baseline = facts.ranked.length > 0 && facts.ranked.every((book) => book.move === null);

  return (
    <AbsoluteFill
      style={{
        background: SCRIM,
        color: INK,
        fontFamily: FONT,
        padding: CARD.padding,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 28,
      }}
    >
      <div style={{fontSize: SLIDE.header, letterSpacing: '0.22em', color: MUTED}}>
        {`${copy.week} ${digits(week.split('-W')[1] ?? week, facts.language)}`}
      </div>

      <div style={{fontSize: 108, fontWeight: 700, textAlign: 'center', lineHeight: 1.1}}>
        {`TOP ${digits(facts.ranked.length, facts.language)} ${copy.charts[facts.label_key] ?? facts.label_key}`}
      </div>

      <div style={{width: 160, height: 4, background: RULE, borderRadius: 2}} />

      <div style={{fontSize: SLIDE.detail, color: MUTED, letterSpacing: '0.06em'}}>
        {copy.markets[facts.market] ?? facts.market}
      </div>

      {/* ⚠️ **The basis, and the window it actually has** (ticket 23). The six-month window is *accumulated* from our
          own snapshots, so an early week must state the smaller number rather than claiming six months it does not
          hold — which is the same rule the description keeps. */}
      <div style={{fontSize: SLIDE.label, color: MUTED, marginTop: 12}}>{copy.disclosure}</div>

      {/* ⚠️ Ticket 18's footnote, and it is the reason the intro exists at all: a baseline that looked like a normal
          week would be indistinguishable from one. */}
      {baseline ? (
        <div style={{fontSize: SLIDE.label, color: MUTED, opacity: 0.8}}>{copy.baseline}</div>
      ) : null}

      {/* The outro is the same card — deliberately. It is one idea (the chart), shown at both ends, and a second design
          for the closing frame would be a second thing to keep in step for no gain. */}
      {block.key === 'outro' ? (
        <div style={{fontSize: SLIDE.label, color: MUTED, opacity: 0.6, marginTop: 8}}>{copy.attribution}</div>
      ) : null}
    </AbsoluteFill>
  );
};
