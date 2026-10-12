"""The thumbnail still — 0085_12.

⚠️ These read the renderer's **source**, like `test_world.py`, and for the same reason: a canvas cannot be inspected
from pytest. What is checked is the *contract* — the size, the shared headline rule, the logo's still numbers, the
rest state, the reserved regions — while the frames themselves were verified by rendering and looking.

Two failure modes this file exists to catch, both silent:

- **The thumbnail disagreeing with the video.** Issue 13's rule is one bundle, three surfaces. If the still picked
  its own figure, both artefacts would still render perfectly and only a viewer holding them side by side would
  notice the product contradicting itself. The rule lives in `headline.ts` and this file asserts that *both* callers
  use it rather than each keeping a copy that happens to agree today.
- **The still animating.** A thumbnail is a still: anything frame-dependent makes "the same bundle gives the same
  image" stop being true, and a re-render could land on a different frame of an entrance.
"""
import json
import re
import unittest

from market_overview import render, store

DATE = "2026-10-12"
REMOTION = store.root() / "remotion"
THUMBNAIL_SOURCE = (REMOTION / "Thumbnail.tsx").read_text(encoding="utf-8")
BRAND_SOURCE = (REMOTION / "Brand.tsx").read_text(encoding="utf-8")
ROOT_SOURCE = (REMOTION / "Root.tsx").read_text(encoding="utf-8")
THEME_SOURCE = (REMOTION / "theme.ts").read_text(encoding="utf-8")
THUMB_THEME_SOURCE = (REMOTION / "world" / "theme.ts").read_text(encoding="utf-8")
STATIONS_SOURCE = (REMOTION / "world" / "stations.tsx").read_text(encoding="utf-8")
BLOCKS_SOURCE = (REMOTION / "blocks.tsx").read_text(encoding="utf-8")
HEADLINE_SOURCE = (REMOTION / "headline.ts").read_text(encoding="utf-8")

COMMENT = re.compile(r"/\*.*?\*/|//[^\n]*", re.S)


def code_only(source: str) -> str:
    """⚠️ Comments stripped. Several tests below look for the *absence* of a pattern, and the prose explaining why
    that pattern is forbidden contains the pattern. `test_world.py` learned this the hard way first."""
    return COMMENT.sub("", source)


class TheComposition(unittest.TestCase):
    """It is its own composition, at the still's own size."""

    def test_it_is_registered_at_you_tubes_still_size(self):
        """⚠️ 1280x720 is YouTube's, and it is **not** the video's 1920x1080 — a still at the wrong size is
        letterboxed or cropped by the platform, and the logo's reserved area would be sized against the wrong frame."""
        block = ROOT_SOURCE.split('id="Thumbnail"')[1].split("/>")[0]
        self.assertIn("width={1280}", block)
        self.assertIn("height={720}", block)
        self.assertIn("durationInFrames={1}", block)

    def test_the_video_is_still_1920_by_1080(self):
        block = ROOT_SOURCE.split('id="MarketBrief"')[1].split("/>")[0]
        self.assertIn("width={1920}", block)
        self.assertIn("height={1080}", block)

    def test_it_does_not_join_the_brief_s_registry(self):
        """⚠️ The still is not a block of the brief. Adding it to `REGISTRY` would schedule it on the timeline and
        give the video a fourteenth card that has no slot."""
        self.assertNotIn("Thumbnail", (REMOTION / "MarketBrief.tsx").read_text(encoding="utf-8"))

    def test_the_still_s_camera_is_not_on_the_video_s_rail(self):
        """⚠️ `STATIONS` is the video's rail, and `test_world.py` asserts both that it holds exactly one station per
        rendered block and that each station starts where the last ended. A thumbnail viewpoint is not a cut, so it
        must stay outside that table or it breaks both assertions and puts an uncut camera on a continuous rail."""
        self.assertIn("export const THUMBNAIL", STATIONS_SOURCE)
        # ⚠️ Matched on `define(`, which is the only way into the table — not on the word "thumbnail", which appears
        # in prose throughout this file and would make the assertion unfalsifiable the moment anyone wrote it down.
        self.assertNotIn("define('thumbnail'", STATIONS_SOURCE)
        self.assertIn("define('", STATIONS_SOURCE)


