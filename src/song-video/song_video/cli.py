"""The `song-video` command line — the conductor (ADR 0002).

One command, by hand (ADR 0004): `sv build`.

⚠️ **The menu is a front end for the record, never the record itself** (issue 04). A song with no record asks its
four questions — song, title, themes, wave form — and writes the answers down; every later run **replays** them.
Asking again would make the second answer the product and the first video unreproducible.

⚠️ **Interactivity is a default, not a trap.** Every question has a flag, so the same run is scriptable, and
`--replay` makes a rebuild a flag rather than a menu.

⚠️ **Nothing expensive happens before the ledger.** This module renders no frame and touches no master: it resolves
the answers, guards the master's digest, records the run, and prints what is about to be built — because the
expensive mistake is an hour of frames spent on a mis-tick, and this costs nothing.
"""
from __future__ import annotations

import argparse
import dataclasses
import pathlib
import sys

from market_overview import logo

from . import caption, catalogue, library, master, package, paths, plan, record, render, seo, sound, stage

#: ⚠️ **Fixed, not asked.** A rate that could change between runs would change how many frames the piece has while
#: still claiming to be "as long as the song" — and the recorded frame count is a contract a rebuild reads.
FPS = 30


class Refused(RuntimeError):
    """The run cannot go ahead, and the reason **is** the answer: printed on stderr, exit 1, nothing written."""


@dataclasses.dataclass(frozen=True)
class Resolved:
    """What this command line resolved to, and what to say about it."""

    #: The pair on disk — the master, and the cover this run resolved to (attached by `--cover`, paired by name, or
    #: none at all). Carried because the render has to stage **the files themselves**, and a record describes a
    #: master rather than pointing at one.
    song: library.Song
    run: record.Run
    #: Whether the answers came from the record rather than from a menu or flags.
    replayed: bool
    #: ⚠️ The ffprobe on **this** machine. What was recorded and what is true today are two different facts, and
    #: a length that moved between them has an explanation worth printing.
    ffprobe: str
    #: ⚠️ **What the master sounds like**, measured on this machine: the stream's shape, its integrated loudness and its
    #: true peak (issue 09). `None` when the toolchain found no audio stream to read — which the ledger *says* rather
    #: than passing over, because "unmeasured" and "silent" are different sentences.
    audio: sound.Audio | None
    #: ⚠️ **The upload text**: the title a search result shows and the description beside it, written into every
    #: package (issue 07's "handable to its own uploader"). Built during the *resolve*, so a title that cannot fit a
    #: search result is a refusal before the ledger rather than a discovery after an hour of frames.
    text: seo.Upload


# ── the run ──────────────────────────────────────────────────────────────────────────────────────────────


def _build(options: argparse.Namespace) -> int:
    """`sv build` — one song in, N reels out. Resolve, guard, record, say what will be built, and build it."""
    try:
        resolved = _resolve(options)
    except (Refused, catalogue.CatalogueError, master.MasterError, record.RecordError) as refusal:
        print(str(refusal), file=sys.stderr)
        return 1

    _ledger(resolved)

    # ⚠️ **Flushed, so the ledger stays above the render.** stdout is block-buffered when it is a pipe while the
    # render's own stream is flushed per line, so without this the first frame's progress would appear *above* the
    # plan it belongs to — and the ledger would look like something printed after the fact.
    sys.stdout.flush()

    try:
        made = _render(resolved)
    except (render.RenderError, logo.LogoError) as failure:
        # ⚠️ A failed theme **fails the run** (issue 07): no summary, no exit zero, and — because every artefact
        # is moved into place only once it is whole — nothing half-written pretending to be a package.
        print(str(failure), file=sys.stderr)
        return 1

    _made(made)
    return 0


