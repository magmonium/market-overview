/**
 * The still's caption — the **word** half of it, and the label table that word comes from. (Map issue 08)
 *
 * ⚠️ **The value half is Python's.** `caption.duration_at` writes the length in the script's own numerals
 * (`৪:০০`), and this file supplies the word beside it. That is the brief's own split — *values in the bundle,
 * words in the label table* — applied to one line of a thumbnail: neither side can invent the other's half, and
 * nothing in the render layer has to know that ০ is U+09E6.
 *
 * ⚠️ **An unknown language is refused, not defaulted.** A caption in a language nobody chose is worse than no
 * caption at all, and by eye it is indistinguishable from one somebody did choose.
 */
export type Language = 'bn' | 'en';

/** ⚠️ The label table. A word, not a translation service: this is copy, and it is hand-written. */
const WORDS: Record<Language, {readonly music: string}> = {
  bn: {music: 'সংগীত'},
  en: {music: 'Music'},
};

/** The languages with a word for every label. ⚠️ Kept in step with Python's `caption.LANGUAGES` by refusing in
 * both directions: Python refuses an unknown `--lang`, and this refuses an unknown one at the render. */
export const LANGS = Object.keys(WORDS) as Language[];

/**
 * The caption line: the word, and the duration Python already wrote.
 *
 * ⚠️ **No upper-casing.** Bengali has no letter case, so a `text-transform` here would be a Latin habit applied to
 * a script that cannot express it — and it would silently do nothing at best.
 */
export const captionFor = (lang: string, duration: string): string => {
  const words = WORDS[lang as Language];

  if (!words) {
    throw new Error(`unknown caption language "${lang}" — the languages are ${LANGS.join(', ')}`);
  }
  return `${words.music} · ${duration}`;
};
