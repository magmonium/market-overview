"""The Amazon.in bestseller pages — **the workhorse, and the only source two of the four charts depend on.**

⚠️ **Ticket 02 names this as scraped, and the repository now says so out loud.** There is no bestsellers API, and
scraping is contrary to Amazon's conditions of use — which is a decision the reader of this product is owed rather than a
detail, and it is why ticket 17's corroboration gate is load-bearing here rather than decorative: *"Amazon's bestseller
list is the very one HWR warns 'can be gamed'."*

⚠️ **This is the first HTML in the product.** Every source the brief reads is a JSON API, so there was no parser in the
environment at all; `selectolax` is a dependency of `books-brief` alone, and its **`lexbor` backend** is the one that is
not deprecated in 1.0.

⚠️ **The ASIN is the only identifier on a card, and ticket 05 wants an ISBN.** ✅ They coincide for a physical book —
a book's ASIN *is* its ISBN-10 — so `enrich.isbn13` converts it. ⚠️ A Kindle edition's ASIN (`B08N67G4CC`) is **not an
ISBN**, and there the row keeps the ASIN: it is the vendor's own stable identifier, not the synthesised `title + author`
key ticket 05 refuses, and `enrich.isbn13` returning `""` is what marks the identity **unresolved** downstream.

⚠️ **A card with no rank badge is skipped rather than numbered.** Its position in the document is an inference, and on a
page where one card failed to render the inference is wrong for every card after it — so the chart is one short instead
of silently mis-ranked. ⚠️ And a page with no cards at all returns **nothing rather than raising**, because a block page,
a failed render and a genuine empty list look identical from here; `freshness.guard` already treats a vendor that
produced nothing as **missing** (ticket 18), and a parser that raised would take the other three charts with it.
"""
from __future__ import annotations

import re
from typing import Iterator

from curl_cffi import requests
from selectolax.lexbor import LexborHTMLParser

from .. import charts, corroborate, enrich, prices
from . import Page

#: The vendor slug, as `charts` spells it.
VENDOR = "amazon-in"

# ⚠️ **The selectors, named once.** They are the whole of this module's knowledge of Amazon's markup, and a page change
# shows up as one of these returning nothing rather than as a wrong field — which is why the parser drops a card it
# cannot rank instead of guessing at it.
CARD = "#gridItemRoot"
ASIN = "[data-asin]"
RANK = "span.zg-bdg-text"
TITLE = "a.a-link-normal.aok-block > span > div"
PUBLISHER = "a.a-link-child div"
STARS = "a[aria-label*='out of 5 stars']"
PRICE = "span[class*='p13n-sc-price']"
FORMAT = "div.a-row.a-size-small span"
IMAGE = "img.p13n-product-image"

_RANK = re.compile(r"#(\d+)")
#: ⚠️ **Both halves in one attribute** — `4.5 out of 5 stars, 3,661 ratings`. The count is optional because a book with
#: a rating but no count is not a shape Amazon produces; the *whole* attribute is optional, which the fixture proves.
_STARS = re.compile(r"([\d.]+) out of 5 stars(?:, ([\d,]+) ratings?)?")
#: ⚠️ `₹329.00` → `329.00`. The symbol is stripped rather than parsed: ADR 0003 keeps the currency out of the snapshot,
#: and a second currency would be a change to the renderer rather than to this regex.
_MONEY = re.compile(r"([\d,]+(?:\.\d+)?)")


def _text(node: object) -> str:
    """A node's text, whitespace collapsed.

    ⚠️ Amazon's markup is full of newlines and indentation, and a title that keeps a line break prints as two lines on a
    slide — which is the kind of wrongness that looks like a layout bug rather than a parser bug.
    """
    if node is None:
        return ""
    return " ".join(node.text().split())  # type: ignore[attr-defined]


def _stars(label: str) -> tuple[float | None, int | None]:
    """The rating and its count, or two `None`s.

    ⚠️ **Never `(0.0, 0)`.** An unrated book is *no opinion*, and ticket 23's Bayesian average already treats a missing
    rating that way rather than as a bad one — a zero would be a claim the vendor did not make.
    """
    match = _STARS.search(label)
    if match is None:
        return None, None
    count = match.group(2)
    return float(match.group(1)), int(count.replace(",", "")) if count else None


def _price(raw: str) -> float | None:
    """`₹329.00` → `329.0`, or `None` when the card states no price."""
    match = _MONEY.search(raw)
    return float(match.group(1).replace(",", "")) if match else None


#: ⚠️ **The address is declared by the chart, not by a table here** (ticket 29).
#:
#: ⚠️ This module used to hold a slug→node table, which put the same fact in two places: `charts.py` declared
#: `amazon-in/hindi` and eight more per-language lists **Amazon does not publish**, while this table named the one list it
#: does — and nothing connected the two, so neither could tell the other it was wrong.
#: ⚠️ Now `charts.Listing.address` is the **only** copy, and `Listing.__post_init__` refuses a scraped list without one.

