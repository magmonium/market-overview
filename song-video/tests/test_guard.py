"""0087_04 — the guard: **a recorded run describes one file.**

⚠️ This is the refusal that protects a rebuild, and it is the whole reason the digest exists. If the master is
swapped — a different take, a remaster, a re-encode — then the recorded title, themes and wave form describe a
video nobody approved, and the honest outcome is to **stop** rather than re-cut silently under the same name.

It is the brief's session-date guard in another costume: *refuse, rather than publish something adjacent to
what was asked for.*
"""
import dataclasses
import pathlib
import tempfile
import unittest

from song_video import master, record

from support import write_wav


class Guard(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.where = pathlib.Path(self._tmp.name)
        self.path = self.where / "dure-kothay.wav"

    def a_record_of(self, path: pathlib.Path) -> record.Run:
        probed = master.probe(path)
        return record.Run(
            song="dure-kothay",
            title="Dure Kothay",
            lang="en",
            cover=None,
            themes=("vinyl",),
            wave="ribbon",
            fps=30,
            duration_seconds=probed.duration_seconds,
            master=record.Master(name=path.name, sha256=probed.sha256, bytes=path.stat().st_size),
            toolchain=record.Toolchain(ffprobe=probed.toolchain),
        )

    def test_a_swapped_master_is_refused_rather_than_recut_under_an_approved_title(self):
        write_wav(self.path, seconds=1.5)
        run = self.a_record_of(self.path)

        # The file is still the file: the guard has nothing to say.
        record.verify(run, master.probe(self.path))

        # A different take, under the same name.
        write_wav(self.path, seconds=2.0)
        with self.assertRaises(record.RecordError) as caught:
            record.verify(run, master.probe(self.path))

        message = str(caught.exception)
        self.assertIn("dure-kothay.wav", message, "the refusal must name the file it is refusing")
        self.assertIn("changed", message, "…and say what changed")

    def test_a_swapped_cover_is_refused_because_a_still_is_a_delivery(self):
        """⚠️ The master's guard, seen through the other input. The artwork in the still is part of what was
        approved, so a different image at the same filename would be drawn under that approval — invisibly, because
        the filename is the one thing a person checks."""
        write_wav(self.path, seconds=1.5)
        art = self.where / "dure-kothay.png"
        art.write_bytes(b"the approved artwork")
        run = dataclasses.replace(self.a_record_of(self.path), cover=record.cover_of(art))

        record.verify_cover(run, art)  # the file is still the file: nothing to say

        art.write_bytes(b"a different poster entirely")
        with self.assertRaises(record.RecordError) as caught:
            record.verify_cover(run, art)

        message = str(caught.exception)
        self.assertIn("dure-kothay.png", message, "the refusal must name the image it is refusing")
        self.assertIn("approved", message, "…and say what the record describes instead")

    def test_a_run_with_no_recorded_cover_has_nothing_to_guard(self):
        """⚠️ No cover is a supported state (the still draws the theme's motif), so there is no image here the guard
        could be right or wrong about."""
        write_wav(self.path, seconds=1.5)
        run = self.a_record_of(self.path)

        record.verify_cover(run, self.where / "absent.png")  # nothing recorded, so nothing to compare


if __name__ == "__main__":
    unittest.main()
