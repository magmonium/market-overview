"""Ticket 12 — the four charts. And ticket 17's sharpest rule, encoded as data.

⚠️ **The charts are data, and the data carries the rule.** Ticket 17 counts corroboration by **vendor**, not by list:
Amazon.in's nine language categories are nine *lists* and **one source**. Encoding that distinction in the chart
definitions is what stops a later reader counting nine and believing it.
"""
import unittest

from books_brief import charts


class TheFourCharts(unittest.TestCase):
    def test_the_all_language_chart_ranks_one_list_from_one_vendor(self):
        """⚠️ Ticket 17's rule in one assertion.

        Counting a vendor's several lists as several corroborating sources would be *"a lie told in arithmetic"* — and it
        is why the all-language chart cannot satisfy the two-vendor gate on its own (ticket 17's rule 3).

        ⚠️ **It is one list now, not nine** (ticket 29). Ticket 02 declared nine per-language categories for this chart;
        Amazon publishes **one mixed-language ranking**, and the correction took the chart from nine lists to one — which
        makes its failure to reach the gate **permanent** rather than accidental.
        """
        chart = charts.get("all-language")

        self.assertEqual(len(chart.lists), 1)
        self.assertEqual(chart.vendors, ("amazon-in",))

    def test_the_comics_chart_declares_a_live_us_list_beside_the_monthly_one(self):
        """⚠️ ⚠️ **What makes `comics` build every week, and then what widens it to four regions** (tickets 33, 34).

        The chart declared `nyt` + `amazon-in`, and its NYT half is **monthly** — so for three weeks in four the guard
        found no fresh list from NYT and ticket 18 made the whole chart absent. ⚠️ Ticket 33 added Amazon.com's **print**
        Comics node (`4366`: 30 ranked cards, 22 real ISBN-13s) and ticket 34 answered the operator's *"from different
        country europe amerika uk india and create list"* with **eight storefronts** — one per country, because a store
        is a vendor.

        ⚠️ **Every node id here was read off the store's own category tree and then fetched**, because they are
        locale-specific and the guess is what broke the comics chart in the first place.
        """
        chart = charts.get("comics")

        self.assertEqual(
            chart.vendors,
            ("nyt", "amazon-us", "amazon-uk", "amazon-ca", "amazon-de", "amazon-fr", "amazon-it", "amazon-es", "amazon-in"),
        )
        self.assertEqual(
            [entry.slug for entry in chart.lists],
            [
                "nyt/graphic-books-and-manga",
                "amazon-us/comics",
                "amazon-uk/comics",
                "amazon-ca/comics",
                "amazon-de/comics",
                "amazon-fr/comics",
                "amazon-it/comics",
                "amazon-es/comics",
                "amazon-in/comics",
            ],
        )
        # ⚠️ Every Amazon list is **live**, so it is exempt from the date check — which is what a store ranking is.
        for vendor in chart.vendors:
            if vendor.startswith("amazon-"):
                with self.subTest(vendor=vendor):
                    self.assertIn(vendor, charts.LIVE)

    def test_every_amazon_store_a_chart_declares_is_priced_and_live(self):
        """⚠️ **The invariant moved to where it can see the client** (ticket 34).

        ⚠️ It was written here first, and then deleted: `test_fetch_amazon`'s
        `test_every_amazon_list_a_chart_declares_states_an_address` already asserts the same contract, and **two tests
        for one rule is the drift this table's own history warns about**. ⚠️ What that test now covers is both halves —
        the store is named in `MARKETPLACES` (so its rows carry a currency) *and* it is in `LIVE` (so the guard does not
        ask a store ranking for a date it never states).

        ⚠️ **Why it mattered enough to write twice**: declaring the four European stores without a `MARKETPLACES` entry
        would not have failed anything — `currency` would simply have been **empty**, the documented *unknown* degrade,
        and `amazon.de`'s `HUF 5,711.66` would have printed as a bare `5711.66`. ⚠️ The rule was correct and tested; the
        **table** was what fell behind, and only a test that reads both can notice.
        """
        for chart in charts.ALL:
            for entry in chart.lists:
                vendor = entry.slug.partition("/")[0]
                if vendor.startswith("amazon-"):
                    with self.subTest(list=entry.slug):
                        self.assertIn(vendor, charts.LIVE, f"{entry.slug} is a store ranking and must be live")


