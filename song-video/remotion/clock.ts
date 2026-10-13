/**
 * The reel's **time line**: the piece's own time, changing, under the title — where the still has a caption.
 *
 * ⚠️ **The still states the length; the reel counts through it.** `সংগীত · ৩:০২` is a fact about the file, and a
 * fact is what a still can carry. A reel has a clock, so what belongs under its title is the *elapsed* time — the
 * same number the caption is about, moving. The halves split exactly as the caption's do: the **total** is
 * Python's string and the word is the label table's, and the only thing computed here is the elapsed value.
 *
 * ⚠️ **Frame-derived, never `Date.now()`.** A clock read from the machine would make every rebuild a different
 * film (ADR 0003). This is a pure function of `frame` and `fps`, so frame 744 of a rebuild is the frame that was
 * approved — and `accent.ts` and `backdrop.ts` are deterministic for the same reason.
 *
 * ⚠️ **The rounding is `caption.duration_at`'s**, deliberately: that function rounds to the nearest second, so the
 * last frame writes the same string the still prints and the ledger quotes, and a reel *ends* on its own caption
 * instead of a second short of it. (Python rounds half to even, this rounds half up — the two can differ only on
 * an exact half second, and the total is Python's either way.)
 */

/** ⚠️ A translation table rather than arithmetic: nobody should have to know that ০ is U+09E6. `caption.py`'s twin. */
const DIGITS: Record<string, string> = {
  bn: '০১২৩৪৫৬৭৮৯',
  en: '0123456789',
};

/**
 * Seconds as a clock face: `৪:০০`, or `4:00`.
 *
 * ⚠️ **Minutes and seconds, never an hours field** — one rule, shared with `caption.duration_at`, because a song
 * is minutes long: a piece that ran past the hour prints `61:03` on both sides rather than growing a field the
 * still could not show.
 */
export const clockAt = (seconds: number, lang: string): string => {
  const digits = DIGITS[lang] ?? DIGITS.en;
  const whole = Math.round(seconds);
  const written = (value: number, width = 1) =>
    `${value}`
      .padStart(width, '0')
      .replace(/[0-9]/g, (digit) => digits[Number(digit)]);
  return `${written(Math.floor(whole / 60))}:${written(whole % 60, 2)}`;
};

/**
 * The line itself: `০:৪২ / ৩:০২`.
 *
 * ⚠️ The total is `props.duration`, **as Python formatted it** — this module never recomputes a length, so the
 * reel cannot disagree with the still about how long the song is. Only the elapsed half is ours to derive.
 */
export const clockFor = (frame: number, fps: number, lang: string, duration: string): string =>
  `${clockAt(frame / fps, lang)} / ${duration}`;
