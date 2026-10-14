"""Ticket 06 — the dwell, and ticket 07's entrance ceiling.

⚠️ **A hundred books do not fit three minutes at a full reading time each**, so the dwell follows the **interest
curve**: the top of the chart is read and the tail is glanced. That is a product decision, not a compression
accident — and the honest consequence is that the **description** carries the detail the video cannot dwell on.
"""
import unittest

from books_brief import timeline


class TheDwell(unittest.TestCase):
    def test_the_whole_run_fits_the_three_minute_cap(self):
        """⚠️ Ticket 06's table, and the arithmetic that produced it.

        `6 + 35 + 40 + 42 + 40 + 6 = 169` seconds, against the host repo's own 180-second cap — and the ~11 seconds of
        headroom are deliberate, so a repeated title (the superset, ticket 14) does not push the run over.
        """
        self.assertEqual(timeline.total_seconds(), 169)
        self.assertLess(timeline.total_seconds(), timeline.CAP_SECONDS)

    def test_the_top_of_the_chart_is_read_and_the_tail_is_glanced(self):
        """⚠️ Ticket 06's honest consequence, as numbers.

        Nobody reads a publisher and a pub date in 1.0 s — so below about rank 50 a slide is a **glance**, and the full
        detail lives in the description instead. That is why ticket 15's two-tier rows exist.
        """
        self.assertEqual(timeline.dwell_for(1), 3.5)
        self.assertEqual(timeline.dwell_for(10), 3.5)
        self.assertEqual(timeline.dwell_for(11), 2.0)
        self.assertEqual(timeline.dwell_for(100), 1.0)

    def test_the_entrance_never_eats_the_reading_window(self):
        """⚠️ Ticket 07 — and the brief's own comment predicted it.

        *"An entrance that runs for a fifth of a card eats a fifth of the time there is to read a number."* At a 1.0 s
        tail slide the default 0.4 s entrance would eat **40 %** of the only time there is, so the span is capped at
        15 % of the dwell — and capped again at the 0.4 s the host repo's `enter()` defaults to.
        """
        self.assertEqual(timeline.span_for(1.0), 0.15)
        self.assertEqual(timeline.span_for(3.5), 0.4)


class TheSchedule(unittest.TestCase):
    def test_the_schedule_and_the_total_agree(self):
        """⚠️ **The arithmetic cross-check, and it is the one that matters.**

        `total_seconds` sums the bands as *seconds*; `schedule` lays them out as *frames*. Two implementations of one
        table, so a disagreement between them is a run that overruns its own cap by exactly the amount nobody checked —
        the failure `total_seconds`'s own docstring names.

        ⚠️ And it is asserted at **100 books**, the real chart, rather than at a small count where a band boundary
        would not be exercised.
        """
        self.assertEqual(
            timeline.total_frames(100), round(timeline.total_seconds(100) * timeline.FPS)
        )

    def test_the_run_is_the_cap_minus_eleven_seconds(self):
        """Ticket 06's table: `6 + 35 + 40 + 42 + 40 + 6 = 169 s` against the brief's 180-second cap."""
        self.assertEqual(timeline.total_seconds(100), 169.0)
        self.assertEqual(timeline.total_frames(100), 5070)
        self.assertLess(timeline.total_seconds(100), timeline.CAP_SECONDS)

    def test_the_intro_and_the_outro_show_no_book(self):
        """⚠️ Their `rank` is `None` — *"which book this slot shows"* — and the renderer keys off that to know which
        slots draw a slide and which draw a card. A `0` here would be a rank no chart has, and a renderer indexing
        `ranked[rank - 1]` would read the **first** book on both.
        """
        slots = timeline.schedule(3)

        self.assertEqual([block.key for block in slots], ["intro", "book", "book", "book", "outro"])
        self.assertIsNone(slots[0].rank)
        self.assertIsNone(slots[-1].rank)

    def test_every_book_slot_is_contiguous_and_in_rank_order(self):
        """⚠️ **No gaps and no overlaps**, because the blocks are placed by accumulating durations rather than by
        each slot computing its own start. A gap would show as a held frame; an overlap as two slides fighting for the
        same frame, which Remotion resolves by *stacking* them rather than by complaining.
        """
        slots = timeline.schedule(12)
        books = [block for block in slots if block.key == "book"]

        self.assertEqual([block.rank for block in books], list(range(1, 13)))
        for earlier, later in zip(slots, slots[1:]):
            self.assertEqual(later.start, earlier.start + earlier.duration)

    def test_the_entrance_never_exceeds_the_ceiling_and_never_eats_the_slide(self):
        """⚠️ Ticket 07's rule, asserted on the frames the renderer actually gets.

        A 3.5 s slide may spend 0.4 s arriving; a 1.0 s tail slide may spend only 0.15 s. The old default would have
        spent 0.4 s on the tail — **40 % of the only time there is to read a publisher**.
        """
        books = [block for block in timeline.schedule(100) if block.key == "book"]
        head, tail = books[0], books[-1]

        self.assertEqual(head.enter_frames, 12)
        self.assertEqual(tail.enter_frames, 4)
        for block in books:
            self.assertLess(block.enter_frames, block.duration)

    def test_a_short_chart_is_a_shorter_run_and_not_a_slower_one(self):
        """⚠️ Ticket 06's *degrade to omission*, one level up: a chart holding sixty-three rows ends at rank 63.

        ⚠️ Padding out to a hundred would hold the outro on the last book for thirty-seven slides' worth of frames —
        a frozen frame at the end of the video, which reads as a broken render rather than as a short chart.
        """
        short = timeline.schedule(63)

        self.assertEqual(sum(1 for block in short if block.key == "book"), 63)
        self.assertLess(timeline.total_frames(63), timeline.total_frames(100))


if __name__ == "__main__":
    unittest.main()
