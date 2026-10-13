"""The master's own facts — its length, and the frame count a run derives from it (issue 09).

⚠️ **The length is load-bearing here, where it is optional in the brief.** The brief measures its bed to
*check* the mix — "audio present for the full runtime, no drift at the close" — and shrugs if ffprobe is
missing, because a missing measurement costs a printed number rather than the brief. **Here the song's length
*is* the piece's length**, so an unmeasurable master is a **refusal**: the alternative is a video whose
length nobody chose.

⚠️ **The measurement is the brief's own** (`market_overview.audio`), deliberately. `duration()` applies the
loader path that Remotion's `--enable-shared` build needs, and derives ffprobe from the ffmpeg it has already
found — including the operator's `MARKET_OVERVIEW_FFMPEG` override. Re-implementing that is how the silent
abort gets discovered a second time.
"""
from __future__ import annotations

import dataclasses
import hashlib
import math
import pathlib

from market_overview import audio

from . import paths

#: The precision a duration is trusted to. ⚠️ **The ceiling needs it**: 1.1 s at 30 fps is
#: `33.000000000000004`, and a naive `ceil` buys the piece a silent frame that nobody asked for.
MICROSECONDS = 6


def frames(duration_seconds: float, fps: int) -> int:
    """How many frames a piece of this length has — the ceiling rule, stated **once**.

    ⚠️ **Here rather than in either caller.** The probe (`Master.frames_at`) and the plan (`Job.frames`) must
    not be able to disagree about how long the piece is; both come through this function, so there is one
    ceiling and one rounding, not two that happen to match today.
    """
    return math.ceil(round(duration_seconds * fps, MICROSECONDS))


class MasterError(RuntimeError):
    """The supplied song cannot be used, so the run stops rather than making something of the wrong length."""


@dataclasses.dataclass(frozen=True)
class Master:
    """A supplied song, and the facts a run records about it."""

    path: pathlib.Path
    duration_seconds: float
    sha256: str
    #: ⚠️ **Which ffprobe measured it, by path.** Provenance, not a guard: a rebuild on another machine with
    #: another ffprobe is a legitimate rebuild — a *different* take is not. Recording it is what lets a rebuild
    #: say "the length moved because the measurement did" rather than leaving a frame count unexplained.
    toolchain: str

    def frames_at(self, fps: int) -> int:
        """How many frames the piece has at `fps` — the song's length, rounded **up** to a whole frame.

        ⚠️ Rounded up rather than truncated: a song whose final frame is short by a few milliseconds must not
        lose them. The tail is arithmetic, not silence (issue 09).
        """
        return frames(self.duration_seconds, fps)


def digest(path: pathlib.Path, *, chunk: int = 1 << 20) -> str:
    """The master's `sha256`, streamed.

    ⚠️ **This is a guard, not a checksum.** A recorded run describes **one file**, and the digest is how the
    run knows the file it is about to render is still the file somebody approved: a swapped master must
    **refuse**, rather than quietly become a different video under a title somebody signed off (issue 04).

    Streamed in blocks, because a full-length master has no business being read into memory to be hashed.
    """
    accumulator = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(chunk):
            accumulator.update(block)
    return accumulator.hexdigest()


def probe(path: pathlib.Path, *, root: pathlib.Path | None = None, timeout: float = 120.0) -> Master:
    """Measure a master, or refuse.

    `root` is the directory the toolchain is found from — the parent's, where `node_modules` lives. It is a
    parameter so a test can pin it, and it defaults to the repository rather than the nested project, because
    that is where Remotion is installed and the reel does not install a second copy.
    """
    where = paths.repo_root() if root is None else root

    try:
        toolchain = audio.binary(where)
    except audio.AudioError as exc:
        raise MasterError(str(exc)) from exc

    seconds = audio.duration(path, ffmpeg=toolchain, timeout=timeout)
    # ⚠️ `probe_binary` never raises, and its absence is the *same* refusal as an unreadable file: a length nobody
    # can measure is a piece whose length nobody chose. Asking for it here (rather than letting `duration` swallow
    # it) is what makes `Master.toolchain` a fact rather than a hopeful empty string.
    probe = audio.probe_binary(toolchain)
    if seconds is None or probe is None:
        raise MasterError(
            f"cannot measure {path.name}: ffprobe could not read it, or it is not audio this toolchain "
            f"decodes — the length of the piece depends on it, so the run stops here"
        )
    return Master(
        path=path,
        duration_seconds=seconds,
        sha256=digest(path),
        toolchain=str(probe),
    )