#: ⚠️ Twenty-five seconds: long enough for a 450 KB page, short enough that a wrong address fails rather than hangs.
TIMEOUT = 25


def fetch(chart: charts.Chart, *, week: str) -> Iterator[Page]:
    """Every Amazon.in list this chart reads, fetched — **and parsed by nobody**.

    ⚠️ **Only the lists the chart declares are read**, and each is fetched from the address it declares. ⚠️ **That address
    *is* the list's identity here**: an Amazon bestseller page names no list at all, so a wrong address fetches a
    different list under this one's name — the quietest possible wrong answer, since the rows parse perfectly and
    describe the wrong books.

    ⚠️ **The refusal moved to declaration time** (ticket 29). This function used to raise `MissingNodeError` for a list it
    had no node for; now `charts.Listing` will not construct a scraped list without an address at all, so by the time
    this runs there is nothing left to guess at. ⚠️ That is the difference between a run that refuses and a spec that is
    wrong — and it is why the rule lives in a constructor rather than in a comment.

    ⚠️ It yields `Page`s rather than rows — see `fetch/__init__`. The conductor writes each page to
    `store/<week>/raw/` **before** `parse` sees it, because a response written after a successful parse can never show
    what the parser was *given* on the day the parser was what broke.
    """
    for entry in chart.lists:
        vendor, _, name = entry.slug.partition("/")
        if vendor != VENDOR:
            continue

        # ⚠️ `curl_cffi` impersonating Chrome, the same trick ticket 02 names for Anandabazar behind Akamai. A plain
        # fetcher is answered with a block page, which parses to **no rows** — and a parser that returns nothing is a
        # vendor the freshness guard calls *missing*, so the failure is visible rather than silent.
        response = requests.get(entry.address, impersonate="chrome", timeout=TIMEOUT)
        response.raise_for_status()
        yield Page(
            listing=entry,
            name=f"{VENDOR}-{name}.html",
            payload=response.content,
        )


def parse(payload: bytes, *, listing: charts.Listing) -> list[corroborate.Row]:
    """One bestseller page, shaped into rows.

    ⚠️ **The list slug comes from the declaration, and this is the opposite of the NYT rule.** NYT's response carries
    `list_name_encoded`, so its rows are tagged with what the vendor *said* and a mismatch is visible. ⚠️ An Amazon
    bestseller page carries **no list name at all** — the address is the only thing that knows — so the declaration is
    the only honest source, and a wrong address is invisible either way.

    ⚠️ `listing` is required for the same reason it is in `nyt.parse`: a parser cannot tag a row with where it came from
    without being told, and ticket 20's country and language have nowhere else to come from.
    """
    tree = LexborHTMLParser(payload.decode("utf-8", errors="replace"))

    rows: list[corroborate.Row] = []
    for card in tree.css(CARD):
        rank = _RANK.search(_text(card.css_first(RANK)))
        asin_node = card.css_first(ASIN)
        asin = (asin_node.attributes.get("data-asin") or "") if asin_node else ""
        # ⚠️ **Both are required, and neither is inferred.** No badge means nobody stated the position; no ASIN means no
        # key to corroborate on — and a row with a synthesised key is the collision ticket 05 refuses.
        if rank is None or not asin:
            continue

        stars = card.css_first(STARS)
        rating, count = _stars(
            (stars.attributes.get("aria-label") or "") if stars else ""
        )
        image = card.css_first(IMAGE)
        amount = _price(_text(card.css_first(PRICE)))

        rows.append(
            corroborate.Row(
                list=listing.slug,
                rank=int(rank.group(1)),
                # ⚠️ The ISBN when the ASIN is one, the ASIN when it is not — see the module docstring.
                isbn=enrich.isbn13(asin) or asin,
                title=_text(card.css_first(TITLE)),
                publisher=_text(card.css_first(PUBLISHER)),
                cover_url=(image.attributes.get("src") or "") if image else "",
                # ⚠️ The retailer and the count are set **only when a price was found**, so an unpriced row cannot claim
                # a comparison that did not happen — and ticket 04 forbids the word *best* off one listing.
                price=prices.Price(
                    amount=amount,
                    retailer=VENDOR if amount is not None else None,
                    edition=_text(card.css_first(FORMAT)) or None,
                    retailers=(VENDOR,) if amount is not None else (),
                    # ⚠️ **Amazon.in quotes rupees**, and it is the only vendor here that does — which is exactly why
                    # the currency is on the price rather than a constant in the model.
                    currency=prices.CURRENCY,
                ),
                rating=rating,
                ratings_count=count,
                country=listing.country,
                language=listing.language,
            )
        )

    return rows

