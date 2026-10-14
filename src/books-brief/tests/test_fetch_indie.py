"""The Indie Bestsellers parser — **the cleanest source in the set**, and the only one whose freshness is verifiable.

⚠️ A row carries **rank**, **title**, **author**, **publisher**, **price** and a **real ISBN-13**, where Amazon gives an
ASIN and PW gives a paywalled 2012 archive. ⚠️ **And the list is dated in its own URL** —
`/bestseller-list-v2/national/2026-10-14` — so the date the freshness guard needs is a fact about the *address* rather
than a field the vendor chose to publish.

⚠️ **The fixture is verbatim**: ranked rows of the National list for the week of 2026-10-14, unaltered, with the page's
other rows removed because a whole scraped page is ABA's content rather than ours.
"""
import pathlib
import unittest

from books_brief import charts
from books_brief.fetch import indie

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "indie-national.html"

#: ⚠️ The list is the **national** one, and it is the only list the site serves. ⚠️ **The address is the undated form**
#: (ticket 29) — `indie.fetch` appends the date the week implies, which is what makes this vendor's freshness verifiable.
LISTING = charts.Listing(
    slug="indie/national",
    country="us",
    language="en",
    address="https://www.indiebound.org/bestseller-list-v2/national",
)

WEEK = "2026-W41"


class WhenAListIsPublished(unittest.TestCase):
    def test_the_date_is_the_wednesday_after_the_week_closed(self):
        """⚠️ **Derived from the week key, never from a clock** (ADR 0003) — and it is the **end** of the freshness span
        rather than its start.

        A Sun–Sat week closes on Sunday, so the list compiled from it lands on the Wednesday following — which is what
        ticket 10 says about when these lists appear, and what the recorded page proves: the list for `2026-W41` is at
        `/national/2026-10-14`, and `freshness.span("2026-W41")` ends on exactly that date.

        ⚠️ **So this is the one vendor whose freshness the guard can verify from the response**, because the date is in
        the address rather than in a field the vendor may or may not have filled in.
        """
        self.assertEqual(indie.published_on(WEEK), "2026-10-14")
        self.assertEqual(indie.published_on(WEEK), indie.freshness.span(WEEK)[1])

    def test_the_derived_date_is_the_one_the_guard_accepts(self):
        """⚠️ **The two halves have to agree, and this is the assertion that says so.**

        A parser that derived a date outside `freshness.span` would produce rows the guard then discards — a source that
        fetches perfectly and is refused every week, which would look like a guard bug rather than an address bug.
        """
        self.assertTrue(indie.freshness.is_fresh(indie.published_on(WEEK), week=WEEK))


