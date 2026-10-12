"""The music bed — read, normalised, never modified. (0085_11)

Issue 11 settled that the bed is **supplied in `resource/` and never fetched**, and that the licence question is
discharged once by the operator rather than managed by the pipeline every day. So there is no sourcing here and no
licence metadata — what is left is purely technical, and it is four decisions:

| Decision | Here |
|---|---|
| Never edit the master | the master is only ever an *input*; the derived bed goes to the run's scratch file |
| One level, every run | `loudnorm` to a fixed LUFS target, so no two days differ in perceived volume |
| Trim with a fade | `atrim` to the run's measured length, then a frame-derived `volume` ramp in and out |
| Reproducible | the whole graph is a pure function of (master, run length) — no clock, no randomness |

⚠️ **The decision lives in Python, not in the renderer** (ADR 0002), and for the same reason as the mark in
`logo.py`: the JS layer's job is to draw what it is told, and a Python decision is reachable from pytest. Loudness
is also the one defect a reviewer cannot see — a bed 6 dB down on Tuesday looks exactly like a bed on Monday.

⚠️ **`resource/` is read, never written.** The operator's file is the master: the licence is theirs, and a
pipeline that normalises its inputs in place destroys the thing it was given.

⚠️ **ffmpeg.** The toolchain is Remotion's own bundled build, found in `node_modules` — so there is **no system
`ffmpeg` prerequisite**, which is the whole reason this is not a documented install step. That build is a
*stripped* one (`--disable-filters` with an allow-list), which constrains what may be used here and is why this
module touches only the filters it was verified to have. `tests/test_audio.py` asserts that allow-list directly,
so a filter this build lacks fails the suite rather than the daily run.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess


# ── the level ─────────────────────────────────────────────────────────────────────────────────────────────

#: ⚠️ **YouTube's own reference level.** YouTube turns *down* anything above about -14 LUFS and does not turn
#: quieter content up — so landing exactly here means the level shipped is the level heard. A lower target (a
#: quieter bed) is a legitimate operator preference; it is one number, and it is this one.
TARGET_LUFS = -14.0

#: -1.5 dBTP leaves headroom for the lossy encode that follows; -1.0 is the usual ceiling, and clipping is the one
#: audio defect that is unrecoverable downstream.
TRUE_PEAK = -1.5
LRA = 11.0

#: Fade durations, in seconds. ⚠️ **Constants, not wall-clock**: a re-render lands on the same ramp. The tail is
#: the longer of the two because the brief ends on the close card — the bed must leave before the music does,
#: rather than be cut off mid-phrase.
FADE_IN = 1.5
FADE_OUT = 4.0

#: Where the bed starts in the master. A constant rather than a measurement: an offset that drifted between runs
#: would move every scene transition with it (issue 11's determinism requirement). Raise it to skip a sting.
OFFSET = 0.0

#: 48 kHz stereo, AAC at 192 kbps. Music only, no voice, so there is headroom to spare.
SAMPLE_RATE = 48000
CHANNELS = 2
BITRATE = "192k"

#: The scratch name, inside the date folder that is the run's own directory. Dot-prefixed so a half-finished run
#: never reads as a delivered package, and removed in a `finally`.
BED_NAME = ".bed.wav"

#: ⚠️ An **order, first match wins**, exactly as `logo.py` does for the mark. A lossless master is preferred,
#: because normalising a lossy file means encoding its artefacts along with its music.
MUSIC_NAMES: tuple[str, ...] = (
    "music.wav",
    "music.flac",
    "music.aiff",
    "music.aif",
    "music.m4a",
    "music.mp3",
    "music.aac",
    "music.ogg",
    "music.opus",
    "music.webm",
)

#: Point at a specific binary — including a full system `ffmpeg`, which has filters this build lacks.
FFMPEG_ENV = "MARKET_OVERVIEW_FFMPEG"

#: ⚠️ The bundled build is `--enable-shared`, so its dylibs sit *beside* the binary and it will not start without
#: being told where they are: run bare it aborts with `Library not loaded: libavdevice.dylib`. That is why the
#: binary is never invoked without an environment built by `binary_env()`.
_SHARED_LIB_PATH = "DYLD_LIBRARY_PATH"

#: The filters and encoders this module is allowed to assume. ⚠️ Remotion's build is `--disable-filters` plus an
#: allow-list, so `afade`, `acrossfade`, `volumedetect` and `astats` are all **absent** — the obvious tools for
#: this job are exactly the ones that are missing. Asserted by the test suite.
REQUIRED_FILTERS: tuple[str, ...] = ("atrim", "asetpts", "loudnorm", "volume", "aformat")
REQUIRED_ENCODERS: tuple[str, ...] = ("aac",)


class AudioError(RuntimeError):
    """The bed cannot be used as supplied, so the run stops rather than shipping silent or wrong-level output."""


def _num(value: float) -> str:
    """`-14.0` → `-14`, `1.5` → `1.5`. Keeps the filtergraph readable and stable in a command log."""
    return f"{value:g}"

# ── the toolchain ─────────────────────────────────────────────────────────────────────────────────────────


def _bundled(root: pathlib.Path) -> pathlib.Path | None:
    """Remotion's own ffmpeg, whichever platform's package this install has.

    ⚠️ Globbed rather than named per-platform, because the package name encodes the architecture
    (`compositor-darwin-arm64`, `compositor-linux-x64-gnu`, …) and hard-coding one would silently stop finding it
    on the next machine.
    """
    for candidate in sorted((root / "node_modules" / "@remotion").glob("compositor-*/ffmpeg*")):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def binary(root: pathlib.Path) -> pathlib.Path:
    """The ffmpeg to use: the operator's, else Remotion's, else whatever is on `PATH`.

    ⚠️ **Bundled before `PATH`**, deliberately. It is the build this module was verified against, and it is the one
    certainly present on a machine that can render at all — preferring it is what removes the system prerequisite
    instead of merely documenting it.
    """
    explicit = os.environ.get(FFMPEG_ENV)
    if explicit:
        path = pathlib.Path(explicit)
        if not path.is_file():
            raise AudioError(f"{FFMPEG_ENV} points at {explicit}, which is not a file")
        return path

    bundled = _bundled(root)
    if bundled is not None:
        return bundled

    found = shutil.which("ffmpeg")
    if found:
        return pathlib.Path(found)

    raise AudioError(
        "no ffmpeg found. Remotion's bundled build was not in node_modules (is `npm install` done?) and there is "
        f"none on PATH — set {FFMPEG_ENV} to a full system ffmpeg."
    )


def binary_env(ffmpeg: pathlib.Path) -> dict[str, str]:
    """The environment a bundled binary needs to start at all.

    ⚠️ **Prepended rather than replaced**: a machine may already need `DYLD_LIBRARY_PATH` for something else, and
    clobbering it would break an unrelated tool for the duration of the run.
    """
    if not ffmpeg.parent.name.startswith("compositor-"):
        return {}
    existing = os.environ.get(_SHARED_LIB_PATH, "")
    value = f"{ffmpeg.parent}{os.pathsep}{existing}" if existing else str(ffmpeg.parent)
    return {_SHARED_LIB_PATH: value}


def _root_of(where: pathlib.Path) -> pathlib.Path:
    """Walk up until a directory holds `node_modules` — the root the toolchain is found from.

    ⚠️ Returns `where` unchanged when there is none, which is the **normal** case under pytest: a tmp directory has
    no `node_modules`, so `binary()` falls through to a system ffmpeg, or raises its own clear error. Searching is a
    convenience for the real call sites, not a requirement they depend on.
    """
    start = where if where.is_dir() else where.parent
    for candidate in (start, *start.parents):
        if (candidate / "node_modules").is_dir():
            return candidate
    return start


def run(ffmpeg: pathlib.Path, args: list[str], *, timeout: float | None = None) -> str:
    """Invoke ffmpeg, or raise `AudioError` with its own reason attached.

    ⚠️ `-loglevel error` and the stderr tail both survive, because ffmpeg's failure text is the only description of
    *why* a filtergraph was rejected — and a bare non-zero exit is not something anyone can act on.
    """
    env = dict(os.environ)
    env.update(binary_env(ffmpeg))
    try:
        completed = subprocess.run(
            [str(ffmpeg), "-hide_banner", "-loglevel", "error", *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except FileNotFoundError as exc:
        raise AudioError(f"ffmpeg toolchain missing: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise AudioError(f"ffmpeg timed out after {timeout}s") from exc
    if completed.returncode != 0:
        tail = (completed.stderr or completed.stdout or "").strip()[-1200:]
        raise AudioError(f"ffmpeg failed ({completed.returncode}): {tail}")
    return completed.stdout or ""



# ── measuring ────────────────────────────────────────────────────────────────────────────────────────────


def probe_binary(ffmpeg: pathlib.Path) -> pathlib.Path | None:
    """ffprobe's sibling of `ffmpeg`, or the one on `PATH`.

    ⚠️ Returns `None` rather than raising. A missing ffprobe costs *measurement*, not the bed: the render still
    gets its music and only the numbers that would have been printed are absent, so failing the run over it would
    be the wrong trade.
    """
    sibling = ffmpeg.with_name(f"ffprobe{ffmpeg.suffix}")
    if sibling.is_file() and os.access(sibling, os.X_OK):
        return sibling
    found = shutil.which("ffprobe")
    return pathlib.Path(found) if found else None


def duration(path: pathlib.Path, *, ffmpeg: pathlib.Path | None = None, timeout: float = 120.0) -> float | None:
    """A media file's duration in seconds, or `None` when it cannot be measured.

    ⚠️ This is how "audio present for the full runtime, no drift at the close" (0085_11) is *checked* rather than
    asserted: the trimmed bed's measured length is compared against the run's own. A `-shortest` mux would happily
    absorb a bed that was a second short, and the result would be a brief whose music stops before the close card.
    """
    if ffmpeg is None:
        return None
    probe = probe_binary(ffmpeg)
    if probe is None:
        return None
    env = dict(os.environ)
    env.update(binary_env(ffmpeg))
    try:
        completed = subprocess.run(
            [
                str(probe),
                "-hide_banner",
                "-loglevel",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    try:
        return float(json.loads(completed.stdout)["format"]["duration"])
    except (KeyError, TypeError, ValueError):
        return None


# ── the filtergraph ──────────────────────────────────────────────────────────────────────────────────────


def fade_expression(seconds: float) -> str:
    """The in and out ramp, as a function of time on the *trimmed* bed.

    ⚠️ **`eval=frame` is load-bearing.** `volume` defaults to `eval=once`, which evaluates the expression before
    any frame exists — `t` is undefined, the result is `NaN`, and ffmpeg fails with `Invalid value NaN for volume`.
    The failure is at least loud, but the fix is not guessable from the message.

    ⚠️ **The run length is interpolated as a literal.** The obvious `(duration-t)` does not work: `duration` is not
    in the expression's variable set (`Undefined constant or missing '('`). The bed's length is known before the
    graph is built, so it is written in.

    ⚠️ Commas inside the expression are escaped (`\\,`), because an unescaped comma is a *filter separator* and the
    graph parses to something else entirely.
    """
    finite = _num(seconds)
    return (
        f"volume=eval=frame:volume=min(1\\,min(t/{_num(FADE_IN)}\\,({finite}-t)/{_num(FADE_OUT)}))"
    )


def filtergraph(seconds: float) -> str:
    """Trim → level → fade → the output format, in that order, and the order matters.

    ⚠️ **`loudnorm` before the fade.** Normalising after would measure the fades as part of the programme and raise
    the level to compensate — so the bed would get progressively louder as the fades were made longer. The -14
    target is the level of the *bed*, and the fades are applied to it.

    ⚠️ **`atrim` first.** The fade-out is anchored to the end of the *run*, not the end of the master, so the trim
    has to happen before the ramp is evaluated. `asetpts` resets the timestamps the trim leaves behind, without
    which `t` does not start from zero and the fade-in lands nowhere.

    ⚠️ **`end` is `OFFSET + seconds`, not `seconds`.** `atrim` keeps `[start, end)`, so the segment it yields is
    `end - start` long — writing `end=seconds` gives a bed short by exactly `OFFSET`. It is invisible while
    `OFFSET` is 0, which is precisely what makes it the kind of bug that survives every test until an operator
    changes the other constant.
    """
    return ",".join(
        (
            f"atrim=start={_num(OFFSET)}:end={_num(OFFSET + seconds)}",
            "asetpts=PTS-STARTPTS",
            f"loudnorm=I={_num(TARGET_LUFS)}:TP={_num(TRUE_PEAK)}:LRA={_num(LRA)}",
            fade_expression(seconds),
            f"aformat=sample_rates={SAMPLE_RATE}:channel_layouts={'stereo' if CHANNELS == 2 else 'mono'}",
        )
    )



# ── the asset ────────────────────────────────────────────────────────────────────────────────────────────


def find(resource: pathlib.Path) -> pathlib.Path | None:
    """The supplied bed. `None` when the operator has not dropped one yet.

    ⚠️ `None` is a **supported** state, not an error — the same contract as the mark in `logo.py`. The brief is
    silent-with-music, and "no music supplied yet" is how it looks before the operator acts; refusing to build
    would make the pipeline unusable until an asset arrived.
    """
    for name in MUSIC_NAMES:
        candidate = resource / name
        if candidate.is_file():
            return candidate
    return None


def prepared_path(date_dir: pathlib.Path) -> pathlib.Path:
    """Where this run's derived bed lives — beside the language folders, never inside one.

    ⚠️ **One file for both editions**, above `bn/` and `en/`. "Both editions carry the same bed" then holds by
    construction: there is one file, so there is nothing for the two editions to disagree about. Normalising per
    edition would make it a hope.
    """
    return date_dir / BED_NAME


def prepare(
    date: pathlib.Path,
    seconds: float,
    *,
    root: pathlib.Path,
    resource: pathlib.Path | None = None,
    timeout: float | None = None,
) -> tuple[pathlib.Path, str] | None:
    """Normalise the supplied bed for this run, or `None` if none was supplied.

    `date` is the run's own directory (`output/<date>/`), `root` is the repository — the one that holds
    `node_modules`, and so the toolchain.

    Returns the derived bed's path and a one-line report. ⚠️ The **master is never written**: it is passed to
    ffmpeg as an input, and the derived audio lands in the run's own directory.
    """
    supplied = resource if resource is not None else root / "resource"
    master = find(supplied)
    if master is None:
        return None
    if seconds <= 0:
        raise AudioError(f"the run has no length ({seconds}s), so there is nothing to fit the bed to")

    ffmpeg = binary(root)
    out = prepared_path(date)
    out.parent.mkdir(parents=True, exist_ok=True)

    # ⚠️ The bed is **looped** when the master is shorter than the run. `atrim` alone would leave the tail silent —
    # a brief whose music stops a minute before the close card, which is precisely the "drift at the close" 0085_11
    # asks to rule out. `-stream_loop` is an *input* option, so it needs none of the filters this build lacks
    # (`aloop` and `acrossfade` are both absent from the allow-list).
    #
    # ⚠️ A whole number of repeats, computed, not `-1` (loop forever and rely on the trim to stop it): a bounded
    # input is the weaker assumption, and the count is derivable from the two durations.
    source_seconds = duration(master, ffmpeg=ffmpeg)
    loops: int | None = None
    if source_seconds is not None and source_seconds > 0:
        loops = max(1, int(-(-(seconds + OFFSET) // source_seconds))) if source_seconds < seconds + OFFSET else 1

    args: list[str] = []
    if loops is not None and loops > 1:
        args += ["-stream_loop", str(loops - 1)]
    args += [
        "-i",
        str(master),
        "-af",
        filtergraph(seconds),
        "-c:a",
        "pcm_s16le",
        # ⚠️ A **WAV** intermediate, not AAC. Two reasons: the `.m4a` extension resolves to the `ipod` muxer, which
        # this build does not enable (`unable to choose an output format`), and a lossless intermediate means the
        # music is encoded to AAC exactly once — at the mux, not twice.
        #
        # ⚠️ `-f wav` explicitly, for the same reason the mux names `-f mp4`: the format should come from the
        # command, not from a filename that a future rename could change.
        "-f",
        "wav",
        "-y",
        str(out),
    ]
    run(ffmpeg, args, timeout=timeout)

    measured = duration(out, ffmpeg=ffmpeg)
    # ⚠️ Measured, not assumed. A trim that silently produced 90 s of a 175 s run would otherwise reach the mux,
    # `-shortest` would absorb it, and the brief would ship with its music ending halfway through.
    if measured is not None and abs(measured - seconds) > 1.0:
        raise AudioError(
            f"the normalised bed measures {measured:.2f}s against a {seconds:.2f}s run — refusing rather than "
            f"muxing a bed that does not cover the brief"
        )

    looped = f", looped x{loops}" if loops and loops > 1 else ""
    report = (
        f"music: {master.name} → {out.name} "
        f"({_num(TARGET_LUFS)} LUFS, {_num(seconds)}s, fade {_num(FADE_IN)}/{_num(FADE_OUT)}s{looped})"
    )
    return out, report


def mux(
    video: pathlib.Path,
    bed: pathlib.Path,
    out: pathlib.Path | None = None,
    *,
    root: pathlib.Path | None = None,
    timeout: float | None = None,
) -> pathlib.Path:
    """Put the bed on the rendered video, and never re-encode the picture.

    ⚠️ `-c:v copy`: the rendered frames are the expensive artefact, and re-encoding them to add audio would degrade
    every one of them for a container change. The picture that lands in the package is bit-for-bit the picture the
    renderer produced — which is what keeps 0085_11 additive, rather than a re-render of everything.

    ⚠️ `+faststart` moves the moov atom to the front, which is what lets YouTube start processing an upload before
    it has finished arriving.

    ⚠️ The output is written to a sibling and moved into place, so the named package file is never observable as a
    half-written one. `out` defaults to replacing `video` in place.

    `root` locates the toolchain; when omitted it is walked up from the output, so the common call needs only the
    two paths it already has.
    """
    destination = out if out is not None else video
    ffmpeg = binary(root if root is not None else _root_of(destination))
    # ⚠️ The staging suffix must not be the thing that names the format. ffmpeg infers the muxer from the output
    # **extension**, and a staging file called `x.mp4.muxing` has none it recognises — so leaving the format
    # implicit makes every mux fail with `Unable to choose an output format`. `-f mp4` is what makes the temp name
    # free to be a temp name.
    staging = destination.with_name(destination.name + ".muxing")
    try:
        run(
            ffmpeg,
            [
                "-i",
                str(video),
                "-i",
                str(bed),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                BITRATE,
                "-shortest",
                "-movflags",
                "+faststart",
                "-f",
                "mp4",
                "-y",
                str(staging),
            ],
            timeout=timeout,
        )
        staging.replace(destination)
    finally:
        staging.unlink(missing_ok=True)
    return destination

