"""Ticket 05 — the identity key, and ticket 17's per-field priority.

⚠️ **The ISBN is the key everything hangs on**: ticket 14's dedupe (`chart + ISBN`), ticket 01's week-over-week diff,
and ticket 05's cover lookup all use it. A wrong identity therefore does not produce a wrong *field* — it produces a
wrong **row**, and the error cascades into the diff where nothing looks wrong.

⚠️ **An identity must be corroborated like anything else** (ticket 17): a title with no ISBN falls back to
`title + author + publisher` and is marked unresolved, rather than being given a synthesised key two books could share.
"""
from __future__ import annotations

import dataclasses
from typing import Iterable, Mapping

from . import covers, delta, genre, prices, rank

#: ⚠️ Ticket 05 §3's two states. The key is an ISBN when it is **resolved**, and a normalised `title + author` when it
#: is not — recorded on the row so the weakness is **visible rather than silent**.
RESOLVED = "resolved"
UNRESOLVED = "unresolved"

#: ⚠️ The absent price, spelled once. `prices.best([])` returns this, so a row that found no offer and a row nobody
#: looked for share one value — and neither is a zero (ticket 04).
NO_PRICE = prices.Price(amount=None, retailer=None, edition=None, retailers=())


@dataclasses.dataclass(frozen=True)
class Details:
    """Everything known about one title **besides where it ranked**.

    ⚠️ **Separate from `rank.Ranked` on purpose.** Ranking is ticket 03's arithmetic over positions; this is ticket 05's
    identity-and-fields work. Keeping them apart is what lets the ranker stay testable without a network and lets the
    enrichment grow without the ranking rule changing — which matters, because `chart_logic: 1` is stamped in every
    snapshot and a change to the ranking invalidates a replay (ticket 03).

    ⚠️ **Every field is optional and every default is empty.** A vendor that gave only a title still gets a row; see
    `build`.
    """

    title: str = ""
    author: str = ""
    publisher: str = ""
    #: ⚠️ **The source's own string, never a label.** `2026-10-14`, `2026-10` or `2026` — the slide decides what each
    #: prints as (ticket 05 §2), because the words a viewer reads belong to the renderer (ADR 0003).
    published: str | None = None
    #: The vendor's own category words. `genre.slug_for` maps them, and an unknown one is `other` (ticket 26).
    category: str = ""
    price: prices.Price = NO_PRICE
    cover: covers.Cover | None = None
    #: ⚠️ Ticket 23's review signal — **cumulative over the book's whole life**, which is why it measures popularity
    #: rather than the six months. Acceptable *only because the chart states it* (ticket 15).
    rating: float | None = None
    #: ⚠️ **A rating without its count is meaningless**, and the count is also what lets `window._mean_rating` weight the
    #: shrinkage target rather than averaging a three-review book with a fifty-thousand-review one.
    ratings_count: int | None = None
    #: ⚠️ **Ticket 20's two labels, and they belong on `Details` because that is what this dataclass *is*** —
    #: *"everything known about one title besides where it ranked."* ⚠️ Where they come from is the **gate**: the
    #: conductor reads them off `corroborate.Title`, which already decided them from the sorted-first list, and puts
    #: them here. So `enrich.build` needs no new argument and stays a pure function of its inputs.
    country: str = ""
    language: str = ""


@dataclasses.dataclass(frozen=True)
class Book:
    """**One row of the chart, as the renderer reads it** — ticket 07's eight fields, flat.

    ⚠️ **This is the shape whose absence blocked the render layer.** `rank.Ranked` carries four fields, two of which
    (`isbn`, `rank`) the slide prints; the other six are here. The conductor used to drop `corroborate.Row.title` on the
    floor between the gate and the snapshot, so a chart of a hundred ISBNs would have rendered a hundred rank numerals
    beside blank space.

    ⚠️ **Values, never display strings** (ADR 0003). `genre` is a slug, `identity` is a state, `price.retailer` is a
    vendor slug, and `published` is the source's own string — the renderer's label tables own every word a viewer sees.
    """

    isbn: str
    rank: int
    weeks_on_chart: int
    is_new: bool
    #: ⚠️ `None` means **no Δ to report**, and it is `None` for two different reasons the renderer must treat the same:
    #: week one (ticket 18 — the row is a stated baseline) and a title absent from last week (ticket 07 — NEW *replaces*
    #: the Δ slot). Never `0`, which would say the title held station.
    move: int | None
    title: str
    author: str
    publisher: str
    published: str | None
    genre: str
    price: prices.Price
    identity: str
    cover: covers.Cover | None
    #: ⚠️ The week's own sales term — see `rank.Ranked.score`. It rides here because the **snapshot is the window's
    #: evidence** (ticket 23), and the listings a week's score came from are not kept.
    score: float = 0.0
    #: ⚠️ **The snapshot is this week's evidence for a six-month window** (ticket 23), so the review signal has to be
    #: *committed* — the window cannot re-fetch a rating that was true four weeks ago, and a rebuild must see what the
    #: run saw.
    rating: float | None = None
    ratings_count: int | None = None
    #: ⚠️ **Ticket 20's two labels**, and they reach here on `Details` rather than as a new parameter — so `build` stays
    #: a pure function of what it was handed, and the merge grows no second lookup.
    #:
    #: ⚠️ **Appended after `ratings_count` rather than placed beside `genre`**, which is where they belong to read: every
    #: field above this line is positional in some caller, and inserting one would silently reinterpret the rest. A
    #: constructor that took these positionally would be a defect the type checker could not see.
    country: str = ""
    language: str = ""