class ParsingTheNationalList(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = indie.parse(
            FIXTURE.read_bytes(), listing=LISTING, published=indie.published_on(WEEK)
        )

    def test_a_row_carries_its_rank_and_its_title(self):
        self.assertEqual([row.rank for row in self.rows], [1, 2, 3])
        self.assertEqual(
            [row.title for row in self.rows],
            [
                "Threshing Day (Wing and Claw Collection) (The Empyrean)",
                "The Witch (Deluxe Edition)",
                "The Pirate Queen",
            ],
        )

    def test_the_isbn_is_a_real_one_and_not_an_asin(self):
        """⚠️ **The difference that matters between this source and Amazon's.**

        Amazon's only identifier is an ASIN, which *happens* to be an ISBN-10 for a physical book and is not one at all
        for a Kindle edition. ⚠️ Indie Bestsellers publishes the **ISBN-13 itself**, so `enrich.isbn13` is a check here
        rather than a conversion — and a malformed one would still come back marked unresolved rather than trusted.
        """
        self.assertEqual(
            [row.isbn for row in self.rows],
            ["9781682818084", "9781464249648", "9780385550345"],
        )

    def test_the_price_is_a_value_and_the_retailer_is_the_list(self):
        """⚠️ Ticket 04 — `24.99`, not `$24.99`: the symbol belongs to the renderer (ADR 0003).

        ⚠️ **And the count is one**, which is what forbids the word *best*: Indie Bestsellers is a list, so a price off it
        was never compared with another shop's.
        """
        self.assertEqual([row.price.amount for row in self.rows], [24.99, 29.99, 32.0])
        self.assertEqual(self.rows[0].price.retailer, "indie")
        self.assertEqual(self.rows[0].price.retailers, ("indie",))
        # ⚠️ The list states no format, so the edition is absent rather than guessed at.
        self.assertIsNone(self.rows[0].price.edition)

    def test_the_price_carries_its_currency_and_it_is_not_rupees(self):
        """⚠️ ⚠️ **The defect this field exists for, and it was live in this very parser.**

        The row's amount is **24.99** and the page wrote **`$24.99`** — and until `Price.currency` existed the model had
        nothing to say about that, while the renderer drew `₹` for every price unconditionally. ⚠️ So this source's
        prices would have rendered as **₹24.99**: a dollar figure wearing a rupee sign, wrong by about eighty times, and
        completely unremarkable to look at.

        ⚠️ **The cause was a comment that cited a superseded ticket** — `prices.CURRENCY` said *"every chart is
        India-anchored (ticket 12)"* — and three later tickets had already overturned that (19, 20, 22). ⚠️ The code
        never noticed because nothing asked it to.
        """
        self.assertEqual([row.price.currency for row in self.rows], ["USD"] * 3)
        self.assertNotEqual(self.rows[0].price.currency, "INR")

    def test_the_rows_carry_the_date_the_list_was_published(self):
        """⚠️ **The date comes from the address, so the parser is told it rather than reading it.** The page carries no
        date of its own — the URL is the only thing that knows — which is the same shape as ticket 20's labels.
        """
        self.assertEqual([row.published for row in self.rows], ["2026-10-14"] * 3)

    def test_the_rows_carry_the_country_and_language_the_list_declares(self):
        self.assertEqual([row.country for row in self.rows], ["us"] * 3)
        self.assertEqual([row.language for row in self.rows], ["en"] * 3)


class WhatThePageCannotGive(unittest.TestCase):
    def test_a_page_with_no_ranked_rows_yields_nothing_rather_than_raising(self):
        """⚠️ An empty answer is not a crash — the same rule `amazon.parse` keeps, and for the same reason: a block page,
        a failed render and a genuinely empty list look identical from here, and `freshness.guard` already treats a
        vendor that produced nothing as **missing**.
        """
        self.assertEqual(indie.parse(b"<html><body>no rows</body></html>", listing=LISTING), [])

    def test_a_row_with_no_rank_is_skipped_rather_than_numbered(self):
        """⚠️ A position inferred from document order agrees with the badge on a clean page and disagrees silently on a
        page where a row failed to render — which is exactly when the rank matters most.

        ⚠️ **This test was a tautology for one run, and the reason is worth keeping.** The payload was built with
        `payload.replace(b'class="views-field-field-rank"', …)` — and the fixture's attribute is
        `class="views-field views-field-field-rank"`, so the search matched **nothing**, the replace changed nothing, and
        the parser correctly returned three rows for a payload that was never broken. ⚠️ A `bytes.replace` that silently
        no-ops turns an assertion into a tautology, so this now **asserts the payload changed** before parsing it.
        """
        payload = FIXTURE.read_bytes().replace(b"views-field-field-rank", b"rank-field-gone")

        self.assertNotEqual(payload, FIXTURE.read_bytes(), "the payload must actually be damaged")
        self.assertEqual(indie.parse(payload, listing=LISTING), [])


class FetchingAList(unittest.TestCase):
    def test_the_list_the_site_does_not_serve_cannot_be_declared_at_all(self):
        """⚠️ `charts.py` used to declare `indie/fiction` and `indie/nonfiction`; the site serves **one national list**.

        ⚠️ **The refusal is the point, and it moved to declaration time** (ticket 29). `indie.fetch` used to raise
        `MissingListError` for a slug it had no address for; now `charts.Listing` refuses to construct a scraped list
        without an address — so a fiction list cannot be declared unless somebody first finds where it lives. ⚠️ And
        falling back to the national list for a fiction chart would return a **real list of the wrong books**, which is
        the quietest wrong answer there is.
        """
        with self.assertRaises(ValueError) as raised:
            charts.Listing(slug="indie/fiction", country="us", language="en")

        self.assertIn("indie/fiction", str(raised.exception))

    def test_the_english_chart_reads_the_one_list_the_site_serves(self):
        """⚠️ **One list, not two** — the national one, at the **undated** address the client dates for itself.

        ⚠️ The date cannot live in the declaration, because only the conductor knows which week is being built — so the
        declaration states *where* the list is and `indie.fetch` appends *when*.
        """
        chart = charts.get("english")
        indie_lists = [entry for entry in chart.lists if entry.slug.startswith("indie/")]

        self.assertEqual([entry.slug for entry in indie_lists], ["indie/national"])
        self.assertEqual(
            indie_lists[0].address, "https://www.indiebound.org/bestseller-list-v2/national"
        )


if __name__ == "__main__":
    unittest.main()

