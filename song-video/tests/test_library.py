"""0087_01 — `resource/song/` as an interface: what a *song* is.

⚠️ Written before `library.discover` can satisfy it. It replaces nothing: the empty-folder refusal from
`test_cli.py` stays exactly as it was, and this cycle is the tracer bullet for the pairing rule.
"""
import pathlib
import tempfile
import unittest

from song_video import library


class Discovery(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.songs = pathlib.Path(self._tmp.name) / "resource" / "song"
        self.songs.mkdir(parents=True)

    def test_a_master_pairs_with_its_cover_and_a_stray_file_is_not_a_song(self):
        """The folder is the interface: one name, one master, one optional cover — and `code` noise ignored."""
        (self.songs / "dure-kothay.mp3").write_bytes(b"")
        (self.songs / "dure-kothay.jpg").write_bytes(b"")
        (self.songs / ".DS_Store").write_bytes(b"")

        found = library.discover(self.songs)

        self.assertEqual([song.name for song in found], ["dure-kothay"])
        self.assertEqual(found[0].master.name, "dure-kothay.mp3")
        self.assertEqual(found[0].cover.name, "dure-kothay.jpg")


    def test_a_paired_cover_is_not_an_orphan(self):
        (self.songs / "dure-kothay.mp3").write_bytes(b"")
        (self.songs / "dure-kothay.jpg").write_bytes(b"")

        self.assertEqual(library.orphans(self.songs), [])

    def test_an_image_no_master_answers_to_is_reported_rather_than_guessed_at(self):
        """⚠️ The rule is the pair, so a loose image is not a cover — and this is the *diagnosis* of the run that
        drew the theme's motif while the operator's own cover art sat in the folder, beside a master whose name it
        did not share. Naming the file is the whole of the fix: the rule does not change, the silence does."""
        (self.songs / "dure-kothay.mp3").write_bytes(b"")
        (self.songs / "man-poreche-preme.png").write_bytes(b"")
        (self.songs / ".DS_Store").write_bytes(b"")

        self.assertEqual(
            [song.cover for song in library.discover(self.songs)], [None], "not a cover, and never guessed at"
        )
        self.assertEqual([path.name for path in library.orphans(self.songs)], ["man-poreche-preme.png"])

    def test_images_are_the_folders_artwork_in_a_stable_order(self):
        """⚠️ One place decides what an image is — suffix, hidden files, order — so the pairing rule and the
        explicit one can never disagree about which files they are disagreeing about."""
        for name in ("b.png", "a.jpg", "notes.txt", ".DS_Store"):
            (self.songs / name).write_bytes(b"")

        self.assertEqual([path.name for path in library.images(self.songs)], ["a.jpg", "b.png"])

    def test_a_named_image_is_what_cover_at_returns_and_a_path_is_not_a_name(self):
        """⚠️ The explicit half of the pairing rule, and everything `sv build --cover` does: a name in this folder,
        or nothing. A separator makes it a path, and a path is not a name this folder can answer for."""
        (self.songs / "man-poreche-preme.png").write_bytes(b"")
        (self.songs / ".DS_Store").write_bytes(b"")

        self.assertEqual(
            library.cover_at(self.songs, "man-poreche-preme.png"), self.songs / "man-poreche-preme.png"
        )
        self.assertIsNone(library.cover_at(self.songs, "poster.jpg"), "a name that is not there is not a cover")
        self.assertIsNone(library.cover_at(self.songs, ".DS_Store"), "and a hidden file is not an image")
        self.assertIsNone(
            library.cover_at(self.songs, "nested/man-poreche-preme.png"),
            "a separator makes it a path, and this is a name lookup in one folder",
        )


if __name__ == "__main__":
    unittest.main()
