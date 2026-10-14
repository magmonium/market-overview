"""Where the data is — the one seam **both products** share.

⚠️ **Two roots, and they answer different questions.** `store.root()` is the **repository**: the code, the
`node_modules` the renderer is invoked from, the vendored fonts, and the committed snapshot. This module is
the **data root**: the operator's licensed assets and the day's deliverables, which live **outside** the
repository so that a build artefact and a rebuildable snapshot stop being the same kind of thing.

⚠️ **Why outside, and why shared.** Two tools write here — the brief and the reel — so the folders are
**namespaced per product** (`resource/brief/`, `resource/reel/`, `output/brief/`, `output/reel/`). Two runs
can then proceed at the same time without a lock, because they cannot touch the same file; the guarantee is
a property of the layout rather than of a lockfile that would need a stale-lock story of its own.

⚠️ **The word `reel` is deliberately absent.** The brief names its own namespace and nothing else: the reel
depends on this package, never the reverse, so a brief that could name the reel's folders would be one import
away from knowing about a product it must not need to build. The reel reads `data_root()` from here and spells
its own half.

⚠️ **`store/` is not here.** The per-date snapshot and the reel's recorded run stay in the repository, because
they are the *rebuild evidence* and they are committed — see the note in `store.py`.
"""
from __future__ import annotations

import os
import pathlib

#: The one variable both products read.
#:
#: ⚠️ **Not `MARKET_OVERVIEW_ROOT`.** That name is the *repository*: `deploy/Dockerfile` sets it to `/app` and
#: `deploy/daily-brief.sh` uses it to `cd`, and **no Python module reads it**. A data root answering to the
#: same name would make two different ideas look like one, and the version that got set would be the wrong one.
DATA_ENV = "MARKET_OVERVIEW_DATA"

#: The brief's own half of the data root: the licensed assets and the day's packages.
BRIEF = "brief"


def data_root() -> pathlib.Path:
    """The shared data root — outside the repository, one folder for both products.

    Defaults to the XDG data directory, the partner to the credentials in `~/.config/market-overview/`
    (`publish.credentials_dir`) — not `~/Documents`, which a laptop may be syncing, and not the repository,
    which a 250 MB reel and a gitignored deliverable must both stay out of.

    ⚠️ **Resolved per call, not frozen at import**, so the environment is read when the run starts rather than
    when the module was first imported — and so a test can point a whole tool at a temporary root through the
    one seam, which is the habit `store.root()` and the reel's `paths.py` already keep.
    """
    override = os.environ.get(DATA_ENV)
    if override:
        return pathlib.Path(override).expanduser()
    return pathlib.Path.home() / ".local" / "share" / "market-overview"


def brief_resource() -> pathlib.Path:
    """`resource/brief/` — the mark and the music bed. Read, never written (see the README's asset contract)."""
    return data_root() / "resource" / BRIEF


def brief_output() -> pathlib.Path:
    """`output/brief/<date>/<lang>/` — the day's packages, and the derived bed above them."""
    return data_root() / "output" / BRIEF
