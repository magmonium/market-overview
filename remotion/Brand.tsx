import {getInputProps} from 'remotion';

/**
 * The product mark — the chip, the bug, and the lockup. (0085_10)
 *
 * ⚠️ **Why a chip and not a low-opacity watermark.** Issue 21 rejected the watermark proposal, and the reason
 * is worth keeping: over a dark, moving, gradient scene it is neither readable nor consistent, which defeats
 * the point of a permanent mark. An **opaque plate whose fill we choose** turns "will it be legible over
 * whatever is behind it?" from a hope about the scene into a property the pipeline owns — and the fill is
 * derived from the mark's own ink (`logo.py`), so one asset serves every card, both editions, video and still.
 *
 * ⚠️ **The bug is rendered once, above the whole brief — not as `Card` furniture.** It is present on all
 * thirteen blocks, and three of them (`Disclosure`, `ColdOpen`, `Close`) do not use `Card` at all, so
 * card-furniture would make the mark vanish for the first five seconds and the last. One persistent element is
 * also one thing to size against the safe area rather than thirteen.
 */

/** The mark, as the wrapper props carry it — inlined by `logo.py`, never read from disk here. */
export type Mark = {
  src: string;
  name: string;
  ink: string;
  polarity: 'light' | 'dark';
  chip: string;
  declared: string;
};

/**
 * Issue 21's numbers, transcribed rather than referenced, so a change here is a visible contradiction with the
 * ticket rather than a silent drift. `tests/test_logo.py` asserts these against the ticket's verdict table.
 */
export const RESERVED = {width: 260, height: 160, left: 1660, top: 0} as const;
export const BUG = {size: 96, inset: 48} as const;

/**
 * Issue 21's thumbnail numbers, transcribed for the same reason as `BUG` — **same corner, larger share of the
 * frame.** 128 of 1280 is 10 % against the bug's 5 %, which is the whole point: at the ~210 px a feed shows the
 * still at, this reads at about **21 px** — identifiable, where a 96 px bug scaled down would not be (issue 21's
 * own arithmetic).
 */
export const STILL = {size: 128, inset: 40} as const;
export const RESERVED_STILL = {width: 320, height: 200} as const;

/**
 * ⚠️ **One plate at two sizes, derived rather than transcribed twice.** The chip's corner radius and inner padding
 * were written for a 96 px plate; scaling them by the same ratio is what keeps the 128 px still reading as the same
 * furniture rather than as a sticker. `18 / 96` is chosen so the video's values come out **exactly** as they were —
 * this is a refactor that changes nothing about the brief.
 */
const PLATE_RATIO = 18 / 96;

type Placement = {size: number; inset: number};

const plate = ({size, inset}: Placement) => ({
  position: 'absolute' as const,
  top: inset,
  right: inset,
  width: size,
  height: size,
  borderRadius: size * PLATE_RATIO,
  // Padding, so the *mark* is what fits in the plate rather than the plate being the mark.
  padding: size * PLATE_RATIO,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
});

/**
 * ⚠️ **The issue gives the bug a size and the lockup only "full-size".** So this number is a derivation, not a
 * transcription: 200 px is ~10% of the frame's width, which is exactly the share issue 21 chose for the
 * thumbnail mark (128 of 1280). Reasoning by the constraint the ticket *did* name, rather than picking a
 * number that looks nice on one still.
 */
export const LOCKUP = {size: 200, top: 72} as const;

/**
 * The mark, read from the render props rather than threaded through thirteen components.
 *
 * Same reasoning as `copy` in Furniture.tsx: the mark is **ambient to the whole composition** — every block
 * has the same one — so a card cannot forget to ask for it, and adding a card needs no thought about branding.
 */
export const suppliedMark = (): Mark | null => {
  const {mark} = getInputProps() as {mark?: Mark | null};
  return mark ?? null;
};

/**
 * The product mark on its plate, at a given placement. Used at two sizes and two scales of frame: the video's
 * corner bug and the thumbnail's larger mark.
 *
 * ⚠️ Absent when no asset was supplied, and that is deliberate — the mark is the operator's to drop in, and
 * until they do **the brief still renders**, just without it. A placeholder wordmark would be inventing
 * branding, which is worse than not having any.
 */
export const Plated = ({mark, placement = BUG}: {mark: Mark | null; placement?: Placement}) => {
  if (!mark) {
    return null;
  }
  return (
    <div style={{...plate(placement), background: mark.chip}}>
      <img
        src={mark.src}
        alt=""
        style={{maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', display: 'block'}}
      />
    </div>
  );
};

/** The video's corner bug: 96 px on its 48 px inset, present on every block. */
export const CornerBug = ({mark}: {mark: Mark | null}) => <Plated mark={mark} placement={BUG} />;

/** The thumbnail's mark: the same plate, 128 px on a 40 px inset — issue 21's "larger share of the frame". */
export const ThumbnailMark = ({mark}: {mark: Mark | null}) => <Plated mark={mark} placement={STILL} />;

/**
 * The lockup: the mark large, on the cold open and the close only — the two moments where it is not competing
 * with the figures. **No chip**, because issue 21 gives the reason: the background there is ours.
 *
 * Top-centre rather than top-right, so it does not sit under the bug that is also present on these blocks.
 */
export const Lockup = ({mark}: {mark: Mark | null}) => {
  if (!mark) {
    return null;
  }
  return (
    <div
      style={{
        position: 'absolute',
        top: LOCKUP.top,
        left: 0,
        right: 0,
        display: 'flex',
        justifyContent: 'center',
      }}
    >
      <img
        src={mark.src}
        alt=""
        style={{maxWidth: LOCKUP.size, maxHeight: LOCKUP.size, objectFit: 'contain', display: 'block'}}
      />
    </div>
  );
};
