"""Ticket 15 — the upload text: the title, the description, the tags.

⚠️ **The description cannot hold the full list with every field.** `1. Title — Author — Publisher — ₹399` runs to
roughly **6,800 characters** for a hundred rows against YouTube's **5,000** — so the rows mirror the video's own dwell
weighting (ticket 06): full rows for the top ten, title and author for the rest. **The video gives the shape; the
description gives the data.**

⚠️ **The limits are checked, not hoped for** — and an over-long description **refuses** rather than shipping, because
YouTube truncates the *tail*, which is the part of the list nobody would check.

⚠️ **The tag budget is in characters, not tags.** The brief names this trap: *"a handful of long sector names blows it
without anything looking wrong."* So tags are appended **while they fit**, never "the first N".

⚠️ **Authored, not translated** — the reel's rule. A Bengali search and a Latin one are two different queries, so the
copy is written per chart rather than derived from one another.
"""
from __future__ import annotations

import dataclasses
from typing import Any, Iterable

from . import charts

#: YouTube's limits — the same numbers the brief's own `metadata.py` uses.
TITLE_LIMIT = 100
DESCRIPTION_LIMIT = 5000
TAG_BUDGET = 500

#: ⚠️ **Fifteen is a cliff, not a budget**: past it YouTube ignores *all* the hashtags, so a longer block is strictly
#: worse than a short one. Three is also all that displays above the title.
HASHTAGS_SHOWN = 3
HASHTAGS_MAX = 15

#: ⚠️ The ranks that get a **full** row. Ticket 06 gives the top ten 3.5 s each and the tail 1.0 s, so the
#: description's detail follows the same interest curve the video does.
FULL_ROWS = 10

#: The chart's display name. ⚠️ Display strings belong with the renderer's label tables in principle (ADR 0003) — but
#: this text is never *drawn*: it is written beside the video to be pasted into an uploader, which is the same
#: distinction `song-video`'s `seo.py` draws.
NAMES: dict[str, str] = {
    "bengali": "Bengali Books",
    "english": "English Books",
    "all-language": "Indian Books (All Languages)",
    "comics": "Comics",
}

#: ⚠️ Authored per chart, not translated — a Bengali reader's query and an English reader's are different queries.
HASHTAGS: dict[str, tuple[str, ...]] = {
    "bengali": ("#Top100Books", "#BengaliBooks", "#Bestsellers"),
    "english": ("#Top100Books", "#Books", "#Bestsellers"),
    "all-language": ("#Top100Books", "#IndianBooks", "#Bestsellers"),
    "comics": ("#Top100Comics", "#Comics", "#Bestsellers"),
}

#: The fixed tags every chart carries, before the week's own are appended.
CHANNEL_TAGS: tuple[str, ...] = ("Top 100 Books", "bestsellers", "book chart")

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


class MetadataError(RuntimeError):
    """The upload text cannot be written to fit, so the run stops rather than shipping a truncated list."""


@dataclasses.dataclass(frozen=True)
class Row:
    """One title, as the description needs it."""

    rank: int
    title: str
    author: str
    publisher: str = ""
    price: str = ""


@dataclasses.dataclass(frozen=True)
class Metadata:
    """The package's front matter — and the JSON a deferred uploader reads."""

    title: str
    description: str
    tags: list[str]
    hashtags: list[str]
    video: str = ""
    thumbnail: str = ""
    bundle_hash: str = ""

    def as_text(self) -> str:
        """The **human's** file — title, then tags, then the description, in the order an uploader pastes them.

        ⚠️ The tags go on one line because that is the shape a YouTube tag field takes, and a pasted list that had to be
        re-split by hand is a list somebody will get wrong at 11pm.
        """
        return "\n".join(
            [self.title, "", ", ".join(self.tags), "", self.description]
        )

    def as_json(self) -> dict[str, Any]:
        """The **machine's** file — and, in the package, the completeness marker (ticket 13).

        ⚠️ It carries the `bundle_hash` so a deferred uploader can say **which week's facts** the text describes. A
        package whose JSON named a different bundle from the one on disk is a package built from something else.
        """
        return dataclasses.asdict(self)


