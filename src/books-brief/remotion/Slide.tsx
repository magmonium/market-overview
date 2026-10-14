import {AbsoluteFill, Img, useCurrentFrame} from 'remotion';
import type {Book, ChartFacts} from './bundle.ts';
import type {Copy} from './copy.ts';
import {coverUrl} from './facts.ts';
import {DASH, countryLabel, digits, genreLabel, languageLabel, moveLabel, priceLine, publishedLabel} from './format.ts';
import {BG, CARD, FONT, GREEN, INK, MUTED, RED, RULE, SCRIM, SLIDE} from './palette.ts';

/**
 * **The slide: one book, and the four registers it has to fill** (ticket 07).
 *
 * ```
 * ┌──────────────────────────────────────────────────────────────────────┐
 * │  TOP 100 BENGALI BOOKS · WEEK 41        ┌─────────────────────────┐  │  header = which chart
 * │                                         │  reserved mark 260×160  │  │
 * │                                         └─────────────────────────┘  │
 * │   ┌──────────────┐    7   ▲ 3                                        │
 * │   │              │   ───────────────────────────────                 │  main = the book
 * │   │    COVER     │   Ekti Shonar Boi                                 │
 * │   │   (34 %)     │   Sunil Gangopadhyay · Ananda Publishers           │
 * │   └──────────────┘   ₹399 · Amazon · paperback · Oct 2026            │
 * │  ────────────────────────────────────────────────────────────────    │  ticker = the world
 * │  Sources: … · Ranked by … · window: 7 weeks                          │  footer = how we know
 * └──────────────────────────────────────────────────────────────────────┘
 * ```
 *
 * ⚠️ **One idea per register, and that is the layout's whole argument.** A slide carrying a chart's name, a book's
 * position, the market behind it and the basis it rests on reads as four questions rather than one — so each register
 * answers exactly one of them, and the header is the only place the chart's own name appears.
 *
 * ⚠️ **The entrance is handed in as frames** (`enterFrames`, off the block) and never computed here. Ticket 07's
 * `span = min(0.4, dwell × 0.15)` is a *data* decision: a 1.0 s tail slide may spend 0.15 s arriving, where the host
 * repo's 0.4 s default would have spent **40 % of the only time there is to read a publisher**.
 */