class OneFigureThreeSurfaces(unittest.TestCase):
    """⚠️ **The rule issue 13 rests on, and the reason `headline.ts` exists.**

    The video, the thumbnail and the metadata must agree about the day's number. They cannot be *made* to agree by
    keeping three copies that happen to match — they have to share one function, so there is nothing to drift. This
    is the whole content of issue 14's "the featured figure is the headline figure: the same rule, not a new one".
    """

    def test_the_rule_lives_in_one_place(self):
        self.assertIn("export const headline", HEADLINE_SOURCE)

    def test_both_surfaces_call_it_rather_than_keeping_their_own_copy(self):
        for name, source in (("blocks.tsx", BLOCKS_SOURCE), ("Thumbnail.tsx", THUMBNAIL_SOURCE)):
            with self.subTest(file=name):
                self.assertIn("headline(", source)
                self.assertIn("from './headline'", source)

    def test_neither_surface_still_picks_its_own_hardest_move(self):
        """⚠️ A `reduce` over `indexes` written inline is exactly the copy that drifts.

        Scoped to the two functions, not to the files: `blocks.tsx` uses `Math.abs` for a heat cell's tint and would
        make a file-wide assertion pass no matter what the cold open did — an assertion that cannot fail is worse
        than none.
        """
        cold_open = BLOCKS_SOURCE.split("export const ColdOpen")[1].split("export const ")[0]
        thumbnail = code_only(THUMBNAIL_SOURCE)
        for name, body in (("ColdOpen", cold_open), ("Thumbnail", thumbnail)):
            with self.subTest(function=name):
                self.assertNotIn("reduce(", body, "the inline rule is the copy that drifts")
                self.assertNotIn("Math.abs(", body)

    def test_the_rule_is_the_largest_absolute_move(self):
        """Absolute, not largest fall: a +2.1 % day is as much the story as a −2.1 % one, and the pipeline has no
        view about direction. Asserted on the source because the rule is about the *choice*, not the rendering."""
        body = HEADLINE_SOURCE.split("export const headline")[1]
        self.assertIn("Math.abs(", body)
        self.assertIn("reduce(", body)

    def test_it_is_total_where_the_inline_version_was_not(self):
        """⚠️ A still is rendered by a **different command against whatever props it is handed**, so `headline` can
        meet an empty scoreboard in a way `ColdOpen` never could — and `reduce` over an empty array throws."""
        body = HEADLINE_SOURCE.split("export const headline")[1]
        self.assertIn("rows.length === 0", body)

    def test_both_surfaces_survive_an_empty_scoreboard(self):
        """The guard is only worth having if both callers handle the `null` it returns."""
        self.assertIn("featured ?", THUMBNAIL_SOURCE)
        self.assertIn("featured ?", BLOCKS_SOURCE)


class TheMark(unittest.TestCase):
    """Issue 21's numbers, at the still's scale — same corner, larger share of the frame."""

    def test_the_still_s_numbers_are_the_ticket_s(self):
        self.assertIn("export const STILL = {size: 128, inset: 40}", BRAND_SOURCE)
        self.assertIn("RESERVED_STILL = {width: 320, height: 200}", BRAND_SOURCE)

    def test_the_video_s_numbers_are_unchanged(self):
        """⚠️ The refactor must not have moved the brief's own furniture. These two lines are issue 21's verdict
        table, and `test_logo.py` checks them too — deliberately duplicated here so a change shows up in both."""
        self.assertIn("export const BUG = {size: 96, inset: 48}", BRAND_SOURCE)
        self.assertIn("RESERVED = {width: 260, height: 160, left: 1660, top: 0}", BRAND_SOURCE)

    def test_the_plate_scales_so_the_video_s_values_come_out_identically(self):
        """⚠️ One plate at two sizes, derived rather than transcribed twice — and the ratio is chosen so the video's
        numbers are **exactly** what they were. `18 / 96` is 0.1875, so a 96 px plate is still 18 px radius and 18 px
        padding. Without that, a refactor that looks cosmetic would silently restyle every card in the brief."""
        self.assertIn("const PLATE_RATIO = 18 / 96", BRAND_SOURCE)
        self.assertIn("size * PLATE_RATIO", BRAND_SOURCE)

    def test_the_thumbnail_uses_the_still_placement_not_the_bug(self):
        self.assertIn("<Plated mark={mark} placement={STILL} />", BRAND_SOURCE)

    def test_the_mark_is_absent_rather_than_placeholder_when_none_was_supplied(self):
        """⚠️ The supported state, same as the video: no asset means no mark, never an invented wordmark."""
        self.assertIn("if (!mark)", BRAND_SOURCE)



