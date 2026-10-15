"""Ticket 32 — the identity of a title: **the work, not the product**.

⚠️ **The rule these tests pin is the one that decides whether a chart is a chart of *books* or of *listings*.** Keyed by
ISBN, the English chart ranked **92 distinct titles in 100 rows** — eight books appearing twice, each pair being two
editions of one work. ⚠️ And the reason it is `title + author` rather than `title` is that only one of the two possible
errors can be repaired: an under-merge leaves a duplicate, an over-merge invents a book.
"""
import unittest

from books_brief import identity


class WhatTwoVendorsCanAgreeOn(unittest.TestCase):
    """⚠️ `normalise` — the reductions, and the two it deliberately does not make."""

    def test_case_punctuation_and_spacing_go(self):
        """⚠️ **The measured disagreements, not a preference**: BoiChitro writes `Tenida Samagra` where Dey's writes
        `TENIDA SAMAGRA`, and a shop's blurb writes `Putul Nacher Itikatha` with a colon.
        """
        self.assertEqual(identity.normalise("TENIDA SAMAGRA"), identity.normalise("Tenida Samagra"))
        self.assertEqual(identity.normalise("Putul Nacher Itikatha"), identity.normalise("Putul Nacher Itikatha:"))
        self.assertEqual(identity.normalise("  Galpa   101 "), identity.normalise("Galpa 101"))

    def test_bengali_survives_whole(self):
        """⚠️ ⚠️ **The trap this avoids.** A normaliser that kept only `a-z0-9` would turn every Bengali title into the
        empty string — and every Bengali row on a chart into **one row**, which is a far worse failure than a duplicate.
        """
        self.assertEqual(identity.normalise("দেশান্তরে বাজ"), "দেশান্তরেবাজ")
        self.assertNotEqual(identity.normalise("দেশান্তরে বাজ"), "")

    def test_two_encodings_of_one_word_agree(self):
        """⚠️ `NFKD` — a composed character and its decomposed form are the same word, and a store's CMS may hand over
        either. ⚠️ This is what makes the key stable across sources rather than merely across runs.
        """
        self.assertEqual(identity.normalise("Café"), identity.normalise("Cafe\u0301"))

    def test_two_different_books_stay_different(self):
        """⚠️ ⚠️ **Not a stemmer and not a similarity.** `Galpa 101` and `Galpa 102` are different books, and so are the
        two *Court of…* titles below — which any fuzzy distance worth the name would merge.
        """
        self.assertNotEqual(identity.normalise("Galpa 101"), identity.normalise("Galpa 102"))
        self.assertNotEqual(
            identity.normalise("A Court of Splintered Harmony"),
            identity.normalise("A Court of Forgotten Melody"),
        )


class TheSpellingTable(unittest.TestCase):
    """⚠️ The one place a spelling is decided, and it is **data** — the same shape as `genre.py`'s vocabulary table."""

    def test_the_two_measured_pairs_resolve_to_one_key(self):
        """⚠️ ⚠️ **Both entries were justified by a *work*, not by a resemblance between names.**

        `Byomkesh Samagra` is one book that Dey's attributes to *Saradindu Bandopadhyay* and BoiChitro to *Sharadindu
        Bandyopadhyay*; `Galpa 101` is one book credited to *Satyajit Roy* and *Satyajit Ray*. ⚠️ Without the table the
        work key merges **3 of the 5** titles the two shops share; with it, all five.
        """
        self.assertEqual(
            identity.work("Byomkesh Samagra", "Saradindu Bandopadhyay"),
            identity.work("Byomkesh Samagra", "Sharadindu Bandyopadhyay"),
        )
        self.assertEqual(
            identity.work("Galpa 101", "Satyajit Roy"),
            identity.work("Galpa 101", "Satyajit Ray"),
        )

    def test_an_author_the_table_does_not_know_passes_through(self):
        """⚠️ **A table that guessed would be a rule in disguise** — an unknown author is their own key, which is the
        conservative direction and the one a third spelling will land on until it is measured and added.
        """
        self.assertEqual(identity.spelling("Someone Else"), "someoneelse")


class TheWorkKey(unittest.TestCase):
    """⚠️ `work` — what the chart is actually keyed by."""

    def test_the_same_work_from_two_shops_is_one_key(self):
        """⚠️ **The defect this closes, as a test**: two editions of one book are two ISBNs and one work, so the key has
        to be the work — otherwise the chart ranks the book twice and says nothing about it.
        """
        self.assertEqual(
            identity.work("Protocols: An Operating Manual for the Human", "Andrew Huberman"),
            identity.work("PROTOCOLS: An Operating Manual for the Human", "Andrew Huberman"),
        )

    def test_the_author_is_part_of_the_key(self):
        """⚠️ Two books can share a title and differ by author, so the author is not decoration."""
        self.assertNotEqual(identity.work("Compass", "A"), identity.work("Compass", "B"))

    def test_a_row_with_no_author_cannot_merge_with_one_that_has_it(self):
        """⚠️ ⚠️ **The asymmetry, deliberately.** An empty author produces `title|`, which matches no authored key — so
        a vendor that states no author keeps its own row. ⚠️ That is the conservative direction: a duplicate is visible
        and repairable, and a merged pair of different books is neither.
        """
        self.assertNotEqual(identity.work("Compass", ""), identity.work("Compass", "Smaranjit Chakraborty"))
        self.assertEqual(identity.work("Compass", ""), "compass|")

    def test_a_title_cannot_forge_a_key_boundary(self):
        """⚠️ The separator is `|`, and `normalise` strips it from every input — so no title can pretend to end early
        and swallow another row's author.
        """
        self.assertEqual(identity.work("A|B", "C"), identity.work("AB", "C"))
        self.assertNotEqual(identity.work("A|B", "C"), identity.work("A", "B|C"))

    def test_the_same_inputs_always_give_the_same_key(self):
        """⚠️ Ticket 03's determinism, one level down: a key that varied between runs would make the Δ and the window
        disagree with the chart they belong to.
        """
        self.assertEqual(identity.work("Galpa 101", "Satyajit Ray"), identity.work("Galpa 101", "Satyajit Ray"))


class ReadingAStoredRow(unittest.TestCase):
    """⚠️ `from_row` — the migration, and the only place a week recorded before ticket 32 is read."""

    def test_the_key_wins_when_the_row_has_one(self):
        self.assertEqual(identity.from_row({"key": "a|b", "isbn": "9788172151234"}), "a|b")

    def test_a_row_written_before_the_key_existed_falls_back_to_its_isbn(self):
        """⚠️ ⚠️ **Not a convenience — the reason the change is not a break.** The store holds weeks keyed by ISBN, and a
        Δ that could not read them would find no incumbent at all and report **a whole chart as NEW** on the first week
        after the change. ⚠️ `isbn` *was* the key then, so this reads the same fact under its old name.
        """
        self.assertEqual(identity.from_row({"isbn": "9788172151234"}), "9788172151234")

    def test_a_row_with_neither_is_empty_rather_than_a_crash(self):
        """⚠️ An empty key is **skipped** by the window and the Δ rather than raising — a snapshot with a malformed row
        costs that row, not the week.
        """
        self.assertEqual(identity.from_row({}), "")
        self.assertEqual(identity.from_row({"key": "", "isbn": ""}), "")

