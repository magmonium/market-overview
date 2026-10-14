"""0087_05 — the plan: one run becomes N jobs, one per theme.

⚠️ **N, never N × M.** The wave form is a *single* choice shared by the whole run, and this is where that stops
being a promise and becomes arithmetic: one job per theme, every job carrying the same wave form. The map's
whole argument for making the wave form single-choice lives in this equality.

⚠️ **The frame count is derived, never declared.** It comes from the recorded duration through the one ceiling
rule in `master`, so the plan cannot disagree with the probe about how long the piece is.
"""
import unittest

from song_video import plan, record

DIGEST = "b" * 64


def a_run(*themes: str) -> record.Run:
    return record.Run(
        song="dure-kothay",
        title="Dure Kothay",
        lang="en",
        cover=None,
        themes=tuple(themes),
        wave="ribbon",
        fps=30,
        duration_seconds=214.556,
        master=record.Master(name="dure-kothay.mp3", sha256=DIGEST, bytes=5761197),
        toolchain=record.Toolchain(ffprobe="/opt/remotion/ffprobe"),
    )


class Jobs(unittest.TestCase):
    def test_one_job_per_theme_sharing_the_single_wave_form(self):
        jobs = plan.jobs(a_run("vinyl", "neon", "parchment"))

        self.assertEqual(
            [job.theme for job in jobs],
            ["vinyl", "neon", "parchment"],
            "the recorded order is the build order",
        )
        self.assertEqual({job.wave for job in jobs}, {"ribbon"}, "one wave form, shared by the run")
        self.assertEqual({job.song for job in jobs}, {"dure-kothay"})
        self.assertEqual({job.title for job in jobs}, {"Dure Kothay"})
        self.assertEqual({job.fps for job in jobs}, {30})
        # ceil(214.556 × 30) = ceil(6436.68) = 6437 — and if this number ever moves, the piece's length moved.
        self.assertEqual({job.frames for job in jobs}, {6437})


if __name__ == "__main__":
    unittest.main()
