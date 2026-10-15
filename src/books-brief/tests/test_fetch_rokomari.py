"""Rokomari — the Bangladeshi bridge, and the only source that is neither DOM nor JSON at the top level.

⚠️ **The fixture is the raw flight**, escapes and all, because unescaping a JavaScript string literal is half of what
this parser does. ⚠️ A fixture built from already-decoded text would skip the step most likely to break — ticket 02's
warning about hand-built fixtures, applied to a payload rather than to markup.

⚠️ ⚠️ **And there are two fixtures now, because the record's shape changed one day later** (ticket 30, 2026-10-15).
`rokomari-flight.html` is the 2026-10-14 recording — the one that made this parser — and
`rokomari-flight-2026-10-15.html` is the 2026-10-15 one, which exists because the first stopped parsing: the store
inserted an **`adClickUrl` field between the product object and `productType`**, and the flat regex that found records
required them adjacent. ⚠️ **Both are kept**, because a parser that only survives the newest shape is a parser nobody
has tested against the shape it was written for.
"""
import json
import pathlib
import unicodedata
import unittest

from books_brief import charts, freshness
from books_brief.fetch import rokomari

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "rokomari-flight.html"
#: ⚠️ The second recording — see the module docstring. It carries **one** chunk, chosen because it is the smallest that
#: holds a book record (2.3 KB), so the fixture stays a few kilobytes.
SECOND = (
    pathlib.Path(__file__).resolve().parent
    / "fixtures"
    / "rokomari-flight-2026-10-15.html"
)

LISTING = charts.Listing(
    slug="rokomari/best-sellers",
    country="bd",
    language="bn",
    address="https://www.rokomari.com/book/category/72/best-seller-books",
)


def push(*records: str) -> bytes:
    """One flight chunk carrying `records`, escaped the way the page escapes them.

    ⚠️ **For the shapes neither recording contains, and never instead of them** — a nested product object, a record that
    is not a book, a brace inside a title. ⚠️ The escaping is the page's (`json.dumps` of a JS string literal), because
    that is the half of this parser a hand-built fixture must not skip.
    """
    literal = json.dumps("".join(records))
    return f"<script>self.__next_f.push([1,{literal}]);</script>".encode("utf-8")



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

    def test_the_cover_is_the_cards_own_image_and_not_the_placeholder(self):
        """⚠️ ⚠️ **The picture was in the card all along, and this parser left it there** (2026-10-15) — so every
        Rokomari row fell to ticket 07's branded tile while its cover sat a thousand characters earlier in the same card.

        ⚠️ **And it is `data-src`, not `src`**: the store lazy-loads, so `src` is `/nstatic/images/placeholder-image.gif`
        — ⚠️ a parser that read *that* would put **the same grey placeholder on every row**, which is a chart whose covers
        all look broken rather than one that is missing them. The assertion names the placeholder for that reason.
        """
        self.assertEqual(
            [row.cover_url for row in self.rows],
            [
                "https://rokbucket.rokomari.io/ProductNew20190903/130X186/923a19a70434_890.gif",
                "https://rokbucket.rokomari.io/ProductNew20190903/130X186/1bf45d109584_884.gif",
            ],
        )
        for row in self.rows:
            self.assertNotIn("placeholder", row.cover_url)

    def test_the_rows_are_undated_because_the_payload_states_no_date(self):
        """⚠️ ⚠️ **The fact that makes this vendor `LIVE`, and the correction is ticket 30's.**

        Nothing in the flight carries a publication date, so `published` is empty — and `freshness.is_fresh("")` is
        **False**, because an undated list is one the guard **cannot verify**.

        ⚠️ **This test used to conclude *"so the Bengali chart goes absent, which is the correct outcome"*, and that
        conclusion was wrong.** A retailer's own bestseller category is **regenerated per order**, so there is no dated
        artefact for a date to be missing *from* — which is exactly the case `charts.LIVE` exists for. ⚠️ The guard's
        finding is unchanged and still asserted; what changed is that `ROKOMARI` is named in the exemption, so the chart
        **builds** instead of being refused forever.
        """
        self.assertEqual([row.published for row in self.rows], ["", ""])
        self.assertFalse(freshness.is_fresh(self.rows[0].published, week="2026-W41"))
        self.assertIn(charts.ROKOMARI, charts.LIVE)

    def test_a_chunk_that_names_a_product_without_containing_one_is_not_a_row(self):
        """⚠️ **The opening `{"product":{` appears in the flight for things that are not books**, so the walk finds
        records the store renders for something else — and those are skipped rather than ranked.

        ⚠️ So the parser matches the **whole record** and then checks the marker: the fixture's records yield **two**
        rows, and two is the right answer. ⚠️ A parser that counted markers would have invented a book.
        """
        flight = rokomari.flight(FIXTURE.read_bytes())

        self.assertEqual(len(list(rokomari.records(flight))), 2)
        self.assertEqual(len(rokomari.parse(FIXTURE.read_bytes(), listing=LISTING)), 2)


