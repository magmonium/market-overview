"""Ticket 24 — the publish target: **YouTube, one video per chart, `private` by default.**

⚠️ **The package was built for this and this is the only thing it was waiting on.** `package.py` says a folder *"has to
be handable to its own uploader without picking files out of a mixed folder"*, and `metadata-<chart>.json` names the video,
the thumbnail and the `bundle_hash` — *"self-contained by construction"* (ticket 15). So nothing here decides **what** to
upload: the manifest already did, and it was generated from the bundle, so the upload cannot disagree with the video.

⚠️ **The credentials are the brief's, and that is the point of importing them rather than copying them.** The token lives
at `~/.config/market-overview/token.json` for **one scope** (`youtube.upload`) — so a second credentials directory would
mean the operator authorising the same client twice for the same permission, and two tokens that expire independently.
⚠️ The consequence is deliberate: **`bb publish` has no `--authorise`.** That flow needs a browser and belongs to
`mo publish --authorise`, which already grants everything this module can do. `--check` is here because *verifying* a
token is cheap and the moment it matters is before an hour of rendering, not after.

⚠️ **The upload is idempotent, and here that is a *refusal*, not a skip.** Ticket 10: *"a re-run of the same week posts
nothing, and a rebuilt week (different hash) refuses rather than putting two different charts under one title."* ⚠️ The
second half is the one worth having: two charts under one title is not a duplicate, it is a **contradiction**, and the
week's evidence says which one is real.

⚠️ **`private` by default.** ADR 0006's sharpest line is that *"ADR 0004's real protection was never the window server;
it is the README's 'Before you publish' list… the reason a human runs it."* The books equivalent is the check this whole
map was built toward — **is the Bengali chart actually Bengali, are the covers the right books, is the rank plausible,
does the footer name the right sources.** An upload that defaulted to `public` would delete that check silently, on a
timer. The switch is one flag, and it is the operator's to make once, deliberately.
"""
from __future__ import annotations

import json
import pathlib
import sys
from typing import Any, Iterable

# ⚠️ **The one authorisation**, imported rather than reimplemented. See the module docstring: the token is shared, the
# scope is shared, and the consent flow is the brief's — so this module must not grow a second copy of any of them.
from market_overview.publish import (
    AVAILABLE,
    CLIENT_SECRET,
    DEFAULT_PRIVACY,
    PRIVACY,
    SCOPE,
    TOKEN,
    credentials_dir,
)

from . import package, paths

# ⚠️ **The upload's transport, imported from the brief, and the retry policy is the reason.**
#
# The scope, the token, the client and the retry table are one decision each — and a copy of the retry table here would
# be a second policy that drifts the first time either is tuned. `service` is public; `_send` is not, and importing a
# private name across a package boundary is a cost accepted deliberately rather than duplicating it.
from market_overview.publish import _send as send
from market_overview.publish import service

try:  # ⚠️ The same optional extra the brief uses — `uv sync --extra publish`.
    from googleapiclient.http import MediaFileUpload
except ImportError:  # pragma: no cover - the refusal path, not a path the suite exercises
    # ⚠️ **Bound to `None` rather than left undefined**, so `upload`'s guard is a check rather than the only thing
    # standing between a missing extra and a `NameError`. ⚠️ And `AVAILABLE` is **not** redefined here: it is the brief's
    # own answer to the same question, and two answers to one question is how they start disagreeing.
    MediaFileUpload = None  # type: ignore[assignment,misc]

#: ⚠️ The resumable chunk size. Small enough that a dropped connection resumes rather than restarts, large enough that a
#: two-minute video is a handful of requests.
CHUNK = 1024 * 1024

#: ⚠️ **The marker lives in the package folder**, because that is what persists across runs — ticket 10's own note: an
#: ephemeral `output/` re-uploads the week on every firing. ⚠️ It is deliberately **not** `store/`: the store is the
#: week's *evidence*, and what went up on YouTube is not evidence about the chart.
MARKER = "published.json"


class PublishError(RuntimeError):
    """The upload cannot proceed — and it is printed, never a traceback."""


