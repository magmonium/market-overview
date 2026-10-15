"""Ticket 03 — the chart logic, and ticket 11's hard constraint.

⚠️ **A cap is a *bound*, not a preference.** The incumbency multiplier makes churn *unlikely*; only an admission rule
makes it *impossible*. So the two are not alternatives — one is the preference and one is the guarantee, and this file
tests the guarantee.
"""
import unittest

from books_brief import rank


def newcomers(count: int) -> list[rank.Candidate]:
    """`count` candidates, each scoring lower than the last, so their order is never in doubt."""
    return [
        rank.Candidate(key=f"978000000{n:04d}", isbn=f"978000000{n:04d}", score=100.0 - n) for n in range(count)
    ]


def listing(list_slug: str, *, rank_at: int, size: int) -> rank.Listing:
    """One list's view of a title — where it ranked, and how deep the list went."""
    return rank.Listing(list=list_slug, rank=rank_at, size=size)


class TheAdmissionRule(unittest.TestCase):
    def test_at_most_ten_newcomers_can_enter_a_chart(self):
        """⚠️ Ticket 11, in the brief's own words: *"new entry should not be more then 10"*.

        Twenty newcomers, an empty chart and room for a hundred — and exactly **ten** enter. ⚠️ A `previous` chart is
        supplied because **week one is a different behaviour** (ticket 03), and this is not week one.
        """
        board = rank.chart(newcomers(20), previous=("9789999999991",))

        self.assertEqual(
            [row.isbn for row in board.ranked],
            [f"978000000{n:04d}" for n in range(10)],
        )
        self.assertEqual(
            list(board.watchlist),
            [f"978000000{n:04d}" for n in range(10, 20)],
        )

    def test_week_one_bypasses_the_cap_but_an_empty_previous_chart_does_not(self):
        """⚠️ Ticket 03's own catch, and the distinction that makes it safe.

        With **no previous week** every title is a newcomer, so the admission rule would admit ten and ship a chart
        labelled "Top 100" holding **ten books**. So week one bypasses it.

        ⚠️ But `previous=()` is *not* the same thing: it says a previous chart existed and was **empty**, and the cap
        must still apply. Collapsing the two would switch the cap off for any week that churned completely — which is
        precisely the week it matters most.
        """
        first = rank.chart(newcomers(20), previous=None)
        churned = rank.chart(newcomers(20), previous=())

        self.assertEqual(len(first.ranked), 20)
        self.assertTrue(all(row.is_new for row in first.ranked))

        self.assertEqual(len(churned.ranked), 10)
        self.assertEqual(len(churned.watchlist), 10)


class TheScore(unittest.TestCase):
    def test_a_title_on_two_lists_scores_exactly_twice_a_title_on_one(self):
        """⚠️ Ticket 03, step 3 — **the sum *is* the corroboration bonus.**

        No separate "trust multiplier" is needed: a title carried by three lists accumulates three terms. So a
        single-source title can never out-rank a three-source title at the same position — which is what *"genuine and
        authentic"* means as arithmetic rather than as a promise.

        Both lists are a hundred deep, so depth-weighting contributes nothing here and the arithmetic is the plain
        position: `(100 + 1 − 1) / 100 = 1.0` each.
        """
        one = [listing("nyt/hardcover-fiction", rank_at=1, size=100)]
        two = one + [listing("pw/fiction", rank_at=1, size=100)]
        weights = {"nyt": 1.0, "pw": 1.0}

        self.assertEqual(rank.score(one, weights=weights), 1.0)
        self.assertEqual(rank.score(two, weights=weights), 2.0)

    def test_a_number_one_in_a_shallow_list_is_worth_less_than_one_in_a_deep_list(self):
        """⚠️ Ticket 03, step 2 — and the step the all-language chart could not do without.

        Amazon.in's per-language categories differ wildly in depth (ticket 02), so without this a #1 in a twenty-deep
        category would out-rank a #1 in a hundred-deep one. That is precisely how *"a low-selling product can top a
        narrow subcategory"* — the HWR warning ticket 17 quotes as the reason this product has a gate at all.

        A twenty-deep list is a fifth of the reference depth, so its #1 scores `1.0 × 20/100 = 0.2`.
        """
        shallow = [listing("amazon-in/gujarati", rank_at=1, size=20)]
        deep = [listing("amazon-in/hindi", rank_at=1, size=100)]

        self.assertEqual(rank.score(shallow, weights={"amazon-in": 1.0}), 0.2)
        self.assertEqual(rank.score(deep, weights={"amazon-in": 1.0}), 1.0)