class TheSecondRecording(unittest.TestCase):
    """⚠️ ⚠️ **Recorded 2026-10-15, one day after the first, because the record's shape changed** (ticket 30).

    ⚠️ The store inserted an **`adClickUrl` field between the product object and `productType`** — precisely where the old
    pattern demanded `,"productType"`. ⚠️ It then matched **nothing**: `parse` returned zero rows and
    `freshness.guard` reported Rokomari as **missing** rather than as broken. ⚠️ **A build is what found it** — the vendor
    had answered, the fetched page held 60 records, and the chart was still refused.
    """

    def test_todays_shape_parses_and_the_field_that_broke_it_is_named(self):
        raw = SECOND.read_text("utf-8")
        rows = rokomari.parse(SECOND.read_bytes(), listing=LISTING)

        self.assertIn('\\"adClickUrl\\"', raw, "the fixture must carry the field, or this tests nothing")
        self.assertEqual(len(rows), 1)
        self.assertEqual(nfc(rows[0].title), nfc("পুফি"))
        self.assertEqual(rows[0].isbn, "rokomari:873")
        self.assertEqual(rows[0].price.currency, "BDT")

    def test_the_card_that_broke_the_parser_still_carries_its_cover(self):
        """⚠️ **The second recording's own image**, so the cover rule is pinned against the newest page as well as the
        oldest.
        """
        rows = rokomari.parse(SECOND.read_bytes(), listing=LISTING)

        self.assertEqual(
            rows[0].cover_url,
            "https://rokbucket.rokomari.io/ProductNew20190903/130X186/img141210_873.gif",
        )

    def test_a_cover_belongs_to_its_own_card_and_never_the_previous_one(self):
        """⚠️ ⚠️ **The window rule, and it is the whole safety of this feature.** A card's picture sits *before* its
        record, so the last image in the window is this row's — ⚠️ and a card with **no** image of its own must leave the
        row **without** a cover rather than reaching back for the previous card's.

        ⚠️ A wrong cover is worse than a missing one: nobody looking at a slide can tell that the picture belongs to
        another book.
        """
        payload = push(
            '{"className":"x","data-src":"https://rokbucket.rokomari.io/first.jpg"}'
            '{"product":{"id":8,"title":"First"},"productType":"book"}'
            '{"product":{"id":9,"title":"Second"},"productType":"book"}'
        )

        rows = rokomari.parse(payload, listing=LISTING)

        self.assertEqual([row.title for row in rows], ["First", "Second"])
        self.assertEqual(
            [row.cover_url for row in rows], ["https://rokbucket.rokomari.io/first.jpg", ""]
        )

    def test_a_field_added_inside_the_product_object_is_survived_too(self):
        """⚠️ **The walk counts braces rather than describing a shape**, so a *nested* object inside `product` is not a
        second way to break it — which the flat regex could not have claimed.
        """
        payload = push(
            '{"product":{"id":3,"title":"Nested","meta":{"depth":1}},"productType":"book"}'
        )

        rows = rokomari.parse(payload, listing=LISTING)

        self.assertEqual([row.title for row in rows], ["Nested"])
        self.assertEqual([row.isbn for row in rows], ["rokomari:3"])

    def test_a_record_that_is_not_a_book_is_skipped(self):
        """⚠️ The marker is checked **after** the braces balance, so a record for something that is not a book is not
        this list's evidence — and does not become a row.
        """
        payload = push('{"product":{"id":4,"title":"A Magazine"},"productType":"magazine"}')

        self.assertEqual(rokomari.parse(payload, listing=LISTING), [])

    def test_a_brace_inside_a_title_does_not_swallow_the_records_after_it(self):
        """⚠️ ⚠️ **The reason the walk is string-aware.** A naive brace counter would read the `{` inside a quoted title
        as structure, never balance, and return **nothing** — the same silent failure the regex produced, arrived at
        differently. ⚠️ A title with a brace in it is not exotic; a title with a `}` is.
        """
        payload = push(
            '{"product":{"id":5,"title":"A { Brace"},"productType":"book"}'
            '{"product":{"id":6,"title":"After"},"productType":"book"}'
        )

        rows = rokomari.parse(payload, listing=LISTING)

        self.assertEqual([row.title for row in rows], ["A { Brace", "After"])
        self.assertEqual([row.rank for row in rows], [1, 2])


if __name__ == "__main__":
    unittest.main()
