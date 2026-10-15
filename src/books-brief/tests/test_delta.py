"""Ticket 01 — the comparison window, and the Δ the slide prints.

⚠️ **Δ is against the previous *committed* week's chart, computed per chart** (tickets 01, 14). Rank is chart-local, so
the same title can move *up* in the Bengali chart and *down* in the all-language one in the same week — that is the
superset working, not a contradiction.

⚠️ **And this ticket owns only one of the chart's two windows.** Ticket 23's six-month basis asks *"what sold most over
six months?"*; this asks *"how has that ranking moved since last week?"* Keeping them apart matters, because a six-month
basis is far stickier than a weekly one.
"""
import unittest

from books_brief import delta


class TheMove(unittest.TestCase):
    def test_a_title_that_climbed_reports_a_positive_delta(self):
        """⚠️ Ticket 01 — *"Positive = moved up."*

        The sign is not cosmetic. The slide colours the Δ (ticket 07) and the description prints it, so a sign that
        ran the other way would make every rising title look like a falling one — in both places at once.
        """
        moved = delta.move(rank=7, key="9788172151234", previous={"9788172151234": 10})

        self.assertEqual(moved, 3)

    def test_a_title_that_slipped_reports_a_negative_delta(self):
        """The other half of the pair — and the half a sign error would hide."""
        moved = delta.move(rank=9, key="9788172151234", previous={"9788172151234": 4})

        self.assertEqual(moved, -5)

    def test_a_title_absent_from_the_previous_week_has_no_delta_at_all(self):
        """⚠️ **The NEW case, and `None` is not `0`.**

        Ticket 07 rules that NEW **replaces the Δ slot** — *"never a blank Δ, and never `▲0`"*. A `0` here would render
        as a flat arrow, which says the title held station: a different, and false, claim about a book that was not on
        the chart at all.
        """
        moved = delta.move(rank=3, key="9788172151234", previous={"9780000000002": 1})

        self.assertIsNone(moved)

    def test_week_one_has_no_delta_because_there_is_nothing_to_diff(self):
        """⚠️ Ticket 18 — *"every row carries no Δ and no NEW badge"*.

        ⚠️ **`None` here means *there is no previous week*, and it is deliberately not an empty dict.** An empty dict
        would say a previous chart existed and was empty — which is the case ticket 03's `previous=()` names, and it
        switches the newcomer cap back on. Collapsing the two would give week one a chart of ten books.
        """
        self.assertIsNone(delta.move(rank=1, key="9788172151234", previous=None))


class TheWindow(unittest.TestCase):
    def test_the_window_is_the_previous_iso_week(self):
        self.assertEqual(delta.previous_week("2026-W41"), "2026-W40")

    def test_the_window_crosses_a_year_boundary_without_going_to_week_zero(self):
        """⚠️ The bug a naive `int(week) - 1` produces: `2026-W00`, which is not a week.

        2027-W01 begins Mon 4 Jan 2027, so the week before it is the last week of **2026** — and 2026 has 53 ISO
        weeks, because it began on a Thursday. A week-arithmetic that did not go through a real date would ask the
        store for a folder that can never exist, and the diff would silently read as *week one*.
        """
        self.assertEqual(delta.previous_week("2027-W01"), "2026-W53")


class ThePreviousChart(unittest.TestCase):
    def test_the_previous_chart_is_read_by_rank_not_by_position(self):
        """⚠️ **Ticket 01's whole mechanism, in one function.**

        The previous week's chart is a *list of rows*, and the Δ needs each title's **rank**. Returning the list and
        letting the caller zip it against positions would be right only while the chart is dense and ordered — which is
        exactly the assumption a watchlisted or short chart breaks.
        """
        bundle = {
            "charts": {
                "bengali": {
                    "ranked": [
                        {"isbn": "9780000000002", "rank": 1},
                        {"isbn": "9788172151234", "rank": 2},
                    ]
                }
            }
        }

        self.assertEqual(
            delta.ranks(bundle, "bengali"),
            {"9780000000002": 1, "9788172151234": 2},
        )

    def test_a_chart_that_was_never_built_has_no_previous_and_is_not_an_empty_chart(self):
        """⚠️ Ticket 13 — a chart whose sources failed is an **absent key**, so its previous week is `None`.

        ⚠️ And the distinction is load-bearing rather than pedantic: `rank.chart` **bypasses the newcomer cap** on
        `None` (ticket 03), because with no previous week every title reads as new and the cap would ship a "Top 100"
        holding ten books.
        """
        self.assertIsNone(delta.ranks({"charts": {"comics": {"ranked": []}}}, "bengali"))
        self.assertIsNone(delta.ranks({"charts": {}}, "bengali"))


if __name__ == "__main__":
    unittest.main()
