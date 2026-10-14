"""Ticket 05 — the cover pipeline's URLs and its cache.

⚠️ **Three normalisations, and two of them are visible defects if missed.** Google Books hands back `http://` URLs
carrying `edge=curl`, which draws a decorative curled page-corner into the image, at a `zoom` too small to sit on a
slide. So the raw URL is never used as given.

⚠️ **Open Library is the fallback, and it returns a *blank image* for a cover it does not have** — which would render
silently as an empty tile. `?default=false` turns that into a 404 the run can see, which is the difference between a
missing cover and a cover that looks like a design choice.
"""
import contextlib
import hashlib
import pathlib
import tempfile
import unittest
import urllib.error
import urllib.request
from unittest import mock

from books_brief import covers, paths


class TheGoogleBooksUrl(unittest.TestCase):
    def test_the_raw_url_is_upgraded_de_curled_and_enlarged(self):
        """⚠️ Ticket 05's three normalisations, each a named trap.

        The URL below is the shape Google Books actually returns: `http`, `zoom=1`, and `edge=curl`.
        """
        raw = (
            "http://books.google.com/books/content?id=abc&printsec=frontcover"
            "&img=1&zoom=1&edge=curl&source=gbs_api"
        )

        url = covers.google_books_url(raw)

        self.assertTrue(url.startswith("https://"), "http would be mixed content")
        self.assertNotIn("edge=curl", url, "the curled corner is drawn into the image")
        self.assertIn("zoom=2", url, "the default thumbnail is too small for a slide")


class TheOpenLibraryUrl(unittest.TestCase):
    def test_a_missing_cover_404s_rather_than_rendering_blank(self):
        """⚠️ Ticket 05 — Open Library answers a cover it does not have with a **blank image**, not an error.

        Rendered, that is an empty tile nobody notices. `?default=false` makes it a 404, so the run can tell the
        difference between *no cover* and *a cover that is a white rectangle*.
        """
        self.assertEqual(
            covers.open_library_url("9788172151234"),
            "https://covers.openlibrary.org/b/isbn/9788172151234-L.jpg?default=false",
        )


class WhereACoverIsKept(unittest.TestCase):
    def test_a_cover_is_cached_under_its_isbn(self):
        """⚠️ Ticket 05 — keyed by **ISBN, not by week**.

        A cover is immutable per ISBN, so one fetch serves every chart and every week the title appears in. That is
        what makes the superset's repetition (ticket 14) free rather than duplicated.
        """
        self.assertEqual(covers.path_for("9788172151234").name, "9788172151234.jpg")


class TheSourceOrder(unittest.TestCase):
    def test_google_books_wins_when_the_volume_carried_a_cover(self):
        """⚠️ Ticket 05 — *"Source order: **Google Books `imageLinks`** first… then **Open Library** as the fallback."*

        ⚠️ **And the volume is already in hand**, which is why it is first rather than merely preferred: identity
        resolution had to read it to turn a title into an ISBN (ticket 05 §3), so its cover costs no extra request.

        ⚠️ The chosen URL is the **normalised** one — picking the source and fixing the source are the same decision,
        and a caller that had to remember to call `google_books_url` as well would eventually not.
        """
        raw = (
            "http://books.google.com/books/content?id=abc&printsec=frontcover"
            "&img=1&zoom=1&edge=curl&source=gbs_api"
        )

        chosen = covers.url_for("9788172151234", google=raw)

        self.assertTrue(chosen.startswith("https://"), "http would be mixed content")
        self.assertIn("zoom=2", chosen, "the default thumbnail is too small for a slide")
        self.assertNotIn("edge=curl", chosen, "the curled corner is drawn into the image")

    def test_open_library_is_the_fallback_when_there_is_no_google_cover(self):
        """The ordinary case for a title Google Books knows but has not scanned."""
        self.assertEqual(
            covers.url_for("9788172151234"), covers.open_library_url("9788172151234")
        )

    def test_an_empty_google_url_is_the_same_as_no_google_url(self):
        """⚠️ **A vendor answering `""` must not produce a cover *of nothing*.**

        Google Books omits `imageLinks` on plenty of volumes, and a client that normalised the omission to an empty
        string would send this function down the Google branch with a URL of `""`. That is not a 404 — it is a request
        to nowhere, and it would surface as a fetch error rather than as *this title has no cover*.
        """
        self.assertEqual(
            covers.url_for("9788172151234", google=""),
            covers.open_library_url("9788172151234"),
        )


