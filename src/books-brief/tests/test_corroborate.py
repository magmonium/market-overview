"""Ticket 17 — the corroboration gate.

⚠️ **The rule the whole product rests on: corroboration counts *vendors*, not lists.** Amazon.in's nine language
categories are nine lists and **one source**, so counting them as nine corroborating voices would be *"a lie told in
arithmetic"*. These are the tests that keep that honest.
"""
import unittest

from books_brief import charts, corroborate


class TheGate(unittest.TestCase):
    def test_two_lists_from_one_vendor_do_not_corroborate_each_other(self):
        """⚠️ Ticket 17's sharpest rule.

        A title at #1 in NYT's hardcover-fiction list *and* #1 in its hardcover-nonfiction list has been seen by **one**
        source. ⚠️ Two lists, one voice — and a gate that counted *lists* would admit it, which is *"a lie told in
        arithmetic"*.

        ⚠️ **The example moved in ticket 29.** It used to be Amazon.in's Hindi and Tamil categories — nine lists, one
        vendor — but Amazon publishes **no per-language bestseller list at all**, so the all-language chart now declares
        one list and the pair that demonstrates the rule is NYT's two.
        """
        rows = [
            corroborate.Row(list="nyt/hardcover-fiction", rank=1, isbn="9788129100001", title="A"),
            corroborate.Row(list="nyt/hardcover-nonfiction", rank=1, isbn="9788129100001", title="A"),
        ]

        result = corroborate.admit(rows, chart=charts.get("english"))

        self.assertEqual(result.admitted, ())
        self.assertEqual([title.isbn for title in result.parked], ["9788129100001"])

    def test_a_title_carried_by_two_vendors_is_admitted(self):
        """The comics chart's pair: NYT's graphic-books list plus Amazon.in's Comics & Mangas.

        ⚠️ **Not the Bengali chart any more** (ticket 29). This used to pair Anandabazar's weekly list with Rokomari's,
        but Anandabazar could not be declared — no list was ever found and no client was ever written — so the Bengali
        chart has **one** vendor and cannot admit anything at all.
        """
        rows = [
            corroborate.Row(list="amazon-in/comics", rank=3, isbn="9788172151234", title="B"),
            corroborate.Row(list="nyt/graphic-books-and-manga", rank=7, isbn="9788172151234", title="B"),
        ]

        result = corroborate.admit(rows, chart=charts.get("comics"))

        self.assertEqual([title.isbn for title in result.admitted], ["9788172151234"])
        self.assertEqual(result.parked, ())


class WhatTheGateCarries(unittest.TestCase):
    def test_the_title_and_author_come_from_the_same_list_every_time(self):
        """⚠️ **A real defect, found by asking who supplies the author.**

        The loop was `sorted` over the ISBNs, which made the *set* of admitted titles independent of the order the
        vendors answered in — but `seen[0]` was not, so the **title and author** came from whichever source happened to
        reply first. Ticket 03 requires the same week to re-render identically, and a field is part of the chart: a
        re-run could have printed a different spelling of the same book and nothing would have flagged it.

        ⚠️ The winner is the **alphabetically first list**, so it is a stated rule rather than a coincidence of dict
        insertion order.
        """
        rows = [
            corroborate.Row(
                list="nyt/graphic-books-and-manga",
                rank=7,
                isbn="9788172151234",
                title="NYT's Title",
                author="NYT's Author",
            ),
            corroborate.Row(
                list="amazon-in/comics",
                rank=3,
                isbn="9788172151234",
                title="Amazon's Title",
                author="Amazon's Author",
            ),
        ]

        forward = corroborate.admit(rows, chart=charts.get("comics"))
        reverse = corroborate.admit(list(reversed(rows)), chart=charts.get("comics"))

        self.assertEqual(forward.admitted, reverse.admitted)
        # ⚠️ `amazon-in/…` sorts before `nyt/…`, so the Amazon list supplies both fields — whichever order the vendors
        # were read in.
        self.assertEqual(forward.admitted[0].title, "Amazon's Title")
        self.assertEqual(forward.admitted[0].author, "Amazon's Author")

    def test_the_lists_author_survives_the_gate(self):
        """⚠️ Ticket 17 — *"title / author: the vendor that published the list the title ranked on."*

        ⚠️ **The gate is the last place a row's fields are still attributable to the vendor that supplied them.** A
        field dropped here cannot be recovered later — the merge would fall back to an enrichment source and nobody
        would be able to tell that the chart had contradicted its own list.

        ⚠️ **The pair is a US list and an Indian one now** (ticket 29): the Bengali chart used to supply this case with
        an Indian/Bangladeshi pair, and it has one vendor since Anandabazar could not be declared.
        """
        rows = [
            corroborate.Row(
                list="amazon-in/comics",
                rank=1,
                isbn="9788172151234",
                title="B",
                author="An Author",
            ),
            corroborate.Row(
                list="nyt/graphic-books-and-manga",
                rank=2,
                isbn="9788172151234",
                title="B",
                author="Another Author",
            ),
        ]

        result = corroborate.admit(rows, chart=charts.get("comics"))

        # ⚠️ `amazon-in/…` sorts first, so **its** author is the one that survives — and the point of the assertion is
        # that the field comes from a list at all, rather than from whichever vendor replied first.
        self.assertEqual(result.admitted[0].author, "An Author")

    def test_a_vendor_that_carries_no_author_gives_an_empty_string_and_not_absence(self):
        """⚠️ Amazon.in's listings carry no author at all, and that is **ordinary** — so the field is empty rather than
        missing. ⚠️ The difference matters downstream: an empty string means *this vendor has no opinion*, which lets
        Google Books supply one, while `None` would have to be treated as a deliberate blank.
        """
        rows = [
            corroborate.Row(list="amazon-in/comics", rank=1, isbn="9788172151234", title="B"),
            corroborate.Row(list="nyt/graphic-books-and-manga", rank=2, isbn="9788172151234", title="B"),
        ]

        result = corroborate.admit(rows, chart=charts.get("comics"))

        self.assertEqual(result.admitted[0].author, "")


