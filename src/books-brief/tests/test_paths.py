"""Ticket 09 — the folder seams, and the one a test can relocate.

⚠️ **`data_root()` is defined *here*, and every data folder calls it by that module-level name.** The reel learned this
the hard way: delegating straight to the brief's own resolver would leave one half of the layout outside this module's
seam, so patching `books_brief.paths.data_root` would redirect `output/` and not `resource/` — **one test seam quietly
covering half of what it claims to.**

So the data folders are asserted separately, each following the same seam. A test that relocated the root and checked
only one of them would pass while the others wrote into the operator's real data root.
"""
import pathlib
import tempfile
import unittest
from unittest import mock

from books_brief import paths


class WhereTheDataLives(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name)

        patcher = mock.patch.object(paths, "data_root", return_value=self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_relocating_the_data_root_takes_the_cover_cache_with_it(self):
        """Ticket 05 caches covers under the shared root's `resource/books/`, keyed by ISBN."""
        self.assertEqual(
            paths.cover_cache_dir(), self.root / "resource" / "books" / "covers"
        )

    def test_relocating_the_data_root_takes_the_packages_with_it(self):
        """Ticket 13 writes packages under `output/books/<week>/<chart>/` — the brief's `output/<date>/<lang>` shape."""
        self.assertEqual(paths.output_dir(), self.root / "output" / "books")

    def test_relocating_the_data_root_takes_the_bed_with_it(self):
        """⚠️ **The bed is the brief's folder, but it is reached through *this* module's `data_root()`.**

        The music is one licensed asset shared by both products (0085_11), exactly as the mark is — so it lives in
        `resource/brief/` and not under `resource/books/`. ⚠️ But it resolves through this module's own seam, so a test
        that relocates the root moves the bed with everything else. A `music_dir()` that delegated straight to the
        brief's resolver would pass every other assertion here and quietly read the operator's real data root.
        """
        self.assertEqual(paths.music_dir(), self.root / "resource" / "brief")


class WhereTheToolchainLives(unittest.TestCase):
    def test_the_toolchain_root_is_the_repository_and_not_this_project(self):
        """⚠️ **The bundled `ffmpeg` is installed once, at the repository root, beside the brief.**

        `market_overview.audio` finds it there (`node_modules/@remotion/compositor-*`), so the mux has to be pointed at
        the repository rather than at `src/books-brief`. ⚠️ Asserted by *what is in it* rather than by arithmetic on
        `parents`: a rename that moved this project would silently make `parents[1]` mean `src/`, which is exactly the
        trap the reel's `repo_root` docstring records.
        """
        self.assertNotEqual(paths.repo_root(), paths.project_root())
        self.assertTrue(
            (paths.repo_root() / "src" / "market_overview").is_dir(),
            "the toolchain root is the repository — the folder holding the brief's own package",
        )


class WhereTheRenderStages(unittest.TestCase):
    def test_the_staging_folder_is_in_the_project_and_not_the_data_root(self):
        """⚠️ Ticket 09 — `public/` is *"render staging, gitignored"*, and it is **not data**.

        ⚠️ **The distinction is what keeps this test honest, and the `setUp` above is the whole point of it.** The data
        root is relocatable so a test can point the layout at a temporary directory — but `public/` must **not** move
        with it: Remotion only serves assets from the render project's own `public/`, so a staging folder under the data
        root would be a folder the renderer cannot see. A `public_dir()` that delegated to `data_root()` would pass
        every other test in this file and fail here.
        """
        self.assertEqual(paths.public_dir(), paths.project_root() / "public")


if __name__ == "__main__":
    unittest.main()
