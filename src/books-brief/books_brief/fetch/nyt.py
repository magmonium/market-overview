"""The NYT Books API — the English chart's source (ticket 19) and one of comics' (ticket 22).

⚠️ **The list slug carries the vendor** — `nyt/hardcover-fiction` — which is what lets `corroborate.vendor_of` count
sources without a second table that could disagree with the first.

⚠️ **A book with no ISBN-13 is skipped**, because the ISBN is the key the gate corroborates on: a synthesised key would
let two different books collide into one row, which is worse than a missing title.
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Iterator

from .. import charts, corroborate
from . import Page

#: The vendor slug, as `charts` spells it.
VENDOR = "nyt"

#: The API's base. ⚠️ `v3` is the current version, and the key is read from the environment — a key committed to the
#: repository is a key that has been published.
BASE = "https://api.nytimes.com/svc/books/v3/lists/current"
KEY_ENV = "NYT_API_KEY"

#: ⚠️ The lists this client reads, taken from `charts.Chart.lists`. Named here so a parser cannot quietly invent a list
#: the charts do not declare — a row from an undeclared list would be discarded by the gate anyway (ticket 17).
LISTS: tuple[str, ...] = (
    "hardcover-fiction",
    "hardcover-nonfiction",
    "graphic-books-and-manga",
)


class MissingKeyError(RuntimeError):
    """The API key is absent, so the lists cannot be read — a **refusal**, not a crash."""


def parse(payload: bytes, *, listing: charts.Listing) -> list[corroborate.Row]:
    """One list response, shaped into rows.

    ⚠️ The `list_name_encoded` comes from the **response**, not from the caller, so the row is tagged with what the
    vendor actually said it was — a mismatch between the requested list and the answered one is visible rather than
    silently assumed away.

    ⚠️ **The list's `published_date` rides onto every row**, because it is the *only* evidence ticket 10's freshness
    guard has: a books chart has no session clock, so a stale response looks exactly like a fresh one. ⚠️ It is read
    without validation — a date that will not parse is `freshness`'s refusal to make, not this parser's crash, and one
    vendor's malformed field must not cost the other three charts.

    ⚠️ **`listing` is required, and that is ticket 20's shape.** NYT's payload carries a list name and a date and no
    geography at all, so the country and the language can only come from the *declaration* — and making it an argument
    means a client cannot parse without saying which list it was reading. ⚠️ The two can disagree, and then the row says
    so: the slug is the response's, the geography is the request's, and both are visible.
    """
    body = json.loads(payload)
    results = body["results"]
    list_slug = f"{VENDOR}/{results['list_name_encoded']}"
    published = results.get("published_date") or ""

    rows: list[corroborate.Row] = []
    for book in results["books"]:
        isbn = book.get("primary_isbn13")
        if not isbn:
            continue
        rows.append(
            corroborate.Row(
                list=list_slug,
                rank=int(book["rank"]),
                isbn=isbn,
                title=book["title"],
                # ⚠️ NYT carries the author and **nothing else does**, which is what makes the English chart's rows the
                # only ones whose author is not a second choice (ticket 17 puts the list ahead of Google Books).
                author=book.get("author") or "",
                published=published,
                # ⚠️ Ticket 20 — from the declaration, because the payload has nothing to offer and a defaulted country
                # would be a label nobody could check.
                country=listing.country,
                language=listing.language,
            )
        )
    return rows


def fetch(chart: charts.Chart, *, week: str) -> Iterator[Page]:
    """Every NYT list this chart reads, fetched — **and parsed by nobody**.

    ⚠️ **Only the lists the chart declares are read**, taken from `charts.Chart.lists` — so a chart cannot be quietly
    fed a list it does not own, and adding a list is a change to the chart rather than to this function.

    ⚠️ **No key is a refusal, not a crash.** `MissingKeyError` is caught by the conductor, which treats the chart as
    absent (ticket 18) — the run refuses only if *nothing* could be built.

    ⚠️ **It yields `Page`s rather than rows, and that is the evidence rule** — see `fetch/__init__`. The conductor writes
    each page to `store/<week>/raw/` **before** `parse` sees it, because a response written after a successful parse can
    never show what the parser was *given* on the day the parser was what broke.
    """
    key = os.environ.get(KEY_ENV)
    if not key:
        raise MissingKeyError(f"{KEY_ENV} is not set, so the NYT lists cannot be read")

    for entry in chart.lists:
        # ⚠️ `entry.slug`, not `entry` — a list is a `charts.Listing`, so it carries its own country and language
        # (ticket 20) as well as its address.
        vendor, _, name = entry.slug.partition("/")
        if vendor != VENDOR or name not in LISTS:
            continue
        with urllib.request.urlopen(f"{BASE}/{name}.json?api-key={key}", timeout=30) as response:
            yield Page(
                listing=entry,
                # ⚠️ The filename is the client's, because the client is what knows this is JSON — see `Page.name`.
                name=f"{VENDOR}-{name}.json",
                payload=response.read(),
            )
