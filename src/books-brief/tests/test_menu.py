"""The Books Brief's front door — and the two rules a menu has to keep to be worth having.

⚠️ **It asks nothing a flag could have said**, and ⚠️ **it refuses before it asks.** The second is the one that is easy
to skip: a menu that asks what it can and *then* dies on stdin has spent the operator's typing and taught them nothing —
the reel's own `_screen` discipline, kept here.
"""
import contextlib
import io
import sys
import unittest
from unittest import mock

from books_brief import cli, menu


class TheWeek(unittest.TestCase):
    def _run(self, argv: list[str], *, tty: bool = True) -> tuple[int, list[list[str]]]:
        """Run the menu with the conductor captured, returning `(exit code, what it was handed)`."""
        seen: list[list[str]] = []

        with (
            mock.patch.object(cli, "main", side_effect=lambda handed: seen.append(handed) or 0),
            mock.patch.object(sys, "stdin", mock.Mock(isatty=lambda: tty)),
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            return menu.main(argv), seen

    def test_a_week_given_on_the_command_line_is_handed_straight_to_the_conductor(self):
        """⚠️ **The property that makes the menu safe to add**: no option exists in it that a flag cannot express.

        `./build books --week 2026-W41` must reach the conductor as `bb build --week 2026-W41` and **ask nothing** — so
        a script, a timer or a CI job never touches the prompts at all. That is the reel's own arrangement, and the
        reason `./build` is a front end rather than a second implementation.
        """
        code, seen = self._run(["--week", "2026-W41"])

        self.assertEqual(code, 0)
        self.assertEqual(seen, [["build", "--week", "2026-W41"]])

    def test_the_week_is_normalised_before_it_keys_a_folder(self):
        """⚠️ **The store is keyed by this string**, so `2026-W4` and `2026-W04` would be two different weeks — one of
        which can never be found again by the run that wrote it.
        """
        code, seen = self._run(["--week", "2026-W4"])

        self.assertEqual(code, 0)
        self.assertEqual(seen, [["build", "--week", "2026-W04"]])

    def test_a_week_that_is_not_a_week_is_refused_before_the_conductor_is_asked(self):
        """⚠️ **`2026-W99` looks perfectly well-formed and is not a week.**

        That is why the check goes through `date.fromisocalendar` rather than a pattern — and why it happens **here**: the
        conductor's complaint would arrive after the question had been asked, and a typo is the operator's to fix before
        a run starts rather than after.
        """
        for wrong in ("2026-W99", "2026-W00", "week 41", "2026", ""):
            with self.subTest(week=wrong):
                code, seen = self._run(["--week", wrong])

                self.assertEqual(code, 1)
                self.assertEqual(seen, [], "the conductor must not have been reached")

    def test_no_terminal_and_no_week_refuses_rather_than_hanging_on_stdin(self):
        """⚠️ **Refused before the question, not after it.**

        A timer, a CI job or a piped invocation has no terminal. `input()` there raises `EOFError` — a traceback for what
        is really *"you did not tell me which week"* — so the guard runs first and says so in words.
        """
        code, seen = self._run([], tty=False)

        self.assertEqual(code, 1)
        self.assertEqual(seen, [])

    def test_this_week_is_an_iso_week_the_store_can_key_on(self):
        """⚠️ The menu is the **one** place in this product that reads a clock, and it is allowed to — a human is being
        asked what to build, and the answer is passed as a flag. Everything downstream stays deterministic (ADR 0003).
        """
        week = menu.this_week()

        self.assertRegex(week, r"^\d{4}-W\d{2}$")
        # ⚠️ And it is a real week, not merely a well-shaped string.
        self.assertEqual(menu._checked(week), week)

    def test_a_named_subcommand_is_passed_straight_through_without_asking(self):
        """⚠️ **The front door has to reach `publish`, and it must not ask a question on the way.**

        `bb publish --week 2026-W41` names its week as a flag and asks nothing — so a menu that prompted first would ask
        an already-answered question, and on a timer it would die on `input()` instead of publishing. ⚠️ The prompt is the
        menu's job; the subcommand list is `cli.main`'s, and this line is the seam between the two.
        """
        with mock.patch.object(cli, "main", return_value=0) as conductor:
            code = menu.main(["publish", "--week", "2026-W41", "--dry-run"])

        self.assertEqual(code, 0)
        conductor.assert_called_once_with(["publish", "--week", "2026-W41", "--dry-run"])

    def test_the_bare_command_still_asks_and_still_builds(self):
        """⚠️ The other half: passing a command through must not have made the menu forget its own job."""
        code, seen = self._run(["--week", "2026-W41"], tty=False)

        self.assertEqual(code, 0)
        self.assertEqual(seen, [["build", "--week", "2026-W41"]])


if __name__ == "__main__":
    unittest.main()
