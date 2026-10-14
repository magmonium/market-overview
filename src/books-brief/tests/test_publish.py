"""Ticket 24 — the publish target, and the two refusals that make it safe to re-run.

⚠️ **Everything here runs against a stub**, and that is the design rather than a testing convenience. An uploader whose
only entry point is a live API with real credentials behind it is an uploader that quietly stops being tested — so
`upload` takes its client as a **parameter** and `run` builds one lazily, which means the whole module is reachable
without a token, a channel or a network.
"""
import json
import pathlib
import unittest
from unittest import mock

from books_brief import package, paths, publish

from support import temporary_store

WEEK = "2026-W41"
CHART = "bengali"


def a_package(root: pathlib.Path, *, bundle_hash: str = "aaa111") -> pathlib.Path:
    """A finished package on disk — the four files `package.assemble` would have written.

    ⚠️ **`exist_ok=True`, and the second call is the point.** The rebuilt-week test calls this again on the same folder
    with a different hash, which is exactly what a rebuild does — and the first version of this helper could not express
    that, so the test failed on its own fixture rather than on the behaviour it was checking.
    """
    directory = root / "output" / "books" / WEEK / CHART
    directory.mkdir(parents=True, exist_ok=True)
    names = package.filenames(WEEK, CHART)

    (directory / names["video"]).write_bytes(b"x" * 2048)
    (directory / names["thumbnail"]).write_bytes(b"y" * 1024)
    (directory / names["text"]).write_text("the human's half")
    (directory / names["json"]).write_text(
        json.dumps(
            {
                "title": "Top 100 Bengali Books | Week 41",
                "description": "Ranked on sales and reviews over six months\n",
                "tags": ["bengali books", "top 100"],
                "hashtags": ["#books"],
                "video": names["video"],
                "thumbnail": names["thumbnail"],
                "bundle_hash": bundle_hash,
                "language": "bn",
            }
        )
    )
    return directory


class TheManifestIsTheInput(unittest.TestCase):
    def test_a_package_with_no_manifest_is_refused(self):
        """⚠️ **The manifest is the completion marker, so its absence is the same fact as an unfinished package.**

        `package.assemble` writes it last, after refusing to describe artefacts that are not there — so an uploader that
        went looking for the filenames anyway would be guessing at what to send, from a folder that says it is not ready.
        """
        with temporary_store() as root:
            with mock.patch.object(paths, "data_root", return_value=root):
                (root / "output" / "books" / WEEK / CHART).mkdir(parents=True)

                with self.assertRaises(publish.PublishError) as raised:
                    publish.manifest(WEEK, CHART)

        self.assertIn("not finished", str(raised.exception))

    def test_the_body_is_read_from_the_manifest_and_not_re_derived(self):
        """⚠️ **There is no second description of the chart anywhere in this module.**

        Every string the API is told comes out of `metadata-<chart>.json`, which was generated from the week's bundle —
        so the upload cannot disagree with the video. That is the same property `package.assemble` protects when it
        refuses to write text about artefacts that are not there.
        """
        with temporary_store() as root:
            with mock.patch.object(paths, "data_root", return_value=root):
                a_package(root)
                sent = publish.body(publish.manifest(WEEK, CHART), "private")

        self.assertEqual(sent["snippet"]["title"], "Top 100 Bengali Books | Week 41")
        self.assertEqual(sent["snippet"]["tags"], ["bengali books", "top 100"])
        self.assertEqual(sent["snippet"]["defaultLanguage"], "bn")
        self.assertEqual(sent["status"]["privacyStatus"], "private")

    def test_a_privacy_that_is_not_a_privacy_is_refused(self):
        """⚠️ A typo must not reach the API as an unknown status, where the failure would be a rejected upload after an
        hour of rendering rather than a complaint before one.
        """
        with self.assertRaises(publish.PublishError):
            publish.body({"title": "t"}, "sort-of-private")


