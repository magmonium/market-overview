"""Ticket 09's staging folder — the one place a composition can fetch from.

⚠️ **A Remotion composition can only serve assets from the render project's own `public/`**, and this product's
snapshot lives in `store/` — inside the project, committed, and *not* servable. So a run **copies** the week's
`facts.json` into `public/` for the duration of the render.

⚠️ **Why the snapshot is staged rather than passed as props.** The brief puts its whole bundle in `--props`, but this
product's render is one bundle read by **four** compositions, and the chart id is what varies (ticket 13). Staging the
bundle once and varying the prop is what makes *"four independent renders from one snapshot"* literally true — and it
keeps `render.command`'s pinned props at `{chart, week}`, which is the thing that stops the renderer bundling the
**brief's** root by mistake.
"""
import hashlib
import pathlib
import tempfile
import unittest
from unittest import mock

from books_brief import paths, stage, store

from support import temporary_store


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TheStagedSnapshot(unittest.TestCase):
    def setUp(self):
        self._store = temporary_store()
        self.root = self._store.__enter__()
        self.addCleanup(self._store.__exit__, None, None, None)

        self._public = tempfile.TemporaryDirectory()
        self.addCleanup(self._public.cleanup)
        # ⚠️ **A `public/` that does not exist yet**, which is the state a fresh clone is in: the temporary directory
        # stands in for the project, and the staging folder inside it is what the copy has to create. Pointing at the
        # temporary directory itself would make `assertFalse(...exists())` false before the test began — which is how
        # this line was wrong the first time.
        self.public = pathlib.Path(self._public.name) / "public"

    def _week(self, week: str = "2026-W41") -> pathlib.Path:
        return store.write_facts(week, {"meta": {"week": week}, "charts": {}})

    def test_the_week_is_staged_where_the_renderer_can_fetch_it(self):
        """⚠️ The staged path and the fetch path must be **the same string**, and this asserts both halves.

        `url_for` is what the composition hands to `staticFile`; `staged_path` is where the copy actually lands. They
        are two sides of a subprocess boundary — the same shape as `render.ENTRY` — so a disagreement between them is a
        render that reports a missing file rather than a test that fails.
        """
        self._week()

        staged = stage.snapshot("2026-W41", self.public)

        self.assertEqual(staged, self.public / "weeks" / "2026-W41" / "facts.json")
        self.assertEqual(
            staged.relative_to(self.public).as_posix(), stage.url_for("2026-W41")
        )

    def test_the_staged_copy_is_the_snapshot_byte_for_byte(self):
        """⚠️ **A copy, never a re-serialisation.**

        The tempting version is to read the bundle and dump it again — which would reorder keys, or re-escape the
        Bengali titles the operator can read. The renderer must receive *exactly* the bytes the snapshot holds, so the
        two digests are compared rather than the call to `copyfile` being trusted.
        """
        source = self._week()

        staged = stage.snapshot("2026-W41", self.public)

        self.assertEqual(digest(staged), digest(source))

    def test_a_fresh_clone_has_no_public_folder_and_the_stage_creates_it(self):
        """⚠️ `public/` is gitignored, so **a fresh clone does not have one** — and a `copyfile` into a missing
        directory raises rather than creating it.

        This is the difference between a first run on a new machine working and failing at the last step of a fetch
        that has already cost a week's requests.
        """
        self._week()

        self.assertFalse(self.public.exists())

        stage.snapshot("2026-W41", self.public)

        self.assertTrue(self.public.is_dir())

    def test_a_week_with_no_snapshot_refuses_rather_than_staging_nothing(self):
        """⚠️ **`FileNotFoundError`, not an empty stage.**

        A week is only ever rendered from a snapshot that was written (ADR 0003 — the snapshot's existence is the
        switch), so a missing one means the caller skipped the build. Staging nothing would let the render proceed and
        fail inside Remotion with a fetch error, a long way from the actual cause.
        """
        with self.assertRaises(FileNotFoundError):
            stage.snapshot("2026-W41", self.public)

        self.assertFalse((self.public / "weeks").exists())


