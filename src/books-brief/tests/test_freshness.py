"""Ticket 10's freshness guard — ⚠️ **the guard against the failure that has no symptom.**

⚠️ **What it is for.** A books chart has no session clock. A stale Amazon.in scrape produces a chart that is quietly last
week's — plausible, complete, correctly formatted and wrong — and ticket 01's week-over-week diff reports **zero
movement**, which reads as *nothing happened* rather than *nothing was fetched*. The brief catches its version of this
by asking the exchange whether it traded; there is no exchange here, so the **only** evidence available is the date the
vendor puts on its own list.

⚠️ **The mechanism is ticket 18's, not ticket 10's.** Ticket 10 fixed only that the guard exists; ticket 18 fixed what it
does when it trips: *"a stale source is a missing source for that week."* So a vendor whose every list is stale drops out
exactly as a vendor that failed, and **the chart that needed it goes absent**. ⚠️ That is deliberately stricter than
dropping the stale rows and shipping the rest — a chart quietly built from the surviving vendors is precisely the silent
wrong answer this guard exists to prevent.
"""
import unittest

from books_brief import corroborate, freshness

WEEK = "2026-W41"


def row(list_slug: str, published: str, rank: int = 1) -> corroborate.Row:
    return corroborate.Row(
        list=list_slug,
        rank=rank,
        isbn=f"97881721512{rank:02d}",
        title="A",
        published=published,
    )


class TheSpan(unittest.TestCase):
    def test_the_span_runs_from_the_weeks_monday_into_the_following_week(self):
        """⚠️ **The span cannot end on the week's own Sunday, and that is the whole difficulty.**

        Ticket 10: *"a Sun–Sat sales week closes Sunday; lists compiled from it land Monday–Tuesday."* ⚠️ So the list
        that describes week 41 is **published in week 42** — and a guard that asked *"is this date inside 2026-W41?"*
        would refuse every correct answer on the one day the run happens.

        ⚠️ And it is not slack: the recorded NYT response for this very week is dated **2026-10-14**, the Wednesday of
        the following week. The boundary is the real thing, not a theoretical one.
        """
        self.assertEqual(freshness.span(WEEK), ("2026-10-05", "2026-10-14"))

    def test_the_span_is_derived_from_the_week_key_not_from_a_clock(self):
        """⚠️ The week is an argument (ADR 0003). A span read off today's date would make a rebuild of week 41 depend on
        when it was rebuilt — so a replay would disagree with the original run about which rows were fresh.
        """
        self.assertEqual(freshness.span("2026-W41"), freshness.span("2026-W41"))
        self.assertNotEqual(freshness.span("2026-W41"), freshness.span("2026-W42"))

    def test_a_week_that_starts_in_the_previous_year_is_still_right(self):
        """⚠️ `2026-W01` begins on **2025-12-29** — the key's year and the date's year disagree. Week arithmetic that
        multiplied the week number by seven would put the span a year out, the same trap `window.monday` documents.

        ⚠️ **My first version of this test was wrong and the code was right**: I wrote `2027-W01` expecting it to start in
        2026, but 2027 begins on a Friday, so its week 1 is the week of Thursday the 7th — 2027-01-04. `2026-W01` is the
        week that genuinely straddles the year boundary.
        """
        self.assertEqual(freshness.span("2026-W01"), ("2025-12-29", "2026-01-07"))


class WhetherAListIsFresh(unittest.TestCase):
    def test_a_list_published_on_the_day_the_week_opened_is_fresh(self):
        self.assertTrue(freshness.is_fresh("2026-10-05", week=WEEK))

    def test_a_list_published_on_the_last_day_the_span_allows_is_fresh(self):
        """⚠️ **The boundary is inclusive, and it is the date the real response carried.** An exclusive comparison would
        refuse the recorded NYT list for this week by one day.
        """
        self.assertTrue(freshness.is_fresh("2026-10-14", week=WEEK))

    def test_a_list_dated_before_the_week_began_is_stale(self):
        """⚠️ **The failure this exists for.** A scrape that answered with last week's list carries last week's date, and
        every row in it is last week's ranking — which would be ranked as this week's.
        """
        self.assertFalse(freshness.is_fresh("2026-10-04", week=WEEK))

    def test_a_list_dated_beyond_the_span_is_stale(self):
        """⚠️ A date far ahead is a broken parse or a placeholder the vendor never filled in — and a parser that misread
        `published_date` would otherwise read as *very* fresh, which is the most dangerous way to be wrong.
        """
        self.assertFalse(freshness.is_fresh("2026-11-01", week=WEEK))

    def test_an_undated_list_is_stale_rather_than_fresh(self):
        """⚠️ **The default matters more than the rule.**

        The tempting default is *"no date, so nothing to check, so let it through"* — and it disables the guard for
        exactly the source that broke, silently, on the day it broke. ⚠️ Ticket 10's own words: the source must be
        **verified** to have published for the week being built, *"not trusted because the calendar says it is Tuesday."*
        A list with no date has not been verified, so it is refused.
        """
        self.assertFalse(freshness.is_fresh("", week=WEEK))

    def test_a_date_that_is_not_a_date_is_stale(self):
        """⚠️ A parser that put a vendor's human-readable string where an ISO date belongs must refuse, not crash the
        run — a malformed field in one source is not a reason to lose the other three charts.
        """
        self.assertFalse(freshness.is_fresh("14 October 2026", week=WEEK))


