"""Ticket 23 — the window, and the two rules that make it a window rather than a week.

⚠️ **The accumulation is the whole point**: *"the snapshot is no longer just this week's chart; it is this week's
evidence for a six-month window."* So these tests write **several weeks** to a temporary store and check what the window
makes of them — which is the only way to test a claim about six months.
"""
import unittest

from books_brief import store, window

from support import temporary_store


def row(
    isbn: str,
    rank: int,
    *,
    score: float = 1.0,
    rating: float | None = None,
    count: int | None = None,
) -> dict:
    """⚠️ A snapshot row, **with its `score`** — the week's committed sales term, which is what the window aggregates.
    A row without one would contribute zero, which is why the field is on every row this module reads.
    """
    return {"isbn": isbn, "rank": rank, "score": score, "rating": rating, "ratings_count": count}


def write(root, week: str, rows: list[dict], slug: str = "bengali") -> None:
    store.write_facts(week, {"meta": {"week": week}, "charts": {slug: {"ranked": rows}}})


class TheWeeks(unittest.TestCase):
    def test_the_window_covers_the_stored_weeks_oldest_first(self):
        """⚠️ Order matters: the newest week must win the review fields, and *oldest first* is what makes that a rule
        rather than a consequence of directory listing order.
        """
        with temporary_store() as root:
            for week in ("2026-W39", "2026-W40", "2026-W41"):
                write(root, week, [row("9788172151234", 1)])

            self.assertEqual(
                window.weeks(root, ending="2026-W41"),
                ("2026-W39", "2026-W40", "2026-W41"),
            )

    def test_a_rebuild_of_an_old_week_sees_the_window_as_it_was(self):
        """⚠️ **ADR 0003's replay guarantee, and this is where it is easiest to lose.**

        Re-running week 41 *after* week 52 has landed must produce the week-41 chart — so a later week must be invisible
        to it. Without the `ending` stop, the same command would give a different answer depending on when it was run,
        and nothing downstream would flag it.
        """
        with temporary_store() as root:
            for week in ("2026-W41", "2026-W52"):
                write(root, week, [row("9788172151234", 1)])

            self.assertEqual(window.weeks(root, ending="2026-W41"), ("2026-W41",))

    def test_the_window_is_capped_at_six_months(self):
        """⚠️ Twenty-six weeks, and **the cap is on the window rather than on the store.** Every week is kept (ticket
        01), so the cap is what stops a year-old chart's evidence from still being counted.
        """
        with temporary_store() as root:
            for number in range(1, 40):
                write(root, f"2026-W{number:02d}", [row("9788172151234", 1)])

            covered = window.weeks(root, ending="2026-W39")

            self.assertEqual(len(covered), window.WEEKS)
            self.assertEqual(covered[-1], "2026-W39")
            self.assertEqual(covered[0], "2026-W14")


