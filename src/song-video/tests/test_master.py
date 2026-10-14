"""0087_03 — the master's own facts: **how long it is**, and the frame count a run derives from that.

⚠️ **The fixture is written by the standard library, not supplied.** `resource/reel/song/` is operator-supplied
and gitignored, so a test that needed a real master would depend on a file the repository does not have. A
16-bit mono WAV of a known length is a couple of kilobytes and entirely deterministic.

⚠️ **The second case is a real bug class, not padding.** A duration that is *meant* to be a whole number of
frames can arrive as `33.000000000000004`, and a naive ceiling would add a silent frame to the piece.
"""
import pathlib
import tempfile
import unittest

from song_video import master

from support import write_wav


class Duration(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.where = pathlib.Path(self._tmp.name)

    def test_the_probe_derives_frames_by_ceiling_and_never_by_float_noise(self):
        # 1.5 s is exactly 45 frames at 30 fps, and 10.5 at 7 — the ceiling makes it 11.
        exact = master.probe(write_wav(self.where / "exact.wav", seconds=1.5))

        self.assertAlmostEqual(exact.duration_seconds, 1.5, places=3)
        self.assertEqual(exact.frames_at(30), 45)
        self.assertEqual(exact.frames_at(7), 11)
        # ⚠️ The probe records **which ffprobe measured it**. A different build can disagree by a frame, and a
        # rebuild that lands on a different length must be able to say why.
        self.assertTrue(pathlib.Path(exact.toolchain).is_file(), "the probe names the ffprobe it used")

        # 1.1 s × 30 is 33 frames, but `1.1 * 30` is 33.000000000000004 — the answer is still 33.
        noisy = master.probe(write_wav(self.where / "noisy.wav", seconds=1.1, rate=10000))

        self.assertAlmostEqual(noisy.duration_seconds, 1.1, places=3)
        self.assertEqual(noisy.frames_at(30), 33, "float noise must not buy the piece an extra frame")


class Digest(unittest.TestCase):
    """The hash a recorded run guards on: if the master changes, the record describes a different file.

    ⚠️ **The expectation is a literal from `shasum`, not a second `hashlib` call in the test.** A digest has
    exactly one right answer, and a test that recomputed it the way the module does would agree with the
    module even if both hashed the wrong file. `shasum` is a different implementation, so this disagrees
    wherever it should.
    """

    #: 1.5 s of digital silence at 8 kHz, 16-bit mono, as `wave` writes it: 24044 bytes.
    EXPECTED = "e9a21532f6f9019cb9f59a6933ce83554e128b0f995062054d215b22d7dc93a5"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.where = pathlib.Path(self._tmp.name)

    def test_the_digest_identifies_the_file_and_the_probe_records_the_same_one(self):
        path = write_wav(self.where / "master.wav", seconds=1.5)

        self.assertEqual(master.digest(path), self.EXPECTED)
        # The same value, reached through the other entry point: what a run would write down.
        self.assertEqual(master.probe(path).sha256, self.EXPECTED)


if __name__ == "__main__":
    unittest.main()
