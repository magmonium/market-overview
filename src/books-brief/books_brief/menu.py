"""The Books Brief's front door — **the week and the chart, asked once, then handed to the conductor as flags.**

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

from . import charts, cli


class Refused(RuntimeError):
    """The menu cannot ask, or was given an answer it cannot use — printed, never a traceback."""


#: ⚠️ The charts the prompt offers, **read off `charts.ALL`** — a menu that listed them itself would be a second place
#: to keep them right, and it would be wrong the first time a chart was added or removed.
CHARTS: tuple[str, ...] = charts.KNOWN


def _offered() -> str:
    """The numbered list the prompt shows — `1 english, 2 bengali, …`."""
    return ", ".join(f"{number} {slug}" for number, slug in enumerate(CHARTS, start=1))


def _checked_charts(typed: str) -> tuple[str, ...]:
    """The charts a typed answer names, as slugs — ⚠️ **refused here rather than at the conductor.**

    ⚠️ The same reason the week is checked here: the conductor's complaint would arrive *after* the question had been
    answered, and a typo is the operator's to fix before a run starts rather than after.

    ⚠️ **A number, a name, or several separated by commas** — because the flag this stands in for (`--chart`) is
    repeatable, so a prompt narrower than the flag would be the front end inventing a limit the tool does not have.
    ⚠️ And the numbers are the *prompt* while the slugs are the *answer*: the operator types `2`, and what reaches the
    conductor is `--chart bengali`.

    ⚠️ **Blank returns `()`, which is the flag's own default** — *every chart the week could build* — rather than four
    names. Saying it with four flags would turn a quiet default into three warnings about charts nobody asked for.

    ⚠️ **Deduplicated and returned in `charts.ALL` order**, so `4,1` and `1,4` ask for the same run — the rule the
    reel's `_tick` keeps, and for the same reason: the same week has to rebuild identically.
    """
    if not typed.strip():
        return ()

    wanted: list[str] = []
    for token in typed.split(","):
        token = token.strip()
        if not token:
            continue
        if token.isdigit() and 1 <= int(token) <= len(CHARTS):
            wanted.append(CHARTS[int(token) - 1])
        elif token in CHARTS:
            wanted.append(token)
        else:
            raise Refused(
                f"{token!r} is not a chart — the charts are {', '.join(CHARTS)}, "
                f"or a number 1 to {len(CHARTS)}, or blank for every one"
            )

    return tuple(slug for slug in CHARTS if slug in set(wanted))


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
    """Parse, ask for whatever a flag did not supply, and hand the week and the chart to the conductor."""
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
        description="One week's Top-100 charts — asks which week and which chart, then builds it.",
    )
    parser.add_argument("--week", help="the ISO week, e.g. 2026-W41 — defaults to this week")
    # ⚠️ The chart has a flag because **no option exists in a menu that a flag cannot express** — so the question below
    # is a convenience over `bb build --chart english`, never a capability of its own.
    parser.add_argument(
        "--chart",
        action="append",
        help="one chart to build; repeatable (default: every chart the week could build)",
    )
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
        asking = given is None
        if asking:
            given = _line("ISO week (YYYY-Wnn, blank for this week)", default=this_week())

        week = _checked(given)

        # ⚠️ ⚠️ **The chart is asked only when the week is also being asked, and that is what makes it safe to add.**
        # Naming the week is how an operator — or a timer, or a CI job — says *"build it, do not interview me"*, and a
        # second prompt on that path would turn `./build books --week 2026-W41` from a command into a question a timer
        # has no terminal to answer. ⚠️ So the chart question belongs to the **interactive** run: the one where the week
        # was not supplied either.
        charts_wanted = options.chart
        if charts_wanted is not None:
            # ⚠️ **An explicit empty value is a typo, the same rule the week keeps.** `--chart ""` was *given*, and
            # answering it with "every chart" would render four when the operator asked for one they mistyped.
            if any(not token.strip() for token in charts_wanted):
                raise Refused("--chart was given nothing — name a chart, or omit it for every one")
            charts_wanted = list(_checked_charts(",".join(charts_wanted)))
        elif asking:
            charts_wanted = list(_checked_charts(_line(f"chart — {_offered()} (blank for every one)")))
        else:
            charts_wanted = []
    except Refused as refusal:
        print(str(refusal), file=sys.stderr)
        return 1

    # ⚠️ The ledger goes to **stdout** and the questions to stderr, so a redirected run reads as a record of what was
    # built rather than as a transcript of the menu. ⚠️ The chart is named only when the run was narrowed, because
    # *"every chart"* is what the bare line has always meant.
    print(f"books · {week}{' · ' + ', '.join(charts_wanted) if charts_wanted else ''}", flush=True)
    flags = [token for chart in charts_wanted for token in ("--chart", chart)]
    return cli.main(["build", "--week", week, *flags])


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