def _render(resolved: Resolved) -> list[pathlib.Path]:
    """Stage the song, then **every thumbnail before any video**, then the videos (issues 03, 07, 08).

    ⚠️ **The order is the quality gate.** N one-frame stills cost seconds, so a theme that reads badly is seen and
    killed before an hour of frames is spent on it — and a sporadic browser death, which this toolchain does
    produce, costs seconds here rather than a render.

    ⚠️ The master is **copied**, never moved and never re-encoded: a composition can only fetch from the render
    project's `public/`, and the renderer has to hear the master rather than a step the pipeline introduced.
    """
    staged = stage.copy(resolved.song.master, paths.public_dir())
    cover = stage.copy(resolved.song.cover, paths.public_dir()) if resolved.song.cover else None

    place = render.Stage(
        # ⚠️ The reel's own tree, and **not** `paths.repo_root()`: the render runs there, and `remotion/index.ts`
        # is relative — the parent has a file with the same name, holding the brief's compositions.
        root=render.where(),
        output_dir=paths.output_dir(),
        staged=staged.name,
        cover=cover.name if cover else None,
        seed=resolved.run.master.sha256,
        lang=resolved.run.lang,
        # ⚠️ The operator's own mark, through the brief's loader: one licensed asset, one place that answers the
        # ink-polarity question. `None` when they have not supplied one, which is a supported state.
        mark=logo.load(paths.mark_dir()),
    )

    jobs = plan.jobs(resolved.run)
    # ⚠️ **The upload text is written first, and it is not decoration.** It is the only artefact here that costs nothing
    # and the only one that is *copy*, so a refusal it can cause — a title over the limit, a language with no table —
    # belongs before the first frame. That is the same argument that puts the ledger before the render and the stills
    # before the reels. It also makes each package complete *as* a package: video, still, title, description.
    written = [path for job in jobs for path in _upload_text(place.output_dir, job, resolved.text)]

    stills = [render.thumbnail(place, job) for job in jobs]
    reels = [render.video(place, job) for job in jobs]
    return [*written, *stills, *reels]


def _upload_text(output_dir: pathlib.Path, job: plan.Job, text: seo.Upload) -> list[pathlib.Path]:
    """Write the title and the description beside the reel, and return what was written.

    ⚠️ `utf-8`, and no `ensure_ascii`: the copy is Bengali, and a title file made of `\\u09ac…` escapes would be a file
    that has to be decoded before it can be trusted — the same reason the record is written the way it is. The trailing
    newline on the title is for the tools that read the file a line at a time.
    """
    title_path = package.title_text(output_dir, job)
    description_path = package.description_text(output_dir, job)
    title_path.parent.mkdir(parents=True, exist_ok=True)
    title_path.write_text(text.title + "\n", encoding="utf-8")
    description_path.write_text(text.description, encoding="utf-8")
    return [title_path, description_path]


def _made(made: list[pathlib.Path]) -> None:
    """What is now on disk — printed only once every one of them is whole."""
    print(f"song-video · {len(made)} files")
    for path in made:
        print(f"  {path.stat().st_size / 1024 / 1024:6.2f} MB  {_relative(path)}")


def _resolve(options: argparse.Namespace) -> Resolved:
    """The run this command line describes: replayed from the record, or answered and recorded now."""
    songs = library.discover(paths.song_dir())
    if not songs:
        # ⚠️ **The song is the product** (issue 01): nothing to play means nothing to make, and it is the one
        # absence that is not a supported state.
        raise Refused(f"no songs in {paths.song_dir()} — drop a master in and run again")

    if options.song is not None or len(songs) == 1:
        song = _song(options.song, songs, ask=False)
        if _record_file(song.name).is_file():
            # ⚠️ A recorded song **replays**. The record is the rebuild contract, and re-asking would make the
            # second answer the product.
            return _replay(song, options)
        if options.replay:
            raise Refused(
                f"{song.name} has no record at {_relative(_record_file(song.name))} — --replay rebuilds a "
                f"recorded run, and this song has never been answered"
            )
    elif options.replay:
        raise Refused(
            f"{len(songs)} songs in {paths.song_dir()} and --replay needs one — say which with --song "
            f"({_names(songs)})"
        )

    # ⚠️ The song is resolved **before** the screen. An ambiguous folder is the more specific refusal, and it is
    # the one that can name the songs that could have been chosen.
    song = _song(options.song, songs)
    _screen(options)
    return _answered(song, options)