class TheCadenceEveryListDeclares(unittest.TestCase):
    """⚠️ ⚠️ **Ticket 22's source table called NYT's graphic-books list *weekly* — and the payload says `MONTHLY`.**

    ⚠️ That one wrong cell is the whole of the comics chart's absence: `bestsellers_date: 2026-10-03` against a weekly
    span of `2026-10-05 … 2026-10-14`, so the guard called the list stale on the very week it describes, and ticket 18
    made the chart absent rather than smaller. ⚠️ **The cadence is declared, and the declaration is refused if it is not
    one we know** — a misspelt `"monthly"` would otherwise keep the weekly rule silently, which is the failure this field
    exists to remove.
    """

    def test_only_the_monthly_lists_say_so(self):
        """⚠️ **Pinned rather than counted**, so a second monthly list has to be a decision rather than an accident —
        the same shape `test_a_language_is_either_declared_or_deliberately_unknown` keeps for the labels.
        """
        monthly = {
            entry.slug for chart in charts.ALL for entry in chart.lists if entry.cadence == "monthly"
        }

        self.assertEqual(monthly, {"nyt/graphic-books-and-manga"})

    def test_every_other_list_is_weekly_by_default(self):
        """⚠️ **The default is the rule the product has always used**, so nothing else changed cadence by accident."""
        for chart in charts.ALL:
            for entry in chart.lists:
                if entry.slug != "nyt/graphic-books-and-manga":
                    with self.subTest(list=entry.slug):
                        self.assertEqual(entry.cadence, "weekly")

    def test_a_cadence_nobody_recognises_cannot_be_declared(self):
        """⚠️ A refusal rather than a warning, for ticket 29's reason: the mistake this prevents is a list that quietly
        keeps the *weekly* rule, and a warning is read once while a constructor is read on every run.
        """
        with self.assertRaises(ValueError) as raised:
            charts.Listing(
                slug="nyt/graphic-books-and-manga",
                country="us",
                language="en",
                cadence="fortnightly",
            )

        self.assertIn("fortnightly", str(raised.exception))


class TheLabelsEveryListDeclares(unittest.TestCase):
    """⚠️ Ticket 20 — **country and language are properties of the *list*, not of the chart.**

    ⚠️ **And declaring them here is what stops them drifting.** `comics` reads a US list and an Indian one, so a
    chart-level country would be wrong for it; a chart reading several Amazon.in language lists would have several
    languages. ⚠️ Declared per list, no chart is a special case — and a new list **cannot be added without saying where
    it is and what language it is**, which is the same discipline that makes `vendors` the spine (ticket 18).
    """

    def test_every_declared_list_says_where_it_is(self):
        """⚠️ **The country, always** — a row with no country is a row nobody can label (ticket 20).
        """
        for chart in charts.ALL:
            for entry in chart.lists:
                with self.subTest(list=entry.slug):
                    self.assertTrue(entry.country, f"{entry.slug} declares no country")

    def test_a_language_is_either_declared_or_deliberately_unknown(self):
        """⚠️ **Empty means *unknown*, and it is a state rather than an omission** (ticket 29).

        The all-language list carries Hindi, Tamil, Telugu and Urdu rows side by side, so a single language would be
        confidently wrong on most of them — ⚠️ and by ticket 20's rule a *constant* label **renders**, which would put the
        wrong language on a hundred rows.

        ⚠️ **There are two such lists now, and they are the same shape of thing** (ticket 30): BoiChitro is a Bengali
        bookshop whose *bestseller* list carries English rows too — its own top ten holds *Strange Weather in Tokyo*
        beside *দেশান্তরে বাজ* — so a declared `bn` would be wrong on some rows for exactly the reason a declared `hi`
        would be wrong on most of the all-language list. ⚠️ **The set is pinned rather than counted**, so a third list
        cannot quietly join it without someone deciding that its language is genuinely unknown.
        """
        unlabelled = {
            entry.slug for chart in charts.ALL for entry in chart.lists if not entry.language
        }

        self.assertEqual(
            unlabelled, {"amazon-in/indian-languages", "boichitro/bestsellers"}
        )

    def test_the_comics_chart_varies_in_country(self):
        """⚠️ Ticket 20's amended boundary, and what gives the country label something to say.

        *"A label that says the same thing on all 100 rows is not information."* ⚠️ **The chart that demonstrates it moved
        in ticket 29**: the Bengali chart used to span India and Bangladesh, but Anandabazar could not be declared, so it
        is `bd` throughout — and `comics` reads a US list and an Indian one.

        ⚠️ ⚠️ **And it is eight countries now, not two** (ticket 34). The operator asked for *"different country europe
        amerika uk india"*, so the chart reads one storefront per country and the label has more to say than any other
        chart's. ⚠️ The set is pinned rather than counted, so a store cannot be added without someone deciding which
        country it speaks for.
        """
        countries = {entry.country for entry in charts.get("comics").lists}

        self.assertEqual(countries, {"us", "gb", "ca", "de", "fr", "it", "es", "in"})

    def test_the_bengali_chart_spans_india_and_bangladesh_again(self):
        """⚠️ ⚠️ **This test replaces one that asserted the opposite — twice over** (ticket 30).

        It was *"the one chart whose country varies"* (`in`, `bd`) while it declared Anandabazar alongside Rokomari;
        ticket 29 removed the Indian half, so it became `test_the_bengali_chart_no_longer_varies_in_country` and asserted
        `{"bd"}` with a **Bangladeshi** market. ⚠️ **Both readings were right about the sources they had, and the sources
        have changed again**: ticket 30's search found an Indian vendor that *can* be declared — BoiChitro, whose
        hundred-deep popularity ranking is a JSON endpoint — so the chart spans the two countries ticket 21 built it for.

        ⚠️ **And the market widens back with it**, which is ticket 19's rule read the other way: *a chart's scope is what
        its lists can support*, so `india+bangladesh` is right for exactly the reason `bangladesh` was.
        """
        chart = charts.get("bengali")

        self.assertEqual({entry.country for entry in chart.lists}, {"in", "bd"})
        self.assertEqual(chart.market, "india+bangladesh")
        # ⚠️ ⚠️ **Three vendors now, and the Indian half is a *pair*** (ticket 32): Rokomari is the Bangladeshi side,
        # and BoiChitro and Bangabani are both Indian — which is the margin ticket 29 left this chart without.
        self.assertEqual(chart.vendors, ("rokomari", "boichitro", "bangabani"))

    def test_the_english_chart_now_spans_the_english_speaking_world(self):
        """⚠️ ⚠️ **This test replaces one that asserted the opposite** (2026-10-15).

        It used to be `test_the_english_chart_varies_in_neither`, and it asserted `{entry.country} == {"us"}` — *"the
        English chart is the one chart where neither of the brief's labels appears"* (ticket 19). ⚠️ **Ticket 19 was right
        about the sources it had; the operator has since changed them.** The chart now reads the four Amazon Books
        bestsellers beside NYT and Indie, so its rows carry `us`, `gb`, `ca` and `au`.

        ⚠️ **And that turns ticket 20's country label on for this chart**, which is the point rather than a side effect:
        *"a label that says the same thing on all 100 rows is not information"* — with four countries on it, it is. ⚠️ The
        language still does **not** vary (every list is `en`), so that label stays off.
        """
        chart = charts.get("english")

        self.assertEqual(
            {entry.country for entry in chart.lists}, {"us", "gb", "ca", "au"}
        )
        self.assertEqual({entry.language for entry in chart.lists}, {"en"})
        # ⚠️ **The market follows the sources** — see the chart's own note in `charts.py`.
        self.assertEqual(chart.market, "worldwide")


