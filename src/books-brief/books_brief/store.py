"""The per-week snapshot — `store/<week>/` (tickets 09 and 10).

It holds the raw source responses and the facts bundle, which is what makes the rebuild promise real: a re-render
reads this instead of fetching (ADR 0003).

⚠️ **This is the one folder that stays in the project.** `output/` and `resource/` are *data* and live outside the
repository under `paths.data_root()`; this is *evidence*, it is committed, and `root()` below therefore means the
project — the folder holding `books_brief/`, `remotion/` and `tests/`.

⚠️ **The key is the ISO week** (ticket 10) — `2026-W41` — not a date. A weekly product's snapshot is weekly, and the
ISO week is zero-padded so it sorts as a string and needs no state to derive.

Writes are atomic. A half-written bundle is worse than a missing one, because it looks complete.
"""
from __future__ import annotations

import json
import os
import pathlib
import tempfile
from typing import Any

from . import paths

FACTS = "facts.json"

#: ⚠️ The folder holding the source responses **verbatim** (ticket 18). Beside the bundle, and committed for the same
#: reason: it is evidence, not data.
RAW = "raw"


def root() -> pathlib.Path:
    """The product's own root — `store/` sits beside `books_brief/` and `remotion/`."""
    return paths.project_root()


def dir_for(week: str) -> pathlib.Path:
    """`store/<week>/` — one ISO week, e.g. `2026-W41`."""
    return root() / "store" / week


def write_facts(week: str, bundle: dict[str, Any]) -> pathlib.Path:
    """Write `store/<week>/facts.json` **atomically** and return its path.

    ⚠️ **Atomic, because a half-written bundle is worse than a missing one** — it *looks* complete, so a replay would
    read it and render a chart from a truncated file. The temporary file is a dot-prefixed sibling, so a crash mid-write
    leaves the previous week's snapshot exactly as it was.
    """
    target = dir_for(week)
    target.mkdir(parents=True, exist_ok=True)
    path = target / FACTS

    handle, temporary = tempfile.mkstemp(dir=target, prefix=".facts-", suffix=".json")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(bundle, stream, indent=2, sort_keys=True, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        pathlib.Path(temporary).unlink(missing_ok=True)
        raise
    return path


def read_facts(week: str) -> dict[str, Any]:
    """Read a snapshot back — **the entry point for a re-render**, and the reason a week need not be re-fetched."""
    return json.loads(dir_for(week).joinpath(FACTS).read_text(encoding="utf-8"))


def raw_dir(week: str) -> pathlib.Path:
    """`store/<week>/raw/` — the source responses, verbatim (ticket 18)."""
    return dir_for(week) / RAW


def write_raw(week: str, name: str, payload: bytes) -> pathlib.Path:
    """Write one source response **verbatim, before it is parsed** — and the ordering is the whole point.

    ⚠️ The brief's rule, quoted in ticket 18: *"the raw response is snapshotted even when parsing fails — at that point
    the evidence of what was actually received is exactly what is needed."* A response written *after* a successful
    parse is a response the parser already vouched for, so it can never show what the parser was **given** on the day
    the parser was what broke.

    ⚠️ **Bytes, not a decoded object.** `json.loads` followed by `json.dump` would reorder keys, re-escape non-ASCII
    titles and drop any field the parser's model does not carry — so a snapshot written that way is *a* JSON file and
    not *the* response, and it cannot settle an argument about what the vendor said.

    ⚠️ **Atomic**, for the same reason the bundle is: a half-written response is worse than a missing one, because it
    looks complete — and a later run would read it back as evidence.
    """
    target = raw_dir(week)
    target.mkdir(parents=True, exist_ok=True)
    path = target / name

    handle, temporary = tempfile.mkstemp(dir=target, prefix=".raw-", suffix=".part")
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        pathlib.Path(temporary).unlink(missing_ok=True)
        raise
    return path

