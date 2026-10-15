"""Rokomari — **the Bangladeshi bridge** (ticket 21), and the fourth parsing shape in the set.

⚠️ **The books are not in the DOM and not in JSON.** The page is a Next.js App Router render, so its content ships as a
series of `self.__next_f.push([1,"…"])` calls whose arguments are **JavaScript string literals** — the real text is
escaped (`\\"` for `"`) and the chunks have to be unescaped and joined before anything is readable. ⚠️ A DOM parser sees
**nothing**: the ranked-list probe on this page finds **0** nodes, which is what sent the first investigation down the
wrong path entirely.

⚠️ **What a book is, once the flight is unescaped**, is a **self-contained JSON object**:

    {"product":{"id":890,"categoryId":0,"price":180,"title":"ময়ূরাক্ষী","subTitle":"হুমায়ূন আহমেদ"},
     "productType":"book"}

⚠️ **`productType: "book"` is the marker**, and `subTitle` is the **author** — not a subtitle. ⚠️ The id is Rokomari's
own, **not an ISBN**, so a row's key is prefixed (`rokomari:890`) and `enrich.isbn13` returns `""` for it, which is what
marks the identity **unresolved** (ticket 05).

⚠️ ⚠️ **And the list carries no date.** The flight has no publication date anywhere, so a Rokomari row is **undated** —
and `freshness.is_fresh("")` is **False**, because an undated list is one the guard cannot verify. ⚠️ **That is no longer
a refusal, and the correction is ticket 30's** (2026-10-15): a retailer's own bestseller category is **regenerated per
order**, so there is no dated artefact for a date to be missing *from* — which is exactly the case `charts.LIVE` exists
for, and `ROKOMARI` is in it. ⚠️ The half that still protects the product is untouched: a Rokomari that answers *nothing*
is still a **missing** vendor and still makes the chart absent.

⚠️ ⚠️ **CORRECTED AGAIN 2026-10-15 — the record shape changed, and the parser now walks braces.** The regex that used to
find records required `,"productType"` immediately after the product object; the store inserted an **`adClickUrl` field
between them**, so the pattern matched **nothing** and the vendor was reported *missing* rather than *broken*. See
`RECORD` and `records` for the walk that replaced it, and `tests/fixtures/rokomari-flight-2026-10-15.html` for the second
recording.
"""
from __future__ import annotations

import json
import re
from typing import Iterator

from curl_cffi import requests

from .. import charts, corroborate, enrich, prices
from . import Page

#: The vendor slug, as `charts` spells it.
VENDOR = "rokomari"

#: ⚠️ **Bangladeshi Taka**, and the reason `Price.currency` exists. Rendering ৳180 as ₹180 is wrong by about a factor of
#: one and a half, and it would look entirely correct.
CURRENCY = "BDT"

#: ⚠️ **The address is declared by the chart** (ticket 29) — `charts.Listing.address` — and this constant is gone.
#:
#: ⚠️ It used to live here *and* be ignored: this client fetched `BEST_SELLERS` for **any** `rokomari/*` slug, so
#: `rokomari/leaderboard` was a name pointing at nothing while the client quietly read the right page. ⚠️ And ticket 29
#: named `/list/38927` as the list — **fetching both settles it**: the Best Seller category carries **60** `product`
#: records and `/list/38927` carries **none**. ⚠️ The ticket's `39 /book/<id>` links were anchors rather than records,
#: which is the same *reading an absence as proof* the ticket itself warns about.

#: ⚠️ The flight chunks, **raw** — quotes and escapes included, because unescaping them is half the parser's job.
CHUNK = re.compile(r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)')

#: ⚠️ ⚠️ **A record is found by balancing braces, not by a regex** (corrected 2026-10-15).
#:
#: The pattern that used to live here was `\{"product":\{([^{}]*)\},"productType":"book"\}`, and its own note said the
#: flatness was what made it *"honest here rather than fragile"* — because *"a product record has no nested braces"*.
#: ⚠️ **Both halves of that assumption broke, and the second one broke within a day of being written.** Rokomari inserted
#: a field **between** the product object and the marker:
#:
#:     2026-10-14   {"product":{…},"productType":"book"}
#:     2026-10-15   {"product":{…},"adClickUrl":"$undefined","productType":"book"}
#:
#: ⚠️ **The pattern then matched nothing at all** — and *nothing* is exactly how it failed: the recorded page holds 60
#: records, the fetched page held 60, `parse` returned **0 rows**, and `freshness.guard` reported the vendor as
#: **missing** rather than the parser as broken. ⚠️ That is the shape of failure this product refuses everywhere else, so
#: the scan is structural now: find the record's opening, walk to its matching brace, and let `json.loads` be the judge.
#: ⚠️ A field added *inside* the product object is handled by the same walk, because the walk counts braces rather than
#: describing a shape.
RECORD = '{"product":{'

