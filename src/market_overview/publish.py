"""Publish a finished package to YouTube — the deferred upload step. (0085_13)

⚠️ **The package was designed for this, and this module is the only thing it was waiting on.** `package.py` builds
each edition into `output/<date>/<lang>/` and says so: the folder "has to be handable to its own uploader without
picking files out of a mixed folder". `metadata.py` names `metadata-<lang>.json` *"the JSON the deferred upload
step will read"* and writes the video and thumbnail filenames into it. So nothing here decides *what* to upload —
the manifest already did, and it is generated from the bundle, so the upload cannot disagree with the video.

## What this module decides, and why each is a decision

- **The scope is `youtube.upload` and nothing else.** Not `youtube` (read+write over the whole account), not
  `youtube.force-ssl`. This process uploads videos and sets thumbnails; a wider token could do more than the tool
  can, which is a liability with no upside.
- **The category is Education.** The brief opens with a disclosure that it is educational and not advice, and the
  category is the one place YouTube is told what the video *is*. `News & Politics` is defensible too; Education is
  the one the product's own on-screen text claims.
- **The upload is idempotent, and that is not a nicety.** Every other step of this pipeline is re-runnable —
  `store/` makes a re-render safe, `package.py` makes assembly safe — and an uploader that re-uploads on every run
  would be the one place where "just run it again" costs something irreversible. See `marker`.
- **A dry run exists, and it is the same path.** `--dry-run` reads the package, validates it, builds the request
  body, checks whether the edition has already gone up and reports the lot — contacting nothing and recording
  nothing. That is what makes the flow testable on a machine with no credentials and no channel. ⚠️ It is
  deliberately **not** a parallel code path: a rehearsal that took a different route would only prove something
  about the rehearsal. See `run`'s `dry_run`.
- **⚠️ The video lands `private` by default.** ADR 0004's real protection was never the window server; it is the
  "Before you publish" list in the README — the Bengali reading as Bengali, the music sitting right, the mark
  being there — *"the reason a human runs it"*. An upload that defaults to `public` deletes that check silently,
  on a schedule, at four in the morning. `--privacy public` is one flag away, and it is the operator's call to
  make once, deliberately.

## Credentials

Two files, both **outside the repository**, under `~/.config/market-overview/` (override the directory with
`MARKET_OVERVIEW_CREDENTIALS`):

- `client-secret.json` — the operator's, downloaded from the Google Cloud console.
- `token.json` — produced by `mo publish --authorise`, the one step that needs a browser.

⚠️ **The token is a refresh token, and one from an OAuth client whose consent screen is still in "Testing"
expires in seven days.** That is the commonest way an uploader that worked on a laptop dies on a server a week
later, and nothing in this module can prevent it — the consent screen has to be **published**.

⚠️ **That failure is also the reason `mo publish --check` exists.** A rejected token surfaces as `invalid_grant`
from inside `google-auth`; left uncaught it reads as a bug in this tool rather than a token that needs
re-authorising, and the first place the upload path would notice is the end of an hour-long build. `check` drives
the same credential path in a second, and `service` turns every way it can fail into a refusal. See `check`.
"""
from __future__ import annotations

import datetime as _datetime
import json
import os
import pathlib
import sys
import time
from typing import Any

from . import render

try:  # pragma: no cover - the branch a build-only install takes is covered by test_publish.py
    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    AVAILABLE = True
except ImportError:  # pragma: no cover
    AVAILABLE = False


class PublishError(RuntimeError):
    """The upload cannot proceed — no credentials, no package, or the API refused. A refusal, not a crash."""


#: ⚠️ The narrowest scope that can do the job: upload a video and set its thumbnail. A wider token would let this
#: process do more than the tool can, and a credential should be able to do exactly what it is for.
SCOPE = "https://www.googleapis.com/auth/youtube.upload"

#: 27 — Education. See the module docstring; the product's own disclosure claims this.
CATEGORY = "27"

#: The operator's credentials live here, never in the repo.
CREDENTIALS_ENV = "MARKET_OVERVIEW_CREDENTIALS"
CLIENT_SECRET = "client-secret.json"
TOKEN = "token.json"

#: ⚠️ **`private`, not `public`.** Publishing is the step a human is still in the loop for, and a schedule that
#: defaults the other way removes them without asking.
PRIVACY = ("private", "unlisted", "public")
DEFAULT_PRIVACY = "private"

#: The resumable chunk. A brief is tens of megabytes, so one-shot would mostly work — but "mostly" is the wrong
#: property for the one step that cannot be tidied up afterwards.
CHUNK = 8 * 1024 * 1024

RETRIABLE = (500, 502, 503, 504)
MAX_RETRIES = 5


