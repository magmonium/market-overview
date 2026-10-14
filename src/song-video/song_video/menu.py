"""The front door — one menu over both products, run by `./build`.

⚠️ **A front end, not a second implementation.** The menu asks, then hands the answers to the tools that already
own them — `market_overview.cli.main` for the brief, `song_video.cli.main` for the reel — as **flags**, and both
conductors then run exactly as they do from `mo build` and `sv build`. Nothing about either product's run is
defined here, and **no option exists in the menu that a flag cannot express**: the scheduled brief
(`mo build --lang bn en`) and `sv build --replay` keep working untouched.

⚠️ **Why the menu lives in the reel's package.** The dependency runs `song-video → market-overview`, so this is the
only environment where *both* are importable — a brief that could launch the reel would have to depend on a product
built from a folder inside itself. `./build` is a three-line script that runs this module through that environment.

⚠️ **The prompts are the reel's own**, imported rather than re-written: questions go to stderr so stdout stays the
ledger, and a numbered list answers with a number. A second prompt style would be a second thing to keep in step.
"""
from __future__ import annotations

import argparse
import datetime as _datetime
import sys

from market_overview import cli as brief

from . import caption, catalogue, cli as reel, library, paths

#: The projects the menu offers: id, name, and what the product is — the *product*, because that is what is being
#: chosen, with the tool's name beside it because that is what the operator will type directly.
PROJECTS: tuple[tuple[str, str, str], ...] = (
    ("brief", "Market Brief", "market-overview · one day's Indian market, Bengali + English"),
    ("reel", "Song Reel", "song-video · one supplied song, one or more themes"),
)

#: The brief's editions, as the prompt's own `(id, label)` pairs. ⚠️ `bn en` is here and named for what it is: the
#: pair the schedule builds, and the only answer that produces a complete day in one run.
EDITIONS: tuple[tuple[str, str], ...] = (
    ("bn", "bn — Bengali: what a bare `mo build` makes"),
    ("en", "en — English"),
    ("bn en", "bn + en — both editions: what the daily schedule builds"),
)

#: ⚠️ Flags that belong to one product only. Passed to the other they are **refused, not ignored**: a front end
#: that silently drops `--theme` from a brief run teaches the operator that the flag did nothing, which is only
#: true until the day it means something.
REEL_ONLY: tuple[str, ...] = ("song", "title", "theme", "wave", "artist", "cover", "replay")


def _line(question: str, *, default: str = "") -> str:
    """One free-text answer, with a default an empty line accepts.

    ⚠️ The default is **shown**, not merely applied: a pre-filled answer the operator cannot see is an answer they
    were never asked for — which is exactly the objection to the reel's language being derived silently.
    """
    shown = f" [{default}]" if default else ""
    print(f"  {question}{shown}: ", end="", file=sys.stderr, flush=True)
    return input().strip() or default


def _chosen(kind: str, value: str, available: tuple[str, ...]) -> str:
    """Refuse an answer outside the catalogue, in the catalogue's own words."""
    if value not in available:
        raise reel.Refused(f"unknown {kind} {value!r} — the choices are {', '.join(available)}")
    return value


def _menu_one(kind: str, choices: tuple[tuple[str, str], ...]) -> str:
    """The reel's own numbered prompt, reused rather than re-written."""
    return reel._menu_one(kind, list(choices))


def _menu_many(kind: str, choices: tuple[tuple[str, str], ...]) -> tuple[str, ...]:
    return reel._menu_many(kind, list(choices))


# ── the brief ────────────────────────────────────────────────────────────────────────────────────────────


def _brief(options: argparse.Namespace) -> int:
    """Edition(s), then the date — the two things the brief's own run is asked for."""
    editions = options.lang or _menu_one("edition", EDITIONS).split()
    date = options.date or _line("session date (YYYY-MM-DD, blank for today)")
    if date:
        # ⚠️ Validated here rather than left to the conductor, because the conductor's complaint would arrive after
        # two questions had been asked — and a typo is the operator's to fix before the run starts, not after.
        try:
            date = _datetime.date.fromisoformat(date).isoformat()
        except ValueError:
            raise reel.Refused(f"the date must be YYYY-MM-DD, got {date!r}") from None

    print(f"brief · {' + '.join(editions)} · {date or 'today'}", flush=True)
    argv = ["build", "--lang", *editions]
    if date:
        argv += ["--date", date]
    return brief.main(argv)


# ── the reel ─────────────────────────────────────────────────────────────────────────────────────────────


def _one_language(options: argparse.Namespace) -> str | None:
    """The single `--lang` value a one-language product can take, or `None` if none was given.

    ⚠️ **The flag is shared with the brief, where it takes several editions** (`nargs="+"`), so the reel has to
    narrow it to one — and a second value is **refused rather than dropped**: `build reel --lang bn en` asks for a
    product that does not exist, because a song has one caption.
    """
    if not options.lang:
        return None
    if len(options.lang) > 1:
        raise reel.Refused(
            f"a reel has one caption language, and {len(options.lang)} were given — "
            f"the choices are {', '.join(caption.LANGUAGES)}"
        )
    return options.lang[0]


