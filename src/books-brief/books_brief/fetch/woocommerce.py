"""The Bengali booksellers' own rankings — **the second vendor the Bengali chart was missing** (ticket 30).

⚠️ **What was searched, and what was found.** Ticket 29 left the Bengali chart with one vendor and two open items —
*"a second weekly Bengali ranking"* and *"a date for Rokomari"* — and both were searches rather than corrections. Seven
candidate addresses were fetched (2026-10-15) and **four of them are not sources at all**:

| Fetched | What it actually is | Verdict |
|---|---|---|
| `amazon.in/…/s?k=bengali+books+bestsellers` | a **search results page** — *1–16 of over 1,000 results*, no rank badge anywhere | ❌ confirms ticket 29's finding |
| `daraz.com.bd/tag/bengali-novels` | a tag page that ships **no products** in its HTML | ❌ empty |
| `goodreads.com/shelf/show/bengali` | an **all-time shelving count** (*"shelved 75 times"*), not sales, and not weekly | ❌ not a sales list |
| `flipkart.com/books/bengali~language/pr` | a **category browse** of **20,109** products, popularity-sorted | ⚠️ a real ordering, but undated and unwieldy — recorded, not declared |

⚠️ **What is a source.** Two Bengali bookshops — **BoiChitro** (`boichitro.in`) and **Boighar** (`boighar.in`) — run
WooCommerce, and WooCommerce publishes a **Store API**: a JSON endpoint, no scraping and no key, whose `orderby` accepts
`popularity`. ⚠️ `boichitro.in` answers **100 products** at
`/wp-json/wc/store/v1/products?orderby=popularity&per_page=100`, and ⚠️ **the parameter is honoured rather than
decorative**: `popularity`, `date` and `rating` return three different orders, verified by fetching all three.

⚠️ ⚠️ **The position *is* the rank here, and that is the opposite of `amazon.parse`'s rule.** Amazon renders a `#1` badge,
and a parser that numbered the cards would agree on a clean page and disagree silently on a page where one card failed
to render. ⚠️ A JSON array has no failed cards — the array *is* the ranking, and its order is the store's own statement —
so numbering it is honest rather than inferred. ⚠️ **And the position survives a skipped record**: a product we cannot
key is left out of the rows but its place in the store's ranking is not renumbered away, because that place is a fact
about the *list* rather than a count of what we managed to parse.

⚠️ **The name is two titles and two authors in one string.** BoiChitro's `name` reads
`Deshantare Baj || Abhik Dutta || দেশান্তরে বাজ || অভীক দত্ত` — English title, English author, Bengali title, Bengali
author, `||`-separated — and **the shape is not consistent**: some records carry two segments, some four. ⚠️ So the title
is taken as the **first segment** and the author comes from the store's own **`pa_authorname` attribute**, which is a
field rather than a guess. ⚠️ A record with no author attribute keeps an **empty** author, which is the ordinary case
(`corroborate.Row.author`) and one Google Books answers.

⚠️ ⚠️ **The ISBN is a real field, and it is sometimes a spreadsheet's casualty.** `pa_isbn` is present on **18 of the
first 100** BoiChitro products and is a genuine ISBN-13 — which is what makes this vendor *corroborate*: an Amazon.in row
and a BoiChitro row meet on an ISBN rather than on a title. ⚠️ But one recorded value is `9.78939E 12`, a number that has
been through Excel's scientific notation and **lost digits it cannot get back**. ⚠️ It is passed through
`enrich.isbn13` like every other identifier, fails, and the row falls back to the vendor's own key — the same
degradation `amazon.parse` applies to a Kindle ASIN. **Nothing is reconstructed from it**, because a repaired ISBN is a
guess wearing a check digit.

⚠️ **The currency is read off the payload**, unlike `amazon.MARKETPLACES`: the Store API states `currency_code` per
product, so there is nothing for a table here to get wrong.

⚠️ ⚠️ **And a third store joined in the same way, which is the point of one module** (ticket 32). **Bangabani**
(`bangabani.in`) answers **100 products** at
`/wp-json/wc/store/v1/products?category=143&orderby=popularity&per_page=100`, and it is the strongest Indian Bengali
source found in three searches — for three reasons that are all facts about the payload rather than hopes:

- ⚠️ **Its ISBNs are in `sku`, not in an attribute.** **54 of 100** carry a real ISBN-13 there, and `_key` already tries
  the SKU *second* — so half this store's rows arrive with an identity another vendor can corroborate on, which is the
  thing BoiChitro can only do on 18 rows.
- ⚠️ **Its titles are Bengali script** (`পাতাঝরার মরশুমে`) where every other Bengali vendor's are romanised, and **all
  100 of them are** — measured, because ticket 20's rule turns on it: this list declares `language="bn"` while BoiChitro's
  declares none, and a `bn` that was wrong on some rows would be *"a constant label that renders"*.
- ⚠️ **Its ranking is the `category` *and* the `orderby`.** The category's **default** order is not popularity — verified
  by comparing the two id orders — so the address is the list, exactly as ticket 29 requires.

⚠️ **What it does not have is an author**: no `pa_*` attributes at all, and its blurbs carry no byline, so its rows key as
`title|` and cannot merge with an authored row (ticket 32). ⚠️ That is the conservative direction and it is recorded here
rather than discovered later.


⚠️ **The language is left unknown, and the reason is `all-language`'s.** These are *stores'* bestseller lists, and a
store's list carries Bengali, English and Hindi rows side by side — BoiChitro's own top ten holds
*Strange Weather in Tokyo* beside *দেশান্তরে বাজ*. ⚠️ So the lists declare **no** language (ticket 20's *empty means
unknown*, which draws no label) rather than a `bn` that would be confidently wrong on the English rows.
"""
from __future__ import annotations

