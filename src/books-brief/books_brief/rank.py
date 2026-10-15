"""Ticket 03 — the chart logic.

⚠️ **The rule, in the order ticket 03 fixed it:** normalise each source to a *position*, weight it by *depth*, **sum**
— which is the corroboration bonus — apply an *incumbency* multiplier, then **admit at most ten newcomers**. Every
step is deterministic: the same inputs must always produce the same chart, or a week cannot be replayed.

⚠️ **The ≤10 cap is an *admission rule*, not a multiplier** (ticket 11). A multiplier makes churn *unlikely*; only a
rule makes it *bounded* — and the brief asked for a hard number, not a tendency.

⚠️ **Week one is a different behaviour, not an edge case.** With no previous chart every title reads as new, so the
cap would admit ten and ship a "Top 100" holding ten books (ticket 03, and ticket 18's 26-week ramp).
"""
from __future__ import annotations

import dataclasses
from typing import Iterable, Mapping

from . import corroborate

#: The chart's size.
LIMIT = 100

#: ⚠️ **The brief's hard constraint** — *"new entry should not be more then 10"* (ticket 11).
NEWCOMER_CAP = 10

#: The incumbency multiplier's shape (ticket 03, step 4). ⚠️ `WEEKS_CAP` stops a long-running title becoming
#: impossible to dislodge: past eight weeks, being established stops buying any more protection.
GAMMA = 0.15
WEEKS_CAP = 8

#: ⚠️ The reference depth for ticket 03's depth-weighting: a list this deep counts fully, a shallower one counts
#: proportionally less. A hundred because that is the chart's own size, so "deep enough to be a real chart" is the
#: bar a list has to clear.
N_REF = 100

#: ⚠️ **Ticket 23's credibility weight, in ratings.** A title with this many ratings is trusted at its own mean; a title
#: with a tenth of it is shrunk nine tenths of the way to the global mean. Fifty because that is roughly where a rating
#: stops being an anecdote — and ⚠️ it is a *judgement*, which is why it is a named constant and not a literal.
PRIOR = 50.0

#: ⚠️ **How much a review is worth beside a sales position** (ticket 23's deliverable: *"the ranking formula — sales
#: term, review term, and their weights"*). A weight rather than a derivation, and recorded here so tuning the chart is
#: a data change. ⚠️ Chosen so that **five stars from fifty thousand readers is worth well under one sales position** —
#: otherwise the chart is a popularity contest with sales as a footnote, which is not what the brief asked for.
REVIEW_WEIGHT = 0.2

#: ⚠️ The mean a thin rating is shrunk toward, when the caller does not know the window's own. The caller *should* —
#: `window.py` computes it from the week's rows — and this default is the "no information" value, not a preference.
DEFAULT_MEAN = 4.0


@dataclasses.dataclass(frozen=True)
class Listing:
    """One list's view of a title: **where it ranked, and how deep the list went.**

    ⚠️ The size is not decoration. Without it, a #1 in a twenty-deep category would out-score a #1 in a hundred-deep
    one — which is how a narrow subcategory becomes a bestseller (the HWR warning ticket 17 quotes).
    """

    list: str
    rank: int
    size: int


@dataclasses.dataclass(frozen=True)
class Candidate:
    """A title the gate admitted, with the score its sources gave it."""

    #: ⚠️ ⚠️ **The work** (ticket 32) — `corroborate.Title.key`, and what the whole chart is keyed by from here on: the
    #: ordering's tie-break, the incumbency test, the watchlist and the window. ⚠️ `isbn` rides beside it because it is
    #: a *field* of the row — the product it came from, and the name of its cover file — not its identity.
    key: str
    isbn: str
    score: float
    weeks_on_chart: int = 0
    #: ⚠️ Ticket 23's review signal — **cumulative over the book's whole life**, which is why it measures popularity
    #: rather than the six months. Acceptable *only because the chart states it* (ticket 15).
    rating: float | None = None
    #: ⚠️ **A rating without its count is meaningless.** 5.0 from three reviews must not outrank 4.6 from fifty
    #: thousand, so the count is what lets the term decide how far to trust the rating at all.
    ratings_count: int | None = None


@dataclasses.dataclass(frozen=True)
class Ranked:
    """One row of the chart."""

    #: ⚠️ **The work, not the ISBN** (ticket 32) — see `Candidate.key`. ⚠️ This is the field the snapshot carries so
    #: that next week's Δ and the six-month window can recognise this row again, which is why it has to be the identity
    #: rather than the product: a row's ISBN can change when a store switches edition, and its work cannot.
    key: str
    isbn: str
    rank: int
    weeks_on_chart: int
    is_new: bool
    #: ⚠️ **The week's own sales term, committed to the snapshot** — ticket 23's `score`, and it is here because the
    #: six-month window aggregates these and **cannot recompute them**: the listings a week's score came from are not
    #: in the snapshot. ⚠️ And it has to be the *candidate's* score rather than the chart rank, because the chart rank
    #: depends on the window — aggregating it would be circular.
    score: float = 0.0


@dataclasses.dataclass(frozen=True)
class Board:
    """The chart, and what it held back."""

    ranked: tuple[Ranked, ...]
    watchlist: tuple[str, ...]


def points(entry: Listing) -> float:
    """⚠️ Ticket 03, step 1 — the title's **position** in its list, not its raw rank.

    `(n + 1 − rank) / n`, so a #1 in a ten-book list and a #1 in a hundred-book list both score **1.0**. Position,
    not prestige: a list's *length* is a different question from a title's *place* in it, and step 2 is where the
    length is paid for.
    """
    return (entry.size + 1 - entry.rank) / entry.size


