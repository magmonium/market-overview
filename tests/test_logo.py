"""The shipped mark — polarity, the chip, and the one requirement on the asset. (0085_10)

⚠️ Why these are worth having at all: the chip is the *entire* mechanism that makes one asset work on every
card in both editions (issue 21). If polarity detection is wrong the mark is drawn dark-on-dark, and the
failure is invisible in a diff and easy to miss in a 1080p still — the logo just looks slightly wrong. So the
logic is tested here rather than judged by eye.
"""
import base64
import pathlib
import re
import tempfile
import unittest

from market_overview import logo


#: A minimal outlined mark: a light ink on a dark plate. Nothing here needs a font.
LIGHT_MARK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" fill="#0b0e13"/>
  <path d="M8 8h48v48H8z" fill="#f4f6fa"/>
  <path d="M16 16h32v32H16z" fill="#f4f6fa"/>
</svg>"""

#: The same shape with a dark ink — a mark drawn for a light card.
DARK_MARK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <path d="M8 8h48v48H8z" fill="#101418"/>
</svg>"""


class Colour(unittest.TestCase):
    def test_every_hex_length_a_designer_actually_writes(self):
        self.assertEqual(logo._parse_colour("#fff"), (255, 255, 255))
        self.assertEqual(logo._parse_colour("#F4F6FA"), (244, 246, 250))
        self.assertEqual(logo._parse_colour("#000000"), (0, 0, 0))

    def test_a_four_and_eight_digit_hex_keeps_the_colour_and_drops_the_alpha(self):
        self.assertEqual(logo._parse_colour("#ffff"), (255, 255, 255))
        self.assertEqual(logo._parse_colour("#f4f6faff"), (244, 246, 250))

    def test_rgb_functional_notation(self):
        self.assertEqual(logo._parse_colour("rgb(0, 0, 0)"), (0, 0, 0))
        self.assertEqual(logo._parse_colour("rgba(255,255,255,0.5)"), (255, 255, 255))
        self.assertEqual(logo._parse_colour("rgb(50%, 50%, 50%)"), (128, 128, 128))

    def test_names_the_common_marks_use(self):
        self.assertEqual(logo._parse_colour("white"), (255, 255, 255))
        self.assertEqual(logo._parse_colour("Black"), (0, 0, 0))

    def test_values_that_are_not_an_ink_we_can_measure_are_skipped(self):
        # ⚠️ Each of these has to return None rather than a guess: an unmeasurable ink must fall back to the
        # documented default, because a *wrong* luminance flips the chip and makes the mark less legible.
        for value in ("none", "currentColor", "inherit", "transparent", "url(#grad)", "context-fill", ""):
            with self.subTest(value=value):
                self.assertIsNone(logo._parse_colour(value))


class Luminance(unittest.TestCase):
    def test_the_ends_of_the_scale(self):
        self.assertAlmostEqual(logo.luminance((0, 0, 0)), 0.0)
        self.assertAlmostEqual(logo.luminance((255, 255, 255)), 1.0)

    def test_mid_grey_is_perceptually_dark_not_half(self):
        # ⚠️ The reason this is WCAG-weighted rather than a channel average. #808080 averages to 0.5, which
        # would put it exactly on the threshold; perceptually it is well below it. The threshold decides which
        # way the chip goes, so this is the whole job.
        self.assertLess(logo.luminance((128, 128, 128)), 0.5)

    def test_green_reads_brighter_than_blue_at_the_same_channel_value(self):
        self.assertGreater(logo.luminance((0, 255, 0)), logo.luminance((0, 0, 255)))


class Ink(unittest.TestCase):
    def test_the_dominant_fill_wins_over_the_plate(self):
        # Two light paths against one dark plate — the ink is the light colour, whichever order they appear.
        self.assertEqual(logo.ink(LIGHT_MARK), "#f4f6fa")

    def test_the_plate_wins_when_it_is_the_dominant_fill(self):
        self.assertEqual(logo.ink(DARK_MARK), "#101418")

    def test_a_style_attribute_is_read_as_well_as_the_attribute(self):
        svg = '<svg><path style="fill: #fff"/></svg>'
        self.assertEqual(logo.ink(svg), "#ffffff")

    def test_a_gradients_stops_count_as_the_ink(self):
        # A gradient is how the fill is painted, so its stops are the mark's colour as much as a flat fill is.
        svg = '<svg><linearGradient><stop stop-color="#37d67a"/><stop stop-color="#37d67a"/></linearGradient></svg>'
        self.assertEqual(logo.ink(svg), "#37d67a")

    def test_fill_opacity_is_not_mistaken_for_a_fill(self):
        self.assertIsNone(logo.ink('<svg><path fill-opacity="0.5"/></svg>'))

    def test_a_mark_declaring_no_measurable_fill_yields_nothing(self):
        self.assertIsNone(logo.ink('<svg><path d="M0 0h1v1H0z" fill="url(#g)"/></svg>'))



