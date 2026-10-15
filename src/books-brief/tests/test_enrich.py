"""Ticket 05 — the identity key, and ticket 17's per-field priority.

⚠️ **The ISBN is the key everything hangs on**: ticket 14's dedupe (`chart + ISBN`), ticket 01's week-over-week diff,
and ticket 05's cover lookup all use it. So a wrong identity does not produce a wrong *field* — it produces a wrong
**row**, and the error cascades into the diff, where nothing would look wrong.
"""
import unittest

from books_brief import covers, enrich, prices, rank


class TheIdentityKey(unittest.TestCase):
    def test_an_isbn_ten_is_converted_to_its_isbn_thirteen(self):
        """⚠️ Ticket 05 — *"normalise ISBN-10 → ISBN-13 before it is ever used as a key."*

        The pair below is the canonical worked example: the ten-digit form and its thirteen-digit equivalent.

        ⚠️ **The check digit is recomputed, not copied.** An implementation that merely prefixed `978` and kept the old
        check digit would produce a plausible-looking string that matches no real ISBN — the quietest possible failure,
        because nothing downstream could tell it from a correct one.
        """
        self.assertEqual(enrich.isbn13("0306406152"), "9780306406157")

    def test_the_key_is_the_digits_however_they_were_punctuated(self):
        """⚠️ ISBNs arrive hyphenated, spaced and bare from five different vendors, and the key must be **one** string.

        ⚠️ And a string that is not an ISBN yields **`""`, not a guess** — the caller then knows the identity is
        unresolved and can mark the row, which a fabricated key would make impossible to detect.
        """
        self.assertEqual(enrich.isbn13("0-306-40615-2"), "9780306406157")
        self.assertEqual(enrich.isbn13("9780306406157"), "9780306406157")
        self.assertEqual(enrich.isbn13("not an isbn"), "")

    def test_an_isbn_ten_ending_in_x_is_still_ten_digits(self):
        """⚠️ An ISBN-10's check digit can be **X**, standing for ten — `043942089X` is a real one.

        The digit is *dropped* in the conversion, but it still has to be **counted**: strip it and a valid ISBN-10
        reads as nine digits, so the function rejects it as not-an-ISBN and the title loses its identity entirely. The
        mutation that removed this branch passed every other test in the file.
        """
        self.assertEqual(enrich.isbn13("043942089X"), "9780439420891")


def ranked(*isbns: str) -> tuple[rank.Ranked, ...]:
    """A ranked board's rows, one per ISBN, so a row can be built without a network."""
    return tuple(
        rank.Ranked(key=isbn, isbn=isbn, rank=number + 1, weeks_on_chart=0, is_new=False)
        for number, isbn in enumerate(isbns)
    )


class ThePublicationDate(unittest.TestCase):
    def test_the_source_date_is_carried_through_untouched(self):
        """⚠️ Ticket 05 §2 — *"render the precision that exists"* — and the **rendering** is the renderer's job.

        ⚠️ **This is ADR 0003, and it is the rule most easily broken by good intentions.** The snapshot carries
        *values*; the words a viewer reads live in the renderer's label tables. So the row keeps the source's own
        string — `2026-10-14`, `2026-10`, `2026` — and the slide decides whether that prints as *14 Oct 2026*, *Oct
        2026* or *2026*.

        ⚠️ **Nothing is lost by not formatting here**, which is the test that this split is in the right place: all
        three precisions survive verbatim, so the renderer can print any of them. A `published_label()` in this module
        would have been the tempting version, and it would have put three English month strings in the committed
        evidence of a Bengali chart.
        """
        books = enrich.build(
            ranked("9788172151234", "9780000000002", "9780000000003"),
            details={
                "9788172151234": enrich.Details(published="2026-10-14"),
                "9780000000002": enrich.Details(published="2026-10"),
                "9780000000003": enrich.Details(published="2026"),
            },
            previous=None,
        )

        self.assertEqual(
            [book.published for book in books], ["2026-10-14", "2026-10", "2026"]
        )

    def test_a_title_with_no_pub_date_omits_the_field_rather_than_blank_filling_it(self):
        """⚠️ Ticket 05 — *"the field is **omitted** — never blank-filled, never guessed."*

        ⚠️ And the omission is **structural, not cosmetic**: ticket 07 rules that a field with no value does not render
        and leaves no hole, so `None` is what lets the price line move up into the space instead of a gap appearing
        where a date should be.
        """
        books = enrich.build(ranked("9788172151234"), details={}, previous=None)

        self.assertIsNone(books[0].published)


