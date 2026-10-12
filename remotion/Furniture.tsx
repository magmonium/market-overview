import {AbsoluteFill, getInputProps} from 'remotion';
import {type Copy, type Language, tableFor} from './copy';
import {FONT, MUTED, RULE, SCRIM} from './theme';

/**
 * The label table for the edition being rendered.
 *
 * ⚠️ Read from **Remotion's own input props**, not threaded through fourteen components as a `lang`
 * prop — and deliberately **not** read from the facts bundle. The bundle stays language-neutral so both
 * editions read the identical file, which is what makes it impossible for them to disagree about a
 * number. That is ticket 20's parity rule, and putting the language in the bundle would quietly break it.
 *
 * A Proxy rather than a hook: the language is ambient to the whole composition — every card is in one
 * language — so this way a card cannot forget to ask for it, and adding a card needs no thought about
 * language at all.
 */
export const copy = new Proxy({} as Copy, {
  get: (_target, group) => {
    if (typeof group !== 'string') {
      return undefined;
    }
    const {lang} = getInputProps() as {lang?: Language};
    return tableFor(lang ?? 'bn')[group as keyof Copy];
  },
}) as Copy;


/** Frame-derived entrance. Motion must fit *inside* the reading window, never consume it — an
 * entrance that runs for a fifth of a card eats a fifth of the time there is to read a number. */
export const enter = (frame: number, fps: number, span = 0.4) => {
  const limit = Math.max(1, Math.round(fps * span));
  const raw = Math.min(Math.max(frame, 0), limit) / limit;
  return {opacity: raw, lift: (1 - raw) * 22};
};

/**
 * The furniture every card shares: a reserved top-right mark area, the block title, and the footer
 * register that carries the disclosure and the attribution.
 *
 * ⚠️ The **persistent disclosure strip** (ticket 01) is not decoration — a two-minute video whose
 * only disclosure is at the start and the end leaves anyone watching the middle with none. It sits
 * in the footer register, which is also why the logo lives top-right: the two reserved areas are
 * disjoint by decision so neither has to negotiate space.
 */
/**
 * ⚠️ `scrim` defaults to the dense `SCRIM` because most cards carry figures. The three framing blocks —
 * the pre-roll, the cold open and the close — pass `SCRIM_OPEN` instead: they are the shots where the world
 * *is* the content. See the note on the two constants in theme.ts.
 */
export const Card = ({
  title,
  scrim = SCRIM,
  children,
}: {
  title?: string;
  scrim?: string;
  children: React.ReactNode;
}) => (
  <AbsoluteFill
    style={{
      // ⚠️ The scrim, not a flat fill: an opaque card would hide the world behind it entirely, and a scrim
      // strong enough to be uniform would hide the world too. See the note on `SCRIM` in theme.ts.
      background: scrim,
      color: '#f4f6fa',
      fontFamily: FONT,
      padding: '64px 96px 88px',
      display: 'flex',
      flexDirection: 'column',
    }}
  >
    {/* Reserved top-right safe area, 260x160 at `x >= 1660, y <= 160` (issue 21's verdict table). The mark
        lands there in 0085_10 — on a chip, rendered once above the whole brief rather than here, because this
        component is not used by three of the thirteen blocks. See Brand.tsx.
        ⚠️ The region is anchored to the **frame corner**, not to this card's padded content box, and that
        distinction is easy to get wrong: a measurement built from these paddings reported a collision (455 of
        765 brightest) that did not exist. Measured on the real region, six cards read 44-53 of 765 — the
        scrim, and nothing else. `tests/safe_area.py` takes `--box=` so a measurement can be re-aimed.
        ⚠️ The dead `seconds` prop that used to sit here is gone: pushed hard right via `marginLeft: 'auto'`,
        it was the one live way this space could have been stolen, and it read as a feature rather than as
        unused code. */}

    <header
      style={{
        display: 'flex',
        alignItems: 'baseline',
        gap: 28,
        minHeight: 56,
        marginBottom: 24,
      }}
    >
      {title ? <div style={{fontSize: 46, fontWeight: 600}}>{title}</div> : null}
    </header>

    <main style={{flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column'}}>{children}</main>

    <footer style={{borderTop: `1px solid ${RULE}`, paddingTop: 16}}>
      <div style={{display: 'flex', justifyContent: 'space-between', gap: 32}}>
        <div style={{fontSize: 24, color: MUTED}}>{copy.disclosure}</div>
        <div style={{fontSize: 24, color: MUTED, whiteSpace: 'nowrap'}}>
          {copy.furniture.attribution}
        </div>
      </div>
    </footer>
  </AbsoluteFill>
);
