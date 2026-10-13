"""0087_08 — staging: the song, in the one place a composition can fetch from.

⚠️ **Not a conversion, and not a normalisation "just for staging".** A composition can serve assets only from
the render project's `public/` folder, so the master is **copied** there for the duration of a run — byte for
byte, because the renderer has to hear the master and not a lossy step the pipeline introduced on its way past.

⚠️ And it is the **copy** that is scratch. `resource/` is read and never written ([the master is never
touched](issues/09-the-master-is-never-touched.md)): a pipeline that rewrites its own inputs destroys the thing
it was given, and a "staged" master is exactly how that starts.
"""
import pathlib
import tempfile
import unittest

from song_video import master, stage

from support import write_wav


class Staging(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.where = pathlib.Path(self._tmp.name)
        self.master = self.where / "dure-kothay.wav"
        self.public = self.where / "public"

    def test_the_staged_copy_is_the_master_byte_for_byte_and_the_master_is_untouched(self):
        write_wav(self.master, seconds=1.5)
        before = master.digest(self.master)

        staged = stage.copy(self.master, self.public)

        self.assertEqual(staged, self.public / "dure-kothay.wav")
        self.assertEqual(
            master.digest(staged),
            before,
            "the renderer must hear the master, not a re-encode of it",
        )
        self.assertEqual(master.digest(self.master), before, "the master is never touched")


if __name__ == "__main__":
    unittest.main()
