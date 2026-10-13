"""Where the reel's folders are — the one seam a test patches.

The nested project owns its own `resource/`, `store/` and `output/`; ⚠️ **the mark does not.** The logo is
the brief's own operator asset, read from the parent's `resource/` through the brief's own loader, so **one
licensed file serves both products** and there is one place to change it (map: reuse before repetition).

⚠️ A named function per folder rather than an inline path, so a test can point the whole tool at a temporary
root without freezing anything else — the habit of the brief's `store.root()`.
"""
from __future__ import annotations

import pathlib


def project_root() -> pathlib.Path:
    """The reel's root — `resource/`, `store/` and `output/` sit under it."""
    return pathlib.Path(__file__).resolve().parents[2]


def repo_root() -> pathlib.Path:
    """The repository holding both products: the brief and the reel."""
    return project_root().parent


def song_dir() -> pathlib.Path:
    """`resource/song/` — the masters, and the optional covers beside them."""
    return project_root() / "resource" / "song"


def mark_dir() -> pathlib.Path:
    """The brief's own `resource/` — the logo the reel draws, reused rather than copied."""
    return repo_root() / "resource"


def shared_remotion() -> pathlib.Path:
    """The brief's `remotion/` — vendored fonts and the seeded PRNG the reel draws with."""
    return repo_root() / "remotion"


def store_dir() -> pathlib.Path:
    """`store/<song>/` — the recorded run that makes a rebuild a rebuild."""
    return project_root() / "store"


def output_dir() -> pathlib.Path:
    """`output/<song>/<theme>/` — the packages."""
    return project_root() / "output"


def public_dir() -> pathlib.Path:
    """Staging for the renderer: the song is copied here for the run and deleted with it."""
    return project_root() / "public"
