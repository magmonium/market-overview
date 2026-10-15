"""Ticket 23 — the six-month window, and the finding that it can only be **accumulated**.

⚠️ **The sources publish a *current* snapshot.** Amazon.in's list is current, Anandabazar's and NYT's are weekly, and a
six-month sales total is a Nielsen BookScan product — ruled out of scope. So *"ranked over six months"* cannot be
**fetched**; it has to be built out of our own committed snapshots.

⚠️ **That changes what a snapshot *is*.** Ticket 23's own words: *"the snapshot is no longer just this week's chart; it
is **this week's evidence for a six-month window**."* Ticket 10 already kept every week and ticket 01 already kept them
all — this module is what gives that habit a purpose **beyond** the Δ diff.

⚠️ **The window is what the store holds, never what the calendar says.** Weeks 1–25 cannot have six months of it, so the
chart ships from week 1 stating the window it has (ticket 18's **26-week ramp**) rather than holding for half a year.
"""
from __future__ import annotations

import dataclasses
import datetime as _datetime
import pathlib
from typing import Iterable, Mapping

from . import delta, identity, rank, store

#: ⚠️ Six months, in ISO weeks. The window's *maximum* — the store is what decides how much of it exists.
WEEKS = 26


@dataclasses.dataclass(frozen=True)
class Observation:
    """What the window says about one title — **accumulated, not read off one week.**

    ⚠️ `sales` is the **mean weekly position score over the window**, not a sum. A sum would reward a title simply for
    having existed longer: a book present for all 26 weeks would score 26× one present for a single week, even if both
    sat at #1 whenever they appeared. ⚠️ The mean divides by the window's length, so *"was #1 for half the window"* is
    worth half of *"was #1 throughout"* — which is the comparison the chart is actually making.
    """

    weeks: int
    sales: float
    rating: float | None
    ratings_count: int | None


@dataclasses.dataclass(frozen=True)
class Window:
    """The weeks the window covers, what it observed, and the mean a thin rating shrinks toward."""

    weeks: tuple[str, ...]
    observed: dict[str, Observation]
    mean_rating: float


def weeks(root: pathlib.Path, *, ending: str, count: int = WEEKS) -> tuple[str, ...]:
    """The stored weeks the window covers, **oldest first**, ending at `ending` and never beyond it.

    ⚠️ **Read off the store, not off a calendar.** The window is accumulated, so its length *is* however many snapshots
    exist — and a chart that claimed six months while holding seven weeks would be stating something untrue (which is
    why ticket 15 prints the number).

    ⚠️ **`ending` is a hard stop.** A rebuild of an old week must see the window **as it was then**, not as it is now —
    otherwise re-running week 41 after week 52 landed would produce a *different* chart, which is the replay guarantee
    ADR 0003 rests on.
    """
    root = root / "store"
    if not root.is_dir():
        return ()

    found = sorted(
        entry.name
        for entry in root.iterdir()
        if (entry / store.FACTS).is_file() and entry.name <= ending
    )
    return tuple(found[-count:])


