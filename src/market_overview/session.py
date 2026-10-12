"""Which session a run is for — and whether that session has finished printing.

Derived from the **spine itself**. TradingView returns the bar's own timestamps — `time`
is the session's open (09:15 IST) and `last_bar_update_time` is its last update — so the
guard needs **no second source**: BSE stays out of it and the abort path stays Python-only.

⚠️ This is **load-bearing, not defensive**, because the run is manual (ADR 0004). An
operator can fire it on a holiday or mid-session, and neither produces an error: a holiday
yields *yesterday's* numbers and a mid-session run yields *unfinished* ones. Both would be
published as if they were today's close.
"""
from __future__ import annotations

import datetime as _datetime

IST = _datetime.timezone(_datetime.timedelta(hours=5, minutes=30), "IST")

SESSION_OPEN = _datetime.time(9, 15)
SESSION_CLOSE = _datetime.time(15, 30)

# The india feed is ~15 minutes delayed (`update_mode` = 'delayed_streaming_900'), so
# "final" is the close plus that delay plus a margin — and 16:00 IST is already the
# post-close build time the design names.
FINAL_FROM = _datetime.time(16, 0)


class StaleSessionError(RuntimeError):
    """The requested date is not the session the data describes, or is not yet final."""


def in_ist(moment: int | float) -> _datetime.datetime:
    """A vendor Unix timestamp, in the exchange's own zone."""
    return _datetime.datetime.fromtimestamp(moment, IST)


def session_date(bar_time: int | float) -> _datetime.date:
    """The session a bar belongs to, from the bar's own open timestamp."""
    return in_ist(bar_time).date()


def ensure_final(bar_time: int | float, last_update: int | float, requested: str) -> _datetime.date:
    """Return the session date, or refuse. Two refusals, because they are two mistakes.

    - **The wrong day** — holiday, weekend, or a mistyped date. The bar is not for the date
      asked for. A holiday is the dangerous one: it produces no error at all.
    - **The right day, not yet closed** — the bar exists and is still moving.
    """
    session = session_date(bar_time)
    wanted = _datetime.date.fromisoformat(requested)

    if session != wanted:
        raise StaleSessionError(
            f"asked for {wanted} but the newest session is {session} — "
            "a holiday or a weekend produces no error, only the previous session's numbers"
        )

    updated = in_ist(last_update)
    if updated.date() != session or updated.time() < FINAL_FROM:
        raise StaleSessionError(
            f"session {session} has not finished printing: last update "
            f"{updated:%Y-%m-%d %H:%M} IST is before {FINAL_FROM:%H:%M} IST"
        )
    return session