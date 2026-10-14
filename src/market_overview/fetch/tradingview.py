"""TradingView scanner client — the **spine** (see the README's glossary).

Plain HTTP, no API key, no cookie priming. One request carries every price the
brief needs, which is why nothing else fetches prices.

⚠️ Two measured properties of this API shape the code:

1. **An unresolvable ticker is simply absent** from `data`, with HTTP 200 and no
   `errors` entry. A short result is silent, so callers must assert how many rows
   they expect rather than trusting what came back.
2. **Null columns are dropped**, so a row's `d` array can be shorter than the
   requested `columns`. Zipping by position would then attribute every later value
   to the wrong column — a wrong number that still looks plausible. This module
   refuses that outright instead.
"""
from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass

INDIA_SCAN = "https://scanner.tradingview.com/india/scan"
GLOBAL_SCAN = "https://scanner.tradingview.com/global/scan"

# The resolvable index set, measured 2026-10-12. Note NSE:NIFTYMIDCAP150 and
# NSE:NIFTYSMLCAP250 are real index memberships but are NOT queryable symbols,
# and NSE:CNXMIDCAP / NSE:CNXSMALLCAP are the 100s, not the 150/250s.
INDEX_TICKERS: tuple[str, ...] = (
    "NSE:NIFTY",
    "NSE:CNX500",
    "NSE:BANKNIFTY",
    "BSE:SENSEX",
    "NSE:NIFTYJR",
)

# The six return windows. Each is one vendor field; nothing is computed.
WINDOWS: tuple[str, ...] = ("change", "Perf.W", "Perf.1M", "Perf.3M", "Perf.6M", "Perf.Y")

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
)

_HEADERS = {
    "User-Agent": _USER_AGENT,
    "Content-Type": "application/json",
    "Accept": "application/json",
}


class ScanError(RuntimeError):
    """The spine could not be read. Prices are the spine, so this aborts a run."""


class ScanShapeError(ScanError):
    """A row came back with fewer values than columns — values would misalign."""


class MissingTickersError(ScanError):
    """Tickers were requested and did not resolve.

    Raised rather than tolerated because the failure is otherwise invisible: the
    API answers 200 with an empty or short `data` list.
    """


@dataclass(frozen=True)
class ScanResult:
    """A scan's parsed rows **and the bytes they came from**.

    Both, because the raw response is snapshotted to `store/<date>/raw/` before parsing:
    if the parser is what broke, the evidence of its input must already be on disk.
    """

    name: str
    raw: bytes
    rows: dict[str, dict[str, object]]
    total_count: int | None = None


# The full NSE universe. `indexes` is included although it is the bulky column, because it
# carries Nifty-500 membership — so the volume floor costs no extra request. Measured at
# 1.45 MB for 3,199 rows *with* it, against 0.95 MB without.
UNIVERSE_COLUMNS: tuple[str, ...] = (
    "name",
    "close",
    "change",
    "volume",
    "relative_volume_10d_calc",
    "Value.Traded",
    "market_cap_basic",
    "sector",
    "industry",
    "SMA50",
    "SMA100",
    "SMA200",
    "Perf.W",
    "Perf.1M",
    "Perf.3M",
    "Perf.6M",
    "Perf.Y",
    "indexes",
)

NIFTY500 = "NSE:CNX500"

# The bar's own timestamps. `time` is the session's open (09:15 IST) so it dates the
# session; `last_bar_update_time` says whether the session has finished printing.
TIMESTAMP_COLUMNS: tuple[str, ...] = ("time", "last_bar_update_time")

INDEX_COLUMNS: tuple[str, ...] = ("close",) + WINDOWS + TIMESTAMP_COLUMNS

# The dependency strip, measured 2026-10-12 — all nine resolve, on the GLOBAL scan.
# ⚠️ `TVC:BRENT` does not exist; `ICEEUR:BRN1!` is the ICE Brent contract.
DEPENDENCY_TICKERS: tuple[str, ...] = (
    "NSE:INDIAVIX",
    "TVC:GOLD",
    "TVC:SILVER",
    "NYMEX:CL1!",
    "ICEEUR:BRN1!",
    "FX_IDC:USDINR",
    "FX_IDC:EURINR",
    "FX_IDC:GBPINR",
    "FX_IDC:JPYINR",
)
DEPENDENCY_COLUMNS: tuple[str, ...] = ("close", "change", "Perf.W", "Perf.1M", "Perf.Y")