#: ⚠️ The marker a record must carry, checked **after** the braces balance — so a record that parses but is not a book is
#: skipped rather than ranked.
BOOK = "book"

TIMEOUT = 25


def records(flight_text: str) -> Iterator[str]:
    """Every brace-balanced `{"product":…}` record in a decoded flight, **as text**.

    ⚠️ **String-aware, and that is not a refinement.** A brace inside a quoted title would unbalance a naive counter and
    silently swallow the records after it — ⚠️ the same class of silent nothing the regex produced. So a `"` opens a span
    that is skipped (with `\\` escapes honoured), and only structural braces are counted.

    ⚠️ **A record whose braces never close ends the scan rather than raising** — a truncated response is a vendor that
    produced nothing, which the guard already treats as **missing**.
    """
    cursor = 0
    while True:
        start = flight_text.find(RECORD, cursor)
        if start < 0:
            return

        depth = 0
        in_string = False
        escaped = False
        for position in range(start, len(flight_text)):
            character = flight_text[position]
            if in_string:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    in_string = False
                continue
            if character == '"':
                in_string = True
            elif character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    yield flight_text[start : position + 1]
                    cursor = position + 1
                    break
        else:
            return

#: ⚠️ ⚠️ **The card's own cover: the `data-src` on the vendor's image host.** Rokomari lazy-loads its cards — `src` is
#: `/nstatic/images/placeholder-image.gif` and the real file is the `data-src` beside it — ⚠️ so a parser that read `src`
#: would put **the same grey placeholder on every row**, which looks exactly like a chart whose covers are all missing.
#:
#: ⚠️ ⚠️ **Matched by the *host* rather than by the component's class, and the recording is what says so.** The obvious
#: selector is `productContainer_coverImage__…`, and ⚠️ **it appears on only 15 of the 60 cards** — the other
#: forty-five render the same picture through a different component, so a class-based pattern finds a cover for one row in
#: sixty. ⚠️ A CSS-module hash is a **build artefact** and which component draws the picture is the store's business; the
#: image *host* is the source's, and it is the same on every card.
COVER = re.compile(r'"data-src":"(https://rokbucket\.rokomari\.io/[^"]+)"')


def _cover(card: str) -> str:
    """The card's cover image — **the last one in the card, and `""` when the card has none**.

    ⚠️ ⚠️ **`card` is the text between the previous record and this one, and that bound is the whole rule.** A card's
    picture sits a little *before* the record it belongs to, inside the same card, so the last image in the window is
    this row's. ⚠️ A card that carries none leaves the window without one and the row keeps **no** cover — which is the
    right degradation, because a wrong cover on a slide is worse than a missing one: nobody looking at it can tell.
    """
    found = COVER.findall(card)
    return found[-1] if found else ""




def flight(payload: bytes) -> str:
    """Every `__next_f` chunk, **unescaped and joined** — the page's content as the browser would see it.

    ⚠️ `json.loads` on each literal, because that is exactly what a JavaScript string literal is. ⚠️ A chunk that will
    not parse is **skipped rather than fatal**: one malformed chunk is not a reason to lose a whole list, and the records
    that survive are still true.
    """
    text = payload.decode("utf-8", errors="replace")
    parts: list[str] = []
    for chunk in CHUNK.findall(text):
        try:
            parts.append(json.loads(chunk))
        except ValueError:
            continue
    return "".join(parts)


