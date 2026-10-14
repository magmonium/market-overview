"""The renderer's own catalogue, **read rather than mirrored** (map issues 04 and 05).

The menu must offer exactly what the renderer can draw, and the *renderer* owns that list: the themes, their
names and the four wave forms all live in `remotion/themes.ts`, because that is where they are used.

⚠️ **Mirroring them here would be a second copy of a menu**, which is a different thing from a second copy of a
formatting rule. A mirror of a formatter drifts visibly — a number a human can compare. A mirror of a menu drifts
**invisibly**: a theme added to the renderer and missed in the copy is a theme the operator simply cannot tick,
and nothing anywhere would say so.

⚠️ So this **asks the renderer**. Node strips the types off `themes.ts` and hands the catalogue back as JSON. It
costs a subprocess and it puts node on this module's path — both cheaper than a menu that quietly lies.

⚠️ **It reads its own source tree, not `paths.data_root()`.** Those two are different *ideas*: `paths.data_root()`
is the **data** — the songs and the packages, which a test may point at a temporary directory — while this module
reads the **code** it is part of. Sharing the one seam would mean a test that relocates `resource/reel/song/`
silently disables the menu.
"""
from __future__ import annotations

import dataclasses
import json
import pathlib
import subprocess
from typing import Any

#: ⚠️ The file that **is** the catalogue. Named once, so a rename is a one-line change and a failure can say
#: exactly what it went looking for.
MODULE = "remotion/themes.ts"

TIMEOUT = 60.0

#: The probe. ⚠️ It imports the very module the render layer imports, so "a theme the composition cannot draw"
#: cannot appear in the menu — the disagreement is not *detected*, it is **impossible**.
PROBE = """
import('./{module}').then((module) => {{
  process.stdout.write(JSON.stringify({{
    themes: module.THEMES.map(({{id, name}}) => ({{id, name}})),
    forms: module.FORMS,
  }}));
}});
""".format(module=MODULE)


class CatalogueError(RuntimeError):
    """The catalogue cannot be read, so the menu cannot be offered and nothing is rendered."""


@dataclasses.dataclass(frozen=True)
class Entry:
    """One option the menu offers: the id the record stores, and the name it shows."""

    id: str
    name: str


def where() -> pathlib.Path:
    """The render layer's root — the project tree this module is installed in.

    ⚠️ Deliberately **not** `paths.data_root()`, which is the data a test may relocate, and not `paths.repo_root()`
    either — that is the repository, where `node_modules` live, one level above this project. The renderer's
    catalogue is source, and source does not move because a fixture pointed the data root somewhere else.

    ⚠️ `parents[1]` — the package sits directly in the project, with no `src/` layer (see `paths.project_root`).
    """
    return pathlib.Path(__file__).resolve().parents[1]


def read(root: pathlib.Path | None = None) -> dict[str, Any]:
    """The renderer's catalogue, as it answers."""
    cwd = where() if root is None else root

    try:
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", PROBE],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )
    except FileNotFoundError as exc:
        raise CatalogueError(
            "node is not on PATH, and the catalogue lives in the render layer — there is nothing to offer"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise CatalogueError(f"reading {MODULE} timed out after {TIMEOUT:g}s") from exc

    if completed.returncode != 0:
        tail = (completed.stderr or completed.stdout or "").strip()[-1200:]
        raise CatalogueError(f"could not read {MODULE}: {tail}")

    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise CatalogueError(
            f"{MODULE} answered with something that is not JSON: {completed.stdout[:200]!r}"
        ) from exc


def themes(root: pathlib.Path | None = None) -> tuple[Entry, ...]:
    """The themes the menu offers, in the order the renderer orders them."""
    return tuple(Entry(id=item["id"], name=item["name"]) for item in read(root)["themes"])


def forms(root: pathlib.Path | None = None) -> tuple[str, ...]:
    """The wave forms the menu offers."""
    return tuple(read(root)["forms"])
