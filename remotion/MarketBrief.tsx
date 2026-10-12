import {AbsoluteFill, Audio, Sequence, staticFile} from 'remotion';
import {Backdrop} from './Backdrop';
import {CornerBug, type Mark} from './Brand';
import * as blocks from './blocks';
import type {FactsBundle} from './bundle';
import type {Language} from './copy';

/** The composition's props. ⚠️ `bundle` is the language-neutral facts; `lang` picks the label table
 * and is never written into the bundle — see the note in Furniture.tsx.
 *
 * ⚠️ `backdrop` defaults to **on** but is a prop, so the DOM-only render stays reachable from the CLI with
 * `--props`. That is the fallback the old 3D layer also had: if the animated background misbehaves on a render
 * machine, the brief still renders complete — same blocks, same numbers, same charts — and the failure is a
 * lost layer rather than a lost video.
 *
 * ⚠️ `mark` is the product mark, inlined by `logo.py` as a data URI. It rides **beside** the bundle for the
 * same reason `lang` does: it is not a fact, and the bundle has to stay the one thing both editions read
 * identically (ADR 0003). Absent when the operator has not supplied an asset — a brief without branding, not
 * a failed render. */
export type MarketBriefProps = {
  bundle: FactsBundle;
  lang: Language;
  backdrop?: boolean;
  mark?: Mark | null;
  /**
   * ⚠️ **Preview only — every real render leaves this unset, and that is load-bearing.**
   *
   * The delivered brief is rendered **silent** and the music is muxed on afterwards by `audio.mux`, so the bed is
   * loudness-normalised **once** and both editions mux the identical file. Baking audio into the composition would
   * double it (once here, once at the mux) and skip that normalisation, so `render._write_props` never writes this
   * field and the copy tests pin the wrapper's key set to exactly `{bundle, lang, mark}`.
   *
   * It exists so Remotion Studio can *play* the bed while a card is being composed (`./bn`): a **filename inside the
   * Remotion `public/` folder**, resolved with `staticFile`. Absent means silent; `bed = null` is the shipping path.
   */
  bed?: string | null;
};

/**
 * The running order, resolved from the bundle.
 *
 * ⚠️ **The timeline comes from `props.timeline`, not from this file.** Slot durations are a data
 * decision — 0085_08 will resize each slot to fit the longer of Bengali and English — so the renderer
 * must not hold a second opinion about them. It cuts exactly where the bundle says.
 *
 * ⚠️ A block whose data was absent is **not in the timeline at all**: Python drops it, and its slot is
 * removed rather than redistributed. So a thin day renders a shorter brief, never a slower one, and
 * this component has no "is there enough?" logic to get wrong.
 */
const REGISTRY: Record<string, React.ComponentType<FactsBundle>> = {
  disclosure: blocks.Disclosure,
  cold_open: blocks.ColdOpen,
  indexes: blocks.Indexes,
  leaders: blocks.Leaders,
  most_active: blocks.MostActive,
  sectors: blocks.Sectors,
  heat_map: blocks.HeatMap,
  breadth: blocks.Breadth,
  dma: blocks.Dma,
  flows: blocks.Flows,
  dependencies: blocks.Dependencies,
  broader: blocks.Broader,
  calendar: blocks.Calendar,
  close: blocks.Close,
};

export const MarketBrief = ({bundle, backdrop = true, mark = null, bed = null}: MarketBriefProps) => (
  <AbsoluteFill style={{background: '#0b0e13'}}>
    {/* ⚠️ The animated backdrop goes behind the DOM, once, for the whole brief — one layer rather than one per
        block, so the field is continuous from the pre-roll to the close. Turning `backdrop` off removes this and
        nothing else: the cards are a complete brief on their own, which is the fallback the old 3D layer asked
        for too. */}
    {backdrop ? <Backdrop bundle={bundle} /> : null}

    {/* ⚠️ Preview-only, and silent in every real render — see the note on `bed`. Studio needs an element to play;
        the deliverable gets its music from the ffmpeg mux instead. */}
    {bed ? <Audio src={staticFile(bed)} /> : null}

    {bundle.timeline.blocks.map((block) => {
      const Block = REGISTRY[block.key];
      if (!Block) {
        return null;
      }
      return (
        <Sequence
          key={block.id}
          from={block.from}
          durationInFrames={block.duration}
          name={`${block.id} ${block.key}`}
        >
          <Block {...bundle} />
        </Sequence>
      );
    })}

    {/* ⚠️ Last, so the mark sits above every block — it is present throughout, and three of the blocks
        (`Disclosure`, `ColdOpen`, `Close`) do not use `Card`, so per-card furniture would lose it exactly
        where the first and last impressions are made. See the note in Brand.tsx. */}
    <CornerBug mark={mark} />
  </AbsoluteFill>
);

/** The composition's length and frame rate are the bundle's, so the runtime cannot drift from the data
 * that justified it. */
export const metadata = ({props}: {props: MarketBriefProps}) => ({
  durationInFrames: Math.max(props.bundle?.timeline?.total_frames ?? 1, 1),
  fps: props.bundle?.timeline?.fps ?? 30,
});
