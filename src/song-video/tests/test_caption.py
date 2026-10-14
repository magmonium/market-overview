"""The caption's value half — the duration, written in the caption's own numerals. (Map issue 08)

⚠️ **The Bengali case is the whole reason this module exists.** `৪:০০` is not `4:00` with a font applied — the
digits are different characters, and a Bengali caption in ASCII numerals reads as unfinished to the audience it is
written for. The render layer owns the *word*; this owns the *number*.
"""
import unittest

from song_video import caption


class TheScriptOfATitle(unittest.TestCase):
    def test_a_bengali_title_chooses_a_bengali_caption(self):
        self.assertEqual(caption.language_of("দূরে কোথায়"), "bn")
        # ⚠️ Mixed is still Bengali: an artist's Latin name does not make the title English.
        self.assertEqual(caption.language_of("দূরে কোথায় (Dure Kothay)"), "bn")

    def test_everything_else_is_english(self):
        self.assertEqual(caption.language_of("Dure Kothay"), "en")
        self.assertEqual(caption.language_of(""), "en", "an empty title cannot choose a script, so it defaults")


class TheDuration(unittest.TestCase):
    def test_the_duration_is_minutes_and_seconds_in_the_scripts_own_digits(self):
        # 240.024 s is the real four-minute song this was built against — and it must read as 4:00, not 4:00.02.
        self.assertEqual(caption.duration_at(240.024, lang="en"), "4:00")
        self.assertEqual(caption.duration_at(240.024, lang="bn"), "৪:০০")

    def test_the_seconds_are_padded_and_the_rounding_is_to_the_nearest_second(self):
        self.assertEqual(caption.duration_at(65.4, lang="en"), "1:05")
        self.assertEqual(caption.duration_at(65.6, lang="en"), "1:06")
        self.assertEqual(caption.duration_at(9.0, lang="en"), "0:09")
        self.assertEqual(caption.duration_at(9.0, lang="bn"), "০:০৯")

    def test_a_piece_longer_than_an_hour_grows_minutes_rather_than_an_hours_field(self):
        self.assertEqual(caption.duration_at(3663.0, lang="en"), "61:03", "a song is minutes long, even a long one")

    def test_an_unknown_language_is_refused_rather_than_guessed(self):
        with self.assertRaises(ValueError) as caught:
            caption.duration_at(240.0, lang="fr")

        self.assertIn("fr", str(caught.exception))
        self.assertIn("bn, en", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