class TheCountryAndTheLanguage(unittest.TestCase):
    """⚠️ Ticket 20's two labels — and they are decided **here**, at the gate, for the same reason the title and the
    author are: this is where a row's fields are still attributable to the list that supplied them.

    ⚠️ **Same determinism rule, same reason.** A title carried by both a US list and an Indian one has *two* right
    answers, and the gate already fixes which one wins — the first in sorted list order — so a re-run prints the same
    country it printed the first time (ticket 03's *"the same week, re-rendered"*).

    ⚠️ **The chart that demonstrates it is `comics` now** (ticket 29). It used to be `bengali`, spanning India and
    Bangladesh — but Anandabazar could not be declared, so the Bengali chart is `bd` throughout and the US/Indian pair
    lives on the comics chart.
    """

    def _pair(self) -> tuple[corroborate.Row, corroborate.Row]:
        """The same title on a US list and an Indian one — the comics chart's ordinary case (ticket 22)."""
        return (
            corroborate.Row(
                list="nyt/graphic-books-and-manga",
                rank=1,
                isbn="9788172151234",
                title="B",
                country="us",
                language="en",
            ),
            corroborate.Row(
                list="amazon-in/comics",
                rank=2,
                isbn="9788172151234",
                title="B",
                country="in",
                language="en",
            ),
        )

    def test_a_title_carries_the_country_and_language_of_its_first_list(self):
        """⚠️ `amazon-in/comics` sorts before `nyt/graphic-books-and-manga`, so **India** wins — and that is a decision
        rather than a fallthrough. The alternative is the country depending on which vendor happened to answer first,
        which is precisely the bug `admit` already had once for the title.
        """
        result = corroborate.admit(list(self._pair()), chart=charts.get("comics"))

        self.assertEqual(result.admitted[0].country, "in")
        self.assertEqual(result.admitted[0].language, "en")

    def test_the_order_the_vendors_answered_in_does_not_change_the_country(self):
        """⚠️ **The defect this file already records, one field along.**

        The loop sorted the *set* of ISBNs but read `seen[0]` from the caller's order, so the title could differ between
        two runs of the same week. A country read the same way would drift identically — and a country is worse, because
        nothing downstream can tell that *US* is the wrong answer for an Indian row.
        """
        first, second = self._pair()

        forwards = corroborate.admit([first, second], chart=charts.get("comics"))
        backwards = corroborate.admit([second, first], chart=charts.get("comics"))

        self.assertEqual(forwards.admitted[0].country, backwards.admitted[0].country)

    def test_a_row_from_no_declared_list_carries_nothing_rather_than_guessing(self):
        """⚠️ Empty, and the renderer reads empty as *no label* — the same state as a constant one (ticket 20). A
        guessed `in` would put a country on a row whose country nobody knows.

        ⚠️ **The labels come from the *row*, not from the declaration** — `admit` reads `seen[0]`, so a client that did
        not tag its rows supplies nothing and the slot stays empty. ⚠️ Both vendors still count (`nyt` and `amazon-in`
        are the comics chart's spine), which is what makes the title admitted at all.
        """
        rows = [
            corroborate.Row(list="nyt/hardcover-fiction", rank=1, isbn="9788172151234", title="B"),
            corroborate.Row(list="amazon-in/indian-languages", rank=2, isbn="9788172151234", title="B"),
        ]

        result = corroborate.admit(rows, chart=charts.get("comics"))

        self.assertEqual(result.admitted[0].country, "")
        self.assertEqual(result.admitted[0].language, "")


if __name__ == "__main__":
    unittest.main()
