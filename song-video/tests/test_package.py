"""0087_07 — the package: what a job's files are called, and where they land.

⚠️ **The assertion that matters is that two themes of one song have different *basenames*.** Everything else here
could be satisfied by a scheme that put the themes in folders and named both files `output.mp4` — and that scheme
breaks the moment one file is moved, sent or uploaded, because the folder is not part of what travels.
"""
import pathlib
import unittest

from song_video import package, plan


def a_job(theme: str) -> plan.Job:
    return plan.Job(
        song="dure-kothay",
        title="Dure Kothay",
        theme=theme,
        wave="ribbon",
        fps=30,
        duration_seconds=214.556,
    )


class Names(unittest.TestCase):
    def test_a_package_holds_the_reel_and_the_thumbnail_it_belongs_to(self):
        out = pathlib.Path("/build/output")
        job = a_job("neon")

        self.assertEqual(package.dir_for(out, job), out / "dure-kothay" / "neon")
        self.assertEqual(
            package.reel(out, job),
            out / "dure-kothay" / "neon" / "song-reel-dure-kothay-neon.mp4",
        )
        self.assertEqual(
            package.thumbnail(out, job),
            out / "dure-kothay" / "neon" / "thumbnail-dure-kothay-neon.jpg",
        )

    def test_two_themes_of_one_song_never_share_a_filename(self):
        out = pathlib.Path("/build/output")
        vinyl, neon = a_job("vinyl"), a_job("neon")

        self.assertNotEqual(package.reel(out, vinyl).name, package.reel(out, neon).name)
        self.assertNotEqual(package.thumbnail(out, vinyl).name, package.thumbnail(out, neon).name)


if __name__ == "__main__":
    unittest.main()
