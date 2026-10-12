"""The blocks derived from the universe — and the rules they enforce."""
import unittest

from market_overview import universe
from market_overview.fetch import tradingview


def member(**overrides) -> dict[str, object]:
    row: dict[str, object] = {
        "name": "SYM",
        "close": 100.0,
        "change": 1.0,
        "relative_volume_10d_calc": 2.0,
        "Value.Traded": 1.3e9,
        "market_cap_basic": 1e11,
        "sector": "Finance",
        "SMA50": 90.0,
        "SMA100": 80.0,
        "SMA200": 70.0,
        "indexes": [{"proname": "NSE:CNX500"}],
    }
    row.update(overrides)
    return row


def scan(rows: dict[str, dict[str, object]]) -> tradingview.ScanResult:
    return tradingview.ScanResult(name="w", raw=b"{}", rows=rows)


class SectorKey(unittest.TestCase):
    def test_tradingview_taxonomy_becomes_a_slug(self):
        self.assertEqual(universe.sector_key("Producer Manufacturing"), "producer_manufacturing")
        self.assertEqual(universe.sector_key("Non-Energy Minerals"), "non_energy_minerals")

    def test_a_missing_sector_has_no_key(self):
        self.assertEqual(universe.sector_key(None), "")
        self.assertEqual(universe.sector_key("   "), "")


class Nifty500(unittest.TestCase):
    def test_non_members_are_excluded(self):
        world = scan({"NSE:IN": member(name="IN"), "NSE:OUT": member(name="OUT", indexes=[])})
        self.assertEqual([r["name"] for r in universe.nifty500(world)], ["IN"])

    def test_a_missing_indexes_field_is_not_a_member(self):
        world = scan({"NSE:X": member()})
        world.rows["NSE:X"].pop("indexes")
        self.assertEqual(universe.nifty500(world), [])


class Leaderboard(unittest.TestCase):
    def test_order_is_by_move_and_each_row_carries_relative_volume(self):
        members = [
            member(name="UP", change=8.0, relative_volume_10d_calc=166.0),
            member(name="DOWN", change=-5.0, relative_volume_10d_calc=3.0),
            member(name="FLAT", change=0.0, relative_volume_10d_calc=1.0),
        ]
        gainers = universe.leaderboard(members, rising=True)
        self.assertEqual([r["symbol"] for r in gainers], ["UP", "FLAT", "DOWN"])
        self.assertEqual(gainers[0]["relative_volume"], 166.0)

    def test_losers_are_the_other_end(self):
        members = [member(name="UP", change=8.0), member(name="DOWN", change=-5.0)]
        self.assertEqual(universe.leaderboard(members, rising=False)[0]["symbol"], "DOWN")

    def test_the_board_is_cut_to_size(self):
        members = [member(name=f"M{i}", change=float(i)) for i in range(10)]
        self.assertEqual(len(universe.leaderboard(members)), universe.LEADERBOARD_SIZE)

    def test_a_row_without_a_change_is_not_ranked(self):
        members = [member(name="OK", change=1.0), member(name="MISSING", change=None)]
        self.assertEqual([r["symbol"] for r in universe.leaderboard(members)], ["OK"])


class MostActive(unittest.TestCase):
    def test_the_unusual_name_wins_over_the_big_company(self):
        """⚠️ Cash-flow ranking would pick BIG; relative volume picks ODD. This is the rule."""
        members = [
            member(name="BIG", relative_volume_10d_calc=0.73, **{"Value.Traded": 1.3e13}),
            member(name="ODD", relative_volume_10d_calc=388.0, **{"Value.Traded": 1.386e10}),
        ]
        found = universe.most_active(members)
        self.assertEqual(found["symbol"], "ODD")
        self.assertAlmostEqual(found["cash_flow_crore"], 1386.0, places=1)

    def test_direction_is_not_a_filter(self):
        """A falling stock can be the most active: the card is *where the action was*."""
        members = [
            member(name="UP", change=5.0, relative_volume_10d_calc=2.0),
            member(name="DOWN", change=-9.0, relative_volume_10d_calc=50.0),
        ]
        self.assertEqual(universe.most_active(members)["symbol"], "DOWN")

    def test_a_null_relative_volume_is_excluded_not_treated_as_low(self):
        """⚠️ No 10-day history is not 'quiet' — measured on MONEYVIEW, which returned null."""
        members = [
            member(name="NEW", relative_volume_10d_calc=None),
            member(name="KNOWN", relative_volume_10d_calc=1.0),
        ]
        self.assertEqual(universe.most_active(members)["symbol"], "KNOWN")

    def test_no_relative_volume_at_all_yields_nothing(self):
        self.assertIsNone(universe.most_active([member(relative_volume_10d_calc=None)]))

    def test_the_sector_travels_as_a_key(self):
        found = universe.most_active([member(sector="Energy Minerals")])
        self.assertEqual(found["sector_key"], "energy_minerals")


