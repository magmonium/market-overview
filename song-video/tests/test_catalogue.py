"""0087_11 — the menu's catalogue: **read from the renderer, never mirrored.**

⚠️ The alternative was a hand-maintained list of theme ids in Python, pinned to the TypeScript by a test — the
brief's own habit for `display.py`. It is the wrong habit here: `display.py` mirrors *formatting rules*, where a
drift shows up in a number a human can compare, while this would mirror the **menu itself**. A theme added to the
renderer and missed in the copy is a theme the operator cannot tick, and nothing anywhere would say so.

So this shells out to the renderer's catalogue. It is slower and it makes the suite depend on node — both true,
and both cheaper than a menu that quietly lies.
"""
import pathlib
import tempfile
import unittest
from unittest import mock

from song_video import catalogue, paths


class TheRenderersOwnCatalogue(unittest.TestCase):
    def test_the_menu_offers_exactly_the_themes_the_renderer_can_draw(self):
        """⚠️ The ids ride in `run.json` and in output filenames, so this list is a **contract**: changing it is
        a migration, and this test is where somebody finds that out — deliberately, not by surprise."""
        found = catalogue.themes()

        self.assertEqual([entry.id for entry in found], ["vinyl", "neon", "parchment", "aurora"])
        self.assertTrue(all(entry.name for entry in found), "every theme needs a name the menu can show")

    def test_the_menu_offers_exactly_the_wave_forms_the_renderer_can_draw(self):
        self.assertEqual(list(catalogue.forms()), ["bars", "ribbon", "ring", "bloom"])


class WhereTheCatalogueIsReadFrom(unittest.TestCase):
    def test_relocating_the_data_root_does_not_take_the_menu_with_it(self):
        """⚠️ The catalogue is **source**, and `paths.project_root()` is the **data** root a test relocates.

        If they shared the one seam, the CLI's own tests — which point `resource/`, `store/` and `output/` at a
        temporary directory — would silently answer "unknown theme" for every theme that exists.
        """
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

        patcher = mock.patch.object(paths, "project_root", return_value=pathlib.Path(self._tmp.name))
        patcher.start()
        self.addCleanup(patcher.stop)

        self.assertEqual([entry.id for entry in catalogue.themes()], ["vinyl", "neon", "parchment", "aurora"])


if __name__ == "__main__":
    unittest.main()
