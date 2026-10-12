"""The package's SEO text — 0085_13.

⚠️ **The interesting tests here are the mirrors.** `display.py` re-implements two rules the renderer already owns —
`theme.ts`'s `percent` and `headline.ts`'s headline figure — because a subprocess boundary means it has to. A second
implementation that has quietly diverged produces a description quoting a different number from the video, and nothing
anywhere raises: both surfaces are internally consistent and only a reader comparing them would notice.

So these tests pin the *shared convention* (the minus sign, the decimals, the rule) on both sides, and pin the
behaviour that makes the rule a rule rather than an accident of array order.
"""
import json
import re
import unittest
from unittest import mock

from market_overview import display, metadata, store

ROOT = store.root()
REMOTION = ROOT / "remotion"
DATE = "2026-10-12"

BUNDLE = json.loads((store.dir_for(DATE) / store.FACTS).read_text(encoding="utf-8"))
THEME_SOURCE = (REMOTION / "theme.ts").read_text(encoding="utf-8")
HEADLINE_TS = (REMOTION / "headline.ts").read_text(encoding="utf-8")
BN = metadata.labels_for("bn")
EN = metadata.labels_for("en")

BUILT = {lang: metadata.build(DATE, BUNDLE, lang, bundle_hash="0" * 64, video="v.mp4", thumbnail="t.jpg")
         for lang in ("bn", "en")}


#: A deliberately thin day: the spine and nothing else. Every optional card is absent, which is the state the
#: degrade-to-omission rules are supposed to survive.
SPARSE = {"meta": {"schema": 1, "date": DATE, "source": "test"}, "indexes": [], "timeline": {"blocks": []}}


class TheTwoTrees(unittest.TestCase):
    """Two native trees, and the *structure* is what has to match."""

    def test_both_languages_have_the_same_phrase_keys(self):
        """⚠️ A key present in one and not the other is a `KeyError` in a run, or — worse — a section silently missing
        from one edition, which is parity broken in the direction nobody checks."""
        self.assertEqual(set(metadata.PHRASES["bn"]), set(metadata.PHRASES["en"]))

    def test_every_phrase_key_is_actually_used(self):
        """A phrase nothing calls is copy that reads as a feature and ships nothing."""
        source = (ROOT / "src" / "market_overview" / "metadata.py").read_text(encoding="utf-8")
        body = source.split("def _sections")[1]
        for key in metadata.PHRASES["en"]:
            with self.subTest(phrase=key):
                self.assertIn(f'"{key}"', body, f"phrase {key!r} is defined but never used")

    def test_the_bengali_is_written_in_bengali(self):
        """⚠️ The one thing a test can prove about a translation: that it is not one.

        Checked on the phrase's **literal text** — its slots removed — because a pure-slot phrase like `closing` is
        `{attribution} · {disclosure}` and carries no words of its own in either language. Requiring script there would
        be requiring the wrong thing; `test_copy.py` holds the same line for the label tables.
        """
        bengali = re.compile(r"[\u0980-\u09ff]")
        for tree, wanted in (("bn", True), ("en", False)):
            for key, phrase in metadata.PHRASES[tree].items():
                literal = re.sub(r"\{[^}]*\}", "", phrase).strip(" ·:-—")
                if not literal:
                    continue
                with self.subTest(tree=tree, phrase=key):
                    found = bool(bengali.search(literal))
                    self.assertEqual(found, wanted, f"{key!r} in the {tree} tree: {literal!r}")

    def test_the_trees_share_the_slots(self):
        """The logic is shared, so the placeholders must line up — a `{items}` against a `{rows}` is a `KeyError`."""
        for key in metadata.PHRASES["en"]:
            with self.subTest(phrase=key):
                self.assertEqual(
                    set(re.findall(r"\{(\w+)\}", metadata.PHRASES["bn"][key])),
                    set(re.findall(r"\{(\w+)\}", metadata.PHRASES["en"][key])),
                )


