"""The animated backdrop — what replaced the three.js world.

⚠️ These read the renderer's **source**, not a running browser. That is the same deliberate limit `test_world.py`
carried: a rendered layer cannot be inspected from pytest, so what is checked here is the *contract* — that the 3D
dependency is actually gone, that the backdrop is frame-derived and deterministic, that it is vibrant and animating,
and that a slide no longer fades out — while the frames themselves were verified by rendering and looking.

The four failure modes this file exists to catch, all silent:

- **three.js creeping back.** The whole point of the change was to drop a WebGL canvas, an ANGLE-only Chromium
  flag and four dependencies. A reintroduced import would render perfectly and re-cost all of that.
- **A card that hides the backdrop.** Every card used to paint an opaque `#0b0e13`. Reverting one would leave the
  brief rendering perfectly, with the entire layer behind it invisible and no error anywhere.
- **A backdrop that is not reproducible.** `Math.random()` or wall-clock time would make two renders of the same
  bundle differ, which breaks the promise ADR 0003 rests on.
- **A slide that fades the background out.** The card scrim used to *reveal* from 35 % opacity; the requirement is
  that it no longer animates, so the backdrop stays put behind every card.
"""
import json
import re
import unittest

from market_overview import store

REMOTION = store.root() / "remotion"
MARKET_BRIEF_SOURCE = (REMOTION / "MarketBrief.tsx").read_text(encoding="utf-8")
THUMBNAIL_SOURCE = (REMOTION / "Thumbnail.tsx").read_text(encoding="utf-8")
BACKDROP_SOURCE = (REMOTION / "Backdrop.tsx").read_text(encoding="utf-8")
FURNITURE_SOURCE = (REMOTION / "Furniture.tsx").read_text(encoding="utf-8")
THEME_SOURCE = (REMOTION / "theme.ts").read_text(encoding="utf-8")
BLOCKS_SOURCE = (REMOTION / "blocks.tsx").read_text(encoding="utf-8")
PACKAGE = json.loads((store.root() / "package.json").read_text(encoding="utf-8"))

COMMENT = re.compile(r"/\*.*?\*/|//[^\n]*", re.S)


def code_only(source: str) -> str:
    """⚠️ Source with comments removed. Several tests below look for the *absence* of a pattern, and the prose
    explaining why that pattern is forbidden contains the pattern — so scanning raw source fails on the
    documentation rather than on the code."""
    return COMMENT.sub("", source)


BACKDROP_CODE = code_only(BACKDROP_SOURCE)


class ThreeIsGone(unittest.TestCase):
    """⚠️ The dependency, the canvas and the ANGLE requirement all have to be actually gone — not merely unused."""

    def test_no_three_dependency_is_declared(self):
        declared = set(PACKAGE.get("dependencies", {})) | set(PACKAGE.get("devDependencies", {}))
        for name in ("three", "@types/three", "@react-three/fiber", "@remotion/three"):
            with self.subTest(dependency=name):
                self.assertNotIn(name, declared, f"{name} is still a declared dependency")

    def test_no_renderer_file_imports_three(self):
        for path in sorted(REMOTION.rglob("*.ts*")):
            source = code_only(path.read_text(encoding="utf-8"))
            with self.subTest(file=path.name):
                self.assertNotIn("from 'three'", source)
                self.assertNotIn("from \"three\"", source)
                self.assertNotIn("@react-three/fiber", source)
                self.assertNotIn("@remotion/three", source)
                self.assertNotIn("ThreeCanvas", source)

    def test_the_world_directory_and_its_smoke_test_are_deleted(self):
        self.assertFalse((REMOTION / "world").exists(), "the 3D world still exists on disk")
        self.assertFalse((REMOTION / "ThreeSmoke.tsx").exists(), "the WebGL smoke test still exists")

    def test_the_angle_requirement_is_dropped(self):
        """⚠️ ANGLE was pinned *only* because three.js fails silently under the default backend. With no WebGL
        context left there is nothing to pin, and a stale setting would be a claim about machinery that is gone.

        ⚠️ Comments are stripped first: the note in the config *explains* the removal, so it contains the very
        symbol this test forbids — scanning raw source would fail on the documentation rather than the code."""
        config = code_only((store.root() / "remotion.config.ts").read_text(encoding="utf-8"))
        self.assertNotIn("setChromiumOpenGlRenderer", config)



