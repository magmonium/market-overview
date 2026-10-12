import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ChartConfiguration} from 'chart.js';
import {Chart} from './Chart';
import {Lockup, suppliedMark} from './Brand';
import {Card, copy, enter} from './Furniture';
import {headline} from './headline';

import type {FactsBundle, Quote, Window} from './bundle';
import {GREEN, FONT, INK, MUTED, NEUTRAL, RED, RULE, SCRIM_OPEN, crore, number, percent, tone} from './theme';

/** A heat-tinted percentage cell. The tint carries magnitude; the number carries the truth. */
const Cell = ({value, digits = 2}: {value: number | null; digits?: number}) => {
  const strength = value === null ? 0 : Math.min(Math.abs(value) / 4, 1);
  const alpha = Math.round(strength * 96)
    .toString(16)
    .padStart(2, '0');
  return (
    <div
      style={{
        padding: '12px 14px',
        textAlign: 'right',
        fontVariantNumeric: 'tabular-nums',
        borderRadius: 6,
        background: value === null ? 'transparent' : `${value >= 0 ? GREEN : RED}${alpha}`,
      }}
    >
      {percent(value, digits)}
    </div>
  );
};

const WINDOW_KEYS = ['change', 'Perf.W', 'Perf.1M', 'Perf.3M', 'Perf.6M', 'Perf.Y'] as const;

const windows = (window: Window, digits = 2) =>
  WINDOW_KEYS.map((key) => <Cell key={key} value={window[key] ?? null} digits={digits} />);

/** The sector table's header register — denser than the index scoreboard's on purpose, because fourteen
 * rows have to fit where six do. Shared so its seven headers cannot drift apart. */
const HEADER: React.CSSProperties = {
  fontSize: 20,
  color: MUTED,
  textAlign: 'right',
  padding: '8px 12px',
};

/** Right-aligned tabular figures, so a column can actually be read down its length. */
const NUMBER: React.CSSProperties = {textAlign: 'right', fontVariantNumeric: 'tabular-nums'};

/** Block 0 — the disclosure, before any content. A viewer who watches nothing else has still read it. */
export const Disclosure = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {opacity} = enter(frame, fps);
  return (
    <AbsoluteFill
      style={{
        background: SCRIM_OPEN,
        color: INK,
        fontFamily: '"Kohinoor Bangla", system-ui, sans-serif',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '0 160px',
        textAlign: 'center',
      }}
    >
      <div style={{opacity, fontSize: 44, lineHeight: 1.5, color: MUTED}}>{copy.disclosure}</div>
    </AbsoluteFill>
  );
};