def observe(
    root: pathlib.Path,
    *,
    ending: str,
    slug: str,
    current: Iterable[Mapping[str, object]] = (),
    count: int = WEEKS,
) -> Window:
    """Accumulate the window's evidence for one chart.

    ⚠️ **`current` is this week's rows, and it has to be *passed in* rather than read — that is a real ordering
    constraint, not a convenience.** The snapshot's **existence** is the switch that means *already built* (ADR 0003),
    so at the moment a week is being built **its own rows are not on disk**. A window that read only the store would
    therefore score every one of this week's titles at zero — and on week one that is the whole chart.

    ⚠️ **So the week being built is taken from `current` when the store does not have it, and from the store when it
    does.** The second case is not hypothetical — it is what makes this module testable against a written week — and
    getting it wrong in the other direction would **double-count** the week on any path that had already stored it.

    ⚠️ **The position score is computed here, from the row's own `rank`**, because the snapshot does not carry the
    listings a week's score came from. `rank.N_REF` is used as the list's depth — the same assumption ticket 03 already
    makes about what *"deep enough to be a real chart"* means. ⚠️ **The consequence is stated rather than hidden:** the
    window's sales term is a *position* aggregate and is not the same number as any single week's vendor-weighted score.
    It is not meant to be — the two answer different questions.
    """
    stored = weeks(root, ending=ending, count=count)
    on_disk = ending in stored
    covered = (
        stored
        if on_disk
        else weeks(root, ending=delta.previous_week(ending), count=max(0, count - 1))
    )

    batches: list[list[Mapping[str, object]]] = []
    for week in covered:
        try:
            bundle = store.read_facts(week)
        except (FileNotFoundError, ValueError):
            # ⚠️ A snapshot that will not read is **skipped**, not fatal: it costs the window one week rather than the
            # whole chart — the same degrade-to-omission rule the rest of the product keeps.
            continue
        batches.append(bundle.get("charts", {}).get(slug, {}).get("ranked", []))

    if not on_disk:
        # ⚠️ **Last, so this week's reading wins the review fields** — the run's own rows, which the store does not have.
        batches.append(list(current))
        covered = (*covered, ending)

    seen: dict[str, Observation] = {}
    for rows in batches:
        for row in rows:
            key = identity.from_row(row)
            # ⚠️ **The key is the only thing required**, and `rank` deliberately is not: the week being built carries
            # its `score` but no chart rank yet (that is what the window is for), so a guard on `rank` would drop the
            # run's own rows.
            if not key:
                continue

            earlier = seen.get(key)
            # ⚠️ **The newest week wins for the review fields**, and that is not "latest is best": a rating is
            # cumulative over the book's whole life, so last week's reading is not *older* evidence, it is *less*
            # evidence. ⚠️ Taking the newest also keeps a rebuild deterministic — the same weeks give the same answer.
            seen[key] = Observation(
                weeks=(earlier.weeks if earlier else 0) + 1,
                sales=(earlier.sales if earlier else 0.0) + _week_score(row),
                rating=_newest(row.get("rating"), earlier.rating if earlier else None),
                ratings_count=_newest(
                    row.get("ratings_count"), earlier.ratings_count if earlier else None
                ),
            )

    # ⚠️ Divided by the **window's** length, not by each title's appearances — see `Observation.sales`.
    span = max(1, len(batches))
    return Window(
        weeks=(*covered, ending),
        observed={
            isbn: dataclasses.replace(entry, sales=entry.sales / span)
            for isbn, entry in seen.items()
        },
        mean_rating=_mean_rating(seen),
    )


def _newest(current: object, earlier: object) -> object:
    """⚠️ This week's reading, or last week's when this one has none — **never a zero**, which would be a rating of
    nothing rather than an absence of one (ticket 04's rule, on a different field).
    """
    return current if current is not None else earlier


def _week_score(row: Mapping[str, object]) -> float:
    """⚠️ The week's **committed** sales term — `rank.Ranked.score`, which the snapshot carries for exactly this reason.

    ⚠️ **Not recomputed from the row's `rank`.** The score is ticket 03's vendor-weighted, depth-adjusted position, and
    the listings it came from are not in the snapshot — so a window that tried to rebuild it from `rank` alone would
    silently score a #1 in a twenty-deep category the same as a #1 in a hundred-deep one, which is the exact error
    ticket 03's `N_REF` step exists to prevent.

    ⚠️ **And not the chart rank either**, which would be circular: this week's chart ranks depend on the window.
    """
    value = row.get("score")
    return (
        float(value)
        if isinstance(value, (int, float)) and not isinstance(value, bool)
        else 0.0
    )


def _mean_rating(observed: dict[str, Observation]) -> float:
    """The mean a thin rating shrinks toward — **weighted by the ratings themselves.**

    ⚠️ **Weighted, not a plain mean of means.** A plain mean would let a book with three ratings count as much as one
    with fifty thousand — the same mistake `review_term` exists to avoid, made one level up — and it would make the
    shrinkage target itself jump around on a thin week.
    """
    rated = [
        entry
        for entry in observed.values()
        if entry.rating is not None and entry.ratings_count
    ]
    weight = sum(entry.ratings_count or 0 for entry in rated)
    if not weight:
        return rank.DEFAULT_MEAN
    return sum(entry.rating * (entry.ratings_count or 0) for entry in rated) / weight


def monday(week: str) -> str:
    """The ISO week's Monday, as an ISO date — `2026-W41` → `2026-10-05`.

    ⚠️ **Derived from the key, never from a clock.** The week is an argument (ADR 0003), and the publication date the
    metadata prints has to be a property of the week rather than of when the run happened — or two runs of one week
    would publish under two different dates.

    ⚠️ **Through `date.fromisocalendar`, not arithmetic on the week number.** `2027-W01` begins in **2026**, and a naive
    `week * 7` would put it in the wrong year.
    """
    year, _, number = week.partition("-W")
    return _datetime.date.fromisocalendar(int(year), int(number), 1).isoformat()


def previous(root: pathlib.Path, *, ending: str) -> str | None:
    """The week before `ending` that the store actually holds — or `None` when there is none.

    ⚠️ **`None` is week one** (ticket 03), and it is deliberately *not* an empty string: the newcomer cap is **bypassed**
    on `None` and **applied** on an empty tuple, and collapsing the two would ship a "Top 100" holding ten books.
    """
    earlier = weeks(root, ending=delta.previous_week(ending), count=1)
    return earlier[0] if earlier else None