class TheBackdrop(unittest.TestCase):
    """The layer behind the DOM: vibrant, animating, and a pure function of the frame and the seed."""

    def test_it_is_mounted_once_for_the_whole_brief(self):
        """⚠️ One layer, not one per block — so the field is continuous from the pre-roll to the close."""
        self.assertEqual(MARKET_BRIEF_SOURCE.count("<Backdrop "), 1)
        self.assertNotIn("Backdrop", BLOCKS_SOURCE)
        self.assertIn("import {Backdrop} from './Backdrop'", MARKET_BRIEF_SOURCE)

    def test_it_is_frame_derived_not_wall_clock(self):
        """⚠️ `useCurrentFrame()` is Remotion's virtual clock, so the same props give the same frames anywhere."""
        self.assertIn("useCurrentFrame", BACKDROP_CODE)
        self.assertNotIn("Date.now", BACKDROP_CODE)
        self.assertNotIn("performance.now", BACKDROP_CODE)

    def test_it_is_deterministic(self):
        """⚠️ The blob/speck fields are a pure function of a seed (ADR 0003) — never `Math.random()`."""
        self.assertNotIn("Math.random", BACKDROP_CODE)
        self.assertIn("seeded(seed)", BACKDROP_CODE)
        self.assertIn("export const seeded", code_only(THEME_SOURCE))

    def test_it_actually_animates(self):
        """⚠️ A "background animation" that never moves is the failure this whole change is about. The motion is
        sine/cosine of the elapsed seconds, so the field drifts, breathes and scrolls rather than sitting still."""
        self.assertIn("Math.sin(seconds", BACKDROP_CODE)
        self.assertIn("const seconds = frame / fps", BACKDROP_CODE)
        self.assertIn("backgroundPosition", BACKDROP_CODE, "the grid must scroll")

    def test_it_is_vibrant(self):
        """The palette is a set of saturated aurora colours, not the old desaturated 3D neutrals."""
        for name in ("RISING", "FALLING"):
            match = re.search(rf"const {name} = \[(.*?)\];", BACKDROP_SOURCE, re.S)
            with self.subTest(palette=name):
                self.assertIsNotNone(match, f"{name} palette is missing")
                colours = re.findall(r"#[0-9a-fA-F]{6}", match.group(1))
                self.assertGreaterEqual(len(colours), 4, f"{name} needs a spread of colours to stay vibrant")
        # The lobes are radial gradients blended with `screen`, which keeps overlaps bright rather than muddy.
        self.assertIn("radial-gradient", BACKDROP_CODE)
        self.assertIn("mixBlendMode: 'screen'", BACKDROP_CODE)

    def test_it_reads_the_day_s_direction(self):
        """The only thing that varies daily is which palette is used — the composition never changes."""
        self.assertIn("window?.change", BACKDROP_CODE)
        self.assertIn("rising", BACKDROP_CODE)


class TheSlideDoesNotFadeOut(unittest.TestCase):
    """⚠️ The card scrim is a fixed wash, so the backdrop is never faded out as a slide arrives."""

    def test_the_scrim_does_not_reveal(self):
        """The old `Card` held its scrim at `REVEAL_FROM` (0.35) and resolved it up over ~1.2 s — i.e. it faded the
        background *out* at the moment a viewer arrived. Both constants and the animated opacity must be gone."""
        codes = code_only(FURNITURE_SOURCE)
        self.assertNotIn("REVEAL_SECONDS", codes)
        self.assertNotIn("REVEAL_FROM", codes)
        self.assertNotIn("REVEAL", FURNITURE_SOURCE)

    def test_the_scrim_is_the_card_s_own_background(self):
        """⚠️ The scrim must be the card's **`background`**, never a separate positioned layer.

        A positioned `<AbsoluteFill>` scrim placed *before* the content paints **over** that content — CSS paint
        order puts positioned boxes (step 6) after in-flow non-positioned content (steps 3-5). Every figure on the
        card was therefore dimmed to whatever the gradient let through: measured on a rendered still, white
        `#f4f6fa` text peaked at luminance **79 of 255** on the scoreboard and **71** on the sector table, instead
        of ~245 — the "slides are barely visible" bug. As the card's own background it is always painted first,
        so the hazard cannot come back.
        """
        assert_in = self.assertIn
        assert_in("background: scrim", FURNITURE_SOURCE)
        self.assertNotIn(
            "<AbsoluteFill style={{background: scrim}}",
            FURNITURE_SOURCE,
            "a separate positioned scrim layer paints over the card's own text",
        )
        self.assertNotIn("opacity: scrim", FURNITURE_SOURCE)


class Depth(unittest.TestCase):
    """The DOM is always in front, and the backdrop is only where the layout says it may be."""

    def test_no_card_paints_an_opaque_background(self):
        """⚠️ The silent failure: a card that fills its frame solidly hides the entire backdrop layer, renders
        perfectly, and reports nothing."""
        for name, source in (("blocks.tsx", BLOCKS_SOURCE), ("Furniture.tsx", FURNITURE_SOURCE)):
            with self.subTest(file=name):
                self.assertNotIn("background: '#0b0e13'", source, f"{name} would hide the backdrop behind it")

    def test_both_scrims_are_translucent(self):
        """A scrim that is not translucent is an opaque card with extra steps."""
        for name in ("SCRIM", "SCRIM_OPEN"):
            match = re.search(rf"export const {name} =\n((?:.*\n)*?).*?;", THEME_SOURCE)
            with self.subTest(scrim=name):
                self.assertIsNotNone(match, f"{name} is missing")
                self.assertIn("rgba(11,14,19,", match.group(1), f"{name} is not translucent")

    def test_the_open_scrim_goes_only_where_the_lower_frame_is_empty(self):
        """⚠️ The split is the layout's, not a taste call. The dense table cards hold their content down to the
        bottom edge, so the backdrop must be a hint there; the sparse cards leave the lower band to it. `sectors`
        is the counter-example that set the rule: a thin scrim put the backdrop behind the heat cells, where it
        competed with the cells' own colour."""
        opened = set(re.findall(r"<Card title=\{copy\.blocks\.(\w+)\} scrim=\{SCRIM_OPEN\}>", BLOCKS_SOURCE))
        self.assertEqual(
            opened | {"close"},
            {"most_active", "breadth", "dma", "flows", "dependencies", "calendar", "close"},
        )
        dense = set(re.findall(r"<Card title=\{copy\.blocks\.(\w+)\}>", BLOCKS_SOURCE))
        self.assertEqual(dense, {"indexes", "leaders", "sectors", "heat_map", "broader"})


if __name__ == "__main__":
    unittest.main()
