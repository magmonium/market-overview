"""The recorded run — `store/<song>/run.json` (issue 04).

⚠️ **This file is an interface, not a cache.** It is committed, a human reads it to see what was built, and the
next run **replays it instead of asking the menu again** — which is the only thing that makes a rebuild a
rebuild rather than a second opinion. So the shape of the JSON is a contract, and the file is kept legible
(`indent=2`, `ensure_ascii=False`: a Bengali title stays a Bengali title).

⚠️ **The write is atomic**, in the brief's `store.py` habit: a temporary file in the destination, flushed,
`fsync`ed, then `os.replace`d over the target. A half-written record is worse than a missing one, because it
*looks* like something a run can be rebuilt from.

⚠️ **The toolchain is recorded but never guarded.** Provenance and identity are different questions: which ffprobe
measured the piece is worth writing down, and a *different* ffprobe is a legitimate rebuild, while a different
master is not ([the run menu](../../../ideas/.scratch/song-video/issues/04-the-run-menu.md)).
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import pathlib
import tempfile
from typing import Any

from . import master

#: The record's filename inside `store/<song>/`.
RUN = "run.json"


@dataclasses.dataclass(frozen=True)
class Master:
    """The supplied file as the record remembers it.

    ⚠️ **Not `master.Master`.** That one is a *live measurement* — a path, a duration, a digest read off the
    disk a moment ago. This one is what was **written down**: the file's name, the digest the guard checks,
    and its size. Confusing the two would mean comparing a measurement against itself.
    """

    name: str
    sha256: str
    bytes: int


@dataclasses.dataclass(frozen=True)
class Toolchain:
    """What measured the master.

    ⚠️ **Provenance, not a guard.** A rebuild on another machine, with another ffprobe, is a legitimate rebuild —
    a *different master* is not, and that is the digest's job. So this is recorded and printed, and a mismatch is
    never a refusal: it is the sentence that explains why a length moved.
    """

    ffprobe: str


@dataclasses.dataclass(frozen=True)
class Cover:
    """The supplied image as the record remembers it — `Master`'s twin, and for the same reason.

    ⚠️ **A cover is not a folder fact once it is in a still.** The artwork is part of the delivery, so a run
    records *which* image went in, and its digest with it: a different image at the same filename would re-cut a
    different still under the same approved title. Without the digest, swapping the art and rebuilding would be
    indistinguishable from a faithful rebuild — the one failure nothing else in the pipeline can see.
    """

    name: str
    sha256: str
    bytes: int


@dataclasses.dataclass(frozen=True)
class Run:
    """One run's answers, as they will be replayed.

    The song and the title are the two different things the map is emphatic about: `song` is an **id** (a
    folder name), `title` is the string a human typed and the video will display.
    """

    song: str
    title: str
    #: ⚠️ **The caption's script**, `bn` or `en` — a choice like the others, so it is recorded rather than
    #: re-derived: a rebuild whose caption changed language would not be the delivery somebody approved.
    lang: str
    #: ⚠️ Which image rides the still's art panel, held as a **name inside `resource/reel/song/`** rather than a path:
    #: this file is committed and read on other machines, and an absolute path to somebody's desktop is not a
    #: rebuild. `None` is a supported state — the still draws the theme's motif instead (issue 08).
    cover: Cover | None
    themes: tuple[str, ...]
    wave: str
    fps: int
    duration_seconds: float
    master: Master
    toolchain: Toolchain
    #: ⚠️ The artist, **for the upload text only** — never drawn, and never parsed from a filename or a tag (issue 04's
    #: rule). Empty means nobody said, which is why it is defaulted rather than asked for: a song with no named artist is
    #: a supported state, and the description simply omits the line instead of leaving a placeholder to edit.
    artist: str = ""


def dir_for(store_dir: pathlib.Path, song: str) -> pathlib.Path:
    """`store/<song>/` — one folder per song, not per date: a song has no date."""
    return store_dir / song


def _document(run: Run) -> dict[str, Any]:
    """The run as it goes on the wire. Explicit, so a field rename cannot silently change the file."""
    return {
        "song": run.song,
        "title": run.title,
        "artist": run.artist,
        "lang": run.lang,
        "cover": None
        if run.cover is None
        else {"name": run.cover.name, "sha256": run.cover.sha256, "bytes": run.cover.bytes},
        "themes": list(run.themes),
        "wave": run.wave,
        "fps": run.fps,
        "duration_seconds": run.duration_seconds,
        "master": {
            "name": run.master.name,
            "sha256": run.master.sha256,
            "bytes": run.master.bytes,
        },
        "toolchain": {"ffprobe": run.toolchain.ffprobe},
    }


def cover_of(path: pathlib.Path) -> Cover:
    """Describe an image for the record, digest and all — `master.probe`'s job, for a file that has no length.

    ⚠️ Hashed **here** rather than trusted from the caller, so the one place that decides what the digest covers
    is the one place that writes it down.
    """
    return Cover(name=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size)


def save(store_dir: pathlib.Path, run: Run) -> pathlib.Path:
    """Write the record atomically and return its path."""
    target = dir_for(store_dir, run.song)
    target.mkdir(parents=True, exist_ok=True)
    path = target / RUN

    handle, temporary = tempfile.mkstemp(dir=target, prefix=".run-", suffix=".json")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as fh:
            json.dump(_document(run), fh, indent=2, ensure_ascii=False)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temporary, path)
    except BaseException:
        pathlib.Path(temporary).unlink(missing_ok=True)
        raise
    return path


def load(store_dir: pathlib.Path, song: str) -> Run:
    """Read a record back — the entry point for a replay.

    ⚠️ **A missing `toolchain` is not a malformed record.** It is *provenance*, and a record written before the
    field existed still describes a run somebody approved: refusing to replay it would throw away the answers to
    protect a diagnostic. The digest is the field that must be there, and a record without **it** fails loudly,
    which is exactly what a `KeyError` on the line below does.

    ⚠️ `lang` is read the same way, and an absent one comes back **empty** rather than guessed: which language a
    caption is written in is a *choice*, and this module has no business making it. The conductor fills a missing
    value from the title's own script, which is where that policy belongs.

    ⚠️ **`cover` likewise, and it comes back `None` rather than re-paired.** A record written before the artwork was
    recorded rebuilds with the theme's motif, not with whichever image happens to share the master's name today:
    the pairing is the folder's *offer*, and a still whose art was never written down is not a still this record can
    rebuild. Answering the run again is one command — remove `store/<song>/run.json` — and the new record names it.
    """
    document = json.loads((dir_for(store_dir, song) / RUN).read_text(encoding="utf-8"))
    remembered = document.get("cover")
    return Run(
        song=document["song"],
        title=document["title"],
        lang=document.get("lang", ""),
        cover=Cover(name=remembered["name"], sha256=remembered["sha256"], bytes=int(remembered["bytes"]))
        if remembered
        else None,
        themes=tuple(document["themes"]),
        wave=document["wave"],
        fps=int(document["fps"]),
        duration_seconds=float(document["duration_seconds"]),
        master=Master(
            name=document["master"]["name"],
            sha256=document["master"]["sha256"],
            bytes=int(document["master"]["bytes"]),
        ),
        toolchain=Toolchain(ffprobe=document.get("toolchain", {}).get("ffprobe", "")),
        artist=document.get("artist", ""),
    )


class RecordError(RuntimeError):
    """The file on disk is not the file the record describes, so the run stops rather than re-cutting."""


def verify(run: Run, live: master.Master) -> None:
    """Refuse unless the master on disk is the master the record describes.

    ⚠️ **The digest is the identity; the name is only the explanation.** A file that was renamed but not
    changed is still the same master, so the check is the digest alone — and the message names both files,
    because "something changed" is not a refusal anybody can act on.

    ⚠️ **This is why the digest is recorded at all.** Without it, a swapped master would be silently re-cut
    under a title and a theme list that were approved for a *different* take — the one failure mode that no
    other check in the pipeline can see, because every other artefact would be internally consistent.
    """
    if live.sha256 == run.master.sha256:
        return

    raise RecordError(
        f"{live.path.name} has changed since {run.song} was recorded: the record describes "
        f"{run.master.name} (…{run.master.sha256[-12:]}), and the file on disk is …{live.sha256[-12:]}. "
        f"The recorded title, themes and wave form describe the take that was approved, so this run stops "
        f"rather than re-cutting it under that name."
    )


def verify_cover(run: Run, cover: pathlib.Path) -> None:
    """Refuse unless the image on disk is the image the record describes — [`verify`](#verify)'s twin.

    ⚠️ **A still is a delivery and its artwork is part of it.** A different image under the same filename would be
    re-cut under an approval given for different art, and silently, because the name — the one thing a person
    checks — is unchanged. That is a swapped master seen through the other input, so it gets the other input's
    guard.

    ⚠️ A **missing** image is not this function's business: the conductor asks the folder for the recorded name and
    refuses in the folder's words when it is gone (naming `--cover`, since that is how such an image got there).
    """
    if run.cover is None or not cover.is_file():
        return
    digest = hashlib.sha256(cover.read_bytes()).hexdigest()
    if digest == run.cover.sha256:
        return

    raise RecordError(
        f"{cover.name} is not the image {run.song} was recorded with: the record describes "
        f"…{run.cover.sha256[-12:]} and the file on disk is …{digest[-12:]}. The still's artwork was approved as it "
        f"stood, so this run stops rather than drawing different art under the same name."
    )
