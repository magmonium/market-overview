"""Ticket 17 — corroboration, **reported rather than required**.

⚠️ ⚠️ **REVERSED 2026-10-15: every title any declared list carries is admitted, and corroboration is *carried* on the
row instead of gating it.** Ticket 17's rule was that a title enters a chart only when **two vendors** carry it — and
the arithmetic that killed it is worth recording, because the rule was not wrong so much as *unsatisfiable*:

    the `english` chart declares two vendors (NYT, Indie)
    the gate admits a title only when two *different vendors* carry it
    ⇒ the chart can only ever rank the *intersection* of those two lists — **16 rows**, against a "Top 100" title

⚠️ **And it was worse than a short chart: it made a chart impossible.** `all-language` has one vendor and `comics` one
usable one, so under an intersection gate **neither could admit a single title, ever** — which is why both shipped
absent every week and looked like a sourcing failure rather than a rule that could not be met.

⚠️ **What replaces it.** The chart ranks the **union**: every title any declared list carries, deduplicated by ISBN,
ordered by ticket 03's score — which *already* sums each source's weighted position, so **a title on three lists still
out-ranks a title on one**. Corroboration did not stop mattering; it stopped being a filter and became the ranking.

⚠️ **The vendor is still the unit**, and that has not changed: Amazon.in's several lists are **one voice**, so
`Title.sources` counts lists and ticket 03's score weights them by vendor. Counting a vendor's own lists as several
corroborating voices would still be *"a lie told in arithmetic"*.

⚠️ ⚠️ **And one consequence of this reversal is still open — latent, not active, and it belongs to ticket 03.** That
score sums each *list*, so a vendor declaring **two lists a title could appear on twice** would count twice: exactly
the lie above. ⚠️ **No declared chart can currently do that** — `english`'s two NYT lists are fiction and nonfiction, and
one book cannot be on both — so it is a guard to add rather than a defect to repair. ⚠️ It is recorded here because a
reader of this docstring would otherwise reasonably believe the weighting is already per vendor, and it is not.

⚠️ **Every admitted title keeps the lists that carried it.** That half of auditability is unchanged, and it is now the
*only* thing standing where the gate used to be: recording just the winner would let the chart *assert* a fact rather
than *show* why it believes it.
"""
from __future__ import annotations

import dataclasses
from typing import Iterable

from . import charts, identity, prices


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

    #: ⚠️ ⚠️ **The work, which is what the chart ranks** (ticket 32) — `identity.work(title, author)`, and the key every
    #: stage after this one groups by. ⚠️ It is **not** the ISBN: an ISBN identifies an *edition*, so keying on it ranked
    #: one book twice whenever two stores sold different printings of it (measured: the English chart held 92 distinct
    #: titles in 100 rows). ⚠️ The two fields are kept apart rather than folded together because they answer different
    #: questions — `key` is *what this row is*, `isbn` is *which product it came from* — and only the second one is a
    #: cover's filename (`covers.path_for`).
    key: str
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


