"""The label tables.

Both editions render from one facts bundle, so the *only* thing that can legitimately differ between
them is the words. That makes the tables worth pinning harder than they look: a key present in one table
and absent from the other shows up as a raw slug in a finished video, and the renderer's slug fallback
means it does so **without crashing** — so nothing else in the suite would ever notice.

What these tests can prove is structure and script. Whether the Bengali reads as native wording rather
than translated wording is a human judgement, and 0085_07 marks it as one.
"""
import io
import json
import pathlib
import re
import shutil
import tempfile
import unittest
from unittest import mock

from market_overview import render

ROOT = pathlib.Path(__file__).resolve().parents[1]
REMOTION = ROOT / "remotion"

# The Bengali block, U+0980-U+09FF. Bengali numerals U+09E6-U+09EF fall inside it, which is why a
# label like `নিফটি ৫০` counts as Bengali without carrying a single Bengali letter.
BENGALI = re.compile(r"[\u0980-\u09FF]")


def table(lang: str) -> dict:
    return json.loads((REMOTION / f"copy.{lang}.json").read_text(encoding="utf-8"))


BN = table("bn")
EN = table("en")

TABLES = (("bn", BN), ("en", EN))


def groups(t: dict) -> dict:
    return {key: value for key, value in t.items() if isinstance(value, dict)}


class Shape(unittest.TestCase):
    def test_the_two_tables_are_key_for_key_identical(self):
        bn, en = groups(BN), groups(EN)
        self.assertEqual(set(bn), set(en), "group names differ between the tables")
        for group in sorted(bn):
            self.assertEqual(set(bn[group]), set(en[group]), group)

    def test_every_group_the_renderer_asks_for_exists_in_both(self):
        """Derived from the components rather than hand-listed, so a card added in a later task cannot
        quietly introduce a group that one table is missing."""
        asked: set[str] = set()
        for path in sorted(REMOTION.glob("*.tsx")):
            for group in re.findall(r"copy\.(\w+)", path.read_text(encoding="utf-8")):
                # `copy.bn.json` / `copy.en.json` are import paths, not label groups.
                if group not in ("bn", "en"):
                    asked.add(group)
        self.assertTrue(asked, "no copy.* references found — the scan, not the tables, has broken")
        for group in sorted(asked):
            self.assertIn(group, BN, f"{group} missing from Bengali")
            self.assertIn(group, EN, f"{group} missing from English")

    def test_sector_labels_cover_the_whole_taxonomy_not_just_todays_board(self):
        """Ticket 26 maps TradingView's twenty global sectors, but only thirteen fit one scoreboard. The
        tail rotates as the day moves, so a label missing today is a slug on some future date."""
        for lang, t in TABLES:
            self.assertEqual(len(t["sectors"]), 20, lang)

    def test_sector_labels_cover_the_keys_a_bundle_can_emit(self):
        facts = json.loads(
            (ROOT / "store" / "2026-10-12" / "facts.json").read_text(encoding="utf-8")
        )
        emitted = {row["sector_key"] for row in facts["sectors"]}
        self.assertTrue(emitted, "the golden bundle carries no sector keys to check against")
        for lang, t in TABLES:
            self.assertEqual(emitted - set(t["sectors"]), set(), f"{lang} unlabelled")

    def test_no_underscored_label_renders_as_its_own_key(self):
        """The renderer falls back to the raw key when a label is missing, so a key-shaped label would
        make a present key indistinguishable from an absent one.

        Only **multi-token** keys are checked, and compared raw. Those are the ones whose fallback is
        unmistakably a slug: `technology_services` on screen is always a bug. Single-token keys are left
        alone because `of` and `Sensex` are legitimate labels that happen to resemble their keys, and no
        mechanical rule separates those from a missing one — that leftover risk is what 0085_07's human
        read is for."""
        for lang, t in TABLES:
            for group, labels in groups(t).items():
                for key, label in labels.items():
                    self.assertTrue(label.strip(), f"{lang} {group}.{key} is blank")
                    self.assertNotIn("_", label, f"{lang} {group}.{key} leaks a code-style key")
                    if "_" in key:
                        self.assertNotEqual(
                            label.strip(), key, f"{lang} {group}.{key} renders as the key itself"
                        )


    def test_interpolated_labels_are_phrases_and_keep_their_placeholders(self):
        """A label carrying a `{...}` token is a *phrase*: the token marks where a value goes, and the reason it is a
        phrase rather than a word is that **word order differs between the languages** and cannot be fixed in shared
        layout code. `of 497` is not expressible as `of` + `497` in Bengali, where the postposition follows the noun —
        and the long date is the same problem twice over, `{month} {day}` in English and `{day} {month}` in Bengali.

        A table that dropped a token would render a note with no value in it and still read as a sentence, so both
        tables are required to carry the **same tokens** for the same label."""
        tokens = {
            lang: {
                (group, key): sorted(re.findall(r"\{(\w+)\}", label))
                for group, labels in groups(t).items()
                for key, label in labels.items()
                if "{" in label
            }
            for lang, t in TABLES
        }
        self.assertEqual(set(tokens["bn"]), set(tokens["en"]), "the tables interpolate different labels")
        self.assertTrue(tokens["bn"], "no interpolated label — a phrase has been flattened back to a word")
        for spot in sorted(tokens["bn"]):
            with self.subTest(label=spot):
                self.assertEqual(tokens["bn"][spot], tokens["en"][spot], "a table lost or gained a placeholder")


