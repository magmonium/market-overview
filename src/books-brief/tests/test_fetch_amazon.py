"""The Amazon.in parser — the workhorse, and the only source three of the four charts depend on.

⚠️ **Fetch and parse are separated, and only the parse is tested** — the brief's own discipline (`_degrade(day, name,
fetch, parse, default)`), because a parser is a pure function of bytes and the suite stays hermetic.

⚠️ **The fixture is verbatim, and that is the point.** Ticket 02's warning: Amazon's HTML is undocumented, and *"a
fixture built from the rendered text would pass its test and fail on the real page."* So `tests/fixtures/
amazon-in-comics.html` is three of the thirty cards Amazon actually served, unaltered — see its own header for the URL
and the date.

⚠️ **And this is the first HTML in the product.** Every source the brief reads is a JSON API, so there was no parser in
the environment at all — `selectolax` is a dependency of `books-brief` alone, and its `lexbor` backend is the one that
is not deprecated in 1.0.
"""
import pathlib
import unittest

from books_brief import charts, prices
from books_brief.fetch import amazon

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "amazon-in-comics.html"

#: ⚠️ The list the fixture came from — `Comics & Mangas` at node `1318104031`. **Amazon's page names no list**, so unlike
#: NYT this cannot come from the response: the declaration is the only thing that knows which address was read.
#: ⚠️ **The address is part of it** (ticket 29), because for a scraped vendor the address *is* the list's identity.
LISTING = charts.Listing(
    slug="amazon-in/comics",
    country="in",
    language="en",
    address="https://www.amazon.in/gp/bestsellers/books/1318104031/",
)


class ParsingAListPage(unittest.TestCase):
    def test_a_page_becomes_rows_with_a_rank_and_a_title(self):
        """⚠️ **The title is the card's own title node — not the image's `alt`, which is a different string.**

        ⚠️ Card one renders `… (Pop-Up And Lift The Flap)` in its title div while its `<img alt>` reads
        `… (Pop-Up And Lift The Flap Board Book)` — two strings on one card, and the *alt* is the longer one. ⚠️ **I
        wrote the alt's version into this expectation first, decided the parser was truncating, and "fixed" it** — the
        recording showed the parser was right and my expectation was not. It is the third time this session that a
        hand-typed expectation was the defect rather than the code, and the shape is always the same: the fixture is a
        fact and the expectation is a memory.
        """
        rows = amazon.parse(FIXTURE.read_bytes(), listing=LISTING)

        self.assertEqual(len(rows), 3)
        self.assertEqual([row.rank for row in rows], [1, 2, 3])
        self.assertEqual(
            [row.title for row in rows],
            [
                "101 Tales The Great Panchatantra Collection - Collection Of Witty Moral Stories For Kids For "
                "Personality Development (Hardback)",
                "Pee-Ka-Boo | Pop-Up Baby Animals (Pop-Up And Lift The Flap)",
                "Diary of a Wimpy Kid: Fight or Flight (Book 21): Greg Heffley\u2019s Funniest School Adventure Yet | "
                "Bestselling Kids Illustrated Series for Ages 7\u201312: THE NEXT HILARIOUS BOOK IN THE BESTSELLING "
                "SERIES",
            ],
        )

    def test_the_rank_comes_from_the_badge_and_not_from_the_page_order(self):
        """⚠️ **The badge is the vendor's own statement; the order is an inference.**

        Amazon renders `#1`, `#2`, `#3` in `zg-bdg-text`, and a parser that numbered the cards by their position in the
        document would agree with the badge on a clean page and disagree silently on a page where a card failed to
        render — which is exactly when the rank matters most.
        """
        rows = amazon.parse(FIXTURE.read_bytes(), listing=LISTING)

        self.assertEqual([row.rank for row in rows], [1, 2, 3])

    def test_the_asin_is_the_key_and_a_book_asin_is_its_isbn_ten(self):
        """⚠️ **Amazon's only identifier is an ASIN — and ticket 05 says the ISBN is the key everything hangs on.**

        ✅ The two coincide for a physical book: `9390093953` is an ISBN-10, and `enrich.isbn13` converts it. ⚠️ They do
        **not** coincide for a Kindle edition, whose ASIN (`B08N67G4CC`) is not an ISBN at all — and that row keeps the
        ASIN as its key and is marked **unresolved** by `enrich.build`, which is ticket 05's documented fallback rather
        than a new mechanism.

        ⚠️ **The expected check digits were wrong when I first wrote them**, and the code was right: they are *computed*
        by `_check_digit`, and a hand-typed thirteen-digit string that merely looks plausible is exactly the failure
        ticket 05 warns about — *"a plausible string matching no real book, and nothing downstream could tell."*
        """
        rows = amazon.parse(FIXTURE.read_bytes(), listing=LISTING)

        self.assertEqual(
            [row.isbn for row in rows],
            ["9789390093953", "9789362142771", "9780241745212"],
        )

    def test_a_non_isbn_asin_keeps_the_asin_rather_than_being_dropped(self):
        """⚠️ **A Kindle ASIN is a real identifier from the vendor, not a missing one.**

        Ticket 05 refuses to *synthesise* a key that two books could share — a `title + author` string. An ASIN is
        neither synthesised nor shared: it is the vendor's own, and it is stable. So the row keeps it, and
        `enrich.isbn13` returning `""` for it is what marks the identity **unresolved** downstream.
        """
        payload = FIXTURE.read_bytes().replace(b'data-asin="9390093953"', b'data-asin="B08N67G4CC"')

        rows = amazon.parse(payload, listing=LISTING)

        self.assertEqual(rows[0].isbn, "B08N67G4CC")

    def test_the_row_carries_the_country_and_language_the_list_declares(self):
        """⚠️ Ticket 20 — from the declaration, because an Amazon page names no geography either."""
        rows = amazon.parse(FIXTURE.read_bytes(), listing=LISTING)

        self.assertEqual([row.country for row in rows], ["in"] * 3)
        self.assertEqual([row.language for row in rows], ["en"] * 3)

    def test_the_row_carries_the_list_it_was_asked_for(self):
        """⚠️ **The opposite of the NYT rule, and for a reason.**

        NYT's response carries `list_name_encoded`, so the row is tagged with what the vendor *said* and a mismatch is
        visible. ⚠️ An Amazon bestseller page carries **no list name at all** — the address is the only thing that knows
        — so the declaration is the only honest source, and a wrong address would be invisible either way.
        """
        rows = amazon.parse(FIXTURE.read_bytes(), listing=LISTING)

        self.assertTrue(all(row.list == "amazon-in/comics" for row in rows))