/** Block 1 — the cold open: one number, held. */
export const ColdOpen = ({indexes, meta}: FactsBundle) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {opacity, lift} = enter(frame, fps, 0.5);
  // ⚠️ The rule lives in `headline.ts`, shared with the thumbnail (0085_12). Extracted rather than copied: two
  // copies that agree today are two copies that can contradict each other later, and the contradiction would only
  // be visible to someone holding the thumbnail next to the video.
  const featured = headline(indexes);
  return (
    <AbsoluteFill
      style={{
        background: SCRIM_OPEN,
        color: INK,
        fontFamily: '"Kohinoor Bangla", system-ui, sans-serif',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {/* ⚠️ The lockup goes on the cold open and the close only — issue 21's two moments where the mark is not
          competing with the figures. It reads the mark from the render props rather than from `props`, because
          `props` here is the facts bundle and the mark is deliberately not part of it. */}
      <Lockup mark={suppliedMark()} />
      <div style={{opacity, transform: `translateY(${lift}px)`, textAlign: 'center'}}>
        <div style={{fontSize: 40, color: MUTED, marginBottom: 20}}>
          {featured ? (copy.indexes[featured.labelKey] ?? featured.labelKey) : '—'} · {meta.date}
        </div>
        <div
          style={{
            fontSize: 220,
            fontWeight: 700,
            lineHeight: 1,
            color: tone(featured?.change ?? null),
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          {percent(featured?.change ?? null)}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** Block 2 — five indices, six windows. Heat-tinted, because the shape matters as much as the digits. */
export const Indexes = ({indexes}: FactsBundle) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {opacity} = enter(frame, fps);
  return (
    <Card title={copy.blocks.indexes}>
      <div
        style={{
          opacity,
          display: 'grid',
          gridTemplateColumns: '1fr 190px repeat(6, 152px)',
          // ⚠️ `height: 100%` + `auto` rows: without them the table sits in the top third of the frame
          // and leaves most of the card empty. Legibility beats spectacle, and empty space is neither —
          // a viewer has nothing to rest on and the card reads as unfinished.
          height: '100%',
          gridAutoRows: '1fr',
          gap: 6,
          alignItems: 'center',
        }}
      >
        <div />
        <div />
        {WINDOW_KEYS.map((key) => (
          <div
            key={key}
            style={{fontSize: 22, color: MUTED, textAlign: 'right', padding: '12px 14px'}}
          >
            {copy.windows[key] ?? key}
          </div>
        ))}

        {indexes.map((index) => (
          <div key={index.ticker} style={{display: 'contents'}}>
            <div style={{fontSize: 34}}>{copy.indexes[index.label_key] ?? index.label_key}</div>
            <div
              style={{
                fontSize: 32,
                textAlign: 'right',
                fontVariantNumeric: 'tabular-nums',
                color: MUTED,
              }}
            >
              {number(index.close, 0)}
            </div>
            {windows(index.window)}
          </div>
        ))}
      </div>
    </Card>
  );
};

/** A 5-row board. Each row carries its **relative volume**, because `+8 % on 166x` is a different
 * fact from `+8 %` on an ordinary day and the row has room to say which. */
const Board = ({title, rows}: {title: string; rows: Quote[]}) => (
  <div style={{flex: 1, display: 'flex', flexDirection: 'column'}}>
    <div style={{fontSize: 26, color: MUTED, marginBottom: 10}}>{title}</div>
    {rows.map((row) => (
      <div
        key={row.symbol}
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 150px 200px',
          alignItems: 'baseline',
          padding: '10px 0',
          borderBottom: `1px solid ${RULE}`,
        }}
      >
        <div style={{fontSize: 32}}>{row.symbol}</div>
        <div
          style={{
            fontSize: 30,
            textAlign: 'right',
            fontVariantNumeric: 'tabular-nums',
            color: tone(row.change),
          }}
        >
          {percent(row.change)}
        </div>
        <div style={{fontSize: 24, textAlign: 'right', color: MUTED}}>
          {row.relative_volume === null ? '—' : `${row.relative_volume.toFixed(0)}×`}
        </div>
      </div>
    ))}
  </div>
);

/** Block 9 — both ends at once, so the day reads as a market rather than a list. */
export const Leaders = ({leaders}: FactsBundle) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {opacity} = enter(frame, fps);
  if (!leaders) {
    return null;
  }
  return (
    <Card title={copy.blocks.leaders}>
      <div style={{opacity, display: 'flex', gap: 72, flex: 1, alignItems: 'stretch'}}>
        <Board title={copy.leaders.gainers} rows={leaders.gainers} />
        <Board title={copy.leaders.losers} rows={leaders.losers} />
      </div>
    </Card>
  );
};

/** Block 13 — the one stock where the most happened. **Direction-agnostic**: it is the unusual name,
 * not the biggest riser, and the cash figure says how much money that was. */
export const MostActive = ({most_active}: FactsBundle) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {opacity, lift} = enter(frame, fps, 0.5);
  if (!most_active) {
    return null;
  }
  return (
    <Card title={copy.blocks.most_active} scrim={SCRIM_OPEN}>
      <div
        style={{
          opacity,
          transform: `translateY(${lift}px)`,
          display: 'flex',
          alignItems: 'center',
          gap: 48,
          flex: 1,
        }}
      >
        <div style={{flex: 1}}>
          <div style={{fontSize: 92, fontWeight: 700, lineHeight: 1.1}}>{most_active.symbol}</div>
          <div style={{fontSize: 30, color: MUTED, marginTop: 10}}>
            {copy.sectors[most_active.sector_key] ?? most_active.sector_key}
          </div>
        </div>
        <div style={{textAlign: 'right'}}>
          <div
            style={{
              fontSize: 92,
              fontWeight: 700,
              color: tone(most_active.change),
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            {percent(most_active.change)}
          </div>
          <div style={{fontSize: 32, color: MUTED, marginTop: 18}}>
            {copy.most_active.relative_volume}{' '}
            <span style={{color: INK, fontSize: 42}}>
              {most_active.relative_volume === null
                ? '—'
                : `${most_active.relative_volume.toFixed(0)}×`}
            </span>
          </div>
          <div style={{fontSize: 32, color: MUTED, marginTop: 10}}>
            {copy.most_active.cash_flow}{' '}
            <span style={{color: INK, fontSize: 42}}>
              {crore(most_active.cash_flow_crore)}
            </span>{' '}
            <span style={{fontSize: 26}}>cr</span>
          </div>
        </div>
      </div>
    </Card>
  );
};

/** Block 3 — thirteen cap-weighted sectors across six windows. */
export const Sectors = ({sectors}: FactsBundle) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {opacity} = enter(frame, fps);
  if (!sectors) {
    return null;
  }
  return (
    <Card title={copy.blocks.sectors}>
      <div
        style={{
          opacity,
          display: 'grid',
          // ⚠️ Stocks and market cap each get a real column rather than riding inside the name cell.
          // Inlined, the counts stepped in and out with the length of each sector's name, so the one
          // thing a column is for — comparing numbers down the page — did not work.
          gridTemplateColumns: '1fr 96px 150px repeat(6, 142px)',
          height: '100%',
          gridAutoRows: '1fr',
          gap: 4,
          alignItems: 'center',
        }}
      >
        {/* The sector name is its own header. */}
        <div />
        <div style={HEADER}>{copy.sectors_columns.stocks}</div>
        <div style={HEADER}>{copy.sectors_columns.market_cap}</div>
        {WINDOW_KEYS.map((key) => (
          <div key={key} style={HEADER}>
            {copy.windows[key] ?? key}
          </div>
        ))}
        {sectors.map((sector) => (
          <div key={sector.sector_key} style={{display: 'contents'}}>
            <div style={{fontSize: 28}}>
              {copy.sectors[sector.sector_key] ?? sector.sector_key}
            </div>
            <div style={{...NUMBER, fontSize: 20, color: MUTED}}>{sector.members}</div>
            <div style={{...NUMBER, fontSize: 22, color: MUTED}}>
              {(sector.market_cap_crore / 1e5).toFixed(1)}L cr
            </div>
            {windows(sector.window)}
          </div>
        ))}
      </div>
    </Card>
  );
};

/**
 * Block 4 — the same thirteen, as area. Cell size is the sector's weight and colour is its day, so the
 * two facts ride two channels instead of one number the eye has to read.
 *
 * ⚠️ It reads the **scoreboard's own list**, per ticket 26 — one list serves both blocks, so the two
 * cards cannot end up disagreeing about the same sector.
 */
export const HeatMap = ({sectors}: FactsBundle) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {opacity} = enter(frame, fps);
  if (!sectors) {
    return null;
  }
  const heaviest = Math.max(...sectors.map((sector) => sector.market_cap_crore));
  return (
    <Card title={copy.blocks.heat_map}>
      <div
        style={{
          opacity,
          display: 'flex',
          flexWrap: 'wrap',
          gap: 14,
          alignContent: 'center',
          flex: 1,
        }}
      >
        {sectors.map((sector) => {
          const share = sector.market_cap_crore / heaviest;
          const day = sector.window['change'] ?? null;
          const alpha = Math.round(Math.min(Math.abs(day ?? 0) / 4, 1) * 200)
            .toString(16)
            .padStart(2, '0');
          return (
            <div
              key={sector.sector_key}
              style={{
                width: 140 + share * 420,
                height: 110 + share * 190,
                background: `${day === null ? RULE : day >= 0 ? GREEN : RED}${alpha}`,
                border: `1px solid ${RULE}`,
                borderRadius: 10,
                padding: 18,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div style={{fontSize: 26}}>
                {copy.sectors[sector.sector_key] ?? sector.sector_key}
              </div>
              <div
                style={{
                  fontSize: 40,
                  fontWeight: 700,
                  color: tone(day),
                  fontVariantNumeric: 'tabular-nums',
                }}
              >
                {percent(day)}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};

/** Block 7 — red versus green: two counters and one bar, over the same floor every other card uses. */
export const Breadth = ({breadth}: FactsBundle) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {opacity} = enter(frame, fps, 0.5);
  if (!breadth) {
    return null;
  }
  const total = Math.max(breadth.counted, 1);
  const rising = (breadth.rising / total) * 100;
  return (
    <Card title={copy.blocks.breadth} scrim={SCRIM_OPEN}>
      <div
        style={{
          opacity,
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          gap: 40,
        }}
      >
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end'}}>
          <div>
            <div style={{fontSize: 150, fontWeight: 700, color: GREEN, lineHeight: 1}}>
              {breadth.rising}
            </div>
            <div style={{fontSize: 30, color: MUTED}}>{copy.breadth.rising}</div>
          </div>
          <div style={{textAlign: 'center', fontSize: 26, color: MUTED, paddingBottom: 24}}>
            {/* ⚠️ A whole phrase with the number interpolated, not a preposition with the number appended
                beside it. `of 497` cannot be expressed as `of` + `497` in Bengali — the postposition comes
                after the noun — so a word-sized label would let the shared layout dictate English word
                order to a Bengali sentence. The template lets each table own its own order. */}
            {copy.breadth.counted_note.replace('{n}', String(breadth.counted))}
            {breadth.flat > 0 ? ` · ${copy.breadth.flat} ${breadth.flat}` : ''}
          </div>
          <div style={{textAlign: 'right'}}>
            <div style={{fontSize: 150, fontWeight: 700, color: RED, lineHeight: 1}}>
              {breadth.falling}
            </div>
            <div style={{fontSize: 30, color: MUTED}}>{copy.breadth.falling}</div>
          </div>
        </div>

        <div style={{display: 'flex', height: 40, borderRadius: 8, overflow: 'hidden'}}>
          <div style={{width: `${rising}%`, background: GREEN}} />
          <div style={{width: `${100 - rising}%`, background: RED}} />
        </div>
      </div>
    </Card>
  );
};

/** Block 8 — how much of the market sits above its own averages.
 *
 * ⚠️ One denominator across all three bars, and it is **stated on the card**. A stock needs roughly 200
 * sessions before it has a 200-day average at all, so three separate denominators would make the bars
 * silently incomparable — and counting a stock with no average as "below" would invent a bearish fact
 * out of missing data. */
export const Dma = ({dma}: FactsBundle) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {opacity} = enter(frame, fps, 0.5);
  if (!dma) {
    return null;
  }
  return (
    <Card title={copy.blocks.dma} scrim={SCRIM_OPEN}>
      <div
        style={{
          opacity,
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          gap: 36,
        }}
      >
        {(['sma50', 'sma100', 'sma200'] as const).map((key) => {
          const value = dma.above[key] ?? null;
          return (
            <div
              key={key}
              style={{
                display: 'grid',
                gridTemplateColumns: '220px 1fr 170px',
                alignItems: 'center',
                gap: 24,
              }}
            >
              <div style={{fontSize: 34}}>{copy.dma[key]}</div>
              <div
                style={{
                  height: key === 'sma200' ? 46 : 32,
                  background: RULE,
                  borderRadius: 6,
                }}
              >
                <div
                  style={{
                    width: `${value === null ? 0 : Math.max(value, 1)}%`,
                    height: '100%',
                    background: value !== null && value >= 50 ? GREEN : RED,
                    borderRadius: 6,
                  }}
                />
              </div>
              <div
                style={{
                  fontSize: 40,
                  textAlign: 'right',
                  fontVariantNumeric: 'tabular-nums',
                  color: value === null ? MUTED : value >= 50 ? GREEN : RED,
                }}
              >
                {value === null ? '—' : `${value.toFixed(0)}%`}
              </div>
            </div>
          );
        })}
        <div style={{fontSize: 24, color: MUTED}}>
          {dma.eligible} {copy.dma.eligible}
        </div>
      </div>
    </Card>
  );
};

/**
 * Block 10 — foreign and domestic, always **side by side**.
 *
 * ⚠️ Both categories, never one alone: FII and DII frequently offset each other, and domestic
 * institutions absorbing foreign selling is the pattern Indian commentary watches most closely. A card
 * showing only FII would misread the day.
 *
 * Colour here is "inflow green", which is intuitive — but it must not be read as a verdict. FII selling
 * is not bad news when DII buying is absorbing it, which is exactly what the pairing exists to show.
 */
export const Flows = ({flows}: FactsBundle) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {opacity} = enter(frame, fps, 0.5);
  if (!flows) {
    return null;
  }
  const widest = Math.max(
    Math.abs(flows.fii.net ?? 0),
    Math.abs(flows.dii.net ?? 0),
    1
  );
  return (
    <Card title={copy.blocks.flows} scrim={SCRIM_OPEN}>
      <div style={{opacity, display: 'flex', gap: 80, flex: 1, alignItems: 'center'}}>
        {(['fii', 'dii'] as const).map((side) => {
          const net = flows[side].net;
          const share = (Math.abs(net ?? 0) / widest) * 50;
          return (
            <div key={side} style={{flex: 1}}>
              <div style={{fontSize: 36, color: MUTED}}>{copy.flows[side]}</div>
              <div
                style={{
                  fontSize: 104,
                  fontWeight: 700,
                  lineHeight: 1.15,
                  color: tone(net),
                  fontVariantNumeric: 'tabular-nums',
                }}
              >
                {crore(net)}
              </div>
              <div style={{fontSize: 26, color: MUTED}}>cr · {copy.flows.net}</div>

              {/* Diverging around zero, so the two sides are comparable at a glance. */}
              <div style={{display: 'flex', height: 26, marginTop: 20, borderRadius: 4}}>
                <div style={{flex: 1, display: 'flex', justifyContent: 'flex-end'}}>
                  {(net ?? 0) < 0 ? (
                    <div style={{width: `${share * 2}%`, background: RED, borderRadius: 4}} />
                  ) : null}
                </div>
                <div style={{width: 2, background: RULE}} />
                <div style={{flex: 1}}>
                  {(net ?? 0) >= 0 ? (
                    <div style={{width: `${share * 2}%`, background: GREEN, borderRadius: 4}} />
                  ) : null}
                </div>
              </div>

              <div style={{fontSize: 26, color: MUTED, marginTop: 22}}>
                {copy.flows.buy} {crore(flows[side].buy)} · {copy.flows.sell}{' '}
                {crore(flows[side].sell)}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};

/**
 * Block 5 — the global cues, and the one card in the brief that is **not coloured by sign**.
 *
 * ⚠️ `*INR` rising means the rupee is *weaker*, so a green "up" would say the opposite of the truth.
 * Ticket 05's rule is "coloured by meaning, not by sign", which here means no colour at all: the
 * direction is carried by the number and its arrow.
 */
export const Dependencies = ({dependencies}: FactsBundle) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {opacity} = enter(frame, fps);
  if (!dependencies) {
    return null;
  }
  return (
    <Card title={copy.blocks.dependencies} scrim={SCRIM_OPEN}>
      <div
        style={{
          opacity,
          display: 'flex',
          flexWrap: 'wrap',
          gap: 18,
          alignContent: 'center',
          flex: 1,
        }}
      >
        {dependencies.map((row) => {
          const day = row.window['change'] ?? null;
          return (
            <div
              key={row.ticker}
              style={{
                width: 400,
                border: `1px solid ${RULE}`,
                borderRadius: 10,
                padding: '18px 22px',
              }}
            >
              <div style={{fontSize: 26, color: MUTED}}>
                {copy.dependencies[row.label_key] ?? row.label_key}
              </div>
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'baseline'}}>
                <div style={{fontSize: 46, color: NEUTRAL, fontVariantNumeric: 'tabular-nums'}}>
                  {number(row.close, 2)}
                </div>
                <div style={{fontSize: 32, color: NEUTRAL, fontVariantNumeric: 'tabular-nums'}}>
                  {day === null ? '—' : `${day >= 0 ? '\u25b2' : '\u25bc'} ${percent(day)}`}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};

/** Block 6 — the cap tiers, as ranked bars. Chart.js, with `animation: false` (see Chart.tsx). */
export const Broader = ({broader}: FactsBundle) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {opacity} = enter(frame, fps);
  if (!broader) {
    return null;
  }
  const config: ChartConfiguration = {
    type: 'bar',
    data: {
      labels: broader.map((row) => copy.indexes[row.label_key] ?? row.label_key),
      datasets: [
        {
          data: broader.map((row) => row.window['change'] ?? 0),
          backgroundColor: broader.map((row) => tone(row.window['change'] ?? null)),
          borderRadius: 6,
        },
      ],
    },
    options: {
      indexAxis: 'y',
      scales: {
        x: {
          grid: {color: RULE},
          border: {display: false},
          ticks: {color: MUTED, font: {family: FONT, size: 26}},
        },
        y: {
          grid: {display: false},
          border: {color: RULE},
          ticks: {color: INK, font: {family: FONT, size: 34}},
        },
      },
    },
  };
  return (
    <Card title={copy.blocks.broader}>
      <div style={{opacity, flex: 1, display: 'flex', alignItems: 'center'}}>
        <Chart config={config} width={1700} height={380} />
      </div>
    </Card>
  );
};

/** Block 11 — the one block with **no always-present part**.
 *
 * Each of the three sub-cards is dropped when it is empty, and facts.json omits the key entirely when
 * nothing qualified. So this component renders whatever survived, and nothing when nothing did — which
 * is why the block itself is skipped rather than shown as an empty shell. */
export const Calendar = ({corporate_actions, ipos, announcements}: FactsBundle) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {opacity} = enter(frame, fps);
  const columns = [
    {
      title: copy.calendar.corporate_actions,
      rows: (corporate_actions ?? []).slice(0, 8).map((action) => ({
        left: action.symbol,
        right: `${copy.kinds[action.kind] ?? action.kind}${
          action.amount === null ? '' : ` ₹${action.amount}`
        }`,
        note: action.ex_date.slice(5),
      })),
    },
    {
      title: copy.calendar.ipos,
      rows: (ipos ?? []).map((ipo) => ({
        left: ipo.symbol,
        right: ipo.end ? `${ipo.start.slice(5)} → ${ipo.end.slice(5)}` : ipo.start.slice(5),
        note: '',
      })),
    },
    {
      title: copy.calendar.announcements,
      rows: (announcements ?? []).slice(0, 6).map((item) => ({
        left: item.subject,
        right: '',
        note: '',
      })),
    },
  ].filter((column) => column.rows.length > 0);

  if (columns.length === 0) {
    return null;
  }

  return (
    <Card title={copy.blocks.calendar} scrim={SCRIM_OPEN}>
      <div style={{opacity, display: 'flex', gap: 44, flex: 1}}>
        {columns.map((column) => (
          <div key={column.title} style={{flex: 1, minWidth: 0}}>
            <div style={{fontSize: 26, color: MUTED, marginBottom: 12}}>{column.title}</div>
            {column.rows.map((row, index) => (
              <div
                key={`${column.title}-${index}`}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  gap: 14,
                  padding: '9px 0',
                  borderBottom: `1px solid ${RULE}`,
                  fontSize: 24,
                }}
              >
                <span
                  style={{
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {row.left}
                </span>
                <span style={{color: MUTED, whiteSpace: 'nowrap'}}>{row.right}</span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </Card>
  );
};

/**
 * Block 12 — the close.
 *
 * ⚠️ It **leads forward**, it does not recap. Ticket 22's rule is that the close is the one card with a
 * reason to point at tomorrow, and a silent piece's only promise is its sequence — so the forward line
 * comes first and the day's figure closes the loop rather than re-listing it.
 */
export const Close = ({meta, indexes}: FactsBundle) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {opacity, lift} = enter(frame, fps, 0.6);
  return (
    <Card scrim={SCRIM_OPEN}>
      {/* The other half of the lockup pair — see the note in ColdOpen. */}
      <Lockup mark={suppliedMark()} />
      <div
        style={{
          opacity,
          transform: `translateY(${lift}px)`,
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          gap: 28,
        }}
      >
        <div style={{fontSize: 40, color: MUTED}}>{copy.furniture.as_on} · {meta.date}</div>
        <div style={{fontSize: 76, fontWeight: 600, lineHeight: 1.25}}>
          {copy.indexes[indexes[0].label_key] ?? indexes[0].label_key}{' '}
          <span
            style={{
              color: tone(indexes[0].window['change'] ?? null),
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            {percent(indexes[0].window['change'] ?? null)}
          </span>
        </div>
        <div style={{fontSize: 34, color: MUTED}}>{copy.blocks.close} →</div>
      </div>
    </Card>
  );
};





