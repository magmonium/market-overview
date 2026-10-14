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
and `freshness.is_fresh("")` is **False**, because an undated list is one the guard cannot verify. ⚠️ That means this
vendor is refused as **stale** until a date is found, which is the correct outcome rather than a bug: ticket 10's rule is
that a source must be *verified* to have published for the week, and this one cannot be.
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

#: ⚠️ One book. The inner object is matched without nesting because a product record has no nested braces — which is what
#: makes a regex honest here rather than fragile.
PRODUCT = re.compile(r'\{"product":\{([^{}]*)\},"productType":"book"\}')

TIMEOUT = 25


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
    """
    rows: list[corroborate.Row] = []

    for position, match in enumerate(PRODUCT.finditer(flight(payload)), start=1):
        try:
            product = json.loads(f"{{{match.group(1)}}}")
        except ValueError:
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

