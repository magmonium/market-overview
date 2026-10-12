/**
 * The facts bundle — the **sole interface** from Python (ADR 0003).
 *
 * Everything here is a value or a label key. Display strings live in `copy.<lang>.json`, resolved in
 * the render layer, so a string appearing here would be a bug: a number could then change what the
 * viewer reads, and copy could change what the viewer is told happened.
 *
 * ⚠️ Every block except `indexes`, `meta` and `timeline` is **optional**, because a card whose source
 * was absent is omitted rather than zero-filled. The renderer's job is to skip it, never to
 * substitute a default that would assert something the day's data does not support.
 */

/** Six calendar windows keyed by the vendor field. `null` is "missing", never zero. */
export type Window = Record<string, number | null>;

export type IndexFacts = {
  /** A stable slug, deliberately not a ticker — the copy tables outlive a rename. */
  label_key: string;
  ticker: string;
  close: number | null;
  window: Window;
};

export type Quote = {
  symbol: string;
  close: number | null;
  change: number | null;
  relative_volume: number | null;
};

export type MostActive = Quote & {
  cash_flow_crore: number | null;
  sector_key: string;
};

export type SectorFacts = {
  sector_key: string;
  members: number;
  market_cap_crore: number;
  window: Window;
};

export type Side = {buy: number | null; sell: number | null; net: number | null};

export type FlowFacts = {session: string; fii: Side; dii: Side};

export type ActionFacts = {
  symbol: string;
  kind: string;
  amount: number | null;
  ex_date: string;
};

export type IpoFacts = {symbol: string; start: string; end: string | null};

export type AnnouncementFacts = {subject: string; ref: string};

export type BreadthFacts = {
  rising: number;
  falling: number;
  flat: number;
  counted: number;
  universe: number;
};

export type DmaFacts = {eligible: number; above: Record<string, number | null>};

/** One card's slot. `from` and `duration` are in frames, computed in Python so the renderer and the
 * data agree on the runtime rather than each having an opinion. */
export type TimelineBlock = {
  id: string;
  key: string;
  seconds: number;
  from: number;
  duration: number;
};

export type Timeline = {
  fps: number;
  build_seconds: number;
  cap_seconds: number;
  total_frames: number;
  blocks: TimelineBlock[];
};

export type FactsBundle = {
  meta: {schema: number; date: string; source: string};
  indexes: IndexFacts[];
  timeline: Timeline;
  broader?: IndexFacts[];
  dependencies?: IndexFacts[];
  leaders?: {gainers: Quote[]; losers: Quote[]};
  most_active?: MostActive;
  sectors?: SectorFacts[];
  breadth?: BreadthFacts;
  dma?: DmaFacts;
  flows?: FlowFacts;
  corporate_actions?: ActionFacts[];
  ipos?: IpoFacts[];
  announcements?: AnnouncementFacts[];
};