class TheMarker(unittest.TestCase):
    def test_the_marker_lives_in_the_package_because_that_is_what_persists(self):
        """⚠️ Ticket 10: *"`output/books/` must persist across runs — that is where the published-marker lives, and an
        ephemeral `output/` re-uploads the week on every firing."*

        ⚠️ And it is deliberately **not** in `store/`: the store is the week's *evidence*, and what went up on YouTube is
        not evidence about the chart.
        """
        with temporary_store() as root:
            with mock.patch.object(paths, "data_root", return_value=root):
                a_package(root)
                path = publish.remember(WEEK, CHART, "abc123", "private", "aaa111")

                self.assertEqual(path, package.dir_for(WEEK, CHART) / publish.MARKER)
                self.assertEqual(
                    publish.record(WEEK, CHART)["url"], "https://youtu.be/abc123"
                )

    def test_a_marker_that_will_not_parse_reads_as_never_uploaded(self):
        """⚠️ **Recoverable beats correct here, and it is a deliberate choice.**

        A half-written marker is impossible — `remember` writes atomically — but if one ever appeared, treating it as an
        error would block the week permanently. Uploading again is recoverable; refusing forever is not.
        """
        with temporary_store() as root:
            with mock.patch.object(paths, "data_root", return_value=root):
                a_package(root)
                publish.marker(WEEK, CHART).write_text("{ not json")

                self.assertIsNone(publish.record(WEEK, CHART))


class PublishingAWeek(unittest.TestCase):
    """⚠️ Ticket 10's idempotence, and the two refusals are **different facts** — which is why they are worded apart.

    *Already up from this bundle* is a re-run and posts nothing. *Already up from a different bundle* means the week was
    **rebuilt**, and the run refuses: two different charts under one title is not a duplicate, it is a contradiction.
    """

    def _publish(self, root: pathlib.Path, **kwargs: object):
        """Run `publish.run` with the client stubbed — so nothing here needs a token, a channel or a network.

        ⚠️ **The record is read *inside* the patch, and that is not tidiness.** The first version of this helper returned
        only the exit code, so the assertions read `publish.record` after the temporary root had been unpatched — and
        they read the *real* data root, found no marker, and failed with a `NoneType` error that looked like a bug in
        `record` rather than in the test.
        """
        with mock.patch.object(paths, "data_root", return_value=root):
            with mock.patch.object(publish, "service", return_value=mock.Mock()):
                with mock.patch.object(publish, "upload", return_value="vid123") as upload:
                    code = publish.run(WEEK, [CHART], **kwargs)  # type: ignore[arg-type]
                    recorded = publish.record(WEEK, CHART)
        return code, upload, recorded

    def test_a_first_run_uploads_and_records_the_bundle_it_came_from(self):
        with temporary_store() as root:
            a_package(root, bundle_hash="aaa111")
            code, upload, recorded = self._publish(root)

            self.assertEqual(code, 0)
            self.assertEqual(upload.call_count, 1)
            self.assertEqual(recorded["bundle_hash"], "aaa111")
            self.assertEqual(recorded["video_id"], "vid123")

    def test_a_re_run_of_the_same_bundle_posts_nothing(self):
        """⚠️ **The half that makes *"just run it again"* free** — every other step of this pipeline is re-runnable, so
        an uploader that re-uploaded on every run would be the one place where re-running costs something irreversible.
        """
        with temporary_store() as root:
            a_package(root, bundle_hash="aaa111")
            self._publish(root)

            code, upload, _ = self._publish(root)

            self.assertEqual(code, 0)
            self.assertEqual(upload.call_count, 0, "a re-run must not upload again")

    def test_a_rebuilt_week_refuses_rather_than_posting_a_second_chart(self):
        """⚠️ **The refusal worth having.** The bundle changed, so the chart under that title is no longer the chart
        YouTube holds — and publishing would leave two different Top 100s sharing one title with nothing to say which is
        which.
        """
        with temporary_store() as root:
            a_package(root, bundle_hash="aaa111")
            self._publish(root)

            # The week is rebuilt: same folder, different evidence.
            a_package(root, bundle_hash="bbb222")

            code, upload, recorded = self._publish(root)

            self.assertEqual(code, 1, "a rebuilt week must refuse")
            self.assertEqual(upload.call_count, 0)
            # ⚠️ And the **first** upload's record is left alone: a refusal that rewrote the marker would erase the only
            # note of which video is up there.
            self.assertEqual(recorded["bundle_hash"], "aaa111")

    def test_a_dry_run_sends_nothing_and_records_nothing(self):
        """⚠️ **The same path, not a parallel one.** A rehearsal that took a different route would only prove something
        about the rehearsal — so `--dry-run` builds the real request body and reports it, and stops one line short.
        """
        with temporary_store() as root:
            a_package(root, bundle_hash="aaa111")

            code, upload, recorded = self._publish(root, dry_run=True)

            self.assertEqual(code, 0)
            self.assertEqual(upload.call_count, 0)
            self.assertIsNone(recorded)

    def test_a_week_where_every_chart_is_already_up_never_builds_a_client(self):
        """⚠️ **A re-run must not touch the network at all** — not even to construct a client — because the commonest
        reason to run `publish` twice is that nothing changed.
        """
        with temporary_store() as root:
            a_package(root, bundle_hash="aaa111")
            self._publish(root)

            with mock.patch.object(paths, "data_root", return_value=root):
                with mock.patch.object(publish, "service") as service:
                    self.assertEqual(publish.run(WEEK, [CHART]), 0)

            service.assert_not_called()


    def test_a_week_with_nothing_to_publish_refuses_rather_than_succeeding_quietly(self):
        """⚠️ **A defect a smoke run found, not a test.**

        `bb publish --week 2026-W52` on a week that was never built printed nothing and exited **zero** — which on a
        timer reads as *"the week went up"* rather than *"the week was never built"*. ⚠️ Ticket 10: a refusal **exits
        non-zero and writes nothing**, and this is the case where silence is indistinguishable from success.

        ⚠️ And it cannot fire on a healthy re-run: a week that *was* built has packages on disk, so the list is
        non-empty and each chart reports *already up* on its own line.
        """
        with temporary_store() as root:
            with mock.patch.object(paths, "data_root", return_value=root):
                self.assertEqual(publish.run(WEEK, ()), 1)


