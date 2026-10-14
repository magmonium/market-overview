"""The package — assembly and the completeness marker. (0085_13)

⚠️ **What these tests are really about is the folder a crashed run leaves behind.** "A failed run leaves no package
that looks complete" is the plan's Done-When, and the tempting way to satisfy it — write everything, then delete it on
failure — is the one that does not work, because a process killed mid-write never runs its cleanup. So completeness is
a **file that exists only at the end**, and these tests check that it is absent in every failure mode we can produce.

⚠️ The second thing they are about is that the **files identify themselves**. Issue 13 puts the date and the language
in every filename for a specific reason: a file dragged out of its folder still says what it is, and the loss of that
property is exactly how a Bengali thumbnail is uploaded beside an English video.
"""
import json
import pathlib
import tempfile
import unittest
from unittest import mock

from market_overview import package, paths, render, store

DATE = "2026-10-12"
LANG = "bn"


class Repo(unittest.TestCase):
    """A real temp store, a real bundle, two real artefact files and no renderer."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)

        # ⚠️ The fake repo needs the label tables, because that is where `metadata.labels_for` reads them from — the
        # same place the production root has them. Copied rather than stubbed: the point of the one-glossary rule is
        # that the metadata reads the render layer's *real* tables, so a stub would test the opposite.
        real = pathlib.Path(store.root())  # before the patch below
        (self.root / "remotion").mkdir()
        for name in ("copy.bn.json", "copy.en.json"):
            (self.root / "remotion" / name).write_bytes((real / "remotion" / name).read_bytes())

        # A bundle with just enough in it to exercise the description's optional sections.
        source = json.loads((real / "store" / DATE / store.FACTS).read_text(encoding="utf-8"))
        self.bundle = {key: source[key] for key in ("meta", "indexes", "timeline") if key in source}
        facts = self.root / "store" / DATE
        facts.mkdir(parents=True)
        (facts / store.FACTS).write_bytes(json.dumps(self.bundle, indent=2, sort_keys=True).encode())

        # The two artefacts the renderers own. ⚠️ Written here as bytes, because assembly must not care *how* they
        # were made — only that they are there.
        self.directory = self.root / "output" / "brief" / DATE / LANG
        self.directory.mkdir(parents=True)
        (self.directory / render.video_name(DATE, LANG)).write_bytes(b"a picture with sound")
        (self.directory / render.thumbnail_name(DATE, LANG)).write_bytes(b"a still")

        # ⚠️ **Two seams: the snapshot stays in the repository, the package does not.** `store.root` redirects the
        # committed facts bundle; `paths.data_root` redirects `output/brief/`. Patching one and not the other is
        # how a suite quietly starts reading — and writing — the operator's real delivery folder.
        for patcher in (
            mock.patch.object(store, "root", return_value=self.root),
            mock.patch.object(paths, "data_root", return_value=self.root),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def names(self) -> dict:
        return package.filenames(DATE, LANG)


class Assembly(Repo):
    """The happy path: four artefacts, a manifest that matches, and a hash that moves when the bundle does."""

    def test_every_filename_carries_the_date_and_the_language(self):
        """⚠️ The property whose loss uploads a Bengali thumbnail beside an English video."""
        for kind, name in self.names().items():
            with self.subTest(artefact=kind):
                if kind == "text" or kind == "json":
                    # `metadata-<lang>.txt` / `.json` sit *inside* a dated, language-named folder, so the language is
                    # the part that has to be in the name; the folder carries the date.
                    self.assertIn(LANG, name)
                else:
                    self.assertIn(DATE, name)
                    self.assertIn(LANG, name)

    def test_it_writes_all_four_artefacts(self):
        published = package.assemble(DATE, LANG)
        for kind, name in self.names().items():
            with self.subTest(artefact=kind):
                self.assertTrue((self.directory / name).is_file(), f"{kind} missing")
        self.assertEqual(published.lang, LANG)
        self.assertEqual(published.video, self.names()["video"])
        self.assertEqual(published.thumbnail, self.names()["thumbnail"])

    def test_the_manifest_matches_what_was_returned(self):
        published = package.assemble(DATE, LANG)
        on_disk = json.loads((self.directory / package.MANIFEST(LANG)).read_text(encoding="utf-8"))
        self.assertEqual(on_disk, published.as_json())

    def test_the_bundle_hash_is_the_bundle_s_own_digest(self):
        published = package.assemble(DATE, LANG)
        self.assertEqual(
            published.bundle_hash,
            package.bundle_hash(DATE),
            "the hash must be of the file on disk, so a re-render can prove what it was built from",
        )

    def test_a_changed_bundle_changes_the_hash(self):
        """⚠️ A hash that cannot move is not evidence. The bundle is rewritten and the digest must follow."""
        before = package.bundle_hash(DATE)
        path = self.root / "store" / DATE / store.FACTS
        path.write_bytes(path.read_bytes() + b"\n")
        self.assertNotEqual(package.bundle_hash(DATE), before)


class Completeness(Repo):
    """⚠️ **The plan's Done-When: "a failed run leaves no package that looks complete, tested by killing mid-write."**

    The failure modes below are the ones a real run can actually produce. A kill -9 mid-write cannot be simulated in
    process, but every *reachable* state it leaves behind can: a folder with some of the artefacts, a folder with a
    stale manifest from an earlier run, and a folder whose assembly raised part way through.
    """

    def _incomplete(self, *, drop: str) -> None:
        (self.directory / self.names()[drop]).unlink()

    def test_a_missing_video_refuses(self):
        """⚠️ And the message names the **file**, not the concept: the operator has to go and look at a folder, so
        "video missing" would send them looking for something that is not a filename anywhere in the system."""
        missing = self.names()["video"]
        self._incomplete(drop="video")
        with self.assertRaises(package.PackageError) as caught:
            package.assemble(DATE, LANG)
        self.assertIn(missing, str(caught.exception))
        self.assertIn("would look complete", str(caught.exception))

    def test_a_missing_thumbnail_refuses(self):
        self._incomplete(drop="thumbnail")
        with self.assertRaises(package.PackageError):
            package.assemble(DATE, LANG)

    def test_a_refusal_writes_no_manifest(self):
        """⚠️ **This is the test the Done-When asks for.** The folder keeps its video and thumbnail — the renderers put
        them there and assembly does not delete other people's work — but without the manifest it visibly is not a
        package, and a second run will try again rather than leave this one looking finished."""
        self._incomplete(drop="thumbnail")
        with self.assertRaises(package.PackageError):
            package.assemble(DATE, LANG)
        self.assertFalse((self.directory / package.MANIFEST(LANG)).exists())
        self.assertFalse((self.directory / package.TEXT(LANG)).exists())

    def test_a_stale_manifest_is_removed_before_anything_else_happens(self):
        """⚠️ **The subtle one.** If the manifest were only written at the end, a re-run that *failed* would leave the
        previous run's JSON in place — and the folder would read as a finished package built from facts that are no
        longer the ones on disk. Removing it up front is what makes the file a statement about *this* run."""
        package.assemble(DATE, LANG)
        self.assertTrue((self.directory / package.MANIFEST(LANG)).exists())

        self._incomplete(drop="video")
        with self.assertRaises(package.PackageError):
            package.assemble(DATE, LANG)

        self.assertFalse(
            (self.directory / package.MANIFEST(LANG)).exists(),
            "the previous run's manifest survived a failed re-run, so the folder still reads as complete",
        )

    def test_a_failure_part_way_through_leaves_no_manifest(self):
        """⚠️ Assembly writes the text file first and the JSON last. A crash between the two is the exact window the
        ordering exists to protect, so it is simulated rather than argued about."""
        real_write = package._write
        calls = []

        def failing_write(path, text):
            calls.append(path.name)
            if path.name == package.MANIFEST(LANG):
                raise OSError("the disk went away")
            return real_write(path, text)

        with mock.patch.object(package, "_write", side_effect=failing_write):
            with self.assertRaises(OSError):
                package.assemble(DATE, LANG)

        self.assertEqual(calls, [package.TEXT(LANG), package.MANIFEST(LANG)], "the JSON must be written last")
        self.assertFalse((self.directory / package.MANIFEST(LANG)).exists())

    def test_no_scratch_files_are_left_behind(self):
        """⚠️ The temp file is dot-prefixed and lives *inside* the package folder, so a crash that left one would put
        an unexplained file where a human looks for the day's deliverable."""
        package.assemble(DATE, LANG)
        leftovers = [p.name for p in self.directory.iterdir() if p.name.startswith(".")]
        self.assertEqual(leftovers, [])

    def test_the_metadata_is_readable_by_the_person_who_did_not_run_it(self):
        """⚠️ `mkstemp` creates `0600` and `os.replace` keeps it, so without an explicit chmod the two metadata files
        are owner-only while the video beside them is `0644` — a papercut the day the uploader is someone else."""
        package.assemble(DATE, LANG)
        for name in (package.TEXT(LANG), package.MANIFEST(LANG)):
            with self.subTest(file=name):
                mode = (self.directory / name).stat().st_mode & 0o777
                self.assertEqual(mode, 0o644)

