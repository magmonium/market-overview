"""The Books Brief's front door — **the week, asked once, then handed to the conductor as a flag.**

⚠️ **A front end, not a second implementation.** Nothing about the run is defined here: the menu asks, then calls
`books_brief.cli.main(["build", "--week", …])`, and the conductor runs exactly as it does from `bb build --week …`.
⚠️ **No option exists in the menu that a flag cannot express** — that is the property that makes `bb build --week
2026-W41` the scriptable path and this merely a convenience over it.

⚠️ **Why this lives here and not in `song_video.menu`, where the other two products' menu lives.** The dependency runs
`song-video → market-overview` and `books-brief → market-overview`, and **no sibling depends on another** — so the
reel's environment cannot import this package, and neither can the brief's. That is not an accident to work around; it is
the boundary that keeps a third product from becoming a fourth package inside the second. ⚠️ The consequence is that
`./build` **dispatches the environment per product** rather than running one menu that knows them all.

⚠️ **The prompts are this product's own**, and they follow the reel's conventions rather than importing them (they are
not importable): questions go to **stderr** so stdout stays the ledger, and a numbered list answers with a number.

⚠️ **This is the one place in the product that reads a clock**, and it is allowed to: a *human* is being asked what to
build, and the answer is passed as a flag. Everything downstream stays deterministic, because the week is an argument and
never a second reading of the calendar (ADR 0003).
"""
from __future__ import annotations

import argparse
import datetime as _datetime
import sys

from . import cli


class Refused(RuntimeError):
    """The menu cannot ask, or was given an answer it cannot use — printed, never a traceback."""


def this_week() -> str:
    """The current ISO week, as the default the prompt **shows**.

    ⚠️ Shown and not merely applied — the reel's rule: *"a pre-filled answer the operator cannot see is an answer they
    were never asked for."*
    """
    iso = _datetime.date.today().isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _line(question: str, *, default: str = "") -> str:
    """One free-text answer, with a default an empty line accepts."""
    shown = f" [{default}]" if default else ""
    print(f"  {question}{shown}: ", end="", file=sys.stderr, flush=True)
    return input().strip() or default


def _checked(week: str) -> str:
    """⚠️ **Validated here rather than left to the conductor**, because the conductor's complaint would arrive after the
    question had been asked — and a typo is the operator's to fix before a run starts, not after.

    ⚠️ Parsed through `fromisocalendar`, not by pattern-matching the string: `2026-W99` looks perfectly well-formed and
    is not a week. The store is keyed by this string, so a wrong one is a folder that can never exist.
    """
    year, _, number = week.partition("-W")
    try:
        _datetime.date.fromisocalendar(int(year), int(number), 1)
    except (ValueError, TypeError):
        raise Refused(
            f"{week!r} is not an ISO week — the form is `2026-W41`, and the store is keyed by it"
        ) from None
    return f"{int(year)}-W{int(number):02d}"


def main(argv: list[str] | None = None) -> int:
    """Parse, ask for whatever a flag did not supply, and hand the week to the conductor."""
    arguments = list(sys.argv[1:] if argv is None else argv)

    # ⚠️ **A named subcommand is passed straight through, and that is what keeps the front door complete.**
    #
    # `bb publish` needs a week and takes flags, but it **asks nothing** — so routing it through the prompt below would
    # ask a question the operator had already answered, and a timer has no terminal to answer it on. ⚠️ The menu's job is
    # the *question*; the subcommand list belongs to `cli.main`, and this is the one line that says so.
    if arguments and arguments[0] in ("build", "publish"):
        return cli.main(arguments)

    parser = argparse.ArgumentParser(
        prog="build books",
        description="One week's four Top-100 charts — asks which week, then builds it.",
    )
    parser.add_argument("--week", help="the ISO week, e.g. 2026-W41 — defaults to this week")
    options = parser.parse_args(argv)

    try:
        if options.week is None and not sys.stdin.isatty():
            # ⚠️ Refused **before** the question, the reel's own discipline: a menu that asks what it can and then dies
            # on stdin has spent the operator's typing and taught them nothing.
            raise Refused(
                "there is no terminal to ask on (stdin is not a tty) — name the week, "
                "`./build books --week 2026-W41`, or run from a terminal"
            )

        # ⚠️ **`is None`, not falsy — and this is the difference between a front end and a nuisance.** `--week ""` was
        # *given*: an operator or a script that passed the flag meant to name a week, and re-asking (or worse, quietly
        # substituting this week) answers a question nobody asked. An explicit empty value is a typo to refuse, and only
        # an *absent* flag is a question to ask.
        given = options.week
        if given is None:
            given = _line("ISO week (YYYY-Wnn, blank for this week)", default=this_week())

        week = _checked(given)
    except Refused as refusal:
        print(str(refusal), file=sys.stderr)
        return 1

    # ⚠️ The ledger goes to **stdout** and the questions to stderr, so a redirected run reads as a record of what was
    # built rather than as a transcript of the menu.
    print(f"books · {week}", flush=True)
    return cli.main(["build", "--week", week])


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