class TheStagedMark(unittest.TestCase):
    def setUp(self):
        self._public = tempfile.TemporaryDirectory()
        self.addCleanup(self._public.cleanup)
        self.public = pathlib.Path(self._public.name) / "public"

    def test_no_asset_is_staged_as_an_explicit_null_rather_than_as_no_file(self):
        """⚠️ **The fetch must never 404.** A composition can only serve from `public/`, so an absent `mark.json` is a
        failed render — to learn something that was never an error.

        ⚠️ And *no mark* is a **valid brief**, not a broken one: the mark is the operator's to drop in, and until they
        do the charts still render, just without it.
        """
        with mock.patch.object(paths, "mark_dir", return_value=self.public / "nothing"):
            staged = stage.mark(self.public)

        self.assertEqual(staged, self.public / "mark.json")
        self.assertEqual(staged.read_text(encoding="utf-8"), "null")

    def test_the_mark_is_staged_once_and_not_beside_each_week(self):
        """⚠️ It is identical for every chart and every week (ticket 09), so a copy per week would be the same bytes
        four times over — and a mark that changed in one of them would be a chart wearing different branding.
        """
        with mock.patch.object(paths, "mark_dir", return_value=self.public / "nothing"):
            staged = stage.mark(self.public)

        self.assertEqual(staged, self.public / stage.mark_url())
        self.assertEqual(staged.parent, self.public)


class TheStagedCovers(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name)
        self.public = self.root / "public"
        self.cache = self.root / "resource" / "books" / "covers"

        patcher = mock.patch.object(paths, "data_root", return_value=self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_a_cover_the_chart_has_is_staged_under_its_isbn(self):
        """⚠️ **The cache is in the data root and `staticFile` can only serve from `public/`**, so without this copy a
        slide pointing at `resource/books/covers/` renders a broken image.

        ⚠️ Keyed by **ISBN**, which is what makes the superset cheap (ticket 14): a title in both the Bengali and the
        all-language chart resolves to one file.
        """
        self.cache.mkdir(parents=True)
        (self.cache / "9788172151234.jpg").write_bytes(b"a cover")

        staged = stage.covers(["9788172151234"], self.public)

        self.assertEqual(staged, [self.public / "covers" / "9788172151234.jpg"])
        self.assertEqual(
            staged[0].relative_to(self.public).as_posix(),
            stage.covers_url("9788172151234"),
        )
        self.assertEqual(staged[0].read_bytes(), b"a cover")

    def test_no_isbns_stages_nothing_at_all(self):
        """⚠️ **An absent file is the signal, not a gap.**

        Ticket 07's missing-cover rule is a **branded tile** — the book's initial on `BG` with a `RULE` border — and the
        renderer reaches it by reading `cover: null` on the row. ⚠️ So the caller passes only the ISBNs whose row records
        a cover, which makes an empty list the *whole* mechanism for a chart with none — and it must not even create the
        folder.
        """
        self.assertEqual(stage.covers([], self.public), [])
        self.assertFalse((self.public / "covers").exists())

    def test_a_cover_recorded_but_missing_from_the_cache_is_a_refusal(self):
        """⚠️ **Learned from a render, not reasoned out — and the first version of this test was wrong.**

        The tempting behaviour is to skip the row and let the tile draw, on the argument that *"one lost JPEG must not
        refuse a week."* ⚠️ **A render proved it fails in the worst possible way:** the row still says
        `cover: {url, sha256}`, so the renderer requests a file that was never staged, Remotion's `<Img>` gets a 404 and
        **cancels the whole render**.

        ⚠️ And refusing is *correct*, not merely convenient: ticket 05's cache is what makes a rebuild possible without
        committing hundreds of images a week, so a recorded cover whose bytes have vanished means the snapshot is no
        longer reproducible from disk.
        """
        with self.assertRaises(FileNotFoundError):
            stage.covers(["9788172151234"], self.public)

        self.assertFalse((self.public / "covers").exists())


if __name__ == "__main__":
    unittest.main()
