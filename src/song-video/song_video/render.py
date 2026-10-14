"""The render step — the subprocess boundary, and the order it is used in (issues 03, 07, 08).

⚠️ **Every thumbnail before any video.** N one-frame stills cost seconds; a theme that reads badly should be seen
and killed before an hour of frames is spent on it. That ordering is the conductor's (`cli`), and this module
exists so that both renders go through **one** place for everything else.

⚠️ **Nothing lands in a package until it is whole.** Remotion's `--overwrite` unlinks its target before writing it,
so rendering straight at `song-reel-….mp4` would let a render that dies at 90% destroy last run's good file. Every
render writes a dot-prefixed sibling and is moved into place only once it exists and passes its own checks — the
brief's lesson, and the reason a failed run leaves the previous package exactly as it was.

⚠️ **The song is heard, not only measured.** The reel has no second audio step: the composition plays the staged
master, and Remotion encodes it once at one pinned bitrate into the video that ships (issue 09). The brief's
`loudnorm`-then-mux pipeline is deliberately absent — the master's level is the artist's, not the pipeline's.
"""
from __future__ import annotations

import dataclasses
import json
import pathlib
from collections.abc import Callable

# ⚠️ **Borrowed from the brief, private names and all, deliberately.** Neither helper is composition-specific:
# `_stream` is what keeps a long render from looking hung *and* what still attaches the reason when it dies, and
# `_browser_flag` encodes a trap this machine already taught once — Remotion's bundled `chrome-headless-shell` dies
# at "Getting composition". A second copy would be a second list of browsers to keep in step, and the copy that
# fell behind would be the one that ran on the operator's machine.
#
# ⚠️ The cost is real and named: a rename in the brief breaks this import. It breaks it **loudly**, at import, in
# the reel's own suite — which is the acceptable half of the trade. The right long-term home is a public name on
# the brief's side; the brief is untouched by decision, so this is the documented price of not repeating it.
from market_overview.render import (  # noqa: PLC2701 - see above
    JPEG_QUALITY,
    MAX_STILL_BYTES,
    RenderError as BriefRenderError,
    _browser_flag,
    _concurrency_flag,
    _stream,
)

from . import caption, package, plan, sound

#: The render layer's entry point, relative to `where()`.
ENTRY = "remotion/index.ts"


def where() -> pathlib.Path:
    """The **render layer's own tree** — the project holding `remotion/index.ts`, and the directory a render runs
    from.

    ⚠️ **Deliberately not `paths.data_root()`, and not `paths.repo_root()` either.** `paths.data_root()` is the
    *data* a test may relocate, for the reason `catalogue.where` gives; `repo_root()` is where the toolchain lives.
    This is the *code* the renderer is made of, and — because `ENTRY` is relative — it is the only thing that makes
    `remotion/index.ts` mean **our** entry. ⚠️ **Both projects have a file by that name.** Run the
    render from the repository and Remotion bundles the *brief's* root, then reports a missing composition and help
    fully lists `MarketBrief, Thumbnail, IndexCard`.

    ⚠️ `parents[1]` — the package sits directly in the project, with no `src/` layer (see `paths.project_root`).
    """
    return pathlib.Path(__file__).resolve().parents[1]

#: ⚠️ **Named, never derived.** The renderer's registry is the other side of a subprocess boundary, so a typo is a
#: failed render rather than an import error — the same reason the brief names its two composition ids.
REEL = "SongReel"
THUMBNAIL = "SongReelThumbnail"

#: ⚠️ **320k, and this is the map's own number rather than a copy of the brief's.** Issue 09 asks for *one pinned
#: **high-bitrate** encode, because the music is the content* — while `market_overview.audio.BITRATE` is 192k, which
#: is tuned for a bed under speech. Reusing it here quietly made the brief's trade-off the song's.
#:
#: ⚠️ **This is the encode, not the master.** Nothing normalises, trims, fades or re-masters the artist's file: the
#: level and the length are theirs (issue 09). The one thing this pipeline owns is the *loss*, and a song is worth
#: more bits than a music bed.
AUDIO_BITRATE = "320k"


class RenderError(RuntimeError):
    """A render failed. ⚠️ **A failed theme fails the run** (issue 07) — never a folder that looks finished with
    two of three videos in it, and never a package half-written."""