class Script(unittest.TestCase):
    def test_the_english_table_carries_no_bengali_glyph(self):
        """A stray Bengali glyph in the English table is a label copied from the wrong table. It would
        render as tofu in a font with no Bengali coverage — visible only to someone watching the English
        edition, which on this side of the project nobody does."""
        for group, labels in groups(EN).items():
            for key, label in labels.items():
                self.assertIsNone(BENGALI.search(label), f"en {group}.{key}")

    def test_most_bengali_labels_are_actually_bengali(self):
        """Not all of them: ticket 20 keeps domain acronyms as they are — `Nifty`, `Sensex`, `FII/FPI`,
        `DII` — and glossing them would be worse than leaving them. But the bulk must be Bengali, or the
        table has been filled in from the English one."""
        labels = [label for t in groups(BN).values() for label in t.values()]
        bengali = [label for label in labels if BENGALI.search(label)]
        self.assertGreaterEqual(len(bengali), int(len(labels) * 0.6))

    def test_the_disclosures_are_two_different_strings(self):
        """The Bengali disclosure is a deliverable in its own right, not the English sentence twice.
        This guards the degenerate case only — that the wording *reads as native* is the human gate in
        0085_07, and no test can hold that."""
        self.assertTrue(BN["disclosure"].strip())
        self.assertTrue(EN["disclosure"].strip())
        self.assertNotEqual(BN["disclosure"], EN["disclosure"])
        self.assertIsNotNone(BENGALI.search(BN["disclosure"]))
        self.assertIsNone(BENGALI.search(EN["disclosure"]))

    def test_the_disclosure_is_verbatim_from_ticket_01(self):
        """Copied, not retyped. The wording is settled and was argued over; a silent drift in a risk
        disclosure is the one edit nobody would catch by reading a diff."""
        self.assertEqual(
            BN["disclosure"],
            "শিক্ষামূলক তথ্য · কোনো বিনিয়োগ পরামর্শ বা সুপারিশ নয় · শেয়ার বাজারে বিনিয়োগে ঝুঁকি আছে",
        )
        self.assertEqual(
            EN["disclosure"],
            "Educational only · Not investment advice or a recommendation · "
            "Investments in securities markets are subject to risk",
        )


class _StubProcess:
    """The slice of `subprocess.Popen` that `render._stream` touches, and nothing more.

    ⚠️ `_stream` streams the render rather than capturing it, so this test must stub `Popen`, not `run`: the fake
    is iterated line by line, closed, and waited on.
    """

    def __init__(self, returncode: int):
        self.stdout = io.StringIO("")
        self.returncode = returncode

    def wait(self, timeout: float | None = None) -> int:
        return self.returncode

    def kill(self) -> None:  # pragma: no cover - the timeout path is covered in tests/test_render.py
        pass