class WhatTheCardCarries(unittest.TestCase):
    """⚠️ **The reason the recording was worth doing: the card carries more than the chart's skeleton.**

    ⚠️ These fields ride on `corroborate.Row` for the module's own stated reason — *"a field dropped here cannot be
    recovered later"*, which is the argument `author` already makes. ⚠️ And they are **the source's own**, which is what
    ticket 17's per-field priority needs: *"the vendor that published the list the title ranked on"* comes first, and
    Google Books is the second opinion.
    """

    def setUp(self) -> None:
        self.rows = amazon.parse(FIXTURE.read_bytes(), listing=LISTING)

    def test_the_price_arrives_as_a_number_and_a_currency_that_was_stripped(self):
        """⚠️ **Ticket 04 was never blocked — only unlocated.**

        The card renders `₹329.00`, and the row carries `329.0` with the retailer and the edition beside it, because
        ticket 04's rule is that a price the slide prints is a *value*: the symbol, the grouping and the sign belong to
        the renderer (ADR 0003). ⚠️ And the edition is the format Amazon states — `Hardcover`, `Board book` — which is
        the same string the slide already has a slot for.
        """
        first = self.rows[0].price

        self.assertEqual(first.amount, 329.0)
        self.assertEqual(first.retailer, "amazon-in")
        self.assertEqual(first.edition, "Hardcover")
        # ⚠️ One retailer, so ticket 04 forbids the word *best* — the count is what the renderer reads to decide.
        self.assertEqual(first.retailers, ("amazon-in",))
        self.assertEqual(self.rows[1].price.edition, "Board book")

    def test_the_review_signal_is_the_source_s_own(self):
        """⚠️ **Ticket 23's review term, arriving from the list rather than from a second lookup.**

        Amazon renders `aria-label="4.5 out of 5 stars, 3,661 ratings"` — both halves of the Bayesian average in one
        attribute, which is exactly the shape `rank.review_term` needs and the reason a ratings *count* is not optional.
        """
        self.assertEqual(self.rows[0].rating, 4.5)
        self.assertEqual(self.rows[0].ratings_count, 3661)
        self.assertEqual(self.rows[1].rating, 4.2)
        self.assertEqual(self.rows[1].ratings_count, 340)

    def test_an_unrated_book_is_absent_rather_than_zero(self):
        """⚠️ **The fixture has a real unrated card, and it is worth more than a constructed one.**

        The third card carries no star row at all. ⚠️ `0.0` would say *this book is rated zero* — a claim the vendor did
        not make — and ticket 23's rule is that **unrated is not penalised**. `None` is the absence, and the Bayesian
        average already treats it as *no opinion* rather than as a bad one.
        """
        self.assertIsNone(self.rows[2].rating)
        self.assertIsNone(self.rows[2].ratings_count)

    def test_the_publisher_and_the_cover_come_from_the_card(self):
        """⚠️ Two fields that would otherwise be Google Books' second opinion — and the cover in particular, because the
        list's own image is the one the vendor chose to represent the title it ranked.
        """
        self.assertEqual(self.rows[0].publisher, "Wonder House Books")
        self.assertEqual(self.rows[2].publisher, "Jeff Kinney")
        self.assertTrue(self.rows[0].cover_url.startswith("https://images-eu.ssl-images-amazon.com/images/I/"))


