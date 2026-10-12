import {useEffect, useRef} from 'react';
import {Chart as ChartJS, type ChartConfiguration, registerables} from 'chart.js';
import {BG, FONT, MUTED, RULE} from './theme';

ChartJS.register(...registerables);

/**
 * A Chart.js canvas, drawn once and never animated.
 *
 * ⚠️ `animation: false` is **not** a preference. Chart.js animates against wall-clock time, and this
 * composition is rendered frame by frame against Remotion's virtual clock — so an animated chart
 * would be a slightly different picture on every render and the determinism guarantee would be gone.
 * The entrance is Remotion's job (a frame-derived transform on the wrapper), never Chart.js's.
 *
 * `responsive: false` for the same reason: a resize observer would make the drawing depend on the
 * measuring environment rather than only on the props.
 */
export const Chart = ({
  config,
  width,
  height,
}: {
  config: ChartConfiguration;
  width: number;
  height: number;
}) => {
  const canvas = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvas.current) {
      return;
    }
    const chart = new ChartJS(canvas.current, {
      ...config,
      options: {
        animation: false,
        responsive: false,
        maintainAspectRatio: false,
        // Flat, quiet defaults: the figure is the story, not the chart furniture.
        plugins: {
          legend: {display: false},
          tooltip: {enabled: false},
          ...config.options?.plugins,
        },
        ...config.options,
      },
    });
    return () => chart.destroy();
  }, [config, width, height]);

  return <canvas ref={canvas} width={width} height={height} />;
};

/** Shared axis styling, so every flat chart in the brief reads as the same one. */
export const axis = (labels: readonly string[]) => ({
  type: 'bar' as const,
  data: {labels, datasets: []},
  options: {
    layout: {padding: 0},
    scales: {
      x: {
        grid: {display: false},
        border: {color: RULE},
        ticks: {color: MUTED, font: {family: FONT, size: 24}},
      },
      y: {
        grid: {color: RULE},
        border: {display: false},
        ticks: {color: MUTED, font: {family: FONT, size: 22}},
      },
    },
    elements: {bar: {borderRadius: 4}},
    backgroundColor: BG,
  },
});
