"""The Indie Bestsellers list — **the cleanest source in the set**, and the reason is worth stating.

⚠️ A row carries **rank**, **title**, **author**, **publisher**, **price** and a **real ISBN-13** — where Amazon gives an
ASIN and PW gives a paywalled 2012 archive. ⚠️ **And the list is dated in its own URL**:
`/bestseller-list-v2/national/2026-10-14`. That date is the Wednesday *after* `2026-W41`'s Sunday, which is exactly what
`freshness.span("2026-W41")` allows — so this is the first vendor whose freshness the guard can verify **from the
response** rather than from the declaration.

⚠️ **The declaration does not match, again.** `charts.py` says `indie/fiction` and `indie/nonfiction`; what the site
publishes is `/bestseller-list-v2/national/<date>` and per-region lists (`/gliba/`, `/miba/`, …). ⚠️ That is the fourth
declaration in this set to name a list the vendor does not serve — and unlike the others, **this one is fixable without a
decision**, because the national list is plainly the list the chart meant.

⚠️ **What the parser reads and what it leaves.** The description cell is comma-separated prose —
`Yotam Ottolenghi, Ten Speed Press, $45.00, 9781984860088` — so the **price** and the **ISBN** are unambiguous but the
author and publisher are not: an author line can carry commas of its own (`James Patterson, Maxine Paetro`). ⚠️ So those
two are **left empty rather than guessed at**, which is ticket 17's own arrangement — the list supplies what it can prove,
and Google Books is the second opinion.
"""
from __future__ import annotations

import re
from typing import Iterator

from curl_cffi import requests
from selectolax.lexbor import LexborHTMLParser

from .. import charts, corroborate, enrich, freshness, prices
from . import Page

#: The vendor slug, as `charts` spells it.
VENDOR = "indie"

# ⚠️ Drupal `views` classes, and they are the whole of this module's knowledge of the page. A row is a `<tr>`; the rank,
# the description and the weeks-on-list are three sibling `<td>`s.
ROW = "tr"
RANK = "td.views-field-field-rank"
DESCRIPTION = "td.views-field-field-description"
TITLE = "td.views-field-field-description strong a"

#: ⚠️ **The ISBN is the last field of the description**, and it is a real one — so unlike Amazon's ASIN this needs no
#: conversion, only the separators stripped.
ISBN = re.compile(r"\b(\d{13}|\d{9}[\dXx])\b")
#: ⚠️ `$45.00` — a **value**, and the currency is stripped rather than kept (ADR 0003).
PRICE = re.compile(r"\$(\d+(?:\.\d\d)?)")

#: ⚠️ **Indie Bestsellers is a US list, so its prices are in dollars** (ticket 19). It states `$24.99`, and the row
#: carries `USD` — ⚠️ without it the slide would print `₹24.99`, which is a different number by about eighty times.
CURRENCY = "USD"

#: ⚠️ **The list's address is declared by the chart** (ticket 29) — `charts.Listing.address` — and it is the **undated**
#: form, because only the conductor knows the week. The date is appended in `fetch` below, and that is what makes this
#: vendor's freshness verifiable: the address states the week the list was compiled for.

TIMEOUT = 25


def published_on(week: str) -> str:
    """The date Indie Bestsellers publishes for `week` — **the Wednesday after its Sunday**.

    ⚠️ **Derived from the week, never from a clock** (ADR 0003), and it is the **end** of `freshness.span` rather than
    the start: the list for a week that closed on Sunday lands on the Wednesday following, which is what ticket 10 says
    about when the compiled lists appear and what the recorded page proves — `/national/2026-10-14` for `2026-W41`.

    ⚠️ **So this is the one vendor whose freshness the guard can verify from the response**, because the date is in the
    address. Every other source either states a date the vendor chose or states none at all.
    """
    return freshness.span(week)[1]


