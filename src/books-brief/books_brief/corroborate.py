"""Ticket 17 — the corroboration gate.

⚠️ **A title enters a chart when two *vendors* carry it.** Not two lists: a vendor is a *source*, and Amazon.in's nine
language categories are one voice. Counting them separately would be *"a lie told in arithmetic"*.

⚠️ **A single-vendor title is not discarded — it is parked.** It goes on the watchlist, with its status recorded, and
does not appear in the chart. Ticket 11's ≤10 cap already needed a holding pen for its overflow, so **one list serves
both** — and *"a silent drop is indistinguishable from a title that never existed."*

⚠️ **Every admitted title keeps the lists that carried it.** That is the half of auditability that is easy to forget:
recording only the winner would let the chart *assert* a fact rather than *show* why it believes it.
"""
from __future__ import annotations

import dataclasses
from typing import Iterable

from . import charts, prices

#: ⚠️ **The floor, and it is two.** One vendor is a claim; two vendors is a corroboration. Ticket 17's rule 1.
VENDORS_REQUIRED = 2


@dataclasses.dataclass(frozen=True)
class Row:
    """One title as **one list** saw it.

    ⚠️ The list slug carries its vendor — `amazon-in/bengali` — which is what makes the vendor countable without a
    second lookup table that could disagree with the first.
    """

    list: str
    rank: int
    isbn: str
    title: str
    #: ⚠️ **Ticket 17 puts the *list's* author ahead of every enrichment source** — *"title / author: the vendor that
    #: published the list the title ranked on"*. It rides here for the same reason the title does: the gate is where a
    #: row's fields are still attributable to the vendor that supplied them, and a field dropped here cannot be
    #: recovered later. ⚠️ Empty rather than absent, because a vendor that carries no author is ordinary.
    author: str = ""
    #: ⚠️ **The date the vendor says it published this list** — ticket 10's freshness guard, and the *only* evidence
    #: available for it. It rides the row for the same reason the list slug does: it is a property of the list, every row
    #: of that list carries the same one, and keeping it here means the guard is a pure function of the rows.
    #:
    #: ⚠️ **Empty means *this vendor did not date its list*, and that is stale, not fresh** — see `freshness`.
    published: str = ""
    #: ⚠️ **Ticket 20's two labels, and they are properties of the *list*** — so they ride here beside the slug, which is
    #: the other thing every row of a list shares. A client takes them from the `charts.Listing` it was asked for.
    #:
    #: ⚠️ **Empty is the honest value when the list declared neither**, and the renderer reads empty as *no label* — the
    #: same state as a label that does not vary (ticket 20). A defaulted `in` would put a country on every row of every
    #: chart, including the English chart's, where ticket 19 says neither label should appear.
    country: str = ""
    language: str = ""
    #: ⚠️ **What the card carries beyond the chart's skeleton**, and they ride here for the reason this dataclass's
    #: `author` already gives: *"a field dropped here cannot be recovered later."* ⚠️ Ticket 17's per-field priority is
    #: what consumes them — the **list** comes first and Google Books is the second opinion — so a field the list
    #: supplied but the gate dropped would silently become Google's, or nobody's.
    publisher: str = ""
    #: ⚠️ **The list's own image, undownloaded.** `covers.download` fetches the bytes and hashes them (ticket 05); a URL
    #: is what a parser can honestly produce, and a `covers.Cover` here would claim bytes nobody holds.
    cover_url: str = ""
    #: ⚠️ Ticket 04 — and it arrives as a **value**: `329.0`, not `₹329.00`. The symbol, the grouping and the sign are
    #: the renderer's (ADR 0003), and ⚠️ `retailers` is the **count consulted**, which is what forbids the word *best*
    #: on a price nobody compared.
    price: prices.Price = prices.Price(amount=None, retailer=None, edition=None, retailers=())
    #: ⚠️ Ticket 23's review signal — **both halves, from the same card as the rank.** That is why the review term needs
    #: no second lookup for a scraped row, and why the count is not optional: a rating without it cannot be weighted.
    #:
    #: ⚠️ `None` is *unrated*, never `0.0` — a zero would be a claim the vendor did not make, and ticket 23's rule is
    #: that unrated is not penalised.
    rating: float | None = None
    ratings_count: int | None = None