class TheLiveRankings(unittest.TestCase):
    """⚠️ ⚠️ **The vendors whose list is a live ranking rather than a compiled weekly list** (2026-10-15).

    ⚠️ **It is declared here because it is a fact about the source**, and `freshness.guard` reads it to know not to ask
    for a date the source never states. ⚠️ Without it every Amazon row was discarded as undated and every chart declaring
    one went **absent** — which is why `comics` and `all-language` never built, and why the English chart could not have
    gained an international list at all.
    """

    def test_every_amazon_marketplace_is_live(self):
        for vendor in (
            charts.AMAZON_US,
            charts.AMAZON_UK,
            charts.AMAZON_CA,
            charts.AMAZON_AU,
            charts.AMAZON_IN,
        ):
            with self.subTest(vendor=vendor):
                self.assertIn(vendor, charts.LIVE)

    def test_a_compiled_list_is_not_live(self):
        """⚠️ **The exemption is narrow, and this is the half that keeps it so.**

        NYT and Indie are *dated* lists — the page describing week 41 keeps saying *week 41* next week — so the guard must
        keep asking them, which is the whole point of the guard.

        ⚠️ ⚠️ **`rokomari` was named here as a third, and that was the reading ticket 30 corrects.** This test said *"it
        is a compiled list whose date is simply missing"*, which was the right description of the **guard's complaint**
        and the wrong description of the **source**: a retailer's bestseller category is regenerated per order, so there
        is no dated artefact for a date to be missing *from*. ⚠️ That is the whole difference between the two sets, and
        it is a fact about the vendor rather than about what we would prefer to be true.
        """
        for vendor in ("nyt", "indie"):
            with self.subTest(vendor=vendor):
                self.assertNotIn(vendor, charts.LIVE)

    def test_the_retailers_live_rankings_are_live_too(self):
        """⚠️ **Ticket 30's correction, asserted where the old claim used to be.**

        Rokomari's Best Seller category and BoiChitro's Store API are both **regenerated** rather than compiled, so both
        are exempt from a date neither states — and ⚠️ that is what brings the Bengali chart back, because a vendor the
        guard refuses every week is a vendor the chart can never use.
        """
        for vendor in (charts.ROKOMARI, charts.BOICHITRO, charts.BANGABANI):
            with self.subTest(vendor=vendor):
                self.assertIn(vendor, charts.LIVE)

    def test_every_live_vendor_is_also_a_located_one(self):
        """⚠️ ⚠️ **This test used to assert `LIVE ⊆ SCRAPED` and offer the nesting as the *definition* of live.**

        Its reason was *"a live list is always a scraped one — a JSON API that states no date is a source to fix, not one
        to exempt"*. ⚠️ **BoiChitro is exactly that JSON API, and it is exempt**, so the reason was not a rule: what makes
        a list live is that **there is no stale copy of it to date**, and whether the bytes arrive as JSON or as HTML says
        nothing about that.

        ⚠️ The nesting still holds, and for an honest reason rather than a rhetorical one: a live list is always a
        **located** one (`SCRAPED`), because a list whose address cannot be checked is not one anybody can fetch. So it
        is asserted — but it is no longer what *live* means.
        """
        self.assertTrue(charts.LIVE <= charts.SCRAPED)


if __name__ == "__main__":
    unittest.main()
