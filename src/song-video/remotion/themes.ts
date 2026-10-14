/**
 * The catalogue — **who the themes are, and what a theme is allowed to decide.** (Map issue 05)
 *
 * ⚠️ **Hand-authored, not generated.** A theme is a point of view: a palette, a type treatment, a motif and a
 * motion grammar. A parameterised theme table buys surface variety and no point of view, which is why the
 * brief's label tables are hand-authored too. Adding a theme here is *new code*, and that is the intent.
 *
 * ⚠️ **The ids are data.** They ride in `run.json`, in the recorded run and in every output filename, so
 * renaming one is a **migration**, not a refactor — which is why `THEMES` and `THEME_IDS` are asserted equal
 * rather than trusted to stay in step.
 *
 * ⚠️ **A theme does not own the geometry.** Three of the four forms are coordinate transforms of one profile
 * (ticket 06), so the drawings are **shared** and a theme *styles* them. That is what makes "every theme renders
 * every theme renders every wave form" structural instead of a rule somebody has to remember — the corrected form
 * of that ticket's completeness rule.
 */
import type {Accent} from './accent.ts';

/** The four wave forms, in the order the menu offers them. */
export const FORMS = ['bars', 'ribbon', 'ring', 'bloom'] as const;
export type FormId = (typeof FORMS)[number];

/** The theme ids the menu offers and `run.json` records. ⚠️ Data, not names. */
export const THEME_IDS = ['vinyl', 'neon', 'parchment', 'aurora'] as const;
export type ThemeId = (typeof THEME_IDS)[number];

/** The moving object a theme is built around. ⚠️ Owned by the theme — the menu never asks (issue 05). */
export type Motif = 'disc' | 'notes';

/** Every colour a drawing may read. ⚠️ All required: a missing slot paints `undefined`, and React drops that
 * **silently** — a theme with a hole in it renders as a black rectangle with nothing anywhere to explain it. */
export type Palette = {
  /** The field behind everything. */
  readonly field: string;
  /** The title, and anything that must read as text. */
  readonly ink: string;
  /** Material the playhead has not reached. */
  readonly muted: string;
  /** The wave itself. */
  readonly wave: string;
  /** The pulse's halo. */
  readonly glow: string;
  /**
   * The **needle on the progress dial** — the operator's ask in their own words: *"white line … progress is with red
   * bar"*, then *"the bar will be vertical and thin like radio indicator"*.
   *
   * ⚠️ **Authored per theme rather than one shared red**, for the reason the rest of the palette is: a red that reads
   * as a marker on `parchment`'s paper is lurid on `neon`'s near-black, and one that sings on `neon` disappears into
   * `vinyl`'s barn reds. The line the needle travels is the theme's own `ink` at low strength, so the pair belongs to
   * the theme's world on the light theme *and* the dark ones.
   */
  readonly progress: string;
};

export type Theme = {
  readonly id: ThemeId;
  /** What the menu shows. */
  readonly name: string;
  readonly motif: Motif;
  readonly palette: Palette;
  /**
   * The colours this theme's **backdrop** may be made of — one is chosen per piece from the recorded digest.
   *
   * ⚠️ **Authored, and inside the theme's own family.** The operator asked that different videos look different;
   * four arbitrary hues per theme would make the catalogue a generator, so each entry is a colour this theme's
   * author would have painted anyway, and the *choice* is what varies. The theme's structural palette — field,
   * ink, wave — is never chosen: a `vinyl` reel is recognisably `vinyl` in all four.
   */
  readonly accents: readonly Accent[];
  /**
   * How many frames of the envelope the **pulse** and the light are averaged over — ⚠️ **the eye's filter, not the
   * clock's.** The landscape keeps its peaks (`waves.bars` reads the raw envelope); this settles only the two things
   * that change on every single frame, because a halo driven by a true peak strobes at frame rate.
   *
   * ⚠️ **A theme's own number, because how calm the motion is *is* taste** — which is exactly why `envelope.ts` puts
   * smoothing here. `Parchment` and `Aurora` are the soothing ones and average over most of a second; `Neon` is a sign
   * in a window and stays the punchiest of the four.
   */
  readonly smooth: number;
  /**
   * How an amplitude becomes a **height**.
   *
   * ⚠️ **The correction the first real frame asked for.** Peak-normalised, the brief's own level-consistent bed
   * rendered as a near-solid block with its texture crushed into the top fifth: one loud moment owned the whole
   * scale, and the song's shape — the thing the product exists to show — became a rectangle.
   *
   * The clock must stay physically honest (it *is* the amplitude), so the correction lives here instead: every
   * curve in this catalogue lifts the middle and pins both ends, which is asserted as a property rather than
   * admired in a still.
   */
  readonly curve: (amplitude: number) => number;
};

/** A power curve with `gamma < 1`: 0 stays 0, 1 stays 1, and everything between gains height. */
const lift = (gamma: number) => (amplitude: number): number => amplitude ** gamma;

