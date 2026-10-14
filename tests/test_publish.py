"""Publishing — the one step that cannot be tidied up afterwards. (0085_13)

⚠️ **What these tests are really about is the second run.** Every other stage of this pipeline is re-runnable:
`store/` makes a re-render safe, `package.py` makes assembly safe, and the README says so twice. Uploading is the
one place where "just run it again" is irreversible, so the properties worth testing are the ones that stop a
scheduled run from posting the same brief twice — or from posting a *different* brief under a name a viewer has
already seen.

⚠️ And the second thing they are about is that **the payload is the package's own metadata**, read back from disk.
`metadata-<lang>.json` is generated from the bundle, so a test that found the upload body disagreeing with it would
be finding that the tool can describe a video it did not make.

Nothing here reaches the network: the API client is a stub, which is exactly why `upload()` takes its client as a
parameter rather than looking one up.
"""
from __future__ import annotations

import contextlib
import io
import json
import pathlib
import tempfile
import unittest
from unittest import mock

from market_overview import paths, publish, render, store

DATE = "2026-10-12"
LANG = "bn"
VIDEO_ID = "dQw4w9WgXcQ"

#: A manifest in the shape `package.assemble` writes, carrying only the fields the uploader reads.
MANIFEST: dict = {
    "lang": LANG,
    "date": DATE,
    "title": "নিফটি ৫০ | ১২ অক্টোবর, ২০২৬",
    "description": "শিক্ষামূলক তথ্য · কোনো বিনিয়োগ পরামর্শ নয়",
    "tags": ["market brief", "nifty 50"],
    "hashtags": ["#MarketBrief"],
    "video": render.video_name(DATE, LANG),
    "thumbnail": render.thumbnail_name(DATE, LANG),
    "bundle_hash": "a" * 64,
}


class _Exec:
    def execute(self) -> dict:
        return {}


class _Upload:
    """Stands in for a resumable request: one chunk, then complete."""

    def __init__(self, response: dict) -> None:
        self.response = response

    def next_chunk(self) -> tuple[None, dict]:
        return None, self.response


class Stub:
    """A `service` that records what it was asked to do and answers the way the API would.

    ⚠️ The recording lists are named `inserted`/`thumbed` and **not** `inserts`/`thumbnails`, because
    `thumbnails` is a *method* on the client this stands in for — and a stub whose attribute shadows the method it
    is meant to provide fails in a way that reads as a bug in the code under test.
    """

    def __init__(self, video_id: str = VIDEO_ID) -> None:
        self.video_id = video_id
        self.inserted: list[dict] = []
        self.thumbed: list[dict] = []
        self.order: list[str] = []

    def videos(self):
        stub = self

        class _Videos:
            def insert(self, **kwargs):
                stub.order.append("insert")
                stub.inserted.append(kwargs)
                return _Upload({"id": stub.video_id})

        return _Videos()

    def thumbnails(self):
        stub = self

        class _Thumbnails:
            def set(self, **kwargs):
                stub.order.append("set")
                stub.thumbed.append(kwargs)
                return _Exec()

        return _Thumbnails()


