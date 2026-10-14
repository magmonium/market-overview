"""The render step — the subprocess boundary (ticket 09).

⚠️ **Both projects have a `remotion/index.ts`.** The reel's `where()` records what happens if you get this wrong:
*"Run the render from the repository and Remotion bundles the brief's root, then reports a missing composition and
helpfully lists `MarketBrief, Thumbnail, IndexCard`."* So the entry is named relative to **this** project's tree, and
`where()` is the only thing that makes it mean ours.

⚠️ **One bundle, four charts.** The chart rides as an **input prop** — exactly as the brief passes `lang` — rather than
as a second composition or a second bundle.
"""
from __future__ import annotations

import json
import pathlib
import subprocess

from . import paths

#: The render layer's entry point, **relative to `where()`**.
ENTRY = "remotion/index.ts"


class RenderError(RuntimeError):
    """A render failed, or reported success and wrote nothing — ⚠️ **the second is the one worth having a type for.**

    A `remotion render` that exits zero and leaves no file is the failure that would otherwise be discovered at upload
    time, by which point the run has moved on and the scratch file has been cleaned up.
    """

#: The composition the renderer registers for this product.
COMPOSITION = "BooksBrief"

#: ⚠️ **The still's own composition**, at 1280×720 and one frame long (ticket 16). It is a separate composition rather
#: than a frame of the video, because a grabbed frame is composed for *motion* and may be caught half-settled.
THUMBNAIL_COMPOSITION = "BooksThumbnail"


def where() -> pathlib.Path:
    """**This product's own tree** — the project holding `remotion/index.ts`, and the directory a render runs from.

    ⚠️ Deliberately neither `paths.data_root()` — the *data* a test relocates — nor the repository root, where the
    toolchain lives. This is the *code* the renderer is made of.
    """
    return paths.project_root()


def entry() -> pathlib.Path:
    """The entry point, absolute.

    ⚠️ Asserted in the tests against `paths.project_root()` rather than trusted: this is the single line that decides
    whether Remotion bundles this product or the brief, and its failure mode is a missing-composition error that names
    three compositions nobody asked for.
    """
    return where() / ENTRY


def run(argv: list[str]) -> None:
    """Run one render, from `where()` — ⚠️ **the cwd is the tree the relative `ENTRY` means ours in.**

    ⚠️ `check=True`, so a failed render raises rather than leaving the run to continue into a package built around a
    video that was never produced.
    """
    subprocess.run(argv, cwd=where(), check=True)  # noqa: S603 - the argv is built here, not from input


def command(*, chart: str, week: str, output: pathlib.Path) -> list[str]:
    """The argv for one chart's render.

    ⚠️ `ENTRY` is passed **relative**, because the render runs from `where()` — an absolute entry would work from any
    directory and would quietly make the wrong-tree mistake possible again.
    """
    return [
        "npx",
        "remotion",
        "render",
        ENTRY,
        COMPOSITION,
        str(output),
        "--props",
        json.dumps({"chart": chart, "week": week}),
    ]


def still_command(*, chart: str, week: str, output: pathlib.Path) -> list[str]:
    """The argv for one chart's **thumbnail** — `remotion still`, not `render`.

    ⚠️ `--frame=0`, and the still's composition has **no entrance at all** (see `BooksThumbnail`), which is what makes
    frame 0 *the settled state* rather than a frame chosen to be past one. A grabbed frame of the video would be
    caught mid-fade, because the slide's entrance is still running at the moment a thumbnail is most likely to be taken.
    """
    return [
        "npx",
        "remotion",
        "still",
        ENTRY,
        THUMBNAIL_COMPOSITION,
        str(output),
        "--frame=0",
        "--props",
        json.dumps({"chart": chart, "week": week}),
    ]
