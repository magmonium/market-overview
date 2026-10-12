"""The four BSE feeds. Every quirk pinned below was measured against the live feed."""
import datetime
import unittest

from market_overview.fetch import bse

SESSION = datetime.date(2026, 10, 12)
UNTIL = SESSION + datetime.timedelta(days=7)


def turnover(**overrides):
    row = {
        "REPORTING_DATE": "2026-10-12T00:00:00",
        "NET_BSENSE": -17084800000.00,
        "PURCHASE_BSENSE": 125832100000.00,
        "SALE_BSENSE": 142916900000.00,
        "NET_DII": 30450200000.00,
        "PURCHASE_DII": 155067300000.00,
        "SALE_DII": 124617100000.00,
        "NET_Mutual": None,
    }
    row.update(overrides)
    return {"Table": [row]}


class Flows(unittest.TestCase):
    def test_net_converts_to_crore(self):
        """⚠️ The feed is raw rupees. Without ÷ 1e7 a card renders '₹10,37,39,90,000 crore'."""
        flows = bse.net_flows(turnover())
        self.assertAlmostEqual(flows["fii"]["net"], -1708.48, places=2)
        self.assertAlmostEqual(flows["dii"]["net"], 3045.02, places=2)

    def test_dii_comes_from_the_dii_fields_not_bsense(self):
        """⚠️ DII is `NET_DII`. Reading `*_BSENSE` would blank half the pair."""
        flows = bse.net_flows(turnover())
        self.assertNotEqual(flows["dii"]["net"], flows["fii"]["net"])
        self.assertAlmostEqual(flows["dii"]["buy"], 15506.73, places=2)

    def test_the_pair_offsets_on_this_session(self):
        """The story the pairing exists to tell: foreign selling, domestic buying."""
        flows = bse.net_flows(turnover())
        self.assertLess(flows["fii"]["net"], 0)
        self.assertGreater(flows["dii"]["net"], 0)

    def test_the_session_rides_along(self):
        self.assertEqual(bse.net_flows(turnover())["session"], "2026-10-12")

    def test_no_table_is_an_error(self):
        with self.assertRaises(bse.BseError):
            bse.net_flows({"Table": []})


class ActionKind(unittest.TestCase):
    """⚠️ `Purpose` arrives dirty. These strings are copied from the live feed."""

    def test_every_measured_purpose_classifies(self):
        cases = {
            "Right Issue of Equity Shares ": "rights",
            "Stock  Split From Rs.10/- to Rs.1/-": "split",
            "Interim Dividend": "dividend",
            "Interim Dividend - Rs. - 12.0000": "dividend",
            "Consolidation of Shares ": "consolidation",
            "Bonus issue 1:1": "bonus",
            "Income Distribution (InvIT) ": "income_distribution",
        }
        for purpose, expected in cases.items():
            with self.subTest(purpose=purpose):
                self.assertEqual(bse.action_kind(purpose), expected)

    def test_double_and_trailing_spaces_do_not_matter(self):
        self.assertEqual(bse.action_kind("Stock  Split From Rs.5/- to Rs.1/-"), "split")
        self.assertEqual(bse.action_kind("Consolidation of Shares "), "consolidation")

    def test_an_unknown_purpose_is_not_misclassified(self):
        self.assertEqual(bse.action_kind("Something Else Entirely"), "other")

    def test_the_amount_survives_the_stray_dash(self):
        self.assertEqual(bse.action_amount("Interim Dividend - Rs. - 12.0000"), 12.0)
        self.assertIsNone(bse.action_amount("Interim Dividend"))