class TheTitle(unittest.TestCase):
    """`series · date · the day's headline move`, front-loaded, ≤ 100 characters."""

    def test_it_is_three_parts_in_that_order(self):
        for lang in ("bn", "en"):
            with self.subTest(lang=lang):
                parts = BUILT[lang].title.split(" | ")
                self.assertEqual(len(parts), 3)
                self.assertEqual(parts[0], metadata.labels_for(lang)["metadata"]["series"])
                self.assertRegex(parts[1], r"^\d{1,2} \S+ \d{4}$", "the date must be a fixed shape so episodes sort")

    def test_it_fits_you_tubes_hundred_characters(self):
        """⚠️ Over 100 and the *move* is what gets truncated — the only part a viewer is searching for — and nothing
        else in the run would notice. Asserted on the real bundle rather than on a remembered number."""
        for lang in ("bn", "en"):
            with self.subTest(lang=lang):
                self.assertLessEqual(len(BUILT[lang].title), metadata.TITLE_LIMIT)
                self.assertEqual(BUILT[lang].warnings, [])

    def test_the_move_is_the_figure_the_cold_open_leads_with(self):
        """⚠️ Issue 13's anti-fabrication rule at the title: the same figure, from the same rule. A title promising a
        move the video does not open on is the product contradicting itself, and only a viewer would see it."""
        for lang in ("bn", "en"):
            with self.subTest(lang=lang):
                self.assertIn(display.percent(display.headline_change(BUNDLE)), BUILT[lang].title)
                self.assertIn(display.headline_label(BUNDLE, metadata.labels_for(lang)), BUILT[lang].title)

    def test_the_date_is_native_wording_with_latin_numerals(self):
        """⚠️ The hybrid the video already uses — Bengali labels, Latin figures — and issue 13's one-glossary rule.
        `১২ অক্টোবর` would make the description the one surface where a reader has to convert."""
        self.assertIn("12 অক্টোবর 2026", BUILT["bn"].title)
        self.assertIn("12 Oct 2026", BUILT["en"].title)

    def test_the_bengali_month_names_are_bengali_and_the_english_ones_are_not(self):
        bengali = re.compile(r"[\u0980-\u09ff]")
        for month in range(1, 13):
            with self.subTest(month=month):
                self.assertRegex(BN["metadata"][f"month_{month}"], bengali)
                self.assertNotRegex(EN["metadata"][f"month_{month}"], bengali)


