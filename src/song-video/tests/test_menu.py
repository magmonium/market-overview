"""The front door — `./build`: which product, then what that product needs.

⚠️ **What these tests pin is the hand-off.** The menu owns exactly one thing — the questions and their order — and
everything else belongs to the conductor it calls. So the assertions that matter are the **argv** each conductor
receives, because that is the whole of the contract between them: a menu that asked beautifully and then passed the
wrong flag is a front end that breaks a run nothing else would notice.
"""
from __future__ import annotations

import contextlib
import io
import pathlib
import tempfile
import unittest
from unittest import mock

from song_video import catalogue, menu, paths

from support import write_wav

SONG = "dure-kothay"
TITLE = "দূরে কোথায় (Dure Kothay)"

#: A stand-in catalogue, so this suite never shells out to node. ⚠️ The renderer's *real* list is
#: `test_catalogue.py`'s business — what the menu needs is that it reads it rather than guessing.
THEMES = (catalogue.Entry(id="vinyl", name="Vinyl"), catalogue.Entry(id="neon", name="Neon"))
FORMS = ("bars", "ribbon")


def _no_questions(*_args: object) -> str:
    """The `input` seam: a question nobody was supposed to be asked is a failed test, not a hang."""
    raise AssertionError("the run asked a question — a flag or the folder should have answered it")


class Menu(unittest.TestCase):
    """A temporary data root with one song in it, both conductors stubbed, and stdin under the test's control."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name)
        self.songs = self.root / "resource" / "reel" / "song"
        self.songs.mkdir(parents=True)
        self.master = write_wav(self.songs / f"{SONG}.wav", seconds=1.5)

        for name, value in (("data_root", self.root), ("project_root", self.root)):
            patcher = mock.patch.object(paths, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

        for name, stand_in in (("themes", lambda: THEMES), ("forms", lambda: FORMS)):
            patcher = mock.patch.object(catalogue, name, stand_in)
            patcher.start()
            self.addCleanup(patcher.stop)

        # ⚠️ **Both conductors are stubbed, and that is the whole point of this file**: it tests the menu, not a
        # render. Only `main` is replaced on each module, so the catalogue, the refusals and the prompts are real.
        self.brief = mock.MagicMock(return_value=0)
        self.reel = mock.MagicMock(return_value=0)
        for name, stand_in in (("brief", self.brief), ("reel", self.reel)):
            patcher = mock.patch.object(getattr(menu, name), "main", stand_in)
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_menu(self, *argv: str, answered: list[str] | None = None, terminal: bool = True):
        """Run `./build`, capturing both streams, with stdin either answering or forbidden to."""
        out, err = io.StringIO(), io.StringIO()
        with (
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
            mock.patch("sys.stdin", mock.Mock(isatty=lambda: terminal)),
            mock.patch("builtins.input", side_effect=answered or _no_questions),
        ):
            code = menu.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def handed_to_brief(self) -> list[str]:
        self.assertEqual(self.reel.call_count, 0, "the reel was invoked by a brief run")
        self.assertEqual(self.brief.call_count, 1, "the brief was not handed the run")
        return self.brief.call_args.args[0]

    def handed_to_reel(self) -> list[str]:
        self.assertEqual(self.brief.call_count, 0, "the brief was invoked by a reel run")
        self.assertEqual(self.reel.call_count, 1, "the reel was not handed the run")
        return self.reel.call_args.args[0]


class ChoosingTheBrief(Menu):
    def test_the_editions_and_the_date_it_asked_for_reach_mo_as_flags(self):
        """The questions, then the flags `mo build` would have been given by hand."""
        code, out, err = self.run_menu(answered=["1", "3", "2026-10-14"])

        self.assertEqual(code, 0)
        self.assertEqual(self.handed_to_brief(), ["build", "--lang", "bn", "en", "--date", "2026-10-14"])
        self.assertIn("Market Brief", err, "the project list names the product")
        self.assertIn("brief · bn + en · 2026-10-14", out, "the run it decided on goes to stdout, with the ledger")

    def test_a_blank_date_is_today_and_no_date_flag_at_all(self):
        """⚠️ Today is the *conductor's* default and the menu does not re-implement it: passing today's date
        explicitly would be the front end picking a session, which is the session guard's job."""
        code, _out, _err = self.run_menu(answered=["1", "1", ""])

        self.assertEqual(code, 0)
        self.assertEqual(self.handed_to_brief(), ["build", "--lang", "bn"])

    def test_a_flag_answers_the_question_the_menu_would_have_asked(self):
        code, _out, _err = self.run_menu("brief", "--lang", "en", "--date", "2026-10-14", answered=[])

        self.assertEqual(code, 0)
        self.assertEqual(self.handed_to_brief(), ["build", "--lang", "en", "--date", "2026-10-14"])

    def test_an_unparseable_date_is_refused_before_the_conductor_runs(self):
        code, _out, err = self.run_menu("brief", "--lang", "bn", "--date", "yesterday")

        self.assertEqual(code, 1)
        self.assertIn("YYYY-MM-DD", err)
        self.assertEqual(self.brief.call_count, 0, "a typo must not start a run")


