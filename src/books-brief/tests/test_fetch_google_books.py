"""The Google Books parser — **ticket 17's enrichment source**, and the one that fills four of a row's fields.

⚠️ **Google Books is not a chart source and never can be.** Ticket 02 is explicit: it has *"no weekly cadence"* and gives
`publishedDate`, `publisher`, `authors`, hi-res `imageLinks` and `saleInfo` — so it is **enrichment, not a chart**. Ticket
17's per-field priority table names it for **publisher**, **publication date**, **cover**, **ISBN** and **genre**, and for
nothing else. ⚠️ It cannot corroborate a title's *sales*, because it has no sales.

⚠️ **Fetch and parse are separated, and only the parse is tested** — the boundary rule this package's own `__init__.py`
states, so the suite stays hermetic.

⚠️ **The fixture is hand-built from the API's documented schema, not recorded** — the same note `test_fetch_nyt.py`
carries, and the same reason: this is a **JSON API with a published field list**, not an undocumented HTML scrape. A real
recording should replace the file before the product ships, and nothing in the parser should have to change when it does.
⚠️ That distinction is the whole reason this client could be written and the five scrape parsers could not.
"""
import pathlib
import unittest

from books_brief.fetch import google_books

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "google-books-volume.json"


class ReadingOneVolume(unittest.TestCase):
    def test_a_volume_gives_the_fields_ticket_seventeen_gives_google_books(self):
        """⚠️ Exactly five fields, and each one is in the priority table: **publisher, publication date, cover, ISBN,
        genre**. A sixth would be this client claiming a field it has no business deciding.
        """
        volume = google_books.parse_volume(FIXTURE.read_bytes(), isbn="9788172151234")

        self.assertIsNotNone(volume)
        assert volume is not None
        self.assertEqual(volume.isbn, "9788172151234")
        self.assertEqual(volume.publisher, "Ananda Publishers")
        # ⚠️ The **source's own string**, never a label — `2026-10` becomes *Oct 2026* in the renderer (ADR 0003).
        self.assertEqual(volume.published, "2026-10")
        self.assertEqual(volume.author, "Sunil Gangopadhyay")
        self.assertEqual(volume.category, "Fiction / Literary")

    def test_the_cover_url_is_normalised_on_the_way_out(self):
        """⚠️ Ticket 05's three normalisations, and this is where they have to happen.

        Google Books hands back `http://`, a `zoom=1` thumbnail and `edge=curl` — which draws a decorative curled
        page-corner *into the picture*. A client that passed the URL through would put all three on a slide, so the
        normalisation is not a later step that someone might forget.
        """
        volume = google_books.parse_volume(FIXTURE.read_bytes(), isbn="9788172151234")

        assert volume is not None
        assert volume.cover_url is not None
        self.assertTrue(volume.cover_url.startswith("https://"))
        self.assertIn("zoom=2", volume.cover_url)
        self.assertNotIn("edge=curl", volume.cover_url)


class WhenGoogleBooksDisagrees(unittest.TestCase):
    def test_a_lookup_that_returns_a_different_isbn_is_not_a_match(self):
        """⚠️ **Ticket 17's identity rule, and it is the one that stops a cascade.**

        The lookup asks for one ISBN and Google Books answers with another — a mis-catalogue, or a fuzzy match on a
        search rather than a volume fetch. ⚠️ Accepting it would be the *"single fuzzy title search"* ticket 05 forbids:
        the wrong cover, the wrong pub date, and a corrupted week-over-week diff, all from a response that looks fine.
        """
        payload = FIXTURE.read_bytes().replace(b"9788172151234", b"9780000000002")

        self.assertIsNone(google_books.parse_volume(payload, isbn="9788172151234"))

    def test_a_volume_with_no_isbn_thirteen_is_not_a_match_either(self):
        """⚠️ The identity is the **ISBN-13**, normalised — an ISBN-10 alone is not the key everything else hangs on
        (ticket 05), so a volume carrying only one cannot resolve an identity.
        """
        payload = FIXTURE.read_bytes().replace(b'"ISBN_13"', b'"ISBN_10"')

        self.assertIsNone(google_books.parse_volume(payload, isbn="9788172151234"))

    def test_no_items_is_none_and_not_a_crash(self):
        """⚠️ An empty result is ordinary — plenty of books are not in Google Books — and it must be `None` rather than
        an exception, because a *failed lookup* is a field that omits (ticket 07) and not a chart that refuses.
        """
        self.assertIsNone(google_books.parse_volume(b'{"totalItems": 0}', isbn="9788172151234"))

    def test_a_volume_with_no_image_links_has_no_cover_and_not_an_empty_url(self):
        """⚠️ **An empty string would be a request to nowhere.** The renderer reaches ticket 07's branded tile by reading
        `cover: null`, so absence has to stay absent — an `""` would send it down the `Img` path and 404 the render.
        """
        payload = FIXTURE.read_bytes().replace(b'"imageLinks"', b'"somethingElse"')

        volume = google_books.parse_volume(payload, isbn="9788172151234")

        assert volume is not None
        self.assertIsNone(volume.cover_url)


if __name__ == "__main__":
    unittest.main()