class GuardingAVendorsRows(unittest.TestCase):
    def test_a_stale_lists_rows_never_reach_the_gate(self):
        """⚠️ **Dropping the rows is what makes the guard real.** Reporting the staleness while still passing the rows
        through would leave last week's ranking in this week's chart, which is the exact outcome being guarded against.
        """
        rows = [
            row("amazon-in/bengali", "2026-10-14"),
            row("anandabazar/bengali", "2026-10-04"),
        ]

        guarded = freshness.guard(rows, week=WEEK, vendors=["amazon-in", "anandabazar"])

        self.assertEqual([r.list for r in guarded.rows], ["amazon-in/bengali"])

    def test_a_vendor_whose_every_list_is_stale_is_reported_missing(self):
        """⚠️ **This is the half that makes the failure visible.** Without it a stale vendor is a quietly absent
        contributor, and the chart ships smaller while claiming to rank the lists it declares (ticket 18's spine).

        ⚠️ **Both vendors are missing here, and my first version of this test expected only one.** I supplied a stale
        `anandabazar` row and forgot that `amazon-in` then produced *nothing at all* — which is the same condition from
        the chart's side, and the code was right to report it.
        """
        rows = [
            row("amazon-in/bengali", "2026-10-04"),
            row("anandabazar/bengali", "2026-10-04"),
        ]

        guarded = freshness.guard(rows, week=WEEK, vendors=["amazon-in", "anandabazar"])

        self.assertEqual(guarded.rows, ())
        self.assertEqual(guarded.missing, ("amazon-in", "anandabazar"))

    def test_a_stale_vendor_beside_a_fresh_one_is_missing_alone(self):
        """⚠️ The case the guard is really for: one source published, one did not."""
        rows = [
            row("amazon-in/bengali", "2026-10-14"),
            row("anandabazar/bengali", "2026-10-04"),
        ]

        guarded = freshness.guard(rows, week=WEEK, vendors=["amazon-in", "anandabazar"])

        self.assertEqual(guarded.missing, ("anandabazar",))

    def test_a_vendor_that_answered_nothing_at_all_is_missing(self):
        """⚠️ The same path as a client that raised, and deliberately so: from the chart's side *"the vendor produced no
        usable evidence"* is one condition, however it came about. ⚠️ It is also why `guard` takes the declared vendors
        rather than inferring them from the rows — a vendor that returned nothing leaves no rows to infer from.
        """
        guarded = freshness.guard([], week=WEEK, vendors=["nyt", "pw"])

        self.assertEqual(guarded.missing, ("nyt", "pw"))
        self.assertEqual(guarded.rows, ())

    def test_a_vendor_with_one_fresh_list_among_stale_ones_is_not_missing(self):
        """⚠️ **Per list, then per vendor** — and the two halves are not the same question.

        Each list's own date governs its own rows, so a stale list is dropped without touching its vendor's fresh ones.
        ⚠️ Then the *vendor* is judged on what survived, because a vendor is a source (ticket 17) and the chart needs the
        source, not a particular list. An Amazon.in that published its Bengali list but not yet its comics one is a
        vendor that answered.
        """
        rows = [
            row("amazon-in/bengali", "2026-10-14"),
            row("amazon-in/comics", "2026-09-30"),
        ]

        guarded = freshness.guard(rows, week=WEEK, vendors=["amazon-in"])

        self.assertEqual([r.list for r in guarded.rows], ["amazon-in/bengali"])
        self.assertEqual(guarded.missing, ())

    def test_a_vendor_the_chart_does_not_declare_is_not_its_problem(self):
        """⚠️ A chart's `vendors` are its spine (ticket 18), so evidence from an undeclared source is not evidence for
        that chart — and its absence cannot make the chart missing either.
        """
        guarded = freshness.guard(
            [row("nyt/hardcover-fiction", "2026-10-04")], week=WEEK, vendors=["amazon-in"]
        )

        self.assertEqual(guarded.missing, ("amazon-in",))
        self.assertEqual(guarded.rows, ())

    def test_the_missing_vendors_are_sorted_so_the_refusal_reads_the_same_every_run(self):
        guarded = freshness.guard([], week=WEEK, vendors=["pw", "amazon-in", "nyt"])

        self.assertEqual(guarded.missing, ("amazon-in", "nyt", "pw"))


if __name__ == "__main__":
    unittest.main()