class WhichChartsToPublish(unittest.TestCase):
    def test_the_week_is_read_off_the_disk_and_not_off_the_declaration_table(self):
        """⚠️ **Ticket 13's partial delivery, seen from the uploader.** A week may hold three charts and not four, so a
        run that walked `charts.ALL` would try to publish a chart nobody built — and refuse the whole week for it.
        """
        with temporary_store() as root:
            with mock.patch.object(paths, "data_root", return_value=root):
                a_package(root)
                # A folder that is not a finished package — the chart the run died on.
                (root / "output" / "books" / WEEK / "comics").mkdir(parents=True)

                self.assertEqual(publish.charts_in(WEEK), (CHART,))

    def test_a_week_that_was_never_built_offers_nothing(self):
        with temporary_store() as root:
            with mock.patch.object(paths, "data_root", return_value=root):
                self.assertEqual(publish.charts_in(WEEK), ())


class TheSharedCredentials(unittest.TestCase):
    """⚠️ **Ticket 24's sharpest decision, and it is one import.** The token, the scope and the consent flow are the
    brief's — so the operator authorises **once** for both products, and `bb publish` has no `--authorise` of its own.
    """

    def test_the_scope_is_the_narrow_one_the_brief_already_uses(self):
        """⚠️ `youtube.upload` and nothing else: not `youtube` (read+write over the whole account), not
        `youtube.force-ssl`. A wider token could do more than the tool can, which is a liability with no upside.
        """
        self.assertEqual(publish.SCOPE, "https://www.googleapis.com/auth/youtube.upload")

    def test_the_token_is_the_briefs_own_file(self):
        """⚠️ **One token, one expiry, one place to re-authorise.** A second credentials directory would mean two tokens
        for one permission, expiring independently — and the README's likeliest way a schedule dies is a token nobody
        renewed.
        """
        from market_overview.publish import credentials_dir

        # ⚠️ Asserted as **two functions returning the same place**, not as one name pointing at the other: an alias
        # would make this pass even if the brief later moved its credentials, which is the thing worth noticing.
        self.assertEqual(publish.credentials_dir(), credentials_dir())
        self.assertEqual(publish.TOKEN, "token.json")
        self.assertEqual(publish.CLIENT_SECRET, "client-secret.json")

    def test_the_default_privacy_is_private(self):
        """⚠️ ADR 0006: *"Uploading straight to `public` on a timer deletes that check without saying so."* The books
        equivalent is the check this whole map was built toward — is the Bengali chart actually Bengali, are the covers
        the right books, is the rank plausible, does the footer name the right sources.
        """
        self.assertEqual(publish.DEFAULT_PRIVACY, "private")
        self.assertNotEqual(publish.DEFAULT_PRIVACY, "public")


if __name__ == "__main__":
    unittest.main()


