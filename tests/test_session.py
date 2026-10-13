"""The session clock, and the two distinct ways a run must refuse."""
import datetime
import unittest

from market_overview import session

# Real vendor timestamps for the 2026-10-12 session.
BAR = 1791776700          # 09:15 IST — the session open, so this dates the session
MID_SESSION = 1791793800  # 14:00 IST — the bar exists and is still moving
FEED_CAUGHT_UP = 1791799800  # 15:40 IST — the threshold: ten minutes past the close
JUST_CLOSED = 1791799740     # 15:39 IST — closed, but the delayed feed has not caught up
LATE_WRITE = 1791800043      # 15:44:03 IST — the final write 2026-10-13 refused on
FINAL = 1791801917           # 16:15 IST — finished printing


class SessionDate(unittest.TestCase):
    def test_the_bar_dates_the_session_in_ist(self):
        self.assertEqual(session.session_date(BAR), datetime.date(2026, 10, 12))

    def test_the_open_is_0915_ist(self):
        self.assertEqual(session.in_ist(BAR).time(), session.SESSION_OPEN)


class EnsureFinal(unittest.TestCase):
    def test_a_final_session_is_accepted(self):
        self.assertEqual(
            session.ensure_final(BAR, FINAL, "2026-10-12"), datetime.date(2026, 10, 12)
        )

    def test_the_wrong_day_is_refused_as_a_holiday(self):
        """⚠️ The dangerous one: a holiday produces no error, only the previous numbers."""
        with self.assertRaises(session.StaleSessionError) as caught:
            session.ensure_final(BAR, FINAL, "2026-10-11")
        self.assertIn("2026-10-11", str(caught.exception))
        self.assertIn("2026-10-12", str(caught.exception))

    def test_a_mid_session_run_is_refused(self):
        with self.assertRaises(session.StaleSessionError) as caught:
            session.ensure_final(BAR, MID_SESSION, "2026-10-12")
        self.assertIn("not finished printing", str(caught.exception))

    def test_a_run_before_the_feed_catches_up_is_refused(self):
        """Closed at 15:30, but the india feed is ~15 min delayed — at 15:39 it is still moving."""
        with self.assertRaises(session.StaleSessionError):
            session.ensure_final(BAR, JUST_CLOSED, "2026-10-12")

    def test_the_threshold_is_accepted(self):
        """⚠️ 15:40 exactly — the accepting side of the boundary `FINAL_FROM` sets.

        Stated rather than implied, so that moving the constant has to move this case too.
        """
        self.assertEqual(
            session.ensure_final(BAR, FEED_CAUGHT_UP, "2026-10-12"), datetime.date(2026, 10, 12)
        )

    def test_the_final_write_that_refused_a_whole_day_is_accepted(self):
        """⚠️ 15:44:03 IST — the 2026-10-13 clock row, and the case that moved `FINAL_FROM`.

        Not because the minute is special, but because of the shape of the refusal: the write
        had already happened, so every retry re-sent the same request and got the same answer
        for the rest of the day — and the server's 16:30 firing would have refused with it.
        """
        self.assertEqual(
            session.ensure_final(BAR, LATE_WRITE, "2026-10-12"), datetime.date(2026, 10, 12)
        )

    def test_an_update_from_another_day_is_refused(self):
        with self.assertRaises(session.StaleSessionError):
            session.ensure_final(BAR, FINAL - 86400, "2026-10-12")


if __name__ == "__main__":
    unittest.main()
