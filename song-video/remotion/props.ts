/**
 * What a render is given — **the whole input, and nothing else.** (Map issue 03)
 *
 * ⚠️ The renderer never fetches and never asks. Every answer was collected before the first frame, which is
 * precisely what makes a re-run a rebuild rather than a re-enactment: the same props produce the same frames.
 */
/**
 * The mark, **as the brief's own `logo.load()` returned it** — inlined as a data URI, with the chip fill
 * already computed from the mark's ink polarity. Reused rather than re-read: one licensed asset, one loader,
 * one place where the polarity question is answered.
 */
export type Mark = {readonly src: string; readonly chip: string} | null;

export type SongReelProps = {
  /** The string the operator typed. ⚠️ Never parsed from a filename or an ID3 tag (issue 04). */
  readonly title: string;
  /**
   * The staged master's filename, inside the render project's `public/` folder.
   *
   * ⚠️ **The renderer analyses its own audio** (ADR 0006), so this is the only thing a render needs to know
   * about the song — and the staged copy is byte-identical to the master the record guarded on.
   */
  readonly song: string;
  /**
   * How long the piece is, in frames — **Python's measurement, not JavaScript's.**
   *
   * ⚠️ It comes from `master.frames` over the ffprobe duration, so "the piece is exactly as long as the song"
   * has one implementation instead of two that agree today. The envelope is *indexed* against this length and
   * never the reverse: a decoder and a container can differ by a frame, and MP3 padding is the everyday example.
   */
  /**
   * Which theme to draw. ⚠️ An id from the catalogue, and an unknown one is **refused** rather than defaulted —
   * a reel in the wrong theme is indistinguishable from a reel in the right one.
   */
  readonly theme: string;
  /**
   * The staged cover's filename, or `null` — the optional `<name>.<image>` beside the master (issue 01).
   *
   * ⚠️ **A staged file, not an inlined data URI** — unlike the mark. A cover is a photograph of megabytes, and
   * base64-ing it into the props would inflate every frame's props by a third; the mark is small enough that
   * inlining it is free.
   */
  readonly cover: string | null;
  readonly frames: number;
  readonly mark: Mark;
  /**
   * The master's own digest — **the seed everything per-song is derived from.**
   *
   * ⚠️ It is already recorded, for a different reason: a swapped master must be refused (issue 09). It rides here
   * so that the *look* can vary per song without varying per render: the accent a piece is lit by, and the paths its
   * light drifts along, are pure functions of this string. Nothing new is written down, and a record made before any
   * of this existed replays into its own colours.
   */
  readonly seed: string;
  /**
   * The caption's script, `bn` or `en` — **from the record**, because a rebuild must not re-decide it.
   *
   * ⚠️ It decides the **word** the still prints; the numerals the duration is written in were already decided by
   * Python, which is why this is a language and not a label.
   */
  readonly lang: string;
  /**
   * How long the piece is, **as the still writes it**: `৪:০০`, or `4:00`.
   *
   * ⚠️ Python's formatting of Python's own measurement — never a second opinion. The still, the ledger and the
   * record must not disagree about how long the song is, and the numerals are script-dependent, so nothing here
   * could recompute it.
   */
  readonly duration: string;
};
