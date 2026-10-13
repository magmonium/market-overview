"""What is in `resource/song/` — the input side (map ticket 01).

One song is a **pair**: a master, and the optional cover sharing its basename. The folder *is* the interface
— no manifest, no index, no sidecar JSON, so adding a song is dropping a file in.

⚠️ **Discovery only.** The pipeline accepts **any** format the toolchain reads (issue 01); these suffix lists
exist so the menu can tell a song from a stray file, and for nothing else. They are **orders, first match
wins**, in the brief's `MUSIC_NAMES` habit: a folder holding two encodes of one song gets the lossless one as
the master, and the choice never depends on filesystem order.
"""
from __future__ import annotations

import dataclasses
import pathlib

#: Preference order for the **master**. Lossless first, because a re-encode of a lossy file carries its
#: artefacts along with its music — the same reason the brief prefers a lossless bed.
AUDIO_SUFFIXES: tuple[str, ...] = (
    ".wav",
    ".flac",
    ".aiff",
    ".aif",
    ".m4a",
    ".mp3",
    ".aac",
    ".ogg",
    ".opus",
    ".webm",
)

#: The cover, beside the master.
IMAGE_SUFFIXES: tuple[str, ...] = (".jpg", ".jpeg", ".png", ".webp")


@dataclasses.dataclass(frozen=True)
class Song:
    """One song's pair.

    ⚠️ `name` is an **id, not a title**: it is the menu entry, the `store/<name>/` folder and the `<song>`
    segment of every output filename. Nothing displays it — the title is typed at run time (issue 04).
    """

    name: str
    master: pathlib.Path
    cover: pathlib.Path | None = None


def _first(paths: list[pathlib.Path], suffixes: tuple[str, ...]) -> pathlib.Path | None:
    """The first candidate matching the *earliest* suffix, or `None`.

    ⚠️ Iterates the suffixes, not the files, so the answer is a property of the preference order rather than
    of the order the filesystem happened to return.
    """
    for suffix in suffixes:
        for path in sorted(paths):
            if path.suffix.lower() == suffix:
                return path
    return None


def images(song_dir: pathlib.Path) -> list[pathlib.Path]:
    """Every image in `song_dir`, in a stable order — what a cover **can** be.

    ⚠️ **One place decides what an image is** — the suffixes, the hidden files, the order — so the pairing rule
    and the explicit one (`cover_at`) can never disagree about which files they are disagreeing about.
    """
    if not song_dir.is_dir():
        return []
    return [
        path
        for path in sorted(song_dir.iterdir())
        if path.is_file() and not path.name.startswith(".") and path.suffix.lower() in IMAGE_SUFFIXES
    ]


def cover_at(song_dir: pathlib.Path, name: str) -> pathlib.Path | None:
    """The image **named** `name` in `song_dir` — or `None`, if that name is not an image there.

    ⚠️ **The explicit half of the pairing rule**, and everything `sv build --cover` does. A cover shares the
    basename of the master it belongs to, which is what lets a song be added by dropping two files in — and it is
    also why an image no master answers to is not a cover for anything: with two masters in the folder a loose
    image belongs to neither, and a *guessed* pairing would be a pairing nobody chose.

    The operator can still choose it, by name, here. That is an answer rather than an inference, so it is recorded
    with the rest of them ([issue 04](../../../ideas/.scratch/song-video/issues/04-the-run-menu.md)) rather than
    re-derived from whichever files happen to be in the folder when the reel is rebuilt.
    """
    wanted = song_dir / name
    # ⚠️ `name` may carry a path separator, in which case it is a path rather than a name in this folder — and
    # `song_dir / "a/b.png"` is a different file, which this function must never resolve to.
    return wanted if wanted in images(song_dir) else None


def orphans(song_dir: pathlib.Path) -> list[pathlib.Path]:
    """Every image in `song_dir` whose name **no master answers to**, in a stable order.

    ⚠️ **Reported, never guessed at.** A cover shares its master's basename — that is what makes this folder an
    interface rather than a folder — so an image no master answers to is not a cover for anything, and with two
    masters here a loose image belongs to neither. The rule stands; the **silence** did not: an image that paired
    with nothing used to be dropped without a word, the still drew the theme's motif instead, and nothing anywhere
    said why. One run of that is what this function exists for.
    """
    paired = {song.name for song in discover(song_dir)}
    # ⚠️ The **stem**, which is what the pairing rule compares: `beshorom.mp3` beside `beshorom.png` is one song,
    # and the cover's format is never the master's business.
    return [path for path in images(song_dir) if path.stem not in paired]


def discover(song_dir: pathlib.Path) -> list[Song]:
    """Every song in `song_dir`, in a stable order.

    An absent folder returns an empty list, exactly like an empty one, so a fresh clone refuses with the same
    reason as a folder somebody emptied. ⚠️ **The song is the product**: nothing to play means nothing to
    make, and this is the one absence that is *not* a supported state (issue 01).

    A cover with no master is **not** a song, so it is skipped rather than reported as one with no audio — it is
    named by [`orphans`](orphans), which is the run's chance to say why it drew no image.
    """
    if not song_dir.is_dir():
        return []

    grouped: dict[str, list[pathlib.Path]] = {}
    for path in song_dir.iterdir():
        if not path.is_file() or path.name.startswith("."):
            continue  # `.DS_Store` and friends are not songs
        suffix = path.suffix.lower()
        if suffix in AUDIO_SUFFIXES or suffix in IMAGE_SUFFIXES:
            grouped.setdefault(path.stem, []).append(path)

    songs: list[Song] = []
    for name in sorted(grouped):
        master = _first(grouped[name], AUDIO_SUFFIXES)
        if master is None:
            continue  # a bare cover in the folder is silently not a song
        songs.append(Song(name=name, master=master, cover=_first(grouped[name], IMAGE_SUFFIXES)))
    return songs

