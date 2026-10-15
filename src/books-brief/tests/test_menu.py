"""The Books Brief's front door — and the two rules a menu has to keep to be worth having.

⚠️ **It asks nothing a flag could have said**, and ⚠️ **it refuses before it asks.** The second is the one that is easy
to skip: a menu that asks what it can and *then* dies on stdin has spent the operator's typing and taught them nothing —
the reel's own `_screen` discipline, kept here.
"""
import contextlib
import datetime as _datetime
import io
import sys
import unittest
from unittest import mock

from books_brief import charts, cli, menu


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

    def test_the_default_is_the_last_week_whose_lists_can_exist(self):
        """⚠️ ⚠️ **The bug this fixes, asserted.**

        A Sun–Sat sales week is compiled *after* it closes, so **this** week can never be built yet — and a prompt
        pre-filled with it sent every operator, every time, into `no chart could be built` and a message about a vendor
        that had done nothing wrong.

        ⚠️ Pinned as the two *properties* that make the answer right, rather than as a literal week: the week's own
        Sunday has passed, and the next week's has not.
        """
        week = menu.last_buildable_week()
        today = _datetime.date.today()

        self.assertEqual(menu._checked(week), week, "the default has to be a week the store can key on")
        self.assertNotEqual(week, menu.this_week(), "this week's lists cannot exist yet")
        self.assertLess(menu._closed_on(week), today, "the week has to have closed")
        # ⚠️ The **next** week's Sunday, which is this one plus seven days — no second helper needed, and no assumption
        # about which week this is.
        self.assertGreaterEqual(menu._closed_on(week) + _datetime.timedelta(days=7), today)

    def test_the_prompt_offers_the_last_buildable_week_rather_than_this_one(self):
        """⚠️ **What the operator actually sees.** The default is *shown*, so a wrong offer is one keystroke from being
        corrected — which is why the value matters and why the question now says why it is not this week.
        """
        offered: list[str] = []

        with (
            mock.patch.object(cli, "main", return_value=0),
            mock.patch.object(
                menu, "_line", side_effect=lambda question, *, default="": offered.append(default) or default
            ),
            mock.patch.object(sys, "stdin", mock.Mock(isatty=lambda: True)),
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            menu.main([])

        # ⚠️ The first prompt is the week and the second is the chart, whose own default is the empty answer.
        self.assertEqual(offered, [menu.last_buildable_week(), ""])

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


class TheChart(unittest.TestCase):
    """⚠️ **The second question** — and the two rules it has to keep to be worth adding.

    ⚠️ **It is a convenience over `--chart`, never a capability of its own**: the number is the prompt and the slug is
    what reaches the conductor. ⚠️ And **a week named as a flag is asked nothing** — that is the path a timer or a CI
    job runs, and a second prompt on it would turn a command into a question no timer can answer.
    """

    def _run(
        self, argv: list[str], *, answers: list[str] = (), tty: bool = True
    ) -> tuple[int, list[list[str]]]:
        """Run the menu with the prompts answered from `answers`, returning `(exit code, what was handed on)`.

        ⚠️ **`_line` is the seam, not stdin.** The prompts are the only thing under test here, and patching them is both
        simpler and stricter than feeding a fake terminal — ⚠️ with no answers left, a prompt this test did not expect
        **raises** rather than quietly passing.
        """
        seen: list[list[str]] = []

        with (
            mock.patch.object(cli, "main", side_effect=lambda handed: seen.append(handed) or 0),
            mock.patch.object(menu, "_line", side_effect=answers),
            mock.patch.object(sys, "stdin", mock.Mock(isatty=lambda: tty)),
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            return menu.main(argv), seen

    def test_a_numbered_answer_reaches_the_conductor_as_the_chart_flag(self):
        """⚠️ **The number is the prompt and the slug is the answer.** The operator types `2`; what the conductor is
        handed is `--chart english` — so the question is a front end for the flag, not a second vocabulary.

        ⚠️ **The numbers follow `charts.ALL`'s own order** — `bengali` first, because that is the chart the product is
        named after — which is why `2` is `english` and not `1`.
        """
        code, seen = self._run([], answers=["2026-W41", "2"])

        self.assertEqual(code, 0)
        self.assertEqual(seen, [["build", "--week", "2026-W41", "--chart", "english"]])

    def test_the_prompt_is_built_from_the_declaration_rather_than_a_copy_of_it(self):
        """⚠️ **A menu that listed the charts itself would be a second place to keep them right**, and it would be wrong
        the first time a chart was added or removed. ⚠️ Pinned as an equality, so adding a chart to `charts.ALL` cannot
        leave this prompt behind.
        """
        self.assertEqual(menu.CHARTS, charts.KNOWN)
        self.assertEqual(menu._offered(), "1 bengali, 2 english, 3 all-language, 4 comics")

    def test_a_name_is_accepted_as_well_as_a_number(self):
        """⚠️ The prompt shows numbers and the flag takes names, so an operator will type either — refusing one of them
        would be the front end inventing a rule the tool does not have.
        """
        code, seen = self._run([], answers=["2026-W41", "comics"])

        self.assertEqual(code, 0)
        self.assertEqual(seen, [["build", "--week", "2026-W41", "--chart", "comics"]])

    def test_several_are_accepted_because_the_flag_is_repeatable(self):
        """⚠️ **A prompt narrower than its flag is a limit the front end invented.** `--chart` may be given more than
        once, so the question may be answered with more than one — ⚠️ and the answer comes back in `charts.ALL` order,
        so `4,2` and `2,4` ask for the same run rather than two orders of the same one.
        """
        code, seen = self._run([], answers=["2026-W41", "4,2"])

        self.assertEqual(code, 0)
        self.assertEqual(seen, [["build", "--week", "2026-W41", "--chart", "english", "--chart", "comics"]])

    def test_the_same_two_charts_typed_the_other_way_round_ask_for_the_same_run(self):
        """⚠️ **The determinism rule, one layer up.** The flags reach the conductor in declaration order whatever order
        the numbers were typed, so a re-typed answer cannot produce a different run.
        """
        _, forwards = self._run([], answers=["2026-W41", "2,4"])
        _, backwards = self._run([], answers=["2026-W41", "4,2"])

        self.assertEqual(forwards, backwards)

    def test_blank_means_every_chart_and_is_said_with_no_flags_at_all(self):
        """⚠️ **The quiet default.** *Every chart the week could build* is exactly what an absent `--chart` means, so
        saying it with four flags would turn a default into three warnings about charts nobody asked for.
        """
        code, seen = self._run([], answers=["2026-W41", ""])

        self.assertEqual(code, 0)
        self.assertEqual(seen, [["build", "--week", "2026-W41"]])

    def test_a_chart_that_is_not_a_chart_is_refused_before_the_conductor_is_asked(self):
        """⚠️ The week's own rule, one question along: a typo is the operator's to fix **before** a run starts, not
        after — because by then the question has been answered and the render may already be committed to.
        """
        for wrong in ("7", "hindi", "0", "english-ish"):
            with self.subTest(answer=wrong):
                code, seen = self._run([], answers=["2026-W41", wrong])

                self.assertEqual(code, 1)
                self.assertEqual(seen, [], "the conductor must not have been reached")

    def test_a_week_named_as_a_flag_asks_nothing_at_all(self):
        """⚠️ ⚠️ **The rule that keeps the menu safe to extend.**

        `./build books --week 2026-W41` is the scriptable path — a timer or a CI job runs exactly that — so it must not
        acquire a second question. ⚠️ The chart question belongs to the **interactive** run: the one where the week was
        not supplied either. ⚠️ Asserted by giving `_line` no answers at all, so a prompt here would raise.
        """
        code, seen = self._run(["--week", "2026-W41"], answers=[])

        self.assertEqual(code, 0)
        self.assertEqual(seen, [["build", "--week", "2026-W41"]])

    def test_a_chart_named_as_a_flag_is_handed_on_and_not_asked_again(self):
        """⚠️ *"Asks for whatever a flag did not supply"* — so a chart given as a flag passes through, and only the week
        is asked for.
        """
        code, seen = self._run(["--chart", "english"], answers=["2026-W41"])

        self.assertEqual(code, 0)
        self.assertEqual(seen, [["build", "--week", "2026-W41", "--chart", "english"]])


if __name__ == "__main__":
    unittest.main()
