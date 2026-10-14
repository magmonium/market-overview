"""Ticket 13's package — assembly, and **the file that says the folder is finished.**

⚠️ **What these tests are really about is the folder a crashed run leaves behind.** The tempting way to satisfy *"a
failed run leaves no package that looks complete"* — write everything, then delete it on failure — is the one that does
not work, because a process killed mid-write never runs its cleanup. So completeness is a **file that exists only at
the end**, and these tests check it is absent in every failure mode that can be produced.

⚠️ The second thing they are about is that **the files identify themselves**: the video and the thumbnail carry the week
*and* the chart, so a file dragged out of its folder still says what it is — the property whose loss uploads a Bengali
thumbnail beside a comics video.
"""
import json
import unittest
from unittest import mock

from books_brief import charts, enrich, facts, package, paths, prices, rank, store

from support import temporary_store

WEEK = "2026-W41"


def snapshot(week: str = WEEK) -> dict:
    """A week's snapshot with one row, so a package can be assembled without a network."""
    books = enrich.build(
        (rank.Ranked(isbn="9788172151234", rank=1, weeks_on_chart=2, is_new=False, score=1.4),),
        details={
            "9788172151234": enrich.Details(
                title="Ekti Shonar Boi",
                author="Sunil Gangopadhyay",
                publisher="Ananda Publishers",
                price=prices.Price(
                    amount=399.0,
                    retailer="amazon-in",
                    edition="paperback",
                    retailers=("amazon-in",),
                ),
            )
        },
        previous=None,
    )
    return facts.build(
        week, charts={"bengali": facts.Chart(books=books)}, window_weeks=7
    )


class Repo(unittest.TestCase):
    """A real temp store, a real snapshot, and two real artefact files — with no renderer."""

    def setUp(self):
        self._store = temporary_store()
        self.root = self._store.__enter__()
        self.addCleanup(self._store.__exit__, None, None, None)

        patcher = mock.patch.object(paths, "data_root", return_value=self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

        store.write_facts(WEEK, snapshot())

        # ⚠️ The two artefacts the renderers own, written here as bytes — **assembly must not care how they were made**,
        # only that they are there.
        self.directory = package.dir_for(WEEK, "bengali")
        self.directory.mkdir(parents=True)
        names = package.filenames(WEEK, "bengali")
        (self.directory / names["video"]).write_bytes(b"a picture with sound")
        (self.directory / names["thumbnail"]).write_bytes(b"a still")


class Assembly(Repo):
    def test_a_finished_package_holds_four_files_and_names_the_week_on_the_two_that_leave(self):
        """⚠️ **The naming rule, asserted rather than assumed.**

        The video and the thumbnail are the files an uploader picks up, so they carry the **week and the chart** — a file
        dragged out of its directory still identifies itself. The two metadata files stay in the folder, so they carry
        the chart alone and the week is the directory they are in.
        """
        package.assemble(WEEK, charts.get("bengali"))

        written = sorted(entry.name for entry in self.directory.iterdir())
        self.assertEqual(
            written,
            [
                "bengali-2026-W41.mp4",
                "metadata-bengali.json",
                "metadata-bengali.txt",
                "thumbnail-2026-W41-bengali.jpg",
            ],
        )

    def test_the_json_is_the_last_thing_to_appear_and_it_carries_the_bundle_hash(self):
        """⚠️ The completion marker, and the one field that makes it a statement about *these* facts.

        ⚠️ A package whose JSON named a different bundle from the one on disk is a package built from something else —
        and the description would be describing a chart nobody rendered.
        """
        text = package.assemble(WEEK, charts.get("bengali"))

        payload = json.loads(
            (self.directory / package.MANIFEST("bengali")).read_text(encoding="utf-8")
        )
        self.assertEqual(payload["bundle_hash"], package.bundle_hash(WEEK))
        self.assertEqual(payload["video"], text.video)
        self.assertEqual(payload["title"], text.title)


class WhenItIsNotComplete(Repo):
    def _drop(self, kind: str) -> None:
        (self.directory / package.filenames(WEEK, "bengali")[kind]).unlink()

    def test_a_missing_artefact_refuses_and_writes_no_manifest(self):
        """⚠️ **The test the whole module exists for.** A description claiming a video exists while nothing plays is
        worse than no package, because the folder looks finished.
        """
        for kind in ("video", "thumbnail"):
            with self.subTest(missing=kind):
                self.setUp()
                self._drop(kind)

                with self.assertRaises(package.PackageError):
                    package.assemble(WEEK, charts.get("bengali"))

                self.assertFalse((self.directory / package.MANIFEST("bengali")).exists())

    def test_a_stale_manifest_is_removed_before_anything_else_happens(self):
        """⚠️ **The subtle one.** If the manifest were only written at the end, a re-run that *failed* would leave the
        previous run's JSON in place — and the folder would read as finished while describing facts that are no longer
        the ones on disk.
        """
        package.assemble(WEEK, charts.get("bengali"))
        self.assertTrue((self.directory / package.MANIFEST("bengali")).exists())

        self._drop("thumbnail")
        with self.assertRaises(package.PackageError):
            package.assemble(WEEK, charts.get("bengali"))

        self.assertFalse(
            (self.directory / package.MANIFEST("bengali")).exists(),
            "the previous run's manifest survived a failed re-run, so the folder still reads as complete",
        )

    def test_a_crash_between_the_two_writes_leaves_no_manifest(self):
        """⚠️ Assembly writes the text file first and the JSON last, so a crash between them is the exact window the
        ordering protects — simulated rather than argued about.
        """
        calls: list[str] = []
        real = package.write_atomically

        def failing(path, text):
            calls.append(path.name)
            if path.name == package.MANIFEST("bengali"):
                raise OSError("the disk went away")
            return real(path, text)

        with mock.patch.object(package, "write_atomically", side_effect=failing):
            with self.assertRaises(OSError):
                package.assemble(WEEK, charts.get("bengali"))

        self.assertEqual(
            calls,
            [package.TEXT("bengali"), package.MANIFEST("bengali")],
            "the JSON must be written last",
        )
        self.assertFalse((self.directory / package.MANIFEST("bengali")).exists())

    def test_no_scratch_files_are_left_behind(self):
        """⚠️ The temp file is dot-prefixed and lives *inside* the package folder, so a crash that left one would put an
        unexplained file where a human looks for the week's deliverable.
        """
        package.assemble(WEEK, charts.get("bengali"))

        leftovers = [
            entry.name for entry in self.directory.iterdir() if entry.name.startswith(".")
        ]
        self.assertEqual(leftovers, [])

    def test_the_metadata_is_readable_by_the_person_who_did_not_run_it(self):
        """⚠️ `mkstemp` creates `0600` and `os.replace` keeps it, so without an explicit chmod the two metadata files are
        owner-only while the video beside them is `0644` — a papercut the day the uploader is someone else.
        """
        package.assemble(WEEK, charts.get("bengali"))

        for name in (package.TEXT("bengali"), package.MANIFEST("bengali")):
            with self.subTest(file=name):
                mode = (self.directory / name).stat().st_mode & 0o777
                self.assertEqual(mode, 0o644)


if __name__ == "__main__":
    unittest.main()
