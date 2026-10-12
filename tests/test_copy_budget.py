"""The copy budget — 0085_08's hard gate.

⚠️ These tests ask a **browser** for their answers, and that is the point: only the browser knows Kohinoor
Bangla's metrics. An estimate would make the gate measure an arithmetic model of the copy rather than the
copy itself — and Bengali width is not predictable from character count. Measured, `Miscellaneous` is 2.9x
wider in English, and `IT` is 3.25x wider in Bengali.

The rest assert the schedule against the measurement: every slot holds the **longer** edition, and the build
fits the cap.
"""
import json
import re
import unittest

from market_overview import copybudget, store, timeline

DATE = "2026-10-12"
ROOT = store.root()
REMOTION = ROOT / "remotion"

BUNDLE = json.loads((store.dir_for(DATE) / store.FACTS).read_text(encoding="utf-8"))
TABLES = {
    lang: json.loads((REMOTION / f"copy.{lang}.json").read_text(encoding="utf-8")) for lang in ("bn", "en")
}
SOURCE = (REMOTION / "blocks.tsx").read_text(encoding="utf-8")

# The card's content box: 1920 minus `Card`'s 2x96 horizontal padding.
CONTENT = 1728

_measured: dict = {}


def measure(runs: list) -> dict:
    """One browser pass per run-set, cached — browser start-up dominates otherwise."""
    key = tuple(sorted(run.key for run in runs))
    if key not in _measured:
        _measured[key] = copybudget.measure(runs)
    return _measured[key]


def first_column(others: tuple, gap: int) -> int:
    """The width a `1fr` column gets, from its grid template and the column count."""
    return CONTENT - sum(others) - len(others) * gap


def runs_for(group: str, size: int) -> list:
    return [
        copybudget.Run(f"{lang}:{key}", table[group][key], size)
        for lang, table in TABLES.items()
        for key in table[group]
    ]


class Fit(unittest.TestCase):
    """Does anything outgrow the box it is given? The Done When's "a test fails when a label outgrows its
    slot" — a regression guard, because today everything fits, in both editions."""

    def test_the_sector_column_holds_every_sector_label(self):
        self.assertIsNotNone(
            re.search(r"gridTemplateColumns: '1fr 96px 150px repeat\(6, 142px\)'", SOURCE),
            "the sector grid moved — the measured box is no longer the real one",
        )
        box = first_column((96, 150) + (142,) * 6, 4)
        measured = measure(runs_for("sectors", 28))
        over = {k: round(v["width"]) for k, v in measured.items() if v["width"] > box or v["lines"] > 1}
        self.assertEqual(over, {}, f"sector labels over {box}px")

    def test_the_index_column_holds_every_index_label(self):
        self.assertIsNotNone(
            re.search(r"gridTemplateColumns: '1fr 190px repeat\(6, 152px\)'", SOURCE),
            "the index grid moved",
        )
        box = first_column((190,) + (152,) * 6, 6)
        measured = measure(runs_for("indexes", 34))
        over = {k: round(v["width"]) for k, v in measured.items() if v["width"] > box or v["lines"] > 1}
        self.assertEqual(over, {}, f"index labels over {box}px")

    def test_card_titles_fit_the_card(self):
        measured = measure(runs_for("blocks", 46))
        over = {k: round(v["width"]) for k, v in measured.items() if v["lines"] > 1}
        self.assertEqual(over, {}, "a title wrapped")

    def test_the_footer_holds_the_disclosure_beside_the_attribution(self):
        """⚠️ The tightest box in the brief, and it is on **every** card. Measured: English uses 1554.7 of
        1728 px — 173 px of slack — against Bengali's 1148.1. A longer disclosure, or a longer attribution,
        breaks every card at once."""
        runs = []
        for lang, table in TABLES.items():
            runs.append(copybudget.Run(f"{lang}:disclosure", table["disclosure"], 24))
            runs.append(copybudget.Run(f"{lang}:attribution", table["furniture"]["attribution"], 24))
        measured = measure(runs)
        for lang in TABLES:
            used = measured[f"{lang}:disclosure"]["width"] + 32 + measured[f"{lang}:attribution"]["width"]
            self.assertLessEqual(used, CONTENT, f"{lang} footer overflows its row")
            self.assertEqual(measured[f"{lang}:disclosure"]["lines"], 1, f"{lang} disclosure wrapped")

    def test_the_english_footer_is_the_tighter_one(self):
        """Records which edition sets the constraint. The map assumed Bengali runs longer; measured, on the
        longest string in the video it is English by 398 px."""
        runs = []
        for lang, table in TABLES.items():
            runs.append(copybudget.Run(f"{lang}:disclosure", table["disclosure"], 24))
            runs.append(copybudget.Run(f"{lang}:attribution", table["furniture"]["attribution"], 24))
        measured = measure(runs)
        slack = {
            lang: CONTENT
            - (measured[f"{lang}:disclosure"]["width"] + 32 + measured[f"{lang}:attribution"]["width"])
            for lang in TABLES
        }
        self.assertLess(slack["en"], slack["bn"])


