"""Blocks derived from the NSE universe scan.

Blocks 3, 4, 7, 8, 9 and 13 all read the *same* 3,199-row scan, so they are computed together,
in one pass, against one definition of the universe. Splitting them across files is how two
cards end up quoting different versions of "the market".

⚠️ Three rules inherited from the design, enforced here rather than left to the caller:

- **Volume is relative, never raw, and only within Nifty 500.** Unfiltered, the relative-volume
  ranking is topped by illiquid shells — measured at 238x on a ₹86-crore company.
- **Sectors are cap-weighted, top 13 by market cap.** For Finance (100 names, the largest
  sector) cap- and equal-weighting give *opposite signs*, so the weighting is a visible
  decision rather than a detail.
- **A null is never a low value.** A recently listed stock has no 10-day history, and "no
  history" is not "quiet".
"""
from __future__ import annotations

import re
from collections import defaultdict

from .fetch import tradingview

# The cap tiers beyond the headline five. ⚠️ Ticket 02 asked for NIFTY100 / NIFTY200 here as
# well, plus Momentum/Alpha/Low-Vol/Quality thematics — but measured on 2026-10-12 **only these
# resolve**: `NSE:CNX100` and `NSE:CNX200` are absent from the scanner with no error, and the
# Midcap/Smallcap available are the **100s**, not the 150/250s.
BROADER_TICKERS: tuple[str, ...] = ("NSE:CNXMIDCAP", "NSE:CNXSMALLCAP")

BROADER_LABEL_KEYS: dict[str, str] = {
    "NSE:CNXMIDCAP": "midcap100",
    "NSE:CNXSMALLCAP": "smallcap100",
}

# How many rows each leaderboard names, and how many sectors the scoreboard ranks.
LEADERBOARD_SIZE = 5
SECTOR_COUNT = 13


def _number(value: object) -> float | None:
    """A vendor number, or `None` — never coerced to zero (see `facts._number`)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


_UNSAFE = re.compile(r"[^a-z0-9]+")


def sectors(
    members: list[dict[str, object]], *, count: int = SECTOR_COUNT
) -> list[dict[str, object]]:
    """Cap-weighted sector rows, ranked by weight and cut to `count`.

    **One list serves both blocks** — the scoreboard ranks it, the heat map sizes and colours
    it — because two lists would eventually disagree on screen about the same sector.

    ⚠️ **Cap-weighted, not equal-weighted.** For Finance — 100 names, the largest sector — the
    two give **opposite signs** (−0.12 % against +0.73 %), so the choice is visible to a viewer.
    Cap-weighting also matches the heat map, which sizes cells by weight, and matches the
    convention: Nifty sectorals are free-float cap-weighted.

    Cutting to the top 13 by weight reproduces ticket 02's count exactly and covers **92.1 %** of
    the universe, dropping a tail that includes a `Miscellaneous` sector of one member.
    """
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in members:
        key = sector_key(row.get("sector"))
        if key:
            groups[key].append(row)

    ranked = []
    for key, rows in groups.items():
        weight = sum(_number(row.get("market_cap_basic")) or 0.0 for row in rows)
        ranked.append(
            {
                "sector_key": key,
                "members": len(rows),
                "market_cap_crore": weight / 1e7,
                "window": {w: _weighted(rows, w) for w in tradingview.WINDOWS},
            }
        )
    ranked.sort(key=lambda item: item["market_cap_crore"], reverse=True)
    return ranked[:count]


def _weighted(rows: list[dict[str, object]], column: str) -> float | None:
    """One column's cap-weighted average, or `None` when nothing carries both a value and a weight."""
    total = 0.0
    accumulated = 0.0
    for row in rows:
        value = _number(row.get(column))
        weight = _number(row.get("market_cap_basic"))
        if value is None or not weight:
            continue
        total += weight
        accumulated += weight * value
    return None if not total else accumulated / total


def breadth(members: list[dict[str, object]]) -> dict[str, int]:
    """Red versus green, over the same Nifty-500 floor every other card uses.

    ⚠️ `flat` is an **exact zero**, not a tolerance band. A band would shift counts by a few
    names for no reader benefit, and the split bar has to sum to its own total — which is why
    `counted` and `universe` are both emitted: they can differ, and the card should not pretend
    they cannot.
    """
    rising = falling = flat = 0
    for row in members:
        change = _number(row.get("change"))
        if change is None:
            continue
        if change > 0:
            rising += 1
        elif change < 0:
            falling += 1
        else:
            flat += 1
    return {
        "rising": rising,
        "falling": falling,
        "flat": flat,
        "counted": rising + falling + flat,
        "universe": len(members),
    }


