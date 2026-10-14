import type {Mark as MarkData} from './bundle.ts';
import {BUG} from './palette.ts';

/**
 * The product mark on its plate — **mirrored from the brief's `Brand.tsx`, not imported** (ticket 07).
 *
 * ⚠️ **Why a plate and not a low-opacity watermark.** Over a dark, dense slide a watermark is neither readable nor
 * consistent, which defeats the point of a permanent mark. An **opaque plate whose fill we choose** turns *"will it be
 * legible over whatever is behind it?"* from a hope about the frame into a property the pipeline owns — and the fill is
 * derived from the mark's own ink by `logo.load`, so one asset serves every chart and both surfaces.
 *
 * ⚠️ **Rendered once above the whole run, not per slide.** It is present on every frame, so per-slide furniture would
 * mean a hundred copies of the same element — and one persistent element is one thing to size against the reserved
 * region rather than a hundred.
 *
 * ⚠️ **Absent when no asset was supplied, and that is deliberate** — the mark is the operator's to drop in, and until
 * they do the charts still render. A placeholder wordmark would be inventing branding, which is worse than none.
 */
export const Mark = ({mark}: {mark: MarkData}) => {
  if (!mark) {
    return null;
  }

  return (
    <div
      style={{
        position: 'absolute',
        // ⚠️ Issue 21's reserved region — `260 × 160` at `x ≥ 1660, y ≤ 160` — anchored to the **frame corner**, not
        // to the slide's padded content box. The distinction is easy to get wrong: a measurement built from the
        // paddings once reported a collision that did not exist.
        top: BUG.inset,
        right: BUG.inset,
        width: BUG.size,
        height: BUG.size,
        // ⚠️ Radius and padding **derived from the size**, so the plate reads as the same furniture at any scale rather
        // than as a sticker at the one size it was tuned for.
        borderRadius: BUG.size * (18 / 96),
        padding: BUG.size * (18 / 96),
        background: mark.chip,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <img
        src={mark.src}
        alt=""
        style={{maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', display: 'block'}}
      />
    </div>
  );
};