def manifest(week: str, chart: str) -> dict[str, Any]:
    """The package's JSON, read as the uploader's input.

    ⚠️ **A missing manifest is a refusal, and it is the same fact `package.assemble` writes last.** That file exists only
    in a *finished* package, so its absence means the video or the thumbnail is not there either — and an uploader that
    went looking for the filenames anyway would be guessing at what to send.
    """
    path = package.dir_for(week, chart) / package.MANIFEST(chart)
    if not path.is_file():
        raise PublishError(
            f"{week}/{chart}: no {path.name} at {path} — the package is not finished, so there is nothing to publish"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def marker(week: str, chart: str) -> pathlib.Path:
    """Where this chart's record of a completed upload lives. See `MARKER`."""
    return package.dir_for(week, chart) / MARKER


def record(week: str, chart: str) -> dict[str, Any] | None:
    """What was uploaded for this chart, or `None` — ⚠️ and `None` is *never uploaded*, not *unknown*."""
    path = marker(week, chart)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        # ⚠️ A marker that will not parse is treated as absent rather than as an error, because the alternative is a
        # half-written file permanently blocking a re-run. `remember` writes atomically, so this should not happen — and
        # if it does, uploading again is recoverable where refusing forever is not.
        return None


def remember(
    week: str, chart: str, video_id: str, privacy: str, bundle_hash: str
) -> pathlib.Path:
    """Record that this chart went up, and from which bundle.

    ⚠️ **`bundle_hash` is the half that makes the refusal possible.** A video id alone would say *something was
    uploaded*; the hash says *which week's facts it describes* — and that is what lets a rebuild notice it is about to
    put a different chart under an existing title.
    """
    path = marker(week, chart)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "week": week,
        "chart": chart,
        "video_id": video_id,
        "url": f"https://youtu.be/{video_id}",
        "privacy": privacy,
        "bundle_hash": bundle_hash,
    }
    # ⚠️ Written through the package's own atomic writer, so the marker cannot be a half-file — and so it gets the same
    # `0644` the metadata beside it has.
    package.write_atomically(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path


#: ⚠️ **Education**, and the same value the brief sends. It is the one place YouTube is told what the video *is*, and
#: *"a ranked list of books with the method stated"* is what the product claims on screen. `Entertainment` is defensible
#: and would be a different product.
CATEGORY = "27"


def body(data: dict[str, Any], privacy: str) -> dict[str, Any]:
    """The request body — **read from the manifest, never re-derived.**

    ⚠️ Every string here came out of `metadata-<chart>.json`, which was generated from the week's bundle. So the upload
    cannot disagree with the video: there is no second description of the chart anywhere in this module, which is the
    same rule `package.assemble` keeps when it refuses to write text about artefacts that are not there.
    """
    if privacy not in PRIVACY:
        raise PublishError(f"privacy must be one of {', '.join(PRIVACY)}, got {privacy!r}")

    return {
        "snippet": {
            "title": data["title"],
            "description": data["description"],
            "tags": list(data["tags"]),
            "categoryId": CATEGORY,
            # ⚠️ The chart's own label language, so YouTube does not infer it from a title that is mostly proper nouns —
            # `TOP 100 BENGALI BOOKS` is the same string in both editions, so the title carries no signal at all.
            "defaultLanguage": data.get("language") or "en",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }


def describe(week: str, chart: str, data: dict[str, Any], privacy: str) -> str:
    """One chart's upload, as text, without sending it — what `--dry-run` prints.

    ⚠️ It reports the **request body and the artefact paths**, not a summary of them: the body is what the API would be
    told, and a hand-written summary would be a second description of the upload. The paths and their sizes are here
    because *"the package is on disk and complete"* is the property a rehearsal is actually checking.
    """
    sent = body(data, privacy)
    snippet, status = sent["snippet"], sent["status"]
    directory = package.dir_for(week, chart)

    def megabytes(name: str) -> str:
        return f"{(directory / name).stat().st_size / 1024 / 1024:.1f} MB"

    return "\n".join(
        (
            f"{chart}: dry run — nothing was sent and nothing was recorded",
            f"  video        {directory / data['video']} ({megabytes(data['video'])})",
            f"  thumbnail    {directory / data['thumbnail']} ({megabytes(data['thumbnail'])})",
            f"  title        {snippet['title']}",
            f"  tags         {', '.join(snippet['tags'])}",
            f"  description  {len(snippet['description'].splitlines())} lines — the whole text is the package's "
            f"{package.TEXT(chart)}",
            f"  status       category {snippet['categoryId']} · language {snippet['defaultLanguage']} · "
            f"{status['privacyStatus']} · made for kids {status['selfDeclaredMadeForKids']}",
        )
    )


def upload(week: str, chart: str, data: dict[str, Any], *, service: Any, privacy: str) -> str:
    """Upload one chart's video, then its thumbnail. Returns the video id.

    ⚠️ **The client is a parameter, not a lookup.** The whole of this module is then testable against a stub — and an
    uploader is exactly the kind of code that quietly stops being tested once its only entry point is a live API with
    real credentials behind it.
    """
    if not AVAILABLE:
        raise PublishError("the YouTube client libraries are not installed — `uv sync --extra publish`")

    directory = package.dir_for(week, chart)
    media = MediaFileUpload(str(directory / data["video"]), chunksize=CHUNK, resumable=True)
    request = service.videos().insert(part="snippet,status", body=body(data, privacy), media_body=media)
    response = send(request, f"{chart}: upload")
    video_id = response.get("id")
    if not video_id:
        raise PublishError(
            f"{chart}: the API accepted the upload but returned no video id — {response}"
        )

    # ⚠️ The thumbnail goes **after** the video, because it cannot be set on a video that does not exist yet.
    thumb = MediaFileUpload(str(directory / data["thumbnail"]))
    service.thumbnails().set(videoId=video_id, media_body=thumb).execute()
    return video_id


def check() -> int:
    """Ask whether the shared token still works, without uploading anything.

    ⚠️ **Cheap, and the moment it matters is *before* the build, not after.** A rejected token surfaces as
    `invalid_grant` from inside `google-auth`; left alone it reads as a bug in this tool rather than a token needing
    re-authorising — and the first place the upload path would notice is the end of an hour of rendering. `service`
    turns every way it can fail into a refusal, so this is one call and one line.
    """
    try:
        client = service()
    except PublishError as exc:
        print(f"the shared token cannot be used: {exc}", file=sys.stderr)
        return 1
    # ⚠️ A real call, not merely a constructed client: a token can build a service object and still be refused by the
    # API, which is exactly the failure this exists to find early.
    client.channels().list(part="id", mine=True).execute()
    print(f"the shared token works — {credentials_dir() / TOKEN}")
    return 0


def run(
    week: str,
    wanted: Iterable[str],
    *,
    privacy: str = DEFAULT_PRIVACY,
    dry_run: bool = False,
) -> int:
    """Publish every chart asked for — or say what it would do.

    ⚠️ **The two refusals are different facts and are worded so.** *Already up from this bundle* is a re-run, and it
    posts nothing. *Already up from a different bundle* means the week was **rebuilt**, and the run refuses: two
    different charts under one title is not a duplicate, it is a contradiction. Ticket 10 asks for both.
    """
    if privacy not in PRIVACY:
        print(f"privacy must be one of {', '.join(PRIVACY)}, got {privacy!r}", file=sys.stderr)
        return 1

    wanted = tuple(sorted(wanted))
    if not wanted:
        # ⚠️ **A week with nothing to publish is not a success, and the first version of this returned 0 silently.**
        #
        # A smoke run found it: `bb publish --week 2026-W52` on a week that was never built printed nothing and exited
        # zero — which on a timer reads as *"the week went up"* rather than *"the week was never built"*. ⚠️ Ticket 10's
        # rule is that a refusal **exits non-zero and writes nothing**, and this is the case where saying nothing is
        # indistinguishable from succeeding.
        #
        # ⚠️ And it cannot fire on a healthy re-run: a week that *was* built has packages on disk, so the list is
        # non-empty and every chart reports *already up* on its own line.
        print(
            f"{week}: no finished package to publish — build the week first, or check the week is the one you meant",
            file=sys.stderr,
        )
        return 1

    # ⚠️ Built **once**, and only when it is needed. A dry run must not touch the network at all, and an all-already-up
    # run must not either — so the client is created lazily rather than at the top.
    client = None

    for chart in wanted:
        try:
            data = manifest(week, chart)
            done = record(week, chart)

            if done is not None and done.get("bundle_hash") == data.get("bundle_hash"):
                print(f"{chart}: already up from this bundle — {done['url']}", flush=True)
                continue
            if done is not None:
                raise PublishError(
                    f"{chart}: {done['url']} is already up from a *different* bundle "
                    f"({done.get('bundle_hash', '')[:12]}… → {str(data.get('bundle_hash'))[:12]}…). The week has been "
                    "rebuilt, so publishing would put a second, different chart under one title — delete the video or "
                    f"the marker at {marker(week, chart)} to decide deliberately"
                )

            if dry_run:
                print(describe(week, chart, data, privacy), flush=True)
                continue

            if client is None:
                client = service()

            print(f"uploading {chart} ({privacy}) …", flush=True)
            video_id = upload(week, chart, data, service=client, privacy=privacy)
            path = remember(week, chart, video_id, privacy, str(data.get("bundle_hash") or ""))
            print(f"{chart}: uploaded https://youtu.be/{video_id} — recorded in {path.name}", flush=True)
        except PublishError as exc:
            print(f"refusing to publish {week}: {exc}", file=sys.stderr)
            return 1

    return 0


def charts_in(week: str) -> tuple[str, ...]:
    """Every chart with a **finished** package this week — ⚠️ read off the disk, not off `charts.ALL`.

    ⚠️ The difference is the whole point of ticket 13's partial delivery: a week may hold three charts and not four, and
    an uploader that walked the declaration table would try to publish a chart nobody built.
    """
    root = paths.output_dir() / week
    if not root.is_dir():
        return ()
    return tuple(
        sorted(
            entry.name
            for entry in root.iterdir()
            if entry.is_dir() and (entry / package.MANIFEST(entry.name)).is_file()
        )
    )