class Polarity(unittest.TestCase):
    def test_light_ink_is_light_ink(self):
        self.assertEqual(logo.polarity("#f4f6fa"), logo.INK_LIGHT)

    def test_dark_ink_is_dark_ink(self):
        self.assertEqual(logo.polarity("#0b0e13"), logo.INK_DARK)

    def test_an_unreadable_ink_falls_back_to_light(self):
        # The frame is near-black throughout, so a mark drawn for it is drawn light.
        self.assertEqual(logo.polarity(None), logo.INK_LIGHT)

    def test_the_override_beats_detection_in_both_directions(self):
        self.assertEqual(logo.polarity("#f4f6fa", "dark"), logo.INK_DARK)
        self.assertEqual(logo.polarity("#0b0e13", "light"), logo.INK_LIGHT)

    def test_an_override_that_is_not_a_polarity_is_ignored_rather_than_trusted(self):
        self.assertEqual(logo.polarity("#f4f6fa", "chartreuse"), logo.INK_LIGHT)


class Chip(unittest.TestCase):
    def test_the_chip_is_always_the_opposite_of_the_ink(self):
        self.assertEqual(logo.chip_for(logo.INK_LIGHT), logo.CHIP_DARK)
        self.assertEqual(logo.chip_for(logo.INK_DARK), logo.CHIP_LIGHT)

    def test_a_light_ink_on_a_dark_chip_is_a_real_contrast_not_a_hope(self):
        # ⚠️ This is the assertion the whole chip mechanism exists to make possible: contrast is computed, not
        # judged. Issue 21 rejected a low-opacity bug precisely because over a dark moving gradient the
        # contrast could not be guaranteed.
        ink = logo.luminance(logo._parse_colour("#f4f6fa"))
        chip = logo.luminance(logo._parse_colour(logo.CHIP_DARK))
        self.assertGreater(abs(ink - chip), 0.5)

    def test_the_dark_chip_is_not_the_raw_scene_colour(self):
        # A chip the exact colour of the frame would look like a hole rather than a plate.
        self.assertNotEqual(logo.CHIP_DARK, "#0b0e13")


class Outlined(unittest.TestCase):
    def test_a_path_only_mark_passes(self):
        logo.assert_outlined(LIGHT_MARK, "logo.svg")

    def test_each_way_a_designer_puts_text_in_an_svg_is_caught(self):
        for element in ("<text x='0' y='0'>A</text>", "<tspan>A</tspan>", "<textPath href='#p'>A</textPath>"):
            with self.subTest(element=element):
                with self.assertRaises(logo.LogoError):
                    logo.assert_outlined(f"<svg>{element}</svg>", "logo.svg")

    def test_a_commented_out_text_element_does_not_condemn_a_good_asset(self):
        # ⚠️ The same trap `test_world.py` fell into: a check that greps source without stripping comments
        # matches its own explanatory note. A designer's leftover comment is not drawn text.
        logo.assert_outlined("<svg><!-- <text>x</text> --><path d='M0 0'/></svg>", "logo.svg")

    def test_the_refusal_names_the_way_out(self):
        # The operator is the one who has to act, so the message has to say what to do, not just what failed.
        with self.assertRaises(logo.LogoError) as caught:
            logo.assert_outlined("<svg><text>A</text></svg>", "logo.svg")
        self.assertIn("Outline the text to paths", str(caught.exception))
        self.assertIn("2x PNG", str(caught.exception))