def build(
    ranked: Iterable[rank.Ranked],
    *,
    details: Mapping[str, Details],
    previous: Mapping[str, int] | None,
) -> tuple[Book, ...]:
    """The chart's rows, enriched — ticket 05's fields joined onto ticket 03's ranking.

    ⚠️ **A missing `Details` costs the *fields*, never the row.** A book both vendors agree is selling does not stop
    being on the chart because Google Books has no pub date for it — and dropping it would make the chart quietly
    shorter than the list it claims to rank. ⚠️ **That is the opposite of ticket 18's spine rule**, where a missing
    *vendor* makes the whole chart absent: *"a degraded chart is a wrong chart."* A degraded *field* is ordinary.

    ⚠️ **`previous` is threaded through rather than diffed here**, so this module never decides *which* week is
    compared — that is ticket 01's window, and `delta.move` is its only implementation.
    """
    return tuple(
        Book(
            isbn=row.isbn,
            rank=row.rank,
            weeks_on_chart=row.weeks_on_chart,
            is_new=row.is_new,
            move=delta.move(rank=row.rank, isbn=row.isbn, previous=previous),
            title=detail.title,
            author=detail.author,
            publisher=detail.publisher,
            published=detail.published,
            # ⚠️ Mapped, never passed through: the vendors disagree about category names, and a runtime guess would not
            # be replayable (ticket 26).
            genre=genre.slug_for(detail.category),
            price=detail.price,
            # ⚠️ Tested against the ISBN rule rather than trusted: a fallback key of `title + author` is a real key for
            # a real row, and `isbn13` returning `""` for it is what tells the two apart (ticket 05 §3).
            identity=RESOLVED if isbn13(row.isbn) else UNRESOLVED,
            cover=detail.cover,
            # ⚠️ The week's sales term, which the **window** aggregates across weeks (ticket 23).
            score=row.score,
            # ⚠️ Carried into the snapshot because the **window** needs them and cannot re-fetch them (ticket 23).
            rating=detail.rating,
            ratings_count=detail.ratings_count,
            # ⚠️ Ticket 20's labels — straight through, because the gate already decided them and this module's job is to
            # join what it was handed rather than to have an opinion about it.
            country=detail.country,
            language=detail.language,
        )
        for row in ranked
        for detail in (details.get(row.isbn, Details()),)
    )


def coverage(books: Iterable[Book]) -> int:
    """How many of a chart's rows have a cover — ticket 05 §4's number, for ticket 16's collage.

    ⚠️ **Reported, not merely recorded.** Ticket 16's rule is that a chart whose coverage is low enough for the hero row
    to be mostly placeholder has a thumbnail that is **not representative of the chart** — so the count is what lets a
    run say so *before* publishing, rather than a statistic nobody reads.
    """
    return sum(1 for book in books if book.cover is not None)


#: ⚠️ The ISBN-13 prefix for a title that was published as ISBN-10. A book that was *only* ever ISBN-13 carries its own
#: prefix (978 or 979) and must not be re-prefixed.
PREFIX = "978"


def _check_digit(body: str) -> str:
    """The EAN-13 check digit for a twelve-digit body.

    ⚠️ **Recomputed, never carried over.** An ISBN-10's check digit is computed by a different rule and is not valid
    for a thirteen-digit ISBN — so an implementation that prefixed `978` and kept the old digit would produce a
    plausible string matching no real book, and nothing downstream could tell.
    """
    total = sum(
        int(digit) * (1 if position % 2 == 0 else 3)
        for position, digit in enumerate(body)
    )
    return str((10 - total % 10) % 10)


def isbn13(raw: str) -> str:
    """The ISBN-13 for a ten- or thirteen-digit ISBN, or `""` when the input is not one.

    ⚠️ **`""` rather than a guess.** A caller that gets an empty string knows the identity is unresolved and can mark
    the row; a caller handed a fabricated key would have no way to tell.
    """
    digits = "".join(
        character for character in raw if character.isdigit() or character in "Xx"
    )

    if len(digits) == 13:
        return digits
    if len(digits) != 10:
        return ""

    body = f"{PREFIX}{digits[:9]}"
    return body + _check_digit(body)
