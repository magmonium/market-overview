/**
 * The snapshot's shape, as this layer reads it — **the sole interface** (ADR 0003).
 *
 * ⚠️ **Every field here is a *value*, and this file is where that stops being a slogan.** `genre` is a slug,
 * `identity` is a state, `published` is the source's own string and `retailer` is a vendor slug — the words a viewer
 * reads are in `copy.ts`, because a display string committed to the snapshot is a string that cannot be re-worded
 * without re-running the week.
 *
 * ⚠️ **Written by hand against `books_brief/facts.py`, and it is the one place the two languages meet.** The bundle is
 * JSON, so nothing checks this file but `tsc` and a render — which is why the Python side asserts the serialised
 * shape field by field (`tests/test_facts.py`) rather than trusting the dataclass.
 */

/** ⚠️ What the slide is allowed to say, and nothing more (ticket 04). `retailers` is the **count consulted**. */
export type Price = {
  readonly amount: number | null;
  readonly retailer: string | null;
  readonly edition: string | null;
  readonly retailers: readonly string[];
  /**
   * ⚠️ **The currency the amount is denominated in** — `INR`, `USD`, `BDT` — and the reason it is a *value* rather
   * than something this layer decides (ADR 0003).
   *
   * ⚠️ **It is not a detail.** The English chart is a **US** list (ticket 19) and the Bengali chart spans **India and
   * Bangladesh** (ticket 20), so `24.99` and `৳180` and `₹180` all occur — and rendering one as another is wrong by a
   * factor of eighty or of one and a half, while looking entirely correct.
   *
   * ⚠️ **Empty means *unknown*, and unknown draws no symbol** — see `format.money`. A default of `INR` here would make
   * a missing currency quietly assert rupees, which is the failure the field exists to prevent.
   */
  readonly currency: string;
};

/** ⚠️ The URL and the hash — the evidence, not the bytes (ticket 05). */
export type Cover = {readonly url: string; readonly sha256: string};

/** One row of the chart — ticket 07's eight fields, flat. */
export type Book = {
  readonly isbn: string;
  readonly rank: number;
  readonly weeks_on_chart: number;
  readonly is_new: boolean;
  /**
   * ⚠️ The Δ, positive for a climb — **`null` for two different reasons the slide must treat the same**: week one
   * (ticket 18 — the row is a stated baseline) and a title absent from last week (ticket 07 — NEW *replaces* the Δ
   * slot). ⚠️ Never `0`, which would claim the title held station.
   */
  readonly move: number | null;
  readonly title: string;
  readonly author: string;
  readonly publisher: string;
  /**
   * ⚠️ **The source's own string** — `2026-10-14`, `2026-10` or `2026` — never a label. Ticket 05 §2 wants *"the
   * precision that exists"* rendered, and that is `format.ts`'s job: the year-only case prints a year, and the
   * committed evidence never carries an English month name.
   */
  readonly published: string | null;
  readonly genre: string;
  /**
   * ⚠️ **Ticket 20's two labels, and they are *values* like everything else here** — `in`, `bd`, `bn`, `hi`. The words
   * are `copy.ts`'s, which is what lets *India* become *ভারত* without re-running a week.
   *
   * ⚠️ **They are properties of the *list* the title ranked on, not of the chart** — the Bengali chart spans India and
   * Bangladesh, and the all-language chart is nine Amazon.in lists in one country and nine languages. ⚠️ And an **empty
   * string is a real answer**: *this list declared neither*, which the slide reads as *no label* — the same state as a
   * label that does not vary (ticket 20).
   */
  readonly country: string;
  readonly language: string;
  readonly price: Price;
  readonly identity: 'resolved' | 'unresolved';
  readonly cover: Cover | null;
};

/**
 * One slot in the run, **in frames** — and the renderer holds no table of its own.
 *
 * ⚠️ **`enterFrames` rides on the block rather than being recomputed here**, which is ticket 07's span ceiling
 * (`min(0.4, dwell × 0.15)`) expressed once, in Python, and handed over. The brief's own rule, and the reason this
 * layer has no `dwell.ts`: *"the timeline comes from `props.timeline`, not from this file."*
 */
