import type {Book, Price} from './bundle.ts';
import {MONTHS, type Copy} from './copy.ts';

/**
 * Values into the words on the slide — **the last step of ADR 0003, and the one that makes the snapshot re-wordable.**
 *
 * ⚠️ **Every function here takes a *value* and returns a *string*.** `published: "2026-10"` becomes *"Oct 2026"*; a
 * `genre` slug becomes a genre; a retailer slug becomes a shop. None of that is in the committed evidence, which is why
 * a week built last year can be re-rendered with today's words.
 *
 * ⚠️ **Nothing here decides anything.** The "best" prefix is printed only when `price.retailers.length > 1`, but that
 * *count* was computed by `prices.best` in Python — this layer reads the answer rather than re-deriving it (ticket 04).
 */

/** ⚠️ The Bengali chart's data numerals (ticket 27), and the same table `song-video`'s `caption.DIGITS` fixes in one
 * place for the reel's caption. */
const BENGALI = ['০', '১', '২', '৩', '৪', '৫', '৬', '৭', '৮', '৯'] as const;

/** ⚠️ U+2212 for a minus, so it is not a hyphen sitting next to a digit. */
export const MINUS = '\u2212';
/** The absence of a value — **never a zero** (tickets 04, 07). */
export const DASH = '\u2014';
/** A title that genuinely did not move. ⚠️ Not the same as `move === null`, which means *no comparison exists*. */
export const HELD = '\u2013';

/**
 * ⚠️ **Rank, price, Δ and the week number use the script's own numerals on the Bengali chart** (ticket 27) — the same
 * split `song-video` makes, where the caption counts in `০১২৩৪৫৬৭৮৯`.
 */
export const digits = (value: string | number, lang: string): string => {
  const text = String(value);
  if (lang !== 'bn') {
    return text;
  }
  return text.replace(/[0-9]/g, (digit) => BENGALI[Number(digit)] ?? digit);
};

/**
 * ⚠️ **Money is currency-specific in three ways, and the first version of this file knew about none of them.**
 *
 * 1. ⚠️ **The symbol** — `₹`, `$`, `৳`.
 * 2. ⚠️ **The grouping** — ₹1,29,900 is a lakh-grouped Indian number and `$129,900` is not, and a dollar figure grouped
 *    the Indian way reads as a typo to the reader it is for.
 * 3. ⚠️ **The minor unit** — an Indian book price is a whole number of rupees, and a US one is **`$24.99`**. The old
 *    `rupees()` rounded unconditionally, which is right for ₹399 and turns a dollar price into `$25`.
 *
 * ⚠️ **The comment that used to sit here said *"because the charts are India-anchored (ticket 12)"*** — the same
 * superseded premise `prices.CURRENCY` carried in Python, in a second language and a second file. ⚠️ Ticket 19 made the
 * English chart **US**, ticket 20 made the Bengali chart span **India and Bangladesh**, and ticket 22 made comics
 * **worldwide** — so "India-anchored" stopped being true three tickets before anyone changed a line of code.
 *
 * ⚠️ **An unknown currency draws no symbol rather than a wrong one.** A price whose denomination the evidence does not
 * state is a price the slide may print as a bare number; it is never one it may label with the wrong sign.
 */
const MONEY: Readonly<Record<string, {symbol: string; locale: string; places: number}>> = {
  INR: {symbol: '₹', locale: 'en-IN', places: 0},
  USD: {symbol: '$', locale: 'en-US', places: 2},
  // ⚠️ Bangladeshi Taka: the ৳ sign and whole-number pricing, like the rupee — but grouped the Western way, because a
  // Taka price is not a rupee price and grouping it as one would be a second wrongness on top of the first.
  BDT: {symbol: '৳', locale: 'en-US', places: 0},
};

/** ⚠️ The amount and its currency into the string the slide prints — **never the symbol without the currency**. */
export const money = (amount: number | null, currency: string, lang: string): string => {
  if (amount === null) {
    return DASH;
  }

  const spec = MONEY[currency];
  if (!spec) {
    // ⚠️ Unknown currency: the number, no sign, and **no rounding** — the minor unit is the currency's to state, and
    // this one has not. See the table's note: a wrong symbol is worse than an absent one because it is *assertive*.
    return digits(amount.toLocaleString('en-US'), lang);
  }

  const shown = amount.toLocaleString(spec.locale, {
    minimumFractionDigits: spec.places,
    maximumFractionDigits: spec.places,
  });
  return `${spec.symbol}${digits(shown, lang)}`;
};

/**
 * ⚠️ Ticket 07's rule, and `null` is what the slide keys off: **NEW replaces the Δ slot.**
 *
 * ⚠️ **Three cases, and `null` is two of them.** `is_new` means there is nothing to compare against; `move === null`
 * on an incumbent means week one, where ticket 18 rules that *"every row carries no Δ"*. Both leave the slot empty, and
 * neither prints `▲0` — which would claim the title held station.
 */
export const moveLabel = (book: Book, lang: string): string | null => {
  if (book.is_new || book.move === null) {
    return null;
  }
  if (book.move === 0) {
    return HELD;
  }
  const arrow = book.move > 0 ? '▲' : '▼';
  return `${arrow} ${digits(Math.abs(book.move), lang)}`;
};