class TheOrder(unittest.TestCase):
    def test_an_incumbent_outranks_a_newcomer_at_the_same_raw_score(self):
        """⚠️ Ticket 03, step 4 — the chart is **stable**, not merely correct.

        Two titles with identical source scores: the one already on the chart keeps its place, because
        `final_score = score × (1 + 0.15 × min(weeks_on_chart, 8))`. ⚠️ This is the *preference*; ticket 11's
        admission rule is the *guarantee*. Without the preference the cap would be doing all the work on its own, and
        the chart would churn its full ten every week.
        """
        # ⚠️ **The ISBNs are chosen so the tie-break cannot produce this order.** The newcomer sorts *first* by ISBN,
        # so if the multiplier were removed the two would tie and the newcomer would win. An earlier version had them
        # the other way round and **passed for the wrong reason** — the ISBN tie-break was doing the work and the
        # multiplier was never exercised, which the mutation check caught and a green run never would have.
        incumbent = rank.Candidate(key="9780000000002", isbn="9780000000002", score=10.0, weeks_on_chart=8)
        newcomer = rank.Candidate(key="9780000000001", isbn="9780000000001", score=10.0)

        board = rank.chart([newcomer, incumbent], previous=("9780000000002",))

        self.assertEqual(
            [row.isbn for row in board.ranked], ["9780000000002", "9780000000001"]
        )

    def test_two_titles_that_score_identically_are_ordered_by_their_key(self):
        """⚠️ Ticket 03, step 6 — the order must be **total**, or the same week could rank two ways.

        Both titles are newcomers of the same age with the same score, so nothing but the key separates them. A tie
        that fell back on the order the sources happened to answer in would make the chart unreplayable — and a
        non-replayable chart is the one thing ADR 0003 will not give up.

        ⚠️ **The tie-break is the *work key*, not the ISBN** (ticket 32): the ISBN is a field two rows carrying the same
        work can disagree about, so it cannot be the thing that orders them. ⚠️ The test is unchanged in substance and
        renamed, which is the honest record — the old name asserted a rule the code no longer follows.

        ⚠️ They are passed in **reverse** order deliberately: the assertion is about the tie-break, not about
        `sorted` being stable.
        """
        second = rank.Candidate(key="9780000000002", isbn="9780000000002", score=5.0)
        first = rank.Candidate(key="9780000000001", isbn="9780000000001", score=5.0)

        board = rank.chart([second, first], previous=None)

        self.assertEqual(
            [row.isbn for row in board.ranked], ["9780000000001", "9780000000002"]
        )


class TheReviewTerm(unittest.TestCase):
    """⚠️ Ticket 23 — *"a raw mean is a trap."*"""

    def test_a_thin_rating_is_shrunk_toward_the_global_mean(self):
        """⚠️ **The sentence the rule exists for:** *"5.0 from 3 reviews must not outrank 4.6 from 50,000."*

        A raw mean gives the three-review book a perfect score and the chart rewards obscurity — which is exactly
        backwards, because a thin rating is not evidence of quality, it is evidence of **nobody having looked**.
        """
        thin = rank.review_term(5.0, 3, mean=4.0)
        solid = rank.review_term(4.6, 50_000, mean=4.0)

        self.assertLess(thin, solid)

    def test_a_title_with_no_rating_contributes_nothing_at_all(self):
        """⚠️ **`0.0`, not a middling default.** A book with no rating has not been *judged average* — it has not been
        judged, and inventing a score for it would let an unrated title outrank a rated one.
        """
        self.assertEqual(rank.review_term(None, 500, mean=4.0), 0.0)
        self.assertEqual(rank.review_term(4.8, None, mean=4.0), 0.0)
        self.assertEqual(rank.review_term(4.8, 0, mean=4.0), 0.0)

    def test_a_rating_at_the_mean_is_the_mean_however_many_reviews_it_has(self):
        """⚠️ **The property that makes it a *credibility* weight rather than a fudge.**

        A book rated exactly at the global mean must land on that mean whether it has three reviews or fifty thousand —
        so the shrinkage moves a thin rating's *distance from the mean* and never the mean itself. An implementation
        that got this wrong would quietly re-rank every book in the chart.
        """
        self.assertAlmostEqual(rank.review_term(4.0, 3, mean=4.0), 4.0)
        self.assertAlmostEqual(rank.review_term(4.0, 50_000, mean=4.0), 4.0)

    def test_more_reviews_move_the_term_toward_the_rating(self):
        """The other half of the same property: with enough reviews, a rating's own value wins."""
        few = rank.review_term(5.0, 10, mean=4.0)
        many = rank.review_term(5.0, 10_000, mean=4.0)

        self.assertLess(few, many)
        self.assertLess(many, 5.0)


class TheScore(unittest.TestCase):
    def test_the_review_term_is_weighed_against_the_sales_term(self):
        """⚠️ **Ticket 23's two terms, and the weight is a *recorded* value** — the map's habit, so tuning the chart is a
        data change and not a rewrite. ⚠️ It is a judgement rather than a derivation, and saying so is the honest thing:
        the ticket fixes *that* reviews count, not how much.
        """
        plain = rank.Candidate(key="9788172151234", isbn="9788172151234", score=1.0)
        rated = rank.Candidate(key="9788172151234", isbn="9788172151234", score=1.0, rating=5.0, ratings_count=50_000)

        self.assertEqual(rank.final_score(plain), 1.0)
        self.assertGreater(rank.final_score(rated), 1.0)
        # ⚠️ And a review **cannot outweigh a sales position**: five stars from fifty thousand readers is worth well
        # under one position, or the chart would be a popularity contest with sales as a footnote.
        self.assertLess(rank.final_score(rated), 2.0)

    def test_an_unrated_title_is_not_penalised_for_it(self):
        """⚠️ The other side of `review_term`'s zero: a book the enrichment source has no rating for keeps its sales
        score exactly. A penalty here would quietly exile every title Google Books does not carry a rating for — which
        is most Bengali books, so the Bengali chart would be ranked on a signal it barely has.
        """
        candidate = rank.Candidate(key="9788172151234", isbn="9788172151234", score=1.4)

        self.assertEqual(rank.final_score(candidate), 1.4)


if __name__ == "__main__":
    unittest.main()

