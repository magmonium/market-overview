import {AbsoluteFill, Sequence} from 'remotion';
import {CornerBug, type Mark} from './Brand';
import * as blocks from './blocks';
import type {FactsBundle} from './bundle';
import type {Language} from './copy';
import {World} from './world/World';

/** The composition's props. ⚠️ `bundle` is the language-neutral facts; `lang` picks the label table
 * and is never written into the bundle — see the note in Furniture.tsx.
 *
 * ⚠️ `webgl` defaults to **on** but is a prop, so the DOM-only render stays reachable from the CLI with
 * `--props`. That is 0085_09's fallback: if the world misbehaves on a render machine, the brief still
 * renders complete — same blocks, same numbers, same charts — and the failure is a lost layer rather than
 * a lost video.
 *
 * ⚠️ `mark` is the product mark, inlined by `logo.py` as a data URI. It rides **beside** the bundle for the
 * same reason `lang` does: it is not a fact, and the bundle has to stay the one thing both editions read
 * identically (ADR 0003). Absent when the operator has not supplied an asset — a brief without branding, not
 * a failed render. */
export type MarketBriefProps = {bundle: FactsBundle; lang: Language; webgl?: boolean; mark?: Mark | null};

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

export const MarketBrief = ({bundle, webgl = true, mark = null}: MarketBriefProps) => (
  <AbsoluteFill style={{background: '#0b0e13'}}>
    {/* ⚠️ The world goes behind the DOM, once, for the whole brief — see the note in World.tsx about why
        one canvas rather than one per block. Turning `webgl` off removes this and nothing else: the cards
        are a complete brief on their own, which is the fallback 0085_09 asks for. */}
    {webgl ? <World bundle={bundle} /> : null}

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
