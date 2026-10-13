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

# The india feed is ~15 minutes delayed (`update_mode` = 'delayed_streaming_900'), so the
# close only exists once the feed has caught up. The design named the close plus that delay —
# 15:45 — and then dropped the margin above it.
#
# ⚠️ **15:40, because 15:45 was a round number standing in for a delay the vendor controls.**
# The two refusals are not the same shape: a bar that is still moving refuses *later* if you
# wait, but a bar whose final write has already happened refuses **forever** — nothing a
# re-run sends changes what is on the wire. 2026-10-13 refused for a whole day on a final
# write of 15:44:03 IST, 57 seconds under the old threshold, and three samples over three
# minutes read the same second; 2026-10-12's final write was 16:15 IST. Ten minutes past the
# close is under both, and still clear of the intraday feed, which is the mistake this guard
# exists to catch. `tests/test_session.py` pins the boundary from both sides.
FINAL_FROM = _datetime.time(15, 40)


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