def weight(entry: Listing, *, weights: Mapping[str, float]) -> float:
    """⚠️ Ticket 03, step 2 — the vendor's weight, scaled by **how deep the list went**.

    A hundred-deep list counts fully; a twenty-deep one counts a fifth. This is the step that matters most on the
    all-language chart, where Amazon.in's per-language categories differ wildly in depth (ticket 02).
    """
    vendor = corroborate.vendor_of(entry.list)
    return weights.get(vendor, 1.0) * min(1.0, entry.size / N_REF)


def score(listings: Iterable[Listing], *, weights: Mapping[str, float]) -> float:
    """⚠️ Ticket 03, step 3 — **the sum, which *is* the corroboration bonus.**

    A title carried by three lists accumulates three terms; a single-source title accumulates one. No separate
    multiplier is needed, and that is the point: *"genuine and authentic"* becomes arithmetic rather than a promise.
    """
    return sum(weight(entry, weights=weights) * points(entry) for entry in listings)


def review_term(
    rating: float | None,
    count: int | None,
    *,
    mean: float = DEFAULT_MEAN,
    prior: float = PRIOR,
) -> float:
    """⚠️ **Ticket 23's credibility-weighted review term — a Bayesian average, not a mean.**

    The ticket's own sentence is the whole specification: *"5.0 from 3 reviews must not outrank 4.6 from 50,000."* A raw
    mean does exactly that, and the chart then **rewards obscurity** — because a thin rating is not evidence of quality,
    it is evidence of nobody having looked.

    So a rating is shrunk toward `mean` in proportion to how few ratings back it:

    ```
    (rating × count + mean × prior) / (count + prior)
    ```

    ⚠️ **A rating at the mean lands on the mean however many reviews it has**, which is the property that makes this a
    *credibility* weight rather than a fudge: the shrinkage moves a thin rating's **distance** from the mean and never
    the mean itself.

    ⚠️ **No rating is `0.0`, not a middling default.** An unrated book has not been judged average — it has not been
    judged — and inventing a score for it would let it outrank a rated one. ⚠️ And the caller then carries that zero
    through `final_score` as *no contribution*, so an unrated title is never **penalised** for the enrichment source not
    carrying a rating, which for Bengali books is most of them.
    """
    if rating is None or not count:
        return 0.0
    return (rating * count + mean * prior) / (count + prior)


def final_score(candidate: Candidate, *, mean: float = DEFAULT_MEAN) -> float:
    """⚠️ Ticket 03's step 4 **and** ticket 23's two terms — the whole formula, in one place.

    ```
    (sales + REVIEW_WEIGHT × review) × (1 + γ·min(weeks_on_chart, cap))
    ```

    ⚠️ **The sales term is no longer a weekly-rank aggregate** (ticket 23's amendment): it is the accumulated
    six-month one, computed by `window.py` and handed in as `candidate.score`. This function does not care how it was
    built, which is what keeps the ranking rule readable while the window changes underneath it.

    ⚠️ **The incumbency multiplier applies to both terms**, deliberately: an incumbent is harder to dislodge *at the
    same standing*, and standing is now sales plus reviews together.
    """
    reviews = REVIEW_WEIGHT * review_term(
        candidate.rating, candidate.ratings_count, mean=mean
    )
    return (candidate.score + reviews) * (
        1 + GAMMA * min(candidate.weeks_on_chart, WEEKS_CAP)
    )


def chart(
    candidates: Iterable[Candidate],
    *,
    previous: tuple[str, ...] | None,
    limit: int = LIMIT,
    cap: int = NEWCOMER_CAP,
    mean: float = DEFAULT_MEAN,
) -> Board:
    """Rank the candidates and admit them.

    ⚠️ **`previous is None` means there is no previous week — which is week one**, so the cap is **bypassed**
    (ticket 03). ⚠️ An empty tuple is *not* the same thing: it says a previous chart existed and was empty, and the
    cap applies. Collapsing the two would silently switch the cap off for every chart that churned completely.
    """
    incumbents = set(previous or ())
    week_one = previous is None

    # ⚠️ The order is **total**: score descending, then key ascending (ticket 03, step 6). A tie that fell back on
    # iteration order would let the same week rank two ways — and a non-replayable chart is not a chart.
    # ⚠️ The tie-break is the **work key** rather than the ISBN (ticket 32): the ISBN is a field that can differ between
    # two rows carrying the same work, so it cannot be the thing that decides their order.
    ordered = sorted(
        candidates,
        key=lambda candidate: (-final_score(candidate, mean=mean), candidate.key),
    )

    ranked: list[Ranked] = []
    watchlist: list[str] = []
    newcomers = 0

    for candidate in ordered:
        is_new = candidate.key not in incumbents

        if is_new and not week_one:
            if newcomers >= cap:
                # ⚠️ The overflow is **held**, not dropped: the watchlist is where ticket 17 parks its single-vendor
                # titles too, so one list serves both, and a silent drop would be indistinguishable from a title
                # that never existed.
                watchlist.append(candidate.key)
                continue
            newcomers += 1

        if len(ranked) >= limit:
            watchlist.append(candidate.key)
            continue

        ranked.append(
            Ranked(
                key=candidate.key,
                isbn=candidate.isbn,
                rank=len(ranked) + 1,
                weeks_on_chart=candidate.weeks_on_chart,
                is_new=is_new,
                # ⚠️ The **pre-incumbency** score — the sales term itself, not the adjusted one. The window averages
                # this across weeks and applies the incumbency rule once, at the end; storing the adjusted value would
                # apply it twice and compound it.
                score=candidate.score,
            )
        )

    return Board(ranked=tuple(ranked), watchlist=tuple(watchlist))
