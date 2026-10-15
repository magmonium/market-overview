"""The source clients — one module per vendor.

⚠️ **Fetch and parse are separated in each module, and only the parse is tested.** The brief draws the same line
(`_degrade(day, name, fetch, parse, default)` — *"Fetch one non-spine feed, snapshot it, shape it"*), for two reasons: a
parser is a **pure function of bytes**, and the suite is **hermetic** — *"nothing in it reaches the network."*

⚠️ **And the conductor does the snapshotting, which is why `fetch` hands back a `Page` rather than rows.** The brief's
ordering is *fetch → snapshot → parse*, and the middle step needs the **week** — so a client that parsed its own response
would have nowhere to write the evidence. ⚠️ That is not a stylistic preference: ticket 18's rule is that *"the raw
response is snapshotted **even when parsing fails** — at that point the evidence of what was actually received is exactly
what is needed"*, and a client that had already parsed could only ever hand back a response the parser had vouched for.

⚠️ So every module here exposes two things and no more:

    fetch(chart) -> Iterable[Page]                    the boundary — talks to the vendor, parses nothing
    parse(payload, *, listing) -> list[Row]           the seam — a pure function of bytes

and `cli.gather` runs between them, writing each page to `store/<week>/raw/` before it is read.
"""
from __future__ import annotations

import dataclasses

from .. import charts


@dataclasses.dataclass(frozen=True)
class Page:
    """One vendor's answer for one list — **the bytes, and what they were asked for.**

    ⚠️ **`listing` rides along because a response cannot always say which list it is.** NYT's payload carries a
    `list_name_encoded`; an Amazon bestseller page carries **no list name at all**, and the address is the only thing that
    knows. So the pairing is made by the client, which is the only place that knows both halves.

    ⚠️ **`name` is the client's, not a derivation from the slug** — the brief's `result.name`, for the same reason. A
    slug is `amazon-in/comics` and a filename cannot hold a slash; more to the point, only the client knows whether what
    it fetched is JSON or HTML, and the extension is a fact about the response rather than about the list.

    ⚠️ ⚠️ **And `published` rides along for the same reason `listing` does: a response cannot always say when it is
    from.** `indie`'s list is dated **in its own address**, so the page itself carries no date a parser could read —
    ⚠️ and without this field the rows arrived *undated*, which `freshness` correctly refuses, so the English chart
    could never be built. ⚠️ A client that cannot state the date leaves it empty, and an empty date is *stale* rather
    than a guess.
    """

    listing: charts.Listing
    name: str
    #: ⚠️ **Bytes, never a decoded object** — `store.write_raw`'s own argument: a snapshot written from `json.loads` has
    #: been through a model, so it can no longer settle an argument about what the vendor actually said.
    payload: bytes
    #: ⚠️ The date the client **asked for**, when its address carried one — ISO, or empty when the vendor states none.
    #: ⚠️ `gather` hands this to `parse`, so it is the only route by which a URL-borne date reaches a row.
    published: str = ""

