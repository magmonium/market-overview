/**
 * ⚠️ **Ticket 08's band, and it is deliberately allowed to not exist.**
 *
 * The index scoreboard is *"a stock brief in miniature"* — fetched through the brief's own
 * `market_overview.fetch.tradingview`, snapshotted, and **dated** by the session clock, because *"a ticker that cannot
 * say when it is from is a ticker that can lie."*
 *
 * ⚠️ **A missing scoreboard omits the band entirely — never zeros, never stale, never a placeholder.** That is the
 * brief's own *degrade to omission* principle with the **abort threshold moved**: the brief treats a short scoreboard
 * as **fatal** (`MissingTickersError`) because *the scoreboard is its content*; here it is decoration, so it must not
 * be. ⚠️ And the layout absorbs the omission without a hole, because the book block is `flex: 1`.
 *
 * ⚠️ **The client is not built yet**, so today the band simply does not render — which is the *designed* degrade state
 * rather than a missing feature. It appears the moment the snapshot carries a scoreboard.
 */
import type {Ticker as TickerFacts} from './bundle.ts';
import type {Copy} from './copy.ts';
import {number, percent} from './format.ts';
import {GREEN, MUTED, RED, RULE} from './palette.ts';

/**
 * **The market band: the world behind the book** (ticket 08).
 *
 * ⚠️ **It is allowed to not exist, and that is the design rather than a gap.** The scoreboard is read through the
 * brief's own client, and a failed fetch — or a short one, or one with no clock — **omits the band entirely**. Never
 * zeros, never stale, never a placeholder. ⚠️ That is still the brief's *degrade to omission* principle with the
 * **abort threshold moved**: there, a short scoreboard raises `MissingTickersError` and stops the day, because *the
 * scoreboard is the content*. Here it is background, so it must not be — and the layout absorbs the omission without a
 * hole, because the book block is `flex: 1`.
 *
 * ⚠️ **The band must read as background.** `MUTED` rather than `INK`, tabular numerals so the columns do not jitter as
 * the digits change, and never a weight that competes with the book. It sits in the thin part of the scrim, which is
 * where the atmosphere is meant to show through.
 *
 * ⚠️ **Colour by sign, and the exception is stated rather than forgotten.** For an equity index up is good, so
 * `GREEN`/`RED` is right — but the brief's own rule is that an **`*INR` pair must be `NEUTRAL`**: for a currency pair
 * *up* means the rupee is **weaker**, so colouring by sign would say the opposite of the truth. None of these five is a
 * currency pair; if one is ever added, it takes `NEUTRAL` and not this line.
 */
export const Ticker = ({ticker, copy, lang}: {ticker: TickerFacts | null; copy: Copy; lang: string}) => {
  if (!ticker || ticker.rows.length === 0) {
    return null;
  }

  return (
    <div
      style={{
        borderTop: `1px solid ${RULE}`,
        borderBottom: `1px solid ${RULE}`,
        padding: '14px 0',
        display: 'flex',
        // ⚠️ **It wraps rather than clipping, and the first render is why.** At 26 px with a 40 px gap the five rows
        // plus the session date came to roughly 2,160 px against a 1,728 px content box, so the last index was cut off
        // **at the frame edge** and the date was pushed off the frame entirely — a silent truncation, which is the one
        // failure this product does not accept anywhere else. The sizes below fit the ticket's five on one line with
        // room to spare; ⚠️ and `wrap` is what makes a **sixth** index degrade to a second line rather than vanish.
        flexWrap: 'wrap',
        alignItems: 'baseline',
        gap: 24,
        color: MUTED,
        fontSize: 20,
        fontVariantNumeric: 'tabular-nums',
        letterSpacing: '0.02em',
      }}
    >
      <span style={{fontSize: 18, letterSpacing: '0.14em', opacity: 0.75}}>
        {copy.ticker.toUpperCase()}
      </span>

      {ticker.rows.map((row) => (
        <span key={row.label_key} style={{whiteSpace: 'nowrap'}}>
          {/* ⚠️ The slug from the snapshot, the words from the table (ADR 0003) — and an unknown slug prints as itself
              rather than as `undefined`, so a new index degrades visibly. */}
          {copy.indices[row.label_key] ?? row.label_key}{' '}
          {/* ⚠️ `number` renders the dash for a `null` close — an index that did not resolve is not an index at zero. */}
          {number(row.close, lang)}{' '}
          <span
            style={{
              color: row.change === null ? MUTED : row.change >= 0 ? GREEN : RED,
            }}
          >
            {percent(row.change, lang)}
          </span>
        </span>
      ))}

      {/* ⚠️ **The session, not the render's clock.** *"A ticker that cannot say when it is from is a ticker that can
          lie"* — and this band sits under a book ranked over **six months**, so without the date a reader has no way to
          tell today's market from the last time the run happened to succeed. */}
      {ticker.as_of ? <span style={{opacity: 0.75}}>{ticker.as_of}</span> : null}
    </div>
  );
};