export type Block = {
  readonly id: string;
  readonly key: 'intro' | 'book' | 'outro';
  /** ⚠️ `start`, not `from` — `from` is a Python keyword, and this is the same number. */
  readonly start: number;
  readonly duration: number;
  readonly enter_frames: number;
  /** ⚠️ `null` on the intro and the outro: they show **no book**, and a `0` would index the first one. */
  readonly rank: number | null;
};

export type Timeline = {
  readonly fps: number;
  readonly cap_seconds: number;
  readonly total_frames: number;
  readonly blocks: readonly Block[];
};

export type ChartFacts = {
  /**
   * ⚠️ The chart's own identity, as **slugs** — the words are `copy.ts`'s (ADR 0003).
   *
   * ⚠️ These three are the ones easiest to leave out of this file, because the *Python* side grew them after the
   * interface was written: `facts.py` reads them off `charts.ALL`. They are here because a renderer that could not name
   * the chart it was drawing, or the market it ranks, would have to hold its own copy of `charts.py` — and the copy
   * that fell behind would be the one that shipped.
   */
  readonly label_key: string;
  /** ⚠️ Which label table the slide is set in (ticket 27). */
  readonly language: string;
  /** ⚠️ The market, **stated** (tickets 19, 21, 22) — the Bengali chart spans India *and* Bangladesh. */
  readonly market: string;
  readonly ranked: readonly Book[];
  readonly watchlist: readonly string[];
  /** ⚠️ Ticket 05 §4 — *"97/100 covers"*, so ticket 16's collage rule has a number rather than a surprise. */
  readonly cover_coverage: number;
  readonly timeline: Timeline;
};

/**
 * ⚠️ One index, as the band reads it — **values only** (ADR 0003).
 *
 * ⚠️ **`close` and `change` are numbers, not formatted strings, and this file got that wrong first.** A `"24,812"`
 * written into the snapshot is a display string in the committed evidence: it cannot be re-grouped for another locale,
 * it cannot be re-coloured by sign, and it cannot be re-worded without re-running the week. ⚠️ `label_key` is the
 * **brief's** slug (`nifty50`, not `NSE:NIFTY`) so a vendor renaming a ticker is a one-line change in a label table.
 */
export type TickerRow = {
  readonly label_key: string;
  readonly close: number | null;
  readonly change: number | null;
};

/**
 * ⚠️ The market band (ticket 08) — **absent is a designed state, not a missing one.**
 *
 * It is fetched through the brief's own `fetch/tradingview` client and snapshotted with the week, so a *failed* fetch
 * leaves it out entirely: *never zeros, never stale, never a placeholder*. That is why this is optional rather than
 * required-with-a-default — no key at all and an empty `rows` mean the same thing to the renderer, and both mean the
 * band does not draw.
 */
export type Ticker = {
  readonly rows: readonly TickerRow[];
  /** ⚠️ The **session** the numbers describe, as an ISO date — *"a ticker that cannot say when it is from is a ticker
   * that can lie."* A `null` here means no band at all: Python omits the whole thing rather than shipping an undated
   * one, so this is only ever `null` in a hand-written bundle. */
  readonly as_of: string | null;
};

export type FactsBundle = {
  readonly meta: {
    readonly schema: number;
    readonly week: string;
    /** ⚠️ Ticket 03's rule version, so a re-run of an old week reproduces the **old** chart. */
    readonly chart_logic: number;
    /** ⚠️ The window the chart **has**, not the six months it aspires to (ticket 23). */
    readonly window_weeks: number;
  };
  /** ⚠️ A chart whose sources failed is an **absent key**, never an empty one (ticket 13). */
  readonly charts: Readonly<Record<string, ChartFacts>>;
  /**
   * ⚠️ Ticket 08's band — **omitted when the fetch failed**, and never defaulted to zeros.
   *
   * ⚠️ It rides at the **bundle** root rather than per chart, because *"the index scoreboard is not chart-specific, so
   * it is fetched once and rendered into all four"* (ticket 13).
   */
  readonly ticker?: Ticker | null;
};

/**
 * The operator's mark, as `logo.load` returned it — inlined as a data URI with its chip fill already derived.
 * `null` when they have not supplied one, which is a **valid brief** rather than a broken one.
 */
export type Mark = {readonly src: string; readonly chip: string} | null;