class TheCoverRecord(unittest.TestCase):
    def test_a_cover_records_where_it_came_from_and_what_it_was(self):
        """⚠️ Ticket 05 — *"the snapshot records where the cover came from — the source URL and a content hash."*

        ⚠️ **That pairing is what keeps a rebuild possible without committing hundreds of images a week**: the
        *evidence* is committed, the *bytes* are cached. A URL alone would not say whether the file still on disk is the
        one the chart was built from — a publisher can re-issue a cover under the same URL, and the snapshot has to be
        able to notice.
        """
        record = covers.Cover(url="https://example.test/c.jpg", sha256="abc123")

        self.assertEqual(record.url, "https://example.test/c.jpg")
        self.assertEqual(record.sha256, "abc123")


class DownloadingACover(unittest.TestCase):
    """Ticket 05 §1 — the bytes, the hash, and the cache keyed by ISBN."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name)

        patcher = mock.patch.object(paths, "data_root", return_value=self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    @contextlib.contextmanager
    def _serving(self, body: bytes | None):
        """A `urlopen` that answers with `body`, or 404s when it is `None` — and **counts the calls**."""
        calls = []

        def opener(url, timeout=None):  # noqa: ANN001, ARG001 - mirrors `urlopen`'s signature
            calls.append(url)
            if body is None:
                raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)  # type: ignore[arg-type]
            # ⚠️ Returned directly, not wrapped in `contextlib.closing` — `_Response` is already a context manager, and
            # the wrapper would call a `close()` it does not have. That is the bug this line had first.
            return _Response(body)

        with mock.patch.object(urllib.request, "urlopen", opener):
            yield calls

    def test_the_bytes_are_cached_under_the_isbn_and_hashed(self):
        """⚠️ **The cache key is the ISBN and the record's hash is of the bytes** — and both halves matter.

        The ISBN key is what makes the superset free (ticket 14): one fetch serves every chart and every week the title
        appears in. ⚠️ The hash is what makes the *evidence* checkable: a publisher can re-issue a cover under the same
        URL, so a snapshot holding only the URL could not tell a rebuild that the image had changed underneath it.
        """
        with self._serving(b"\x89PNG a cover"):
            record = covers.download(covers.open_library_url("9788172151234"), "9788172151234")

        assert record is not None
        self.assertEqual(record.sha256, hashlib.sha256(b"\x89PNG a cover").hexdigest())
        self.assertEqual(
            covers.path_for("9788172151234").read_bytes(), b"\x89PNG a cover"
        )

    def test_a_cover_that_does_not_exist_is_none_and_never_an_empty_file(self):
        """⚠️ **A 404 is the *designed* answer, not an error** — and `?default=false` is what makes it one.

        Open Library answers a cover it does not have with a **blank image** unless asked otherwise, which would render
        silently as an empty tile. With `default=false` the absence is a 404, the run records `cover: null`, and ticket
        07's branded tile draws — *"a missing cover is a designed state, not a hole."*

        ⚠️ And nothing is written to the cache: an empty file there would be a cover that exists and is blank, which is
        the one state the pipeline could not tell from a real one.
        """
        with self._serving(None):
            record = covers.download(covers.open_library_url("9788172151234"), "9788172151234")

        self.assertIsNone(record)
        self.assertFalse(covers.path_for("9788172151234").exists())

    def test_a_cover_already_cached_is_not_fetched_again(self):
        """⚠️ Ticket 05 — *"a cover is immutable per ISBN, so it is fetched once and reused forever."*

        ⚠️ This is not an optimisation. Open Library allows **100 requests per IP per 5 minutes**, and a hundred-cover
        chart fetched twice would spend a fifth of that budget re-downloading images already on disk — on a run that
        then needs the remaining budget for the covers it does not have.
        """
        cache = covers.path_for("9788172151234")
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(b"already here")

        with self._serving(b"a different cover") as calls:
            record = covers.download(covers.open_library_url("9788172151234"), "9788172151234")

        self.assertEqual(calls, [], "the cache must answer before the network does")
        assert record is not None
        self.assertEqual(record.sha256, hashlib.sha256(b"already here").hexdigest())


class _Response:
    """The two methods `download` uses, and nothing else — a `urlopen` stand-in rather than a real response."""

    def __init__(self, body: bytes):
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *_: object) -> None:
        return None


if __name__ == "__main__":
    unittest.main()
