"""0087_07, 0087_10 — the upload text: a title and a description, for the song and for search.

⚠️ **The assertions that matter are the ones about *truth* and *fit*.** Truth: everything in these files comes from the
recorded answers, so a rebuild publishes the same words — and the description says nothing about the music that the
pipeline could not know. Fit: YouTube shows 100 characters of a title, so a title that will not fit is a **refusal**
rather than a snippet that ends mid-word.
"""
import pathlib
import unittest

from song_video import seo

#: Their song, as Python measured and wrote it: 182.040 s, `৩:০২`.
SECONDS = 182.04
TITLE = "বেশরম লতার মতো"


class TheTitle(unittest.TestCase):
    def test_the_song_leads_and_the_length_and_the_genre_follow(self):
        line = seo.title_for(TITLE, lang="bn", seconds=SECONDS)

        self.assertEqual(line, f"{TITLE} | ৩:০২ | বাংলা গান")
        self.assertLessEqual(len(line), seo.TITLE_LIMIT)

    def test_an_artist_is_placed_between_the_song_and_the_length(self):
        """⚠️ The song's name is the query; the artist is the second thing anybody types."""
        line = seo.title_for(TITLE, lang="bn", seconds=SECONDS, artist="অজয় চক্রবর্তী")

        self.assertEqual(line, f"{TITLE} | অজয় চক্রবর্তী | ৩:০২ | বাংলা গান")

    def test_a_title_that_will_not_fit_a_search_result_is_refused_rather_than_cut(self):
        """⚠️ **A refusal, never a truncation.** Trimming the artist's name off the end of their own song's title is the
        kind of help nobody forgives — and the reel's own rule applies: a title that will not fit is a title to shorten."""
        with self.assertRaises(seo.SeoError) as caught:
            seo.title_for("গ" * 120, lang="bn", seconds=SECONDS)

        message = str(caught.exception)
        self.assertIn("over the 100", message)
        self.assertIn("shorten", message)

    def test_the_one_hundredth_character_is_still_fine(self):
        """⚠️ The boundary, asserted: the ceiling is a limit, not a hint — 100 is a title that fits."""
        room = seo.TITLE_LIMIT - len(f" | ৩:০২ | বাংলা গান")
        line = seo.title_for("ক" * room, lang="bn", seconds=SECONDS)

        self.assertEqual(len(line), seo.TITLE_LIMIT)

    def test_an_unknown_language_is_refused_rather_than_answered_in_english(self):
        with self.assertRaises(seo.SeoError):
            seo.title_for(TITLE, lang="fr", seconds=SECONDS)


class TheDescription(unittest.TestCase):
    def test_the_length_is_written_twice_because_it_is_searched_twice(self):
        page = seo.upload_for(TITLE, lang="bn", seconds=SECONDS).description

        self.assertIn("৩:০২", page, "the clock face, exactly as the video, the still and the ledger write it")
        self.assertIn("৩ মিনিট ২ সেকেন্ড", page, "and spelled out, which is how it gets typed into a search box")

    def test_the_description_says_only_what_the_pipeline_knows(self):
        """⚠️ The one sentence of editorial copy states a fact about *this pipeline* — the song is the master, complete
        and untouched (issue 09) — and nothing about the music's mood, meaning or origin, because none of that was
        supplied, and a generated file that guesses is worse than no file."""
        page = seo.upload_for(TITLE, lang="bn", seconds=SECONDS).description

        self.assertIn("কোনও কাটছাঁট নেই", page)
        self.assertIn("অপরিবর্তিত", page)
        self.assertIn("#বাংলাগান", page, "the tags, which are how a browse query finds it")
        self.assertIn("Bangla song", page, "⚠️ both scripts, because people search in both")

    def test_an_artist_is_a_line_when_given_and_absent_when_not(self):
        """⚠️ **Nothing is left as a placeholder.** A generated file that has to be edited before it can be used is not a
        generated file — so an unnamed artist means a shorter description, never `শিল্পী: ……` for somebody to fill in."""
        with_artist = seo.upload_for(TITLE, lang="bn", seconds=SECONDS, artist="অজয় চক্রবর্তী").description
        without = seo.upload_for(TITLE, lang="bn", seconds=SECONDS).description

        self.assertIn("শিল্পী: অজয় চক্রবর্তী", with_artist)
        self.assertNotIn("শিল্পী", without)
        self.assertTrue(without.startswith(TITLE), "and the song is still the first line")

    def test_the_same_answers_write_the_same_two_files(self):
        """⚠️ Determinism, the same promise the frames keep (ADR 0003): a rebuild publishes the same words."""
        first = seo.upload_for(TITLE, lang="bn", seconds=SECONDS, artist="ক")
        again = seo.upload_for(TITLE, lang="bn", seconds=SECONDS, artist="ক")
        other = seo.upload_for(TITLE, lang="bn", seconds=SECONDS)

        self.assertEqual(first, again)
        self.assertNotEqual(first, other, "…and a different answer is a different file")

    def test_an_english_run_gets_english_copy(self):
        upload = seo.upload_for("Dure Kothay", lang="en", seconds=240.0)

        self.assertEqual(upload.title, "Dure Kothay | 4:00 | Bengali song")
        self.assertIn("the full song, uncut", upload.description)
        self.assertIn("4 min 0 sec", upload.description)


if __name__ == "__main__":
    unittest.main()
