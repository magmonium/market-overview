"""The per-date snapshot — `store/<date>/` (see CONTEXT.md).

It holds the raw source responses and the facts bundle, which is what makes the rebuild
promise real: a re-render reads this instead of fetching.

Writes are atomic. A half-written bundle is worse than a missing one, because it looks
complete.
"""
from __future__ import annotations

import json
import os
import pathlib
import tempfile
from typing import Any

FACTS = "facts.json"


def root() -> pathlib.Path:
    """The tool's root — `store/` sits beside `output/`, `resource/` and `src/`."""
    return pathlib.Path(__file__).resolve().parents[2]


def dir_for(date: str) -> pathlib.Path:
    return root() / "store" / date


def write_facts(date: str, bundle: dict[str, Any]) -> pathlib.Path:
    """Write `store/<date>/facts.json` atomically and return its path."""
    target = dir_for(date)
    target.mkdir(parents=True, exist_ok=True)
    path = target / FACTS

    handle, temporary = tempfile.mkstemp(dir=target, prefix=".facts-", suffix=".json")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as fh:
            json.dump(bundle, fh, indent=2, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temporary, path)
    except BaseException:
        pathlib.Path(temporary).unlink(missing_ok=True)
        raise
    return path


def write_raw(date: str, name: str, payload: bytes) -> pathlib.Path:
    """Snapshot a source response verbatim, so a run can be audited and replayed.

    Written before parsing, deliberately: if the parser is what broke, the evidence of
    what it was given must already be on disk.
    """
    target = dir_for(date) / "raw"
    target.mkdir(parents=True, exist_ok=True)
    path = target / name
    handle, temporary = tempfile.mkstemp(dir=target, prefix=".raw-", suffix=".part")
    try:
        with os.fdopen(handle, "wb") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temporary, path)
    except BaseException:
        pathlib.Path(temporary).unlink(missing_ok=True)
        raise
    return path


def read_facts(date: str) -> dict[str, Any]:
    """Read a snapshot back — the entry point for a re-render."""
    return json.loads(dir_for(date).joinpath(FACTS).read_text(encoding="utf-8"))