def _date_words(published_on: str) -> str:
    """`14 Oct, 2026` — ⚠️ assembled from the parts rather than via `%d`, so the day is never zero-padded."""
    year, month, day = (int(part) for part in published_on.split("-"))
    return f"{day} {MONTHS[month - 1]}, {year}"


def title_for(week: str, chart: charts.Chart, published_on: str) -> str:
    """`Top 100 Bengali Books | Week 41 | 14 Oct, 2026` — ticket 15's scheme.

    ⚠️ The fit is **checked**, not hoped for. The reel's rule: *"a title that will not fit is a title to shorten, never
    a layout to bend."*
    """
    iso_week = week.partition("-W")[2]
    built = f"Top 100 {NAMES[chart.slug]} | Week {iso_week} | {_date_words(published_on)}"

    if len(built) > TITLE_LIMIT:
        raise MetadataError(
            f"the title is {len(built)} characters, over the {TITLE_LIMIT} a search result shows: {built!r}"
        )
    return built


def _row_line(row: Row, *, full: bool) -> str:
    line = f"{row.rank}. {row.title} — {row.author}"
    if full and row.publisher:
        line += f" — {row.publisher}"
    if full and row.price:
        line += f" — {row.price}"
    return line


def description_for(
    week: str,
    chart: charts.Chart,
    rows: Iterable[Row],
    *,
    basis_weeks: int,
    published_on: str,
) -> str:
    """The full list, in two tiers, with the basis and the window stated.

    ⚠️ **Refuses rather than truncating.** YouTube cuts at the limit, and it cuts the **tail** — so a list that will not
    fit is a list to shorten, not one to ship and hope nobody reads the end of.
    """
    body = [
        f"TOP 100 {NAMES[chart.slug].upper()} · WEEK {week.partition('-W')[2]}",
        "",
        # ⚠️ Tickets 15 and 23: `Top 100 Bengali Books` does not say *what it ranks*, and the window is the one the
        # chart **has** — the six-month window is accumulated, so weeks 1–25 carry a smaller number here.
        f"Ranked on sales over six months, with user reviews · window: {basis_weeks} weeks",
        "",
    ]
    body.extend(_row_line(row, full=row.rank <= FULL_ROWS) for row in rows)
    body.extend(
        [
            "",
            f"Sources: {', '.join(chart.vendors)}",
            "Covers: Google Books / Open Library",
        ]
    )

    built = "\n".join(body)

    if len(built) > DESCRIPTION_LIMIT:
        raise MetadataError(
            f"the description is {len(built)} characters, over the {DESCRIPTION_LIMIT} YouTube keeps — shorten the "
            f"rows rather than shipping a list whose tail is cut off"
        )
    return built


def tags_for(chart: charts.Chart, rows: Iterable[Row]) -> list[str]:
    """The fixed tags, then the week's authors **while they fit**.

    ⚠️ **A character budget, not a tag count** — the brief's trap, quoted in the module docstring. This appends while
    the joined length stays inside it; *"a slice of the first N would look right and blow the limit on a day of long
    names."*
    """
    chosen = [*CHANNEL_TAGS, NAMES[chart.slug], "2026"]

    for row in rows:
        if row.author and row.author not in chosen:
            if len(", ".join([*chosen, row.author])) > TAG_BUDGET:
                break
            chosen.append(row.author)

    return chosen


def build(
    week: str,
    chart: charts.Chart,
    rows: Iterable[Row],
    *,
    basis_weeks: int,
    published_on: str,
    video: str = "",
    thumbnail: str = "",
    bundle_hash: str = "",
) -> Metadata:
    """One chart's front matter — a **pure function of the bundle**, so a rebuild writes the same bytes (ADR 0003)."""
    materialised = list(rows)
    hashtags = list(HASHTAGS[chart.slug])

    description = description_for(
        week, chart, materialised, basis_weeks=basis_weeks, published_on=published_on
    )

    return Metadata(
        title=title_for(week, chart, published_on),
        description=f"{description}\n\n{' '.join(hashtags)}\n",
        tags=tags_for(chart, materialised),
        hashtags=hashtags,
        video=video,
        thumbnail=thumbnail,
        bundle_hash=bundle_hash,
    )