import json
from typing import Any, Iterator

from curl_cffi import requests

from .. import charts, corroborate, enrich, prices
from . import Page

#: ⚠️ ⚠️ **The WooCommerce stores this client reads, and one module serves them all** — the arrangement `amazon.py`
#: keeps for five marketplaces, and for the same reason: the *endpoint* is the store's, and what differs between two
#: WooCommerce shops is the storefront rather than the shape of the answer.
#:
#: ⚠️ **Only `boichitro` and `bangabani` are declared** (tickets 30, 32). `boighar` is the same client and one line in
#: `charts.py`, and it is **not** declared — because its popularity ordering is unverifiable (its own top five is 2021
#: magazines with one review apiece, against BoiChitro's fifty-odd-review books) and it states **no ISBN at all**, so it
#: could neither corroborate nor be corroborated. ⚠️ Declaring a source that cannot corroborate is not a bigger chart, it
#: is a noisier one. ⚠️ And `bangabani` is the counter-example that keeps that rule honest: it states **no author** but
#: **54 real ISBNs**, so the bar it clears is corroboration rather than completeness.
STORES: tuple[str, ...] = ("boichitro", "boighar", "bangabani")

#: ⚠️ **The store's own ordering, and the one query parameter that changes the answer.** `popularity` is WooCommerce's
#: cumulative sales ranking — see the module docstring for why it is not the `date` order.
ORDERBY = "popularity"

#: ⚠️ **A hundred, because the chart is a Top 100** — a shallower list is paid for by `rank.weight`, so asking for fewer
#: rows would silently cap this vendor's reach rather than fail.
DEPTH = 100

#: ⚠️ **Where a store puts the author, in the order they are tried.** BoiChitro publishes `pa_authorname`; Boighar
#: publishes `pa_authorname` (often literally `N/A`) *or* `pa_author-2`. ⚠️ A declared table rather than a
#: starts-with-`pa_author` scan, because ticket 26's rule applies to attributes too: a runtime guess is not replayable.
AUTHORS: tuple[str, ...] = ("pa_authorname", "pa_author-2", "pa_author")

#: ⚠️ The ISBN attribute, and there is one spelling of it — see the module docstring for the value that arrives mangled.
ISBN_ATTRIBUTE = "pa_isbn"

#: ⚠️ What a store writes when it has no author: **absence wearing a word**. `"N/A"` printed on a slide is a worse
#: answer than an empty slot the renderer omits (ticket 07).
BLANK = frozenset({"", "n/a", "na", "-"})

TIMEOUT = 25


def owns(slug: str) -> bool:
    """Whether a list slug belongs to a store this client reads — `boichitro/bestsellers` is ours, `nyt/…` is not."""
    return corroborate.vendor_of(slug) in STORES


