"""Ticket 26 — the genre vocabulary.

⚠️ **Genre is not a field a source hands over; it is a *classification*, and every source has its own taxonomy.** So
this is a normalisation, and the rule that keeps it honest is that an unmapped category becomes `other` rather than
the nearest plausible bucket — the same discipline as `identity: unresolved` (ticket 05).
"""
import unittest

from books_brief import genre


class TheVocabulary(unittest.TestCase):
    def test_a_category_outside_the_vocabulary_is_labelled_other_rather_than_guessed(self):
        """⚠️ Ticket 26: **`other` is a real value, not a failure.**

        Forcing an unmapped category into the nearest slug would make the label *wrong* rather than merely
        *unhelpful* — and the label is what a viewer uses to decide whether the book is for them.
        """
        self.assertEqual(genre.slug_for("Antiques & Collectibles"), "other")

    def test_each_vendors_own_taxonomy_maps_onto_the_one_vocabulary(self):
        """⚠️ Three sources, three taxonomies, one label.

        A vendor's browse node, a newspaper list's name and a BISAC-ish category all have to land on the same slug,
        or the label would mean something different on every chart.
        """
        self.assertEqual(genre.slug_for("Business & Economics"), "business")
        self.assertEqual(genre.slug_for("hardcover-fiction"), "fiction")


if __name__ == "__main__":
    unittest.main()