/**
 * ⚠️ Ticket 05 §2 — *"render the precision that exists."*
 *
 * | Source gives | Prints |
 * |---|---|
 * | `2026-10-14` | 14 Oct 2026 |
 * | `2026-10` | Oct 2026 |
 * | `2026` | 2026 |
 * | anything else | **omitted** — never guessed, never blank-filled |
 *
 * ⚠️ **Unparseable is `null`, not a best effort.** Ticket 03 requires a week to be replayable, and a guess is not
 * replayable: the same snapshot could render a different label after a library upgrade. ⚠️ And the bounds are checked
 * rather than indexed — `2026-13-45` would otherwise reach `MONTHS[12]` and print `undefined` onto a slide.
 */
export const publishedLabel = (raw: string | null): string | null => {
  if (!raw) {
    return null;
  }

  const full = /^(\d{4})-(\d{2})-(\d{2})$/.exec(raw);
  if (full) {
    const month = Number(full[2]);
    const day = Number(full[3]);
    if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
      return `${day} ${MONTHS[month - 1]} ${full[1]}`;
    }
    return null;
  }

  const month = /^(\d{4})-(\d{2})$/.exec(raw);
  if (month) {
    const index = Number(month[2]);
    return index >= 1 && index <= 12 ? `${MONTHS[index - 1]} ${month[1]}` : null;
  }

  return /^\d{4}$/.test(raw) ? raw : null;
};

/**
 * ⚠️ **Ticket 04's governing rule: never label a price "best" unless it was actually compared.**
 *
 * The count is Python's (`price.retailers`), so this only has to read it. One retailer means there was no comparison to
 * make — the slide names the shop and stops, because *"Best price ₹399"* off a single listing claims something nobody
 * checked.
 */
export const priceLine = (price: Price, copy: Copy, lang: string): string => {
  const parts = [money(price.amount, price.currency, lang)];
  if (price.retailer) {
    parts.push(copy.retailers[price.retailer] ?? price.retailer);
  }
  if (price.edition) {
    parts.push(price.edition);
  }
  return parts.join(' · ');
};

/** ⚠️ **Only when there is a comparison to name.** See `priceLine`. */
export const bestPrefix = (price: Price, copy: Copy): string | null =>
  price.retailers.length > 1 && price.amount !== null ? copy.best : null;

/** ⚠️ A plain `en-IN` number, tabular — used by the market band. See `percent` for the sign rule. */
export const number = (value: number | null, lang: string, places = 2): string =>
  value === null
    ? DASH
    : digits(value.toLocaleString('en-IN', {maximumFractionDigits: places}), lang);

/** ⚠️ A percentage with U+2212 for a minus, so it is not a hyphen sitting next to a digit. */
export const percent = (value: number | null, lang: string, places = 2): string =>
  value === null
    ? DASH
    : `${value >= 0 ? '+' : MINUS}${digits(Math.abs(value).toFixed(places), lang)}%`;

/**
 * ⚠️ A slug the label table does not know prints as itself rather than as `undefined` — `genre.slug_for` can only
 * produce the fourteen slugs, but a vocabulary that grows should degrade visibly rather than silently. */
export const genreLabel = (slug: string, copy: Copy): string => copy.genres[slug] ?? slug;

/**
 * ⚠️ **Ticket 20's rule, as one function: a label shows only where it varies.**
 *
 * ⚠️ **A label that says the same thing on all 100 rows is not information.** The header already says *BENGALI BOOKS*,
 * so *Bengali* under every title is decoration that costs a line of the book's own detail — and on the English chart
 * neither label appears at all, which ticket 19 calls *the rule working* rather than a gap.
 *
 * ⚠️ **Counted over distinct *non-empty* values, and two is the threshold.** Zero means no list declared one; one means
 * it is constant; only from two does the label carry a fact the reader could not have guessed. ⚠️ **Empty is filtered
 * rather than counted** — otherwise one unlabelled row among ninety-nine Indian ones would make the country "vary" and
 * print *India* a hundred times.
 */
export const varies = (values: readonly string[]): boolean =>
  new Set(values.filter((value) => value !== '')).size > 1;

/**
 * ⚠️ **A code the table does not know prints as itself rather than as `undefined`** — the same degrade `genreLabel`
 * keeps, and for the same reason: a vocabulary that grows should look wrong visibly rather than silently.
 */
export const countryLabel = (code: string, copy: Copy): string => copy.countries[code] ?? code;

/** ⚠️ The same rule for ticket 20's second label. See `countryLabel`. */
export const languageLabel = (code: string, copy: Copy): string => copy.languages[code] ?? code;

/**
 * The **Monday of an ISO week**, spelled out — `2026-W41` → `5 OCT 2026`.
 *
 * ⚠️ **Derived from the key, never from a clock.** ADR 0003 rests on a re-render producing identical frames, and
 * `new Date()` would make the still's own date a property of *when it was rendered* rather than of the week it
 * describes — so two renders of one week could disagree, which is exactly the drift the snapshot exists to prevent.
 *
 * ⚠️ **UTC throughout**, for the same reason the brief's own `dates.ts` gives: a render on a machine an hour either side
 * of midnight must produce the same label.
 *
 * ⚠️ The **4th of January is always in week 1** — that is what makes this arithmetic rather than a table of years.
 */
export const isoMondayLabel = (week: string): string => {
  const [year, number] = week.split('-W');
  const jan4 = new Date(Date.UTC(Number(year), 0, 4));
  const weekday = jan4.getUTCDay() || 7;
  const monday = new Date(jan4);
  monday.setUTCDate(jan4.getUTCDate() - weekday + 1 + (Number(number) - 1) * 7);
  return `${monday.getUTCDate()} ${MONTHS[monday.getUTCMonth()].toUpperCase()} ${monday.getUTCFullYear()}`;
};