def group(rows: Iterable[Row], *, vendors: Iterable[str] | None = None) -> list[list[Row]]:
    """**The chart's grouping rule, in one place** — the union of two *exact* relations (ticket 32).

    - **(a) the work key** — same title and same author, which merges the **editions** of one book. Ticket 14's
      `chart + ISBN` could not: two printings are two ISBNs, so the chart ranked one book twice.
    - **(b) a shared real ISBN** — which merges rows the work key **splits**, because two lists that spell a title
      differently still agree on the product.

    ⚠️ ⚠️ **Both are here because the first version of this rule had only (a), and the week's own responses showed what
    that costs**: on 2026-W41 the work key alone produced **246 groups where the ISBN alone produced 223** — it split
    **30** ISBN groups in order to merge **11**. ⚠️ The examples are exactly the shape a single key cannot handle, one
    book listed twice under two titles: `9781464249648` is `The Witch (Deluxe Edition)` on one list and `The Witch` on
    another, and `0063577541` is `Partita` with an author on one list and without one on another.

    ⚠️ **The union is the coarsest of the two partitions**, so it makes every merge either rule justifies and neither
    rule's split. It is still **exact**: both relations are equalities on a value the vendor stated.

    ⚠️ **`vendors` filters, and it is an argument rather than something read off the rows** for the reason the gate's own
    docstring gives: evidence from a source the chart does not declare is not evidence for that chart (ticket 18's
    spine). ⚠️ **It defaults to `None`, which filters nothing** — and that is not a convenience: ticket 32's migration
    merges a *recorded* snapshot, whose rows carry no list at all (the bundle has no `sources` field), so it must be able
    to ask for the grouping without the filter.

    ⚠️ **No representative is chosen here.** A group's fields are a *separate* decision — the gate takes the sorted-first
    row, and the migration takes the best-ranked one — so this function returns the groups and nothing else.
    """
    allowed = None if vendors is None else set(vendors)
    parent: list[int] = []

    def find(index: int) -> int:
        """The group an index belongs to, path-compressed — a union-find because the two relations **overlap**."""
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def join(left: int, right: int) -> None:
        """Merge two groups. ⚠️ **The lower index wins**, so the result does not depend on the order rows arrived in."""
        left, right = find(left), find(right)
        if left != right:
            parent[max(left, right)] = min(left, right)

    by_work: dict[str, int] = {}
    by_isbn: dict[str, int] = {}
    placed: list[tuple[Row, int]] = []

    for row in rows:
        if allowed is not None and vendor_of(row.list) not in allowed:
            continue
        work = identity.work(row.title, row.author)
        index = by_work.get(work)
        if index is None:
            index = len(parent)
            parent.append(index)
        #: ⚠️ `isbn13` returns `""` for a synthetic key, so a store's own id can never *unite* two groups — only a real
        #: ISBN can, and that is the whole point of the relation.
        isbn = identity.isbn13(row.isbn)
        if isbn:
            other = by_isbn.get(isbn)
            if other is not None:
                join(index, other)
            by_isbn[isbn] = find(index)
        by_work[work] = find(index)
        placed.append((row, find(index)))

    grouped: dict[int, list[Row]] = {}
    for row, index in placed:
        grouped.setdefault(find(index), []).append(row)
    return list(grouped.values())


def admit(rows: Iterable[Row], *, chart: charts.Chart) -> Result:
    """Split the rows into what the chart may rank and what waits on the watchlist.

    ⚠️ **Rows from an undeclared vendor are ignored rather than counted.** A chart's `vendors` are its *spine*
    (ticket 18), so evidence from a source the chart does not declare is not evidence for that chart — otherwise a
    stray row could quietly corroborate a title the chart has no business ranking.

    ⚠️ **The grouping itself lives in `group`** (ticket 32) — the union of the work key and a shared ISBN — and it is
    shared rather than inlined because a *second* caller needs the identical rule: ticket 32's migration merges a
    recorded snapshot, and a migration that re-implemented the rule would be a second place for it to drift.
    """
    groups = [
        sorted(found, key=lambda row: row.list) for found in group(rows, vendors=chart.vendors)
    ]

    admitted: list[Title] = []
    parked: list[Title] = []

    # ⚠️ Ordered by the group's own key, so the output is a function of the rows rather than of the union-find's indices.
    for seen in sorted(groups, key=lambda rows: identity.work(rows[0].title, rows[0].author)):
        title = Title(
            # ⚠️ ⚠️ **The key is derived from the *same* row every other field comes from** — the sorted-first one.
            # That is the rule this module already uses for the title, the author and the labels, so the key can never
            # disagree with the title printed beside it. ⚠️ A group merged by ISBN has **several** work keys and must
            # pick one; this is the module's existing rule for picking one, and the alternative — the lowest key —
            # would name a row after whichever spelling happened to sort first in the alphabet.
            key=identity.work(seen[0].title, seen[0].author),
            # ⚠️ **The ISBN is the *sorted-first* row's own**, unchanged from before (ticket 32 changed the grouping, not
            # this). ⚠️ A merged row therefore takes the cover, the price and the identity state of one of its editions —
            # deliberately, because ticket 05's cover order already prefers *the list's own image* and a group has no
            # single product to point at.
            isbn=seen[0].isbn,
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
            # ⚠️ **The *lists* that carried it, deduplicated** (ticket 32). A list can carry one title twice — BoiChitro
            # ranks `Chandmama` at three positions — and a source named twice is still one source (ticket 17).
            sources=tuple(sorted({row.list for row in seen})),
        )
        # ⚠️ ⚠️ **Admitted, not gated** — see the module docstring. This line used to read
        # `(admitted if len(voices) >= VENDORS_REQUIRED else parked)`, and the condition is what made a two-vendor chart
        # rank 16 books and a one-vendor chart rank none.
        admitted.append(title)

    # ⚠️ **`parked` is empty by construction now.** The field stays because `Result` is a shape several callers and a
    # dozen tests already speak — and ⚠️ **nothing became less visible**: a single-list title used to be *held back* with
    # its status recorded, and today it is *admitted* with that same status, which is strictly more.
    return Result(admitted=tuple(admitted), parked=tuple(parked))
