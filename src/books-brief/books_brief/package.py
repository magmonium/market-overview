"""Ticket 13's package — `output/books/<week>/<chart>/`, assembled atomically.

**A package is one chart's complete deliverable**, and it has to be handable to its own uploader without picking files
out of a mixed folder. So the folder holds the video, the metadata text, the metadata JSON and the thumbnail.

⚠️ **The two files that leave the folder carry the week *and* the chart in their names** — `bengali-2026-W41.mp4` and
`thumbnail-2026-W41-bengali.jpg`. The two metadata files stay in the folder, so they carry the chart alone and the week
is the directory they are in. ⚠️ The split is the brief's own reasoning: the property worth protecting is that *"a file
dragged out of its directory still identifies itself"*, and the failure it prevents is a Bengali thumbnail uploaded
beside a comics video.

⚠️ **The JSON is written last, and it is what marks the package complete.** The renders write their own files, each
individually staged-and-renamed, so this module cannot make the *directory* appear in one step. What it can do is make
the directory's **completeness observable**: `metadata-<chart>.json` exists only in a finished package, and it is
deleted **before** anything else is written — so a run that dies half way leaves a folder that visibly is not finished
rather than one that merely looks small.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import tempfile

from . import charts, metadata, paths, store, window

#: ⚠️ The video, and it names both keys — see the module docstring.
VIDEO = "{chart}-{week}.mp4"
#: ⚠️ The thumbnail, and it names both keys too: it is the other file that leaves the folder.
THUMBNAIL = "thumbnail-{week}-{chart}.jpg"


class PackageError(RuntimeError):
    """The package cannot be assembled — an incomplete artefact, or a chart with nothing to describe."""


def MANIFEST(chart: str) -> str:
    """The file whose presence means *this package is finished*. See the module docstring."""
    return f"metadata-{chart}.json"


def TEXT(chart: str) -> str:
    """The human's half of the metadata."""
    return f"metadata-{chart}.txt"


def dir_for(week: str, chart: str) -> pathlib.Path:
    """`output/books/<week>/<chart>/` — **one package per chart** (ticket 13)."""
    return paths.output_dir() / week / chart


def filenames(week: str, chart: str) -> dict[str, str]:
    """The four artefacts, named."""
    return {
        "video": VIDEO.format(chart=chart, week=week),
        "text": TEXT(chart),
        "json": MANIFEST(chart),
        "thumbnail": THUMBNAIL.format(chart=chart, week=week),
    }


def bundle_hash(week: str) -> str:
    """The snapshot's sha256 — ⚠️ **so a deferred uploader can say which week's facts the text describes.**

    A package whose JSON named a different bundle from the one on disk is a package built from something else, and the
    description would be describing a chart nobody rendered.
    """
    digest = hashlib.sha256()
    digest.update((store.dir_for(week) / store.FACTS).read_bytes())
    return digest.hexdigest()


def _grouped(value: int) -> str:
    """`en-IN` grouping — ⚠️ **₹1,29,900 is not ₹129,900.**

    The description sits beside a slide that groups prices the Indian way, and a reader comparing the two would see two
    different numbers for one book. ⚠️ Python's own `f"{n:,}"` is Western, so the grouping is done here rather than
    inherited from a format spec.
    """
    text = str(value)
    if len(text) <= 3:
        return text
    head, tail = text[:-3], text[-3:]
    groups: list[str] = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    return ",".join([*groups, tail])


#: ⚠️ ⚠️ **The symbols the *description* writes — and why the amount alone will not do** (2026-10-15).
#:
#: ⚠️ This was `_rupees(amount)`: a hard-coded `₹` on every price, which was true while every chart was **India-anchored**
#: (ticket 12). ⚠️ **It has not been true since ticket 19** — the English chart's rows are priced in `USD`, `CAD` and
#: `AUD`, and the comics chart's in `CAD` and `INR`. ⚠️ Measured on the re-gathered week, the description printed
#: **`₹31` for a `CAD 30.60`** row: ticket 19's own named failure (`₹24.99`-for-`$24.99`), arriving in the **upload
#: text** rather than on the slide, where nothing had looked.
#:
#: ⚠️ **A currency with no symbol here is written as its code**, because a bare number is the ambiguity this product keeps
#: refusing: `CAD 30.60` cannot be misread, and `₹31` can.
SYMBOLS: dict[str, str] = {
    "INR": "₹",
    "USD": "$",
    "CAD": "CA$",
    "AUD": "A$",
    "GBP": "£",
    "EUR": "€",
    "BDT": "৳",
}


