"""Where the reel's folders are — the seams a test patches.

⚠️ **Two kinds of seam, where there used to be one.** The reel's *data* — the songs it reads and the packages
it writes — lives under the **shared data root** (`market_overview.paths`), outside the repository, namespaced
`resource/reel/` and `output/reel/` so a reel and a brief can render at the same time without touching the same
file. What stays in the project is what is *not* data: `store/`, the recorded run that makes a rebuild a rebuild
— it stays because it is **committed**, exactly as the brief's per-date snapshot does — and `public/`, which is
scratch for a render that runs from this tree.

⚠️ **The mark is still the brief's, and now it is literally the brief's folder.** The logo is read from
`resource/brief/` — the brief's own namespace — through the brief's own loader, so one licensed file serves both
products and there is one place to change it.

⚠️ A named function per folder rather than an inline path, so a test can point the whole tool at a temporary
root without freezing anything else — the habit of the brief's `store.root()`.

⚠️ **`data_root()` is defined *here*, and every data folder calls it by that module-level name.** Delegating
straight to `brief_paths.brief_resource()` would leave the songs and the mark resolving outside this module's
seam, so patching `song_video.paths.data_root` would redirect `output/` and not `resource/` — one test seam
quietly covering half of what it claims to.
"""
from __future__ import annotations

import pathlib

from market_overview import paths as brief_paths
from market_overview import store
from market_overview.paths import BRIEF

#: The reel's own half of the shared data root. ⚠️ Spelled here rather than in the brief: the brief names its
#: own namespace and nothing else, and this is the other half of the same rule.
REEL = "reel"


def project_root() -> pathlib.Path:
    """The reel's own project — `store/` and `public/` sit under it. ⚠️ `resource/` and `output/` do not.

    ⚠️ **`parents[1]`, not `parents[2]`: the package sits directly in the project, with no `src/` layer.** The
    project already lives inside the repository's `src/`, so `src/song-video/src/song_video/` would be a `src`
    inside a `src` for no gain — one level up from `song_video/paths.py` is the project, and two is the repository.
    """
    return pathlib.Path(__file__).resolve().parents[1]


def repo_root() -> pathlib.Path:
    """The repository holding both products — the brief's own root, which is where the toolchain lives.

    ⚠️ **This used to be `project_root().parent`, and that stopped being true.** The reel moved from `song-video/`
    to `src/song-video/`, so both products' code sits under the repository's `src/` — and "one level up" now lands
    on `src/`, where there is no `node_modules` and no `remotion/`. The repository is therefore **asked for rather
    than assumed**: the brief *is* the repository, `store.root()` is documented as the tool's root (the folder
    holding `src/`, `node_modules` and `store/`), and this is one definition of it rather than a second.
    """
    return store.root()


def data_root() -> pathlib.Path:
    """The shared data root — the brief's own resolver, reused rather than re-derived.

    ⚠️ **One environment variable for both products.** `MARKET_OVERVIEW_DATA` overrides it; the default and the
    reasoning live in the brief's `paths.py`, and there is deliberately only one copy of them.
    """
    return brief_paths.data_root()


def song_dir() -> pathlib.Path:
    """`resource/reel/song/` — the masters, and the optional covers beside them."""
    return data_root() / "resource" / REEL / "song"


def mark_dir() -> pathlib.Path:
    """The brief's `resource/brief/` — the logo the reel draws, reused rather than copied."""
    return data_root() / "resource" / BRIEF


def shared_remotion() -> pathlib.Path:
    """The brief's `remotion/` — vendored fonts and the seeded PRNG the reel draws with."""
    return repo_root() / "remotion"


def store_dir() -> pathlib.Path:
    """`store/<song>/` — the recorded run that makes a rebuild a rebuild. ⚠️ In the project, and committed."""
    return project_root() / "store"


def output_dir() -> pathlib.Path:
    """`output/reel/<song>/<theme>/` — the packages, under the shared data root."""
    return data_root() / "output" / REEL


def public_dir() -> pathlib.Path:
    """Staging for the renderer: the song is copied here for the run and deleted with it."""
    return project_root() / "public"

