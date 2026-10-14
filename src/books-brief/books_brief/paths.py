"""Where the Books Brief's folders are — the seams a test patches.

⚠️ **Two kinds of seam, where the reel found there used to be one.** This product's *data* — the cover cache it reads
and the packages it writes — lives under the **shared data root** (`market_overview.paths`), outside the repository,
namespaced `resource/books/` and `output/books/` so a books run and a brief can proceed without touching the same file.
What stays in the project is what is *not* data: `store/`, the committed snapshot that makes a rebuild a rebuild
(ADR 0007), and `public/`, which is scratch for a render that runs from this tree.

⚠️ **`data_root()` is defined *here*, and every data folder calls it by that module-level name.** Delegating straight to
the brief's own resolver would leave half the layout outside this module's seam, so patching
`books_brief.paths.data_root` would redirect `output/` and not `resource/` — **one test seam quietly covering half of
what it claims to.**

⚠️ A named function per folder rather than an inline path, so a test can point the whole tool at a temporary root
without freezing anything else — the habit of the brief's `store.root()`.
"""
from __future__ import annotations

import pathlib

from market_overview import paths as brief_paths

#: The product's own half of the shared data root. ⚠️ Spelled here rather than in the brief: the brief names its own
#: namespace and nothing else, and this is the other half of the same rule.
BOOKS = "books"


def project_root() -> pathlib.Path:
    """This product's own project — `store/`, `remotion/` and `tests/` sit under it.

    ⚠️ **`parents[1]`, not `parents[2]`.** The package sits directly in the project, with no `src/` layer of its own:
    the project already lives inside the repository's `src/`, so `src/books-brief/src/books_brief/` would be a `src`
    inside a `src` for no gain. One level up from `books_brief/paths.py` is the project; two is the repository.
    """
    return pathlib.Path(__file__).resolve().parents[1]


def data_root() -> pathlib.Path:
    """The shared data root — the brief's own resolver, reused rather than re-derived.

    ⚠️ **One environment variable for every product.** `MARKET_OVERVIEW_DATA` overrides it; the default and the
    reasoning live in the brief's `paths.py`, and there is deliberately only one copy of them.
    """
    return brief_paths.data_root()


def cover_cache_dir() -> pathlib.Path:
    """`resource/books/covers/` — ticket 05's cache, **keyed by ISBN**.

    Keyed by ISBN and not by week, because a cover is immutable per ISBN: one fetch serves every chart and every week
    the title appears in, which is what makes the superset's repetition free rather than duplicated.
    """
    return data_root() / "resource" / BOOKS / "covers"


def public_dir() -> pathlib.Path:
    """`public/` — **render staging, and it is not data** (ticket 09).

    ⚠️ **Deliberately not under `data_root()`, and that is why it is its own function rather than a line in another.**
    A Remotion composition can only serve an asset from the render project's **own** `public/` folder, so a staging
    directory in the shared data root would be a directory the renderer cannot see. ⚠️ The consequence is a test seam
    that must *not* follow `data_root`: relocating the root for a test has to leave this alone, or the test would be
    asserting a folder Remotion never looks in.

    ⚠️ **It is gitignored, per project** — see this project's own `.gitignore`, which exists because the repository's
    root-level `public/*` is anchored there and does not reach into `src/books-brief/`.
    """
    return project_root() / "public"


def mark_dir() -> pathlib.Path:
    """The brief's `resource/brief/` — **one licensed mark serves every product** (ticket 09).

    ⚠️ **Deliberately the brief's folder, not a copy under `resource/books/`.** The mark is a licensed asset, and two
    folders holding it means two files that can disagree — so this product reads the brief's own, through the brief's
    own loader, and there is exactly one file to replace when the licence changes.
    """
    return brief_paths.brief_resource()


def output_dir() -> pathlib.Path:
    """`output/books/<week>/<chart>/` — the packages, under the shared data root (ticket 13)."""
    return data_root() / "output" / BOOKS