def _reel(options: argparse.Namespace) -> int:
    """Song, title, then the language, the themes and the wave form.

    ⚠️ **The title is asked before the language, and that order is the point.** The caption's script is normally
    *derived* from the title's own script (`caption.language_of`), so the menu offers that derivation as the
    default and one key accepts it — asking first would let the operator declare a language that the title they
    then type contradicts. `--lang` still overrides, exactly as it always could.
    """
    song = options.song or _song()
    if options.replay:
        print(f"reel · {song} · replaying the recorded run", flush=True)
        return reel.main(["build", "--song", song, "--replay"])

    title = options.title or _line("title (what the video shows)")
    if not title:
        raise reel.Refused("a reel needs a title — it is typed, never read out of a filename")

    lang = _chosen(
        "language",
        _one_language(options) or _line("caption language (bn/en)", default=caption.language_of(title)),
        caption.LANGUAGES,
    )
    themes = tuple(options.theme) or _menu_many("theme", _themes())
    wave = options.wave or _menu_one("wave form", tuple((form, form) for form in catalogue.forms()))

    print(f"reel · {song} · {title} · {lang} · {', '.join(themes)} · {wave}", flush=True)
    argv = ["build", "--song", song, "--title", title, "--lang", lang, "--wave", wave]
    for theme in themes:
        argv += ["--theme", theme]
    if options.artist:
        argv += ["--artist", options.artist]
    if options.cover:
        argv += ["--cover", options.cover]
    return reel.main(argv)


def _song() -> str:
    """The song — and ⚠️ **one candidate is not a choice**, so a folder holding a single master asks nothing."""
    songs = library.discover(paths.song_dir())
    if not songs:
        raise reel.Refused(f"no songs in {paths.song_dir()} — drop a master in and run again")
    if len(songs) == 1:
        return songs[0].name
    return _menu_one("song", tuple((song.name, song.name) for song in songs))


def _themes() -> tuple[tuple[str, str], ...]:
    """The renderer's own catalogue, read rather than mirrored — the menu offers exactly what it can draw."""
    return tuple((entry.id, f"{entry.id} — {entry.name}") for entry in catalogue.themes())


def _project() -> str:
    """Ask which product.

    ⚠️ The one question with no flag of its own for the fallback path — hence the positional argument, so a script
    can say `./build reel …` and never see this list at all.
    """
    return _menu_one("project", tuple((pid, f"{name} — {blurb}") for pid, name, blurb in PROJECTS))


def _reject_foreign(project: str, options: argparse.Namespace) -> None:
    """Refuse a flag that belongs to the product nobody chose.

    ⚠️ **Refused rather than ignored.** Dropping `--theme` from a brief run would be silent, and silence is what
    makes an operator believe a flag was applied — true until the day it is not.
    """
    if project == "brief":
        given = [name for name in REEL_ONLY if getattr(options, name)]
        if given:
            flags = ", ".join(f"--{name}" for name in given)
            raise reel.Refused(f"{flags} belongs to the reel — this is a brief run. Drop it, or run `build reel …`")
    elif options.date:
        raise reel.Refused("--date belongs to the brief — this is a reel run. Drop it, or run `build brief …`")


def main(argv: list[str] | None = None) -> int:
    """Parse, ask for whatever a flag did not supply, and hand one product's build its flags."""
    parser = argparse.ArgumentParser(
        prog="build",
        description="One front door for both products: ask which, then hand the answers to `mo` or `sv`.",
    )
    parser.add_argument("project", nargs="?", choices=[pid for pid, _, _ in PROJECTS], help="which product to build")
    # ⚠️ The brief's own spellings, so the muscle memory carries over.
    parser.add_argument("--date", metavar="YYYY-MM-DD", help="the brief's session date — defaults to today")
    parser.add_argument("--lang", nargs="+", help="brief: which editions · reel: bn or en for the caption")
    # ⚠️ The reel's own spellings, likewise.
    parser.add_argument("--song", help="the reel's song, by the name of its file in resource/reel/song/")
    parser.add_argument("--title", help="what the reel shows — never parsed out of a filename")
    parser.add_argument("--theme", action="append", default=[], help="a theme to build; repeat once per theme")
    parser.add_argument("--wave", help="the wave form — one choice, shared by every theme")
    parser.add_argument("--artist", help="the artist, for the reel's upload text only")
    parser.add_argument("--cover", help="the still's artwork, by the name of its image in resource/reel/song/")
    parser.add_argument("--replay", action="store_true", help="reel: re-run the recorded answers, and ask nothing")

    options = parser.parse_args(argv)

    try:
        # ⚠️ Refused **before** the first question, the same discipline the reel's own `_screen` keeps: a menu that
        # asks what it can and then dies on stdin has spent the operator's typing and taught them nothing.
        if not options.project and not reel._may_ask():
            raise reel.Refused(
                "there is no terminal to ask on (stdin is not a tty) — name the product, `build brief` or "
                "`build reel`, or run from a terminal"
            )
        project = options.project or _project()
        _reject_foreign(project, options)
        return _brief(options) if project == "brief" else _reel(options)
    except reel.Refused as refusal:
        print(str(refusal), file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
