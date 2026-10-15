"""Ticket 10's freshness guard — ⚠️ **the guard against the failure that has no symptom.**

⚠️ **What it is for.** A books chart has no session clock. A stale Amazon.in scrape produces a chart that is quietly last
week's — plausible, complete, correctly formatted and wrong — and ticket 01's week-over-week diff then reports **zero
movement**, which reads as *nothing happened* rather than *nothing was fetched*. The brief catches its version of this by
asking the exchange whether it traded; there is no exchange here, so the **only** evidence available is the date the
vendor puts on its own list.

⚠️ **The mechanism is ticket 18's, not ticket 10's.** Ticket 10 fixed only that the guard exists; ticket 18 fixed what it
does when it trips — *"a stale source is a missing source for that week"* — so a vendor whose every list is stale drops
out exactly as a vendor that failed, and **the chart that needed it goes absent**. ⚠️ That is deliberately stricter than
dropping the stale rows and shipping the rest, because a chart quietly built from the surviving vendors is precisely the
silent wrong answer being guarded against.

⚠️ **And undated is stale.** The tempting default is *"no date, so nothing to check, so let it through"* — which disables
the guard for exactly the source that broke, silently, on the day it broke. Ticket 10's own words are that the source
must be **verified** to have published for the week being built, *"not trusted because the calendar says it is Tuesday."*
"""
from __future__ import annotations

import dataclasses
import datetime as _datetime
from typing import Iterable

from . import corroborate, window

#: ⚠️ **How far past the week's own Sunday a list may still be dated, and it is not slack.**
#:
#: Ticket 10: *"a Sun–Sat sales week closes Sunday; lists compiled from it land Monday–Tuesday."* ⚠️ So the list that
#: describes week 41 is **published in week 42** — and a guard asking *"is this date inside 2026-W41?"* would refuse
#: every correct answer on the one day the run happens. NYT dates its list to the coming Wednesday's issue on top of
#: that, which is what the third day is for.
#:
#: ⚠️ The recorded NYT response for 2026-W41 is dated **2026-10-14** — the Wednesday of the following week — so this
#: boundary is the real thing rather than a theoretical one. A tighter value would refuse the source this product is
#: already built against.
LAG_DAYS = 3


@dataclasses.dataclass(frozen=True)
class Guarded:
    """What survived the guard, and which vendors did not — **both, because either alone is a bug.**

    ⚠️ Rows without `missing` is the silent failure: the stale rows are gone, the chart builds smaller, and nothing says
    so. ⚠️ `missing` without rows is no guard at all: the chart is reported absent while last week's ranking is still
    ranked as this week's.
    """

    rows: tuple[corroborate.Row, ...]
    #: The declared vendors that produced **no usable evidence** — sorted, so a refusal reads the same on every run.
    missing: tuple[str, ...]


def span(week: str, *, cadence: str = "weekly") -> tuple[str, str]:
    """The dates a list may carry and still describe `week` — **inclusive at both ends.**

    ⚠️ **Derived from the week key, never from a clock.** The week is an argument (ADR 0003), so a span read off today
    would make a rebuild of week 41 depend on when it was rebuilt, and a replay would then disagree with the original
    run about which rows were fresh.

    ⚠️ **Through `date.fromisocalendar`, not arithmetic on the week number.** `2027-W01` begins in **2026**, and a naive
    `week * 7` would put the span a year out — the same trap `window.monday` documents.

    ⚠️ ⚠️ **And a monthly list is judged by the *month*, not by the week** (2026-10-15). The weekly span is ten days
    wide — a sales week plus `LAG_DAYS` — which is right for a *compiled weekly* list and **impossible for a monthly
    one**: NYT's `graphic-books-and-manga` is dated the first Saturday of the month, so it reads as stale for the other
    three weeks, and ticket 18 turns a stale vendor into an **absent chart**. ⚠️ So a monthly list is fresh for the
    **month the week falls in**, which keeps the guard's meaning — *a previous month is still stale* — while letting a
    chart build every week of the month its list describes. See `charts.CADENCES`.
    """
    start = _datetime.date.fromisoformat(window.monday(week))

    if cadence == "monthly":
        # ⚠️ The month of the week's **Monday**, because that is the day this function is already anchored to. ⚠️ And
        # the next month is computed by hand rather than by a dependency: `calendar.monthrange` would do it, but three
        # lines for one boundary is cheaper than the import, and `12` is the only case that needs saying.
        first = start.replace(day=1)
        following = (
            _datetime.date(first.year + 1, 1, 1)
            if first.month == 12
            else _datetime.date(first.year, first.month + 1, 1)
        )
        last = following - _datetime.timedelta(days=1)
        # ⚠️ The same `LAG_DAYS` at the end, for the same reason: a monthly list compiled from September's sales lands
        # in the first days of October, and a run in the week that straddles the boundary must not refuse it.
        return first.isoformat(), (last + _datetime.timedelta(days=LAG_DAYS)).isoformat()

    return start.isoformat(), (start + _datetime.timedelta(days=6 + LAG_DAYS)).isoformat()


