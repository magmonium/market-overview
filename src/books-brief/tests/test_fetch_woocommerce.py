"""The booksellers' ranking parser — **the second vendor the Bengali chart was missing** (ticket 30).

⚠️ **The fixture is verbatim, and it is an extract.** Three whole product objects from the response
`boichitro.in/wp-json/wc/store/v1/products?orderby=popularity&per_page=100` actually served on **2026-10-15**, unaltered —
chosen to be the three that exercise the parser's decisions (a real ISBN, a mangled one, and none at all) and chosen
*short*: a Store API record carries its whole `description`, its `tags`, its `srcset` strings and its `_links`, so a
hundred of them is a megabyte and even **three is 28 KB — the largest fixture in this suite**. ⚠️ **That is stated rather
than trimmed**, because the records are the evidence and a record with its fields removed is no longer what the vendor
served (ADR 0002's own rule). ⚠️ Nothing in them was edited.

⚠️ **Fetch and parse are separated, and only the parse is tested** — the brief's own discipline, so the suite stays
hermetic. ⚠️ The one `fetch` test mocks `requests.get`, because a boundary that is never exercised is a boundary that is
assumed (the lesson `test_fetch_amazon.py` learned from a `NameError`).
"""
import json
import pathlib
import unittest
from unittest import mock

from books_brief import charts
from books_brief.fetch import woocommerce

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "boichitro-bestsellers.json"

#: ⚠️ The list the fixture came from. **The store's endpoint names no list**, so unlike NYT this cannot come from the
#: response: the declaration is the only thing that knows which address was read — and for a *located* list the address
#: is its identity (ticket 29).
#:
#: ⚠️ **The language is empty, and that is the chart's own declaration**: a Bengali bookshop's bestseller list carries
#: English rows too, so a `bn` here would be confidently wrong on some of them (ticket 20 — a constant label *renders*).
LISTING = charts.Listing(
    slug="boichitro/bestsellers",
    country="in",
    language="",
    address="https://boichitro.in/wp-json/wc/store/v1/products?orderby=popularity&per_page=100",
)


def payload(*products: dict) -> bytes:
    """A synthetic response — **for the cases the recording does not contain**, never instead of it."""
    return json.dumps(list(products)).encode("utf-8")


def record(**overrides) -> dict:
    """One minimal product, with a field replaced where a test is about that field."""
    product = {
        "id": 1,
        "name": "A Title || An Author",
        "sku": "Publisher1",
        "prices": {"price": "100", "currency_code": "INR"},
        "average_rating": "0",
        "review_count": 0,
        "images": [],
        "attributes": [],
    }
    product.update(overrides)
    return product

