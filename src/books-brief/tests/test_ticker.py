"""Ticket 08 — the market band behind the book, and **deliberately allowed to not exist**.

⚠️ **The band is decoration, so its failure mode is not the brief's.** The brief treats a short index scoreboard as
**fatal** — `facts.build` raises `MissingTickersError`, because *"an unresolvable index comes back as an absent row with
HTTP 200 and no error, so a short scoreboard is otherwise completely silent"* and *the scoreboard is its content*. Here
it is background, so the **abort threshold moves**: a failed fetch omits the band entirely, and the layout absorbs the
omission without a hole because the book block is `flex: 1`.

⚠️ **But it does not become a placeholder.** Never zeros, never stale, never a dash where a number should be — the same
*degrade to omission* principle, one notch down. A band of `—` would be a claim about the market.

⚠️ **Only `parse` is tested**; `fetch` is the boundary, and the suite stays hermetic.
"""
import pathlib
import unittest

from books_brief import ticker

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "tradingview-indexes.json"


class TheBand(unittest.TestCase):
    def test_the_five_indices_come_back_as_slugs_and_values(self):
        """⚠️ Ticket 08 — *"label keys follow the brief's discipline: stable slugs in `facts.json`, display strings in
        the renderer's label tables"* (ADR 0003).

        ⚠️ **Values, never formatted strings.** The row carries `close` and `change` as numbers, so the renderer decides
        the grouping and the sign — which is what lets the band be re-worded without re-running a week. A `"24,812"`
        written here would be a display string in the committed evidence.
        """
        band = ticker.parse(FIXTURE.read_bytes())

        assert band is not None
        self.assertEqual(
            [row.label_key for row in band.rows],
            ["nifty50", "nifty500", "banknifty", "sensex", "next50"],
        )
        self.assertEqual(band.rows[0].close, 24812.35)
        self.assertEqual(band.rows[0].change, 0.42)
        # ⚠️ A falling index carries a negative change, so the renderer's colour path is exercised rather than assumed.
        self.assertEqual(band.rows[-1].change, -0.12)

    def test_the_band_carries_the_session_it_describes(self):
        """⚠️ **Ticket 08's reason for the clock, and it is not decoration either.**

        *"A ticker that cannot say when it is from is a ticker that can lie."* The band sits under a book that was ranked
        over six months, so a reader glancing at the market behind it has no other way to know whether those numbers are
        from today or from the last time the run succeeded.
        """
        band = ticker.parse(FIXTURE.read_bytes())

        assert band is not None
        self.assertEqual(band.as_of, "2026-10-12")

    def test_a_short_scoreboard_omits_the_band_rather_than_showing_four_of_five(self):
        """⚠️ **The threshold that moves, stated as a test.**

        The brief *aborts* on a short scoreboard because the scoreboard is what it publishes. Here the same response is a
        band that would show four indices and silently drop one — a viewer cannot tell a missing index from an index that
        did not move, so the whole band goes rather than most of it.
        """
        payload = FIXTURE.read_bytes().replace(b'"NSE:NIFTYJR"', b'"NSE:SOMETHINGELSE"')

        self.assertIsNone(ticker.parse(payload))

    def test_a_scoreboard_with_no_clock_omits_the_band_too(self):
        """⚠️ *"A ticker that cannot say when it is from is a ticker that can lie."*

        The clock row is `NSE:NIFTY` — the brief's own `CLOCK_TICKER` — and without it the band has numbers and no date.
        ⚠️ The honest answer is to draw nothing: an undated market beside a six-month ranking is the one combination a
        reader would misread.

        ⚠️ **The timestamps are nulled rather than the columns renamed**, because the vendor's response carries the
        *values* and not the column names — `parse_snapshot` is told those, so removing a column name from the payload
        would change nothing. A null timestamp is what a vendor outage actually looks like.
        """
        payload = FIXTURE.read_bytes().replace(b", 1791776700, 1791800100]", b", null, null]")

        self.assertIsNone(ticker.parse(payload))

    def test_something_unreadable_is_none_and_not_a_crash(self):
        """⚠️ A malformed response is *the source being broken*, and the band's answer to that is the same as to a
        missing one: it does not draw. ⚠️ And it must not raise — the chart's own sources are the spine (ticket 18), and
        decoration that can abort a run has stopped being decoration.
        """
        self.assertIsNone(ticker.parse(b"not json at all"))
        self.assertIsNone(ticker.parse(b"{}"))

    def test_a_row_with_a_null_close_keeps_the_row_and_omits_the_number(self):
        """⚠️ Ticket 04's rule, one surface over: *"a missing value and a real zero are different facts."*

        A null close is an index that did not resolve, and the row stays with `None` rather than becoming `0` — the
        renderer draws its own dash, and `₹0`-style lies are not possible.
        """
        payload = FIXTURE.read_bytes().replace(b"[24812.35,", b"[null,")

        band = ticker.parse(payload)

        assert band is not None
        self.assertIsNone(band.rows[0].close)
        self.assertEqual(len(band.rows), 5)


if __name__ == "__main__":
    unittest.main()
