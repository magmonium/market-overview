import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {FactsBundle} from './bundle';
import BN from './copy.bn.json';

/**
 * 0085_02's card: one index, six windows, six seconds.
 *
 * Three rules this file is written to, and they are not stylistic:
 *
 * - **No fetching, no URLs.** The bundle is the only input (ADR 0003). Grep this
 *   layer for `fetch`/`http` and you should find nothing.
 * - **Frame-derived motion only.** `useCurrentFrame()` is Remotion's virtual clock,
 *   so the same props give the same frames on any machine. No `Date.now()`, no
 *   CSS transitions, no `Math.random()`.
 * - **The entrance fits inside the reading window, it does not consume it.** A 6 s
 *   card spends 0.4 s arriving, leaving 5.6 s to read a figure.
 */

const WINDOWS: readonly string[] = [
  'change',
  'Perf.W',
  'Perf.1M',
  'Perf.3M',
  'Perf.6M',
  'Perf.Y',
];

const copy = BN as {
  indexes: Record<string, string>;
  windows: Record<string, string>;
  disclosure: string;
};

const INK = '#f4f6fa';
const MUTED = '#8b95a7';
const GREEN = '#37d67a';
const RED = '#ff5c5c';
const BG = '#0b0e13';

const number = (value: number | null): string =>
  value === null ? '—' : value.toLocaleString('en-IN', {maximumFractionDigits: 2});

/** U+2212 for the sign, so it is not a hyphen sitting next to a digit. */
const percent = (value: number | null): string =>
  value === null
    ? '—'
    : `${value >= 0 ? '+' : '\u2212'}${Math.abs(value).toFixed(2)}%`;

export const IndexCard = ({meta, indexes}: FactsBundle) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // 0085_02 features one index. The five-row scoreboard is 0085_06.
  const featured = indexes[0];

  const enter = interpolate(frame, [0, Math.round(fps * 0.4)], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const shell: React.CSSProperties = {
    background: BG,
    color: INK,
    // "Kohinoor Bangla" is the system Bengali face; it must be named explicitly,
    // because a fallback silently changes the shaping.
    fontFamily: '"Kohinoor Bangla", system-ui, -apple-system, sans-serif',
    // 96px keeps clear of the footer register.
    padding: '72px 96px',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
  };

  if (!featured) {
    return (
      <AbsoluteFill style={shell}>
        <div style={{color: MUTED, fontSize: 40}}>—</div>
      </AbsoluteFill>
    );
  }

  const label = copy.indexes[featured.label_key] ?? featured.label_key;
  const day = featured.window['change'] ?? null;
  const dayColor = day === null ? MUTED : day >= 0 ? GREEN : RED;

  return (
    <AbsoluteFill style={shell}>
      {/*
        Reserved top-right safe area, 260x160 — the product mark lands here in
        0085_10. Nothing may draw into it, which is why the header row below stops
        short of the right edge.
      */}

      <header
        style={{
          display: 'flex',
          alignItems: 'baseline',
          gap: 28,
          opacity: enter,
          transform: `translateY(${(1 - enter) * 18}px)`,
        }}
      >
        <div style={{fontSize: 52, fontWeight: 600}}>{label}</div>
        <div style={{fontSize: 30, color: MUTED}}>{meta.date}</div>
      </header>

      <main
        style={{
          opacity: enter,
          transform: `translateY(${(1 - enter) * 26}px)`,
        }}
      >
        <div style={{fontSize: 168, fontWeight: 700, lineHeight: 1, letterSpacing: '-0.02em'}}>
          {number(featured.close)}
        </div>
        <div style={{fontSize: 84, fontWeight: 600, color: dayColor, marginTop: 12}}>
          {percent(day)}
        </div>

        <div style={{display: 'flex', gap: 44, marginTop: 56}}>
          {WINDOWS.map((window) => {
            const value = featured.window[window] ?? null;
            return (
              <div key={window} style={{minWidth: 190}}>
                <div style={{fontSize: 28, color: MUTED}}>
                  {copy.windows[window] ?? window}
                </div>
                <div
                  style={{
                    fontSize: 44,
                    fontWeight: 600,
                    marginTop: 6,
                    color: window === 'change' ? dayColor : INK,
                  }}
                >
                  {percent(value)}
                </div>
              </div>
            );
          })}
        </div>
      </main>

      {/* The disclosure shares the footer register with attribution — never the close alone. */}
      <footer style={{borderTop: `1px solid #1e2531`, paddingTop: 20}}>
        <div style={{fontSize: 26, color: MUTED}}>{copy.disclosure}</div>
      </footer>
    </AbsoluteFill>
  );
};