def _replay(song: library.Song, options: argparse.Namespace) -> Resolved:
    """Rebuild what was recorded.

    ⚠️ **The guard runs before the flags are compared.** Whether the file on disk is the file the record describes
    is the more fundamental question, and a swapped master must be refused whatever the operator typed — the
    recorded title, themes and wave form were approved for a *different* take.
    """
    run = record.load(paths.store_dir(), song.name)
    if not run.lang:
        # ⚠️ A record written before the caption had a language still replays. Empty means *nobody chose*, so the
        # choice is made here — in the conductor, which owns policy — and never in the reader, which does not.
        run = dataclasses.replace(run, lang=caption.language_of(run.title))
    live = master.probe(song.master)
    record.verify(run, live)
    # ⚠️ The recorded cover has to be **here**. A record names an image rather than a place in the folder, so it is
    # looked up in today's folder — and a still whose artwork has gone cannot be rebuilt, which is a refusal rather
    # than a quiet motif. The message carries both ways out: put the file back, or answer the run again.
    cover = library.cover_at(paths.song_dir(), run.cover.name) if run.cover else None
    if run.cover and cover is None:
        raise Refused(
            f'{run.song} was built with the cover "{run.cover.name}", and no image of that name is in '
            f"{paths.song_dir()} — put it back, or remove {_relative(_record_file(run.song))} to answer again"
        )
    if cover is not None:
        # ⚠️ Same filename is not the same image: a swapped cover re-cuts a different still under an approval given
        # for the old art, which is the defect the master's digest exists for, seen through the other input.
        record.verify_cover(run, cover)
    # ⚠️ Measured **after** the guards, so a refused run pays nothing for a diagnostic nobody will read.
    heard = sound.measure(song.master)
    _flags_agree(run, options)
    return Resolved(
        song=dataclasses.replace(song, cover=cover),
        run=run,
        replayed=True,
        ffprobe=live.toolchain,
        audio=heard,
        text=_text(run),
    )


def _answered(song: library.Song, options: argparse.Namespace) -> Resolved:
    """Ask whatever the flags did not answer, and write the answers down.

    ⚠️ The probe comes **before** the questions: a master that cannot be measured is a refusal, and it is better to
    say so than to collect four answers for a run that cannot happen.
    """
    live = master.probe(song.master)
    # ⚠️ In the map's order — song, title, themes, wave form — so the menu is a sequence rather than a set.
    title = _title(options, song)
    cover = _pick_cover(options, song)
    run = record.Run(
        song=song.name,
        title=title,
        # ⚠️ For the **upload text** and nothing else: it is never drawn, and it is never read out of the file's name
        # or its tags (issue 04). Absent means absent, so the description drops the line rather than guessing.
        artist=options.artist or "",
        # ⚠️ Decided *after* the title exists and never asked for: the caption follows the script the operator
        # typed, and `--lang` overrides. A Bengali title over an English caption reads like a template.
        lang=_lang(options, title),
        cover=record.cover_of(cover) if cover else None,
        themes=_themes(options),
        wave=_wave(options),
        fps=FPS,
        duration_seconds=live.duration_seconds,
        master=record.Master(
            name=live.path.name,
            sha256=live.sha256,
            bytes=live.path.stat().st_size,
        ),
        toolchain=record.Toolchain(ffprobe=live.toolchain),
    )
    # ⚠️ Built **before the record is written**, so a title that will not fit a search result is a refusal that leaves
    # the store exactly as it was — the same promise `unknown theme "sparkle"` keeps.
    text = _text(run)
    record.save(paths.store_dir(), run)
    # ⚠️ The **pair the render stages**, and not always the pair the folder offers: an explicit `--cover` names an
    # image whose stem answers to no master, so the render is handed the run's own answer rather than the default.
    # ⚠️ And what the master *sounds* like — measured once, here, rather than assumed in the ledger (issue 09).
    return Resolved(
        song=dataclasses.replace(song, cover=cover),
        run=run,
        replayed=False,
        ffprobe=live.toolchain,
        audio=sound.measure(song.master),
        text=text,
    )


# ── the four questions, flags first, menu second ─────────────────────────────────────────────────────────


def _song(name: str | None, songs: list[library.Song], *, ask: bool = True) -> library.Song:
    """Which song, from the ones that are there.

    ⚠️ An ambiguous folder is **refused**, not guessed: a run that picked the alphabetically first song would
    render the wrong one under the right flags, and every file it wrote would look correct.
    """
    if name is not None:
        for song in songs:
            if song.name == name:
                return song
        raise Refused(f"{name!r} is not in {paths.song_dir()} — the songs there are {_names(songs)}")

    if len(songs) == 1:
        return songs[0]

    if not ask or not _may_ask():
        raise Refused(f"{len(songs)} songs in {paths.song_dir()} — say which one with --song ({_names(songs)})")

    picked = _menu_one("song", [(song.name, song.name) for song in songs])
    return next(song for song in songs if song.name == picked)


