"""What a run will build — one job per theme (issues 04 and 07).

⚠️ **N jobs, never N × M.** The wave form is a single choice shared by the whole run, so ticking three themes
costs three renders and never three-times-two. This module is where that promise becomes arithmetic, and the
test that asserts every job carries the same wave form is the thing that keeps it true.

⚠️ **A job carries facts, not decisions.** The theme and the wave form were decided by the operator and are
already in the record; the frame count is *derived* through `master.frames`, so a plan can never disagree with
the probe about how long the piece is.
"""
from __future__ import annotations

import dataclasses

from . import master, record


@dataclasses.dataclass(frozen=True)
class Job:
    """One reel to build: a song, a title, a theme, and the run's single wave form."""

    song: str
    title: str
    theme: str
    wave: str
    fps: int
    duration_seconds: float

    @property
    def frames(self) -> int:
        """The piece's length in frames — the song's own length, through the one ceiling rule."""
        return master.frames(self.duration_seconds, self.fps)


def jobs(run: record.Run) -> list[Job]:
    """The run's jobs, in the **recorded** order.

    ⚠️ Recorded order, not sorted. The operator ticked the themes, and a re-run has to build them in the same
    sequence — otherwise a run that dies halfway leaves a folder whose remaining work cannot be predicted from
    the record alone.
    """
    return [
        Job(
            song=run.song,
            title=run.title,
            theme=theme,
            wave=run.wave,
            fps=run.fps,
            duration_seconds=run.duration_seconds,
        )
        for theme in run.themes
    ]