def credentials_dir() -> pathlib.Path:
    """Where the operator's OAuth files live. Outside the repo, like `resource/` — a token is a credential."""
    override = os.environ.get(CREDENTIALS_ENV)
    if override:
        return pathlib.Path(override).expanduser()
    return pathlib.Path.home() / ".config" / "market-overview"


def payload(date: str, lang: str) -> dict[str, Any]:
    """One edition's upload payload — the manifest, which is the whole interface (ADR 0003).

    ⚠️ Read **back from disk** rather than passed in memory, so `mo publish` can ship a day built earlier and so
    the thing uploaded is the thing that was assembled and reviewed. A payload handed over in memory would make
    "what went up" a claim about a run rather than about a file.
    """
    directory = render.out_dir(date, lang)
    manifest = directory / f"metadata-{lang}.json"
    if not manifest.is_file():
        raise PublishError(
            f"{lang}: no package at {directory} — `metadata-{lang}.json` is what marks it complete. "
            f"Build it first: uv run mo build --date {date} --lang {lang}"
        )
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PublishError(f"{lang}: {manifest} is unreadable — {exc}") from exc

    for key in ("lang", "title", "description", "tags", "video", "thumbnail", "bundle_hash"):
        if key not in data:
            raise PublishError(f"{lang}: {manifest} has no {key!r} — it is not a package this tool wrote")
    for key in ("video", "thumbnail"):
        if not (directory / data[key]).is_file():
            raise PublishError(f"{lang}: {data[key]} is named by the manifest but missing from {directory}")
    return data


def marker(date: str, lang: str) -> pathlib.Path:
    """Where the record of an upload lives: `output/<date>/.published-<lang>.json`.

    ⚠️ **Beside the language folders, never inside one.** `package.py` is explicit that a package holds "four
    files and nothing else" — a viewer's folder, not plumbing — so this goes one level up, in the run's own
    directory, where `render.date_dir` already keeps the derived bed for the same reason. `output/` is gitignored
    too, so a record of what *this machine* has sent never becomes a claim about the repository.
    """
    return render.date_dir(date) / f".published-{lang}.json"


def record(date: str, lang: str) -> dict[str, Any] | None:
    """What was uploaded for this edition, or `None` if nothing was.

    ⚠️ **An unreadable record is not "nothing was uploaded".** It is *unknown*, and the caller refuses rather than
    guessing — the two guesses are "post it again" and "skip it silently", and each is wrong on the day it is
    wrong in a different, expensive way.
    """
    path = marker(date, lang)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PublishError(
            f"{path} exists but cannot be read ({exc}) — delete it to upload again deliberately"
        ) from exc