@dataclasses.dataclass(frozen=True)
class Stage:
    """What every render in one run needs, and what no render decides for itself."""

    #: The directory the render runs from — the reel's own tree, from `render.where()`. ⚠️ Not the repository:
    #: both projects have a `remotion/index.ts`, so this field decides *which renderer* is invoked.
    root: pathlib.Path
    #: `output/reel/<song>/`, where the packages go.
    output_dir: pathlib.Path
    #: The staged master's filename **inside `public/`** — what the composition fetches.
    staged: str
    #: The staged cover's filename, or `None`. ⚠️ A supported state, not a hole: both the disc and the still are
    #: designed without one (issue 01).
    cover: str | None
    #: The master's **recorded digest**, which is the seed every per-song decision is derived from — the accent the
    #: piece is lit by and the paths its light drifts along. ⚠️ It rides in the props rather than being re-hashed
    #: from the file: the look must follow the *record*, so that a rebuild of an approved run is the same film.
    seed: str
    #: ⚠️ The caption's script — `bn` or `en`, from the record. It travels with the run because it decides both the
    #: **word** the still prints and the **numerals** the duration is written in.
    lang: str
    #: The mark, as `market_overview.logo.load` returned it — inlined, with the chip already decided. `None` when
    #: the operator has not supplied one, which is also a supported state.
    mark: dict | None
    #: A watchdog for each render. `None` means "as long as it takes", which is the honest default for a piece
    #: whose length is the song's.
    timeout: float | None = None


def props(stage: Stage, job: plan.Job) -> dict[str, object]:
    """**The whole input to one render**, and nothing else (issue 03).

    ⚠️ `frames` is Python's measurement, never the renderer's opinion — the composition's length *is*
    `master.frames` over the ffprobe duration, so "the piece is exactly as long as the song" has one
    implementation instead of two that agree today.

    ⚠️ `duration` is the **value** half of the still's caption, formatted here in the script's own numerals; the
    **word** half lives in the render layer's label table. Neither side can invent the other's half.
    """
    return {
        "title": job.title,
        "song": stage.staged,
        "theme": job.theme,
        "cover": stage.cover,
        "frames": job.frames,
        "mark": stage.mark,
        "seed": stage.seed,
        "lang": stage.lang,
        "duration": caption.duration_at(job.duration_seconds, lang=stage.lang),
    }


# ── the two renders ─────────────────────────────────────────────────────────────────────────────────────


def thumbnail(stage: Stage, job: plan.Job) -> pathlib.Path:
    """The still that ships beside the reel — and the run's **first** artefact (issue 08).

    ⚠️ **Its own composition, at `--frame=0`.** The still's camera has no entrance, so frame 0 *is* the settled
    state rather than a frame chosen to be past one — which is what makes this a still rather than a grabbed frame.
    """
    target = package.thumbnail(stage.output_dir, job)
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = target.with_name(f".still-{job.theme}.jpg")
    wrapper = _props_file(target.parent, stage, job, kind="still")

    command = [
        "npx",
        "remotion",
        "still",
        ENTRY,
        THUMBNAIL,
        str(staging),
        f"--props={wrapper}",
        "--frame=0",
        # ⚠️ JPEG at the brief's quality, and the 2 MB ceiling is checked after the render rather than trusted:
        # it is the one line of the spec that a silent regression could break while everything still looked fine.
        "--image-format=jpeg",
        f"--jpeg-quality={JPEG_QUALITY}",
        "--overwrite",
        *_browser_flag(),
        "--log=info",
    ]

    return _produce(
        command,
        stage=stage,
        target=target,
        staging=staging,
        wrapper=wrapper,
        label=f"remotion still ({job.theme})",
        ceiling=MAX_STILL_BYTES,
    )


def video(stage: Stage, job: plan.Job) -> pathlib.Path:
    """One full-length reel, with the song inside it."""
    target = package.reel(stage.output_dir, job)
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = target.with_name(f".reel-{job.theme}.mp4")
    wrapper = _props_file(target.parent, stage, job, kind="reel")

    command = [
        "npx",
        "remotion",
        "render",
        ENTRY,
        REEL,
        str(staging),
        f"--props={wrapper}",
        # ⚠️ **Named rather than defaulted.** Issue 03 pins H.264 in `yuv420p`, and a change in Remotion's defaults
        # is precisely the kind of thing nothing downstream would notice — the file would be a file.
        "--codec=h264",
        "--pixel-format=yuv420p",
        f"--audio-bitrate={AUDIO_BITRATE}",
        "--overwrite",
        *_browser_flag(),
        *_concurrency_flag(),
        "--log=info",
    ]

    return _produce(
        command,
        stage=stage,
        target=target,
        staging=staging,
        wrapper=wrapper,
        label=f"remotion render ({job.theme})",
        # ⚠️ **Measured against the master, which is the staged file itself** — byte-identical to what the operator
        # supplied (`stage.copy` guarantees it, and the guard is why that promise is worth making). The renderer
        # fetches from the render project's `public/`, so that is where the comparison starts.
        guard=lambda made: sound.shortfalls(
            sound.measure(stage.root / "public" / stage.staged), sound.measure(made)
        ),
    )