class Sectors(unittest.TestCase):
    def members(self):
        return [
            member(name="BIGFIN", sector="Finance", market_cap_basic=1e11, change=2.0),
            member(name="SMALLFIN", sector="Finance", market_cap_basic=9e10, change=-3.0),
            member(name="UTIL", sector="Utilities", market_cap_basic=1e11, change=1.0),
        ]

    def finance(self):
        return next(s for s in universe.sectors(self.members()) if s["sector_key"] == "finance")

    def test_weighting_is_by_market_cap_not_by_headcount(self):
        """⚠️ Cap- and equal-weighting disagree, and can disagree on the *sign*."""
        # (1e11 x 2.0 + 9e10 x -3.0) / 1.9e11
        self.assertAlmostEqual(self.finance()["window"]["change"], -0.3684210526, places=6)
        # equal weighting would have said (2 - 3) / 2
        self.assertNotAlmostEqual(self.finance()["window"]["change"], -0.5, places=3)

    def test_every_window_is_weighted(self):
        self.assertEqual(
            set(self.finance()["window"]), set(tradingview.WINDOWS)
        )

    def test_members_and_weight_ride_along(self):
        self.assertEqual(self.finance()["members"], 2)
        self.assertAlmostEqual(self.finance()["market_cap_crore"], 19000.0, places=1)

    def test_ranking_is_by_weight_and_cut_to_thirteen(self):
        rows = [
            member(name=f"M{i}", sector=f"Sector {i}", market_cap_basic=1e11 - i * 1e9)
            for i in range(20)
        ]
        ranked = universe.sectors(rows)
        self.assertEqual(len(ranked), universe.SECTOR_COUNT)
        self.assertEqual(ranked[0]["sector_key"], "sector_0")

    def test_a_row_with_no_sector_is_dropped(self):
        self.assertEqual(universe.sectors([member(sector=None)]), [])

    def test_a_row_with_no_cap_does_not_break_the_weighting(self):
        rows = [member(sector="Finance", market_cap_basic=None, change=99.0), member()]
        ranked = universe.sectors(rows)
        self.assertEqual(len(ranked), 1)
        self.assertAlmostEqual(ranked[0]["window"]["change"], 1.0, places=6)


class Breadth(unittest.TestCase):
    def test_the_split_sums_to_its_own_total(self):
        found = universe.breadth([member(change=1.0), member(change=-1.0), member(change=0.0)])
        self.assertEqual((found["rising"], found["falling"], found["flat"]), (1, 1, 1))
        self.assertEqual(found["counted"], found["universe"])

    def test_flat_is_an_exact_zero(self):
        self.assertEqual(universe.breadth([member(change=0.0001)])["flat"], 0)

    def test_an_uncounted_row_lowers_counted_but_not_universe(self):
        """The two can differ, so both are emitted rather than implying the split is everything."""
        found = universe.breadth([member(change=1.0), member(change=None)])
        self.assertEqual(found["counted"], 1)
        self.assertEqual(found["universe"], 2)


class Dma(unittest.TestCase):
    def test_one_denominator_over_those_with_all_three_averages(self):
        members = [
            member(close=100.0, SMA50=90.0, SMA100=80.0, SMA200=70.0),
            member(close=50.0, SMA50=60.0, SMA100=70.0, SMA200=80.0),
            member(close=100.0, SMA50=90.0, SMA100=80.0, SMA200=None),
        ]
        found = universe.dma(members)
        self.assertEqual(found["eligible"], 2)
        self.assertAlmostEqual(found["above"]["sma200"], 50.0, places=6)

    def test_a_missing_average_manufactures_no_bearish_fact(self):
        """Counting a stock with no SMA200 as 'below' would invent one out of absent data."""
        found = universe.dma([member(SMA200=None)])
        self.assertEqual(found["eligible"], 0)
        self.assertIsNone(found["above"]["sma200"])


class Broader(unittest.TestCase):
    def test_the_cap_tiers_carry_their_label_keys_and_six_windows(self):
        rows = universe.broader(
            scan(
                {
                    ticker: {"close": 1.0, **{w: 0.5 for w in tradingview.WINDOWS}}
                    for ticker in universe.BROADER_TICKERS
                }
            )
        )
        self.assertEqual([r["label_key"] for r in rows], ["midcap100", "smallcap100"])
        self.assertEqual(set(rows[0]["window"]), set(tradingview.WINDOWS))

    def test_an_unresolved_cap_tier_is_simply_absent_from_the_rows(self):
        rows = universe.broader(scan({universe.BROADER_TICKERS[0]: {"close": 1.0}}))
        self.assertEqual([r["label_key"] for r in rows], ["midcap100"])


if __name__ == "__main__":
    unittest.main()