class Schedule(unittest.TestCase):
    def test_the_calendar_caps_still_match_the_renderer(self):
        """The budget counts what the card shows. If a cap moves here and not there, the gate quietly
        measures a different card than the one that renders."""
        self.assertEqual(copybudget._calendar_caps(), (8, 6))

    def test_every_slot_holds_the_longer_edition(self):
        """Ticket 20's rule, and the reason the timeline is shared: `max(bn, en)`."""
        cards, _ = copybudget.report(DATE)
        over = {card.key: (card.slot, round(card.required, 1)) for card in cards if card.slot < card.required}
        self.assertEqual(over, {}, f"slots shorter than their reading time: {over}")

    def test_the_build_fits_the_cap(self):
        cards, summary = copybudget.report(DATE)
        self.assertLessEqual(summary["required"], timeline.CAP_SECONDS, "the copy does not fit the cap")
        self.assertLessEqual(summary["slot"], timeline.CAP_SECONDS)

    def test_the_scheduled_slots_are_the_measured_reading_time(self):
        """⚠️ The timeline **is** the measurement, not an independent judgement — so the two must agree. A
        card added, dropped or resized without re-running the budget fails here."""
        cards, _ = copybudget.report(DATE)
        scheduled = {block["key"]: block["seconds"] for block in timeline.running_order(BUNDLE)}
        self.assertEqual(set(scheduled), {card.key for card in cards})
        for card in cards:
            self.assertEqual(scheduled[card.key], card.required, card.key)

    def test_the_two_editions_cost_the_same_in_units(self):
        """A finding, recorded so it is not re-litigated: at these string lengths nothing wraps in either
        edition, so the reading cost is language-independent and `max(bn, en)` holds trivially. The width
        difference is real but never reaches a wrap — which is why the fit tests above exist separately."""
        cards, _ = copybudget.report(DATE)
        differ = {
            card.key: card.by_language for card in cards if card.by_language["bn"] != card.by_language["en"]
        }
        self.assertEqual(differ, {}, f"the editions now differ in units: {differ}")

    def test_the_only_card_the_renderer_has_that_the_budget_does_not_is_the_cut(self):
        """⚠️ Pins 0085_08's cut in **both** places at once. The renderer still knows how to draw the heat
        map; the schedule deliberately does not ask it to. If someone schedules it again, or adds a new
        block without costing it, this is what says so."""
        registry = (store.root() / "remotion" / "MarketBrief.tsx").read_text(encoding="utf-8")
        available = set(re.findall(r"^\s+(\w+): blocks\.\w+,", registry, re.MULTILINE))
        scheduled = {block["key"] for block in timeline.running_order(BUNDLE)}

        self.assertTrue(available, "the registry scan found nothing — it has stopped reading the renderer")
        self.assertEqual(available - scheduled, {"heat_map"}, "the cut is no longer the only exclusion")
        self.assertEqual(scheduled - available, set(), "the schedule asks for a block the renderer lacks")


if __name__ == "__main__":
    unittest.main()

