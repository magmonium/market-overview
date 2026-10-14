"""Ticket 08 — the market band behind the book, and **deliberately allowed to not exist**.

⚠️ **It depends on the brief's *library*, never on its *artefact*.** The scoreboard is read through
`market_overview.fetch.tradingview` — the same client, the same tickers — and **not** out of the brief's own
`store/<date>/facts.json`. Reusing that would save one HTTP call and buy a failure mode with no upside: a books run
could not happen on a day the brief did not, and the band would be *as of whatever the brief last did* rather than as of
this run. That is ticket 08's distinction, and it is the same one `pyproject.toml` already records for the whole
dependency.

⚠️ **A failed fetch omits the band entirely** — never zeros, never stale, never a placeholder. That is still the brief's
*degrade to omission* principle; only the **abort threshold** moves, because the brief's scoreboard is its content and
this one is background.

⚠️ **Values, never display strings** (ADR 0003): the rows carry slugs and numbers, and the renderer owns the words.
"""
from __future__ import annotations

import dataclasses

from market_overview import session
from market_overview.facts import CLOCK_TICKER, INDEX_LABEL_KEYS
from market_overview.fetch import tradingview

#: ⚠️ **The brief's own five, reused rather than re-listed.** They are the resolvable index set the brief measured
#: (`INDEX_TICKERS`), and a second list here could drift from it — at which point one product's *"the market"* would be
#: a different market from the other's.
ROWS = tradingview.INDEX_TICKERS


@dataclasses.dataclass(frozen=True)
class Row:
    """One index, as the band reads it — **values only** (ADR 0003).

    ⚠️ `label_key` is the brief's slug (`nifty50`, not `NSE:NIFTY`): the vendor's symbol is an implementation detail of
    the vendor, and the renderer's label table maps the slug to words. ⚠️ A symbol in the snapshot would make a vendor
    renaming a ticker a data migration instead of a one-line change.
    """

    label_key: str
    close: float | None
    change: float | None


@dataclasses.dataclass(frozen=True)
class Ticker:
    """The band: its rows, and **the session it describes**.

    ⚠️ **The date is not decoration.** Ticket 08: *"a ticker that cannot say when it is from is a ticker that can lie."*
    The band sits beneath a book ranked over six months, so without the session a reader has no way to tell whether
    those numbers are from today or from the last time the run happened to succeed.
    """

    rows: tuple[Row, ...]
    as_of: str | None


def _number(value: object) -> float | None:
    """⚠️ A vendor number, or `None` — **never coerced to zero**, because *"a missing value and a real zero are
    different facts"* (the brief's own rule, and the one `prices.py` holds for a price).
    """
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def parse(payload: bytes) -> Ticker | None:
    """The index scan's response as the band reads it — or **`None` when the band should not draw**.

    ⚠️ **Four different `None`s, and every one of them means *no band*:** an unreadable response, a short scoreboard, a
    missing clock, or a clock with no timestamps. ⚠️ That is deliberately *unlike* the brief, whose `facts.build` raises
    `MissingTickersError` on the same input — see the module docstring. Decoration that can abort a run has stopped
    being decoration.
    """
    try:
        result = tradingview.parse_snapshot(
            "tradingview-indexes", payload, tradingview.INDEX_COLUMNS
        )
    except (tradingview.ScanError, ValueError):
        # ⚠️ `ValueError` as well as `ScanError`: `json.loads` raises on a malformed body, and a source being broken is
        # the same fact as a source being absent — to the band, at least.
        return None

    # ⚠️ A short scoreboard is **the whole band's problem, not one row's.** Showing four of five would leave a viewer
    # unable to tell a missing index from one that simply did not move.
    if any(ticker not in result.rows for ticker in ROWS):
        return None

    as_of = _session_date(result)
    if as_of is None:
        return None

    return Ticker(
        rows=tuple(
            Row(
                label_key=INDEX_LABEL_KEYS[ticker],
                close=_number(result.rows[ticker].get("close")),
                change=_number(result.rows[ticker].get("change")),
            )
            for ticker in ROWS
        ),
        as_of=as_of,
    )


def _session_date(result: tradingview.ScanResult) -> str | None:
    """The session the scoreboard describes, as an ISO date — or `None` when the clock cannot be read.

    ⚠️ **The brief's own clock, not a second one.** `NSE:NIFTY`'s `time` is the bar's open (09:15 IST), and
    `session.session_date` is the brief's tested conversion — including the exchange's own timezone, which a hand-rolled
    `utcfromtimestamp` would get wrong by five and a half hours. That error is invisible for most of the day and lands
    the whole band on the wrong date for the rest of it.
    """
    row = result.rows.get(CLOCK_TICKER)
    if row is None:
        return None

    bar = row.get("time")
    if not isinstance(bar, (int, float)) or isinstance(bar, bool):
        return None

    return session.session_date(bar).isoformat()


def fetch() -> bytes:
    """The index scan's **raw response**. ⚠️ The boundary — deliberately not covered by the suite.

    ⚠️ **Bytes, not a parsed result**, so the caller can snapshot it to `store/<week>/raw/` **before** parsing — the
    brief's evidence habit, and the reason a parser that broke can be shown what it was given.
    """
    return tradingview.indexes().raw