class WhatThePageCannotGive(unittest.TestCase):
    def test_a_page_with_no_cards_yields_no_rows_rather_than_raising(self):
        """⚠️ **An empty answer is not a crash.** Amazon serves a real page, a block page and a page whose cards failed
        to render, and all three look alike from here — so the parser returns nothing and lets the caller decide.

        ⚠️ And the caller has already decided: `freshness.guard` treats a vendor that produced nothing as **missing**,
        which makes the chart absent (ticket 18). A parser that raised would take the other three charts with it.
        """
        self.assertEqual(amazon.parse(b"<html><body>no cards here</body></html>", listing=LISTING), [])

    def test_a_card_with_no_rank_badge_is_skipped_rather_than_guessed(self):
        """⚠️ **A card with no badge is a card whose position nobody stated.**

        Numbering it by its place in the document is the inference this parser exists to avoid — and on a page where one
        card failed to render, the inference would be wrong for every card after it. So the row is dropped, and the
        chart is one short rather than silently mis-ranked.
        """
        payload = FIXTURE.read_bytes().replace(b'<span class="zg-bdg-text">#1</span>', b"<span></span>")

        rows = amazon.parse(payload, listing=LISTING)

        self.assertEqual([row.rank for row in rows], [2, 3])


class FetchingAList(unittest.TestCase):
    """⚠️ The network half — and the only part of it the suite touches is the **refusal**, because nothing here reaches
    a vendor. `parse` is the seam and it is fully tested above; `fetch` is the boundary and it is tested for the one
    thing it decides without a network: **whether it knows where the list is.**
    """

    def test_a_scraped_list_with_no_address_cannot_be_declared_at_all(self):
        """⚠️ **The refusal moved from `fetch` to the declaration, and that is the point** (ticket 29).

        `amazon.fetch` used to raise `MissingNodeError` for a list it had no node for — which meant a wrong declaration
        was discovered only once a run spent a fetch on it. ⚠️ Now `charts.Listing` refuses to *exist* without an address
        for a scraped vendor, so the drift ticket 29 found — `amazon-in/hindi` and eight more, naming lists Amazon does
        not publish — **cannot be written down at all**.
        """
        with self.assertRaises(ValueError) as raised:
            charts.Listing(slug="amazon-in/bengali", country="in", language="bn")

        self.assertIn("amazon-in/bengali", str(raised.exception))
        self.assertIn("address", str(raised.exception))

    def test_a_list_the_vendor_does_not_own_is_skipped_without_a_complaint(self):
        """⚠️ A vendor reads **its own** lists, the same guard `nyt.fetch` keeps — so a chart that declares two vendors
        does not make each of them complain about the other's lists.
        """
        chart = charts.get("english")

        # ⚠️ Every list here belongs to NYT, PW or Indie, so there is nothing for Amazon to read — and no refusal,
        # because a missing *list* is not the same as a list that has no address.
        self.assertEqual(list(amazon.fetch(chart, week="2026-W41")), [])

    def test_every_amazon_in_list_a_chart_declares_states_an_address(self):
        """⚠️ **A table that can drift from the charts is a table that will** — which is why there is no longer a table.

        This test used to compare `charts.py`'s declarations against an `amazon.NODES` map, and ⚠️ **the two had already
        drifted**: the chart declared nine per-language lists Amazon does not publish while the map named the one it
        does, and neither could tell the other it was wrong. ⚠️ The address now lives in the declaration and nowhere
        else, so what is left to check is that every `amazon-in` list a chart reads says where it is.
        """
        declared = [
            entry
            for chart in charts.ALL
            for entry in chart.lists
            if entry.slug.startswith(f"{amazon.VENDOR}/")
        ]

        self.assertTrue(declared, "no chart declares an Amazon.in list — this test would pass vacuously")
        for entry in declared:
            with self.subTest(list=entry.slug):
                self.assertTrue(entry.address, f"{entry.slug} declares no address")

    def test_the_all_language_chart_reads_the_one_mixed_ranking(self):
        """⚠️ **The nine lists became one, and the chart now reads the one that exists.**

        Ticket 02 declared `amazon-in/hindi`, `…/bengali`, `…/tamil` and six more for the all-language chart. ⚠️ **Amazon
        publishes no per-language bestseller list at all** — its books nav has no language category, the Indian-languages
        node has no children, and the only per-language address is an unordered search with no rank badges. ⚠️ What it
        publishes is **one mixed-language ranking**, which the chart now reads — and that is what takes the chart from
        nine sources to one, and makes its failure to satisfy the two-vendor gate permanent.
        """
        chart = charts.get("all-language")

        self.assertEqual(len(chart.lists), 1)
        self.assertEqual(chart.lists[0].slug, "amazon-in/indian-languages")
        self.assertIn("86946561031", chart.lists[0].address)

    def test_the_addresses_are_the_bestseller_service_and_not_the_search_one(self):
        """⚠️ `…/s?rh=…` carries a bestseller **sort**, which is a different object from a bestseller **list** — and a
        chart that ranked search results would be claiming something Amazon did not say.

        ⚠️ Asserted against the **declarations**, because that is where an address lives now (ticket 29) — the module
        constant this used to read is gone.
        """
        for chart in charts.ALL:
            for entry in chart.lists:
                if not entry.slug.startswith(f"{amazon.VENDOR}/"):
                    continue
                with self.subTest(list=entry.slug):
                    self.assertIn("/gp/bestsellers/books/", entry.address)
                    self.assertNotIn("/s?", entry.address)

    def test_the_ten_lists_amazon_does_not_publish_are_gone_rather_than_expected_to_fail(self):
        """⚠️ **This test used to be an `expectedFailure`, and it is the one that closed ticket 29.**

        It asserted that ten `amazon-in/*` lists had no address — nine per-language ones for the all-language chart and
        one for the Bengali chart — and it was deliberately left failing, because *"a comment in a ticket is read once; a
        suite that reports one expected failure is read on every run."* ⚠️ **The answer arrived, and the answer was that
        the declarations were wrong rather than the addresses missing.** ⚠️ So the ten are gone: the all-language chart
        reads the one mixed ranking Amazon publishes, and the Bengali chart declares no Amazon.in list at all.

        ⚠️ **And the guard that replaces it is a constructor**, not a test: `charts.Listing` refuses a scraped list
        without an address, so `amazon-in/hindi` cannot be reintroduced by anyone who has not first found the page it
        lives at.
        """
        declared = {
            entry.slug
            for chart in charts.ALL
            for entry in chart.lists
            if entry.slug.startswith(f"{amazon.VENDOR}/")
        }

        for slug in ("amazon-in/hindi", "amazon-in/bengali", "amazon-in/tamil", "amazon-in/telugu"):
            with self.subTest(list=slug):
                self.assertNotIn(slug, declared)


if __name__ == "__main__":
    unittest.main()