class ParsingARecordedRanking(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = woocommerce.parse(FIXTURE.read_bytes(), listing=LISTING)

    def test_the_response_becomes_rows_at_the_stores_own_positions(self):
        """⚠️ ⚠️ **The position *is* the rank, and that is the opposite of `amazon.parse`'s rule.**

        Amazon renders a `#1` badge, and a parser that numbered the cards would disagree silently with it on a page
        where one card failed to render. ⚠️ A JSON array has no failed cards: its order *is* the store's own statement,
        so numbering it is reading rather than inferring.
        """
        self.assertEqual(len(self.rows), 3)
        self.assertEqual([row.rank for row in self.rows], [1, 2, 3])

    def test_the_title_is_the_first_segment_and_never_the_whole_name(self):
        """⚠️ A store concatenates its own fields into `name`, so printing it whole would put
        `Bangalir Duggapujo || Subham Bhattacharjee || …` on a slide as a **title**.
        """
        self.assertEqual(
            [row.title for row in self.rows],
            ["Anamika Bole Dakte Pari Ki Tomay", "NARACH", "Bangalir Duggapujo"],
        )

    def test_the_author_is_the_attribute_rather_than_the_second_segment(self):
        """⚠️ **A field, not a guess.** The segment count is not consistent across records — some carry two, some four —
        so reading the second `||` segment would take an author off one record and a Bengali title off the next.
        """
        self.assertEqual(
            [row.author for row in self.rows],
            ["Rupam Islam", "Debarati Mukhopadhyay", "Subham Bhattacharjee"],
        )

    def test_a_real_isbn_is_the_key_so_another_vendor_can_meet_the_row(self):
        """⚠️ **This is what makes the vendor corroborate** — an Amazon.in row and this one join on an ISBN rather than on
        a title, which is ticket 05's whole point.
        """
        self.assertEqual(self.rows[2].isbn, "9789348544704")

    def test_a_mangled_isbn_falls_back_to_the_stores_key_and_is_never_repaired(self):
        """⚠️ ⚠️ **The recorded trap.** One product states its ISBN as `9.79E 12` — a number that has been through a
        spreadsheet's scientific notation and lost digits it cannot get back.

        ⚠️ **It is not reconstructed.** A repaired ISBN is a guess wearing a check digit, and ticket 05's rule is that an
        unresolved identity is *marked* rather than invented — so the row keeps the store's own prefixed key, exactly as
        `amazon.parse` keeps an ASIN that is not an ISBN.
        """
        self.assertEqual(self.rows[1].isbn, "boichitro:Patra Bharati15422")
        self.assertNotIn("979", self.rows[1].isbn)

    def test_a_record_with_no_isbn_keeps_the_stores_own_key_prefixed(self):
        """⚠️ **Prefixed, because a bare `5519` is a number that could collide with any other store's numbering** — the
        rule `rokomari.parse` reached first.
        """
        self.assertEqual(self.rows[0].isbn, "boichitro:Deep Prakashan5519")

    def test_the_price_carries_the_currency_the_store_quoted(self):
        """⚠️ **Read off the payload, unlike `amazon.MARKETPLACES`.** The Store API states `currency_code` per product, so
        there is nothing here for a table to get wrong — and ⚠️ the *retailer* is set only where a price was found, so an
        unpriced row cannot claim a comparison that did not happen (ticket 04).
        """
        self.assertEqual([row.price.amount for row in self.rows], [206.0, 319.0, 224.0])
        self.assertEqual({row.price.currency for row in self.rows}, {"INR"})
        self.assertEqual({row.price.retailer for row in self.rows}, {"boichitro"})
        self.assertEqual(self.rows[0].price.retailers, ("boichitro",))
        # ⚠️ The format rides with the price, because a price without it is not a price — and the third record states no
        # binding at all, so its edition is absent rather than defaulted.
        self.assertEqual([row.price.edition for row in self.rows], ["Hardcover", "Hardcover", None])

    def test_the_reviews_and_the_cover_ride_along(self):
        self.assertEqual([row.ratings_count for row in self.rows], [5, 7, 48])
        self.assertEqual([row.rating for row in self.rows], [5.0, 4.4, 4.85])
        self.assertTrue(all(row.cover_url.startswith("https://boichitro.in/") for row in self.rows))

    def test_the_labels_come_from_the_declaration(self):
        """⚠️ A store's endpoint names no list and states no country, so ticket 20's labels have nowhere else to come
        from — and ⚠️ **the language stays empty**, because the list is mixed and empty draws no label.
        """
        self.assertEqual({row.country for row in self.rows}, {"in"})
        self.assertEqual({row.language for row in self.rows}, {""})

    def test_the_list_states_no_date_and_the_rows_say_so(self):
        """⚠️ ⚠️ **The fact that makes this vendor `LIVE`.** Nothing in the response is dated, so every row arrives
        undated — and ⚠️ that is not an omission to be papered over with the run's own week: an undated row on a vendor
        that is *not* live is **stale**, which is ticket 10's rule and the reason `charts.LIVE` has to name this store.
        """
        self.assertEqual({row.published for row in self.rows}, {""})
        self.assertIn("boichitro", charts.LIVE)


class ParsingWhatTheRecordingDoesNotContain(unittest.TestCase):
    """⚠️ Synthetic records, and only for cases the three recorded ones cannot show — the fixture stays the evidence."""

    def test_an_unrated_book_is_absent_rather_than_zero(self):
        """⚠️ **`rank.review_term`'s own rule.** A title nobody has rated has not been judged average; a `0.0` here would
        be a judgement, and it would let an unrated book outrank a rated one.
        """
        rows = woocommerce.parse(payload(record(average_rating="0", review_count=0)), listing=LISTING)

        self.assertIsNone(rows[0].rating)
        self.assertIsNone(rows[0].ratings_count)

    def test_an_unpriced_record_claims_no_retailer(self):
        """⚠️ Absence, not zero — and no retailer, so the slide cannot say *best* off a listing that had no price."""
        rows = woocommerce.parse(
            payload(record(prices={"price": "", "currency_code": "INR"})), listing=LISTING
        )

        self.assertIsNone(rows[0].price.amount)
        self.assertIsNone(rows[0].price.retailer)
        self.assertEqual(rows[0].price.retailers, ())
        self.assertEqual(rows[0].price.currency, "")

    def test_a_sku_that_is_a_real_isbn_is_the_key(self):
        """⚠️ ⚠️ **Bangabani's case, and the reason it was worth declaring** (ticket 32).

        BoiChitro publishes its ISBN in a `pa_isbn` **attribute**; Bangabani publishes **no attributes at all** and puts
        a real ISBN-13 in **`sku`** — on **54 of its first 100** records, measured by fetching the address the chart
        declares. ⚠️ `_key` tries the SKU *second*, so this path is what gives half that store's rows an identity another
        vendor can corroborate on. ⚠️ And a *stock code* in the same field must not be mistaken for an ISBN, which is
        what the neighbouring tests hold.
        """
        rows = woocommerce.parse(payload(record(sku="9789354254741")), listing=LISTING)

        self.assertEqual([row.isbn for row in rows], ["9789354254741"])

    def test_a_record_with_no_sku_falls_back_to_the_stores_own_product_id(self):
        """⚠️ **The last resort, and it is `rokomari.parse`'s precedent** — a retailer's own product id is a real, stable
        identifier, so a record with no ISBN and no SKU is still **keyed** rather than dropped. ⚠️ Writing this test is
        what found that: the first version asserted a record with an empty `sku` was *unkeyable*, and the parser
        disagreed — correctly, because `id` is right there in the payload.
        """
        rows = woocommerce.parse(payload(record(id=907, sku="")), listing=LISTING)

        self.assertEqual(rows[0].isbn, "boichitro:907")

    def test_the_position_survives_a_record_that_cannot_be_keyed(self):
        """⚠️ ⚠️ **A skipped record does not pull the rest up.** The store's position is a fact about the *list*, so a
        product with **no identifier at all** — no ISBN, no SKU, no id — leaves a **gap** in the ranks rather than
        silently promoting every title after it.
        """
        rows = woocommerce.parse(
            payload(
                record(id=11, name="First || A", sku="Publisher11"),
                record(id=None, name="Second || B", sku=""),
                record(id=13, name="Third || C", sku="Publisher13"),
            ),
            listing=LISTING,
        )

        self.assertEqual([row.title for row in rows], ["First", "Third"])
        self.assertEqual([row.rank for row in rows], [1, 3])

    def test_a_record_with_no_title_at_all_is_skipped(self):
        """⚠️ A title is what the slide prints, so a record without one is not a row — and its place is not reused."""
        rows = woocommerce.parse(
            payload(record(id=11, name="  || A"), record(id=12, name="Kept || B", sku="K12")),
            listing=LISTING,
        )

        self.assertEqual([row.title for row in rows], ["Kept"])
        self.assertEqual([row.rank for row in rows], [2])

    def test_a_body_that_is_not_a_ranking_returns_nothing_rather_than_raising(self):
        """⚠️ A block page, a failed render and a genuine empty list look identical from here — and a parser that raised
        would take the other charts with it. `freshness.guard` already treats *nothing* as a **missing vendor**.
        """
        for body in (b"", b"<html>blocked</html>", b'{"error":"not a list"}', b"null", b"["):
            with self.subTest(body=body):
                self.assertEqual(woocommerce.parse(body, listing=LISTING), [])

    def test_a_store_that_writes_na_has_no_author_rather_than_the_word(self):
        """⚠️ Boighar writes `N/A` where it has no author, which is **absence wearing a word** — `"N/A"` printed on a
        slide is a worse answer than a slot the renderer omits (ticket 07). ⚠️ And the skip reaches the second attribute,
        which is where Boighar sometimes puts the real one.
        """
        attributes = [
            {"taxonomy": "pa_authorname", "terms": [{"name": "N/A"}]},
            {"taxonomy": "pa_author-2", "terms": [{"name": "Hindol Bhattacharya"}]},
        ]
        rows = woocommerce.parse(payload(record(attributes=attributes)), listing=LISTING)

        self.assertEqual(rows[0].author, "Hindol Bhattacharya")

        bare = woocommerce.parse(
            payload(record(attributes=[{"taxonomy": "pa_authorname", "terms": [{"name": "N/A"}]}])),
            listing=LISTING,
        )
        self.assertEqual(bare[0].author, "")


class TheBoundary(unittest.TestCase):
    def test_a_store_this_client_does_not_read_is_not_ours(self):
        self.assertTrue(woocommerce.owns("boichitro/bestsellers"))
        self.assertTrue(woocommerce.owns("boighar/bestsellers"))
        self.assertFalse(woocommerce.owns("nyt/hardcover-fiction"))
        self.assertFalse(woocommerce.owns("rokomari/best-sellers"))

    def test_a_chart_declaring_no_store_list_is_not_fetched_at_all(self):
        """⚠️ A vendor reads **its own** lists — the guard `nyt.fetch` keeps — so a chart that declares two vendors does
        not make each of them complain about the other's lists.
        """
        self.assertEqual(list(woocommerce.fetch(charts.get("english"), week="2026-W41")), [])

    def test_fetch_reads_the_store_the_chart_declares(self):
        """⚠️ ⚠️ **The boundary, exercised hermetically** — `requests.get` is mocked, so this reaches nothing.

        ⚠️ **It is here because `test_fetch_amazon.py` shipped a `NameError` in exactly this function and nothing caught
        it**: the parse tests never touch `fetch`, and the skip test uses a chart with no Amazon list. ⚠️ A boundary that
        is never exercised is a boundary that is assumed.
        """
        chart = charts.get("bengali")
        expected = {
            entry.slug.split("/", 1)[0]
            for entry in chart.lists
            if woocommerce.owns(entry.slug)
        }
        # ⚠️ **Two stores, one module** (ticket 32) — declaring Bangabani was *naming* it, not writing a client, and
        # this assertion is what keeps that claim honest: both lists are fetched by the same code path.
        self.assertEqual(expected, {"boichitro", "bangabani"})

        with mock.patch.object(woocommerce.requests, "get") as get:
            get.return_value.raise_for_status = mock.Mock()
            get.return_value.content = FIXTURE.read_bytes()

            pages = list(woocommerce.fetch(chart, week="2026-W41"))

        self.assertEqual(
            [page.listing.slug for page in pages], ["boichitro/bestsellers", "bangabani/best-sellers"]
        )
        # ⚠️ **`call_args_list`, not `call_args`**: with two stores fetched, `call_args` is only the *last* call, so the
        # loop below would compare every page against Bangabani's address and pass for the wrong reason.
        self.assertEqual(
            [call.args[0] for call in get.call_args_list],
            [page.listing.address for page in pages],
        )
        # ⚠️ And Rokomari's list was **not** fetched: a vendor reads its own lists.
        self.assertEqual(get.call_count, len(pages))

    def test_an_address_without_the_ordering_is_refused_rather_than_fetched(self):
        """⚠️ ⚠️ **The one parameter that makes these lists rankings, enforced at *fetch* time** (ticket 32).

        A store's endpoint *is* its list only because of `orderby=popularity`: drop that parameter and the same URL is
        the shop's newest-arrivals page, which would rank a chart by recency and look entirely correct while doing it.
        ⚠️ `test_the_declared_address_is_the_stores_own_popularity_ranking` checks the *declared* address; this checks
        the **fetch**, and it is here because ticket 32 added a second store to this client — a declaration that forgot
        the parameter would otherwise have been a silent reordering of the whole chart, and the existing test only ever
        looked at BoiChitro's address.
        """
        chart = charts.Chart(
            slug="bengali",
            label_key="bengali",
            market="india+bangladesh",
            language="bn",
            vendors=(charts.BOICHITRO,),
            lists=(
                charts.Listing(
                    slug="boichitro/bestsellers",
                    country="in",
                    language="",
                    address="https://boichitro.in/wp-json/wc/store/v1/products?per_page=100",
                ),
            ),
        )

        with self.assertRaises(ValueError) as raised:
            list(woocommerce.fetch(chart, week="2026-W41"))

        self.assertIn("orderby", str(raised.exception))

    def test_a_store_list_declared_without_an_address_is_refused(self):
        """⚠️ **The constructor is the rule**, so a store declared without an address is a declaration error rather than
        a run that silently fetches nothing (ticket 29's rule, extended to a located JSON list in ticket 30).
        """
        with self.assertRaises(ValueError) as raised:
            charts.Listing(slug="boichitro/bestsellers", country="in", language="")

        self.assertIn("address", str(raised.exception))

    def test_the_declared_address_is_the_stores_own_popularity_ranking(self):
        """⚠️ ⚠️ **The one thing about this source that a reader cannot see from the slug.** `boichitro/bestsellers` names
        nothing — ticket 29's finding, one level down — and the **address** is what says this is a hundred-deep
        *popularity* ranking rather than the same shop's newest-arrivals page.

        ⚠️ **So `ORDERBY` and `DEPTH` are checked against the declaration rather than merely documented beside it**: an
        address that quietly asked for `orderby=date`, or for thirty products, would fail here. ⚠️ That is the
        constructor's discipline applied to a list whose address cannot be derived from its name — *"the address is the
        list's identity"*, and an identity nobody checks is a comment.
        """
        listing = next(
            entry
            for chart in charts.ALL
            for entry in chart.lists
            if entry.slug == "boichitro/bestsellers"
        )

        self.assertIn(f"orderby={woocommerce.ORDERBY}", listing.address)
        self.assertIn(f"per_page={woocommerce.DEPTH}", listing.address)


if __name__ == "__main__":
    unittest.main()

