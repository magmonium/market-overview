/**
 * The words a viewer reads — **and they live here, not in the snapshot** (ADR 0003).
 *
 * ⚠️ **This is the half of ADR 0003 that is easy to skip.** The bundle carries `label_key: 'bengali'`; this file turns
 * it into *"BENGALI BOOKS"*. The payoff is concrete rather than theoretical: re-wording a chart is a copy change, and
 * **a week committed last year re-renders with today's words** — because the words were never in its evidence.
 *
 * ⚠️ **Two tables, chosen by the chart's own `language`.** Ticket 27's split: *"the title is the product's; the slide
 * is the reader's."* The Bengali chart's slide is set for a Bengali reader; its YouTube title is not, and that string
 * lives in `books_brief/metadata.py` where search — not reading — is the audience.
 */

/** ⚠️ The month names, and they are **Latin in both tables** — deliberately, and worth stating.
 *
 * Ticket 27 named exactly four things as Bengali numerals — *"rank, price, Δ and the week number"* — and the month is
 * not one of them. Half-converting a date (a Bengali year beside a Latin month) reads worse than leaving it alone, so
 * the whole label stays Latin rather than the year drifting away from its own month. Recorded here so it is a visible
 * decision rather than an oversight.
 */
export const MONTHS = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
] as const;

/** The disclosure register's two lines — the footer, and the reason it is always on screen (ticket 07). */
export type Copy = {
  /** ⚠️ The chart's own name, by its **stable slug** — never the display text (ADR 0003). */
  readonly charts: Readonly<Record<string, string>>;
  /** ⚠️ Tickets 19, 21, 22 — the market, as a sentence. The chart has to **state** what it ranks. */
  readonly markets: Readonly<Record<string, string>>;
  /** The word before the week number in the header. */
  readonly week: string;
  /** ⚠️ Ticket 07 — the badge that **replaces** the Δ slot. Never a blank Δ, never `▲0`. */
  readonly new: string;
  /** ⚠️ Ticket 04 — only ever printed when `price.retailers.length > 1`. */
  readonly best: string;
  /** ⚠️ The retailer's **slug** is in the snapshot; its name is a word, so it is here (ADR 0003). */
  readonly retailers: Readonly<Record<string, string>>;
  /** ⚠️ Ticket 26 — the genre is a **slug** in the snapshot and a word here, which is what makes renaming one a copy
   * change rather than a data migration. */
  readonly genres: Readonly<Record<string, string>>;
  /** ⚠️ Ticket 20 — an ISO 3166-1 code to a word. The snapshot carries `in`; the reader gets *India*. ⚠️ A **proper
   * noun**, so the Bengali table spells it in Bengali script rather than transliterating — the same split `markets`
   * already makes for *India & Bangladesh*. */
  readonly countries: Readonly<Record<string, string>>;
  /** ⚠️ Ticket 20 — an ISO 639-1 code to the language's **own name, in this table's script**. ⚠️ Not the vendor's word
   * for its list: `charts.INDIAN_LANGUAGES` pairs `english` with `en`, and only the code reaches the snapshot. */
  readonly languages: Readonly<Record<string, string>>;
  /** The label on the ticker band. */
  readonly ticker: string;
  /** ⚠️ The **brief's own slugs** — `nifty50`, not `NSE:NIFTY` — so a vendor renaming a ticker is a change here and
   * not a data migration. The vendor's symbol never reaches the snapshot (ticket 08). */
  readonly indices: Readonly<Record<string, string>>;
  readonly disclosure: string;
  readonly attribution: string;
  /** ⚠️ The footnote a stated baseline carries (ticket 18) — *"a baseline that looked like a normal week would be
   * indistinguishable from one."* */
  readonly baseline: string;
};

export const EN: Copy = {
  charts: {
    bengali: 'BENGALI BOOKS',
    english: 'ENGLISH BOOKS',
    'all-language': 'INDIAN BOOKS (ALL LANGUAGES)',
    comics: 'COMICS',
  },
  markets: {
    'india+bangladesh': 'India & Bangladesh',
    // ⚠️ **`us` is kept even though no chart declares it any more** (2026-10-15): the English chart's market is now
    // `worldwide`, but a week committed before the change still carries `us`, and ADR 0003's promise is that a past week
    // re-renders with **today's words** (ticket 18). Removing the key would blank the footer of every old week.
    us: 'US lists',
    india: 'India',
    // ⚠️ The Bengali chart's market as of ticket 29: Anandabazar could not be declared, so the chart ranks one
    // Bangladeshi list.
    bangladesh: 'Bangladesh',
    // ⚠️ **The English chart's market as of 2026-10-15** — it reads US, UK, Canadian and Australian lists, so the
    // sentence names no single country. ⚠️ It is shared with the comics chart, which was already `worldwide`.
    worldwide: 'Worldwide',
  },
  week: 'WEEK',
  new: 'NEW',
  best: 'Best',
  // ⚠️ **Every Amazon marketplace is the same shop to a reader** — `amazon.co.uk` is still *Amazon* — so the four
  // international stores added for the English chart (2026-10-15) share the one label. ⚠️ The snapshot keeps the vendor
  // *slug* (`amazon-uk`), which is what makes naming it a copy change rather than a data migration (ADR 0003).
  retailers: {
    'amazon-us': 'Amazon',
    'amazon-uk': 'Amazon',
    'amazon-ca': 'Amazon',
    'amazon-au': 'Amazon',
    'amazon-in': 'Amazon',
    flipkart: 'Flipkart',
  },
  genres: {
    poetry: 'Poetry',
    novel: 'Novel',
    fiction: 'Fiction',
    'non-fiction': 'Non-fiction',
    business: 'Business',
    'self-help': 'Self-help',
    biography: 'Biography',
    history: 'History',
    religion: 'Religion',
    children: "Children's",
    comics: 'Comics',
    academic: 'Academic',
    reference: 'Reference',
    other: 'Other',
  },
  // ⚠️ **The three the English chart added** (2026-10-15): the chart now ranks `us`, `gb`, `ca` and `au` lists, so the
  // country label varies on it for the first time and these are the words it prints. ⚠️ Proper nouns, spelled in Latin
  // here because the table is the English chart's.
  countries: {in: 'India', bd: 'Bangladesh', us: 'US', gb: 'UK', ca: 'Canada', au: 'Australia'},
  languages: {
    hi: 'Hindi',
    bn: 'Bengali',
    ta: 'Tamil',
    mr: 'Marathi',
    ml: 'Malayalam',
    te: 'Telugu',
    kn: 'Kannada',
    gu: 'Gujarati',
    en: 'English',
  },
  ticker: 'Market',
  indices: {
    nifty50: 'NIFTY 50',
    nifty500: 'NIFTY 500',
    banknifty: 'BANK NIFTY',
    sensex: 'SENSEX',
    next50: 'NIFTY NEXT 50',
  },
  disclosure: 'Ranked on sales and reviews over six months',
  attribution: 'Covers: Google Books / Open Library',
  baseline: 'First week — no comparison yet',
};

