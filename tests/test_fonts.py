"""The vendored typeface — described once, present on every machine, and the same one on both sides.

⚠️ **The failure this file exists for is silent.** A face named in the CSS with no file behind it renders as
*nothing*, and a subset missing from `fonts.json` renders half an edition in a fallback — on some machines and
not others, which is the exact class of defect the move to a vendored face was meant to end. Neither shows up as
an error anywhere; both show up as a still that looks right.

So the assertions here are deliberately about **agreement between two descriptions**. `remotion/fonts.json` and
`remotion/fonts.ts` are two halves of one statement — the data and the imports — and `copybudget.py` reads the
same manifest from Python, because the gate measures in a browser "because only the browser knows the face's
metrics", and a gate measuring a face the render might not have used is worse than no gate.
"""
from __future__ import annotations

import json
import re
import unittest

from market_overview import copybudget, store

ROOT = store.root()
REMOTION = ROOT / "remotion"
FONTS = REMOTION / "fonts"

MANIFEST = json.loads((REMOTION / "fonts.json").read_text(encoding="utf-8"))
FONTS_TS = (REMOTION / "fonts.ts").read_text(encoding="utf-8")

#: `import bengali400 from './fonts/NotoSansBengali-bengali-400.woff2';` → name → file.
IMPORTS = dict(
    re.findall(r"^import (\w+) from '\./fonts/([\w.\-]+\.woff2)';", FONTS_TS, re.MULTILINE)
)

MANIFEST_FILES = {face["file"].removeprefix("fonts/") for face in MANIFEST["faces"]}

#: ⚠️ `IMPORTS` maps the *binding* to the *file*, and both directions of the agreement check want the files.
IMPORTED_FILES = set(IMPORTS.values())

#: ⚠️ Comments are stripped before any "is this string gone?" check, because the comments are where the
#: *history* of the string is recorded — this module's own header names the old face to explain why it went.
COMMENT = re.compile(r"/\*.*?\*/|//[^\n]*", re.S)


def code_only(source: str) -> str:
    return COMMENT.sub("", source)

#: ⚠️ The renderer's defaults, plus one. `fontWeight` is only written where it is *not* 400, so 400 has to be
#: added by hand or a file that stopped declaring it would pass this scan.
IMPLICIT_WEIGHT = 400


def weights_the_renderer_asks_for() -> set[int]:
    asked = set()
    for path in sorted(REMOTION.glob("*.ts*")):
        source = path.read_text(encoding="utf-8")
        asked |= {int(weight) for weight in re.findall(r"fontWeight: (\d+)", source)}
    return asked


class Agreement(unittest.TestCase):
    def test_every_face_in_the_manifest_is_imported(self):
        """⚠️ The direction that renders nothing: a rule whose `src` is `url('undefined')`."""
        missing = MANIFEST_FILES - IMPORTED_FILES
        self.assertEqual(missing, set(), "fonts.json declares a face that fonts.ts does not import")

    def test_every_import_is_a_face(self):
        """The other direction — an import nobody declares is a file that ships and is never used."""
        extra = IMPORTED_FILES - MANIFEST_FILES
        self.assertEqual(extra, set(), "fonts.ts imports a file that fonts.json does not describe")

    def test_every_face_file_is_present(self):
        for name in sorted(MANIFEST_FILES):
            with self.subTest(face=name):
                path = FONTS / name
                self.assertTrue(path.is_file(), f"{path} is declared but not on disk")
                self.assertGreater(path.stat().st_size, 1024, f"{path} is too small to be a face")

    def test_the_manifest_is_not_empty(self):
        """A scan that has stopped reading its inputs passes every assertion above."""
        self.assertTrue(MANIFEST_FILES, "the manifest has no faces")
        self.assertTrue(IMPORTS, "the import scan found nothing — it has stopped reading fonts.ts")


class TheSameFaceOnBothSides(unittest.TestCase):
    def test_the_copy_budget_measures_the_renderer_s_family(self):
        """⚠️ The gate measures in a browser; if it names a different family than the renderer, it measures a
        face the brief is not set in — and reports a comfortable, wrong budget."""
        self.assertEqual(copybudget.FONT_FAMILY, MANIFEST["family"])

    def test_the_copy_budget_waits_for_every_baked_weight(self):
        self.assertEqual(
            copybudget.FONT_WEIGHTS, sorted({face["weight"] for face in MANIFEST["faces"]})
        )

    def test_the_stack_names_the_family_first(self):
        """A fallback listed before the real face is a fallback that renders."""
        self.assertTrue(copybudget.FONT.startswith(f'"{MANIFEST["family"]}"'))


class TheWeights(unittest.TestCase):
    def test_the_baked_weights_cover_what_the_blocks_ask_for(self):
        """⚠️ A weight the renderer sets but no face provides is a weight the browser **synthesises** — a
        different and worse rendering than the one the card was composed against, and nothing logs it."""
        baked = {face["weight"] for face in MANIFEST["faces"]}
        asked = weights_the_renderer_asks_for() | {IMPLICIT_WEIGHT}
        self.assertTrue(asked, "the weight scan found nothing — it has stopped reading the renderer")
        self.assertLessEqual(asked, baked, f"the blocks ask for {sorted(asked)}, baked: {sorted(baked)}")

    def test_every_subset_covers_every_weight(self):
        """Otherwise a subset is missing at one weight and silently falls back for exactly that text."""
        by_subset: dict[str, set[int]] = {}
        for face in MANIFEST["faces"]:
            subset = re.sub(r"-\d+\.woff2$", "", face["file"])
            by_subset.setdefault(subset, set()).add(face["weight"])
        expected = {face["weight"] for face in MANIFEST["faces"]}
        for subset, weights in sorted(by_subset.items()):
            with self.subTest(subset=subset):
                self.assertEqual(weights, expected, f"{subset} does not cover every weight")


class NoSystemFace(unittest.TestCase):
    def test_nothing_in_the_render_layer_names_the_old_system_face(self):
        """⚠️ The regression this whole change is about. "Kohinoor Bangla" is an Apple-bundled face, so a single
        surviving reference re-introduces a render that depends on the machine it ran on."""
        for path in sorted(REMOTION.rglob("*.ts*")):
            with self.subTest(file=path.name):
                self.assertNotIn("Kohinoor", code_only(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
