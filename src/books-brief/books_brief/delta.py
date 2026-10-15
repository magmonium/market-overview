"""Ticket 01 — the Δ, and the week it is taken against.

⚠️ **Two windows live on this chart and this module owns exactly one.** Ticket 23's **six-month** basis asks *"what sold
most over six months?"*; this is the **weekly** Δ — *"how has that ranking moved since last week?"* They are different
questions and keeping them apart matters, because a six-month basis is far stickier than a weekly one (which is what
makes ticket 11's ≤10 cap easier to hold than it looked).

⚠️ **Comparison is per chart** (ticket 14). Rank is chart-local, so the same title can move *up* in the Bengali chart and
*down* in the all-language chart in the same week — that is the superset working, not a contradiction.

⚠️ **`None` means *there was no previous week*, and it is not an empty mapping.** That distinction is the one thing in
this module that can quietly break the product: `rank.chart` **bypasses the newcomer cap** on `None` (ticket 03), because
with no previous week every title reads as new and the cap would ship a "Top 100" holding ten books. An empty dict says a
previous chart *existed* and was empty, which switches the cap back on.
"""
from __future__ import annotations

import datetime as _datetime
from typing import Any, Mapping

from . import identity


def previous_week(week: str) -> str:
    """The ISO week before `week`, e.g. `2026-W41` → `2026-W40`.

    ⚠️ **Through a real date, never by subtracting one from the number.** `2027-W01` is preceded by `2026-W53`, and an
    `int(week) - 1` would ask the store for `2026-W00` — a folder that can never exist. The diff would then read as
    *week one*, and the newcomer cap would be bypassed for a week that has a perfectly good predecessor.
    """
    year, _, number = week.partition("-W")
    monday = _datetime.date.fromisocalendar(int(year), int(number), 1)
    iso = (monday - _datetime.timedelta(days=7)).isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def ranks(bundle: Mapping[str, Any], slug: str) -> dict[str, int] | None:
    """One chart's `key → rank` from a snapshot, or `None` when that week never built it.

    ⚠️ **Keyed by rank, not read off the list's order.** The previous chart is a list of rows, and zipping it against
    positions would be correct only while the chart is dense and ordered — precisely the assumption a short or
    watchlisted chart breaks.

    ⚠️ **`key`, not `isbn`** (ticket 32) — see `identity.from_row`, which also reads the ISBN for a week recorded before
    the key existed. ⚠️ This is the half of the change that makes the Δ *survive* it: had this gone on reading `isbn`,
    the first week after the change would have found no incumbent at all and reported a whole chart as NEW.

    ⚠️ An **absent chart key** is `None` (ticket 13 — a chart whose sources failed is not an empty chart), which is the
    same value week one produces. Both mean *nothing to diff against*, and both must bypass the cap rather than admit
    ten newcomers.
    """
    chart = bundle.get("charts", {}).get(slug)
    if not isinstance(chart, dict):
        return None
    return {identity.from_row(row): row["rank"] for row in chart.get("ranked", [])}


def move(*, rank: int, key: str, previous: Mapping[str, int] | None) -> int | None:
    """The Δ for one row — **positive means moved up** (ticket 01) — or `None` when there is none to report.

    ⚠️ **Three different `None`s, and the renderer needs all three to be the same value:**

    | Case | Result |
    |---|---|
    | no previous week at all (week one) | `None` — the row is a **baseline**, and carries no Δ and no NEW badge (ticket 18) |
    | a previous week existed, title absent from it | `None` — the row is **NEW**, and NEW *replaces* the Δ slot (ticket 07) |
    | present in both | `previous − current` |

    ⚠️ **`0` is never returned for a missing title.** Ticket 07 forbids a blank Δ and forbids `▲0`; a flat arrow says
    the title *held station*, which is a different and false claim about a book that was not on the chart at all.
    """
    if previous is None:
        return None
    was = previous.get(key)
    if was is None:
        return None
    return was - rank
