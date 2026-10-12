"""Invoke the render layer.

Python conducts and the JS layer only renders (ADR 0002), so the subprocess boundary
lives here: the entry point, the composition id, the props file and the output path.

The renderer never fetches. `--props` takes a *file*, which is exactly what makes a
re-render from `store/<date>/` a guaranteed match (ADR 0003) — and what makes it
checkable that nothing in the JS layer reaches the network.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess

from . import audio, logo, store, timeline

ENTRY = "remotion/index.ts"
COMPOSITION = "MarketBrief"

#: 0085_12's still, its own composition at 1280×720. Named here rather than derived, because the renderer's
#: registry is the other side of a subprocess boundary — a typo would be a failed render, not an import error.
STILL_COMPOSITION = "Thumbnail"

#: ⚠️ Issue 14's spec: JPEG at quality ~88. The platform re-encodes anyway, so the limit is bytes rather than
#: fidelity, and JPEG over PNG is the choice that respects that.
JPEG_QUALITY = 88

#: YouTube's own ceiling on a thumbnail. Checked after the render rather than trusted, because it is the one
#: constraint in the spec that a silent regression could break without anything else looking wrong.
MAX_STILL_BYTES = 2 * 1024 * 1024

#: Operator-supplied licensed assets — read, never written. See `resource/README.md`.
RESOURCE = "resource"

BROWSER_ENV = "MARKET_OVERVIEW_BROWSER"

# ⚠️ Remotion's bundled `chrome-headless-shell` is a *stripped* build, and on this machine
# it SIGABRTs: `Received signal 6` from logging::LogMessageFatal via mojo/IPC
# `OnPipeError`, at "Getting composition", BEFORE a single frame — identically under the
# default GL, `--gl=swangle` and `--gl=swiftshader`, so it is not the rendering path, and
# there is no `--disable-multiprocess` flag to reach for. Pointing Remotion at a full
# Chrome renders the same composition without complaint. So a full browser is named
# explicitly rather than trusting the default.
DEFAULT_BROWSERS: tuple[str, ...] = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)


def _browser_flag() -> list[str]:
    """`--browser-executable=…`, or nothing, falling back to Remotion's own browser.

    `MARKET_OVERVIEW_BROWSER=/path/to/chrome` overrides — which also makes it possible to
    test the bundled shell deliberately rather than by accident.
    """
    explicit = os.environ.get(BROWSER_ENV)
    if explicit:
        return [f"--browser-executable={explicit}"]
    for candidate in DEFAULT_BROWSERS:
        if pathlib.Path(candidate).exists():
            return [f"--browser-executable={candidate}"]
    return []


def _write_props(
    directory: pathlib.Path, lang: str, bundle: dict, mark: object, *, kind: str = ""
) -> pathlib.Path:
    """The wrapper props file `--props` points at: the bundle verbatim, plus what rides beside it.

    ⚠️ The language and the mark ride **beside** the bundle, never inside it. Both editions must read the identical
    facts file, or they could disagree about a number — which is exactly the drift ticket 20 makes structurally
    impossible by keeping the bundle language-neutral. Neither the language nor the mark is a fact.

    ⚠️ Dot-prefixed and removed by the caller, so a crashed run cannot leave a stray JSON file where the day's
    deliverable belongs. Both the video and the still go through here, so there is one place for that to be right.

    ⚠️ `kind` keeps the video's and the still's wrappers from sharing a name. They are written sequentially and each
    removes its own, so sharing would happen to work — which is the kind of thing that stops working the day someone
    speeds the run up by rendering in parallel.
    """
    wrapper = directory / f".props-{kind}{lang}.json"
    wrapper.write_text(
        json.dumps({"bundle": bundle, "lang": lang, "mark": mark}),
        encoding="utf-8",
    )
    return wrapper


class RenderError(RuntimeError):
    """The render layer failed. A failed edition fails the run."""


class _Unprepared:
    """The sentinel meaning *nobody has told me which bed to use* — distinct from `None`, which means *no music*.

    ⚠️ This distinction is the whole reason for the sentinel. `bed=None` is a deliberate choice — the operator has
    supplied no `music.*`, so the brief is silent, which is a supported state. A default of `bed=None` would make
    "the conductor forgot to prepare the bed" indistinguishable from that choice, and the failure mode is a
    silently silent brief: the one defect nobody notices until it is published.
    """

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "audio.UNPREPARED"


UNPREPARED = _Unprepared()


def run_seconds(bundle: dict) -> float:
    """The length of the brief this bundle produces — the number the bed is trimmed to."""
    return timeline.total_seconds(timeline.running_order(bundle))


def date_dir(date: str) -> pathlib.Path:
    """The run's own directory, `output/<date>/` — one level above the language folders.

    ⚠️ It is the run's, not an edition's: the derived bed lives here so that "both editions carry the same bed"
    holds by construction — there is one file, so there is nothing for the editions to disagree about.
    """
    return store.root() / "output" / date


def out_dir(date: str, lang: str) -> pathlib.Path:
    return date_dir(date) / lang


def video_name(date: str, lang: str) -> str:
    """Date and language ride in the filename, so a package is self-describing."""
    return f"market-brief-{date}-{lang}.mp4"


def video_path(date: str, lang: str) -> pathlib.Path:
    return out_dir(date, lang) / video_name(date, lang)


def thumbnail_name(date: str, lang: str) -> str:
    """⚠️ The date and language ride in the filename here too (issue 13).

    A file dragged out of its folder still identifies itself — and the loss of that property is exactly how an
    English thumbnail gets uploaded beside a Bengali video, which is the mistake issue 13 names.
    """
    return f"thumbnail-{date}-{lang}.jpg"


def thumbnail_path(date: str, lang: str) -> pathlib.Path:
    return out_dir(date, lang) / thumbnail_name(date, lang)


def render(
    date: str,
    lang: str,
    *,
    bed: pathlib.Path | None | _Unprepared = UNPREPARED,
    timeout: float | None = None,
) -> pathlib.Path:
    """Render one edition to `output/<date>/<lang>/`, music and all. Returns the video's path.

    `bed` is the run's already-normalised music. ⚠️ **`UNPREPARED` (the default) is not `None`**: it means *work it
    out* — this call prepares its own bed, so a direct call still gets music when the operator has supplied some.
    Passing `None` explicitly is a deliberate silent brief. The distinction exists because the conductor prepares
    the bed **once for the run** (0085_11: both editions carry the same bed), and forgetting to pass it should not
    quietly produce a silent video.

    ⚠️ The bed is prepared **before** the render, like the mark. A refusal that arrives after a multi-minute render
    is a multi-minute wait to learn that nothing was ever going to work.
    """
    props = store.dir_for(date) / store.FACTS
    if not props.exists():
        raise RenderError(f"no facts bundle at {props} — build the bundle before rendering")

    target = video_path(date, lang)
    target.parent.mkdir(parents=True, exist_ok=True)

    root = store.root()
    bundle = json.loads(props.read_text(encoding="utf-8"))

    if isinstance(bed, _Unprepared):
        prepared = audio.prepare(target.parent.parent, run_seconds(bundle), root=root)
        bed = prepared[0] if prepared is not None else None

    # ⚠️ The mark is loaded **before** the render rather than during it. An unusable asset is a refusal, and a
    # refusal that arrives after a multi-minute render is a multi-minute wait to learn that nothing was ever
    # going to work. `logo.LogoError` propagates: the CLI reports it as a refusal, not as a crash.
    mark = logo.load(root / RESOURCE)

    # ⚠️ The language rides **beside** the bundle, never inside it. Both editions must read the
    # identical facts file, or they could disagree about a number — which is exactly the drift
    # ticket 20 makes structurally impossible by keeping the bundle language-neutral. So the renderer
    # gets a small wrapper props file carrying the bundle verbatim, plus the language beside it.
    #
    # The mark rides beside it too, and for the same reason: it is not a fact, and it is identical in both
    # editions — which is what keeps the bilingual pair honest at the branding layer (issue 21).
    wrapper = _write_props(target.parent, lang, bundle, mark)

    # ⚠️ The render **always** goes to a dot-prefixed sibling, and `output/<date>/<lang>/market-brief-*.mp4` is only
    # ever written at the end. Two reasons, and the second is why this is not conditional on there being a bed:
    #
    # 1. A crash mid-render cannot leave a silent video where the package file is expected — indistinguishable from
    #    a finished one, and uploadable.
    # 2. ⚠️ **Remotion's `--overwrite` unlinks the output file before it starts.** Rendering straight to the target
    #    means a render that dies (or is killed) leaves the package *empty*, destroying a delivery that was already
    #    good. Found the hard way: a long render was interrupted and `output/2026-10-12/bn/` was left with nothing
    #    in it. Staging makes the previous delivery survive a failed re-render, which is what "a run either produces
    #    a complete pair, or produces nothing" has to mean in practice.
    silent = target.with_name(f".silent-{lang}.mp4")

    command = [
        "npx",
        "remotion",
        "render",
        ENTRY,
        COMPOSITION,
        str(silent),
        f"--props={wrapper}",
        "--overwrite",
        *_browser_flag(),
        # ⚠️ `verbose`, not `error`: a long render that dies with `--log=error` takes its reason with
        # it, because the buffer is discarded on death. Learned the hard way on 0085_06.
        "--log=verbose",
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise RenderError(f"render toolchain missing: {exc}") from exc
    finally:
        wrapper.unlink(missing_ok=True)

    try:
        if completed.returncode != 0:
            tail = (completed.stderr or completed.stdout or "")[-2000:]
            raise RenderError(f"remotion render failed ({completed.returncode}):\n{tail}")
        if not silent.exists():
            raise RenderError(f"remotion reported success but wrote no file at {silent}")

        if bed is not None:
            # ⚠️ `audio.AudioError` propagates as a refusal, like `LogoError`: an unmuxable bed is something the
            # operator can fix, and the reason ffmpeg gives is the only description of what to fix.
            audio.mux(silent, bed, target, root=root)
        else:
            silent.replace(target)
    finally:
        silent.unlink(missing_ok=True)
    return target


def still(date: str, lang: str, *, timeout: float | None = None) -> pathlib.Path:
    """Render one edition's thumbnail to `output/<date>/<lang>/`. Returns the image's path.

    ⚠️ **`remotion still`, not a frame grabbed from the video** (issue 14). A grabbed frame is composed for motion —
    mid-move, possibly half-faded — and the class of arbitrary outcome the pipeline is built to avoid. The still is
    its own composition, reusing the same world, and its camera has no entrance at all, so `--frame=0` **is** the
    settled state rather than a frame chosen to be past one.

    ⚠️ The output is staged and moved into place for the same reason the video's is: `--overwrite` unlinks the
    target, so rendering straight at the package file would make a failed still destroy last run's thumbnail.
    """
    props = store.dir_for(date) / store.FACTS
    if not props.exists():
        raise RenderError(f"no facts bundle at {props} — build the bundle before rendering")

    target = thumbnail_path(date, lang)
    target.parent.mkdir(parents=True, exist_ok=True)

    root = store.root()
    bundle = json.loads(props.read_text(encoding="utf-8"))
    # ⚠️ Loaded before the render, like the video's: an unusable mark is a refusal, and a refusal that arrives after
    # a render is a wait to learn that nothing was ever going to work.
    mark = logo.load(root / RESOURCE)
    wrapper = _write_props(target.parent, lang, bundle, mark, kind="still-")

    staging = target.with_name(f".still-{lang}.jpg")
    command = [
        "npx",
        "remotion",
        "still",
        ENTRY,
        STILL_COMPOSITION,
        str(staging),
        f"--props={wrapper}",
        # ⚠️ One frame, and frame 0 at that: the still's station has `from === to` and a zero settle, so there is no
        # entrance to be caught in. See `THUMBNAIL` in remotion/world/stations.tsx.
        "--frame=0",
        "--image-format=jpeg",
        f"--jpeg-quality={JPEG_QUALITY}",
        "--overwrite",
        *_browser_flag(),
        "--log=verbose",
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise RenderError(f"render toolchain missing: {exc}") from exc
    finally:
        wrapper.unlink(missing_ok=True)

    try:
        if completed.returncode != 0:
            tail = (completed.stderr or completed.stdout or "")[-2000:]
            raise RenderError(f"remotion still failed ({completed.returncode}):\n{tail}")
        if not staging.exists():
            raise RenderError(f"remotion reported success but wrote no image at {staging}")

        # ⚠️ Measured, not assumed. The 2 MB ceiling is YouTube's, and it is the one line of issue 14's spec that
        # nothing else in the pipeline would notice being broken — a thumbnail at 3 MB looks completely fine.
        size = staging.stat().st_size
        if size > MAX_STILL_BYTES:
            raise RenderError(
                f"the thumbnail is {size / 1024 / 1024:.2f} MB, over YouTube's 2 MB ceiling — "
                f"lower JPEG_QUALITY rather than shipping one that will not upload"
            )
        staging.replace(target)
    finally:
        staging.unlink(missing_ok=True)
    return target

