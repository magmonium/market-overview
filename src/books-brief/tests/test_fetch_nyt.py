"""The NYT Books API's parser — the English chart's and comics' source (tickets 19 and 22).

⚠️ **Fetch and parse are separated, and only the parse is tested.** The brief does the same
(`_degrade(day, name, fetch, parse, default)` — *"Fetch one non-spine feed, snapshot it, shape it"*), because a parser
is a **pure function of bytes** and the suite is hermetic: *"nothing in it reaches the network."*

⚠️ **The fixture below is hand-built from the documented field list, not recorded.** `rank`, `rank_last_week`,
`weeks_on_list`, `primary_isbn13`, `title`, `author`, `publisher`, `price` and `book_image` come from the API's own
schema; a real recording should replace this file before the product ships, and nothing in the parser should have to
change when it does.
"""
import pathlib
import unittest

from books_brief import charts, freshness
from books_brief.fetch import nyt

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "nyt-hardcover-fiction.json"

#: ⚠️ **A parser is told which list it read, and that is now part of its contract** (ticket 20). The payload carries no
#: geography, so the country and the language can only come from the declaration — and making it an argument means a
#: client cannot parse without saying which list it was reading.
LISTING = charts.Listing(slug="nyt/hardcover-fiction", country="us", language="en")


class ParsingAList(unittest.TestCase):
    def test_a_list_response_becomes_rows_tagged_with_the_list_it_came_from(self):
        """⚠️ The list slug carries the **vendor** — `nyt/hardcover-fiction` — and that is what makes ticket 17's
        vendor count possible without a second table that could disagree with the first.
        """
        rows = nyt.parse(FIXTURE.read_bytes(), listing=LISTING)

        # ⚠️ Three books in the fixture, two rows out: the third carries no ISBN-13, so it is skipped rather than
        # given a synthesised key that another book could collide with.
        self.assertEqual(len(rows), 2)
        self.assertEqual([row.rank for row in rows], [1, 2])
        self.assertEqual([row.isbn for row in rows], ["9780385547345", "9781250328175"])
        self.assertEqual([row.title for row in rows], ["The Widow", "The Black Wolf"])
        # ⚠️ The author rides the row because ticket 17's per-field priority puts the **list** ahead of every enrichment
        # source for it — so it has to survive the parse, and a field dropped here cannot be recovered later.
        self.assertEqual([row.author for row in rows], ["John Grisham", "Louise Penny"])
        self.assertTrue(all(row.list == "nyt/hardcover-fiction" for row in rows))

    def test_every_row_carries_the_date_the_list_was_published(self):
        """⚠️ **The only evidence ticket 10's freshness guard has.**

        A books chart has no session clock, so a stale response is indistinguishable from a fresh one except by this
        date. ⚠️ It rides on every row rather than being returned beside them, because it is a property of the *list* —
        the same as the slug — and keeping it there makes the guard a pure function of the rows.

        ⚠️ **It is the list's date, not a book's.** Ticket 05 warns that NYT's book objects carry date fields of their
        own, and the two are different questions: the list's date says *which week this ranking describes*, which is what
        the guard needs.

        ⚠️ **And it is `bestsellers_date`, not the print date** — see the test below, which is the one that would have
        caught this.
        """
        rows = nyt.parse(FIXTURE.read_bytes(), listing=LISTING)

        self.assertEqual([row.published for row in rows], ["2026-10-10", "2026-10-10"])

    def test_the_date_on_the_rows_is_the_sales_week_and_not_the_print_date(self):
        """⚠️ ⚠️ **The field, asserted — and it is worth a test of its own.**

        The response carries **both** dates, fifteen days apart, and only one of them can be compared against the week
        being built:

            bestsellers_date   2026-10-10    the sales week this list reflects
            published_date     2026-10-25    the *print* date the Book Review will carry

        ⚠️ **`published_date` is documented as eleven days after the list appears online**, so reading it puts the row
        *outside every week's window* — which made NYT permanently **stale** and `english` unbuildable no matter when
        the run happened. ⚠️ That is not a guard working; it is a source the product can never use.

        ⚠️ The fixture carries both fields, so this fails if the parser ever reads the wrong one again.
        """
        rows = nyt.parse(FIXTURE.read_bytes(), listing=LISTING)

        # ⚠️ The sales week ending 2026-10-11 is **2026-W41**, whose window is 2026-10-05 … 2026-10-14 — so this is the
        # list W41 should rank, and the guard says so.
        self.assertTrue(freshness.is_fresh(rows[0].published, week="2026-W41"))
        # ⚠️ The print date from the very same response is *not* fresh for that week — which is why it must not be the
        # field the guard is given.
        self.assertFalse(freshness.is_fresh("2026-10-25", week="2026-W41"))

    def test_a_response_with_no_bestsellers_date_leaves_the_rows_undated(self):
        """⚠️ **Empty, not invented — and empty is *stale*.**

        A parser that substituted today's date for a missing field would turn the guard into a rubber stamp for exactly
        the source that broke. ⚠️ Nor does it raise: one vendor's malformed field must not cost the other three charts.
        """
        payload = FIXTURE.read_bytes().replace(b'"bestsellers_date"', b'"bestsellers_dtae"')

        rows = nyt.parse(payload, listing=LISTING)

        self.assertEqual([row.published for row in rows], ["", ""])
        self.assertFalse(freshness.is_fresh(rows[0].published, week="2026-W41"))


    def test_the_rows_carry_the_country_and_language_the_list_declares(self):
        """⚠️ Ticket 20 — **the list knows where it is; the response does not.**

        NYT's payload carries a list name and a date and nothing about geography, so these two can only come from
        `charts.Listing`. ⚠️ That is the drift-proof direction: a list **cannot be declared without them**, so a chart
        cannot end up with a label table that disagrees with its own sources.
        """
        rows = nyt.parse(FIXTURE.read_bytes(), listing=LISTING)

        self.assertEqual([row.country for row in rows], ["us", "us"])
        self.assertEqual([row.language for row in rows], ["en", "en"])

    def test_the_response_still_names_its_own_list_even_when_it_disagrees_with_the_declaration(self):
        """⚠️ **The slug comes from the response; the geography comes from the declaration — and they can disagree.**

        Ticket 05 wants the row tagged with what the vendor *said* it was, so a mismatch is visible rather than silently
        assumed away. ⚠️ The disagreement is then readable in the row itself: a `nyt/hardcover-fiction` row answered from
        `hardcover-nonfiction` says so, and the country it carries is the one it was *asked* for — which is the only
        answer available, and the one an operator can check.
        """
        payload = FIXTURE.read_bytes().replace(
            b'"hardcover-fiction"', b'"hardcover-nonfiction"'
        )

        rows = nyt.parse(payload, listing=LISTING)

        self.assertEqual(rows[0].list, "nyt/hardcover-nonfiction")
        self.assertEqual(rows[0].country, "us")


if __name__ == "__main__":
    unittest.main()
