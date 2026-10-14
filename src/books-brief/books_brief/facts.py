"""Tickets 13 and 23 — the facts bundle, the **sole interface to the render layer** (ADR 0003).

⚠️ **One file per week, four chart keys.** The brief's bundle is one file per date with the *variant* (language) read
from Remotion input props, and the reason given is parity — *"the bundle stays language-neutral so both editions read
the identical file."* ⚠️ **That reasoning does not transfer**: two language editions are the *same data* twice, while
four charts are **different data**. So the chart id is a key here and the variant is read from input props, exactly as
`lang` is.

⚠️ **A chart whose sources failed is an *absent key*.** The brief's rule — *"a missing strip is an absent key, never an
empty card full of zeros pretending the world was flat"* — buys **partial delivery**: three charts ship, the fourth
refuses.

⚠️ **`chart_logic` is versioned**, because a change to the ranking rule changes the chart — so a re-run of an old week
must reproduce the **old** chart, not the new one.
"""
from __future__ import annotations

import dataclasses
from typing import Any, Mapping

from . import charts, enrich, ticker, timeline

SCHEMA_VERSION = 1

#: ⚠️ The version of ticket 03's rule. Bumped when the ranking changes, so a re-run knows which rule to apply.
CHART_LOGIC = 1


@dataclasses.dataclass(frozen=True)
class Chart:
    """**One chart as the snapshot holds it** — the rows, and what was held back.

    ⚠️ **`books` are `enrich.Book` rows, not `rank.Ranked` ones**, and that is the difference that made the render layer
    buildable. A `Ranked` row carries `isbn`, `rank`, `weeks_on_chart` and `is_new`; ticket 07's slide prints eight
    fields, and the other six — title, author, publisher, pub date, genre, price, cover — arrive here.

    ⚠️ **`watchlist` rides beside the rows rather than inside them.** It holds the ISBNs ticket 11's ≤10 cap overflowed
    *and* the single-vendor titles ticket 17 parked, which are *"real, but not yet admitted"* — one list serving both.
    """

    books: tuple[enrich.Book, ...]
    watchlist: tuple[str, ...] = ()


def _chart_facts(slug: str, chart: Chart) -> dict[str, Any]:
    """One chart, as the renderer reads it — values only, no display strings (ADR 0003).

    ⚠️ `asdict` recurses, so the row's nested `Price` and `Cover` become plain objects. That is deliberate: the
    renderer must be able to read a price's `retailers` count without knowing Python, because that count is what decides
    whether the slide may say *"best"* at all (ticket 04).

    ⚠️ **The chart's own identity rides here as *slugs*** — `label_key`, `language`, `market` — taken from `charts.ALL`
    rather than from this module, so the table stays the one place a chart is declared. The words a viewer reads are the
    renderer's (ADR 0003): *"TOP 100 BENGALI BOOKS"* is `copy.ts`'s, and the market is a slug the label table turns
    into a sentence — which is what lets ticket 20's boundary change without re-running a week.
    """
    spec = charts.get(slug)

    return {
        "label_key": spec.label_key,
        # ⚠️ Which label table the slide is set in (ticket 27) — a *value*, because the Bengali chart's slide is the
        # reader's and the YouTube title is not.
        "language": spec.language,
        # ⚠️ Tickets 19, 21 and 22 — the chart has to **state** the market it ranks, and the three are not the same
        # market: the Bengali chart spans India *and* Bangladesh, the English one is US lists, and the superset is
        # India-only.
        "market": spec.market,
        "ranked": [dataclasses.asdict(book) for book in chart.books],
        "watchlist": list(chart.watchlist),
        # ⚠️ Ticket 05 §4 — the number ticket 16's collage rule needs *before* publishing, rather than a surprise.
        "cover_coverage": enrich.coverage(chart.books),
        # ⚠️ **The run's slots, and they are per chart.** A chart holding sixty-three books is a shorter run, not a
        # slower one — so the timeline cannot sit at the bundle root, where it would describe a hundred-book run that
        # three of the four charts are not.
        #
        # ⚠️ **`enter_frames` rides on each block**, so the renderer never recomputes ticket 07's entrance ceiling.
        # The brief's own rule: *"the timeline comes from `props.timeline`, not from this file."*
        "timeline": {
            "fps": timeline.FPS,
            "cap_seconds": timeline.CAP_SECONDS,
            "total_frames": timeline.total_frames(len(chart.books)),
            "blocks": [
                dataclasses.asdict(block)
                for block in timeline.schedule(len(chart.books))
            ],
        },
    }


def build(
    week: str,
    *,
    charts: Mapping[str, Chart | None],
    window_weeks: int,
    ticker: ticker.Ticker | None = None,
) -> dict[str, Any]:
    """Assemble the week's bundle from the charts that were built.

    ⚠️ **A `None` chart is skipped, not serialised as empty.** The caller passes `None` for a chart whose vendors did
    not answer, and the key is then absent — which is the difference between *"we could not build this"* and *"this
    chart is empty"*. An empty chart would render.

    ⚠️ **And a chart with no rows takes the same path**, because it is the same situation one step later: a chart whose
    sources answered with nothing usable is not a chart. Both leave an **absent key**, which is what buys ticket 13's
    partial delivery — three charts ship, the fourth refuses.

    ⚠️ **The band rides at the root, and is absent rather than `None`.** It is not chart-specific — *"the index
    scoreboard is not chart-specific, so it is fetched once and rendered into all four"* (ticket 13) — and a `None`
    written into the bundle would be a key the renderer has to know to ignore, where an absent one is the same fact it
    already handles everywhere else (ticket 08).
    """
    built = {
        # ⚠️ The slug is passed **as well as** the chart, because the chart's own identity comes from `charts.ALL` —
        # and the name collision with this parameter is harmless: `_chart_facts` is a module-level function, so the
        # `charts` it reads is the imported table, never this mapping.
        slug: _chart_facts(slug, chart)
        for slug, chart in charts.items()
        if chart is not None and chart.books
    }

    bundle: dict[str, Any] = {
        "meta": {
            "schema": SCHEMA_VERSION,
            "week": week,
            "chart_logic": CHART_LOGIC,
            # ⚠️ The window the chart **actually has** (ticket 23). The six-month window is accumulated from our own
            # snapshots, so weeks 1–25 carry a smaller number here rather than claiming six months they do not have.
            "window_weeks": window_weeks,
        },
        "charts": built,
    }

    if ticker is not None:
        bundle["ticker"] = dataclasses.asdict(ticker)

    return bundle