class Seam(unittest.TestCase):
    """What the renderer hands Remotion.

    This lives beside the tables because it guards the rule the tables are defined by: a label table is
    **not** part of the facts bundle and must never become part of it.
    """

    def test_the_render_props_carry_the_bundle_verbatim_and_the_language_beside_it(self):
        """⚠️ Ticket 20's parity rule rests on exactly this and nothing else.

        If the language — or anything else language-specific — is ever written *into* the bundle, the two
        editions stop reading the same numbers. The symptom would be a Bengali figure that differs from the
        English one on the same date, which is the one thing the whole bilingual design forbids, and it
        would appear in a finished video rather than in a test.
        """
        bundle = json.loads(
            (ROOT / "store" / "2026-10-12" / "facts.json").read_text(encoding="utf-8")
        )

        tmp = tempfile.mkdtemp(prefix="market-overview-test-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        # ⚠️ Redirected, so this test never writes near `output/` — the hand-rendered 175 s MP4 for the
        # golden date lives there and is not reproducible in a unit test's runtime.
        target = pathlib.Path(tmp) / "market-brief-2026-10-12-bn.mp4"

        seen: dict = {}

        def fake_popen(command, **_kwargs):
            wrapper = pathlib.Path(
                next(arg for arg in command if arg.startswith("--props=")).split("=", 1)[1]
            )
            seen["name"] = wrapper.name
            seen["during"] = wrapper.exists()
            seen["props"] = json.loads(wrapper.read_text(encoding="utf-8"))
            pathlib.Path(next(arg for arg in command if arg.endswith(".mp4"))).write_bytes(b"stub")
            return _StubProcess(0)

        with (
            mock.patch.object(render, "video_path", lambda date, lang: target),
            mock.patch.object(render.subprocess, "Popen", fake_popen),
            # ⚠️ Pointed at an empty folder, so this test asserts the same thing whether or not the operator
            # has dropped a mark into the real `resource/brief/`. A test whose result depends on a licensed asset
            # being present is a test that fails for the wrong reason on someone else's machine.
            # ⚠️ It patches the **resolver**, not a constant: the bed and the mark both go through
            # `render.resource_dir()`, so one patch keeps them resolving to the same folder — which is the
            # property the old `RESOURCE` constant could only keep by convention.
            mock.patch.object(render, "resource_dir", return_value=pathlib.Path(tmp)),
        ):
            rendered = render.render("2026-10-12", "bn")

        self.assertEqual(seen["props"]["bundle"], bundle, "the bundle was altered on its way through")
        self.assertEqual(seen["props"]["lang"], "bn")
        # ⚠️ `mark` joined this set in 0085_10, for the **same** reason `lang` is here: the mark is not a fact.
        # It rides beside the bundle so both editions receive the identical one, which is what keeps the
        # bilingual pair honest at the branding layer (issue 21).
        self.assertEqual(
            set(seen["props"]), {"bundle", "lang", "mark"}, "the props carry more than they should"
        )
        self.assertNotIn("lang", bundle, "the language has leaked into the facts bundle")
        self.assertNotIn("mark", bundle, "the mark has leaked into the facts bundle")

        # ⚠️ No asset, no mark — and **no failure**. The mark is the operator's to drop in, and until they do
        # the brief still renders; a missing logo is a brief without branding, not a broken run.
        self.assertIsNone(seen["props"]["mark"])

        # Scoped to the render and cleaned up after it, so a package can never contain the wrapper.
        self.assertEqual(seen["name"], ".props-bn.json")
        self.assertTrue(seen["during"])
        self.assertFalse(target.parent.joinpath(".props-bn.json").exists())
        self.assertEqual(rendered, target)

    def test_the_bundle_is_the_same_file_for_both_editions(self):
        """The language is a render argument, not a bundle field, so both editions resolve to the same
        bundle path. If they ever diverge, the editions are reading different data by construction."""
        both = {lang: render.video_path("2026-10-12", lang).parent for lang in ("bn", "en")}
        self.assertEqual(len(set(both.values())), 2, "the editions share an output directory")
        source = json.loads(
            (ROOT / "store" / "2026-10-12" / "facts.json").read_text(encoding="utf-8")
        )
        # One file, read twice. Its own key set is language-neutral — checked here rather than assumed.
        self.assertNotIn("lang", source)
        self.assertNotIn("language", source)


if __name__ == "__main__":
    unittest.main()