def _title(options: argparse.Namespace, song: library.Song) -> str:
    """What the video shows. ⚠️ Typed, never parsed from a filename or an ID3 tag (issue 04)."""
    typed = options.title if options.title is not None else _menu_line("title — what the video shows: ")
    typed = typed.strip()
    if not typed:
        raise Refused("an empty title shows nothing — the title is typed, because it is never parsed from a file")
    return typed


def _themes(options: argparse.Namespace) -> tuple[str, ...]:
    """The themes to build — one video each (issue 07)."""
    entries = catalogue.themes()
    chosen = [(entry.id, entry.name) for entry in entries]
    ticked = tuple(options.theme) if options.theme else _menu_many("theme", chosen)
    _known("theme", ticked, [entry.id for entry in entries])
    return ticked


def _lang(options: argparse.Namespace, title: str) -> str:
    """What the still's caption is written in: the flag, else the title's own script.

    ⚠️ **A default, not a rule.** The reel does not know what language a song is in — it knows what script the
    operator typed. So the caption follows the title, `--lang` settles it when the title cannot (an instrumental, a
    Latin transliteration), and the answer is recorded either way.
    """
    if options.lang is None:
        return caption.language_of(title)
    if options.lang not in caption.LANGUAGES:
        # ⚠️ Quoted like every other refusal in this file (`unknown theme "sparkle"`), not with `repr`'s single
        # quotes — one convention for the messages an operator reads.
        raise Refused(f'unknown language "{options.lang}" — the languages are {", ".join(caption.LANGUAGES)}')
    return options.lang


def _text(run: record.Run) -> seo.Upload:
    """The upload text for this run — built **here**, during the resolve, and never during the render.

    ⚠️ **Because it is published, and because it is cheap.** A title longer than a search result shows is a title to
    shorten, and finding that out in the ledger — the screen whose whole purpose is to make a mis-tick cost seconds —
    is the difference between a copy fix and an hour of frames spent on a reel nobody can title. ⚠️ It is also a
    *refusal* rather than a truncation: silently trimming the artist's name off the end of their own song's title is
    the kind of politeness nobody forgives.
    """
    try:
        return seo.upload_for(run.title, lang=run.lang, seconds=run.duration_seconds, artist=run.artist)
    except seo.SeoError as refusal:
        # ⚠️ Translated into the conductor's own refusal, so the reason is printed on stderr with exit 1 like every
        # other one — and so nothing downstream has to know that `seo` has an error type of its own.
        raise Refused(str(refusal)) from refusal


def _pick_cover(options: argparse.Namespace, song: library.Song) -> pathlib.Path | None:
    """Which image the frame is built around: the flag's, the folder's, or a question.

    ⚠️ **The pairing rule is a *name* rule, and it leaves one case it cannot serve.** A cover belongs beside the
    master whose basename it shares — that is what makes `resource/reel/song/` an interface rather than a folder — so an
    image for a *different* song (a concert poster, artwork for a master not supplied yet) answers to no master, and
    the run drew the theme's motif over it while naming the file only in a ledger warning.

    ⚠️ **The operator's rule, in their words: use the image, and ask when there is a choice.** So the candidates are
    taken in order of how settled they are —

    | | |
    |---|---|
    | `--cover` | an answer, used as given — and refused when it names no image here |
    | the paired image | the folder's own answer; a cover sharing the master's basename needs no question |
    | **one** loose image | taken. One candidate is not a choice, exactly as one song needs no menu |
    | several loose images | **asked**, with *none* among the answers — a poster is not a guess, it is a question |
    | no images | no cover: a supported state, and the still draws the theme's motif (issue 08) |

    ⚠️ **Whichever it was, it is recorded** (issue 04), digest and all, so a replay uses the same artwork without
    asking and a swapped image is refused. A run with no terminal and several candidates **refuses**, naming them
    and `--cover`, rather than picking one — which is how an ambiguous folder of *songs* is refused too.
    """
    if options.cover is not None:
        if pathlib.Path(options.cover).name != options.cover:
            raise Refused(
                f"--cover takes the image's name, not a path ({options.cover}) — the images in {paths.song_dir()} "
                f"are {_images()}"
            )
        named = library.cover_at(paths.song_dir(), options.cover)
        if named is None:
            raise Refused(f'no image "{options.cover}" in {paths.song_dir()} — the images there are {_images()}')
        return named

    if song.cover is not None:
        return song.cover

    loose = library.orphans(paths.song_dir())
    if not loose:
        return None
    if len(loose) == 1:
        return loose[0]
    if not _may_ask():
        raise Refused(
            f"{len(loose)} images in {paths.song_dir()} pair with no master, so choosing one is a decision rather "
            f"than a default — say which one rides {song.name} with --cover ({_images()})"
        )

    # ⚠️ `""` is the *none* answer, and it is an answer: the theme's motif is a designed state, not a hole, so a
    # folder full of posters must not trap the operator into using one of them.
    chosen = _menu_one("cover", [(path.name, path.name) for path in loose] + [("", "— none: the theme's motif")])
    return library.cover_at(paths.song_dir(), chosen) if chosen else None


