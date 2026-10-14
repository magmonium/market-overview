"""Ticket 15 — the upload text.

⚠️ **The description cannot hold the full list with all the fields.** `1. Title — Author — Publisher — ₹399` is roughly
**6,800 characters** for a hundred rows against YouTube's **5,000** limit — arithmetic, not opinion. So the rows mirror
the video's own dwell weighting (ticket 06): full rows for the top ten, compact for the rest.
"""
import unittest

from books_brief import charts, metadata


def rows(count: int) -> list[metadata.Row]:
    """`count` rows, each with every field filled, so a budget test is about the budget and not about sparse data."""
    return [
        metadata.Row(
            rank=number + 1,
            title=f"Book Number {number + 1}",
            author=f"Author {number + 1}",
            publisher="Ananda Publishers",
            price="₹399",
        )
        for number in range(count)
    ]


class TheTitle(unittest.TestCase):
    def test_the_title_names_the_chart_the_iso_week_and_the_date(self):
        """⚠️ Ticket 10 settled that a week is its **ISO week**, so a run in October reads *Week 41* — not a
        launch-relative counter, which would disagree with the `store/2026-W41/` folder it came from.
        """
        built = metadata.build(
            "2026-W41", charts.get("bengali"), rows(3), basis_weeks=7, published_on="2026-10-14"
        )

        self.assertEqual(built.title, "Top 100 Bengali Books | Week 41 | 14 Oct, 2026")
        # ⚠️ The literal 100, not `metadata.TITLE_LIMIT` — a limit the test reads from the code it is testing can
        # never disagree with it.
        self.assertLessEqual(len(built.title), 100)


class TheDescription(unittest.TestCase):
    def test_a_hundred_rows_fit_and_the_detail_follows_the_dwell(self):
        """⚠️ Ticket 15's two tiers, and the limit is **checked rather than hoped for**.

        The top ten carry the publisher and the price — the ranks the video actually dwells on — and the tail carries
        title and author only. Both halves are asserted, because a description that quietly overflowed would be
        truncated by YouTube at the **tail of the list**, which is the part nobody would check.
        """
        built = metadata.build(
            "2026-W41", charts.get("english"), rows(100), basis_weeks=7, published_on="2026-10-14"
        )

        top, tail = built.description.split("\n11. ")

        # ⚠️ Literals for both limits, for the reason the title test gives: a limit read from the code under test
        # cannot disagree with it.
        self.assertLessEqual(len(built.description), 5000)
        self.assertIn("Ananda Publishers", top, "the top ten are full rows")
        self.assertNotIn("Ananda Publishers", tail, "the tail is compact")
        self.assertIn("\n100. Book Number 100", built.description)

    def test_the_description_states_the_basis_and_the_window_it_actually_has(self):
        """⚠️ Tickets 15 and 23 — `Top 100 Bengali Books` no longer says *what it ranks*, and the window is the one the
        chart **has**, not the six months it is aiming at.
        """
        built = metadata.build(
            "2026-W41", charts.get("bengali"), rows(3), basis_weeks=7, published_on="2026-10-14"
        )

        self.assertIn("six months", built.description)
        self.assertIn("7 weeks", built.description)


class TheTags(unittest.TestCase):
    def test_the_tag_budget_is_characters_and_exactly_three_hashtags_are_emitted(self):
        """⚠️ Ticket 15, both traps in one test.

        The budget is in **characters, not tags** — *"a handful of long sector names blows it without anything looking
        wrong"* — so tags are appended **while they fit**, never "the first N". ⚠️ And the hashtag count is **exactly
        three**: fifteen is a cliff rather than a budget, past which YouTube ignores *all* of them.
        """
        built = metadata.build(
            "2026-W41", charts.get("bengali"), rows(100), basis_weeks=7, published_on="2026-10-14"
        )

        self.assertLessEqual(len(", ".join(built.tags)), 500)
        self.assertEqual(len(built.hashtags), 3)


class WhenTheListWillNotFit(unittest.TestCase):
    def test_a_list_that_will_not_fit_is_refused_rather_than_truncated(self):
        """⚠️ Ticket 15 — *"the full list"* is the product's promise, and a silently truncated list breaks it.

        ⚠️ And YouTube truncates the **tail** — the part of the list nobody would check. So the run refuses instead,
        which is the reel's rule (`SeoError`: *"the run stops before it renders an hour of frames"*) rather than the
        brief's warn-and-ship. A hundred rows of long titles is exactly the week this is for.
        """
        oversized = [
            metadata.Row(
                rank=number + 1,
                title="X" * 200,
                author="Y" * 200,
                publisher="Z" * 200,
                price="₹399",
            )
            for number in range(100)
        ]

        with self.assertRaises(metadata.MetadataError):
            metadata.build(
                "2026-W41",
                charts.get("bengali"),
                oversized,
                basis_weeks=7,
                published_on="2026-10-14",
            )


if __name__ == "__main__":
    unittest.main()
