"""Where a job's files land — the naming contract (map issues 04 and 07).

⚠️ **Every filename carries song *and* theme.** A run produces N videos of **one** song, so once two files leave
their folders the theme is the only thing telling them apart — the folder is a convenience, the name is the
identity ([the package](../../../ideas/.scratch/song-video/issues/07-output-package.md)).

⚠️ **The names live here, once.** The ledger prints them before anything expensive starts and the render writes
them; a pattern known in two places is a pattern that gets changed in one of them.
"""
from __future__ import annotations

import pathlib

from . import plan

#: The reel. The product's name, not the tool's — the artefact is the Song Reel.
REEL = "song-reel-{song}-{theme}.mp4"

#: The thumbnail, beside the reel. ⚠️ A `.jpg` of the *name*, not of the reel: an uploader pairs the two by
#: reading one folder, and the pair never has to be worked out from a timestamp.
THUMBNAIL = "thumbnail-{song}-{theme}.jpg"

#: ⚠️ **The upload text, and it is about the *song*, not the theme** — the same two files land in every theme's folder
#: because the package's contract is "hand this folder to its own uploader", and an uploader needs a title and a
#: description as much as it needs a video and a still.
TITLE = "title-{song}-{theme}.txt"
DESCRIPTION = "description-{song}-{theme}.txt"


def dir_for(output_dir: pathlib.Path, job: plan.Job) -> pathlib.Path:
    """`output/reel/<song>/<theme>/` — **one package per theme**, handable to its own uploader."""
    return output_dir / job.song / job.theme


def title_text(output_dir: pathlib.Path, job: plan.Job) -> pathlib.Path:
    """Where the run writes the SEO title — beside the reel it describes."""
    return dir_for(output_dir, job) / TITLE.format(song=job.song, theme=job.theme)


def description_text(output_dir: pathlib.Path, job: plan.Job) -> pathlib.Path:
    """Where the run writes the description — the other half of what an uploader asks for."""
    return dir_for(output_dir, job) / DESCRIPTION.format(song=job.song, theme=job.theme)


def reel(output_dir: pathlib.Path, job: plan.Job) -> pathlib.Path:
    """Where this job's video lands."""
    return dir_for(output_dir, job) / REEL.format(song=job.song, theme=job.theme)


def thumbnail(output_dir: pathlib.Path, job: plan.Job) -> pathlib.Path:
    """Where this job's thumbnail lands — in the same folder as the reel it belongs to."""
    return dir_for(output_dir, job) / THUMBNAIL.format(song=job.song, theme=job.theme)