def remember(date: str, lang: str, video_id: str, privacy: str, bundle_hash: str) -> pathlib.Path:
    """Record an upload, atomically — the same temp-file-then-rename as `store.write_facts`."""
    path = marker(date, lang)
    path.parent.mkdir(parents=True, exist_ok=True)
    written = {
        "video_id": video_id,
        "url": f"https://youtu.be/{video_id}",
        "privacy": privacy,
        # ⚠️ The bundle's hash, so a rebuilt day is uploaded again and an unchanged one is skipped. It is the
        # manifest's own per-edition hash, so re-cutting Bengali does not re-upload English (issue 20).
        "bundle_hash": bundle_hash,
        "published_at": _datetime.datetime.now(_datetime.timezone.utc).isoformat(timespec="seconds"),
    }
    temporary = path.with_name(f".{path.name}.part")
    temporary.write_text(json.dumps(written, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)
    return path


def body(data: dict[str, Any], privacy: str) -> dict[str, Any]:
    """The `videos.insert` request body, straight from the manifest.

    ⚠️ **`privacyStatus` is passed explicitly even though `private` is the API's own default.** A default that
    happens to agree today is not a decision, and this is the one field whose default *is* a policy.
    """
    if privacy not in PRIVACY:
        raise PublishError(f"privacy must be one of {', '.join(PRIVACY)}, got {privacy!r}")
    return {
        "snippet": {
            "title": data["title"],
            "description": data["description"],
            "tags": data["tags"],
            "categoryId": CATEGORY,
            # ⚠️ The edition's own language, so YouTube does not infer it from a title that is mostly proper nouns:
            # `NIFTY 50` and `BSE` are the same string in both editions, so the title carries no signal at all.
            "defaultLanguage": data["lang"],
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }


def describe(date: str, lang: str, data: dict[str, Any], privacy: str) -> str:
    """One edition's upload, as text, without sending it — see `run`'s `dry_run`.

    ⚠️ It reports the **request body and the artefact paths**, not a summary of them. The body is what the API is
    told, and a hand-written summary would be a second description of the upload — which is the one thing this
    module keeps out (`body` reads the manifest for the same reason). The paths and their sizes are here because
    "the package is on disk and complete" is the property a rehearsal is actually checking.
    """
    sent = body(data, privacy)
    snippet, status = sent["snippet"], sent["status"]
    directory = render.out_dir(date, lang)

    def megabytes(name: str) -> str:
        return f"{(directory / name).stat().st_size / 1024 / 1024:.1f} MB"

    return "\n".join(
        (
            f"{lang}: dry run — nothing was sent and nothing was recorded",
            f"  video        {directory / data['video']} ({megabytes(data['video'])})",
            f"  thumbnail    {directory / data['thumbnail']} ({megabytes(data['thumbnail'])})",
            f"  title        {snippet['title']}",
            f"  tags         {', '.join(snippet['tags'])}",
            f"  description  {len(snippet['description'].splitlines())} lines — the whole text is the "
            f"package's metadata-{lang}.txt",
            f"  status       category {snippet['categoryId']} · language {snippet['defaultLanguage']} · "
            f"{status['privacyStatus']} · made for kids {status['selfDeclaredMadeForKids']}",
        )
    )


def _send(request: Any, label: str) -> dict[str, Any]:
    """Drive a resumable request to completion, retrying the failures that are worth retrying.

    ⚠️ A 4xx is **not** retried. It is a refusal — a bad scope, a quota exhausted, a video the channel may not
    accept — and repeating it five times only delays the message and burns quota doing it.
    """
    response = None
    attempts = 0
    while response is None:
        try:
            status, response = request.next_chunk()
        except HttpError as exc:
            code = getattr(exc.resp, "status", None)
            if code not in RETRIABLE or attempts >= MAX_RETRIES:
                raise PublishError(f"{label} refused by the API ({code}): {exc}") from exc
            attempts += 1
            time.sleep(2**attempts)
            print(f"  {label}: retrying after {code} (attempt {attempts})", flush=True)
            continue
        if status is not None:
            print(f"  {label}: {status.progress() * 100:.0f}%", flush=True)
    return response


def service() -> Any:
    """An authenticated client, from the refresh token on disk.

    ⚠️ **The refreshed token is written back.** Google rotates refresh tokens, and a server that discards the new
    one keeps working right up until the moment it stops — with nothing in between to warn anyone.

    ⚠️ **Every way this can fail is a `PublishError`, and that is this module's own contract** — *"A refusal, not a
    crash"* — rather than tidiness. The two libraries throw two different exception types at this code
    (`RefreshError` for a rejected token, `ValueError` for a token file that is not one), neither of which is a
    `PublishError`, so both would otherwise escape as a traceback. And the moment they would escape is the worst
    possible one: after an hour-long build, on the failure the README calls the likeliest way a schedule dies.
    """
    if not AVAILABLE:
        raise PublishError("the YouTube client libraries are not installed — `uv sync --extra publish`")
    token = credentials_dir() / TOKEN
    if not token.is_file():
        raise PublishError(
            f"no credentials at {token} — run `uv run mo publish --authorise` once, on a machine with a browser"
        )
    try:
        credentials = Credentials.from_authorized_user_file(str(token), [SCOPE])
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            token.write_text(credentials.to_json(), encoding="utf-8")
            token.chmod(0o600)
    except RefreshError as exc:
        raise PublishError(
            f"the token at {token} was rejected ({exc}) — run `uv run mo publish --authorise` again on a machine "
            "with a browser. ⚠️ If it worked for a week and then stopped, the OAuth client's consent screen is "
            "almost certainly still in 'Testing': publish it, or the replacement expires in seven days too"
        ) from exc
    except ValueError as exc:
        raise PublishError(
            f"{token} is not a token this tool can read ({exc}) — delete it and run "
            "`uv run mo publish --authorise` again"
        ) from exc
    return build("youtube", "v3", credentials=credentials, cache_discovery=False)


def check() -> int:
    """Prove the credentials on disk work, then exit. Returns a process exit code.

    ⚠️ **This belongs *before* a build, not after one.** A build is over an hour per edition; the token is the part
    most likely to be wrong; and `--authorise` cannot report it, because it stores whatever the consent flow
    returned — which proves the flow ran, not that the token will still be accepted tomorrow. So this drives the
    same `service()` the upload drives, and needs no package, so it can be run before there is anything to upload.

    ⚠️ It proves the **token**, not the whole account. A scope the client was never granted would surface only at
    the upload itself, and saying so here is cheaper than an operator mistaking this for a rehearsal — `--dry-run`
    is the one that walks the upload.

    `cache_discovery=False` means no discovery document is fetched, so nothing here reaches the network unless the
    token actually needed refreshing.
    """
    try:
        service()
    except PublishError as exc:
        print(f"credentials are not usable: {exc}", file=sys.stderr)
        return 1
    print(f"credentials OK — refresh token at {credentials_dir() / TOKEN}")
    return 0


def run(
    date: str,
    langs: tuple[str, ...],
    *,
    privacy: str,
    force: bool,
    api: Any = None,
    dry_run: bool = False,
) -> int:
    """Upload every edition that has not already gone up. Returns a process exit code.

    ⚠️ **A refusal here exits non-zero, like every other refusal in the tool** — because the caller is a schedule,
    and a schedule's only way to say "this did not happen" is its exit code.

    ⚠️ **`dry_run` removes exactly two statements and keeps everything else.** No client is built and nothing is
    sent or recorded; but the package is still read, still validated, the body is still constructed and the
    already-published check still runs — so a rehearsal cannot pass where the real run would refuse. That is the
    entire value of the flag: a test that passed on a *different* path would say nothing about this one.
    """
    client = None
    if not dry_run:
        try:
            client = api if api is not None else service()
        except PublishError as exc:
            print(f"refusing to publish {date}: {exc}", file=sys.stderr)
            return 1

    for lang in langs:
        try:
            data = payload(date, lang)
            known = record(date, lang)
            if known is not None and not force:
                if known.get("bundle_hash") == data["bundle_hash"]:
                    print(f"{lang}: already published — {known.get('url', '?')}", flush=True)
                    continue
                raise PublishError(
                    f"{lang}: already published from a different bundle ({known.get('url', '?')}). "
                    "The numbers changed, so uploading again would add a second video rather than replace the "
                    "first — delete the old one, then pass --force"
                )
            # ⚠️ **After** the already-published check, not before it. A dry run's job is to say what the next real
            # run would do, and on an edition that is already up the next real run does nothing — printing a plan
            # there would promise an upload that would not happen.
            if dry_run:
                print(describe(date, lang, data, privacy), flush=True)
                continue
            print(f"uploading {lang} ({privacy}) …", flush=True)
            video_id = upload(date, lang, data, service=client, privacy=privacy)
            path = remember(date, lang, video_id, privacy, data["bundle_hash"])
            print(f"{lang}: uploaded https://youtu.be/{video_id} — recorded in {path.name}", flush=True)
        except PublishError as exc:
            print(f"refusing to publish {date}: {exc}", file=sys.stderr)
            return 1
    return 0


def authorise() -> int:
    """Run the installed-app consent flow once and store a refresh token.

    ⚠️ **The only step that must happen on a machine with a browser**, which is why it is a flag rather than
    something uploading does implicitly: a server cannot open a consent window, and a scheduled run that tried
    would hang until its timeout with nothing in the log to say why.
    """
    if not AVAILABLE:
        print(
            "the YouTube client libraries are not installed — `uv sync --extra publish`",
            file=sys.stderr,
        )
        return 1
    from google_auth_oauthlib.flow import InstalledAppFlow

    secrets_file = credentials_dir() / CLIENT_SECRET
    if not secrets_file.is_file():
        print(
            f"no OAuth client at {secrets_file} — download one from the Google Cloud console "
            f"(type: Desktop app) and save it there",
            file=sys.stderr,
        )
        return 1

    flow = InstalledAppFlow.from_client_secrets_file(str(secrets_file), [SCOPE])
    credentials = flow.run_local_server(port=0)
    token = credentials_dir() / TOKEN
    token.write_text(credentials.to_json(), encoding="utf-8")
    token.chmod(0o600)
    print(f"authorised — refresh token stored at {token}")
    print(
        "⚠️ if that client's consent screen is still in 'Testing', this token expires in 7 days. "
        "Publish the consent screen before putting this on a schedule."
    )
    return 0


def upload(date: str, lang: str, data: dict[str, Any], *, service: Any, privacy: str) -> str:
    """Upload one edition's video, then its thumbnail. Returns the video id.

    ⚠️ **The client is a parameter, not a lookup.** The whole of this module is then testable against a stub — and
    an uploader is exactly the kind of code that quietly stops being tested once its only entry point is a live
    API with real credentials behind it.
    """
    if not AVAILABLE:
        raise PublishError("the YouTube client libraries are not installed — `uv sync --extra publish`")
    directory = render.out_dir(date, lang)
    media = MediaFileUpload(str(directory / data["video"]), chunksize=CHUNK, resumable=True)
    request = service.videos().insert(part="snippet,status", body=body(data, privacy), media_body=media)
    response = _send(request, f"{lang}: upload")
    video_id = response.get("id")
    if not video_id:
        raise PublishError(f"{lang}: the API accepted the upload but returned no video id — {response}")

    # ⚠️ The thumbnail goes **after** the video, because it cannot be set on a video that does not exist yet.
    thumb = MediaFileUpload(str(directory / data["thumbnail"]))
    service.thumbnails().set(videoId=video_id, media_body=thumb).execute()
    return video_id