def _images() -> str:
    """Every image in the folder, for a refusal whose job is to end in something the operator can type."""
    found = library.images(paths.song_dir())
    return ", ".join(path.name for path in found) if found else "none — there is no image in that folder at all"


def _wave(options: argparse.Namespace) -> str:
    """The wave form — **one** choice, shared by every theme in the run (issue 06)."""
    forms = catalogue.forms()
    chosen = options.wave if options.wave is not None else _menu_one("wave form", [(form, form) for form in forms])
    _known("wave form", (chosen,), list(forms))
    return chosen


def _known(kind: str, given: tuple[str, ...], available: list[str]) -> None:
    """Refuse an id the renderer cannot draw, in the renderer's own words.

    ⚠️ **A refusal rather than a fallback**, for the reason `themeFor` gives on the other side of the seam: a reel
    in a theme nobody chose is indistinguishable from a reel in the one they did.
    """
    unknown = [value for value in given if value not in available]
    if unknown:
        named = ", ".join(f'"{value}"' for value in unknown)
        raise Refused(f"unknown {kind} {named} — the catalogue is {', '.join(available)}")


def _screen(options: argparse.Namespace) -> None:
    """Refuse a menu nobody can answer — **once**, listing everything that would have answered it.

    ⚠️ Checked before the first question, not at the first question. A menu that asks three of its four questions
    and then dies because stdin was never a terminal has spent the operator's typing and taught them nothing.

    ⚠️ The song is deliberately **not** in this list: it has been resolved by now, and its own refusal names the
    songs, which is more use than naming a flag.
    """
    if _may_ask():
        return

    missing = [
        flag
        for flag, supplied in (
            ("--title", options.title is not None),
            ("--theme", bool(options.theme)),
            ("--wave", options.wave is not None),
        )
        if not supplied
    ]
    if missing:
        raise Refused(
            f"there is no terminal to ask on (stdin is not a tty), and the run is missing {', '.join(missing)} "
            f"— pass them, or run from a terminal"
        )


def _flags_agree(run: record.Run, options: argparse.Namespace) -> None:
    """Refuse a flag that **disagrees** with the record, rather than obeying it.

    ⚠️ The record is the take somebody approved. A flag that quietly overwrote it would make the first video
    unreproducible and the second one undocumented — the same defect seen from both ends.
    """
    disagreements = [
        (flag, given, recorded)
        for flag, given, recorded in (
            ("--title", options.title, run.title),
            ("--lang", options.lang, run.lang),
            # ⚠️ The artist is part of what was published, so it is replayed rather than re-answered — and it is held
            # as a plain string, where `""` is *nobody said* and therefore never a disagreement with an absent flag.
            ("--artist", options.artist or None, run.artist or None),
            # ⚠️ The **name**, not the digest: a flag says which image to attach, and whether it is the image the
            # record approved is `verify_cover`'s question, asked above and answered with both digests.
            ("--cover", options.cover, run.cover.name if run.cover else None),
            ("--theme", tuple(options.theme) if options.theme else None, run.themes),
            ("--wave", options.wave, run.wave),
        )
        if given is not None and given != recorded
    ]
    if not disagreements:
        return

    flag, given, recorded = disagreements[0]
    raise Refused(
        f"{flag} says {given!r} and {run.song}'s record says {recorded!r} — the run replays what was approved, "
        f"so remove {_relative(_record_file(run.song))} to answer again"
    )


