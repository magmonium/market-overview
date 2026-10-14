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


def span(week: str) -> tuple[str, str]:
    """The dates a list may carry and still describe `week` — **inclusive at both ends.**

    ⚠️ **Derived from the week key, never from a clock.** The week is an argument (ADR 0003), so a span read off today
    would make a rebuild of week 41 depend on when it was rebuilt, and a replay would then disagree with the original
    run about which rows were fresh.

    ⚠️ **Through `date.fromisocalendar`, not arithmetic on the week number.** `2027-W01` begins in **2026**, and a naive
    `week * 7` would put the span a year out — the same trap `window.monday` documents.
    """
    start = _datetime.date.fromisoformat(window.monday(week))
    return start.isoformat(), (start + _datetime.timedelta(days=6 + LAG_DAYS)).isoformat()


def is_fresh(published: str, *, week: str) -> bool:
    """Whether a list dated `published` was published for `week`.

    ⚠️ **Parsed, not string-compared.** ISO dates happen to sort lexically, which makes `<=` on the raw strings look
    right — right up to the first unpadded `2026-1-5`, which sorts *after* `2026-10-05` and would read as very fresh.
    ⚠️ And a value that will not parse is a **stale** answer rather than a crash: a vendor's human-readable date where an
    ISO one belongs is one source's malformed field, not a reason to lose the other three charts.
    """
    try:
        observed = _datetime.date.fromisoformat(published)
    except (TypeError, ValueError):
        return False

    earliest, latest = span(week)
    return _datetime.date.fromisoformat(earliest) <= observed <= _datetime.date.fromisoformat(latest)


def guard(rows: Iterable[corroborate.Row], *, week: str, vendors: Iterable[str]) -> Guarded:
    """Drop the rows whose list is stale, and report the vendors left with nothing.

    ⚠️ **Per list, then per vendor, and the two halves answer different questions.** Each list's own date governs its own
    rows, so a stale list is dropped without touching its vendor's fresh ones — Amazon.in's Bengali list arriving before
    its comics one is ordinary. ⚠️ Then the *vendor* is judged on what survived, because a vendor is a source (ticket 17)
    and a chart needs the source, not one particular list.

    ⚠️ **`vendors` is an argument rather than something inferred from the rows.** A vendor that returned nothing at all
    leaves no rows to infer from, and that is the commonest way a source fails — so inferring would make the guard blind
    to exactly the case it most needs to see.
    """
    declared = sorted(set(vendors))
    kept: list[corroborate.Row] = []
    answered: set[str] = set()

    for row in rows:
        vendor = corroborate.vendor_of(row.list)
        # ⚠️ An undeclared vendor's rows are not this chart's evidence (ticket 18's spine), so they are dropped here for
        # the same reason `corroborate.admit` drops them — and their absence cannot make the chart missing either.
        if vendor not in declared:
            continue
        if not is_fresh(row.published, week=week):
            continue
        kept.append(row)
        answered.add(vendor)

    return Guarded(
        rows=tuple(kept),
        missing=tuple(vendor for vendor in declared if vendor not in answered),
    )