class Supplied(unittest.TestCase):
    """`resource/` is the operator's folder — these use a stand-in for it, never the real one."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.resource = pathlib.Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, name: str, text: str) -> pathlib.Path:
        path = self.resource / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_nothing_supplied_yields_nothing_rather_than_an_error(self):
        # ⚠️ The asset is the operator's to drop in, and until they do the brief must still render — the mark
        # is absent, not the video. This is also what makes this ticket testable before the asset exists.
        self.assertIsNone(logo.load(self.resource))

    def test_svg_is_preferred_over_a_raster(self):
        self._write("logo.svg", LIGHT_MARK)
        self._write("logo.png", "not really a png")
        self.assertEqual(logo.find(self.resource).name, "logo.svg")

    def test_a_raster_is_accepted_when_it_is_all_there_is(self):
        # Issue 21 sets this fallback explicitly rather than leaving the operator to guess.
        self._write("logo.png", "not really a png")
        self.assertEqual(logo.find(self.resource).name, "logo.png")
        self.assertEqual(logo.load(self.resource)["polarity"], logo.INK_LIGHT)

    def test_the_mark_arrives_as_a_data_uri_on_the_render_props(self):
        self._write("logo.svg", LIGHT_MARK)
        src = logo.load(self.resource)["src"]
        self.assertTrue(src.startswith("data:image/svg+xml;base64,"))
        self.assertEqual(base64.b64decode(src.split(",", 1)[1]).decode("utf-8"), LIGHT_MARK)

    def test_the_chip_follows_the_detected_ink(self):
        self._write("logo.svg", LIGHT_MARK)
        self.assertEqual(logo.load(self.resource)["chip"], logo.CHIP_DARK)
        self._write("logo.svg", DARK_MARK)
        self.assertEqual(logo.load(self.resource)["chip"], logo.CHIP_LIGHT)

    def test_the_env_override_corrects_a_raster_whose_ink_cannot_be_read(self):
        import os

        self._write("logo.png", "not really a png")
        os.environ[logo.POLARITY_ENV] = "dark"
        try:
            mark = logo.load(self.resource)
            self.assertEqual(mark["polarity"], logo.INK_DARK)
            self.assertEqual(mark["chip"], logo.CHIP_LIGHT)
            self.assertEqual(mark["declared"], "dark")
        finally:
            del os.environ[logo.POLARITY_ENV]

    def test_an_unoutlined_mark_stops_the_run_rather_than_shipping(self):
        self._write("logo.svg", "<svg><text>A</text></svg>")
        with self.assertRaises(logo.LogoError):
            logo.load(self.resource)

    def test_loading_twice_gives_the_identical_mark(self):
        # Determinism, held to the same standard as every other animated value: a re-render reproduces it.
        self._write("logo.svg", LIGHT_MARK)
        self.assertEqual(logo.load(self.resource), logo.load(self.resource))

    def test_loading_never_touches_the_supplied_file(self):
        # The supplied file is the master. A pipeline that normalises its inputs in place destroys the thing
        # it was given, and the licence on it is the operator's.
        path = self._write("logo.svg", LIGHT_MARK)
        before = path.read_bytes(), path.stat().st_mtime_ns
        logo.load(self.resource)
        self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), before)


class ReservedRegion(unittest.TestCase):
    """The renderer's numbers against issue 21's verdict table.

    ⚠️ Worth a test because the failure mode is silent: a bug that drifts outside the reserved area still
    renders perfectly, and only collides with something in 0085_12's thumbnail or a future card. Reading the
    TSX is the only way to check it without rendering.
    """

    SOURCE = pathlib.Path(__file__).resolve().parents[1] / "remotion" / "Brand.tsx"

    def _constants(self, name: str) -> dict[str, int]:
        text = self.SOURCE.read_text(encoding="utf-8")
        match = re.search(rf"export const {name} = \{{([^}}]+)\}}", text)
        assert match, f"{name} not found in Brand.tsx"
        return {key: int(value) for key, value in re.findall(r"(\w+):\s*(\d+)", match.group(1))}

    def test_the_reserved_area_is_the_tickets(self):
        # Issue 21: top-right 260 x 160 px, `x >= 1660`, `y <= 160`.
        self.assertEqual(
            self._constants("RESERVED"), {"width": 260, "height": 160, "left": 1660, "top": 0}
        )

    def test_the_reserved_area_reaches_the_frame_corner(self):
        # `x >= 1660` is only the same region as "the top-right corner" if these add up to the frame width.
        region = self._constants("RESERVED")
        self.assertEqual(region["left"] + region["width"], 1920)
        self.assertEqual(region["top"], 0)

    def test_the_bug_is_the_tickets_size_and_inset(self):
        # Issue 21: bug <=96 px on its longest side, 48 px inset from the top and right edges.
        self.assertEqual(self._constants("BUG"), {"size": 96, "inset": 48})

    def test_the_bug_sits_inside_the_reserved_area(self):
        # ⚠️ The relationship, not just the numbers. The chip is opaque and drawn last, so a bug that overhangs
        # the reserved area would cover whatever it overhangs — which is exactly what the reserved area exists
        # to prevent.
        reserved, bug = self._constants("RESERVED"), self._constants("BUG")
        self.assertLessEqual(bug["inset"] + bug["size"], reserved["top"] + reserved["height"])
        self.assertLessEqual(bug["inset"] + bug["size"], 1920 - reserved["left"])

    def test_the_inset_places_the_bug_at_the_top_right(self):
        reserved, bug = self._constants("RESERVED"), self._constants("BUG")
        left = 1920 - bug["inset"] - bug["size"]
        self.assertGreaterEqual(left, reserved["left"])
        self.assertGreaterEqual(bug["inset"], reserved["top"])

    def test_the_lockup_is_derived_from_the_thumbnails_share_not_chosen(self):
        # ⚠️ Issue 21 gives the bug a size and the lockup only "full-size". So the lockup's number has to come
        # from somewhere rather than looking nice on one still — and the ticket does name one share: the
        # thumbnail's mark is 128 of 1280, which is 10%. Asserting the relationship keeps it a derivation.
        lockup = self._constants("LOCKUP")
        self.assertAlmostEqual(lockup["size"] / 1920, 128 / 1280, places=2)

    def test_the_lockup_is_bigger_than_the_bug(self):
        # "Full-size" has to mean something. A lockup at or below the bug's size is not a lockup.
        self.assertGreater(self._constants("LOCKUP")["size"], self._constants("BUG")["size"])
