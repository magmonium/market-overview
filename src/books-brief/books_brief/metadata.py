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

#: ⚠️ ⚠️ **How wide a *tail* title is cut to when the description would not otherwise fit** (2026-10-15).
#:
#: ⚠️ Ticket 15's rule is that a list which will not fit is *"a list to shorten"* — and the measurement says **which
#: part** has to be shortened. The comics chart's description came to **9,295** characters against YouTube's **5,000**:
#: dropping the author from the tail bought **273**, while cutting tail titles to 45 bought **4,100**. ⚠️ **The titles
#: are what give, not the fields** — because comics titles are long (*The Long-Lived King: An Original The Owl House
#: Graphic Novel*) and five thousand characters holds a hundred of them only at about forty-five.
#:
#: ⚠️ It is a **ceiling**, not a fixed width: how much has to give depends on the week's titles, so `_shapes` walks down
#: from here until the description fits.
TAIL_TITLE_WIDTH = 48

#: ⚠️ **The floor the walk stops at, and past it the run refuses.** Below this a title is a *fragment* rather than an
#: abbreviation, and a description full of fragments is the silently-wrong list this module exists to refuse. ⚠️ So the
#: guard is kept — it is just no longer tripped by an ordinary week of long titles.
MIN_TAIL_TITLE_WIDTH = 24

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


def _shorten(title: str, width: int) -> str:
    """A title cut to `width`, **at a word boundary and with an ellipsis**.

    ⚠️ **The ellipsis is the whole point.** A title cut mid-word reads as a typo, and one cut with no mark reads as the
    title itself — so a reader would never learn that the video carries the rest of it. ⚠️ Word boundary first, and a
    hard cut only when the first word is already longer than the width, because no title owes anyone a space in its first
    forty characters (a Bengali or French one least of all).
    """
    if len(title) <= width:
        return title

    cut = title[: width - 1].rstrip()
    if " " in cut:
        word_cut = cut[: cut.rindex(" ")].rstrip()
        if word_cut:
            cut = word_cut
    return f"{cut}…"


def _row_line(
    row: Row, *, full: bool, tail_author: bool = True, width: int | None = None
) -> str:
    """One row — **full for the top ten, compact for the tail** (ticket 15), and shortened only if it must be.

    ⚠️ `tail_author` and `width` are the two things that give when the description is too long, and they are the two
    **cheapest** ones: the author is a bonus beside the title, and the title is cut last and visibly. ⚠️ A row that is not
    shortened keeps every field it had, so a week that fits is unaffected by any of this.
    """
    if full:
        line = f"{row.rank}. {row.title} — {row.author}"
        if row.publisher:
            line += f" — {row.publisher}"
        if row.price:
            line += f" — {row.price}"
        return line

    title = row.title if width is None else _shorten(row.title, width)
    line = f"{row.rank}. {title}"
    if tail_author:
        line += f" — {row.author}"
    return line


def _shapes() -> list[tuple[bool, int | None]]:
    """The tail shapes the description is tried in, **cheapest loss first** — see `description_for`.

    ⚠️ **`(True, None)` first, and that is what keeps this change invisible to every week that already fitted**: a
    hundred ordinary rows keep their authors and their whole titles, exactly as before.
    """
    return [
        (True, None),
        (False, None),
        *[
            (False, width)
            for width in range(TAIL_TITLE_WIDTH, MIN_TAIL_TITLE_WIDTH - 1, -1)
        ],
    ]


def description_for(
    week: str,
    chart: charts.Chart,
    rows: Iterable[Row],
    *,
    basis_weeks: int,
    published_on: str,
) -> str:
    """The full list, in two tiers, with the basis and the window stated.

    ⚠️ **The rows are shortened before the list is, and the search is what makes that safe** (2026-10-15).

    ⚠️ Ticket 15's rule is that a list which will not fit is *"a list to shorten"*, and the measurement says **which part**
    has to be shortened: the comics chart's description came to **9,295** characters against YouTube's **5,000**, and of
    that, dropping the tail's authors bought **273** while cutting tail titles to 45 bought **4,100**. ⚠️ So the titles
    give, and the shapes are tried **cheapest loss first** — see `_shapes` — with the first that fits being the one
    shipped.

    ⚠️ **The refusal is kept, and it is now the last rung rather than the first.** A list whose *top ten* will not fit
    even with a fragment for every tail title is still refused, because YouTube cuts the **tail** — the part of the list
    nobody would check.
    """
    materialised = list(rows)
    header = [
        f"TOP 100 {NAMES[chart.slug].upper()} · WEEK {week.partition('-W')[2]}",
        "",
        # ⚠️ Tickets 15 and 23: `Top 100 Bengali Books` does not say *what it ranks*, and the window is the one the
        # chart **has** — the six-month window is accumulated, so weeks 1–25 carry a smaller number here.
        f"Ranked on sales over six months, with user reviews · window: {basis_weeks} weeks",
        "",
    ]
    footer = [
        "",
        f"Sources: {', '.join(chart.vendors)}",
        "Covers: Google Books / Open Library",
    ]

    for tail_author, width in _shapes():
        built = "\n".join(
            [
                *header,
                *(
                    _row_line(row, full=row.rank <= FULL_ROWS, tail_author=tail_author, width=width)
                    for row in materialised
                ),
                *footer,
            ]
        )
        if len(built) <= DESCRIPTION_LIMIT:
            return built

    raise MetadataError(
        f"the description is {len(built)} characters even with every tail title cut to "
        f"{MIN_TAIL_TITLE_WIDTH} and its author dropped — over the {DESCRIPTION_LIMIT} YouTube keeps. "
        f"Shorten the list rather than shipping one whose tail is cut off."
    )


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