class ChoosingTheReel(Menu):
    def test_the_answers_reach_sv_as_the_flags_it_expects(self):
        # project 2 · title · language (blank → the title's own script) · themes 1,2 · wave 1
        code, _out, err = self.run_menu(answered=["2", TITLE, "", "1,2", "1"])

        self.assertEqual(code, 0)
        self.assertEqual(
            self.handed_to_reel(),
            [
                "build", "--song", SONG, "--title", TITLE, "--lang", "bn",
                "--wave", "bars", "--theme", "vinyl", "--theme", "neon",
            ],
        )
        self.assertNotIn("song — pick one", err, "one master in the folder is not a choice")
        self.assertIn("Song Reel", err)

    def test_the_language_is_offered_from_the_titles_own_script(self):
        """⚠️ A blank answer keeps the derivation — and the derivation is the *title's*, because an English title
        under a Bengali caption is the defect `caption.language_of` exists to prevent."""
        self.run_menu(answered=["2", "Dure Kothay", "", "1", "1"])

        argv = self.handed_to_reel()
        self.assertEqual(argv[argv.index("--lang") + 1], "en")

    def test_the_language_can_be_declared_against_the_scripts_suggestion(self):
        self.run_menu(answered=["2", "Dure Kothay", "bn", "1", "1"])

        argv = self.handed_to_reel()
        self.assertEqual(argv[argv.index("--lang") + 1], "bn", "a declared language wins, and is recorded as one")

    def test_a_second_caption_language_is_refused_rather_than_dropped(self):
        """⚠️ The flag is the brief's too, where it takes several editions — so on the reel, one value is a
        language and two is a request for a product that does not exist."""
        code, _out, err = self.run_menu(
            "reel", "--song", SONG, "--title", TITLE, "--lang", "bn", "en", "--theme", "vinyl", "--wave", "bars"
        )

        self.assertEqual(code, 1)
        self.assertIn("one caption language", err)
        self.assertEqual(self.reel.call_count, 0)

    def test_a_second_song_is_a_question_and_the_answer_picks_it(self):
        write_wav(self.songs / "other.wav", seconds=1.0)

        code, _out, err = self.run_menu(answered=["2", "1", TITLE, "", "1", "1"])

        self.assertEqual(code, 0)
        self.assertIn("song", err, "two masters is a choice")
        self.assertEqual(self.handed_to_reel()[2], SONG, "the id, by the number the menu offered")

    def test_a_blank_title_is_refused_rather_than_invented(self):
        code, _out, err = self.run_menu(answered=["2", ""])

        self.assertEqual(code, 1)
        self.assertIn("needs a title", err)
        self.assertEqual(self.reel.call_count, 0)

    def test_replay_asks_nothing_and_is_passed_through(self):
        code, _out, _err = self.run_menu("reel", "--song", SONG, "--replay", answered=[])

        self.assertEqual(code, 0)
        self.assertEqual(self.handed_to_reel(), ["build", "--song", SONG, "--replay"])

    def test_the_conductors_exit_status_is_the_front_doors(self):
        self.reel.return_value = 3

        code, _out, _err = self.run_menu(
            "reel", "--song", SONG, "--title", TITLE, "--lang", "bn", "--theme", "vinyl", "--wave", "bars"
        )

        self.assertEqual(code, 3, "a failed run must not look like a successful menu")


class Refusals(Menu):
    def test_no_terminal_and_no_product_refuses_without_asking_or_running(self):
        code, _out, err = self.run_menu(terminal=False)

        self.assertEqual(code, 1)
        self.assertIn("build brief", err, "the refusal says what to type instead")
        self.assertEqual((self.brief.call_count, self.reel.call_count), (0, 0))

    def test_the_refusal_comes_before_the_first_question(self):
        """⚠️ The reel's own discipline: a menu that asks what it can and *then* dies on stdin has spent the
        operator's typing and taught them nothing."""
        _code, _out, err = self.run_menu(terminal=False)

        self.assertNotIn("Market Brief", err, "the project list was printed before the refusal")

    def test_a_reel_flag_on_a_brief_run_is_refused_rather_than_dropped(self):
        code, _out, err = self.run_menu("brief", "--lang", "bn", "--theme", "vinyl")

        self.assertEqual(code, 1)
        self.assertIn("--theme", err)
        self.assertEqual(self.brief.call_count, 0)

    def test_a_date_on_a_reel_run_is_refused(self):
        code, _out, err = self.run_menu(
            "reel", "--date", "2026-10-14", "--song", SONG, "--title", TITLE, "--lang", "bn",
            "--theme", "vinyl", "--wave", "bars",
        )

        self.assertEqual(code, 1)
        self.assertIn("--date", err)
        self.assertEqual(self.reel.call_count, 0)


if __name__ == "__main__":
    unittest.main()