export const THEMES: readonly Theme[] = [
  {
    id: 'vinyl',
    name: 'Vinyl',
    motif: 'disc',
    palette: {
      // ⚠️ The **brief's own** near-black, deliberately: the two products should look like relatives, and the
      // reel reuses its palette rather than inventing a second darkness.
      field: '#0b0e13',
      ink: '#f5f7ff',
      muted: '#2a2f3d',
      // Amber rather than white: the wave should read as *light* coming off a record, not as more text.
      wave: '#e8b04b',
      glow: '#ffd489',
      // A warm red that survives the amber field, and reads as a marker rather than as another light.
      progress: '#e2564a',
    },
    curve: lift(0.6),
    // ⚠️ 0.4 s of settling: a record turning is unhurried, and the halo should swell rather than flicker.
    smooth: 12,
    // Lamplight off a record: the barn colours, one of which this piece's backdrop is lit by.
    accents: [
      {name: 'amber', tint: '#e8a13c'},
      {name: 'rose', tint: '#e0657f'},
      {name: 'jade', tint: '#4fbf9f'},
      {name: 'cobalt', tint: '#5a86d8'},
    ],
  },
  {
    id: 'neon',
    name: 'Neon',
    motif: 'notes',
    palette: {
      field: '#07060f',
      ink: '#eef4ff',
      muted: '#241f45',
      wave: '#22d3ee',
      // A magenta halo against a cyan wave, so the pulse is visible even where the wave is thin.
      glow: '#ff4fd8',
      // The hot one: a red-pink with enough teeth to hold its own beside cyan and magenta.
      progress: '#ff3d6e',
    },
    curve: lift(0.5),
    // The punchiest of the four — a sign in a window — but still settled enough to swell rather than strobe.
    smooth: 8,
    // Its own two, plus the two a neon sign has in the window beside it.
    accents: [
      {name: 'cyan', tint: '#22d3ee'},
      {name: 'magenta', tint: '#ff4fd8'},
      {name: 'lime', tint: '#a3e635'},
      {name: 'violet', tint: '#8b5cf6'},
    ],
  },
  {
    id: 'parchment',
    name: 'Parchment',
    motif: 'disc',
    palette: {
      // ⚠️ **A light theme, and the only one.** Nothing in the render may assume a dark field — which is also
      // why the mark is drawn raw with a drop shadow rather than on a chip: at thumbnail size a chip reads as a
      // sticker stuck on the artwork, and the shadow is what keeps a mid-tone mark off the paper.
      field: '#f4ecda',
      ink: '#181713',
      muted: '#cfc3a6',
      wave: '#3a382f',
      glow: '#a3937a',
      // Burnt rather than bright: a primary red on paper is a warning, and this is a bookmark.
      progress: '#b3402f',
    },
    // The gentlest lift of the four: paper does not shout, and the quiet passages are the point of this theme.
    curve: lift(0.75),
    // ⚠️ The longest settling of the four: on paper, motion reads as a stain spreading, never as a blink.
    smooth: 16,
    // ⚠️ Stains rather than lights: this is the light theme, so its accents darken the paper and never glow on it.
    accents: [
      {name: 'sepia', tint: '#b98a4e'},
      {name: 'sage', tint: '#7d9770'},
      {name: 'dusk', tint: '#6b7fa8'},
      {name: 'clay', tint: '#b4674f'},
    ],
  },
  {
    id: 'aurora',
    name: 'Aurora',
    motif: 'notes',
    palette: {
      field: '#06131c',
      ink: '#e8f7f5',
      muted: '#173a44',
      wave: '#5eead4',
      glow: '#a78bfa',
      // A rose, not a fire engine: it has to sit beside teal and violet without becoming the subject.
      progress: '#fb7185',
    },
    // The most lifted, and therefore the closest to abstract: quiet passages stay legible as *movement*, which
    // is what makes this the soothing one.
    curve: lift(0.45),
    // ⚠️ Built to be the calmest theme in the catalogue, and this is half of why.
    smooth: 14,
    // Its own two, plus the two the sky has at that latitude.
    accents: [
      {name: 'violet', tint: '#a78bfa'},
      {name: 'teal', tint: '#5eead4'},
      {name: 'emerald', tint: '#34d399'},
      {name: 'ice', tint: '#7dd3fc'},
    ],
  },
];

/**
 * The theme for an id, or a **refusal**.
 *
 * ⚠️ **An unknown id throws rather than falling back.** A fallback renders a perfectly good reel in a theme
 * nobody chose, written to a filename that says `-<theme>` — a defect that looks like a design choice. The
 * message names the ids that do exist, because "unknown theme" on its own is not something anyone can act on.
 */
export const themeFor = (id: string): Theme => {
  const found = THEMES.find((theme) => theme.id === id);

  if (!found) {
    throw new Error(`unknown theme "${id}" — the catalogue is ${THEME_IDS.join(', ')}`);
  }
  return found;
};
