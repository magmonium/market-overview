"""The Amazon bestseller pages — **the workhorse, and the only free per-country English source there is.**

⚠️ ⚠️ **One module, several marketplaces** (2026-10-15). This client started as `amazon-in` alone; it now reads whichever
Amazon stores a chart declares — `amazon.com`, `amazon.co.uk`, `amazon.ca` and `amazon.com.au` as well as `amazon.in` —
because those stores are the **only free weekly English bestseller lists that exist**: Books+Publishing (AU) and The
Bookseller (UK) are paywalled. ⚠️ Each store is a separate *vendor* (ticket 17's unit) and each quotes its own currency,
which `MARKETPLACES` pairs by slug.

⚠️ **Ticket 02 names this as scraped, and the repository now says so out loud.** There is no bestsellers API, and
scraping is contrary to Amazon's conditions of use — which is a decision the reader of this product is owed rather than a
detail, and it is why ticket 17's corroboration rule is load-bearing here rather than decorative: *"Amazon's bestseller
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
import time
from typing import Iterator

from curl_cffi import requests
from selectolax.lexbor import LexborHTMLParser

from .. import charts, corroborate, enrich, prices
from . import Page

#: ⚠️ ⚠️ **The Amazon marketplaces this product reads, by vendor slug — and each store quotes its own currency**
#: (2026-10-15). The currency lives here rather than being read off the page because a page states a **symbol** (`$`, `£`,
#: `₹`) and a symbol is ambiguous across the dollar stores — `amazon.com`, `amazon.ca` and `amazon.com.au` all print `$`,
#: and three different currencies under one glyph is precisely the `₹24.99`-for-`$24.99` failure ticket 19 names.
#:
#: ⚠️ **A marketplace the table does not name is not read at all.** `fetch` skips it (the same *"a vendor reads its own
#: lists"* guard `nyt.fetch` keeps, one level down) and `parse` leaves the currency empty rather than guessing one — and
#: an empty currency draws no symbol (ADR 0003), so an unlisted marketplace degrades visibly instead of lying.
MARKETPLACES: dict[str, str] = {
    "amazon-us": "USD",
    "amazon-uk": "GBP",
    "amazon-ca": "CAD",
    "amazon-au": "AUD",
    "amazon-in": "INR",
    #: ⚠️ ⚠️ **The four European storefronts** (ticket 34) — and they are four *vendors*, not one "Europe", for the
    #: same reason `amazon.com` and `amazon.co.uk` are two: each store publishes its own country's ranking.
    #:
    #: ⚠️ **Naming them here is not bookkeeping — it is what makes `CURRENCIES` bite.** Declared without an entry, a
    #: store's `currency` is **empty**, which is the documented *unknown* degrade: the price is kept and printed as a
    #: bare number. ⚠️ Measured on the first fetch, `amazon.de` states **`HUF`** — so an unlisted `amazon-de` would have
    #: shipped `5711.66` with no symbol at all, which is the same wrong number this table exists to catch, one step
    #: further from being visible. ⚠️ The invariant is pinned by a test: every Amazon vendor a chart declares is named
    #: here.
    "amazon-de": "EUR",
    "amazon-fr": "EUR",
    "amazon-it": "EUR",
    "amazon-es": "EUR",
}


def owns(slug: str) -> bool:
    """Whether a list slug belongs to a marketplace this client reads.

    ⚠️ **The rule `fetch` keeps, named once so the tests can ask it too.** A chart declares several vendors, so each
    client has to read **its own** lists and stay silent about the rest — the guard `nyt.fetch` keeps in reverse.
    """
    return corroborate.vendor_of(slug) in MARKETPLACES

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

#: ⚠️ ⚠️ **The size token Amazon puts in every card image URL, and why it has to come off** (2026-10-15).
#:
#: A card's `<img src>` is `…/images/I/71eJk7GtUOL._AC_UL300_SR300,200_.jpg`, which is **300×200** — the *grid's* box,
#: not the cover's shape. ⚠️ Measured on the same asset: with the token stripped it answers **1600×2155**, the largest
#: the card declares (`UL900_SR900,600_`) answers 900×600, and both of those are the 3:2 box. ⚠️ So the cover that
#: reached the collage was **twenty-five times fewer pixels and the wrong aspect ratio** — which is what *"the covers
#: look bad"* turned out to be.
#:
#: ⚠️ **Matched on Amazon's own path shape, `/images/I/<id>._<token>.<ext>`**, rather than on any dot-underscore in a
#: filename: a bookshop's `My._Book.jpg` is a real URL and stripping it would 404. ⚠️ And the asset is otherwise the
#: **same file** — the token is a transformation the CDN applies — so this asks for what the card is a thumbnail *of*.
_IMAGE_TOKEN = re.compile(r"(/images/I/[^/]+?)\._[^/]*?(?=\.(?:jpe?g|png|webp|gif)$)", re.I)

_RANK = re.compile(r"#(\d+)")
#: ⚠️ **Both halves in one attribute** — `4.5 out of 5 stars, 3,661 ratings`. The count is optional because a book with
#: a rating but no count is not a shape Amazon produces; the *whole* attribute is optional, which the fixture proves.
_STARS = re.compile(r"([\d.]+) out of 5 stars(?:, ([\d,]+) ratings?)?")
#: ⚠️ `₹329.00` → `329.00`. The symbol is stripped rather than parsed: ADR 0003 keeps the currency out of the snapshot,
#: and a second currency would be a change to the renderer rather than to this regex.
_MONEY = re.compile(r"([\d,]+(?:\.\d+)?)")

#: ⚠️ ⚠️ **The currency the *page* states — a symbol, or a three-letter code** (2026-10-15).
#:
#: ⚠️ `MARKETPLACES` was written on the premise that a store's currency is a property of the **store**, and for
#: `amazon.in` that holds: every card says `₹`. ⚠️ **It does not hold for `amazon.com` and `amazon.co.uk`, which price
#: the *viewer* rather than the store.** The recorded 2026-W41 pages for both quote **HUF** — `HUF 7,249.11` — and the
#: constant turned that into `$7,249.11` on 13 rows of the English chart and `£…` on 21 more: **34 rows carrying a
#: forint amount under a dollar sign**. ⚠️ That is ticket 19's own named failure — the `₹24.99`-for-`$24.99` — live in a
#: shipped bundle, and it is the reason this table exists.
#:
#: ⚠️ **A price in the wrong currency is a wrong number, and a wrong number is worse than a missing field** (ticket 07).
#: So a stated currency that **contradicts** the declaration drops the *price* and keeps the *row*: the chart loses a
#: caption and not a book, which is the same trade every other unreadable field in this product makes.
#:
#: ⚠️ **And a bare `$` is not evidence.** `amazon.com`, `amazon.ca` and `amazon.com.au` all print one — which is
#: precisely why `MARKETPLACES` exists — so `$` maps to the **empty** code and falls back to the declaration, while every
#: other token has to agree with it.
CURRENCIES: dict[str, str] = {
    "$": "",
    "US$": "USD",
    "C$": "CAD",
    "A$": "AUD",
    "£": "GBP",
    "₹": "INR",
    "€": "EUR",
    "¥": "JPY",
}
#: ⚠️ **The code form**, which Amazon serves instead of a symbol on the localised pages — `HUF 1,616.31`. Matched only
#: as a *prefix followed by a space or a digit*, so a word that happens to start with three capitals is not read as a
#: currency.
_CODE = re.compile(r"^([A-Z]{3})(?=\s|\d)")


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


def _cover_url(raw: str) -> str:
    """A card's image URL **without Amazon's size token** — the original the token was derived from.

    ⚠️ See `_IMAGE_TOKEN`: the token is what makes the fetched image a 300×200 thumbnail of a portrait cover, and the
    same asset without it is the original. ⚠️ A URL that does not carry one is returned **untouched**, which is what
    keeps this harmless for every other vendor's CDN.
    """
    return _IMAGE_TOKEN.sub(r"\1", raw)


def _stated(raw: str) -> str:
    """The currency a card's price *states*, as an ISO code — `""` when it states only an ambiguous `$`.

    ⚠️ **Two shapes, because Amazon serves both**: a symbol (`₹329.00`, `£8.99`) and a code (`HUF 1,616.31`). ⚠️ The
    code is tried first — three capitals followed by a space or a digit cannot be a symbol — and anything unrecognised
    is **no evidence** rather than an error, which is why this returns `""` rather than raising. See `CURRENCIES`.
    """
    text = raw.strip()
    code = _CODE.match(text)
    if code:
        return code.group(1)
    for symbol, iso in CURRENCIES.items():
        if text.startswith(symbol):
            return iso
    return ""


#: ⚠️ **The address is declared by the chart, not by a table here** (ticket 29).
#:
#: ⚠️ This module used to hold a slug→node table, which put the same fact in two places: `charts.py` declared
#: `amazon-in/hindi` and eight more per-language lists **Amazon does not publish**, while this table named the one list it
#: does — and nothing connected the two, so neither could tell the other it was wrong.
#: ⚠️ Now `charts.Listing.address` is the **only** copy, and `Listing.__post_init__` refuses a scraped list without one.

#: ⚠️ Twenty-five seconds: long enough for a 450 KB page, short enough that a wrong address fails rather than hangs.
TIMEOUT = 25

#: ⚠️ ⚠️ **A pause between storefronts, measured rather than imagined** (ticket 34).
#:
#: ⚠️ One chart now reads **eight** stores, and a burst of eight back-to-back requests returned an **empty page for one
#: of them** — `200`, a valid title, and **no `#gridItemRoot` at all** — while the same address answered 30 ranked cards
#: a few seconds later. ⚠️ A store that produces no rows is a **missing source**, and ticket 18 makes a chart with a
#: missing source **absent** — so a rate-limited fetch does not cost one country's rows, it costs the whole chart.
#:
#: ⚠️ **It is a pause, not a retry, and the difference is deliberate.** A retry would hide *"this store answered
#: nothing"* behind a second attempt and make a real outage look like latency. ⚠️ A pause lowers the chance of provoking
#: the throttle and leaves the failure **visible** when it happens anyway — which is the same trade every other
#: degrade in this product makes. ⚠️ Scraping politely is also the least this can do: ticket 02 records that scraping
#: is contrary to Amazon's conditions of use, and this product does it anyway because the lists are the product.
PAUSE_SECONDS = 1.5


def fetch(chart: charts.Chart, *, week: str) -> Iterator[Page]:
    """Every Amazon list this chart reads, fetched — **and parsed by nobody**.

    ⚠️ **Whichever marketplaces the chart declares**, and the address each list carries is what selects the store — so a
    chart that names `amazon-uk` reads `amazon.co.uk` and nothing else. A list whose vendor is not in `MARKETPLACES` is
    skipped here exactly as another vendor's list is skipped by `nyt.fetch`.

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
    #: ⚠️ Whether a storefront has already been asked, so the pause lands **between** requests and never before the
    #: first one — a chart that declares one store must not pay the eight-store price. See `PAUSE_SECONDS`.
    asked = False

    for entry in chart.lists:
        # ⚠️ **Any marketplace this client reads**, not one fixed vendor — a chart may declare several, and each is read
        # from the address it declares (ticket 29). A list belonging to another vendor is skipped in silence, which is
        # `owns`' own rule.
        if not owns(entry.slug):
            continue
        # ⚠️ The vendor half is needed for the filename below, so it is read **after** the check rather than before it —
        # which is also why the first version of this line shipped a `NameError`: the check had moved to `owns` and this
        # binding had not.
        vendor, _, name = entry.slug.partition("/")

        # ⚠️ **Between requests, never before the first** — the pause is for the storefront being asked *next*, and a
        # chart with one store should not pay for the eight another chart reads. See `PAUSE_SECONDS`.
        if asked:
            time.sleep(PAUSE_SECONDS)
        asked = True

        # ⚠️ `curl_cffi` impersonating Chrome, the same trick ticket 02 names for Anandabazar behind Akamai. A plain
        # fetcher is answered with a block page, which parses to **no rows** — and a parser that returns nothing is a
        # vendor the freshness guard calls *missing*, so the failure is visible rather than silent.
        response = requests.get(entry.address, impersonate="chrome", timeout=TIMEOUT)
        response.raise_for_status()
        yield Page(
            listing=entry,
            name=f"{vendor}-{name}.html",
            payload=response.content,
        )


