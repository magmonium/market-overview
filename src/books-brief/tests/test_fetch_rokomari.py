"""Rokomari — the Bangladeshi bridge, and the only source that is neither DOM nor JSON at the top level.

⚠️ **The fixture is the raw flight**, escapes and all, because unescaping a JavaScript string literal is half of what
this parser does. ⚠️ A fixture built from already-decoded text would skip the step most likely to break — ticket 02's
warning about hand-built fixtures, applied to a payload rather than to markup.
"""
import pathlib
import unicodedata
import unittest

from books_brief import charts, freshness
from books_brief.fetch import rokomari

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "rokomari-flight.html"

LISTING = charts.Listing(
    slug="rokomari/best-sellers",
    country="bd",
    language="bn",
    address="https://www.rokomari.com/book/category/72/best-seller-books",
)


def nfc(text: str) -> str:
    """⚠️ **Bengali has composing characters, and two strings that look identical may not compare equal.**

    `ময়ূরাক্ষী` contains `য়` (U+09DF), `ূ` (U+09C2) and the conjunct `ক্ষ` — and a literal typed into a test file and
    the bytes a vendor served can differ in normalisation while rendering the same on screen. ⚠️ **The first version of
    this test compared them raw and failed**, which is the *right* failure to have: comparing Unicode without normalising
    is how a test becomes a coin flip on the author's keyboard.
    """
    return unicodedata.normalize("NFC", text)


class ReadingTheFlight(unittest.TestCase):
    def test_the_chunks_are_unescaped_before_anything_is_read(self):
        """⚠️ **Half of this parser is undoing JavaScript's escaping**, and the fixture proves it: the raw file contains
        `\\"title\\":\\"ময়ূরাক্ষী\\"` and the flight contains `"title":"ময়ূরাক্ষী"`.

        ⚠️ A parser that skipped the step would find **no records at all** and report an empty list — which the guard
        would read as *this vendor has nothing*, the quietest possible wrong answer.
        """
        raw = FIXTURE.read_text("utf-8")
        flight = rokomari.flight(FIXTURE.read_bytes())

        self.assertIn('\\"productType\\"', raw, "the fixture must be escaped, or this tests nothing")
        self.assertNotIn('\\"productType\\"', flight)
        self.assertIn('"productType":"book"', flight)

    def test_a_chunk_that_will_not_parse_is_skipped_rather_than_fatal(self):
        """⚠️ One malformed chunk is not a reason to lose a whole list, and the records that survive are still true.

        ⚠️ **`"not json at all"` is *valid* JSON** — a bare string — so it decodes to itself rather than raising, and the
        flight keeps it. My first version of this test expected `""` and was simply wrong about what JSON accepts. ⚠️ A
        chunk that genuinely fails is one that is not a well-formed literal at all, which is what the second payload is.
        """
        self.assertEqual(rokomari.flight(b'<script>self.__next_f.push([1,"a bare string"]);</script>'), "a bare string")
        self.assertEqual(rokomari.flight(b'<script>self.__next_f.push([1,"unterminated]);</script>'), "")


class ParsingTheBestSellers(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = rokomari.parse(FIXTURE.read_bytes(), listing=LISTING)

    def test_the_rank_is_the_payload_order(self):
        """⚠️ **The one place in this product where the position *is* the rank — and the difference matters.**

        `amazon.parse` refuses to number cards by position because a card that failed to render shifts every rank after
        it. ⚠️ Amazon's cards **state** their rank in a badge, so position is a second, worse source. ⚠️ Rokomari's
        records state **no rank at all** — the payload *is* the ranking — so position is the only thing that carries it.
        ⚠️ The rules look contradictory and are not: **prefer a stated rank, and use the order only where the source has
        none.**
        """
        self.assertEqual([row.rank for row in self.rows], [1, 2])

    def test_a_row_carries_its_title_and_its_author(self):
        """⚠️ **`subTitle` is the author on this source**, which the recording is what established — a field named for
        one thing carrying another. ⚠️ Reading it as a subtitle would put an author's name where a book's title goes.

        ⚠️ Compared **normalised** — see `nfc`. The vendor's bytes and a typed literal can differ in composition while
        rendering identically, and an un-normalised comparison is a coin flip on which editor wrote the test.
        """
        self.assertEqual([nfc(row.title) for row in self.rows], [nfc("ময়ূরাক্ষী"), nfc("তোমাকে")])
        self.assertEqual([nfc(row.author) for row in self.rows], [nfc("হুমায়ূন আহমেদ")] * 2)

    def test_the_key_is_the_vendors_own_id_prefixed_because_it_is_not_an_isbn(self):
        """⚠️ **A bare `890` is three digits that could be a truncated ISBN**, so the vendor's id is namespaced.

        ⚠️ It is still a **real** identifier from the vendor — not the synthesised `title + author` key ticket 05 refuses
        — and `enrich.isbn13` returning `""` for it is what marks the row **unresolved** downstream.
        """
        self.assertEqual([row.isbn for row in self.rows], ["rokomari:890", "rokomari:884"])
        self.assertEqual(rokomari.enrich.isbn13(self.rows[0].isbn), "")

    def test_the_price_is_taka_and_says_so(self):
        """⚠️ ⚠️ **The field this whole source turned out to need.**

        The page quotes **৳180** — **Bangladeshi Taka** — and the row carries `180` with `BDT` beside it. ⚠️ Without the
        currency the slide would print **₹180**: wrong by about a factor of one and a half, on a chart that ranks a
        **Bangladeshi** list (ticket 29 — the Indian half, Anandabazar, could not be declared).
        """
        self.assertEqual([row.price.amount for row in self.rows], [180.0, 180.0])
        self.assertEqual([row.price.currency for row in self.rows], ["BDT"] * 2)
        self.assertEqual(self.rows[0].price.retailer, "rokomari")

    def test_the_rows_are_undated_because_the_payload_states_no_date(self):
        """⚠️ ⚠️ **The finding that makes this source unusable as it stands, and the guard is right to refuse it.**

        Nothing in the flight carries a publication date, so `published` is empty — and `freshness.is_fresh("")` is
        **False**, because an undated list is one the guard **cannot verify**. ⚠️ Ticket 10's rule is that a source must
        be verified to have published for the week being built, *"not trusted because the calendar says it is Tuesday."*

        ⚠️ So the Bengali chart goes **absent** rather than shipping a list of unknown vintage — which is the correct
        outcome, not a bug. Finding a date is what would make this source usable, and it is not a parser change.
        """
        self.assertEqual([row.published for row in self.rows], ["", ""])
        self.assertFalse(freshness.is_fresh(self.rows[0].published, week="2026-W41"))

    def test_a_chunk_that_names_a_product_without_containing_one_is_not_a_row(self):
        """⚠️ **The marker appears in the flight more often than the record does, and that is what caught this parser
        out.** A component *reference* — `["$","$L62","890",{…}]` — carries the product beside it, and a `productType`
        string can appear in a chunk that holds no product of its own.

        ⚠️ So the parser matches the **whole record**, not the marker: the fixture's three `productType`-bearing chunks
        yield **two** rows, and two is the right answer. ⚠️ A parser that counted markers would have invented a book.
        """
        self.assertEqual(len(rokomari.PRODUCT.findall(rokomari.flight(FIXTURE.read_bytes()))), 2)


if __name__ == "__main__":
    unittest.main()
