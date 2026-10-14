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
        wrong language on a hundred rows. ⚠️ So exactly one list may declare none, and it must be that one.
        """
        unlabelled = {
            entry.slug for chart in charts.ALL for entry in chart.lists if not entry.language
        }

        self.assertEqual(unlabelled, {"amazon-in/indian-languages"})

    def test_the_comics_chart_is_the_one_whose_country_varies(self):
        """⚠️ Ticket 20's amended boundary, and what gives the country label something to say.

        *"A label that says the same thing on all 100 rows is not information."* ⚠️ **The chart that demonstrates it moved
        in ticket 29**: the Bengali chart used to span India and Bangladesh, but Anandabazar could not be declared, so it
        is `bd` throughout — and `comics` reads a US list and an Indian one.
        """
        countries = {entry.country for entry in charts.get("comics").lists}

        self.assertEqual(countries, {"us", "in"})

    def test_the_bengali_chart_no_longer_varies_in_country(self):
        """⚠️ **The correction, stated where the old claim used to be.**

        This was *"the one chart whose country varies"* (`in`, `bd`) while it declared Anandabazar alongside Rokomari.
        ⚠️ Ticket 29 removed the Indian half — no list was ever located and no client was ever written for it — so the
        chart is `bd` throughout, and its **market narrowed to Bangladesh** with it (the same rule ticket 19 applied when
        it refused to call a US-list chart *global*).
        """
        chart = charts.get("bengali")

        self.assertEqual({entry.country for entry in chart.lists}, {"bd"})
        self.assertEqual(chart.market, "bangladesh")
        self.assertEqual(chart.vendors, ("rokomari",))

    def test_the_english_chart_varies_in_neither(self):
        """⚠️ **And that is the rule working, not a gap** (ticket 19).

        NYT and Indie Bestsellers are both US lists, so *"the English chart is the one chart where neither of the brief's
        labels appears."* ⚠️ The chart still *states* its market — in the footer, once — which is the difference between a
        label and a statement.
        """
        chart = charts.get("english")

        self.assertEqual({entry.country for entry in chart.lists}, {"us"})
        self.assertEqual({entry.language for entry in chart.lists}, {"en"})


if __name__ == "__main__":
    unittest.main()
