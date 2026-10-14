"""The repository's `.env` — ⚠️ **a convenience over the environment, never a second configuration.**

⚠️ **Why it exists.** A credential is read from the environment — the books brief's `NYT_API_KEY`, and its optional
`GOOGLE_BOOKS_API_KEY` — and an operator running a build by hand should not have to remember an `export` in every new
shell. This reads `<repo>/.env` once, at the start of a run, and fills in the variables that are not already set.

⚠️ **The environment always wins, and that is the whole design.** Every value is written only when the name is not
already set to something, so an exported variable is never overridden by a stale file. ⚠️ Without that rule a `.env`
would be a *second* source of truth, and *"why is it using the old key"* would become a question with no visible
answer — which is the failure mode `paths.DATA_ENV` and every other variable here already avoids by having one home.

⚠️ **Nothing here is a config system, and it is deliberately small.** No interpolation, no multi-line values, no
inheritance, and **no new dependency** — the format is `KEY=VALUE`, one per line, which is all a key needs. ⚠️ A
missing file is a no-op, and so is a line that cannot be read: a courtesy that can abort a run is not a courtesy.

⚠️ **It is gitignored** — see the repository's own `.gitignore`, which carries the rule *and* the reason. ⚠️ A key in
a committed file is a published key, which is what `books_brief.fetch.nyt` already says about the environment it reads.
"""
from __future__ import annotations

import os
import pathlib

#: The file, at the repository's root — one for every product, because the credential it holds is not per-product.
ENV_FILE = ".env"


def root() -> pathlib.Path:
    """The repository — `src/`, `docs/`, `deploy/` and `store/` sit under it.

    ⚠️ **The same anchor `store.root()` uses, and deliberately the same expression.** `store/` is the repository's own
    evidence folder, so "where is the repository" has to have one answer rather than two that agree today.

    ⚠️ **Not `MARKET_OVERVIEW_ROOT`.** That name is the *deploy* checkout's path — `deploy/Dockerfile` sets it to
    `/app` and `deploy/daily-brief.sh` uses it to `cd` — and no Python module reads it. `paths.py` already refuses to
    let a second idea answer to it.
    """
    return pathlib.Path(__file__).resolve().parents[2]


def path() -> pathlib.Path:
    """`<repo>/.env` — read if it is there, and **never written by this tool**."""
    return root() / ENV_FILE


def _unquote(value: str) -> str:
    """A value with **one layer of matching quotes** removed, or nothing at all.

    ⚠️ **Matching quotes only.** A key that legitimately begins and ends with the same character has to survive, so a
    lone leading `"` is left alone rather than truncated. ⚠️ Both `'` and `"` are accepted, because an operator pasting
    from a shell, a JSON blob or a YAML file should not have to know which one this format wants.
    """
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def parse(text: str) -> dict[str, str]:
    """The variables in a `.env`'s text — **pure, so the format is tested without touching a filesystem.**

    ⚠️ **`KEY=VALUE`, one per line**, plus the three things an operator will actually type: blank lines, `#` comments,
    and a leading `export ` copied straight out of a shell.

    ⚠️ **A line with no `=`, or with no name, is skipped rather than fatal** — the same rule as everywhere else in this
    product: a malformed courtesy is not a reason to lose a run. ⚠️ And the value keeps any `=` of its own
    (`partition`, not `split`), because a base64 key very often ends in one.
    """
    found: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        name, separator, value = line.partition("=")
        name = name.strip()
        if not separator or not name:
            continue
        found[name] = _unquote(value.strip())
    return found


def load() -> dict[str, str]:
    """Read `<repo>/.env` and fill in the variables that are not already set — **returning what it set.**

    ⚠️ **The return value is the point.** *"The environment wins"* is a claim, and a claim about `os.environ` is one
    that a test can only check by reading the whole environment back — so this hands back exactly what it changed, and
    an empty mapping is the ordinary answer for a run with no `.env` at all.

    ⚠️ **A variable set to the empty string counts as unset**, matching `fetch.nyt`'s own `if not key:` — an empty
    export is not a key, so the file is allowed to supply one rather than leaving the run to fail on a blank.
    """
    try:
        text = path().read_text(encoding="utf-8")
    except OSError:
        # ⚠️ **No file is the ordinary case, not an error** — the environment alone is a complete configuration, and a
        # run that needs no key must not print anything about a file it was never given.
        return {}

    applied: dict[str, str] = {}
    for name, value in parse(text).items():
        if os.environ.get(name):
            continue
        os.environ[name] = value
        applied[name] = value
    return applied