def fetch(chart: charts.Chart, *, week: str) -> Iterator[Page]:
    """Every Indie Bestsellers list this chart reads, fetched — **and parsed by nobody**.

    ⚠️ **`week` is required, and it is the second half of the evidence contract.** `nyt` and `amazon` fetch the address
    their declaration states and nothing else, so they can ignore it — but Indie's list is **dated in its own URL**, so
    the declared address is the *undated* form and the date is appended here. ⚠️ The conductor has the week and always
    did; it simply had no reason to pass it until a source needed one.

    ⚠️ **So this is the one vendor whose freshness the guard can verify from the address** rather than from a field the
    vendor chose to publish.

    ⚠️ **A list whose address the site does not serve is refused at *declaration* time, not here** (ticket 29). This
    function used to raise `MissingListError` for a slug it had no address for; now `charts.Listing` will not construct a
    scraped list without one — ⚠️ and that is the stronger place for the rule, because it fails before a run is spent.
    """
    for entry in chart.lists:
        vendor, _, name = entry.slug.partition("/")
        if vendor != VENDOR:
            continue

        date = published_on(week)
        response = requests.get(
            f"{entry.address}/{date}", impersonate="chrome", timeout=TIMEOUT
        )
        response.raise_for_status()
        yield Page(
            listing=entry,
            name=f"{VENDOR}-{name}-{date}.html",
            payload=response.content,
            # ⚠️ ⚠️ **The date travels with the page, because it is nowhere else.** The list is dated in its own
            # address and the page itself carries no date, so without this the rows arrive undated — which the guard
            # refuses, correctly, leaving the English chart permanently absent. ⚠️ It was in the *filename* only, and a
            # filename is not something a parser should read.
            published=date,
        )


def _text(node: object) -> str:
    """A node's text, whitespace collapsed — the same helper `amazon` keeps, for the same reason."""
    if node is None:
        return ""
    return " ".join(node.text().split())  # type: ignore[attr-defined]


def parse(payload: bytes, *, listing: charts.Listing, published: str = "") -> list[corroborate.Row]:
    """One list page, shaped into rows.

    ⚠️ **`published` is passed in because the date is in the URL, not in the body.** The page itself carries no date a
    parser could read — the address does — so the client extracts it and hands it over. ⚠️ That is the same shape as
    ticket 20's labels: a fact the response does not state has to come from the caller, or the row would have to guess.

    ⚠️ **A row with no rank is skipped rather than numbered**, exactly as in `amazon.parse`: a position inferred from
    document order agrees with the badge on a clean page and disagrees silently on a page where a row failed to render.
    """
    tree = LexborHTMLParser(payload.decode("utf-8", errors="replace"))

    rows: list[corroborate.Row] = []
    for row in tree.css(ROW):
        rank_text = _text(row.css_first(RANK))
        title = _text(row.css_first(TITLE))
        if not rank_text.isdigit() or not title:
            continue

        description = _text(row.css_first(DESCRIPTION))
        isbn = ISBN.search(description)
        price = PRICE.search(description)
        amount = float(price.group(1)) if price else None

        rows.append(
            corroborate.Row(
                list=listing.slug,
                rank=int(rank_text),
                # ⚠️ A real ISBN-13, so no ASIN conversion is needed — and `enrich.isbn13` is still run over it so a
                # malformed one is marked **unresolved** rather than trusted.
                isbn=enrich.isbn13(isbn.group(1)) if isbn else "",
                title=title,
                published=published,
                # ⚠️ **The retailer and the count are set only when a row states a price**, so an unpriced row cannot
                # claim a comparison that did not happen — and ticket 04 forbids the word *best* off one listing.
                price=prices.Price(
                    amount=amount,
                    retailer=VENDOR if amount is not None else None,
                    # ⚠️ Indie Bestsellers states no format, so the edition is absent rather than guessed — the slide
                    # omits the slot (ticket 07).
                    edition=None,
                    retailers=(VENDOR,) if amount is not None else (),
                    # ⚠️ **Dollars**, because this is a US list — see `CURRENCY`.
                    currency=CURRENCY,
                ),
                country=listing.country,
                language=listing.language,
            )
        )

    return rows