class WhatTheWindowObserves(unittest.TestCase):
    def test_the_sales_term_is_the_mean_over_the_window_and_not_a_sum(self):
        """⚠️ **A sum would reward a title for having existed longer.**

        A book at #1 in all three of three weeks and one at #1 in a single week are *not* the same book, and the mean
        over the window is what says so. ⚠️ A sum would give the three-week book three times the score for doing the same
        thing three times — which is not a comparison, it is a count.
        """
        with temporary_store() as root:
            for week in ("2026-W39", "2026-W40", "2026-W41"):
                write(root, week, [row("9788172151234", 1)])

            seen = window.observe(root, ending="2026-W41", slug="bengali")

        self.assertEqual(seen.observed["9788172151234"].weeks, 3)
        # ⚠️ Three perfect weeks over a three-week window is **one** perfect week's worth — `points` at #1 of a
        # hundred-deep list is `(100 + 1 − 1) / 100`.
        self.assertAlmostEqual(seen.observed["9788172151234"].sales, 1.0)

    def test_a_title_present_for_a_third_of_the_window_scores_a_third_as_much(self):
        """⚠️ **The comparison the window exists to make**, stated directly: *"was #1 for part of the window"* is worth
        that part of *"was #1 throughout"*.
        """
        with temporary_store() as root:
            write(root, "2026-W39", [row("9788172151234", 1), row("9780000000002", 1)])
            write(root, "2026-W40", [row("9788172151234", 1)])
            write(root, "2026-W41", [row("9788172151234", 1)])

            seen = window.observe(root, ending="2026-W41", slug="bengali")

        whole = seen.observed["9788172151234"]
        part = seen.observed["9780000000002"]

        self.assertEqual(part.weeks, 1)
        self.assertLess(part.sales, whole.sales)
        self.assertAlmostEqual(part.sales, whole.sales / 3)
    def test_the_review_fields_take_the_newest_reading_not_the_first(self):
        """⚠️ A rating is **cumulative over the book's whole life**, so last week's reading is not older evidence — it is
        *less* evidence. ⚠️ And taking the newest is what keeps a rebuild deterministic.
        """
        with temporary_store() as root:
            write(root, "2026-W40", [row("9788172151234", 1, rating=4.1, count=100)])
            write(root, "2026-W41", [row("9788172151234", 1, rating=4.3, count=180)])

            seen = window.observe(root, ending="2026-W41", slug="bengali")

        self.assertEqual(seen.observed["9788172151234"].rating, 4.3)
        self.assertEqual(seen.observed["9788172151234"].ratings_count, 180)

    def test_a_week_that_carries_no_rating_does_not_erase_the_one_before_it(self):
        """⚠️ **`None` is an absence, not a zero.** A week where the enrichment source had no rating must not reset a
        title's review signal — and a `0.0` written instead would be a book rated *terribly* rather than *not rated*.
        """
        with temporary_store() as root:
            write(root, "2026-W40", [row("9788172151234", 1, rating=4.1, count=100)])
            write(root, "2026-W41", [row("9788172151234", 1)])

            seen = window.observe(root, ending="2026-W41", slug="bengali")

        self.assertEqual(seen.observed["9788172151234"].rating, 4.1)

    def test_the_mean_rating_is_weighted_by_the_ratings_themselves(self):
        """⚠️ **A plain mean of means would repeat the mistake `review_term` exists to avoid, one level up.**

        Three ratings at 5.0 must not pull the shrinkage target as hard as fifty thousand at 4.0 — and a target that
        moved on a thin week would move every thin rating with it.
        """
        with temporary_store() as root:
            write(
                root,
                "2026-W41",
                [
                    row("9788172151234", 1, rating=5.0, count=3),
                    row("9780000000002", 2, rating=4.0, count=50_000),
                ],
            )

            seen = window.observe(root, ending="2026-W41", slug="bengali")

        # ⚠️ **The claim is which side of the *plain* mean it lands on, not an exact float.** A plain mean of the two
        # ratings is **4.5**; the weighted one is a hair over 4.0, because three ratings must not count as much as fifty
        # thousand. ⚠️ Asserting `== 4.0` would be asserting arithmetic rather than the rule — and that is exactly what
        # this test's first version did, failing on `4.00006` while the code was right.
        self.assertLess(seen.mean_rating, 4.25)
        self.assertGreater(seen.mean_rating, 4.0)

    def test_no_ratings_at_all_falls_back_to_the_documented_mean(self):
        """⚠️ Not a crash and not a zero: with nothing rated there is nothing to shrink toward — and the review term is
        `0.0` for every row anyway, so the fallback never reaches a score.
        """
        with temporary_store() as root:
            write(root, "2026-W41", [row("9788172151234", 1)])

            seen = window.observe(root, ending="2026-W41", slug="bengali")

        self.assertEqual(seen.mean_rating, 4.0)


class ThePreviousWeek(unittest.TestCase):
    def test_no_earlier_week_is_none_and_not_an_empty_week(self):
        """⚠️ Ticket 03 — `None` means **week one**, and the newcomer cap is *bypassed* on it. An empty string would
        switch the cap back on and ship a "Top 100" holding ten books.
        """
        with temporary_store() as root:
            write(root, "2026-W41", [row("9788172151234", 1)])

            self.assertIsNone(window.previous(root, ending="2026-W41"))

    def test_the_week_before_is_found_across_a_year_boundary(self):
        """⚠️ Ticket 01's window, read through the store: `2027-W01` is preceded by `2026-W53`, and a naive
        `int(week) - 1` would look for a week that can never exist and silently report *week one*.
        """
        with temporary_store() as root:
            write(root, "2026-W53", [row("9788172151234", 1)])
            write(root, "2027-W01", [row("9788172151234", 1)])

            self.assertEqual(window.previous(root, ending="2027-W01"), "2026-W53")


if __name__ == "__main__":
    unittest.main()
