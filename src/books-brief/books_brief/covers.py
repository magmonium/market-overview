"""Ticket 05 — covers: where they come from, and where they are kept.

⚠️ **Download-and-embed, never hotlinked.** The host repo's precedent is unambiguous — `logo.load` inlines the mark as
a data URI, the music bed is muxed, and `public/` is explicitly preview scaffolding. A renderer that reached the
network for a hundred covers per chart would break the rebuild promise ADR 0003 rests on.

⚠️ **The cache is keyed by ISBN, not by week**, because a cover is immutable per ISBN: one fetch serves every chart and
every week a title appears in. That is what makes the superset's repetition (ticket 14) free rather than duplicated.

⚠️ **The snapshot records the source URL and a hash** (ticket 05), not the bytes — which is what keeps a rebuild
possible without committing hundreds of images a week. The *evidence* is committed; the *bytes* are cached.
"""
from __future__ import annotations

import dataclasses
import hashlib
import pathlib
import urllib.error
import urllib.parse
import urllib.request

from . import paths

#: ⚠️ **Raised from Google Books' default.** `zoom=1` is a thumbnail, and a thumbnail on a 1080p slide is a smudge.
ZOOM = 2

#: ⚠️ **`edge=curl` is stripped**, not kept: it draws a decorative curled page-corner into the image, which is wrong
#: for a clean cover. Ticket 05 named this trap specifically.
_DROP = "edge"

#: ⚠️ ⚠️ **The browser identity this client has to present, and it is not decoration** (2026-10-15). BoiChitro's
#: WordPress uploads answer **`403 Forbidden` to `Python-urllib/3.x`** and **`200` to a browser string** — verified by
#: fetching one image both ways — ⚠️ so *every* cover the Bengali chart's Indian vendor offered was discarded as
#: unreachable and all hundred rows fell to ticket 07's branded tile. ⚠️ A shop that blocks a library's default
#: User-Agent is not asking this product to stop fetching; it is asking it to say what it is.
BROWSER = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/140.0 Safari/537.36"
    ),
    #: ⚠️ An image request from a browser asks for images. `*/*` is what a library sends, and what a bot filter looks for.
    "Accept": "image/avif,image/webp,image/*,*/*;q=0.8",
}

#: ⚠️ **The characters a URL may keep unescaped** — the delimiters, plus `%` so an existing escape is not encoded twice.
#: Everything else, including every non-ASCII character, is percent-encoded before the request is made.
_SAFE = ":/?#[]@!$&'()*+,;=%~"

#: Open Library's large size. `?default=false` turns a missing cover into a **404** instead of a blank image, so the
#: run can tell *no cover* from *a cover that is a white rectangle*.
OPEN_LIBRARY = "https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false"


def encodable(url: str) -> str:
    """A URL `urllib` can actually send — **the non-ASCII parts percent-encoded, the structure left alone**.

    ⚠️ ⚠️ **A defect the Bengali chart's second vendor exposed** (ticket 30). BoiChitro serves covers from filenames
    carrying an **en dash** — `…/WhatsApp-Image–2026….webp` — and `urllib` writes its request line as **ASCII**, so
    `urlopen` raised `UnicodeEncodeError` *before the request was made*. ⚠️ The caller sees that as *"the cover did not
    download"*, which is the same sentence a 403 produces — so the row lost its cover for a reason that had nothing to do
    with the book, and the report said something else. ⚠️ A browser percent-encodes the path before it asks; this is that
    normalisation, with the delimiters kept (a `?` that became `%3F` would turn a query into part of the path).
    """
    return urllib.parse.quote(url, safe=_SAFE)


def google_books_url(raw: str) -> str:
    """Google Books' cover URL, normalised.

    ⚠️ Three fixes, and the first two are visible defects if missed: **`https`** (an `http` image is mixed content),
    **no `edge`** (the curled corner is drawn into the picture), and a **raised `zoom`** (the default is a thumbnail).
    """
    parsed = urllib.parse.urlsplit(raw)
    query = dict(urllib.parse.parse_qsl(parsed.query))
    query.pop(_DROP, None)
    query["zoom"] = str(ZOOM)

    return urllib.parse.urlunsplit(
        ("https", parsed.netloc, parsed.path, urllib.parse.urlencode(query), "")
    )


def open_library_url(isbn: str) -> str:
    """The fallback source, by ISBN."""
    return OPEN_LIBRARY.format(isbn=isbn)


def path_for(isbn: str) -> pathlib.Path:
    """`resource/books/covers/<isbn>.jpg` — the cache, keyed by ISBN (ticket 05)."""
    return paths.cover_cache_dir() / f"{isbn}.jpg"