def is_fresh(published: str, *, week: str, cadence: str = "weekly") -> bool:
    """Whether a list dated `published` was published for `week` — **at the cadence the list declares.**

    ⚠️ **Parsed, not string-compared.** ISO dates happen to sort lexically, which makes `<=` on the raw strings look
    right — right up to the first unpadded `2026-1-5`, which sorts *after* `2026-10-05` and would read as very fresh.
    ⚠️ And a value that will not parse is a **stale** answer rather than a crash: a vendor's human-readable date where an
    ISO one belongs is one source's malformed field, not a reason to lose the other three charts.

    ⚠️ **`cadence` defaults to `"weekly"`, so every existing caller keeps the old rule exactly** — the same opt-in shape
    `guard`'s `live` argument has, and for the same reason: a rule that widened by default would stop being a guard.
    """
    try:
        observed = _datetime.date.fromisoformat(published)
    except (TypeError, ValueError):
        return False

    earliest, latest = span(week, cadence=cadence)
    return _datetime.date.fromisoformat(earliest) <= observed <= _datetime.date.fromisoformat(latest)


def guard(
    rows: Iterable[corroborate.Row],
    *,
    week: str,
    vendors: Iterable[str],
    live: Iterable[str] = (),
    monthly: Iterable[str] = (),
) -> Guarded:
    """Drop the rows whose list is stale, and report the vendors left with nothing.

    ⚠️ **Per list, then per vendor, and the two halves answer different questions.** Each list's own date governs its own
    rows, so a stale list is dropped without touching its vendor's fresh ones — Amazon.in's Bengali list arriving before
    its comics one is ordinary. ⚠️ Then the *vendor* is judged on what survived, because a vendor is a source (ticket 17)
    and a chart needs the source, not one particular list.

    ⚠️ **`vendors` is an argument rather than something inferred from the rows.** A vendor that returned nothing at all
    leaves no rows to infer from, and that is the commonest way a source fails — so inferring would make the guard blind
    to exactly the case it most needs to see.

    ⚠️ ⚠️ **`live` names the vendors whose list is a *live ranking*, and they are exempt from the date check**
    (2026-10-15). The distinction is `charts.LIVE`'s and it is stated there; what matters *here* is the exact scope of the
    exemption: a live vendor's rows are kept **because a live ranking has no stale version to catch** — the page states no
    date because there is nothing to date. ⚠️ **Everything else still applies**: an undeclared vendor's rows are still
    dropped, and a live vendor that returns *nothing* is still **missing**, so its chart is still absent. ⚠️ The exemption
    is opt-in and defaults to empty, so every caller that does not name a live vendor keeps the old rule exactly.

    ⚠️ ⚠️ **`monthly` names the *lists* published monthly, and they are checked against the month rather than the week**
    (2026-10-15). ⚠️ **It takes list slugs where `live` takes vendor slugs, and the asymmetry is the point**: cadence is a
    property of the list — NYT publishes weekly lists too — while "no date at all" is a property of the vendor's whole
    store. ⚠️ The row's own `list` is what selects the rule, so one chart can hold both kinds, which is exactly what
    `comics` does. ⚠️ Opt-in and empty by default, like `live`: a guard that widened by default would stop being a guard.
    """
    declared = sorted(set(vendors))
    ranking = frozenset(live)
    monthly_lists = frozenset(monthly)
    kept: list[corroborate.Row] = []
    answered: set[str] = set()

    for row in rows:
        vendor = corroborate.vendor_of(row.list)
        # ⚠️ An undeclared vendor's rows are not this chart's evidence (ticket 18's spine), so they are dropped here for
        # the same reason `corroborate.admit` drops them — and their absence cannot make the chart missing either.
        if vendor not in declared:
            continue
        # ⚠️ **A live ranking is not dated, so it cannot be stale** — see the docstring. Every other vendor must state a
        # date inside the week's span, or its rows are dropped and the vendor reported missing.
        if vendor not in ranking:
            cadence = "monthly" if row.list in monthly_lists else "weekly"
            if not is_fresh(row.published, week=week, cadence=cadence):
                continue
        kept.append(row)
        answered.add(vendor)

    return Guarded(
        rows=tuple(kept),
        missing=tuple(vendor for vendor in declared if vendor not in answered),
    )