def scan(
    tickers: tuple[str, ...] | list[str],
    columns: tuple[str, ...] | list[str],
    *,
    name: str = "scan",
    url: str = INDIA_SCAN,
    timeout: float = 60.0,
) -> ScanResult:
    """Read `columns` for `tickers`. Returns only the tickers that resolved.

    The client stays dumb about expectations — the *caller* knows how many rows its
    card needs, and asserts it there (`facts.build`). A scoreboard that silently
    renders four rows instead of five is exactly the failure that guards.
    """
    tickers, columns = list(tickers), list(columns)
    body = {"symbols": {"tickers": tickers, "query": {"types": []}}, "columns": columns}
    request = urllib.request.Request(
        url,
        json.dumps(body).encode("utf-8"),
        headers=_HEADERS,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except OSError as exc:  # URLError, socket timeouts, HTTP errors
        raise ScanError(f"{name} scan failed: {exc}") from exc
    payload = json.loads(raw)

    return _shape(name, raw, payload, columns)


def _shape(
    name: str,
    raw: bytes,
    payload: dict,
    columns: tuple[str, ...] | list[str],
) -> ScanResult:
    """Turn a scan payload into rows, refusing any row that would misalign."""
    rows: dict[str, dict[str, object]] = {}
    for row in payload.get("data", []):
        values = row["d"]
        if len(values) != len(columns):
            raise ScanShapeError(
                f"{row['s']}: got {len(values)} values for {len(columns)} columns "
                f"({list(columns)}) — a null column was dropped and the row would misalign"
            )
        rows[row["s"]] = dict(zip(columns, values))
    return ScanResult(
        name=name, raw=raw, rows=rows, total_count=payload.get("totalCount")
    )


def filtered(
    filter_: list[dict],
    columns: tuple[str, ...] | list[str],
    *,
    name: str,
    sort_by: str,
    limit: int = 4000,
    total: int | None = None,
    url: str = INDIA_SCAN,
    timeout: float = 120.0,
) -> ScanResult:
    """A whole-market query rather than a ticker list.

    ⚠️ `range` truncates **silently** — `[0, 3000]` returned 3,000 of 3,199 with no error.
    So the caller must say how many rows it expects (`total`), and anything else refuses.
    That matters because breadth and DMA percentages are computed over this universe; a
    silent 199-row drop moves them.
    """
    columns = list(columns)
    body = {
        "filter": filter_,
        "options": {"lang": "en"},
        "columns": columns,
        "sort": {"sortBy": sort_by, "sortOrder": "desc"},
        "range": [0, limit],
    }
    request = urllib.request.Request(
        url,
        json.dumps(body).encode("utf-8"),
        headers=_HEADERS,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except OSError as exc:
        raise ScanError(f"{name} scan failed: {exc}") from exc

    result = _shape(name, raw, json.loads(raw), columns)
    # `totalCount` is the source's own answer for how many rows exist, so when no explicit
    # expectation is given it *is* the expectation. That makes the truncation guard always
    # on rather than opt-in — a guard you must remember to pass is a guard that gets missed.
    expected = total if total is not None else result.total_count
    if expected is not None and len(result.rows) != expected:
        raise ScanError(
            f"{name}: expected {expected} rows, got {len(result.rows)} "
            f"(totalCount={result.total_count}) — the range truncated the universe"
        )
    return result


NSE_STOCKS: list[dict] = [
    {"left": "type", "operation": "equal", "right": "stock"},
    {"left": "exchange", "operation": "equal", "right": "NSE"},
]


def parse_snapshot(name: str, raw: bytes, columns: tuple[str, ...] | list[str]) -> ScanResult:
    """Re-shape a **recorded** response. The rebuild path, with no network.

    ⚠️ `columns` must be supplied, because the vendor's response carries the *values* but
    **not** the column names. A snapshot therefore cannot name its own fields — the constants in
    this module are what make a rebuild reproducible rather than approximate.
    """
    return _shape(name, raw, json.loads(raw), columns)


def indexes() -> ScanResult:
    """The five resolvable indices, plus the timestamps that date the session."""
    return scan(INDEX_TICKERS, INDEX_COLUMNS, name="tradingview-indexes")


def universe(limit: int = 4000, total: int | None = None) -> ScanResult:
    """Every NSE stock with its Nifty-500 membership. ~1.45 MB for 3,199 rows."""
    return filtered(
        NSE_STOCKS,
        UNIVERSE_COLUMNS,
        name="tradingview-universe",
        sort_by="market_cap_basic",
        limit=limit,
        total=total,
    )


def dependencies() -> ScanResult:
    """The dependency strip — nine tickers, all resolvable, from the GLOBAL scan."""
    return scan(
        DEPENDENCY_TICKERS,
        DEPENDENCY_COLUMNS,
        name="tradingview-dependencies",
        url=GLOBAL_SCAN,
    )


def is_nifty500(row: dict[str, object]) -> bool:
    """Nifty-500 membership, read off the row's own `indexes` list.

    ⚠️ Membership cannot be filtered server-side (`filter` on `indexes` answers 400), and
    an absent `indexes` is "not a member", not "unknown" — measured at 497 members.
    """
    memberships = row.get("indexes")
    if not isinstance(memberships, list):
        return False
    return any(
        isinstance(entry, dict) and entry.get("proname") == NIFTY500
        for entry in memberships
    )