export const Slide = ({
  book,
  facts,
  copy,
  lang,
  week,
  enterFrames,
  ticker,
  labels,
}: {
  book: Book;
  facts: ChartFacts;
  copy: Copy;
  lang: string;
  week: string;
  enterFrames: number;
  ticker: React.ReactNode;
  /** ⚠️ Ticket 20 — which of the two labels this **chart** draws. Decided once in `BooksBrief`, because it is a fact
   * about the run rather than about the row: either the country varies across the chart or it does not. */
  labels: {readonly country: boolean; readonly language: boolean};
}) => {
  const frame = useCurrentFrame();

  // ⚠️ Motion fits *inside* the reading window and never consumes it. The ceiling is already applied — `enterFrames`
  // arrived from the block — so this only has to not run long.
  const limit = Math.max(1, enterFrames);
  const arrived = Math.min(Math.max(frame, 0), limit) / limit;

  const move = moveLabel(book, lang);
  const published = publishedLabel(book.published);
  const best = book.price.retailers.length > 1 && book.price.amount !== null;

  // ⚠️ **The detail line's parts, in the order the reader meets them**: the book's own genre, then where and in what
  // language the list that ranked it was, then the source's own date.
  //
  // ⚠️ **Built as a list and joined, rather than written as a chain of `{part ? <span>·</span> : null}`** — which is what
  // this line used to be. With one optional item that shape is fine; with three it leaves a dangling separator the
  // moment a middle one is absent, and nothing in a test looks at a separator. ⚠️ Ticket 07's rule is that a missing
  // field **omits without leaving a hole**, and a list that is joined cannot leave one by construction.
  const parts = [
    genreLabel(book.genre, copy),
    labels.country ? countryLabel(book.country, copy) : null,
    labels.language ? languageLabel(book.language, copy) : null,
    published,
  ].filter((part): part is string => part !== null && part !== '');

  return (
    <AbsoluteFill
      style={{
        background: SCRIM,
        color: INK,
        fontFamily: FONT,
        padding: CARD.padding,
        display: 'flex',
        flexDirection: 'column',
        // ⚠️ The entrance is on the **whole register**, not per element: four things arriving at four moments would
        // read as four slides rather than one.
        opacity: arrived,
        transform: `translateY(${(1 - arrived) * 22}px)`,
      }}
    >
      {/* ── header: which chart ────────────────────────────────────────────────────────────────────────────── */}
      <header style={{display: 'flex', alignItems: 'baseline', gap: 20, minHeight: 56, marginBottom: 12}}>
        <div style={{fontSize: SLIDE.header, letterSpacing: '0.14em', fontWeight: 600}}>
          {`TOP ${digits(facts.ranked.length, lang)} ${copy.charts[facts.label_key] ?? facts.label_key}`}
        </div>
        <div style={{fontSize: SLIDE.header, letterSpacing: '0.14em', color: MUTED}}>
          {/* ⚠️ The week number is one of ticket 27's four Bengali-numeral fields. */}
          {`${copy.week} ${digits(week.split('-W')[1] ?? week, lang)}`}
        </div>
      </header>

      {/* ── main: the book ─────────────────────────────────────────────────────────────────────────────────── */}
      <main style={{flex: 1, minHeight: 0, display: 'flex', gap: 64, alignItems: 'center'}}>
        <Cover book={book} />

        <div style={{flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
          {/* ⚠️ **The one dominant element.** The brief's cards top out at a 46 px title; a slide whose subject is a
              book's *position in a chart* has to say that position loudest, so 220 is the anchor everything defers to. */}
          <div style={{display: 'flex', alignItems: 'baseline', gap: 32}}>
            <div
              style={{
                fontSize: SLIDE.rank,
                fontWeight: SLIDE.rankWeight,
                lineHeight: 1,
                fontVariantNumeric: 'tabular-nums',
              }}
            >
              {digits(book.rank, lang)}
            </div>
            <div
              style={{
                fontSize: SLIDE.detail,
                fontWeight: 600,
                // ⚠️ Coloured by **meaning**: a NEW entry is neutral (it has no direction to report), a climb is green
                // and a slip is red. `tone()`'s job in the brief, done here on the label rather than on a number.
                color: book.is_new ? MUTED : move === null ? MUTED : move.startsWith('▲') ? GREEN : RED,
              }}
            >
              {/* ⚠️ Ticket 07 — **NEW replaces the Δ slot.** Never a blank Δ, and never `▲0`. */}
              {book.is_new ? copy.new : (move ?? DASH)}
            </div>
          </div>

          <div style={{height: 2, background: RULE, margin: '26px 0 30px'}} />

          {/* ⚠️ A title that will not fit is a title to shorten — the **full** one survives in the description
              (ticket 15), which is what makes clamping honest rather than lossy. Two lines, then clipped. */}
          <div
            style={{
              fontSize: SLIDE.title,
              fontWeight: 700,
              lineHeight: 1.15,
              letterSpacing: '-0.01em',
              maxWidth: '92%',
              display: '-webkit-box',
              WebkitLineClamp: SLIDE.titleLines,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}
          >
            {book.title || DASH}
          </div>

          {/* ⚠️ One line, ellipsised — Amazon.in really does say *"Multiple Writers"*, and a long list must not push
              the price off the slide. */}
          <div
            style={{
              fontSize: SLIDE.author,
              color: MUTED,
              marginTop: 18,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {[book.author, book.publisher].filter(Boolean).join(' · ') || DASH}
          </div>

          <div style={{fontSize: SLIDE.detail, marginTop: 26, display: 'flex', alignItems: 'baseline', gap: 14}}>
            {/* ⚠️ Ticket 04 — the word "best" is printed **only** when more than one retailer was consulted. One
                listing is not a comparison, and the count that decides it was computed in Python. */}
            {best ? (
              <span style={{color: MUTED, fontSize: SLIDE.label, letterSpacing: '0.1em'}}>{copy.best}</span>
            ) : null}
            <span style={{fontVariantNumeric: 'tabular-nums'}}>{priceLine(book.price, copy, lang)}</span>
          </div>

          <div style={{fontSize: SLIDE.detail, color: MUTED, marginTop: 14}}>
            {/* ⚠️ **Ticket 26's genre always draws** (it varies on every chart), and **ticket 20's two draw only where
                the chart disagrees with itself** — see `varies`. ⚠️ Joined from a list, so a label that is not drawn
                cannot leave its separator behind: *Poetry · 14 Oct 2026* rather than *Poetry ·  · 14 Oct 2026*. */}
            {parts.join(' · ')}
          </div>
        </div>
      </main>

      {/* ── the world ──────────────────────────────────────────────────────────────────────────────────────── */}
      {ticker}

      {/* ── how we know ────────────────────────────────────────────────────────────────────────────────────── */}
      <footer
        style={{
          borderTop: `1px solid ${RULE}`,
          paddingTop: 16,
          display: 'flex',
          justifyContent: 'space-between',
          gap: 32,
          fontSize: CARD.footer,
          color: MUTED,
        }}
      >
        <div>{copy.disclosure}</div>
        <div style={{whiteSpace: 'nowrap'}}>
          {[copy.markets[facts.market] ?? facts.market, copy.attribution].join(' · ')}
        </div>
      </footer>
    </AbsoluteFill>
  );
};

/**
 * ⚠️ **The missing cover is a designed state, not a hole** (ticket 07).
 *
 * A book with no cover gets a **branded tile** — its own initial on `BG` with a `RULE` border — and never a blank white
 * box, which is the one thing the ticket forbids. ⚠️ And it is the same tile the collage uses (ticket 16), so the two
 * surfaces agree instead of each inventing a placeholder.
 *
 * ⚠️ **The `Img` is only reached when the row says a cover exists**, because `stage.covers` writes a file only for a row
 * that has one — so a broken image is structurally impossible rather than merely unlikely.
 *
 * ⚠️ `aspectRatio: 2 / 3` rather than a fixed height: a cover is a portrait object, and sizing the column to the frame's
 * height would letterbox every one of them.
 */
const Cover = ({book}: {book: Book}) => (
  <div
    style={{
      // ⚠️ **Constrained by the height as well as the width, and the first render is why.** A `width: 34%` box with a
      // 2:3 ratio derives its height *from its width* — so with the ticker band absent (ticket 08's documented
      // degrade) `main` grew taller than the cover needed and the cover **overlapped the footer rule**. Pinning the
      // height to the row and capping the width keeps the ratio honest in both directions.
      height: '100%',
      maxWidth: `${SLIDE.cover * 100}%`,
      aspectRatio: '2 / 3',
      flexShrink: 0,
      borderRadius: 14,
      overflow: 'hidden',
      background: BG,
      border: `1px solid ${RULE}`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}
  >
    {book.cover ? (
      <Img src={coverUrl(book.isbn)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
    ) : (
      <span style={{fontSize: 140, fontWeight: 700, color: MUTED}}>
        {(book.title.trim()[0] ?? '?').toUpperCase()}
      </span>
    )}
  </div>
);