# ── the menu ────────────────────────────────────────────────────────────────────────────────────────────
# ⚠️ Prompts go to **stderr**, so stdout stays the ledger: `sv build | tee ledger.txt` captures the answers the run
# decided on, not the questions it asked.


def _may_ask() -> bool:
    """Whether there is anybody to ask."""
    return sys.stdin.isatty()


def _menu_line(question: str) -> str:
    """One free-text answer."""
    print(f"  {question}", end="", file=sys.stderr, flush=True)
    return input()


def _menu_one(kind: str, choices: list[tuple[str, str]]) -> str:
    """One choice out of a numbered list.

    ⚠️ **Asked once.** An answer that is not one of the numbers is a refusal naming what the numbers are — the menu
    is a front end, and a front end that argues is worse than a message that says what to type.
    """
    _show(kind, choices)
    return _pick(kind, _menu_line(f"{kind} — pick one (1-{len(choices)}): "), choices)


def _menu_many(kind: str, choices: list[tuple[str, str]]) -> tuple[str, ...]:
    """Several choices out of a numbered list, comma-separated."""
    _show(f"{kind}s", choices)
    return _tick(kind, _menu_line(f"{kind}s — tick one or more (1,3): "), choices)


def _show(kind: str, choices: list[tuple[str, str]]) -> None:
    print(f"  {kind}", file=sys.stderr)
    for number, (_, label) in enumerate(choices, start=1):
        print(f"    {number}  {label}", file=sys.stderr)


def _number(kind: str, token: str, count: int) -> int:
    """A typed number, as a number — or a refusal that says what the numbers are."""
    typed = token.strip()
    if not typed.isdigit() or not 1 <= int(typed) <= count:
        raise Refused(f"{kind} {typed!r} is not one of the numbers 1-{count}")
    return int(typed)


def _pick(kind: str, typed: str, choices: list[tuple[str, str]]) -> str:
    return choices[_number(kind, typed, len(choices)) - 1][0]


def _tick(kind: str, typed: str, choices: list[tuple[str, str]]) -> tuple[str, ...]:
    """Ticked numbers, as ids **in catalogue order** — never in the order they were typed.

    ⚠️ The answer is a *set* of themes and the recorded order is the build order, so `1,3` and `3,1` have to
    produce the same record: otherwise the same run rebuilds differently depending on which number was typed first.
    """
    numbers = {_number(kind, token, len(choices)) for token in typed.split(",") if token.strip()}
    if not numbers:
        raise Refused(f"nothing ticked — a run with no {kind} makes nothing")
    return tuple(choices[number - 1][0] for number in sorted(numbers))


# ── the ledger ──────────────────────────────────────────────────────────────────────────────────────────