/**
 * ⚠️ **Authored, not translated** — the reel's rule, and `metadata.py`'s. A Bengali reader's label is not an English
 * label with different letters: the market sentence names two countries, and the disclosure says what the ranking is
 * *of*, which is a different sentence rather than a different alphabet.
 *
 * ⚠️ **The chart names stay Latin even here**, because the header names the **chart** — a product identifier, like the
 * YouTube title — while the slide's data is the reader's. Ticket 27's split, one line up.
 */
export const BN: Copy = {
  charts: {
    bengali: 'BENGALI BOOKS',
    english: 'ENGLISH BOOKS',
    'all-language': 'INDIAN BOOKS (ALL LANGUAGES)',
    comics: 'COMICS',
  },
  markets: {
    'india+bangladesh': 'ভারত ও বাংলাদেশ',
    us: 'মার্কিন তালিকা',
    india: 'ভারত',
    bangladesh: 'বাংলাদেশ',
    worldwide: 'বিশ্বব্যাপী',
  },
  week: 'WEEK',
  new: 'নতুন',
  best: 'সেরা',
  // ⚠️ Brand names, so they stay as they are — a transliterated "অ্যামাজন" would be a *different* name for the same
  // shop, and a reader comparing against their own copy needs to recognise it.
  retailers: {'amazon-in': 'Amazon', flipkart: 'Flipkart'},
  genres: {
    poetry: 'কবিতা',
    novel: 'উপন্যাস',
    fiction: 'কল্পকাহিনি',
    'non-fiction': 'নন-ফিকশন',
    business: 'ব্যবসা',
    'self-help': 'আত্মউন্নয়ন',
    biography: 'জীবনী',
    history: 'ইতিহাস',
    religion: 'ধর্ম',
    children: 'শিশুতোষ',
    comics: 'কমিকস',
    academic: 'পাঠ্যবই',
    reference: 'তথ্যসূত্র',
    other: 'অন্যান্য',
  },
  // ⚠️ Ticket 20 — proper nouns, spelled in Bengali script rather than transliterated. The Bengali chart is the one
  // chart where the country label draws, so this table is the one a reader actually meets.
  countries: {in: 'ভারত', bd: 'বাংলাদেশ', us: 'মার্কিন যুক্তরাষ্ট্র'},
  languages: {
    hi: 'হিন্দি',
    bn: 'বাংলা',
    ta: 'তামিল',
    mr: 'মারাঠি',
    ml: 'মালায়ালাম',
    te: 'তেলুগু',
    kn: 'কন্নড়',
    gu: 'গুজরাটি',
    en: 'ইংরেজি',
  },
  ticker: 'বাজার',
  // ⚠️ Index names are **proper nouns**, so they are the same in both tables — *"NIFTY 50"* is a name, not a
  // description. The word around them is translated (`বাজার`), which is the split ADR 0003 asks for: the slug is
  // data, the label is copy.
  indices: {
    nifty50: 'NIFTY 50',
    nifty500: 'NIFTY 500',
    banknifty: 'BANK NIFTY',
    sensex: 'SENSEX',
    next50: 'NIFTY NEXT 50',
  },
  disclosure: 'ছয় মাসের বিক্রি ও পর্যালোচনার ভিত্তিতে',
  attribution: 'প্রচ্ছদ: Google Books / Open Library',
  baseline: 'প্রথম সপ্তাহ — তুলনা এখনও নেই',
};

/** ⚠️ An unknown language falls back to English rather than refusing: a label table is copy, and a chart in the wrong
 * *language* is a smaller failure than a chart that will not render. A chart in the wrong **data** is the one this
 * product refuses (see `chartFor` in `facts.ts`). */
export const tableFor = (language: string): Copy => (language === 'bn' ? BN : EN);