# ── the shared mechanics ────────────────────────────────────────────────────────────────────────────────


def _props_file(directory: pathlib.Path, stage: Stage, job: plan.Job, *, kind: str) -> pathlib.Path:
    """The file `--props` points at: one flat object, dot-prefixed, and removed by the caller.

    ⚠️ **Beside the target, not in a shared scratch folder.** Two themes render in sequence and each removes its
    own file, so a single name would *happen* to work — the kind of thing that stops working the day someone
    speeds the run up. The theme is in the name for the same reason: this file belongs to one render.

    ⚠️ `ensure_ascii=False`: the title is typed, and a Bengali title in a props file should read as a Bengali
    title. Escapes would be valid JSON and unreadable to the operator who opens it to see what was rendered.
    """
    wrapper = directory / f".props-{kind}-{job.theme}.json"
    wrapper.write_text(json.dumps(props(stage, job), ensure_ascii=False), encoding="utf-8")
    return wrapper


def _produce(
    command: list[str],
    *,
    stage: Stage,
    target: pathlib.Path,
    staging: pathlib.Path,
    wrapper: pathlib.Path,
    label: str,
    ceiling: int | None = None,
    guard: Callable[[pathlib.Path], list[str]] | None = None,
) -> pathlib.Path:
    """Run one render into scratch, check it, and only then move it into place.

    ⚠️ **The order is the whole function.** `--overwrite` unlinks the target, so a render pointed at the package
    file would delete a good artefact before discovering it cannot replace it. Here the package path is untouched
    until a file exists at the staging path *and* passes the checks — which is what makes "a failed theme fails the
    run" cost a run rather than a delivery.

    ⚠️ **`guard` is the audio's check, and it runs before the move for the same reason `ceiling` does.** A reel whose
    track is silent, narrower or cheaper than the master is not a delivery, and finding that out *after* replacing the
    package would mean the run had destroyed the previous good file to discover it (issue 09).
    """
    try:
        _stream(command, cwd=stage.root, timeout=stage.timeout, label=label)
    except BriefRenderError as exc:
        # ⚠️ Translated, not swallowed: the reel's conductor catches one error type, so the message survives and
        # the boundary stays in one place.
        raise RenderError(str(exc)) from exc
    except FileNotFoundError as exc:
        raise RenderError(
            f"{label}: no render toolchain — run it from the repository that holds `node_modules` ({exc})"
        ) from exc
    finally:
        # ⚠️ Removed even on failure: a crashed run must not leave props where a deliverable belongs.
        wrapper.unlink(missing_ok=True)

    try:
        if not staging.exists():
            raise RenderError(f"{label}: remotion reported success and wrote nothing at {staging.name}")
        if ceiling is not None and staging.stat().st_size > ceiling:
            raise RenderError(
                f"{label}: {staging.stat().st_size / 1024 / 1024:.2f} MB is over the {ceiling / 1024 / 1024:.0f} "
                f"MB ceiling — lower JPEG_QUALITY rather than shipping one that will not upload"
            )
        if guard is not None:
            # ⚠️ **The song, checked rather than assumed.** Nothing else in the pipeline ever looks at the audio
            # inside the file it just made: the master is digest-guarded and the still is size-guarded, so a render
            # that dropped the track, halved the rate or re-encoded it cheaply would have shipped a file that is a
            # file. `issue 09` keeps the *level* the artist's; the *loss* is this pipeline's, and so is catching it.
            lost = guard(staging)
            if lost:
                raise RenderError(
                    f"{label}: the delivery lost the song — {'; '.join(lost)}. The audio that reaches the package "
                    f"is this pipeline's own contract (issue 09), so the run stops rather than shipping it"
                )
        staging.replace(target)
    finally:
        staging.unlink(missing_ok=True)
    return target