class TheRestState(unittest.TestCase):
    """Issue 14: "rendered from the scene's **settled state**, never from a moment mid-entrance"."""

    def test_the_still_s_camera_has_no_entrance_at_all(self):
        """⚠️ Stronger than "render at a frame after the entrance finished": `from` **is** `to` and the settle is
        zero, so the camera never moves and *every* frame is the settled one. There is no frame the still could be
        caught mid-way through, which is what makes `--frame=0` correct rather than merely convenient."""
        station = STATIONS_SOURCE.split("export const THUMBNAIL")[1]
        self.assertIn("settle: 0,", station)
        froms = re.search(r"from: (rail\([^)]*\)),", station).group(1)
        tos = re.search(r"to: (rail\([^)]*\)),", station).group(1)
        self.assertEqual(froms, tos, "a moving camera has an entrance, and a still must not have one")

    def test_the_still_holds_no_clock_of_its_own(self):
        """⚠️ A thumbnail is a still. `useCurrentFrame` or `enter()` would make the image depend on which frame was
        asked for, and a re-render could land somewhere else entirely."""
        code = code_only(THUMBNAIL_SOURCE)
        self.assertNotIn("useCurrentFrame", code)
        self.assertNotIn("enter(", code)
        self.assertNotIn("Math.random", code)

    def test_every_still_scene_is_a_pure_function_of_the_bundle(self):
        code = code_only(STATIONS_SOURCE.split("export const THUMBNAIL")[1])
        self.assertNotIn("Math.random", code)
        self.assertIn("scene: (bundle) =>", code)

    def test_the_still_is_asked_for_frame_zero(self):
        source = (store.root() / "src" / "market_overview" / "render.py").read_text(encoding="utf-8")
        self.assertIn('"--frame=0"', source)


class TheReservedRegions(unittest.TestCase):
    """⚠️ The platform draws a **duration badge** bottom-right and a **progress bar** across the bottom strip.
    Issue 14 puts the figure centre or upper-centre for exactly this reason."""

    def test_the_figure_is_anchored_to_the_top_rather_than_centred(self):
        """⚠️ A layout decision, not a style one. Centred, the number sat on top of the world and hid it — seven
        bars flattened to a sliver of one. Anchoring the figure to the top leaves the lower band to the world, which
        is the same division of the frame the video's own cards use."""
        code = code_only(THUMBNAIL_SOURCE)
        self.assertIn("justifyContent: 'flex-start'", code)
        self.assertIn("paddingTop:", code)

    def test_the_type_sits_above_the_world_band(self):
        """The type must end before the world begins.

        ⚠️ The numbers are the composition: at 720 px tall the grid starts at roughly **470 px**, so `paddingTop` +
        the label's line + the figure's line has to come in under it. Off-centre by construction — the figure is
        measured, not eyeballed, because the failure it prevents (a bar running up behind a digit, reading as a
        rectangle glitching out of the type) looks like a rendering fault rather than like a layout mistake.
        """
        block = code_only(THUMBNAIL_SOURCE).split("justifyContent: 'flex-start'")[1].split("</AbsoluteFill>")[0]
        padding = int(re.search(r"paddingTop: (\d+)", block).group(1))
        sizes = [int(n) for n in re.findall(r"fontSize: (\d+)", block)]
        self.assertEqual(len(sizes), 2, "the label and the figure")
        label, figure = sizes
        # Lines are ~1.2x their font size in the label's case and 1.0 for the figure, plus the label's margin.
        self.assertLess(padding + label * 1.2 + figure + 10, 470, "the type must leave the lower band to the world")
        self.assertGreater(figure, label, "the figure is the largest element in the frame")

    def test_the_still_s_scrim_is_the_thinner_of_the_two(self):
        """⚠️ **The fix for the first render.** `SCRIM_OPEN` is 0.90 opaque through the middle, and over a palette
        that is deliberately dark that is black — the world vanished and the still lost the day's terrain, its only
        source of daily variety. The still needs its own, much thinner scrim.
        """
        still = re.search(r"SCRIM_STILL =\n((?:.*\n)*?).*?;", THEME_SOURCE).group(1)
        opened = re.search(r"SCRIM_OPEN =\n((?:.*\n)*?).*?;", THEME_SOURCE).group(1)
        lightest_still = min(float(a) for a in re.findall(r"rgba\(11,14,19,([0-9.]+)\)", still))
        lightest_open = min(float(a) for a in re.findall(r"rgba\(11,14,19,([0-9.]+)\)", opened))
        self.assertLess(lightest_still, lightest_open, "the still's scrim must be the thinner of the two")

    def test_the_thumbnail_uses_the_still_scrim_and_the_video_does_not(self):
        self.assertIn("SCRIM_STILL", THUMBNAIL_SOURCE)
        self.assertNotIn("SCRIM_OPEN", code_only(THUMBNAIL_SOURCE))

    def test_every_scrim_stays_within_the_closed_palette(self):
        """A scrim of a different hue would read as a tint. All three are the card background at varying alpha."""
        for name in ("SCRIM_STILL", "SCRIM_OPEN", "SCRIM"):
            match = re.search(rf"export const {name} =\n((?:.*\n)*?).*?;", THEME_SOURCE)
            with self.subTest(scrim=name):
                self.assertIsNotNone(match, f"{name} is missing")
                self.assertIn("rgba(11,14,19,", match.group(1))