def _price(price: dict) -> str:
    """`₹399`, `CA$31`, `SEK 240`, or `""` — ⚠️ **never `₹0`, and never another currency's sign.**

    ⚠️ A **string**, and this is one of the few places a display string is right: ticket 15's description is never
    *drawn*, it is written beside the video to be pasted into an uploader — `metadata.py`'s own docstring draws that line.

    ⚠️ The amount and the currency ride **together** in the snapshot (`Price.currency`, ticket 04), so the text is built
    from both or from neither: a missing price and a real zero are different facts, and so are two currencies. ⚠️ An
    **empty** currency is the documented *unknown* degrade — the number is written with no sign, exactly as the slide
    draws it (ADR 0003).
    """
    amount = price.get("amount")
    if not isinstance(amount, (int, float)):
        return ""

    number = _grouped(round(amount))
    currency = price.get("currency") or ""
    if not currency:
        return number
    symbol = SYMBOLS.get(currency)
    return f"{symbol}{number}" if symbol else f"{currency} {number}"


def _rows(bundle: dict, chart: str) -> list[metadata.Row]:
    """The chart's rows, as the description needs them — **read from the snapshot, not from the renderer.**

    ⚠️ **The snapshot, not the bundle that is in memory.** Assembly runs *after* the week is written, so reading it back
    is what proves the committed evidence is enough to rebuild the text — a description built from a live object could
    carry something the snapshot never held, and a later re-run would produce a different one.
    """
    return [
        metadata.Row(
            rank=int(row["rank"]),
            title=row["title"],
            author=row["author"],
            publisher=row["publisher"],
            price=_price(row["price"]),
        )
        for row in bundle.get("charts", {}).get(chart, {}).get("ranked", [])
    ]


def assemble(week: str, chart: charts.Chart) -> metadata.Metadata:
    """Finish one chart's package: write both metadata files, JSON last. Returns what was written.

    ⚠️ **The manifest is deleted first, deliberately.** If it were only written at the end, a re-run that *failed* would
    leave the **previous** run's JSON in place — and the folder would read as a finished package built from facts that
    are no longer the ones on disk. Removing it up front is what makes *"the JSON exists"* a statement about **this**
    run.
    """
    directory = dir_for(week, chart.slug)
    names = filenames(week, chart.slug)
    manifest = directory / names["json"]

    # 1 — the package is not complete until this succeeds, and it must not look complete until then.
    manifest.unlink(missing_ok=True)

    # 2 — refuse rather than write text about artefacts that are not there. A description claiming a video exists while
    #     nothing plays is worse than no package, because the folder looks finished.
    missing = [
        name
        for key, name in names.items()
        if key in ("video", "thumbnail") and not (directory / name).is_file()
    ]
    if missing:
        raise PackageError(
            f"{week}/{chart.slug}: {', '.join(missing)} missing from {directory} — refusing to write metadata for "
            f"a package that would look complete and would not be"
        )

    bundle = store.read_facts(week)

    text = metadata.build(
        week,
        chart,
        _rows(bundle, chart.slug),
        # ⚠️ **The window the chart actually has** (ticket 23), taken from the snapshot rather than recomputed — the
        # description has to state the same number the slide does, and the slide reads it from the same place.
        basis_weeks=bundle["meta"]["window_weeks"],
        published_on=window.monday(week),
        video=names["video"],
        thumbnail=names["thumbnail"],
        bundle_hash=bundle_hash(week),
    )

    # 3 — the human's file, then the machine's. ⚠️ The order matters: the JSON is the completion marker, so it has to
    #     be the last thing to appear.
    write_atomically(directory / names["text"], text.as_text())
    write_atomically(
        manifest,
        json.dumps(text.as_json(), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    )
    return text


def write_atomically(path: pathlib.Path, text: str) -> pathlib.Path:
    """Write one file atomically — the same temp-file-then-rename as `store.write_facts`.
    ⚠️ `fsync` before the rename, not after: the rename is atomic but the *contents* are not, so a machine that lost
    power between them would leave a correctly-named file with nothing in it — the "looks complete" failure this module
    exists to prevent.

    ⚠️ And an explicit `chmod 0644`, because `mkstemp` creates `0600` and `os.replace` keeps it. Without it the two
    metadata files are owner-only while the video beside them is world-readable, which is a papercut the day the
    uploader is not the person who ran the build.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}-", suffix=".part")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    except BaseException:
        pathlib.Path(temporary).unlink(missing_ok=True)
        raise
    return path