def _attribute(product: dict[str, Any], taxonomies: tuple[str, ...]) -> str:
    """The first term of the first attribute in `taxonomies` that states something — `""` when none does.

    ⚠️ **The order is the caller's and the skip is explicit**, because the two stores disagree about which attribute
    holds an author and one of them writes `N/A` where it has none. ⚠️ A blank is skipped rather than returned, so a
    record whose first attribute is `N/A` still reaches its second.
    """
    stated = {
        attribute.get("taxonomy"): [
            str(term.get("name") or "") for term in attribute.get("terms") or []
        ]
        for attribute in product.get("attributes") or []
        if isinstance(attribute, dict)
    }

    for taxonomy in taxonomies:
        for term in stated.get(taxonomy) or []:
            value = " ".join(term.split())
            if value.lower() not in BLANK:
                return value
    return ""

def _title(product: dict[str, Any]) -> str:
    """The English title — **the first `||` segment of `name`**, never the whole string.

    ⚠️ A store concatenates its own fields into `name`, so printing it whole would put
    `Deshantare Baj || Abhik Dutta || দেশান্তরে বাজ || অভীক দত্ত` on the slide as a *title*. ⚠️ The first segment is the
    title by the store's own convention; the author is a **field** (`AUTHORS`) rather than the second segment, because
    the segment count is not consistent across records.
    """
    return " ".join(str(product.get("name") or "").split("||")[0].split())


def _key(product: dict[str, Any], *, vendor: str) -> str:
    """The row's identity — a real ISBN where the store states one, else the store's own stable key.

    ⚠️ **`enrich.isbn13` decides, and it is run on both candidates.** A store's `pa_isbn` is usually a real ISBN-13 and
    sometimes a spreadsheet accident; its `sku` is sometimes a real ISBN and usually a publisher-prefixed stock code
    (`Deep Prakashan5826`). ⚠️ So the ISBN is tried first, the SKU second, and **the store's own id last** — prefixed, as
    `rokomari`'s is, because a bare `5826` is a number that could collide with any other store's numbering.
    ⚠️ `enrich.isbn13` returning `""` is what marks the identity **unresolved** downstream (ticket 05), which is the
    honest outcome for a row we can rank but cannot yet match against another vendor.
    """
    stated = _attribute(product, (ISBN_ATTRIBUTE,))
    for candidate in (stated, str(product.get("sku") or "")):
        resolved = enrich.isbn13(candidate)
        if resolved:
            return resolved

    identifier = str(product.get("sku") or "").strip() or str(product.get("id") or "").strip()
    return f"{vendor}:{identifier}" if identifier else ""


def _amount(product: dict[str, Any]) -> tuple[float | None, str]:
    """The store's price and **the currency it quoted it in** — `(None, "")` when the record states no price.

    ⚠️ Both come off the payload: the Store API carries `prices.price` and `prices.currency_code` per product, so unlike
    an Amazon card — which prints a bare `$` — there is nothing here for a table to get wrong. ⚠️ A price that will not
    parse is **absence rather than zero**, the rule `prices.Price` keeps everywhere else.
    """
    block = product.get("prices") or {}
    raw = block.get("price")
    try:
        amount: float | None = float(raw) if raw not in (None, "") else None
    except (TypeError, ValueError):
        amount = None

    return amount, (str(block.get("currency_code") or "") if amount is not None else "")


def _cover(product: dict[str, Any]) -> str:
    """The store's own cover image, or `""` — ⚠️ the *list's* image, which ticket 07 puts ahead of Google Books."""
    images = product.get("images") or []
    first = images[0] if images and isinstance(images[0], dict) else {}
    return str(first.get("src") or "")


