"""The Amazon bestseller parser — the workhorse, and the only free per-country English source there is.

⚠️ ⚠️ **One parser, five marketplaces** (2026-10-15). The fixture below is `amazon.in`'s, and it is parsed for **every**
store: `amazon.com`, `amazon.co.uk`, `amazon.ca` and `amazon.com.au` serve the **same card markup** — verified by fetching
all five (30 ranked cards each) — so the selectors are one module's knowledge of one page shape rather than five copies of
it. ⚠️ What differs per store is the **currency**, which the declaration supplies (`amazon.MARKETPLACES`) and the page is
now **checked against** — see `CURRENCIES`, and `TheCurrencyIsCheckedAndNotAssumed` below for the bug that rule fixes.

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
from unittest import mock

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

#: ⚠️ ⚠️ **Two more verbatim recordings, and they are why the currency rule changed** (2026-10-15).
#:
#: `amazon-us-english.html` is `amazon.com`'s own page for the week, and every price on it reads **`HUF 7,249.11`**:
#: Amazon prices the *viewer* rather than the store, so the constant labelled a forint amount as dollars.
#: ⚠️ `amazon-ca-english.html` is the other shape — a **bare `$`** — which is the ambiguity `MARKETPLACES` exists for.
#: The two together are the whole rule: a stated currency is checked, and an ambiguous one is decided by the declaration.
HUF_PAGE = pathlib.Path(__file__).resolve().parent / "fixtures" / "amazon-us-english.html"
DOLLAR_PAGE = pathlib.Path(__file__).resolve().parent / "fixtures" / "amazon-ca-english.html"

#: ⚠️ **The same fixture parsed as other marketplaces** (2026-10-15). The markup is identical — that is the finding — so
#: the only thing under test is what the **declaration** changes: the vendor on the row and the currency on its price.
UK = charts.Listing(
    slug="amazon-uk/english",
    country="gb",
    language="en",
    address="https://www.amazon.co.uk/gp/bestsellers/books/",
)
CA = charts.Listing(
    slug="amazon-ca/english",
    country="ca",
    language="en",
    address="https://www.amazon.ca/gp/bestsellers/books/",
)
AU = charts.Listing(
    slug="amazon-au/english",
    country="au",
    language="en",
    address="https://www.amazon.com.au/gp/bestsellers/books/",
)
#: ⚠️ The US store — the declaration the **HUF** page contradicts.
US = charts.Listing(
    slug="amazon-us/english",
    country="us",
    language="en",
    address="https://www.amazon.com/gp/bestsellers/books/",
)
#: ⚠️ A marketplace `MARKETPLACES` does not name, so its rows must carry **no** currency rather than a guessed one.
UNKNOWN = charts.Listing(
    slug="amazon-nz/english",
    country="nz",
    language="en",
    address="https://www.amazon.co.nz/gp/bestsellers/books/",
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

    def test_the_cover_is_asked_for_at_full_size_rather_than_the_card_s_thumbnail(self):
        """⚠️ ⚠️ **A card's `<img src>` is a 300×200 thumbnail of a portrait cover** (2026-10-15).

        ⚠️ It is the *grid's* box and not the cover's shape, and the same asset **without its size token** is the
        original: measured, `…UL300_SR300,200_.jpg` answers **300×200 / 6 KB** while `….jpg` answers **1600×2155 /
        201 KB**. ⚠️ So a collage built from the card's own `src` was **twenty-five times fewer pixels in the wrong
        aspect ratio** — *"the covers look bad"*, and the cause was one URL suffix.
        """
        rows = amazon.parse(FIXTURE.read_bytes(), listing=LISTING)

        self.assertEqual(
            rows[0].cover_url,
            "https://images-eu.ssl-images-amazon.com/images/I/71My1M0AgZL.jpg",
        )
        self.assertNotIn("._AC_", rows[0].cover_url)

    def test_a_cover_url_with_no_size_token_is_left_alone(self):
        """⚠️ **The rule is Amazon's own path shape, not a dot-underscore anywhere.** A bookshop's `My._Book.jpg` is a
        real URL and stripping it would 404 the vendor the Bengali chart depends on — so the match is anchored on
        `/images/I/<id>._<token>.<ext>` and nothing else.
        """
        for url in (
            "https://boichitro.in/wp-content/uploads/My._Book.jpg",
            "https://images-eu.ssl-images-amazon.com/images/I/71My1M0AgZL.jpg",
            "https://cdn.shopify.com/s/files/1/2/3/products/cover.jpg?v=17",
        ):
            with self.subTest(url=url):
                self.assertEqual(amazon._cover_url(url), url)


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


class TheCurrencyIsCheckedAndNotAssumed(unittest.TestCase):
    """⚠️ ⚠️ **`MARKETPLACES` is a claim about the store, and the page can contradict it** (2026-10-15).

    ⚠️ It was written as *"each marketplace quotes its own currency"*, and that is false for two of the five:
    `amazon.com` and `amazon.co.uk` **price the viewer**, and the recorded 2026-W41 pages for both quote **HUF**. The
    constant labelled `HUF 7,249.11` as `$7,249.11` on 13 rows of the shipped English chart — ticket 19's own named
    failure, live — so the rule is now: **the page is asked, and a contradiction drops the price rather than relabelling
    it.**

    ⚠️ **And the half that did not change.** A bare `$` is not evidence — `amazon.com`, `amazon.ca` and `amazon.com.au`
    all print one — so the declaration still decides *which* dollars, and the tests below keep that property with a
    recording that really does print a bare `$`.
    """

    def test_a_bare_dollar_is_resolved_by_the_declaration(self):
        """⚠️ **The ambiguity, kept** — the Canadian page prints `$33.60`, and only the *slug* can say CAD."""
        rows = amazon.parse(DOLLAR_PAGE.read_bytes(), listing=CA)

        self.assertEqual(rows[0].price.currency, "CAD")
        self.assertEqual(rows[0].price.amount, 33.60)
        self.assertEqual(rows[0].price.retailer, "amazon-ca")
        self.assertEqual(rows[0].price.retailers, ("amazon-ca",))

    def test_one_page_read_as_two_dollar_stores_carries_two_currencies(self):
        """⚠️ **The property `MARKETPLACES` exists for**, and the reason a bare `$` must not be read as *no evidence of a
        currency*: the same bytes, the same digits, and the declaration decides what money they are.
        """
        rows = amazon.parse(DOLLAR_PAGE.read_bytes(), listing=AU)

        self.assertEqual(rows[0].price.currency, "AUD")
        self.assertEqual(rows[0].price.amount, 33.60)
        self.assertEqual(rows[0].price.retailer, "amazon-au")

    def test_a_page_stating_a_currency_the_store_does_not_quote_loses_its_price(self):
        """⚠️ ⚠️ **The bug this rule was written for, asserted against the recording that found it.**

        `amazon.com` served `HUF 7,249.11` — a forint price, because Amazon prices the *viewer* — and the constant
        turned it into `$7,249.11`. ⚠️ The row survives with everything else; only the caption goes, because a wrong
        number is worse than a missing field (ticket 07) and the price is a caption, never a ranking input (ticket 04).
        """
        rows = amazon.parse(HUF_PAGE.read_bytes(), listing=US)

        self.assertEqual(len(rows), 2, "the rows themselves are not the price's business")
        self.assertEqual(rows[0].rank, 1)
        self.assertTrue(rows[0].title)
        self.assertIsNone(rows[0].price.amount)
        self.assertIsNone(rows[0].price.retailer)
        self.assertEqual(rows[0].price.retailers, ())
        # ⚠️ The currency stays the *store's*, because that is what the field means — what the amount would be in.
        self.assertEqual(rows[0].price.currency, "USD")

    def test_the_indian_page_parsed_as_another_store_loses_its_price_too(self):
        """⚠️ **The same rule one store over — and it reverses the assertion that used to live here.**

        This was `test_a_uk_row_is_priced_in_pounds_and_names_the_uk_store`, which parsed the **Indian** fixture as
        `amazon-uk` and asserted `GBP`: the declaration overriding a page that plainly says `₹329.00`. ⚠️ That test was
        the bug's own alibi — it encoded *"the declaration wins"* as a virtue, so nothing ever asked what the page said.
        ⚠️ It is kept in substance and reversed: the ₹ contradicts the pound, so the price goes.
        """
        rows = amazon.parse(FIXTURE.read_bytes(), listing=UK)

        self.assertIsNone(rows[0].price.amount)
        self.assertIsNone(rows[0].price.retailer)
        self.assertEqual(rows[0].price.currency, "GBP")
        self.assertEqual(rows[0].country, "gb")

    def test_an_unknown_marketplace_gets_no_currency_rather_than_a_wrong_one(self):
        """⚠️ Unchanged, and deliberately: a slug `MARKETPLACES` does not name leaves the currency **empty**, which draws
        no symbol (ADR 0003) — the same degrade an unknown genre or country keeps, because visibly wrong beats silently
        wrong. ⚠️ The check above needs a *claim* to contradict, and an unlisted marketplace makes none.
        """
        rows = amazon.parse(FIXTURE.read_bytes(), listing=UNKNOWN)

        self.assertEqual(rows[0].price.currency, "")
        self.assertEqual(rows[0].price.retailer, "amazon-nz")


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

    def test_the_stores_are_asked_one_at_a_time(self):
        """⚠️ ⚠️ **A pause between requests — and it was measured, not imagined** (ticket 34).

        ⚠️ The comics chart reads **eight** storefronts, and a burst of eight back-to-back requests returned an **empty
        page for one of them** — `200`, a valid title, and no cards at all — while the same address answered 30 ranked
        cards a few seconds later. ⚠️ An empty store is a *missing source*, and ticket 18 makes a chart with a missing
        source **absent**, so this pause protects the *chart* rather than the server. ⚠️ It is a delay and not a retry:
        a retry would hide a genuine outage behind a second attempt, and the failure must stay visible.

        ⚠️ **Between requests, never before the first** — eight stores is seven pauses, and a chart declaring one store
        must not pay for another chart's eight.
        """
        chart = charts.get("comics")

        with (
            mock.patch.object(amazon, "requests") as requests_mock,
            mock.patch.object(amazon, "time") as time_mock,
        ):
            requests_mock.get.return_value.content = FIXTURE.read_bytes()

            pages = list(amazon.fetch(chart, week="2026-W41"))

        self.assertEqual(len(pages), 8, "the comics chart reads eight Amazon storefronts")
        self.assertEqual(time_mock.sleep.call_count, 7)
        self.assertEqual(time_mock.sleep.call_args.args, (amazon.PAUSE_SECONDS,))
        # ⚠️ And every page carries the address it was read from — the list's identity, for a vendor whose pages name
        # no list at all.
        self.assertEqual(
            [page.listing.slug for page in pages],
            [entry.slug for entry in chart.lists if entry.slug.startswith("amazon-")],
        )

    def test_a_list_the_vendor_does_not_own_is_skipped_without_a_complaint(self):
        """⚠️ A vendor reads **its own** lists, the same guard `nyt.fetch` keeps — so a chart that declares two vendors
        does not make each of them complain about the other's lists.

        ⚠️ **This used to be asserted against the `english` chart, and it cannot be any more** (2026-10-15): the English
        chart now declares four Amazon stores, so `amazon.fetch` on it would spend a fetch — and a test that reaches the
        network is the one thing this suite must never do. ⚠️ The `bengali` chart is the right subject now: it declares
        `rokomari` and `boichitro` and no Amazon store, so there is genuinely nothing here for Amazon to read.
        """
        chart = charts.get("bengali")

        # ⚠️ The one list belongs to Rokomari, so there is nothing for Amazon to read — and no refusal, because a missing
        # *list* is not the same as a list that has no address.
        self.assertEqual(list(amazon.fetch(chart, week="2026-W41")), [])

    def test_fetch_reads_every_marketplace_the_chart_declares(self):
        """⚠️ ⚠️ **The boundary, exercised hermetically** — `requests.get` is mocked, so this reaches nothing.

        ⚠️ **This test exists because the refactor that generalised the client shipped a `NameError`**: the check moved
        from `vendor != VENDOR` to `owns(slug)` and the `vendor` binding the *filename* needs was left behind. ⚠️ Nothing
        caught it, because no other test runs `fetch` against a chart that declares an Amazon list — the parse tests never
        touch `fetch`, and the skip test uses `bengali`. ⚠️ A boundary that is never exercised is a boundary that is
        assumed, so it is exercised here with the network faked.
        """
        chart = charts.get("english")
        expected = {
            entry.slug.split("/", 1)[0] for entry in chart.lists if amazon.owns(entry.slug)
        }

        with mock.patch.object(amazon.requests, "get") as get, mock.patch.object(amazon, "time") as time_mock:
            get.return_value.raise_for_status = mock.Mock()
            get.return_value.content = FIXTURE.read_bytes()

            pages = list(amazon.fetch(chart, week="2026-W41"))

        # ⚠️ **And the pause is faked here too** (ticket 34): four stores would otherwise put three real `sleep`s in a
        # suite whose whole point is that it is instant and reaches nothing.
        self.assertEqual(time_mock.sleep.call_count, len(pages) - 1)

        # ⚠️ One page per Amazon list the chart declares, and the filename carries the marketplace — which is what the
        # `NameError` above broke.
        self.assertEqual({page.listing.slug.split("/", 1)[0] for page in pages}, expected)
        for page in pages:
            with self.subTest(list=page.listing.slug):
                self.assertTrue(page.name.startswith(page.listing.slug.split("/", 1)[0]))
                self.assertTrue(page.name.endswith(".html"))
        # ⚠️ And NYT's and Indie's lists were **not** fetched: a vendor reads its own lists.
        self.assertEqual(get.call_count, len(pages))

    def test_every_amazon_list_a_chart_declares_states_an_address(self):
        """⚠️ **A table that can drift from the charts is a table that will** — which is why there is no longer a table.

        This test used to compare `charts.py`'s declarations against an `amazon.NODES` map, and ⚠️ **the two had already
        drifted**: the chart declared nine per-language lists Amazon does not publish while the map named the one it
        does, and neither could tell the other it was wrong. ⚠️ The address now lives in the declaration and nowhere
        else, so what is left to check is that every Amazon list a chart reads says where it is.

        ⚠️ **And every one of them names a marketplace `MARKETPLACES` knows** (2026-10-15), because that table is what
        supplies the row's currency — a store missing from it would leave its prices unsigned rather than wrong, but it
        would still be a declaration nobody can price.

        ⚠️ ⚠️ **And every one of them is `LIVE`** (ticket 34). A store's ranking states no date because there is nothing
        to date, so without the exemption the freshness guard discards every row and the chart goes **absent** — which is
        how `comics` and `all-language` spent their first weeks. ⚠️ The two halves belong in one test because they are
        one contract: *"an Amazon list is a live ranking the declaration can price"*.
        """
        declared = [
            entry for chart in charts.ALL for entry in chart.lists if amazon.owns(entry.slug)
        ]

        self.assertTrue(declared, "no chart declares an Amazon list — this test would pass vacuously")
        for entry in declared:
            with self.subTest(list=entry.slug):
                vendor = entry.slug.split("/", 1)[0]
                self.assertTrue(entry.address, f"{entry.slug} declares no address")
                self.assertIn(vendor, amazon.MARKETPLACES, f"{entry.slug} names a marketplace with no currency")
                self.assertIn(vendor, charts.LIVE, f"{entry.slug} is a store ranking and must be exempt from the date")

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
                if not amazon.owns(entry.slug):
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
            if amazon.owns(entry.slug)
        }

        for slug in ("amazon-in/hindi", "amazon-in/bengali", "amazon-in/tamil", "amazon-in/telugu"):
            with self.subTest(list=slug):
                self.assertNotIn(slug, declared)


if __name__ == "__main__":
    unittest.main()

