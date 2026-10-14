"""Ticket 04 — the price layer.

⚠️ **The governing rule: never label a price "best" unless it was actually compared.** So the fact that matters is not
just the amount but **which retailers were consulted** — and the renderer decides the words from that, the same split
as every other label (ADR 0003). A slide reading *"Best price ₹399"* off a single Amazon listing would be claiming a
comparison nobody made.
"""
import unittest

from books_brief import prices


def offer(
    retailer: str, amount: float | None, *, edition: str = "paperback"
) -> prices.Offer:
    return prices.Offer(retailer=retailer, amount=amount, edition=edition)


class TheBestPrice(unittest.TestCase):
    def test_the_lowest_offer_wins_and_the_retailer_is_named(self):
        """The primary case — Amazon.in's lowest offer, bettered by Flipkart (ticket 04's two-retailer set)."""
        chosen = prices.best(
            [offer("amazon-in", 399.0), offer("flipkart", 349.0)]
        )

        self.assertEqual(chosen.amount, 349.0)
        self.assertEqual(chosen.retailer, "flipkart")
        # ⚠️ **Both are recorded, not just the winner.** The *count* is what lets the label say "best" honestly, so
        # asserting only the winner would leave the comparison unverified.
        self.assertEqual(chosen.retailers, ("amazon-in", "flipkart"))

    def test_a_single_retailer_is_not_a_comparison(self):
        """⚠️ Ticket 04's governing rule, carried as data.

        `retailers` is what the renderer needs in order **not** to say *"best price"*: with one retailer there was
        nothing to compare against, so the slide names the shop and stops there.
        """
        chosen = prices.best([offer("amazon-in", 399.0)])

        self.assertEqual(chosen.retailers, ("amazon-in",))

    def test_no_offer_is_none_and_never_a_zero(self):
        """⚠️ The host repo's own rule: *"a missing value and a real zero are different facts."*

        A `0.0` here would render as `₹0` and state something untrue, so an absent price is `None` and the slide draws
        a dash (ticket 07). ⚠️ And an offer that *arrives* with no amount — which Amazon.in does, on some listings —
        is the same case, not a different one.
        """
        self.assertIsNone(prices.best([]).amount)
        self.assertIsNone(prices.best([offer("amazon-in", None)]).amount)


if __name__ == "__main__":
    unittest.main()
