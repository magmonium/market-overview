"""0087_04 — the recorded run: what `store/<song>/run.json` holds, and that it survives a round trip.

⚠️ **This file is an interface, not a cache.** It is committed, a human reads it to see what was built, and
the next run replays it instead of asking the menu again. So the test asserts the *documented* shape and the
*legibility* of the file — not merely that Python can re-parse its own structure.
"""
import hashlib
import json
import pathlib
import tempfile
import unittest

from song_video import record

#: A title in Bengali with Latin beside it, because that is the case a naive writer mangles.
TITLE = "দূরে কোথায় (Dure Kothay)"
DIGEST = "a" * 64


class RoundTrip(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.store = pathlib.Path(self._tmp.name) / "store"

    def a_run(self) -> record.Run:
        return record.Run(
            song="dure-kothay",
            title=TITLE,
            lang="bn",
            cover=record.Cover(name="dure-kothay.jpg", sha256=DIGEST, bytes=2048),
            themes=("vinyl", "neon"),
            wave="ribbon",
            fps=30,
            duration_seconds=214.556,
            master=record.Master(name="dure-kothay.mp3", sha256=DIGEST, bytes=5761197),
            toolchain=record.Toolchain(ffprobe="/opt/remotion/ffprobe"),
        )

    def test_a_run_is_written_in_the_documented_shape_and_read_back_unchanged(self):
        run = self.a_run()

        path = record.save(self.store, run)

        self.assertEqual(path, self.store / "dure-kothay" / "run.json")
        self.assertEqual(record.load(self.store, "dure-kothay"), run, "the run must survive its own file")

        text = path.read_text(encoding="utf-8")
        written = json.loads(text)
        self.assertEqual(
            set(written),
            {"song", "title", "artist", "lang", "cover", "themes", "wave", "fps", "duration_seconds", "master",
             "toolchain"},
            "the keys are the documented ones, not whatever the dataclass happens to be called",
        )
        self.assertEqual(set(written["master"]), {"name", "sha256", "bytes"})
        # ⚠️ The artwork is documented exactly as the master is, digest and all: it is part of the delivery, and a
        # different image under the same filename is a different still under the same approved title.
        self.assertEqual(set(written["cover"]), {"name", "sha256", "bytes"})
        self.assertEqual(set(written["toolchain"]), {"ffprobe"})
        self.assertEqual(written["themes"], ["vinyl", "neon"], "a tuple is a list on the wire")
        # ⚠️ Legible rather than `\u09a6...`: this file is read by people, and a title is not an escape code.
        self.assertIn("দূরে", text)


    def test_a_record_written_before_the_toolchain_was_recorded_still_replays(self):
        """⚠️ Provenance is not identity. A record without the toolchain still holds the answers somebody
        approved, and throwing those away to protect a diagnostic would be the wrong trade."""
        path = record.save(self.store, self.a_run())
        document = json.loads(path.read_text(encoding="utf-8"))
        del document["toolchain"]
        path.write_text(json.dumps(document), encoding="utf-8")

        replayed = record.load(self.store, "dure-kothay")

        self.assertEqual(replayed.toolchain, record.Toolchain(ffprobe=""), "an absent provenance is absent")
        self.assertEqual(replayed.title, TITLE, "and the answers survive it")


    def test_a_record_written_before_the_caption_had_a_language_replays_with_an_empty_one(self):
        """⚠️ Empty, not guessed: the language is a *choice*, and `record` has no business making it. The conductor
        fills it from the title's script, which is where that policy belongs."""
        path = record.save(self.store, self.a_run())
        document = json.loads(path.read_text(encoding="utf-8"))
        del document["lang"]
        path.write_text(json.dumps(document), encoding="utf-8")

        replayed = record.load(self.store, "dure-kothay")

        self.assertEqual(replayed.lang, "")
        self.assertEqual(replayed.title, TITLE, "and the answers survive it")


    def test_a_record_written_before_the_artwork_was_recorded_replays_without_it(self):
        """⚠️ `None`, not re-paired by name. The pairing is the folder's *offer*, and the record is the run: a still
        whose artwork was never written down is not a still this record can rebuild. Answering again is one command,
        and the new record names the image — which is why the field is written down rather than re-derived."""
        path = record.save(self.store, self.a_run())
        document = json.loads(path.read_text(encoding="utf-8"))
        del document["cover"]
        path.write_text(json.dumps(document), encoding="utf-8")

        replayed = record.load(self.store, "dure-kothay")

        self.assertIsNone(replayed.cover)
        self.assertEqual(replayed.title, TITLE, "and the answers survive it")

    def test_an_image_is_described_by_its_name_its_size_and_its_digest(self):
        art = pathlib.Path(self._tmp.name) / "man-poreche-preme.png"
        art.write_bytes(b"not-really-a-png")

        described = record.cover_of(art)

        self.assertEqual(described.name, "man-poreche-preme.png")
        self.assertEqual(described.bytes, len(b"not-really-a-png"))
        self.assertEqual(described.sha256, hashlib.sha256(b"not-really-a-png").hexdigest())


if __name__ == "__main__":
    unittest.main()