class Repo(unittest.TestCase):
    """A real output folder in a temp root, a real manifest, and a stub API."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)

        self.directory = self.root / "output" / "brief" / DATE / LANG
        self.directory.mkdir(parents=True)
        self.write_manifest(MANIFEST)

        # ⚠️ The real artefacts, not stubs: `MediaFileUpload` opens the file, so a test that skipped them would be
        # testing an uploader that never touched the bytes it claims to send.
        (self.directory / MANIFEST["video"]).write_bytes(b"a picture with sound")
        (self.directory / MANIFEST["thumbnail"]).write_bytes(b"a still")

        # ⚠️ **Two seams, because there are two roots now.** `render.date_dir` reads the shared data root
        # (`paths.brief_output()`), while the snapshot still reads `store.root` — so patching only one of them
        # would leave the other pointed at the operator's real folders, and a test that "passes" while reading
        # yesterday's package is worse than one that fails.
        for patcher in (
            mock.patch.object(store, "root", return_value=self.root),
            mock.patch.object(paths, "data_root", return_value=self.root),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def write_manifest(self, data: dict) -> None:
        (self.directory / f"metadata-{LANG}.json").write_text(
            json.dumps(data, indent=2, sort_keys=True), encoding="utf-8"
        )

    def package_files(self) -> set[str]:
        return {path.name for path in self.directory.iterdir()}


class ThePayload(Repo):
    def test_the_manifest_is_what_is_sent(self):
        """⚠️ One source. A body built anywhere else is a description that can disagree with the video."""
        sent = publish.body(publish.payload(DATE, LANG), publish.DEFAULT_PRIVACY)
        self.assertEqual(sent["snippet"]["title"], MANIFEST["title"])
        self.assertEqual(sent["snippet"]["description"], MANIFEST["description"])
        self.assertEqual(sent["snippet"]["tags"], MANIFEST["tags"])

    def test_the_edition_declares_its_own_language(self):
        """⚠️ The title is mostly proper nouns — `NIFTY 50` and `BSE` are the same string in both editions — so
        nothing in the title tells YouTube which language this edition is."""
        self.assertEqual(publish.body(MANIFEST, "private")["snippet"]["defaultLanguage"], LANG)

    def test_the_category_is_the_one_the_disclosure_claims(self):
        self.assertEqual(publish.CATEGORY, "27")
        self.assertEqual(publish.body(MANIFEST, "private")["snippet"]["categoryId"], "27")

    def test_an_incomplete_package_is_refused(self):
        (self.directory / f"metadata-{LANG}.json").unlink()
        with self.assertRaises(publish.PublishError):
            publish.payload(DATE, LANG)

    def test_a_manifest_naming_a_missing_artefact_is_refused(self):
        """⚠️ A title with no video behind it is not a partial success, it is a broken one."""
        (self.directory / MANIFEST["video"]).unlink()
        with self.assertRaises(publish.PublishError):
            publish.payload(DATE, LANG)


class Privacy(Repo):
    def test_the_default_is_private(self):
        """⚠️ ADR 0004's real protection is the pre-publish list a human still walks. A schedule that posted to
        `public` would delete that check silently — this asserts the default rather than commenting on it."""
        self.assertEqual(publish.DEFAULT_PRIVACY, "private")

    def test_it_is_always_stated_explicitly(self):
        self.assertEqual(publish.body(MANIFEST, "private")["status"]["privacyStatus"], "private")
        self.assertEqual(publish.body(MANIFEST, "public")["status"]["privacyStatus"], "public")

    def test_it_is_not_for_children(self):
        self.assertFalse(publish.body(MANIFEST, "private")["status"]["selfDeclaredMadeForKids"])

    def test_an_unknown_privacy_is_refused(self):
        with self.assertRaises(publish.PublishError):
            publish.body(MANIFEST, "sort-of-private")


class TheScope(Repo):
    def test_it_is_upload_only(self):
        """⚠️ Not `youtube`, which would let this process read, edit and delete anything on the channel."""
        self.assertEqual(publish.SCOPE, "https://www.googleapis.com/auth/youtube.upload")


class TwicePosted(Repo):
    """⚠️ The reason this module has tests at all: a schedule runs this command again tomorrow, and again the day
    after, and a run that re-uploaded would be a second copy of the same brief on the channel."""

    def test_the_first_run_uploads_and_records_what_it_did(self):
        api = Stub()
        self.assertEqual(publish.run(DATE, (LANG,), privacy="private", force=False, api=api), 0)
        self.assertEqual(len(api.inserted), 1)
        self.assertEqual(len(api.thumbed), 1)

        recorded = publish.record(DATE, LANG)
        self.assertIsNotNone(recorded)
        self.assertEqual(recorded["video_id"], VIDEO_ID)
        self.assertEqual(recorded["url"], f"https://youtu.be/{VIDEO_ID}")
        self.assertEqual(recorded["bundle_hash"], MANIFEST["bundle_hash"])

    def test_a_second_run_over_the_same_bundle_uploads_nothing(self):
        publish.run(DATE, (LANG,), privacy="private", force=False, api=Stub())
        api = Stub()
        self.assertEqual(publish.run(DATE, (LANG,), privacy="private", force=False, api=api), 0)
        self.assertEqual(api.inserted, [], "the same bundle was posted twice")
        self.assertEqual(api.thumbed, [])

    def test_a_rebuilt_bundle_refuses_rather_than_posting_a_second_video(self):
        """⚠️ **The decision, not an oversight.** A rebuilt day means the numbers moved, and YouTube has no replace —
        uploading again would put two different briefs under one title, and a viewer would have no way to tell which
        is which. So this refuses and says how to proceed deliberately."""
        publish.run(DATE, (LANG,), privacy="private", force=False, api=Stub())
        changed = dict(MANIFEST, bundle_hash="b" * 64)
        self.write_manifest(changed)

        api = Stub()
        self.assertEqual(publish.run(DATE, (LANG,), privacy="private", force=False, api=api), 1)
        self.assertEqual(api.inserted, [])

    def test_force_uploads_again_on_request(self):
        publish.run(DATE, (LANG,), privacy="private", force=False, api=Stub())
        api = Stub(video_id="secondVideo")
        self.assertEqual(publish.run(DATE, (LANG,), privacy="private", force=True, api=api), 0)
        self.assertEqual(len(api.inserted), 1)
        self.assertEqual(publish.record(DATE, LANG)["video_id"], "secondVideo")

    def test_an_unreadable_record_is_refused_rather_than_guessed(self):
        """⚠️ The two guesses are "post it again" and "skip it silently", and each is wrong in a different,
        expensive way — so the run stops instead."""
        publish.run(DATE, (LANG,), privacy="private", force=False, api=Stub())
        publish.marker(DATE, LANG).write_text("{ not json", encoding="utf-8")

        api = Stub()
        self.assertEqual(publish.run(DATE, (LANG,), privacy="private", force=False, api=api), 1)
        self.assertEqual(api.inserted, [])


class ThePackageStaysClean(Repo):
    def test_the_record_is_not_written_into_the_package(self):
        """⚠️ `package.py` is explicit that a package holds four files and nothing else — a folder a viewer could be
        handed. The upload record is plumbing, so it lives in `output/brief/<date>/`, one level up."""
        publish.run(DATE, (LANG,), privacy="private", force=False, api=Stub())
        self.assertEqual(
            self.package_files(),
            {f"metadata-{LANG}.json", MANIFEST["video"], MANIFEST["thumbnail"]},
        )
        self.assertTrue(publish.marker(DATE, LANG).is_file())
        self.assertFalse(any(name.startswith(".published") for name in self.package_files()))


class TheOrder(Repo):
    def test_the_thumbnail_is_set_after_the_video_exists(self):
        """⚠️ A thumbnail cannot be attached to a video that does not exist yet, and the failure is confusing
        enough that the order is worth pinning."""
        api = Stub()
        publish.run(DATE, (LANG,), privacy="private", force=False, api=api)
        self.assertEqual(api.order, ["insert", "set"])
        self.assertEqual(api.thumbed[0]["videoId"], VIDEO_ID)


class DryRun(Repo):
    """⚠️ **The flag's whole value is that it is the same path with two statements removed.**

    A build-only install, a laptop with no credentials and no channel, an operator deciding whether the schedule is
    worth trusting — all of those need to see the upload without doing it. So this class tests two things at once,
    and they pull in opposite directions: that nothing is sent or recorded, and that *everything else* still runs.
    A rehearsal that passed where the real run would refuse would be worse than no rehearsal at all.
    """

    def rehearse(self, *, api=None, privacy: str = "private", force: bool = False):
        """Return `(exit code, stdout)` for a dry run. ⚠️ `api` defaults to `None` — no client at all."""
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = publish.run(
                DATE, (LANG,), privacy=privacy, force=force, api=api, dry_run=True
            )
        return code, buffer.getvalue()

    def test_it_needs_no_credentials_and_no_client(self):
        """⚠️ The state the operator is actually in on the first run: nothing authorised, nothing to send to."""
        with mock.patch.object(publish, "service") as client:
            code, shown = self.rehearse()
        self.assertEqual(code, 0)
        self.assertFalse(client.called, "a dry run built an authenticated client")
        self.assertIn("dry run", shown)

    def test_it_sends_nothing_and_records_nothing(self):
        api = Stub()
        code, _ = self.rehearse(api=api)
        self.assertEqual(code, 0)
        self.assertEqual(api.inserted, [], "a dry run sent the video")
        self.assertEqual(api.thumbed, [], "a dry run set the thumbnail")
        self.assertIsNone(publish.record(DATE, LANG), "a dry run wrote a publish record")
        self.assertFalse(publish.marker(DATE, LANG).exists())

    def test_it_reports_the_thumbnail_the_title_and_the_status(self):
        """⚠️ The point of the output: the four fields an operator is checking are the four that are shown."""
        _code, shown = self.rehearse(api=Stub())
        self.assertIn(MANIFEST["title"], shown)
        self.assertIn(MANIFEST["thumbnail"], shown)
        self.assertIn("category 27", shown)
        self.assertIn(f"language {LANG}", shown)
        self.assertIn(publish.DEFAULT_PRIVACY, shown)

    def test_it_reports_the_privacy_it_was_asked_for(self):
        """⚠️ `body` is shared with the real path, so the rehearsal cannot print a different request."""
        _code, shown = self.rehearse(api=Stub(), privacy="public")
        self.assertIn("public", shown)
        self.assertNotIn(publish.DEFAULT_PRIVACY, shown)

    def test_a_broken_package_is_refused_just_as_the_real_run_refuses_it(self):
        (self.directory / MANIFEST["video"]).unlink()
        code, _ = self.rehearse(api=Stub())
        self.assertEqual(code, 1)

    def test_a_rebuilt_bundle_refuses_exactly_as_the_real_run_does(self):
        publish.run(DATE, (LANG,), privacy="private", force=False, api=Stub())
        self.write_manifest(dict(MANIFEST, bundle_hash="b" * 64))
        code, _ = self.rehearse(api=Stub())
        self.assertEqual(code, 1)

    def test_an_edition_already_up_reports_the_skip_and_not_a_plan(self):
        """⚠️ **Parity, and it is deliberate.** The next real run would upload nothing here, so a rehearsal that
        printed an upload plan would promise something the schedule will not do."""
        publish.run(DATE, (LANG,), privacy="private", force=False, api=Stub())
        code, shown = self.rehearse(api=Stub())
        self.assertEqual(code, 0)
        self.assertIn("already published", shown)
        self.assertNotIn("dry run", shown)


class TheCredentials(Repo):
    """⚠️ **Every way `service` can fail has to be a refusal, because of *when* it fails.**

    The token is the likeliest thing to be wrong — a refresh token from an OAuth client still in *"Testing"* expires
    after seven days — and the upload path's first chance to notice is at the end of an hour-long build. The two
    libraries throw two different exception types at that code and neither is a `PublishError`, so the point of these
    tests is the module's own contract: *"A refusal, not a crash."*
    """

    def setUp(self) -> None:
        super().setUp()
        # ⚠️ The **real** `credentials_dir()` is `~/.config/market-overview`. Left unpatched, these tests would
        # write a token into the operator's own home — and read whatever happened to be there.
        self.credentials = self.root / "credentials"
        self.credentials.mkdir(parents=True, exist_ok=True)
        enter = mock.patch.object(publish, "credentials_dir", return_value=self.credentials)
        enter.start()
        self.addCleanup(enter.stop)

    def token(self, **fields) -> pathlib.Path:
        path = self.credentials / publish.TOKEN
        path.write_text(json.dumps(fields), encoding="utf-8")
        return path

    def test_a_missing_token_is_a_refusal_that_names_the_fix(self):
        with self.assertRaises(publish.PublishError) as caught:
            publish.service()
        self.assertIn("--authorise", str(caught.exception))

    def test_a_rejected_refresh_token_refuses_rather_than_tracebacking(self):
        """⚠️ `RefreshError` is **not** a `PublishError` — google-auth's own hierarchy — so nothing catches it by
        accident. This is the test that says the tool catches it deliberately, and it is the failure mode the
        README calls the likeliest way a schedule dies."""
        self.token(refresh_token="a refresh token")
        stale = mock.Mock(expired=True, refresh_token="a refresh token")
        stale.refresh.side_effect = publish.RefreshError("invalid_grant: Token has been expired or revoked")

        with mock.patch.object(publish, "Credentials") as credentials:
            credentials.from_authorized_user_file.return_value = stale
            with self.assertRaises(publish.PublishError) as caught:
                publish.service()

        self.assertIn("invalid_grant", str(caught.exception))
        self.assertIn("--authorise", str(caught.exception))

    def test_a_file_that_is_not_a_token_refuses_rather_than_tracebacking(self):
        self.token(refresh_token="a refresh token")
        with mock.patch.object(publish, "Credentials") as credentials:
            credentials.from_authorized_user_file.side_effect = ValueError("not a JSON token")
            with self.assertRaises(publish.PublishError) as caught:
                publish.service()
        self.assertIn("--authorise", str(caught.exception))

    def test_a_live_token_is_used_without_being_refreshed(self):
        self.token(refresh_token="a refresh token")
        live = mock.Mock(expired=False, refresh_token="a refresh token")

        with mock.patch.object(publish, "Credentials") as credentials, mock.patch.object(
            publish, "build"
        ) as built:
            credentials.from_authorized_user_file.return_value = live
            publish.service()

        self.assertFalse(live.refresh.called, "a token that had not expired was refreshed anyway")
        # ⚠️ `cache_discovery=False` is what keeps `build` off the network — it is not a performance flag here.
        self.assertEqual(
            built.call_args.kwargs, {"credentials": live, "cache_discovery": False}
        )

    def test_a_refreshed_token_is_written_back(self):
        """⚠️ Google rotates refresh tokens. A machine that discards the new one keeps working right up until the
        moment it stops, with nothing in between to warn anyone."""
        path = self.token(refresh_token="a refresh token")
        stale = mock.Mock(expired=True, refresh_token="a refresh token")
        stale.to_json.return_value = '{"refresh_token": "rotated"}'

        with mock.patch.object(publish, "Credentials") as credentials, mock.patch.object(publish, "build"):
            credentials.from_authorized_user_file.return_value = stale
            publish.service()

        self.assertIn("rotated", path.read_text(encoding="utf-8"))

    def test_check_reports_a_working_token_and_exits_zero(self):
        stream = io.StringIO()
        with mock.patch.object(publish, "service"), contextlib.redirect_stdout(stream):
            code = publish.check()
        self.assertEqual(code, 0)
        self.assertIn("credentials OK", stream.getvalue())

    def test_check_reports_a_broken_token_instead_of_raising(self):
        """⚠️ An exit code, not a traceback — a caller's only way to say "this did not happen" is its exit code, and
        `check`'s whole job is to be the cheap early warning for the expensive failure."""
        stream = io.StringIO()
        broken = publish.PublishError("the token at … was rejected (invalid_grant)")
        with mock.patch.object(publish, "service", side_effect=broken), contextlib.redirect_stderr(stream):
            code = publish.check()
        self.assertEqual(code, 1)
        self.assertIn("invalid_grant", stream.getvalue())


class WithoutTheLibraries(Repo):
    def test_a_build_only_install_gets_a_refusal_not_a_traceback(self):
        """⚠️ The client libraries are an optional extra, so this is a state an operator can genuinely be in."""
        with mock.patch.object(publish, "AVAILABLE", False):
            with self.assertRaises(publish.PublishError) as caught:
                publish.service()
        self.assertIn("uv sync --extra publish", str(caught.exception))

    def test_uploading_without_them_refuses_rather_than_crashing(self):
        with mock.patch.object(publish, "AVAILABLE", False):
            self.assertEqual(publish.run(DATE, (LANG,), privacy="private", force=False, api=Stub()), 1)


if __name__ == "__main__":
    unittest.main()