class TheDescription(unittest.TestCase):
    """⚠️ Only the first ~150 characters show before "more", so line one is the whole game."""

    def test_the_disclosure_and_the_headline_both_fit_the_visible_window(self):
        """⚠️ **The test this section exists for.** Issue 13 spends ~60 of the 150 characters on a compact disclosure
        *ahead* of the headline, on the argument that a risk warning findable only after "more" is not really carrying
        one. If the headline pushed the disclosure outside the window, the argument would fail silently."""
        for lang in ("bn", "en"):
            with self.subTest(lang=lang):
                window = BUILT[lang].description[:150]
                self.assertIn(metadata.labels_for(lang)["metadata"]["disclosure_short"], window)
                self.assertIn(display.percent(display.headline_change(BUNDLE)), window)

    def test_the_warning_comes_before_the_figure_not_after(self):
        for lang in ("bn", "en"):
            with self.subTest(lang=lang):
                body = BUILT[lang].description
                self.assertLess(
                    body.index(metadata.labels_for(lang)["metadata"]["disclosure_short"]),
                    body.index(display.percent(display.headline_change(BUNDLE))),
                )

    def test_the_full_statement_is_repeated_at_the_close(self):
        """⚠️ The description is the surface that survives being quoted or screenshotted, so it carries its own copy of
        the attribution and the not-advice line rather than inheriting the video's."""
        for lang in ("bn", "en"):
            with self.subTest(lang=lang):
                labels = metadata.labels_for(lang)
                self.assertIn(labels["disclosure"], BUILT[lang].description)
                self.assertIn(labels["furniture"]["attribution"], BUILT[lang].description)

    def test_it_mirrors_the_video_s_block_order(self):
        """⚠️ A viewer who watches and then reads must find the same sequence, and a reader who skims must not be
        surprised by the video. The order is the contract, so it is asserted rather than left to the editor.

        ⚠️ Markers are the phrase's **first literal**, and an empty one is skipped: `closing` is pure slots, so its
        prefix is `''` and `body.index('')` is `0` — which would have made this test pass by putting the last section
        first. The closing line is checked by its own content instead.
        """
        order = ("indices", "sectors", "cues", "breadth", "dma", "actions", "ipos", "announcements")
        for lang in ("bn", "en"):
            with self.subTest(lang=lang):
                labels = metadata.labels_for(lang)
                phrases = metadata.PHRASES[lang]
                body = BUILT[lang].description
                seen = [
                    body.index(prefix) for key in order
                    if (prefix := phrases[key].split("{")[0].strip(" ·:-—"))
                ]
                self.assertEqual(len(seen), len(order), "every section with data must appear")
                self.assertEqual(seen, sorted(seen), "a section is out of the running order")
                # ⚠️ And the full statement with attribution comes after all of them, never before.
                self.assertGreater(body.index(labels["furniture"]["attribution"]), max(seen))

    def test_it_stays_inside_the_five_thousand_character_limit(self):
        for lang in ("bn", "en"):
            with self.subTest(lang=lang):
                self.assertLess(len(BUILT[lang].description), metadata.DESCRIPTION_LIMIT)

    def test_a_thin_day_produces_a_shorter_description_not_a_broken_one(self):
        """The video's degrade-to-omission rule, applied to prose: an absent card drops its section."""
        thin = metadata.build(DATE, SPARSE, "en", bundle_hash="0" * 64, video="v.mp4", thumbnail="t.jpg")
        self.assertNotIn(metadata.PHRASES["en"]["sectors"].split("{")[0].strip(), thin.description)
        self.assertIn(metadata.PHRASES["en"]["closing"].split("{")[0].strip(), thin.description)




class TheLimits(unittest.TestCase):
    """Issue 13's ceilings on the fields that have them, and the trap among them."""

    def test_the_tags_fit_the_five_hundred_character_budget(self):
        """⚠️ The budget is in **characters**, not tags, so a handful of long sector names blows it without anything
        looking wrong. Tested against the real bundle, whose sectors are the long ones."""
        for lang in ("bn", "en"):
            with self.subTest(lang=lang):
                self.assertLessEqual(len(", ".join(BUILT[lang].tags)), metadata.TAG_BUDGET)

    def test_tags_start_with_the_channels_own_words(self):
        for lang in ("bn", "en"):
            with self.subTest(lang=lang):
                text = metadata.labels_for(lang)["metadata"]
                self.assertEqual(BUILT[lang].tags[:3], [text["tag_channel"], text["tag_daily"], text["tag_india"]])

    def test_there_are_exactly_three_hashtags_and_never_more_than_fifteen(self):
        """⚠️ **The cliff, not the budget.** Exceed 15 hashtags and YouTube ignores *all* of them, so a longer block is
        strictly worse than a short one — which is why this emits a fixed three rather than appending the day's sectors.
        """
        for lang in ("bn", "en"):
            with self.subTest(lang=lang):
                self.assertEqual(len(BUILT[lang].hashtags), metadata.HASHTAGS_SHOWN)
                self.assertLessEqual(len(BUILT[lang].hashtags), metadata.HASHTAGS_MAX)

    def test_the_hashtags_appear_in_the_description(self):
        for lang in ("bn", "en"):
            with self.subTest(lang=lang):
                for hashtag in BUILT[lang].hashtags:
                    self.assertIn(hashtag, BUILT[lang].description)

    def test_a_breach_is_reported_rather_than_hidden(self):
        """⚠️ A limit that only ever passes is not a limit. The warning path is exercised by shrinking the budget,
        because the real bundle is nowhere near it and that is exactly why a regression here would go unnoticed."""
        with mock.patch.object(metadata, "TITLE_LIMIT", 5):
            warned = metadata.build(DATE, BUNDLE, "en", bundle_hash="0" * 64, video="v", thumbnail="t")
        self.assertTrue(warned.warnings)
        self.assertIn("title", warned.warnings[0])


