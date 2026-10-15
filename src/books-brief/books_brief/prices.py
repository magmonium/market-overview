"""Ticket 04 — the price layer.

⚠️ **"Best price" is never labelled "best" unless it was compared.** That rule is the whole ticket: with only one
retailer's price, the slide says *"₹399 · Amazon"* and never *"Best price ₹399"*. So this module reports **which
retailers were consulted** alongside the amount, and the renderer decides the words (ADR 0003 — values here, strings
there).

⚠️ **A missing price is `None`, never `0.0`.** The brief holds this line in `facts._number` — *"a missing value and a
real zero are different facts"* — and `₹0` would state something untrue. ⚠️ An offer that *arrives* with no amount is
the same case: Amazon.in omits the price on some listings, and that is absence, not zero.

⚠️ **The price is not a ranking input.** The chart ranks sales (ticket 03); a cheap book does not rank higher. Price is
a caption, not a signal.
"""
from __future__ import annotations

import dataclasses
from typing import Iterable

#: ⚠️ ⚠️ **There is deliberately no module-level `CURRENCY` here any more** (removed 2026-10-15).
#:
#: It used to hold `"INR"` and justify itself with *"every price this product shows is in rupees, because every chart is
#: India-anchored (ticket 12)"* — a premise three later tickets overturned, and a claim that was **wrong the moment it was
#: read**: the English chart is no longer US, the Bengali chart spans India and Bangladesh, and comics is worldwide.
#:
#: ⚠️ **The currency now lives where the vendor is known.** `Price.currency` carries it per row (ticket 04), and each
#: scraper states the one *its own page* quotes: `fetch.amazon.MARKETPLACES` pairs the five Amazon stores with their
#: currencies, and `indie.CURRENCY` / `rokomari.CURRENCY` name theirs. ⚠️ A single constant cannot be right for a product
#: whose rows are priced in five currencies — and its existence invited exactly the bug it could not prevent, because a
#: parser that forgot to set `currency` would have silently inherited rupees.


@dataclasses.dataclass(frozen=True)
class Offer:
    """One retailer's price for one book.

    ⚠️ `edition` is what the slide names as the *format* — paperback, hardcover, Kindle. **A price without its format
    is not a price**: the same title can differ threefold between them, and a reader comparing against their own copy
    needs to know which one was priced.
    """

    retailer: str
    amount: float | None
    edition: str


@dataclasses.dataclass(frozen=True)
class Price:
    """What the slide shows, and **what it was compared against**."""

    amount: float | None
    retailer: str | None
    edition: str | None
    #: ⚠️ Every retailer consulted, sorted. **This is what stops the label overclaiming** — one entry means there was
    #: no comparison to make, and the renderer can see that without knowing how the price was chosen.
    retailers: tuple[str, ...]
    #: ⚠️ **The currency the amount is denominated in** — `INR`, `USD`, `BDT` — as a **value**, so the symbol stays the
    #: renderer's (ADR 0003). ⚠️ A Bangladeshi book costs **৳180** where an Indian one costs **₹180**, and the two are
    #: not close: rendering one as the other is wrong by about a factor of one and a half while looking entirely
    #: correct.
    #:
    #: ⚠️ **Empty means *unknown*, and unknown draws no symbol.** A default of `INR` would make a parser that forgot —
    #: or a source that never said — quietly assert rupees, which is the exact failure this field exists to prevent.
    #: ⚠️ An empty currency is a price the slide can state as a bare number or omit; it is never a price it may label
    #: with the wrong sign.
    currency: str = ""


def best(offers: Iterable[Offer]) -> Price:
    """The lowest verified offer, with every retailer consulted recorded beside it.

    ⚠️ **Only offers that carry an amount compete.** An unpriced listing is not a price of zero, and letting it into
    the comparison would make "best" mean "cheapest thing we failed to read".
    """
    priced = [offer for offer in offers if offer.amount is not None]

    if not priced:
        return Price(amount=None, retailer=None, edition=None, retailers=())

    # ⚠️ Ties broken by retailer name, so the choice does not depend on the order the sources happened to answer in —
    # the same determinism ticket 03 requires of the ranking.
    winner = min(priced, key=lambda offer: (offer.amount, offer.retailer))

    return Price(
        amount=winner.amount,
        retailer=winner.retailer,
        edition=winner.edition,
        retailers=tuple(sorted({offer.retailer for offer in priced})),
        # ⚠️ **`best` cannot know the currency** — an `Offer` does not carry one, and a comparison across currencies
        # would be meaningless anyway. ⚠️ So it returns **empty**, which is honest: *this is the best price and the
        # model does not know what it is denominated in*. The parsers set it, because they are what read the source.
        currency="",
    )