def _ledger(resolved: Resolved) -> None:
    """What is about to be built, and by which toolchain — printed before the first expensive thing."""
    run = resolved.run
    how = "replayed from" if resolved.replayed else "recorded to"
    print(f"song-video · {run.song} ({how} {_relative(_record_file(run.song))})")
    print(f"  title    {run.title}")
    # ⚠️ **The title a search result will show** — the one line of this screen that is *published*, and a different
    # string from the one above it. Printed beside the internal title because only one of the two is what a stranger
    # reads first, and `--artist` is what puts a name in it.
    print(f"  upload   {resolved.text.title}")
    # ⚠️ The language and the *number* — never the word: "সংগীত" lives in the render layer's label table, so the
    # ledger shows the facts without inventing copy of its own.
    print(f"  caption  {run.lang} · {caption.duration_at(run.duration_seconds, lang=run.lang)}")
    print(f"  master   {run.master.name}  {run.master.bytes} bytes  sha256 …{run.master.sha256[-12:]}")
    # ⚠️ **What the master sounds like, measured rather than assumed** — the one line of this screen that is about the
    # *music* rather than about the plumbing (issue 09). The shape (codec, rate, channel count) is what the delivery is
    # then held to; the loudness and the true peak are the two facts nobody can hear by looking, and a lossy or
    # clipping master is a **ceiling** and a **risk** respectively — never something this pipeline quietly repairs.
    if resolved.audio is None:
        print("  audio    — unmeasured: the toolchain found no audio stream to read")
    else:
        print(f"  audio    {resolved.audio.spoken()}")
        for complaint in resolved.audio.complaints():
            print(f"  ⚠️ {complaint}")
    # ⚠️ **The cover, present or absent, on every run.** The still's art panel is the operator's own image when
    # there is one and the theme's motif when there is not — and that difference cannot be seen in this screen,
    # which is why the absence is printed rather than passed over. "No cover" is a supported state; an
    # *unnoticed* no-cover is what put a complaint about a missing image in front of this line.
    cover = resolved.song.cover
    known = run.cover
    if cover is None:
        print("  cover    — none: no image here shares the master's name")
    else:
        # ⚠️ The remembered digest, printed exactly as the master's is: on a rebuild elsewhere it is the value a
        # different image under the same filename is caught by.
        remembered = f"{known.bytes} bytes  sha256 …{known.sha256[-12:]}" if known else "not recorded"
        print(f"  cover    {cover.name}  {remembered}")
    # ⚠️ And an image that pairs with **nothing** is named, not silently skipped — with the way to attach it, which
    # is the whole of the fix. The rule is that a cover shares its master's basename, so a file that pairs with no
    # master is not a cover *yet*: the operator's own artwork used to sit in this folder while the still drew the
    # theme's motif over it and nothing anywhere said why. Printed as-is — a filename with spaces or Bengali in it
    # is theirs, not ours to prettify.
    for orphan in library.orphans(paths.song_dir()):
        if cover is not None and orphan.name == cover.name:
            continue  # this run attached it deliberately — the cover line above is where it is accounted for
        print(f'  ⚠️ cover {orphan.name} pairs with no master — attach it with --cover "{orphan.name}"')
    # ⚠️ Printed even when it matches, because the *recorded* value is what a rebuild on another machine is
    # compared against — and the mismatch is the sentence that explains why a length moved.
    stale = "" if run.toolchain.ffprobe in ("", resolved.ffprobe) else f"  ⚠️ the record names {run.toolchain.ffprobe}"
    print(f"  measured {resolved.ffprobe}{stale}")
    print(f"  length   {run.duration_seconds:.3f} s → {master.frames(run.duration_seconds, run.fps)} frames "
          f"at {run.fps} fps")
    print(f"  wave     {run.wave} (shared by all {len(run.themes)})")
    for job in plan.jobs(run):
        print(f"  theme    {job.theme:<10} → {_relative(package.reel(paths.output_dir(), job))}")


# ── paths and names ─────────────────────────────────────────────────────────────────────────────────────


def _record_file(song: str) -> pathlib.Path:
    """The record this song would replay."""
    return record.dir_for(paths.store_dir(), song) / record.RUN


def _relative(path: pathlib.Path) -> str:
    """A path as the operator would type it — relative to the project, or to the data root, when it is inside one.

    ⚠️ **Two roots, because the reel's paths now span both.** The recorded run and the staging are in the project;
    the packages are under the data root, outside the repository. Trying only the project would print every
    delivered reel as an absolute `/Users/…` path — honest, and longer than the ledger needs.
    """
    for root in (paths.project_root(), paths.data_root()):
        try:
            return str(path.relative_to(root))
        except ValueError:
            continue
    return str(path)


def _names(songs: list[library.Song]) -> str:
    return ", ".join(song.name for song in songs)







def main(argv: list[str] | None = None) -> int:
    """Parse the command line and run one command. Returns the process exit status."""
    parser = argparse.ArgumentParser(prog="sv", description="Builds the Song Reel.")
    commands = parser.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build", help="build the reel(s) for one song")
    build.add_argument("--song", help="the song to build, by the name of its file in resource/reel/song/")
    build.add_argument("--title", help="what the video shows — never parsed from a filename or a tag")
    build.add_argument("--theme", action="append", default=[], help="a theme to build; repeat once per theme")
    build.add_argument("--wave", help="the wave form — one choice, shared by every theme in the run")
    build.add_argument("--lang", help="the still's caption script, bn or en (default: the title's own script)")
    build.add_argument(
        "--artist",
        help="the artist, for the upload text only — never drawn, and never read out of a file",
    )
    build.add_argument(
        "--cover",
        help="the still's artwork, by the name of its image in resource/reel/song/ "
        "(default: the image sharing the master's name)",
    )
    build.add_argument("--replay", action="store_true", help="re-run the recorded answers, and ask nothing")
    build.set_defaults(run=_build)

    options = parser.parse_args(argv)
    return options.run(options)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
