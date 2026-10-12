"""Build the facts bundle — the **sole interface** to the render layer (ADR 0003).

Everything crossing into JS is a **value** or a **label key**. Display strings live in
the render layer's label tables, so a string appearing here is a bug, not a shortcut.

0085_02 builds the minimal bundle: `meta` plus the index scoreboard's values. The full
fourteen-card bundle is 0085_05.
"""
from __future__ import annotations

from typing import Any

from . import timeline, universe
from .fetch import tradingview

SCHEMA_VERSION = 1

# Label keys are stable slugs, deliberately not tickers: the copy tables must survive
# a vendor renaming a symbol. The label *text* lives in the render layer.
INDEX_LABEL_KEYS: dict[str, str] = {
    "NSE:NIFTY": "nifty50",
    "NSE:CNX500": "nifty500",
    "NSE:BANKNIFTY": "banknifty",
    "BSE:SENSEX": "sensex",
    "NSE:NIFTYJR": "next50",
}

# The dependency strip's label keys, same slug discipline as the indices.
DEPENDENCY_LABEL_KEYS: dict[str, str] = {
    "NSE:INDIAVIX": "indiavix",
    "TVC:GOLD": "gold",
    "TVC:SILVER": "silver",
    "NYMEX:CL1!": "wti",
    "ICEEUR:BRN1!": "brent",
    "FX_IDC:USDINR": "usdinr",
    "FX_IDC:EURINR": "eurinr",
    "FX_IDC:GBPINR": "gbinr",
    "FX_IDC:JPYINR": "jpyinr",
}

# The session clock is read from this row specifically. The dependency strip's markets run
# far past the Indian close — TVC:GOLD was last updated 18:59 IST on the same session — so
# their clock cannot date the Indian session.
CLOCK_TICKER = "NSE:NIFTY"