class TheRow(unittest.TestCase):
    """The shape the renderer reads — ticket 07's eight fields, on one row."""

    def test_a_row_carries_every_field_the_slide_prints(self):
        """⚠️ **The gap this test exists to close.** `rank.Ranked` carries `isbn`, `rank`, `weeks_on_chart` and
        `is_new` — **two** of the eight fields ticket 07's slide prints.

        ⚠️ `corroborate.Row` *does* carry the title, and the conductor used to drop it: a chart of ISBNs renders as a
        rank numeral beside blank space, which is why this is asserted field by field rather than by a row count.
        """
        books = enrich.build(
            ranked("9788172151234"),
            details={
                "9788172151234": enrich.Details(
                    title="Ekti Shonar Boi",
                    author="Sunil Gangopadhyay",
                    publisher="Ananda Publishers",
                    published="2026-10",
                    category="Literature & Fiction",
                    price=prices.Price(
                        amount=399.0,
                        retailer="amazon-in",
                        edition="paperback",
                        retailers=("amazon-in",),
                    ),
                )
            },
            previous={"9788172151234": 10},
        )

        row = books[0]
        self.assertEqual(row.rank, 1)
        self.assertEqual(row.move, 9)
        self.assertEqual(row.title, "Ekti Shonar Boi")
        self.assertEqual(row.author, "Sunil Gangopadhyay")
        self.assertEqual(row.publisher, "Ananda Publishers")
        self.assertEqual(row.published, "2026-10")
        # ⚠️ The genre is the **slug**, never the vendor's words — the renderer's label table owns the display string
        # (ADR 0003), so renaming a genre is a copy change and not a data migration.
        self.assertEqual(row.genre, "fiction")
        self.assertEqual(row.price.amount, 399.0)

    def test_a_title_with_no_isbn_is_marked_unresolved_and_still_gets_a_row(self):
        """⚠️ Ticket 05 §3 — *"no ISBN at all → fall back to normalised `title + author` as the identity key and mark
        the entry `identity: unresolved`, so the weakness is visible rather than silent."*

        ⚠️ **The row is not dropped**, which is the half that matters: the book is genuinely on the vendor's chart, and
        discarding it would make the chart quietly shorter than the list it claims to rank.
        """
        books = enrich.build(
            ranked("sunil-gangopadhyay/ekti-shonar-boi"),
            details={
                "sunil-gangopadhyay/ekti-shonar-boi": enrich.Details(title="Ekti Shonar Boi")
            },
            previous=None,
        )

        self.assertEqual(books[0].identity, "unresolved")
        self.assertEqual(books[0].title, "Ekti Shonar Boi")

    def test_a_resolved_isbn_says_so(self):
        books = enrich.build(
            ranked("9788172151234"), details={}, previous=None
        )

        self.assertEqual(books[0].identity, "resolved")


    def test_a_missing_detail_costs_the_field_and_never_the_row(self):
        """⚠️ Ticket 07's rule, one level down from the layout: a field with no value is omitted, not filled.

        ⚠️ **And it is not the same rule as ticket 18's spine.** A *vendor* going down makes the chart absent — *"a
        degraded chart is a wrong chart"* — while a missing **field** is ordinary: Amazon.in omits prices, NYT carries no
        pub date, and neither is a reason to lose a book that both sources agree is selling.
        """
        books = enrich.build(ranked("9788172151234"), details={}, previous=None)

        row = books[0]
        self.assertEqual(row.rank, 1)
        self.assertEqual(row.title, "")
        self.assertIsNone(row.published)
        self.assertIsNone(row.price.amount)
        self.assertIsNone(row.cover)

    def test_week_one_reports_no_move_at_all(self):
        """⚠️ Ticket 18 — with no previous chart *"every row carries no Δ and no NEW badge"*.

        The row still carries `is_new`, because the admission rule sets it — but `move` is `None` for the whole
        week, which is what lets the renderer tell a stated baseline from a normal week.
        """
        books = enrich.build(ranked("9788172151234"), details={}, previous=None)

        self.assertIsNone(books[0].move)


class TheCoverage(unittest.TestCase):
    def test_coverage_counts_the_rows_that_have_a_cover(self):
        """⚠️ Ticket 05 §4 — *"the pipeline must publish a coverage count per chart (`97/100` covers), so ticket 16's
        missing-cover rule has a number to work with rather than a surprise."*

        ⚠️ **Ticket 16 makes it actionable rather than informational**: if the count is low enough that the thumbnail's
        hero row is mostly placeholder, the collage is not representative of the chart — so the number is *reported*,
        and a chart below the floor is one to look at before publishing.
        """
        books = enrich.build(
            ranked("9788172151234", "9780000000002", "9780000000003"),
            details={
                "9788172151234": enrich.Details(
                    cover=covers.Cover(url="https://example.test/a.jpg", sha256="a")
                ),
                "9780000000002": enrich.Details(
                    cover=covers.Cover(url="https://example.test/b.jpg", sha256="b")
                ),
            },
            previous=None,
        )

        self.assertEqual(enrich.coverage(books), 2)


class TheCountryAndTheLanguage(unittest.TestCase):
    """⚠️ Ticket 20's two labels, travelling the same road the publisher does.

    ⚠️ **They reach `enrich.build` on `Details`, not as a new parameter.** The conductor reads them off the gate's
    `Title` — which is where they are already decided — and puts them on the `Details` it is building anyway, so this
    module stays a **pure function of what it was handed** and the merge grows no second lookup.
    """

    def test_the_row_carries_the_country_and_language_it_was_given(self):
        books = enrich.build(
            ranked("9788172151234"),
            details={
                "9788172151234": enrich.Details(title="B", country="bd", language="bn")
            },
            previous=None,
        )

        self.assertEqual(books[0].country, "bd")
        self.assertEqual(books[0].language, "bn")

    def test_a_row_with_no_country_omits_rather_than_guessing(self):
        """⚠️ Empty, and the renderer reads empty as *no label* — the same case as a constant one (ticket 20). A
        defaulted `in` would put a country on every row of every chart, including the English chart's, where ticket 19
        says neither label should appear.
        """
        books = enrich.build(ranked("9788172151234"), details={}, previous=None)

        self.assertEqual(books[0].country, "")
        self.assertEqual(books[0].language, "")


if __name__ == "__main__":
    unittest.main()
