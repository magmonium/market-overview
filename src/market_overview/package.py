"""The package — `output/brief/<date>/<lang>/`, assembled atomically. (0085_13)

**A package is one language's complete deliverable**, and it has to be handable to its own uploader without picking
files out of a mixed folder. So the folder holds the video, the metadata text, the metadata JSON and the thumbnail,
and every filename carries **date and language** — a file dragged out of its directory still identifies itself, which
is exactly the property whose loss uploads a Bengali thumbnail beside an English video.

## What "atomic" means here, and why it is not folder-atomic

⚠️ **The JSON is written last, and it is what marks the package complete.** The renders write their own files — that is
0085_11 and 0085_12's business, and each of those is individually staged-and-renamed — so this module cannot make the
*directory* appear in one step. What it can do is make the directory's **completeness observable**: `metadata-<lang>.json`
exists only in a finished package, and it is deleted before the rest is written, so a run that dies half way leaves a
folder that visibly is not finished rather than one that merely looks small.

The alternative — rendering into a staging directory and renaming the whole folder — was rejected as worse. It would
mean the render path knowing about packages, and it would still not be atomic across two processes: a crash after the
rename but before the JSON lands is the same problem one directory higher up.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import tempfile
from typing import Any

from market_overview import metadata as metadata_module
from market_overview import render, store


class PackageError(RuntimeError):
    """The package cannot be assembled — an incomplete artefact, or a filename that does not identify itself."""


def MANIFEST(lang: str) -> str:
    """The file whose presence means *this package is finished*. See the module docstring."""
    return f"metadata-{lang}.json"


def TEXT(lang: str) -> str:
    return f"metadata-{lang}.txt"


def bundle_hash(date: str) -> str:
    """The facts bundle's sha256, recorded per edition.

    ⚠️ **Per edition, not per run**, which is issue 20's point: the two packages are separate deliverables and each
    names the exact bundle it was built from. Two hashes that differ would say the editions were rendered from
    different facts, which is the one thing the bilingual pair is not allowed to be.
    """
    digest = hashlib.sha256()
    digest.update((store.dir_for(date) / store.FACTS).read_bytes())
    return digest.hexdigest()


def _write(path: pathlib.Path, text: str) -> pathlib.Path:
    """Write one file atomically — the same temp-file-then-rename as `store.write_facts`.

    ⚠️ `fsync` before the rename, not after: the rename is atomic but the *contents* are not, so a machine that lost
    power between them would leave a correctly-named file with nothing in it. That is precisely the "looks complete"
    failure this module exists to prevent.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}-", suffix=".part")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        # ⚠️ `mkstemp` creates `0600`, and `os.replace` keeps it — so without this the two metadata files are
        # owner-only while the video and thumbnail beside them are `0644`. A package with mixed permissions is a
        # papercut the day the uploader is not the user who ran the build.
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    except BaseException:
        pathlib.Path(temporary).unlink(missing_ok=True)
        raise
    return path


def filenames(date: str, lang: str) -> dict[str, str]:
    """The four artefacts, named. ⚠️ **Every one carries the date and the language** (issue 13)."""
    return {
        "video": render.video_name(date, lang),
        "text": TEXT(lang),
        "json": MANIFEST(lang),
        "thumbnail": render.thumbnail_name(date, lang),
    }


def assemble(date: str, lang: str) -> metadata_module.Metadata:
    """Finish one edition's package: write both metadata files, JSON last. Returns what was written.

    ⚠️ **The manifest is deleted first, deliberately.** If it were only written at the end, a re-run that failed would
    leave the *previous* run's JSON in place — and the folder would read as a finished package built from facts that
    are no longer the ones on disk. Removing it up front is what makes "the JSON exists" a statement about *this* run.
    """
    directory = render.out_dir(date, lang)
    names = filenames(date, lang)
    manifest = directory / names["json"]

    # 1 — the package is not complete until this succeeds, and it must not look complete until then.
    manifest.unlink(missing_ok=True)

    # 2 — refuse rather than write text about artefacts that are not there. A description claiming a video exists
    #     while nothing plays is worse than no package, because the folder looks finished.
    missing = [
        name
        for key, name in names.items()
        if key in ("video", "thumbnail") and not (directory / name).is_file()
    ]
    if missing:
        raise PackageError(
            f"{lang}: {', '.join(missing)} missing from {directory} — refusing to write metadata for a "
            f"package that would look complete and would not be"
        )

    bundle = store.read_facts(date)
    text = metadata_module.build(
        date,
        bundle,
        lang,
        bundle_hash=bundle_hash(date),
        video=names["video"],
        thumbnail=names["thumbnail"],
    )

    # 3 — the human's file, then the machine's. ⚠️ That order matters: the JSON is the completion marker, so it has to
    #     be the last thing to appear.
    _write(directory / names["text"], text.as_text())
    payload = text.as_json()
    _write(manifest, json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    return text