def parse(payload: bytes, *, listing: charts.Listing, published: str = "") -> list[corroborate.Row]:
    """One list page, shaped into rows — **in the order the payload states them**.

    ⚠️ **The rank is the document order, and here that is not an inference.** `amazon.parse` refuses to number cards by
    position because a card that failed to render shifts every rank after it — but Amazon's cards *state* their rank in a
    badge, so the position is a second, worse source. ⚠️ Rokomari's records state **no rank at all**: the payload *is* the
    ranking, the list is ordered, and the position is the only thing that carries it. ⚠️ The two rules look contradictory
    and are not: **prefer a stated rank, and use the order only where the source has none.**

    ⚠️ ⚠️ **The position is counted over the *records*, and the marker is checked before it counts** (2026-10-15). A
    record that parses but does not carry `productType: "book"` is a card the store renders for something else, so it is
    skipped — and ⚠️ the skipped record still holds its place, because the store's ordering is a fact about the list
    rather than a count of what we managed to read (the rule `woocommerce.parse` keeps).
    """
    rows: list[corroborate.Row] = []
    text = flight(payload)
    #: ⚠️ Where the previous record ended. Everything after it and before the next record **is that record's card**, and
    #: that window is how a cover is attributed to a row — see `_cover`.
    previous = 0

    for position, record in enumerate(records(text), start=1):
        at = text.find(record, previous)
        card = text[previous:at] if at >= 0 else ""
        if at >= 0:
            previous = at + len(record)

        try:
            entry = json.loads(record)
        except ValueError:
            continue

        product = entry.get("product") if isinstance(entry, dict) else None
        # ⚠️ **Both halves are required**: a record that is not a book is not this list's evidence, and a record whose
        # `product` is not an object is a shape we do not understand — neither is a row.
        if not isinstance(product, dict) or entry.get("productType") != BOOK:
            continue

        title = (product.get("title") or "").strip()
        if not title:
            continue

        identifier = str(product.get("id") or "").strip()
        amount = product.get("price")

        rows.append(
            corroborate.Row(
                list=listing.slug,
                rank=position,
                # ⚠️ **Prefixed, because a bare `890` is three digits that could be a truncated ISBN.** The vendor's own
                # id is a real, stable identifier — not the synthesised `title + author` key ticket 05 refuses — and
                # `enrich.isbn13` returning `""` for it is what marks the row **unresolved**.
                isbn=f"{VENDOR}:{identifier}" if identifier else "",
                title=title,
                # ⚠️ **`subTitle` is the author on this source**, which the recording is what established.
                author=(product.get("subTitle") or "").strip(),
                # ⚠️ **The card's own image, which this parser used to leave behind** (2026-10-15) — so every Rokomari row
                # fell to ticket 07's branded tile while the picture sat in the same card. See `_cover`.
                cover_url=_cover(card),
                published=published,
                price=prices.Price(
                    amount=float(amount) if amount is not None else None,
                    retailer=VENDOR if amount is not None else None,
                    edition=None,
                    retailers=(VENDOR,) if amount is not None else (),
                    currency=CURRENCY,
                ),
                country=listing.country,
                language=listing.language,
            )
        )

    return rows


def fetch(chart: charts.Chart, *, week: str) -> Iterator[Page]:
    """Every Rokomari list this chart reads, fetched — **and parsed by nobody**.

    ⚠️ **`week` is accepted and deliberately unused**, and that is a finding rather than an oversight: the payload
    carries **no date**, so there is nothing to build a dated address from and nothing to hand the parser as
    `published`. ⚠️ A row from this source is therefore **undated**, `freshness.is_fresh("")` is **False**, and the
    vendor is refused as **stale**.

    ⚠️ **That is the guard working.** Ticket 10 requires a source to be *verified* to have published for the week being
    built, and this one cannot be — so the Bengali chart goes **absent** rather than shipping a list of unknown vintage.
    ⚠️ Finding a date is what would make this source usable, and it is not a parser change.

    ⚠️ **The address is the chart's, and the declaration is the only copy** (ticket 29). This client used to hold its own
    constant and **ignore the declared slug** — which is exactly how a slug came to name a page that is not the list while
    the client quietly fetched the right one. ⚠️ Now `Listing` refuses a scraped list without an address, so there is
    nothing here left to guess at.
    """
    for entry in chart.lists:
        vendor, _, _ = entry.slug.partition("/")
        if vendor != VENDOR:
            continue

        response = requests.get(entry.address, impersonate="chrome", timeout=TIMEOUT)
        response.raise_for_status()
        yield Page(
            listing=entry,
            name=f"{VENDOR}-best-sellers.html",
            payload=response.content,
        )