@dataclasses.dataclass(frozen=True)
class Title:
    """A title the gate has seen, and **which lists carried it**."""

    isbn: str
    title: str
    sources: tuple[str, ...]
    #: ⚠️ Carried through the gate so the merge can prefer it (ticket 17). See `Row.author`.
    author: str = ""
    #: ⚠️ **Ticket 20's labels, decided here for the same reason the title and the author are**: this is the last point
    #: at which a field is still attributable to the list that supplied it, and a field dropped here cannot be recovered.
    #:
    #: ⚠️ **They come from the *sorted-first* list, exactly as the title does** — because a title carried by both an
    #: Indian and a Bangladeshi list has two right answers, and *"the same week, re-rendered"* (ticket 03) means the
    #: choice cannot depend on which vendor answered first.
    country: str = ""
    language: str = ""
    #: ⚠️ **The rest of what the list's own card carries** — see `Row`, where the argument is made in full. They are
    #: here because the gate is the last point at which a field is still attributable to the list that supplied it, and
    #: ⚠️ ticket 17's per-field priority runs one way: **the list first, Google Books second.**
    publisher: str = ""
    cover_url: str = ""
    price: prices.Price = prices.Price(amount=None, retailer=None, edition=None, retailers=())
    rating: float | None = None
    ratings_count: int | None = None


@dataclasses.dataclass(frozen=True)
class Result:
    """What the gate did: what it let through, and what it held back."""

    admitted: tuple[Title, ...]
    parked: tuple[Title, ...]


def vendor_of(list_slug: str) -> str:
    """The vendor half of a list slug — `amazon-in/bengali` is `amazon-in`."""
    return list_slug.split("/", 1)[0]


def admit(rows: Iterable[Row], *, chart: charts.Chart) -> Result:
    """Split the rows into what the chart may rank and what waits on the watchlist.

    ⚠️ **Rows from an undeclared vendor are ignored rather than counted.** A chart's `vendors` are its *spine*
    (ticket 18), so evidence from a source the chart does not declare is not evidence for that chart — otherwise a
    stray row could quietly corroborate a title the chart has no business ranking.
    """
    by_isbn: dict[str, list[Row]] = {}
    for row in rows:
        if vendor_of(row.list) not in chart.vendors:
            continue
        by_isbn.setdefault(row.isbn, []).append(row)

    admitted: list[Title] = []
    parked: list[Title] = []

    # ⚠️ Sorted, so the gate's output does not depend on the order the sources happened to answer in — the same
    # determinism ticket 03 requires of the ranking.
    for isbn in sorted(by_isbn):
        # ⚠️ **Sorted before a *field* is read, not merely before the key is — and that was a real defect.** The
        # `sorted` above made the *set* of admitted titles independent of the order the vendors answered in, but
        # `seen[0]` did not: the title came from whichever source happened to reply first. A re-run could therefore
        # print a different spelling of the same book, which is exactly what ticket 03's *"the same week, re-rendered,
        # must produce the same chart"* forbids — and a field is part of the chart.
        seen = sorted(by_isbn[isbn], key=lambda row: row.list)
        voices = {vendor_of(row.list) for row in seen}
        title = Title(
            isbn=isbn,
            title=seen[0].title,
            # ⚠️ Ticket 17 puts the list ahead of every enrichment source for the author, so it has to survive the
            # gate — and it comes from the same sorted-first list the title does, for the same reason.
            author=seen[0].author,
            # ⚠️ Ticket 20's labels, from the same sorted-first row and for the same reason — see `Title`.
            country=seen[0].country,
            language=seen[0].language,
            # ⚠️ And the rest of the card, from the same row for the same reason: the gate is the last point at which a
            # field is still attributable to the list that supplied it.
            publisher=seen[0].publisher,
            cover_url=seen[0].cover_url,
            price=seen[0].price,
            rating=seen[0].rating,
            ratings_count=seen[0].ratings_count,
            sources=tuple(sorted(row.list for row in seen)),
        )
        (admitted if len(voices) >= VENDORS_REQUIRED else parked).append(title)

    return Result(admitted=tuple(admitted), parked=tuple(parked))