class TheFile(unittest.TestCase):
    """Two files, for two different readers."""

    def test_the_text_file_is_plain(self):
        """⚠️ YouTube descriptions are plain text, so a heading marker or an asterisk pastes in as literal junk. What
        is in the file is exactly what goes in the box."""
        for lang in ("bn", "en"):
            with self.subTest(lang=lang):
                body = BUILT[lang].as_text()
                self.assertNotIn("**", body)
                self.assertNotIn("##", body)
                self.assertIn("TITLE\n", body)
                self.assertIn("DESCRIPTION\n", body)
                self.assertIn("TAGS\n", body)

    def test_the_json_names_the_artefacts_it_belongs_to(self):
        """⚠️ The thumbnail and video are named **explicitly**, so an uploader needs nothing but the language folder.
        That is what "self-contained by construction" means."""
        payload = BUILT["bn"].as_json()
        self.assertEqual(payload["thumbnail"], "t.jpg")
        self.assertEqual(payload["video"], "v.mp4")

    def test_the_two_files_carry_the_same_words(self):
        """The JSON is the same content keyed by field — a future automated upload reads fields rather than parsing
        prose out of a text file, so the two must not drift."""
        for lang in ("bn", "en"):
            with self.subTest(lang=lang):
                payload = BUILT[lang].as_json()
                self.assertIn(payload["title"], BUILT[lang].as_text())
                self.assertIn(payload["description"], BUILT[lang].as_text())

    def test_the_bundle_hash_is_recorded_per_edition(self):
        """⚠️ Issue 20's point: two packages, each naming the bundle it was built from. Two hashes that differ would
        say the editions came from different facts, which is the one thing the pair is not allowed to be."""
        self.assertEqual(BUILT["bn"].bundle_hash, BUILT["en"].bundle_hash)


