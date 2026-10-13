"""The master, placed where a composition can fetch it — `public/` (map issue 03).

A composition can only serve assets from the render project's `public/` folder, so a run **copies** the master
there for the duration of the render. Everything about that copy is deliberate:

| | |
|---|---|
| **byte for byte** | the renderer must hear the master, not a lossy step the pipeline slipped in on the way past |
| **the copy is scratch** | `resource/` is read and never written — a "staged" master that gets normalised is how writing to your inputs begins |
| **the folder is created** | a fresh clone has no `public/`; it is gitignored, because it holds nothing but staging |
| **the name is kept** | the props name a file inside `public/`, and a fetch path that does not look like the song is a fetch path nobody can trace |
"""
from __future__ import annotations

import pathlib
import shutil


def copy(master_path: pathlib.Path, public_dir: pathlib.Path) -> pathlib.Path:
    """Copy the master into `public_dir`, creating it if needed, and return the staged path.

    ⚠️ **A copy, never a move and never a re-encode.** If the master and the staged copy ever differ by a byte,
    the render is of something the operator did not supply — which is why the test compares the two digests
    rather than trusting a `copyfile` call.
    """
    public_dir.mkdir(parents=True, exist_ok=True)
    staged = public_dir / master_path.name
    shutil.copyfile(master_path, staged)
    return staged
