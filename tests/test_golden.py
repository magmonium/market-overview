"""The recorded date rebuilds **exactly** from its own snapshot.

This is 0085_05's fourth Done When, and more usefully the **rebuild promise** ADR 0003 makes:
`store/<date>/raw/` plus the parsers reconstruct `store/<date>/facts.json` with **no network**. If
this ever fails, the snapshot has stopped being sufficient to rebuild a day — which is the whole
reason the raw responses are kept.

⚠️ `tradingview.parse_snapshot` must be handed the column list, because the vendor's response
carries the values but **not** the column names. The snapshot alone cannot name its own fields.
"""
import datetime
import json
import pathlib
import unittest
import urllib.request
from unittest import mock

from market_overview import facts, universe
from market_overview.fetch import bse, tradingview

RECORDED = pathlib.Path(__file__).resolve().parents[1] / "store" / "2026-10-12"
SESSION = datetime.date(2026, 10, 12)
UNTIL = SESSION + datetime.timedelta(days=7)


def raw(name: str) -> bytes:
    return (RECORDED / "raw" / f"{name}.json").read_bytes()


def payload(name: str):
    return json.loads(raw(name))


def _strings(node, path=""):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _strings(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _strings(value, f"{path}[{index}]")
    elif isinstance(node, str):
        yield path, node


class Golden(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (RECORDED / "facts.json").exists():
            raise unittest.SkipTest(f"no recorded snapshot at {RECORDED}")
        cls.golden = json.loads((RECORDED / "facts.json").read_text(encoding="utf-8"))

    def rebuild(self) -> dict:
        return facts.build(
            RECORDED.name,
            indexes=tradingview.parse_snapshot(
                "tradingview-indexes", raw("tradingview-indexes"), tradingview.INDEX_COLUMNS
            ),
            world=tradingview.parse_snapshot(
                "tradingview-universe", raw("tradingview-universe"), tradingview.UNIVERSE_COLUMNS
            ),
            broader=tradingview.parse_snapshot(
                "tradingview-broader",
                raw("tradingview-broader"),
                ("close",) + tradingview.WINDOWS,
            ),
            dependencies=tradingview.parse_snapshot(
                "tradingview-dependencies",
                raw("tradingview-dependencies"),
                tradingview.DEPENDENCY_COLUMNS,
            ),
            flows=bse.net_flows(payload("CategoryTurnover")),
            actions=bse.actions_in_window(payload("DefaultData"), SESSION, UNTIL),
            ipos=bse.openings_in_window(payload("IPO_HomePageDetail"), SESSION, UNTIL),
            announcements=bse.latest_announcements(payload("CorpAnn")),
        )

    def test_the_bundle_rebuilds_exactly(self):
        self.assertEqual(self.rebuild(), self.golden)

    def test_the_rebuild_touches_no_network(self):
        """The strongest form of the promise: block both transports and it still rebuilds."""
        offline = mock.patch.object(
            urllib.request, "urlopen", side_effect=AssertionError("network was reached")
        )
        blocked = mock.patch.object(
            bse._requests, "get", side_effect=AssertionError("network was reached")
        )
        with offline, blocked:
            self.assertEqual(self.rebuild(), self.golden)

    def test_every_block_of_the_fourteen_is_present(self):
        """Ten blocks; the four still to come are renderer-side. A missing key means a card
        whose source silently vanished — the failure the omission rule exists to make visible."""
        self.assertEqual(
            sorted(self.golden),
            [
                "announcements",
                "breadth",
                "broader",
                "corporate_actions",
                "dependencies",
                "dma",
                "flows",
                "indexes",
                "ipos",
                "leaders",
                "meta",
                "most_active",
                "sectors",
                "timeline",
            ],
        )

    def test_the_floor_is_the_whole_universe_here(self):
        """497 members is the measured Nifty 500 — the floor the volume rules depend on."""
        self.assertEqual(self.golden["breadth"]["universe"], 497)
        self.assertEqual(self.golden["breadth"]["counted"], 497)

    def test_the_sector_cut_is_thirteen(self):
        self.assertEqual(len(self.golden["sectors"]), universe.SECTOR_COUNT)
        self.assertEqual(self.golden["sectors"][0]["sector_key"], "finance")

    def test_no_display_strings_leak_into_the_bundle(self):
        """ADR 0003, asserted over **every populated block** rather than a synthetic bundle.

        The exact leaf set is pinned rather than bounded, so a new string field is a decision
        someone has to make on purpose.

        ⚠️ One deliberate exception: `announcements[].subject` is a **verbatim** filing subject.
        Ticket 16 requires it be shown as filed, with a translation beside it, never paraphrased —
        so it is display text by design and the only one. Every other string here is an
        identifier (`symbol`, `ticker`), a key (`label_key`, `sector_key`), or a date.
        """
        leaves = {path.split(".")[-1].split("[")[0] for path, _ in _strings(self.golden)}
        allowed = {
            # identifiers — never prose
            "ticker",
            "symbol",
            "ref",
            # keys: what to label it, and what kind of event it is
            "label_key",
            "sector_key",
            "kind",
            # dates
            "date",
            "session",
            "ex_date",
            "start",
            "end",
            # the bundle's own provenance
            "source",
            # timeline entry identifiers, and the block keys they resolve to
            "key",
            "id",
            # ⚠️ the one deliberate exception
            "subject",
        }
        self.assertEqual(leaves, allowed, f"unexpected string-bearing leaves: {leaves - allowed}")

    def test_the_spine_numbers_match_the_independent_probe(self):
        """Two figures measured by hand while charting ticket 26, reproduced by the code.

        If these drift, either the source changed or the weighting did — and the weighting
        changing would silently flip a sector's colour.
        """
        finance = self.golden["sectors"][0]
        self.assertEqual(finance["sector_key"], "finance")
        self.assertEqual(finance["members"], 100)
        self.assertAlmostEqual(finance["window"]["change"], -0.12, places=2)

    def test_the_most_active_row_reproduces_the_measured_pick(self):
        """GALLANTT at 388x and ₹1,386 cr, as measured during the ticket-25 probe."""
        found = self.golden["most_active"]
        self.assertEqual(found["symbol"], "GALLANTT")
        self.assertAlmostEqual(found["relative_volume"], 388.5, places=1)
        self.assertAlmostEqual(found["cash_flow_crore"], 1385.55, places=1)


class Omission(unittest.TestCase):
    """A card whose source was absent is **absent**, not zero-filled (0085_05's first rule)."""

    @classmethod
    def setUpClass(cls):
        if not (RECORDED / "facts.json").exists():
            raise unittest.SkipTest(f"no recorded snapshot at {RECORDED}")
        cls.raw_indexes = tradingview.parse_snapshot(
            "tradingview-indexes", raw("tradingview-indexes"), tradingview.INDEX_COLUMNS
        )

    def test_no_universe_means_no_universe_cards(self):
        bundle = facts.build(SESSION.isoformat(), indexes=self.raw_indexes)
        for absent in ("leaders", "sectors", "breadth", "dma", "most_active", "broader"):
            self.assertNotIn(absent, bundle)
        self.assertIn("indexes", bundle, "the spine is still there")

    def test_an_absent_source_leaves_the_other_cards_untouched(self):
        whole = facts.build(SESSION.isoformat(), indexes=self.raw_indexes)
        bounded = facts.build(
            SESSION.isoformat(),
            indexes=self.raw_indexes,
            world=tradingview.parse_snapshot(
                "tradingview-universe", raw("tradingview-universe"), tradingview.UNIVERSE_COLUMNS
            ),
        )
        self.assertEqual(set(whole) - set(bounded), set())
        self.assertTrue(set(bounded) - set(whole))

    def test_an_empty_corporate_action_window_is_omitted_rather_than_shown_empty(self):
        bundle = facts.build(SESSION.isoformat(), indexes=self.raw_indexes, actions=[])
        self.assertNotIn("corporate_actions", bundle)


if __name__ == "__main__":
    unittest.main()