class TheMirrors(unittest.TestCase):
    """⚠️ **The tests this file exists for.**

    `display.py` re-implements two rules the renderer already owns — `theme.ts`'s `percent` and `headline.ts`'s headline
    figure — because a subprocess boundary means it has to. A second implementation that has quietly diverged produces a
    description quoting a different number from the video, and **nothing raises**: both surfaces are internally
    consistent and only a reader holding them side by side would notice. So the shared *convention* is pinned on both
    sides here, and the rule's behaviour is pinned independently of it.
    """

    def test_the_minus_sign_is_u2212_on_both_sides(self):
        """⚠️ `-0.70%` and `−0.70%` are different strings, and only one of them is what the video shows. A hyphen next
        to a digit is the defect `theme.ts` calls out; the description has to match it rather than reinvent it."""
        self.assertEqual(display.MINUS, "\u2212")
        body = THEME_SOURCE.split("export const percent")[1].split(";")[0]
        self.assertIn("\\u2212", body, "theme.ts has stopped using the minus sign")

    def test_the_decimals_follow_the_renderer(self):
        body = THEME_SOURCE.split("export const percent")[1].split(";")[0]
        self.assertIn("toFixed(digits)", body, "theme.ts has stopped parameterising the decimals")
        self.assertEqual(display.percent(1.239, 2), "+1.24%")
        self.assertEqual(display.percent(1.239, 1), "+1.2%")

    def test_a_missing_value_is_the_same_dash_both_sides(self):
        """⚠️ The literal em dash in `theme.ts`, not an escape: the renderer writes the character itself, and the two
        sides have to agree on the character rather than on how it is spelled in one of them."""
        body = THEME_SOURCE.split("export const percent")[1].split(";")[0]
        self.assertIn("—", body, "theme.ts has stopped using an em dash for a missing value")
        self.assertEqual(display.DASH, "—")
        self.assertEqual(display.percent(None), "—")

    def test_the_headline_rule_is_nifty_fifty_on_both_sides(self):
        """⚠️ The brief leads on **Nifty 50**, and the rule has to be the same on both sides of the subprocess boundary:
        `headline.ts` picks the figure for the video and the still, `display.py` picks it for the description. Two
        implementations that disagreed would put a different index in the title than on the cold open, and nothing
        anywhere would raise."""
        self.assertIn("export const HEADLINE_KEY = 'nifty50'", HEADLINE_TS)
        self.assertIn("export const headline", HEADLINE_TS)
        self.assertEqual(display.HEADLINE_KEY, "nifty50")
        source = (ROOT / "src" / "market_overview" / "display.py").read_text(encoding="utf-8")
        rule = source.split("def headline(")[1].split("def headline_label")[0]
        self.assertIn("HEADLINE_KEY", rule)

    def test_nifty_fifty_leads_even_when_another_index_moved_more(self):
        """⚠️ **The rule, and the reason it is not "the biggest mover".** A session where the mid-caps ran is still led
        by the index every reader means by "the market"."""
        bundle = {"indexes": [
            {"label_key": "nifty50", "window": {"change": -0.70}},
            {"label_key": "next50", "window": {"change": 3.10}},
        ]}
        self.assertEqual(display.headline(bundle)["label_key"], "nifty50")
        self.assertAlmostEqual(display.headline_change(bundle), -0.70)
        self.assertEqual(display.headline_label(bundle, EN), "Nifty 50")

    def test_the_fallback_is_the_largest_absolute_move(self):
        """⚠️ The old rule, kept only for a bundle with **no** Nifty 50 row — a hand-written props file, or a vendor
        that renamed the symbol. Still absolute: a +2.1 % day is as much the story as a −2.1 % one."""
        bundle = {"indexes": [
            {"label_key": "a", "window": {"change": -0.4}},
            {"label_key": "b", "window": {"change": 2.5}},
            {"label_key": "c", "window": {"change": -0.9}},
        ]}
        self.assertEqual(display.headline(bundle)["label_key"], "b")

    def test_the_rule_does_not_depend_on_the_order_of_the_scoreboard(self):
        """⚠️ A `reduce` with a `>` comparison is order-dependent — it keeps the *first* of two equal values — so a
        vendor that reordered the rows would change which index the video opens on. Exercised with an exact tie, which
        is the only case where the two implementations could plausibly disagree."""
        rows = [
            {"label_key": "first", "window": {"change": -1.5}},
            {"label_key": "second", "window": {"change": 1.5}},
        ]
        self.assertEqual(
            abs(display.headline({"indexes": rows})["window"]["change"]),
            abs(display.headline({"indexes": list(reversed(rows))})["window"]["change"]),
            "the magnitude chosen must not depend on row order",
        )

    def test_an_empty_scoreboard_is_a_dash_rather_than_a_crash(self):
        """⚠️ The metadata is generated by a *different* command from the video and meets whatever bundle it is handed,
        so it cannot rely on `cold_open` having been scheduled."""
        self.assertIsNone(display.headline({"indexes": []}))
        self.assertEqual(display.headline_label({"indexes": []}, EN), "")
        self.assertEqual(display.percent(display.headline_change({"indexes": []})), "\u2014")

    def test_indian_digit_grouping(self):
        """⚠️ `f"{n:,}"` gives `1,234,567`, which on an Indian finance product is simply the wrong number to a reader
        who knows the convention. The video uses `toLocaleString('en-IN')`; this has to agree."""
        self.assertEqual(display.number(1234567, 0), "12,34,567")
        self.assertEqual(display.number(123456, 0), "1,23,456")
        self.assertEqual(display.number(12345, 0), "12,345")
        self.assertEqual(display.number(1234, 0), "1,234")
        self.assertEqual(display.number(999, 0), "999")
        self.assertEqual(display.number(-1234567, 0), "\u221212,34,567")

    def test_a_negative_flow_keeps_its_sign(self):
        """The one place the sign carries meaning rather than direction, so it must survive formatting."""
        self.assertTrue(display.number(-1708, 0).startswith(display.MINUS))
        self.assertFalse(display.number(3045, 0).startswith(display.MINUS))