class ActionWindow(unittest.TestCase):
    def rows(self):
        return [
            {"short_name": "IN", "Purpose": "Interim Dividend", "exdate": "20261012"},
            {"short_name": "EDGE", "Purpose": "Bonus issue 1:1", "exdate": "20261019"},
            {"short_name": "OUT", "Purpose": "Interim Dividend", "exdate": "20261020"},
            {"short_name": "BROKEN", "Purpose": "Interim Dividend", "exdate": "12 Oct 2026"},
        ]

    def test_the_window_is_inclusive_at_both_ends(self):
        picked = bse.actions_in_window(self.rows(), SESSION, UNTIL)
        self.assertEqual([a["symbol"] for a in picked], ["IN", "EDGE"])

    def test_a_row_with_no_parseable_exdate_is_dropped(self):
        """⚠️ `Ex_date` is `'12 Oct 2026'`; only `exdate` (`20261012`) is machine-readable."""
        picked = bse.actions_in_window(self.rows(), SESSION, UNTIL)
        self.assertNotIn("BROKEN", [a["symbol"] for a in picked])

    def test_a_bare_list_is_the_envelope(self):
        """⚠️ This feed is a list, not `{"Table": [...]}` — unlike the other three."""
        with self.assertRaises(bse.BseError):
            bse.actions_in_window({"Table": []}, SESSION, UNTIL)


class Ipos(unittest.TestCase):
    def rows(self):
        """The real 2026-10-12 mix — only two of these six are IPOs."""
        mix = [
            ("HD Fire Protect Limited", "IPO", "2026-10-13"),
            ("Fusion CX Limited", "IPO", "2026-10-14"),
            ("SIS", "BuyBack", "2026-10-13"),
            ("NATCO PHARMA LTD", "RI", "2026-10-12"),
            ("PASUPATI FINCAP LTD", "OTB", "2026-10-13"),
            ("HITECH CORPORATION LTD", "OTB", "2026-10-13"),
        ]
        return [
            {
                "Scrip_name": name,
                "IR_flag": flag,
                "Start_Dt": start + "T00:00:00",
                "End_Dt": start + "T00:00:00",
            }
            for name, flag, start in mix
        ]

    def test_only_real_ipos_survive(self):
        """⚠️ The feed is mostly *not* IPOs. Publishing the rest would announce five buybacks,
        four rights issues and a **delisting** as offers opening this week."""
        picked = bse.openings_in_window({"Table": self.rows()}, SESSION, UNTIL)
        self.assertEqual(
            [p["symbol"] for p in picked],
            ["HD Fire Protect Limited", "Fusion CX Limited"],
        )

    def test_an_offer_outside_the_window_is_excluded(self):
        rows = [
            {
                "Scrip_name": "LATER",
                "IR_flag": "IPO",
                "Start_Dt": "2026-11-01T00:00:00",
                "End_Dt": "2026-11-03T00:00:00",
            }
        ]
        self.assertEqual(bse.openings_in_window({"Table": rows}, SESSION, UNTIL), [])

    def test_the_close_date_rides_along(self):
        picked = bse.openings_in_window({"Table": self.rows()}, SESSION, UNTIL)
        self.assertEqual(picked[0]["end"], "2026-10-13")


class Announcements(unittest.TestCase):
    def rows(self):
        return [
            {"Subject": f"  Company {i} Ltd -Announcement   under Reg 30  ", "Newsid": f"ID{i}"}
            for i in range(12)
        ]

    def test_only_subject_and_ref_cross(self):
        picked = bse.latest_announcements(self.rows(), limit=3)
        self.assertEqual(len(picked), 3)
        self.assertEqual(set(picked[0]), {"subject", "ref"})

    def test_whitespace_is_collapsed_not_paraphrased(self):
        """The subject is legally worded, so it is tidied and kept — never reworded."""
        picked = bse.latest_announcements(self.rows(), limit=1)
        self.assertEqual(picked[0]["subject"], "Company 0 Ltd -Announcement under Reg 30")

    def test_a_bare_list_is_the_envelope(self):
        with self.assertRaises(bse.BseError):
            bse.latest_announcements({"Table": []})


if __name__ == "__main__":
    unittest.main()