class TheFile(unittest.TestCase):
    """Issue 13's package spec, on the Python side."""

    def test_the_filename_carries_the_date_and_the_language(self):
        """⚠️ A file dragged out of its folder still identifies itself — the loss of that property is exactly how an
        English thumbnail gets uploaded beside a Bengali video."""
        self.assertEqual(render.thumbnail_name("2026-10-12", "bn"), "thumbnail-2026-10-12-bn.jpg")

    def test_it_lands_in_the_edition_s_own_folder(self):
        self.assertEqual(
            render.thumbnail_path("2026-10-12", "en").parts[-3:],
            ("2026-10-12", "en", "thumbnail-2026-10-12-en.jpg"),
        )

    def test_the_spec_is_jpeg_at_eighty_eight(self):
        """⚠️ JPEG over PNG, because the platform re-encodes anyway and the limit is bytes rather than fidelity."""
        self.assertEqual(render.JPEG_QUALITY, 88)
        source = (store.root() / "src" / "market_overview" / "render.py").read_text(encoding="utf-8")
        self.assertIn("--image-format=jpeg", source)
        self.assertIn("--jpeg-quality={JPEG_QUALITY}", source)

    def test_the_two_megabyte_ceiling_is_checked_rather_than_trusted(self):
        """⚠️ YouTube's own limit, and the one line of issue 14's spec that nothing else would notice being broken:
        a thumbnail at 3 MB looks completely fine."""
        self.assertEqual(render.MAX_STILL_BYTES, 2 * 1024 * 1024)
        source = (store.root() / "src" / "market_overview" / "render.py").read_text(encoding="utf-8")
        self.assertIn("staging.stat().st_size", source)

    def test_the_still_never_writes_the_package_file_directly(self):
        """⚠️ 0085_11's finding, inherited: `--overwrite` unlinks the target, so a failed still rendered straight at
        the package file would destroy last run's thumbnail."""
        source = (store.root() / "src" / "market_overview" / "render.py").read_text(encoding="utf-8")
        still = source.split("def still(")[1]
        self.assertIn('staging = target.with_name(f".still-{lang}.jpg")', still)
        self.assertIn("staging.replace(target)", still)

    def test_both_editions_are_rendered(self):
        """⚠️ Two stills, one per language — issue 20's parity rule applied to a still. That is why the CLI calls
        the still *inside* the per-edition loop rather than once."""
        cli = (store.root() / "src" / "market_overview" / "cli.py").read_text(encoding="utf-8")
        loop = cli.split("for lang in LANGUAGES:")[1]
        self.assertIn("render.still(day, lang)", loop)

    def test_a_failed_still_fails_the_run(self):
        """⚠️ A language folder missing its thumbnail is an incomplete package, and a folder that *looks* finished is
        worse than one that errors — so the still is inside the same try as the video."""
        cli = (store.root() / "src" / "market_overview" / "cli.py").read_text(encoding="utf-8")
        loop = cli.split("for lang in LANGUAGES:")[1]
        self.assertLess(
            loop.index("render.still(day, lang)"),
            loop.index("except (render.RenderError"),
            "the still must be inside the try, not after it",
        )


if __name__ == "__main__":
    unittest.main()