def dma(members: list[dict[str, object]]) -> dict[str, object]:
    """The share of the universe above each moving average.

    ⚠️ **One denominator, not three.** A stock needs ~200 sessions before it has an SMA200 at
    all, and counting a stock with no SMA200 as "below" would manufacture a bearish fact out of
    missing data. So eligibility is *has all three averages*, and `eligible` is emitted so the
    card can state its own base rather than implying it counted all 497 names.
    """
    averages = (("sma50", "SMA50"), ("sma100", "SMA100"), ("sma200", "SMA200"))
    eligible = 0
    above = {key: 0 for key, _ in averages}

    for row in members:
        close = _number(row.get("close"))
        values = {key: _number(row.get(column)) for key, column in averages}
        if close is None or any(value is None for value in values.values()):
            continue
        eligible += 1
        for key, value in values.items():
            if close > value:
                above[key] += 1

    return {
        "eligible": eligible,
        "above": {
            key: (100.0 * count / eligible) if eligible else None
            for key, count in above.items()
        },
    }


def fetch_broader() -> tradingview.ScanResult:
    """Read the cap-tier indices for block 6.

    A **separate scan** from the headline five, deliberately: keeping them apart is what lets the
    scoreboard assert *exactly five* rows without the broader set joining its count.
    """
    return tradingview.scan(
        BROADER_TICKERS, ("close",) + tradingview.WINDOWS, name="tradingview-broader"
    )


def broader(scan: tradingview.ScanResult) -> list[dict[str, object]]:
    """The cap tiers beyond the headline five, in the scoreboard's own shape.

    ⚠️ Ticket 02 wanted `NIFTY100` and `NIFTY200` here; neither resolves, and neither do the
    Momentum/Alpha/Low-Vol/Quality thematics. Block 6 is therefore **thinner than designed**, and
    that is recorded rather than hidden by substituting index names that mean something else.
    """
    return [
        {
            "label_key": BROADER_LABEL_KEYS[ticker],
            "ticker": ticker,
            "close": _number(scan.rows[ticker].get("close")),
            "window": {w: _number(scan.rows[ticker].get(w)) for w in tradingview.WINDOWS},
        }
        for ticker in BROADER_TICKERS
        if ticker in scan.rows
    ]



def sector_key(name: object) -> str:
    """TradingView's sector string as a **stable key**.

    A key, not a display name: TradingView's taxonomy is its own global one (`Producer
    Manufacturing`, `Non-Energy Minerals`), so the words a viewer reads come from the label
    table, keyed by this slug. Slugging rather than hand-mapping means a sector that appears in
    the most-active card but not the top 13 still has a key.
    """
    return _UNSAFE.sub("_", str(name or "").strip().lower()).strip("_")


def nifty500(world: tradingview.ScanResult) -> list[dict[str, object]]:
    """The floor: membership read off each row's own `indexes` list.

    Costs no extra request — `indexes` rides the same scan — and measured at **497 members**.
    """
    return [row for row in world.rows.values() if tradingview.is_nifty500(row)]


def _quoted(row: dict[str, object]) -> dict[str, object]:
    """The fields every stock-level card quotes."""
    return {
        "symbol": str(row.get("name", "")).strip(),
        "close": _number(row.get("close")),
        "change": _number(row.get("change")),
        "relative_volume": _number(row.get("relative_volume_10d_calc")),
    }


def leaderboard(
    members: list[dict[str, object]], *, rising: bool = True, count: int = LEADERBOARD_SIZE
) -> list[dict[str, object]]:
    """Top movers, each row carrying its **relative volume**.

    A stock that moved 8% on ordinary volume is a different fact from one that moved 8% on
    166x, and the card has room to say which — so direction alone is not the ranking's story.
    """
    scored = [row for row in members if _number(row.get("change")) is not None]
    scored.sort(key=lambda row: _number(row.get("change")), reverse=rising)
    return [_quoted(row) for row in scored[:count]]


def most_active(members: list[dict[str, object]]) -> dict[str, object] | None:
    """The one stock where the most happened. **Direction-agnostic**, by relative volume.

    ⚠️ Ranking by *cash flow* instead would return the largest companies: measured on
    2026-10-09 the cash-flow leader was **RELIANCE on a below-average volume day (relVol 0.73)**
    — a big number and not a story. Relative volume finds the unusual name; cash flow is then
    reported as the *scale* of it.

    ⚠️ A null relative volume is **excluded, never treated as low** — measured on `MONEYVIEW`,
    a recently listed name with no 10-day history.
    """
    scored = [row for row in members if _number(row.get("relative_volume_10d_calc")) is not None]
    if not scored:
        return None
    best = max(scored, key=lambda row: _number(row.get("relative_volume_10d_calc")))
    traded = _number(best.get("Value.Traded"))
    return {
        **_quoted(best),
        # `Value.Traded` is `volume × close` exactly — a vendor field, not a computation — and
        # it arrives in rupees.
        "cash_flow_crore": None if traded is None else traded / 1e7,
        "sector_key": sector_key(best.get("sector")),
    }
