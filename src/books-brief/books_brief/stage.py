"""The snapshot, placed where a composition can fetch it — `public/` (ticket 09).

⚠️ **A Remotion composition can only serve assets from the render project's own `public/` folder**, and this product's
snapshot lives in `store/` — inside the project, committed, and not servable. So a run **copies** the week's
`facts.json` there for the duration of the render.

| | |
|---|---|
| **the copy is scratch** | `store/` is the committed evidence; `public/` is gitignored, because it holds nothing but staging |
| **byte for byte** | the renderer must read *exactly* the snapshot's bytes — re-serialising would reorder keys and re-escape the Bengali titles the operator can read |
| **the name is kept** | `facts.json` is what the file is called on both sides, so a fetch path that does not look like the snapshot is a path nobody can trace |
| **the week namespaces it** | `public/weeks/<week>/` — so a render of one week cannot read another's, which is the same reason the store is keyed that way |

⚠️ **The staged path and the URL are two sides of a subprocess boundary**, exactly like `render.ENTRY`: `url_for` is
what the composition hands to Remotion's `staticFile`, and `staged_path` is where the copy lands. They are asserted
against each other in `tests/test_stage.py`, because a disagreement between them surfaces as a *missing file* inside
Remotion rather than as a failing test.
"""
from __future__ import annotations

import json
import pathlib
import shutil
from typing import Iterable

from market_overview import logo

from . import covers as cover_cache
from . import enrich, paths, store

#: ⚠️ The folder inside `public/` that holds the staged weeks. Spelled once, and the composition's own literal
#: (`remotion/facts.ts`) points back here.
WEEKS = "weeks"

#: ⚠️ The mark, staged **once and not per week** — it is identical for every chart and every week (ticket 09), so
#: staging it beside each week would be the same bytes four times.
MARK = "mark.json"

#: ⚠️ Where a chart's covers are staged. **Mirrored by `remotion/facts.ts`**, which is the other half of this
#: subprocess boundary and cannot share the constant across a language.
COVERS = "covers"


def url_for(week: str) -> str:
    """The path **inside `public/`** the composition fetches — what `staticFile` resolves.

    ⚠️ Forward slashes, deliberately: this is a URL path, not a filesystem one, and it is handed to a browser.
    """
    return f"{WEEKS}/{week}/{store.FACTS}"


def staged_path(week: str, public_dir: pathlib.Path) -> pathlib.Path:
    """Where `week`'s snapshot is staged, whether or not it is there yet."""
    return public_dir / WEEKS / week / store.FACTS


def snapshot(week: str, public_dir: pathlib.Path) -> pathlib.Path:
    """Copy `store/<week>/facts.json` into `public/`, creating the folder, and return the staged path.

    ⚠️ **A copy, never a move and never a re-serialisation.** If the snapshot and the staged file ever differ by a byte,
    the render is of something the run did not build — which is why the test compares the two digests rather than
    trusting the `copyfile` call.

    ⚠️ **The folder is created**, because `public/` is gitignored and a fresh clone has none — and `copyfile` into a
    missing directory raises rather than creating it.

    ⚠️ **A missing snapshot is `FileNotFoundError`, not an empty stage.** A week is only ever rendered from a snapshot
    that was written (ADR 0003 — the snapshot's existence is the switch), so a missing one means the caller skipped the
    build, and saying so here is a long way closer to the cause than a fetch error inside Remotion.
    """
    source = store.dir_for(week) / store.FACTS
    if not source.is_file():
        raise FileNotFoundError(
            f"{week}: no snapshot at {source} — a week is rendered from a snapshot, so build it first"
        )

    target = staged_path(week, public_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return target


def mark_url() -> str:
    """The path inside `public/` the composition fetches for the mark — `mark.json`."""
    return MARK


def mark(public_dir: pathlib.Path) -> pathlib.Path:
    """Stage the operator's mark, or **an explicit `null`** when they have not supplied one.

    ⚠️ **`null` rather than *no file*, and that is the load-bearing half.** A composition can only fetch from
    `public/`, so an absent `mark.json` is a **404 inside Remotion** — a failed render to learn something that was
    never an error. Writing `null` makes the fetch always succeed and leaves *no mark* a state the renderer reads
    rather than one it fails on.

    ⚠️ **And no mark is a valid brief**, not a broken one: `Brand.tsx` says it plainly — *"the mark is the operator's to
    drop in, and until they do the brief still renders, just without it. A placeholder wordmark would be inventing
    branding, which is worse than not having any."*

    ⚠️ **The brief's own loader, not a re-implementation** (ticket 09): `logo.load` reads the asset, derives the chip
    fill from the mark's ink polarity, and **refuses** an asset that is not self-contained. That refusal propagates, on
    the brief's rule that *"an unusable asset is a refusal"* — and it is raised **before** the render, so a licence
    problem costs a second rather than a two-minute render that was never going to work.
    """
    target = public_dir / MARK
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(logo.load(paths.mark_dir()), ensure_ascii=False), encoding="utf-8"
    )
    return target


def covers_url(isbn: str) -> str:
    """The path inside `public/` the composition fetches for one cover."""
    return f"{COVERS}/{isbn}.jpg"


def covers(isbns: Iterable[str], public_dir: pathlib.Path) -> list[pathlib.Path]:
    """Stage the covers for these ISBNs — and ⚠️ **only for ISBNs whose row records one.**

    ⚠️ **The cache is in the data root and `staticFile` can only serve from `public/`**, so a slide pointing at
    `resource/books/covers/` would render a broken image. Copying is the only way across, and it is cheap because the
    cache is keyed by ISBN and the superset repeats titles (ticket 14) — a book in both the Bengali and the
    all-language chart is staged **once per run**, which is why the caller passes every chart's ISBNs together rather
    than calling this per chart.

    ⚠️ **A row with no cover stages nothing, deliberately.** Ticket 07's missing-cover rule is a **branded tile** — the
    book's initial on `BG` with a `RULE` border — and the renderer reaches it by finding `cover: null` on the row. So an
    absent file is not a gap to be filled; it is the signal for a designed state.

    ⚠️ **A cover recorded but missing from the cache is a REFUSAL, and this was learned from a render rather than
    reasoned out.** The tempting behaviour is to skip it and let the tile draw — and that is what this function did
    first, on the argument that *"one lost JPEG must not refuse a week."* ⚠️ **It does not work, and it fails in the
    worst possible way:** the row still says `cover: {url, sha256}`, so the renderer asks for a file that was never
    staged, Remotion's `<Img>` gets a 404 and **cancels the whole render**. The week is refused anyway — just later,
    with `Error loading image with src: …/covers/…jpg` instead of the ISBN that is actually missing.

    ⚠️ And the refusal is *correct*, not merely convenient: ticket 05's cache is what makes a rebuild possible
    **without committing hundreds of images a week**. So a recorded cover whose bytes have vanished means the snapshot
    is **no longer reproducible from disk** — which is precisely the thing this product must not discover halfway
    through a render.
    """
    staged: list[pathlib.Path] = []

    for isbn in isbns:
        source = cover_cache.path_for(isbn)
        if not source.is_file():
            raise FileNotFoundError(
                f"{isbn}: the snapshot records a cover but {source} is not cached — the row would render a "
                f"request for a file that does not exist, which cancels the render rather than drawing the tile. "
                f"Either restore the cache or rebuild the week."
            )

        target = public_dir / COVERS / f"{isbn}.jpg"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        staged.append(target)

    return staged
