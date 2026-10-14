"""The Google Books API — **enrichment, never a chart** (tickets 02, 17).

⚠️ **Google Books cannot be a chart source and this module never pretends otherwise.** Ticket 02 is blunt: no weekly
cadence, no sales, no rank — *"enrichment, not a chart."* What it has is the five fields ticket 17's priority table gives
it: **publisher, publication date, cover, ISBN and genre**. A sixth would be this client claiming a field it has no
business deciding.

⚠️ **A lookup is by ISBN, and a mismatch is refused.** That is ticket 05's identity rule enforced at the boundary: *"a
match confirmed by two sources, never a single fuzzy title search."* Asking for one ISBN and accepting a volume that
answers with a different one is exactly that fuzzy match — and the cascade it starts (wrong cover, wrong pub date, a
corrupted week-over-week diff) is invisible downstream, because the response looks perfectly fine.

⚠️ **Only `parse_volume` is tested**; `fetch` is the boundary — the split `fetch/__init__.py` states, and the reason the
suite is hermetic.
"""
from __future__ import annotations

import dataclasses
import json
import os
import urllib.parse
import urllib.request

from .. import covers, enrich

#: ⚠️ A key is **optional** here — the free tier allows keyless lookups at a lower quota, so a missing key is a slower
#: run rather than a refused one. That is not true of NYT, whose client raises `MissingKeyError`.
BASE = "https://www.googleapis.com/books/v1/volumes"

#: ⚠️ A key committed to the repository is a key that has been published.
KEY_ENV = "GOOGLE_BOOKS_API_KEY"


@dataclasses.dataclass(frozen=True)
class Volume:
    """One volume as Google Books describes it — **and only the fields this product takes from it.**

    ⚠️ **A separate shape from `enrich.Details`, deliberately.** A `Details` is a *row's* set of fields, assembled from
    every source with an opinion; this is **one source's** answer. Collapsing them would make it impossible to tell which
    vendor supplied a publisher — the auditability ticket 17 asks for.

    ⚠️ `cover_url` rather than a `covers.Cover`: the record needs the **hash of the bytes**, and those are not fetched
    yet. A URL is not a cover, and downloading is a separate step with its own failure mode.
    """

    isbn: str
    title: str
    author: str
    publisher: str
    #: ⚠️ The source's own string — `2026-10-14`, `2026-10` or `2026` — never a label (ADR 0003).
    published: str | None
    #: The vendor's own category words. `genre.slug_for` maps them, and an unknown one is `other` (ticket 26).
    category: str
    cover_url: str | None
    #: ⚠️ Ticket 23's review signal, and Google Books is one of the two places it comes from — *"cumulative popularity
    #: signals … which are not six-month sales, but are long-window and free."*
    rating: float | None = None
    #: ⚠️ **Carried beside the rating, never instead of it.** A rating without its count is the trap ticket 23 names.
    ratings_count: int | None = None


def parse_volume(payload: bytes, *, isbn: str) -> Volume | None:
    """One volume lookup, or **`None` when it is not a match**.

    ⚠️ **Four different `None`s, and they are one thing to a caller:** no items, no `volumeInfo`, no ISBN-13, or an
    ISBN-13 that is not the one asked for. Each means *this source has nothing to say about this title* — and ticket 07's
    rule is that a field with no value **omits**, so the caller must not be handed a half-filled row to draw.

    ⚠️ **The ISBN is compared as a normalised ISBN-13**, not as a string. Google Books returns `9788172151234` for one
    volume and `978-81-7215-123-4` for another, and a string comparison would call the second a mismatch — a **false
    refusal**, which is the failure that looks like a missing book rather than like a bug.
    """
    body = json.loads(payload)
    items = body.get("items") or []
    if not items:
        return None

    info = items[0].get("volumeInfo") or {}

    identifiers = info.get("industryIdentifiers") or []
    found = {
        entry.get("type"): entry.get("identifier")
        for entry in identifiers
        if isinstance(entry, dict)
    }
    resolved = enrich.isbn13(found.get("ISBN_13") or "")
    if not resolved or resolved != enrich.isbn13(isbn):
        return None

    # ⚠️ **`thumbnail` before `smallThumbnail`**, and the order matters less than it looks: both are then forced to
    # `zoom=2` by `covers.google_books_url`, so the difference is only which link the vendor considers canonical.
    links = info.get("imageLinks") or {}
    raw = links.get("thumbnail") or links.get("smallThumbnail")

    return Volume(
        isbn=resolved,
        title=info.get("title") or "",
        # ⚠️ Google Books carries a **list** of authors and the slide has one line for it. Joined, never truncated here:
        # ticket 07's ellipsis is the renderer's, and a client that shortened a list would be making a layout decision.
        author=", ".join(info.get("authors") or []),
        publisher=info.get("publisher") or "",
        published=info.get("publishedDate") or None,
        category=(info.get("categories") or [""])[0],
        # ⚠️ `if raw` and not `is not None`: an **empty string** would normalise into a request to nowhere, and the
        # renderer reaches ticket 07's branded tile by reading `cover: null`.
        cover_url=covers.google_books_url(raw) if raw else None,
        # ⚠️ **The pair travels together, and each is `None` on its own terms.** A rating with no count is the trap
        # ticket 23 names, and a count with no rating is equally useless — but the *fields* are independent, so a
        # response carrying one and not the other is recorded as exactly that rather than rounded to a zero.
        rating=_number(info.get("averageRating")),
        ratings_count=_whole(info.get("ratingsCount")),
    )


def _number(value: object) -> float | None:
    """⚠️ A vendor number, or `None` — **never coerced to zero**, because *"a missing value and a real zero are
    different facts"*. A `0.0` rating would be a book rated *terribly* rather than one nobody has rated.
    """
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _whole(value: object) -> int | None:
    """The same rule for a count, which arrives as a number and is stored as one."""
    number = _number(value)
    return int(number) if number is not None else None


def details(volume: Volume, *, cover: covers.Cover | None = None) -> enrich.Details:
    """A `Volume` as the row's fields — with the cover **only if its bytes were fetched**.

    ⚠️ **The cover arrives separately because it has to.** A URL is not a cover: the record holds the *hash* of the bytes
    (ticket 05), and a `Details` whose `cover` was set from a URL alone would put a row in the snapshot claiming a cover
    the cache does not hold. ⚠️ That is the exact state `stage.covers` refuses on — and a render is what taught us why
    it must.
    """
    return enrich.Details(
        title=volume.title,
        author=volume.author,
        publisher=volume.publisher,
        published=volume.published,
        category=volume.category,
        cover=cover,
        rating=volume.rating,
        ratings_count=volume.ratings_count,
    )


def fetch(isbn: str) -> Volume | None:
    """Look one ISBN up. ⚠️ The **boundary** — deliberately not covered by the suite, which stays hermetic.

    ⚠️ `q=isbn:…` rather than the `/volumes/{id}` path: the volume id is Google's own opaque string, and this product
    knows the ISBN, not the id. The mismatch check in `parse_volume` is what makes the search safe to use here — a search
    that answers with a different book is refused rather than believed.
    """
    query: dict[str, str] = {"q": f"isbn:{isbn}"}
    key = os.environ.get(KEY_ENV)
    if key:
        query["key"] = key

    url = f"{BASE}?{urllib.parse.urlencode(query)}"
    with urllib.request.urlopen(url, timeout=30) as response:
        return parse_volume(response.read(), isbn=isbn)