def parse(payload: bytes, *, listing: charts.Listing, published: str = "") -> list[corroborate.Row]:
    """One store's ranking, shaped into rows.

    ⚠️ **A malformed body returns nothing rather than raising** — the rule `amazon.parse` keeps, for the same reason: a
    block page, a failed render and a genuine empty list look identical from here, and a parser that raised would take
    the other charts with it. `freshness.guard` already treats a vendor that produced nothing as **missing**.

    ⚠️ **`published` is accepted and stays empty**, because the response carries **no date anywhere** — see the module
    docstring. ⚠️ That is not an omission: it is the fact that makes these vendors `LIVE` in `charts`, and an empty date
    on a vendor that is *not* live is **stale** rather than a guess.

    ⚠️ **The list slug and both labels come from the declaration.** A store's endpoint names no list, and ticket 20's
    country and language have nowhere else to come from — the arrangement `amazon.parse` keeps.
    """
    vendor = corroborate.vendor_of(listing.slug)

    try:
        products = json.loads(payload.decode("utf-8", errors="replace"))
    except ValueError:
        return []
    if not isinstance(products, list):
        return []

    rows: list[corroborate.Row] = []
    # ⚠️ **The position is counted over the *response*, before anything is skipped** — so a record we cannot key leaves
    # a gap in the ranks rather than pulling every later title up one place. See the module docstring.
    for position, product in enumerate(products, start=1):
        if not isinstance(product, dict):
            continue

        title = _title(product)
        key = _key(product, vendor=vendor)
        # ⚠️ **Both are required and neither is inferred**: a title is what the slide prints, and a key is what
        # corroboration joins on — a row keyed on `title + author` is the collision ticket 05 refuses.
        if not title or not key:
            continue

        amount, currency = _amount(product)
        reviews = product.get("review_count") or 0
        try:
            rating = float(product.get("average_rating")) if reviews else None
        except (TypeError, ValueError):
            rating = None

        rows.append(
            corroborate.Row(
                list=listing.slug,
                rank=position,
                isbn=key,
                title=title,
                author=_attribute(product, AUTHORS),
                publisher=_attribute(product, ("pa_publisher",)),
                cover_url=_cover(product),
                published=published,
                # ⚠️ The retailer and the count are set **only when a price was found**, so an unpriced row cannot claim
                # a comparison that did not happen — ticket 04 forbids the word *best* off one listing.
                price=prices.Price(
                    amount=amount,
                    retailer=vendor if amount is not None else None,
                    edition=_attribute(product, ("pa_binding",)) or None,
                    retailers=(vendor,) if amount is not None else (),
                    currency=currency,
                ),
                # ⚠️ **An unrated book is `None`, not a zero** — `rank.review_term`'s own rule: a title nobody has rated
                # has not been judged average, and a `0.0` here would be a judgement rather than an absence.
                rating=rating,
                ratings_count=reviews or None,
                country=listing.country,
                language=listing.language,
            )
        )

    return rows


def fetch(chart: charts.Chart, *, week: str) -> Iterator[Page]:
    """Every list this chart declares at a WooCommerce store, fetched — **and parsed by nobody**.

    ⚠️ **`week` is accepted and deliberately unused**, exactly as `rokomari.fetch` does and for the same reason: a
    store's ranking carries no date, so there is nothing to build a dated address from and nothing to hand the parser.
    ⚠️ The freshness consequence is real, and it is stated where it belongs — `charts.LIVE`.

    ⚠️ **The address is the chart's, and the declaration is the only copy** (ticket 29). A store's endpoint *is* its
    list — `orderby=popularity&per_page=100` is the whole of what separates this ranking from the same shop's
    newest-arrivals page — so a slug that named the address would be a second place to keep it right.
    """
    for entry in chart.lists:
        if not owns(entry.slug):
            continue

        # ⚠️ ⚠️ **The address must carry the ordering, and this is the one check that keeps a ranking a ranking.**
        # A store's endpoint *is* its list only because of `orderby=popularity` — drop that parameter and the same URL
        # becomes the shop's newest-arrivals page, which would rank a chart by recency and look entirely correct while
        # doing it. ⚠️ Ticket 29's rule is *"the address is the list's identity"*; this is that rule **refusing to
        # fetch** an address that has stopped identifying it.
        # ⚠️ A fetch-time refusal rather than a constructor one, because `ORDERBY` is this client's fact and
        # `charts.Listing` is not allowed to know it.
        if f"orderby={ORDERBY}" not in entry.address:
            raise ValueError(
                f"{entry.slug} does not declare the store's ranking — {entry.address!r} is missing "
                f"`orderby={ORDERBY}`, so it is not a bestseller list"
            )

        response = requests.get(entry.address, impersonate="chrome", timeout=TIMEOUT)
        response.raise_for_status()
        yield Page(
            listing=entry,
            name=f"{corroborate.vendor_of(entry.slug)}-bestsellers.json",
            payload=response.content,
        )