def parse(
    payload: bytes, *, listing: charts.Listing, published: str = ""
) -> list[corroborate.Row]:
    """One bestseller page, shaped into rows.

    ⚠️ **`published` is accepted and deliberately ignored** — Amazon's page carries no list date at all, so there is
    nothing for this client to pass on. ⚠️ It is in the signature because the conductor calls every client the same
    way (`fetch → snapshot → parse`, with the page's own date handed on), and a client that had to be called
    differently would be a special case in the one function that must not have any.

    ⚠️ **The list slug comes from the declaration, and this is the opposite of the NYT rule.** NYT's response carries
    `list_name_encoded`, so its rows are tagged with what the vendor *said* and a mismatch is visible. ⚠️ An Amazon
    bestseller page carries **no list name at all** — the address is the only thing that knows — so the declaration is
    the only honest source, and a wrong address is invisible either way.

    ⚠️ `listing` is required for the same reason it is in `nyt.parse`: a parser cannot tag a row with where it came from
    without being told, and ticket 20's country and language have nowhere else to come from.

    ⚠️ ⚠️ **The vendor is read back off the slug, and that is what selects the currency** (2026-10-15). An Amazon card
    prints a bare `$`, and the store's identity is nowhere in the payload — so the only honest source for *which dollars*
    is the declaration the row came from, exactly as the list slug already argues. ⚠️ A marketplace `MARKETPLACES` does
    not name gets an **empty** currency, which draws no symbol rather than a wrong one.
    """
    vendor = corroborate.vendor_of(listing.slug)
    currency = MARKETPLACES.get(vendor, "")

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
        # ⚠️ **The price is read together with the currency it states** (2026-10-15). The amount alone is not a price:
        # the same digits are different money in different currencies, and `MARKETPLACES` is a claim about the *store*
        # that the page can contradict. See `CURRENCIES`.
        price_text = _text(card.css_first(PRICE))
        amount = _price(price_text)
        stated = _stated(price_text)
        if amount is not None and stated and currency and stated != currency:
            # ⚠️ **Dropped, not relabelled.** A forint amount printed under a dollar sign is a *wrong number*, and
            # ticket 07's rule is that a field with no value **omits** — so the row keeps its rank, title, key and
            # rating and loses only the caption. ⚠️ An unlisted marketplace (`currency == ""`) is untouched: it is
            # already the documented degrade, and the page's code is not this parser's to assert.
            amount = None

        rows.append(
            corroborate.Row(
                list=listing.slug,
                rank=int(rank.group(1)),
                # ⚠️ The ISBN when the ASIN is one, the ASIN when it is not — see the module docstring.
                isbn=enrich.isbn13(asin) or asin,
                title=_text(card.css_first(TITLE)),
                publisher=_text(card.css_first(PUBLISHER)),
                cover_url=_cover_url((image.attributes.get("src") or "")) if image else "",
                # ⚠️ The retailer and the count are set **only when a price was found**, so an unpriced row cannot claim
                # a comparison that did not happen — and ticket 04 forbids the word *best* off one listing.
                price=prices.Price(
                    amount=amount,
                    retailer=vendor if amount is not None else None,
                    edition=_text(card.css_first(FORMAT)) or None,
                    retailers=(vendor,) if amount is not None else (),
                    # ⚠️ **The marketplace's own currency**, from `MARKETPLACES` — never a constant, because this client
                    # now reads stores that quote dollars, pounds and rupees, and the page's symbol cannot tell which.
                    currency=currency,
                ),
                rating=rating,
                ratings_count=count,
                country=listing.country,
                language=listing.language,
            )
        )

    return rows

