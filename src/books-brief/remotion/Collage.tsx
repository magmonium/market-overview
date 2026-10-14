import {AbsoluteFill, Img} from 'remotion';
import type {Book, ChartFacts} from './bundle.ts';
import type {Copy} from './copy.ts';
import {coverUrl} from './facts.ts';
import {digits} from './format.ts';
import {BG, FONT, INK, MUTED, RULE} from './palette.ts';

/**
 * **The collage: all hundred covers, and only the top few legible** (ticket 16).
 *
 * ```
 * ┌──────────────────────────────────────────────────────────────┐
 * │ TOP 100 BENGALI BOOKS                    ┌─────────────────┐ │
 * │ WEEK 41 · 14 OCT 2026                    │  mark @ 128 px  │ │
 * │                                          └─────────────────┘ │
 * │    ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐              │
 * │    │  1   │ │  2   │ │  3   │ │  4   │ │  5   │   ← hero row │
 * │    └──────┘ └──────┘ └──────┘ └──────┘ └──────┘              │
 * │  ░░░ mosaic of the remaining 95, dimmed to a texture ░░░░░░  │
 * │                       [ duration badge ] [ progress bar ]    │
 * └──────────────────────────────────────────────────────────────┘
 * ```
 *
 * ⚠️ **The brief asked for *"a collage of all the books"*, and the medium says no — so the resolution is not to drop
 * either.** At the **210 px** a feed shows this at, a 10×10 grid gives each cover **21 px**: a colour swatch, not a
 * cover. So all hundred appear and only the top five are legible — the mosaic is the *texture*, and it is honest,
 * because every one of the hundred is genuinely in it.
 *
 * ⚠️ **320×180 is the wrong number and this file does not use it.** Ticket 16 asked about legibility at 320×180; the
 * brief's own still has the real figure and it is **measured**: the frame is 1280×720 and *"the feed shows it at
 * **210 px** wide."* That is the size every decision here is judged at.
 *
 * ⚠️ **The mosaic ends above YouTube's chrome.** The platform owns the **bottom-right** (duration badge) and the
 * **bottom strip** (progress bar), so the band stops short of both — and the mark stays top-right at issue 21's *still*
 * size rather than the video's.
 */
const HERO = 5;
/** ⚠️ Dimmed to a **texture**, and the number is the whole idea: at full strength the mosaic competes with the hero row
 * and the thumbnail stops having a subject. */
const MOSAIC = 0.3;
/** ⚠️ YouTube's bottom strip and duration badge. The mosaic ends above this, not under it. */
const CHROME = 64;

export const Collage = ({
  facts,
  copy,
  week,
  published,
}: {
  facts: ChartFacts;
  copy: Copy;
  week: string;
  published: string;
}) => {
  const hero = facts.ranked.slice(0, HERO);
  const rest = facts.ranked.slice(HERO);

  return (
    <AbsoluteFill style={{background: BG, color: INK, fontFamily: FONT, padding: 40}}>
      {/* ── the title: 3-6 words and one idea (ticket 16) ──────────────────────────────────────────────────── */}
      <div style={{position: 'absolute', left: 40, top: 40, right: 200}}>
        <div style={{fontSize: 52, fontWeight: 700, letterSpacing: '-0.01em'}}>
          {`TOP ${digits(facts.ranked.length, facts.language)} ${copy.charts[facts.label_key] ?? facts.label_key}`}
        </div>
        <div style={{fontSize: 28, color: MUTED, marginTop: 8, letterSpacing: '0.08em'}}>
          {`${copy.week} ${digits(week.split('-W')[1] ?? week, facts.language)} · ${published}`}
        </div>
      </div>

      {/* ── the hero row: the five a viewer can actually read ──────────────────────────────────────────────── */}
      <div style={{position: 'absolute', left: 40, right: 40, top: 168, display: 'flex', gap: 18}}>
        {hero.map((book) => (
          <div key={book.isbn} style={{flex: 1, aspectRatio: '2 / 3', borderRadius: 10, overflow: 'hidden', border: `1px solid ${RULE}`}}>
            <Tile book={book} />
          </div>
        ))}
      </div>

      {/* ── the mosaic: the other ninety-five, as a colour field ───────────────────────────────────────────── */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 470,
          bottom: CHROME,
          display: 'grid',
          // ⚠️ **Nineteen columns, so ninety-five tiles fill five exact rows.** A ragged last row would read as missing
          // covers rather than as a grid — and the count is *known* here (`ranked.length`), so there is nothing to
          // guess: a chart with fewer rows simply fills fewer.
          gridTemplateColumns: 'repeat(19, 1fr)',
          gap: 2,
          opacity: MOSAIC,
          overflow: 'hidden',
        }}
      >
        {rest.map((book) => (
          <Tile key={book.isbn} book={book} />
        ))}
      </div>
    </AbsoluteFill>
  );
};

/**
 * ⚠️ **The same branded tile the slide uses** (ticket 07) — the book's initial on `BG` with a `RULE` border — so the two
 * surfaces agree instead of each inventing a placeholder. ⚠️ Never a blank box, never a stock *"no image"* glyph.
 *
 * ⚠️ The `Img` is only reached when the row says a cover exists, because `stage.covers` writes a file only for a row that
 * has one — so a broken tile is structurally impossible rather than merely unlikely.
 */
const Tile = ({book}: {book: Book}) => (
  <div
    style={{
      width: '100%',
      height: '100%',
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
      <span style={{fontSize: 28, fontWeight: 700, color: MUTED}}>
        {(book.title.trim()[0] ?? '?').toUpperCase()}
      </span>
    )}
  </div>
);