@dataclasses.dataclass(frozen=True)
class Cover:
    """Where a cover came from, and what it was — **the evidence, not the bytes** (ticket 05).

    ⚠️ **The URL and the hash together, and neither alone is enough.** The URL says where it came from; the hash says
    whether the file still on disk is the one the chart was built from. A publisher can re-issue a cover under the same
    URL, so a snapshot holding only the URL could not tell a rebuild that the image had changed underneath it — and the
    bytes are deliberately **not** committed, because hundreds of images a week is not evidence, it is a mirror.
    """

    url: str
    sha256: str


def url_for(isbn: str, *, listed: str = "", google: str | None = None) -> str:
    """The URL to fetch this cover from — **ticket 05 §1's source order**, and the normalisation that goes with it.

    ⚠️ **Three sources, and the order is the decision.** The **list's own image** first — the vendor chose the picture
    that represents the title it ranked, and a cover is the one field where the list's answer beats Google's, whose
    edition is not necessarily the edition that is selling. Then **Google Books `imageLinks`**, which costs no extra
    request because identity resolution already read the volume (ticket 05 §3). Then **Open Library**, which is the
    fallback for a volume Google knows but has not scanned.

    ⚠️ ⚠️ **Open Library is *terminal*, and that is what makes a keyless run produce covers at all.** The two sources
    above it can both go dark for reasons that have nothing to do with this book — Amazon ships no image on some rows,
    and Google Books answers a whole chart with `429 Quota exceeded … Queries per day` once the project's daily quota is
    spent. ⚠️ A fallback that is only reached when Google *answers without an image* is not a fallback: it is dead code
    on exactly the run that needs it, and every row falls to ticket 07's branded tile while three sources sit unused.

    ⚠️ **The chosen URL is the normalised one.** Picking the source and *fixing* the source are one decision, and a
    caller that had to remember to also call `google_books_url` would eventually not — which is how `edge=curl` and a
    `zoom=1` thumbnail reach a slide. ⚠️ **The list's URL is passed through untouched**, because the normalisation is
    Google's own (`edge=curl`, `zoom`) and a CDN URL carries neither.

    ⚠️ **Falsy, not `is None`.** Google Books omits `imageLinks` on plenty of volumes and a scraped row with no image
    carries `""`, and a client that normalised either omission to a truthy value would send this down the wrong branch
    with an empty URL — a request to nowhere, which surfaces as a fetch error rather than as *this title has no cover*.
    """
    if listed:
        return listed
    if google:
        return google_books_url(google)
    return open_library_url(isbn)


def download(url: str, isbn: str) -> Cover | None:
    """Fetch one cover, hash it, cache it under the ISBN, and return the record — or `None` when there is no cover.

    ⚠️ **The cache answers before the network does**, and that is a budget decision rather than a speed one: Open Library
    allows **100 requests per IP per 5 minutes**, so re-downloading images already on disk spends the quota a run needs
    for the covers it does *not* have.

    ⚠️ **A 404 is `None` and never an empty file.** `?default=false` on the Open Library URL is what turns *"this cover
    does not exist"* into a status the run can read, instead of the **blank image** the default would give it. ⚠️ And
    nothing is cached on that path: an empty file would be a cover that exists and is blank — the one state the pipeline
    could not tell from a real one.

    ⚠️ **Anything that is not a 404 propagates.** A timeout or a 500 is *the source being unreachable*, which is a
    different fact from *this book has no cover*: the first is a run that should be retried, the second is a branded tile
    (ticket 07). Swallowing them together would silently record a temporary outage as a permanent absence.

    ⚠️ **The request says it is a browser and escapes its URL** — `BROWSER` and `encodable`, and both were found the hard
    way: without the first, a whole chart's covers answered `403`; without the second, a URL with an en dash in it raised
    before it was sent. ⚠️ **Both failures wore the same message**, which is why they are fixed in one place and named in
    the report by their own text.

    ⚠️ **Written atomically**, like the snapshot: a half-written JPEG is a corrupt image that *looks* like a cover, and
    the next run would find it on disk and use it.
    """
    cached = path_for(isbn)

    if cached.is_file():
        return Cover(url=url, sha256=hashlib.sha256(cached.read_bytes()).hexdigest())

    try:
        with urllib.request.urlopen(  # noqa: S310 - the URL is built by this module
            urllib.request.Request(encodable(url), headers=BROWSER), timeout=30
        ) as response:
            body = response.read()
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise

    cached.parent.mkdir(parents=True, exist_ok=True)
    temporary = cached.with_name(f".{cached.name}.part")
    temporary.write_bytes(body)
    temporary.replace(cached)

    return Cover(url=url, sha256=hashlib.sha256(body).hexdigest())