def build(
    date: str,
    *,
    indexes: tradingview.ScanResult,
    world: tradingview.ScanResult | None = None,
    broader: tradingview.ScanResult | None = None,
    dependencies: tradingview.ScanResult | None = None,
    flows: dict[str, object] | None = None,
    actions: list[dict] | None = None,
    ipos: list[dict] | None = None,
    announcements: list[dict] | None = None,
) -> dict[str, Any]:
    """Assemble the bundle from already-fetched results.

    The CLI fetches; this shapes. Keeping them apart is what puts every abort/degrade decision
    in one place, in the conductor, rather than scattered across parsers.
    """
    rows = indexes.rows

    # ⚠️ The expected row count is asserted HERE, where the requirement lives, and not in
    # the client. An unresolvable index comes back as an absent row with HTTP 200 and no
    # error, so a short scoreboard is otherwise completely silent.
    missing = [t for t in tradingview.INDEX_TICKERS if t not in rows]
    if missing:
        raise tradingview.MissingTickersError(
            f"index scoreboard needs {len(tradingview.INDEX_TICKERS)} rows, "
            f"got {len(rows)}; unresolved: {missing}"
        )

    bundle: dict[str, Any] = {
        "meta": {"schema": SCHEMA_VERSION, "date": date, "source": "tradingview"},
        "indexes": [_index_facts(t, rows[t]) for t in tradingview.INDEX_TICKERS],
    }

    # ── The universe blocks — 3, 4, 7, 8, 9 and 13 — from ONE pass over ONE universe ──
    if world is not None:
        members = universe.nifty500(world)
        # ⚠️ The floor is asserted, not assumed. An empty member list would quietly yield a
        # zero-row breadth card and a meaningless sector ranking — both of which would render.
        if not members:
            raise tradingview.MissingTickersError(
                "Nifty 500 membership resolved to zero rows, so the volume floor is gone"
            )
        bundle["leaders"] = {
            "gainers": universe.leaderboard(members, rising=True),
            "losers": universe.leaderboard(members, rising=False),
        }
        # Omitted if nothing carries a relative volume — never a placeholder row.
        found = universe.most_active(members)
        if found is not None:
            bundle["most_active"] = found

        ranked = universe.sectors(members)
        # ⚠️ The documented guard: the aggregation can lose a sector silently, and a short
        # scoreboard must not ship. Top-13 of 20 can only fail if the universe itself is broken.
        if len(ranked) != universe.SECTOR_COUNT:
            raise tradingview.ScanShapeError(
                f"sector scoreboard needs {universe.SECTOR_COUNT} rows, got {len(ranked)}"
            )
        bundle["sectors"] = ranked
        bundle["breadth"] = universe.breadth(members)
        bundle["dma"] = universe.dma(members)

    if broader is not None:
        rows = universe.broader(broader)
        missing_broader = [t for t in universe.BROADER_TICKERS if t not in broader.rows]
        if missing_broader:
            raise tradingview.MissingTickersError(
                f"broader index set unresolved: {missing_broader}"
            )
        bundle["broader"] = rows

    # Degrade to omission: a missing strip is an absent key, never an empty card full of
    # zeros pretending the world was flat.
    if dependencies is not None:
        bundle["dependencies"] = [
            _dependency_facts(ticker, dependencies.rows[ticker])
            for ticker in tradingview.DEPENDENCY_TICKERS
            if ticker in dependencies.rows
        ]

    # The four BSE blocks. Omitted outright when absent or empty — an empty card is not a
    # degraded card, it is a card that wastes its slot (ticket 01's density rule).
    if flows is not None:
        bundle["flows"] = flows
    # ⚠️ `if actions:` not `is not None` — an empty list means nothing qualified, and ticket 01
    # says such a sub-card is omitted rather than shown empty.
    if actions:
        bundle["corporate_actions"] = actions
    if ipos:
        bundle["ipos"] = ipos
    if announcements:
        bundle["announcements"] = announcements

    # ── The running order, computed LAST because it inspects which blocks are present ──
    # ⚠️ Slot timings ride in the bundle rather than in the renderer: a duration is a data
    # decision, and 0085_08 will resize each slot to fit the longer of the two languages.
    order = timeline.running_order(bundle)
    bundle["timeline"] = {
        "fps": timeline.FPS,
        "build_seconds": timeline.BUILD_SECONDS,
        "cap_seconds": timeline.CAP_SECONDS,
        "total_frames": timeline.total_frames(order),
        "blocks": order,
    }
    return bundle


def _index_facts(ticker: str, row: dict[str, object]) -> dict[str, Any]:
    return {
        "label_key": INDEX_LABEL_KEYS[ticker],
        "ticker": ticker,
        "close": _number(row.get("close")),
        "window": {w: _number(row.get(w)) for w in tradingview.WINDOWS},
    }


def _dependency_facts(ticker: str, row: dict[str, object]) -> dict[str, Any]:
    return {
        "label_key": DEPENDENCY_LABEL_KEYS[ticker],
        "ticker": ticker,
        "close": _number(row.get("close")),
        "window": {
            w: _number(row.get(w))
            for w in ("change", "Perf.W", "Perf.1M", "Perf.Y")
        },
    }


def stamps(indexes: tradingview.ScanResult) -> tuple[float, float]:
    """The session clock: the bar's own open, and its last update.

    Raises `MissingTickersError` if the clock row is absent, because a run with no clock
    cannot tell a holiday from a trading day — and that is the one mistake this guard
    exists to catch.
    """
    row = indexes.rows.get(CLOCK_TICKER)
    if row is None:
        raise tradingview.MissingTickersError(
            f"{CLOCK_TICKER} is missing, so the session cannot be dated"
        )
    bar, updated = row.get("time"), row.get("last_bar_update_time")
    if not isinstance(bar, (int, float)) or not isinstance(updated, (int, float)):
        raise tradingview.ScanShapeError(
            f"{CLOCK_TICKER} carries no session timestamps "
            f"(time={bar!r}, last_bar_update_time={updated!r})"
        )
    return float(bar), float(updated)


def _number(value: object) -> float | None:
    """A vendor number, or `None`.

    Never coerced to zero: a missing value and a real zero are different facts, and
    a card that shows 0.00 % for an absent number is stating something untrue.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)
