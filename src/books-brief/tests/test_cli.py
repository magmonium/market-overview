"""Ticket 18 — the conductor, and the refusal that protects the product.

⚠️ **A chart whose sources failed is an absent key, and a week where *every* chart is absent has nothing to publish.**
The brief's rule — *"every refusal exits non-zero and writes nothing"* — is what stops a half-built week reaching the
store, where a later run would read it back as if it were real.
"""
import contextlib
import io
import pathlib
import unittest
from unittest import mock

from books_brief import charts, cli, corroborate, covers, enrich, facts, identity, paths, prices, rank, render, store, ticker, window
from books_brief import fetch
from books_brief.fetch import google_books
from market_overview import audio

from support import temporary_store


def row(list_slug: str, published: str, rank: int = 1) -> corroborate.Row:
    """One source row, dated — the shape every client has to produce."""
    return corroborate.Row(
        list=list_slug,
        rank=rank,
        isbn="9788172151234",
        title="Ekti Shonar Boi",
        published=published,
    )


def snapshot(week: str = "2026-W41") -> dict:
    """A week's snapshot with one row, so a run can be driven without a network."""
    books = enrich.build(
        (rank.Ranked(key="9788172151234", isbn="9788172151234", rank=1, weeks_on_chart=0, is_new=False, score=1.4),),
        details={"9788172151234": enrich.Details(title="Ekti Shonar Boi")},
        previous=None,
    )
    return facts.build(week, charts={"bengali": facts.Chart(books=books)}, window_weeks=7)


class WhenNothingCouldBeBuilt(unittest.TestCase):
    def test_a_week_with_no_charts_refuses_and_writes_no_snapshot(self):
        """⚠️ Ticket 18 — *"if every chart is absent, the run refuses and writes nothing."*

        ⚠️ **"Writes nothing" is the load-bearing half.** A snapshot *is* the replay path, so a week written empty would
        be read back later as a real week containing no charts — and because the snapshot's existence is the switch, the
        next run would refuse to fetch. A refusal that left a file behind would be worse than no run at all.
        """
        empty = {"meta": {"week": "2026-W41"}, "charts": {}}

        with temporary_store() as root:
            with mock.patch.object(cli, "gather", return_value=empty):
                self.assertEqual(cli.build("2026-W41"), 1)

            self.assertFalse((root / "store" / "2026-W41" / "facts.json").exists())


class TheEnrichmentLookup(unittest.TestCase):
    """Ticket 05 §3 — and the rule that matters is that **a failed lookup costs fields, never a row.**"""

    def setUp(self) -> None:
        """⚠️ **The network is closed by default here, because `covers.url_for` is total now.**

        Every title reaches `covers.download` — `url_for` always names a source and its last resort is Open Library —
        so a test that forgot to patch it would not fail. It would make a real request, get a 404, and pass. ⚠️ That is
        the worst kind of green: a suite that is slow, order-dependent and secretly online, which is exactly what this
        suite is built not to be. So the default is *no cover*, and the tests that care override it with their own
        `mock.patch.object(covers, "download", return_value=record)` — the inner patch wins.
        """
        patcher = mock.patch.object(covers, "download", return_value=None)
        self.addCleanup(patcher.stop)
        patcher.start()

    def _admitted(self, *titles: tuple[str, str, str]) -> corroborate.Result:
        """Admitted titles as `(isbn, title, author)` triples — the three fields ticket 17's priority decides."""
        return corroborate.Result(
            admitted=tuple(
                corroborate.Title(
                    # ⚠️ The **real** work key, from the same function the gate uses (ticket 32) — so a test that
                    # goes through the conductor exercises the identity the conductor would actually see.
                    key=identity.work(title, author),
                    isbn=isbn,
                    title=title,
                    sources=("nyt/hardcover-fiction",),
                    author=author,
                )
                for isbn, title, author in titles
            ),
            parked=(),
        )

    def _volume(self, **over: object) -> google_books.Volume:
        base = {
            "isbn": "9788172151234",
            "title": "Ekti Shonar Boi",
            "author": "Sunil Gangopadhyay",
            "publisher": "Ananda Publishers",
            "published": "2026-10",
            "category": "Fiction / Literary",
            "cover_url": None,
        }
        return google_books.Volume(**{**base, **over})  # type: ignore[arg-type]

    def _listing(self, *, cover_url: str) -> corroborate.Result:
        """One admitted title whose **list carried an image** — which is every Amazon.in row.

        ⚠️ `_admitted` above cannot express this: it builds a `Title` with no `cover_url`, and the whole point of the
        case is that the list handed over a picture before enrichment ever ran.
        """
        return corroborate.Result(
            admitted=(
                corroborate.Title(
                    key=identity.work("Ekti Shonar Boi"),
                    isbn="9788172151234",
                    title="Ekti Shonar Boi",
                    sources=("amazon-in/indian-languages",),
                    cover_url=cover_url,
                ),
            ),
            parked=(),
        )

    def test_a_title_the_enrichment_source_does_not_know_still_gets_a_row(self):
        """⚠️ **The rule that stops the chart being quietly short.**

        Google Books has never heard of plenty of Bengali titles. Dropping the row would leave a chart that claims to
        rank a list and silently holds fewer books than it — the failure that looks like a thin week rather than like a
        bug. So the row survives carrying only what the list said, and its fields **omit** (ticket 07).
        """
        with mock.patch.object(google_books, "fetch", return_value=None):
            details = cli._details(self._admitted(("9788172151234", "Ekti Shonar Boi", "")))

        self.assertEqual(details[identity.work("Ekti Shonar Boi")].title, "Ekti Shonar Boi")
        self.assertEqual(details[identity.work("Ekti Shonar Boi")].publisher, "")
        self.assertIsNone(details[identity.work("Ekti Shonar Boi")].cover)

    def test_a_lookup_that_raises_does_not_lose_the_row_either(self):
        """⚠️ A timeout is the *source being unreachable*, not the book being absent — and the run's answer to both is
        the same: the field omits. ⚠️ It is **not** the chart's spine rule (ticket 18): that is about a *chart* vendor
        going down, and enrichment is not a chart source at all (ticket 02).
        """
        with mock.patch.object(google_books, "fetch", side_effect=TimeoutError("no answer")):
            details = cli._details(self._admitted(("9788172151234", "Ekti Shonar Boi", "")))

        self.assertEqual(details[identity.work("Ekti Shonar Boi")].title, "Ekti Shonar Boi")

    def test_the_lists_own_cover_survives_a_lookup_that_answered_nothing(self):
        """⚠️ **The list's image is not Google's to withhold** — and this is a keyless run's whole cover story.

        An Amazon.in row arrives with its picture already in hand, so a lookup that answers nothing costs the *volume's*
        fields and nothing else. ⚠️ The loop used to `continue` **before** the cover was ever read, so the image the list
        had already handed over was dropped on the way past — and the row fell to ticket 07's branded tile for a reason
        that had nothing to do with the cover.
        """
        record = covers.Cover(url="https://m.media-amazon.com/x.jpg", sha256="abc123")

        with (
            mock.patch.object(google_books, "fetch", return_value=None),
            mock.patch.object(covers, "download", return_value=record) as download,
        ):
            details = cli._details(self._listing(cover_url=record.url))

        self.assertEqual(details[identity.work("Ekti Shonar Boi")].cover, record)
        download.assert_called_once_with(record.url, "9788172151234")

    def test_the_lists_own_cover_survives_a_lookup_that_raised(self):
        """⚠️ The same rule for a **429**, which is the live case rather than a hypothetical.

        *The source being unreachable* is not *this book has no cover* — and the anonymous Google Books quota answers a
        full chart with 429s, every one of them on a row that has a cover sitting in `title.cover_url`.
        """
        record = covers.Cover(url="https://m.media-amazon.com/x.jpg", sha256="abc123")

        with (
            mock.patch.object(google_books, "fetch", side_effect=TimeoutError("no answer")),
            mock.patch.object(covers, "download", return_value=record),
        ):
            details = cli._details(self._listing(cover_url=record.url))

        self.assertEqual(details[identity.work("Ekti Shonar Boi")].cover, record)
        # ⚠️ And the row is still the list's row — a cover is not a licence to invent the rest of the fields.
        self.assertEqual(details[identity.work("Ekti Shonar Boi")].title, "Ekti Shonar Boi")

    def test_a_title_with_no_image_anywhere_falls_back_to_open_library(self):
        """⚠️ **The terminal fallback — and it is the only source left on a spent quota.**

        No list image and no volume means the two sources above Open Library have nothing to offer. ⚠️ That is the
        ordinary state of an NYT, indie or Rokomari row on a day Google Books answers `429 Quota exceeded … Queries per
        day` — and before this, `covers.url_for` was reached by **nobody**: the fallback existed, was tested, and could
        not run. So every one of those rows fell to ticket 07's branded tile while a working source sat unused.
        """
        with mock.patch.object(google_books, "fetch", return_value=None):
            details = cli._details(self._admitted(("9788172151234", "Ekti Shonar Boi", "")))

        covers.download.assert_called_once_with(
            covers.open_library_url("9788172151234"), "9788172151234"
        )
        # ⚠️ And the cover is still **null** unless the bytes arrived: a URL is not a cover (ticket 05), so the row
        # takes ticket 07's branded tile rather than claiming an image the cache does not hold.
        self.assertIsNone(details[identity.work("Ekti Shonar Boi")].cover)

    def test_the_lists_title_wins_over_the_enrichments(self):
        """⚠️ **Ticket 17's per-field priority, and it is not a nicety.**

        The title and the author come from *"the vendor that published the list the title ranked on"*. A chart that
        printed the volume's title would be contradicting the list it claims to rank — and the reader, who can see the
        list, would be looking at two different names for one book.
        """
        with mock.patch.object(
            google_books, "fetch", return_value=self._volume(title="A Different Title")
        ):
            details = cli._details(self._admitted(("9788172151234", "Ekti Shonar Boi", "")))

        self.assertEqual(details[identity.work("Ekti Shonar Boi")].title, "Ekti Shonar Boi")
        # ⚠️ And the fields the priority table *does* give Google Books come through untouched.
        self.assertEqual(details[identity.work("Ekti Shonar Boi")].publisher, "Ananda Publishers")
        self.assertEqual(details[identity.work("Ekti Shonar Boi")].published, "2026-10")

    def test_a_cover_url_with_no_bytes_leaves_the_row_without_a_cover(self):
        """⚠️ **A URL is not a cover** — and this is the invariant `stage.covers` refuses on.

        A `Details` whose cover was set from a URL alone would put a row in the snapshot claiming a cover the cache does
        not hold. ⚠️ A render taught us exactly what happens next: the composition requests the file, Remotion's `<Img>`
        gets a 404, and **the whole render is cancelled**. So the record is set only when the bytes are on disk, and a
        cover that will not download is the branded tile (ticket 07).
        """
        with (
            mock.patch.object(
                google_books,
                "fetch",
                return_value=self._volume(cover_url="https://example.test/c.jpg"),
            ),
            mock.patch.object(covers, "download", return_value=None),
        ):
            details = cli._details(self._admitted(("9788172151234", "Ekti Shonar Boi", "")))

        self.assertIsNone(details[identity.work("Ekti Shonar Boi")].cover)

    def test_a_cover_whose_bytes_arrive_is_recorded_with_its_hash(self):
        """The other half — and the hash is what makes the snapshot's claim checkable later (ticket 05)."""
        record = covers.Cover(url="https://example.test/c.jpg", sha256="abc123")

        with (
            mock.patch.object(
                google_books,
                "fetch",
                return_value=self._volume(cover_url="https://example.test/c.jpg"),
            ),
            mock.patch.object(covers, "download", return_value=record),
        ):
            details = cli._details(self._admitted(("9788172151234", "Ekti Shonar Boi", "")))

        self.assertEqual(details[identity.work("Ekti Shonar Boi")].cover, record)


    def test_the_lists_author_wins_and_googles_fills_in_only_when_it_is_empty(self):
        """⚠️ **Ticket 17's priority, and the fallback that makes it usable.**

        The list's author comes first — *"the vendor that published the list the title ranked on"*. ⚠️ But Amazon.in
        carries no author at all, so an **empty** author means *this vendor has no opinion*, not *the book has none* —
        and the row would otherwise lose an author it could have had.
        """
        with mock.patch.object(
            google_books, "fetch", return_value=self._volume(author="Google's Author")
        ):
            with_author = cli._details(
                self._admitted(("9788172151234", "Ekti Shonar Boi", "The List's Author"))
            )
            without = cli._details(self._admitted(("9788172151234", "Ekti Shonar Boi", "")))

        # ⚠️ Two stubs, two identities (ticket 32): the author is part of the work key, so a row with the list's author
        # and a row without it are *different* keys — which is the conservative half of the rule, stated as a test.
        self.assertEqual(
            with_author[identity.work("Ekti Shonar Boi", "The List's Author")].author, "The List's Author"
        )
        self.assertEqual(without[identity.work("Ekti Shonar Boi")].author, "Google's Author")

    def test_the_lists_own_price_and_rating_win_over_googles(self):
        """⚠️ **Ticket 17's per-field priority, and these are the two fields Google is worst at.**

        Google Books reports a price as a `saleInfo` *estimate* and carries **no rating at all** — so for ticket 23's
        review signal the list's own card is not merely preferred, it is the only source there is.

        ⚠️ **And the merge is where it could silently revert.** `dataclasses.replace` keeps only the fields it is told,
        so setting the list's values *before* the merge and not after would leave them surviving exactly until a volume
        arrived — which is the ordinary case, and would have looked like a parser bug rather than a merge bug.
        """
        title = corroborate.Title(
            key=identity.work("B"),
            isbn="9788172151234",
            title="B",
            sources=("amazon-in/comics",),
            publisher="Wonder House Books",
            price=prices.Price(
                amount=329.0, retailer="amazon-in", edition="Hardcover", retailers=("amazon-in",)
            ),
            rating=4.5,
            ratings_count=3661,
        )
        admitted = corroborate.Result(admitted=(title,), parked=())

        with mock.patch.object(google_books, "fetch", return_value=None):
            without_a_volume = cli._details(admitted)

        with mock.patch.object(
            google_books,
            "fetch",
            return_value=self._volume(publisher="Google's Publisher"),
        ):
            with mock.patch.object(covers, "download", return_value=None):
                with_a_volume = cli._details(admitted)

        for details in (without_a_volume, with_a_volume):
            with self.subTest(volume=details is with_a_volume):
                # ⚠️ Keyed by the **work** now (ticket 32) — `_details` returns one entry per identity, so the stub's
                # own `identity.work("B")` is what the conductor would have used.
                self.assertEqual(details[identity.work("B")].price.amount, 329.0)
                self.assertEqual(details[identity.work("B")].rating, 4.5)
                self.assertEqual(details[identity.work("B")].ratings_count, 3661)
                self.assertEqual(details[identity.work("B")].publisher, "Wonder House Books")


class TheFailureReport(unittest.TestCase):
    """⚠️ **One line per *kind* of failure, not one per title** — and the difference is whether a log gets read."""

    def _stderr(self, missed: dict[str, list[str]]) -> str:
        """Whatever `_report` said — captured, because the whole point is what does and does not get printed."""
        stream = io.StringIO()
        with contextlib.redirect_stderr(stream):
            cli._report(missed)
        return stream.getvalue()

    def test_a_source_wide_outage_is_one_line_and_not_one_per_title(self):
        """⚠️ **The 503 wall, stated as a test.**

        Google Books answers a spent daily quota to *every* title, so a per-title line is a hundred and thirty copies
        of one sentence. ⚠️ That is worse than noise: it buries the row that failed for its **own** reason, which is the
        only one an operator can act on.
        """
        isbns = [f"97800000000{n:02d}" for n in range(130)]

        printed = self._stderr({"google books did not answer: HTTP Error 503": isbns})

        self.assertEqual(len(printed.splitlines()), 1)
        self.assertIn("130 of the week's titles", printed)

    def test_the_titles_behind_a_failure_are_named_but_capped(self):
        """⚠️ *Which* titles a failure hit is the evidence — but all 130 on one line is the wall again, and the rest are
        in the snapshot for anyone who wants to check one.
        """
        isbns = [f"97800000000{n:02d}" for n in range(130)]

        printed = self._stderr({"the cover did not download: timed out": isbns})

        self.assertIn("9780000000000", printed)
        self.assertIn("and 127 more", printed)

    def test_failures_that_differ_get_their_own_lines(self):
        """⚠️ **The point of grouping by message rather than by title.**

        Two different faults are two facts, and collapsing them into one count would lose exactly the distinction the
        report exists to make.
        """
        printed = self._stderr(
            {
                "google books did not answer: HTTP Error 503": ["9780000000001"],
                "the cover did not download: timed out": ["9780000000002"],
            }
        )

        self.assertEqual(len(printed.splitlines()), 2)

    def test_a_run_where_everything_answered_says_nothing(self):
        """⚠️ **The empty case, and it is what keeps the report readable.**

        A summary printed unconditionally would be one line of noise in every healthy log — which is how a real warning
        stops being noticed. ⚠️ And a *short* list is not truncated: `and 127 more` on a failure that hit two titles
        would be a lie about how much there was to see.
        """
        self.assertEqual(self._stderr({}), "")
        self.assertNotIn("more", self._stderr({"a failure": ["9780000000001", "9780000000002"]}))


class TheMarketBand(unittest.TestCase):
    """⚠️ Ticket 08 — and the rule that matters is that **decoration cannot abort a run.**"""

    def test_a_failed_fetch_omits_the_band_and_does_not_raise(self):
        """⚠️ **The abort threshold, stated as a test.**

        The brief raises `MissingTickersError` on a short scoreboard and stops the day — *"the scoreboard is the
        content."* Here the same failure must leave the run alone: the band is background behind a book, so it goes and
        the charts still render.
        """
        with mock.patch.object(ticker, "fetch", side_effect=OSError("no route to host")):
            self.assertIsNone(cli._band("2026-W41"))

    def test_the_raw_response_is_written_before_it_is_parsed(self):
        """⚠️ **The brief's evidence habit, and the ordering is the point.**

        Ticket 18: *"the raw response is snapshotted even when parsing fails — at that point the evidence of what was
        actually received is exactly what is needed."* A response written after a successful parse can never show what
        the parser was given on the day the parser was what broke.

        ⚠️ Asserted with a payload the parser **refuses**, which is the only way to prove the order: if the write
        happened after the parse, nothing would be on disk.
        """
        with temporary_store() as root:
            with mock.patch.object(ticker, "fetch", return_value=b"not json at all"):
                self.assertIsNone(cli._band("2026-W41"))

            written = root / "store" / "2026-W41" / "raw" / "tradingview.json"
            self.assertTrue(written.is_file(), "the evidence must survive a failed parse")
            self.assertEqual(written.read_bytes(), b"not json at all")


class TheWeeklyScore(unittest.TestCase):
    """⚠️ Ticket 23's accumulation has a **circle in it**, and `_weekly` is what breaks it."""

    def test_the_weekly_score_is_ticket_threes_and_needs_no_window(self):
        """⚠️ **The reason this is its own function.**

        The window's sales term is the *accumulated* weekly score. If the weekly score needed the window there would be
        no way in and the chart could never be built at all — so the weekly score must be a pure function of this week's
        rows, and the window a pure function of the weekly scores.

        ⚠️ And the **sum across vendors is the corroboration bonus** (ticket 03): a title two vendors carried scores
        above one that only a single vendor did, which is *"genuine and authentic"* as arithmetic rather than a promise.
        """
        rows = [
            corroborate.Row(list="amazon-in/comics", rank=1, isbn="9788172151234", title="A"),
            corroborate.Row(list="nyt/graphic-books-and-manga", rank=1, isbn="9788172151234", title="A"),
            corroborate.Row(list="amazon-in/comics", rank=2, isbn="9780000000002", title="B"),
        ]

        weekly = cli._weekly(rows, charts.get("comics"))

        # ⚠️ Keyed by the **work** (ticket 32): `_weekly` scores a work from every listing that carried it, so the
        # corroboration bonus is visible here — the same title on two lists outscores the one on a single list.
        self.assertGreater(weekly[identity.work("A")], weekly[identity.work("B")])

    def test_a_list_that_carries_one_title_twice_counts_once(self):
        """⚠️ ⚠️ **The defect the committed week's merge caught** (ticket 32).

        BoiChitro ranks `Chandmama` at **92, 95 and 96** — three product ids for one book — and a score that summed all
        three gave it **2.7**, which put it at **rank 1** on the Bengali chart. ⚠️ One shop's duplicate listings are not
        three corroborating voices; that is *"a lie told in arithmetic"*, and the merge of the recorded week is what made
        it visible.

        ⚠️ Ticket 03 counts **lists**: a work contributes **at most one term per list**, at its **best** position in it.
        """
        rows = [
            corroborate.Row(list="boichitro/bestsellers", rank=1, isbn="boichitro:1", title="Chandmama"),
            corroborate.Row(list="boichitro/bestsellers", rank=3, isbn="boichitro:2", title="Chandmama"),
            corroborate.Row(list="boichitro/bestsellers", rank=4, isbn="boichitro:3", title="Chandmama"),
            #: ⚠️ A filler, so the list is **four deep** and the ranks sit inside it — the real ranking is a hundred
            #: deep and `rank.points` divides by the size, so a rank beyond the size is not a case worth testing.
            corroborate.Row(list="boichitro/bestsellers", rank=2, isbn="boichitro:9", title="Something Else"),
        ]

        scored = cli._weekly(rows, charts.get("bengali"))

        #: ⚠️ **One term, at the best position the shop gave the book** — which is what `rank.score` computes for a work
        #: carried once by one list. ⚠️ Asserted through the product's own function rather than by re-deriving the
        #: arithmetic here, so the test cannot agree with a wrong implementation of it.
        expected = rank.score(
            [rank.Listing(list="boichitro/bestsellers", rank=1, size=4)],
            weights={"boichitro": cli.DEFAULT_WEIGHT},
        )
        self.assertEqual(scored[identity.work("Chandmama")], expected)

    def test_a_title_the_window_never_saw_scores_zero_rather_than_vanishing(self):
        """⚠️ **Zero, not absent.** A candidate the window has no observation for still becomes a candidate — it simply
        scores nothing — so the chart can never lose a title to a bookkeeping gap. ⚠️ And on a fresh build it cannot
        happen: the window includes the week being built, so every admitted title is in it by construction.
        """
        admitted = corroborate.Result(
            admitted=(
                corroborate.Title(
                    key=identity.work("A"),
                    isbn="9788172151234",
                    title="A",
                    sources=("nyt/hardcover-fiction",),
                ),
            ),
            parked=(),
        )
        empty = window.Window(weeks=(), observed={}, mean_rating=4.0)

        candidates = cli._candidates({}, admitted, empty)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].score, 0.0)
        self.assertIsNone(candidates[0].rating)


class TheRun(unittest.TestCase):
    def test_every_thumbnail_is_rendered_before_any_video(self):
        """⚠️ **Ticket 16's quality gate, asserted rather than intended.**

        Four one-frame stills cost seconds, so a chart whose collage reads badly is seen and killed **before** an hour of
        frames is spent on it — the reel's own ordering, and its reason. ⚠️ The order is easy to lose to a refactor,
        because both loops look identical and swapping them costs nothing until the day it costs an hour.
        """
        order: list[str] = []

        with temporary_store() as root:
            store.write_facts("2026-W41", snapshot())
            with (
                mock.patch.object(cli, "stage"),
                mock.patch.object(cli, "package"),
                mock.patch.object(cli, "_music", return_value=None),
                mock.patch.object(
                    cli, "_produce", side_effect=lambda *a, **k: order.append(k["kind"])
                ),
            ):
                self.assertEqual(cli.build("2026-W41"), 0)

        self.assertEqual(order, ["thumbnail", "video"])

    def test_the_package_is_assembled_after_both_artefacts_exist(self):
        """⚠️ **The metadata describes artefacts that have to be there**, and the manifest is what says the folder is
        finished (ticket 13) — so assembly cannot honestly run before the renders.
        """
        order: list[str] = []

        with temporary_store() as root:
            store.write_facts("2026-W41", snapshot())
            with (
                mock.patch.object(cli, "stage"),
                mock.patch.object(cli, "_music", return_value=None),
                mock.patch.object(
                    cli, "_produce", side_effect=lambda *a, **k: order.append(k["kind"])
                ),
                mock.patch.object(
                    cli, "package", mock.Mock(assemble=mock.Mock(side_effect=lambda *a: order.append("package")))
                ),
            ):
                cli.build("2026-W41")

        self.assertEqual(order, ["thumbnail", "video", "package"])

    def test_a_replayed_week_counts_down_even_when_it_was_recorded_counting_up(self):
        """⚠️ **The bug this guards: a code change that a replay never sees.**

        The snapshot carries the timeline, and a replay reads the snapshot — so a week recorded in rank order rendered
        1 → 100 forever, whatever `timeline.schedule` said. The rows replay as recorded; the running order is today's.
        """
        recorded = snapshot()
        blocks = recorded["charts"]["bengali"]["timeline"]["blocks"]
        recorded["charts"]["bengali"]["timeline"]["blocks"] = list(reversed(blocks))

        with temporary_store():
            store.write_facts("2026-W41", recorded)
            with (
                mock.patch.object(cli, "stage"),
                mock.patch.object(cli, "package"),
                mock.patch.object(cli, "_music", return_value=None),
                mock.patch.object(cli, "_produce"),
            ):
                self.assertEqual(cli.build("2026-W41"), 0)

            replayed = store.read_facts("2026-W41")

        self.assertEqual(
            replayed["charts"]["bengali"]["timeline"], snapshot()["charts"]["bengali"]["timeline"]
        )
        self.assertEqual(
            [row["isbn"] for row in replayed["charts"]["bengali"]["ranked"]],
            [row["isbn"] for row in recorded["charts"]["bengali"]["ranked"]],
        )

    def test_the_bed_is_prepared_before_the_first_render_and_removed_after(self):
        """⚠️ **The bed is scratch, and it lands inside the chart's package folder** — the folder a human opens to find
        the week's deliverable.

        So it is cut **before** the first render (an unusable bed is a refusal, and a refusal that arrives after an hour
        of frames is an hour spent learning nothing) and removed whether the run succeeds or not — leaving the folder
        holding the four files ticket 13 promises and nothing else.
        """
        order: list[str] = []
        beds: list[pathlib.Path] = []

        with temporary_store() as root:
            store.write_facts("2026-W41", snapshot())

            def fake_music(week, chart, seconds):
                # ⚠️ `package.dir_for`'s own location, spelled out here because `cli.package` is mocked in this test: the
                # assertion is about the run *removing* what the bed prepared, wherever it put it.
                directory = root / "output" / "books" / week / chart.slug
                directory.mkdir(parents=True, exist_ok=True)
                bed = directory / ".bed.wav"
                bed.write_bytes(b"music")
                beds.append(bed)
                order.append("music")
                return bed, "music: music.mp3 → .bed.wav"

            with (
                mock.patch.object(cli, "stage"),
                mock.patch.object(cli, "package"),
                mock.patch.object(cli, "_music", side_effect=fake_music),
                mock.patch.object(cli, "_produce", side_effect=lambda *a, **k: order.append(k["kind"])),
            ):
                self.assertEqual(cli.build("2026-W41"), 0)

            # ⚠️ Asserted **inside** the store's lifetime: the temp directory is deleted on exit, so `exists()` after the
            # block is false whatever the code did — the mistake the scratch-file test below records.
            self.assertEqual(order, ["music", "thumbnail", "video"], "the bed is cut before the first render")
            for bed in beds:
                self.assertFalse(bed.exists(), "the derived bed must not survive the run")

    def test_the_video_is_handed_its_chart_own_bed_and_a_still_is_handed_none(self):
        """⚠️ **A thumbnail has no audio**, so it is never given a bed — and the video gets **its own chart's** bed, cut
        to its own length, rather than one file shared across four runs of four different lengths (see `_music`).
        """
        beds: dict[str, pathlib.Path] = {}
        handed: dict[str, pathlib.Path | None] = {}

        with temporary_store() as root:
            store.write_facts("2026-W41", snapshot())

            def fake_music(week, chart, seconds):
                directory = root / "output" / "books" / week / chart.slug
                directory.mkdir(parents=True, exist_ok=True)
                bed = directory / ".bed.wav"
                bed.write_bytes(b"music")
                beds[chart.slug] = bed
                return bed, "music"

            def fake_produce(chart, week, *, kind, bed=None):
                handed[kind] = bed

            with (
                mock.patch.object(cli, "stage"),
                mock.patch.object(cli, "package"),
                mock.patch.object(cli, "_music", side_effect=fake_music),
                mock.patch.object(cli, "_produce", side_effect=fake_produce),
            ):
                self.assertEqual(cli.build("2026-W41"), 0)

        self.assertIsNone(handed["thumbnail"], "a still has no audio to carry")
        self.assertEqual(handed["video"], beds["bengali"])

    def test_an_unusable_bed_refuses_the_run_and_renders_nothing(self):
        """⚠️ 0085_11's refusal, kept here: a bed the toolchain cannot read is something the operator can fix, and the run
        stops **before** any render rather than shipping a week of silent videos.
        """
        with temporary_store():
            store.write_facts("2026-W41", snapshot())
            with (
                mock.patch.object(cli, "stage"),
                mock.patch.object(cli, "package"),
                mock.patch.object(cli, "_music", side_effect=audio.AudioError("not a container it can read")),
                mock.patch.object(cli, "_produce") as produce,
            ):
                self.assertEqual(cli.build("2026-W41"), 1)

            produce.assert_not_called()


class ChoosingTheCharts(unittest.TestCase):
    """⚠️ Ticket 13's partial delivery, one flag along — **a run may be asked for a single chart.**

    ⚠️ **`--chart` narrows the *render* and never the *gather***: the bundle is the week's evidence and the replay path
    (ADR 0003), so a run asked for one chart still snapshots the whole week. ⚠️ What these tests pin is the
    **reporting** — an asked-for chart that is not in the bundle has to be said out loud, because the alternative is a
    run that prints nothing, exits zero and produces no video, which reads as success.
    """

    def _build(self, only: tuple[str, ...]) -> tuple[int, list[str], str]:
        """Run `build` against a one-chart snapshot, returning `(exit code, what rendered, what was said)`."""
        rendered: list[str] = []
        complaints = io.StringIO()

        with temporary_store():
            store.write_facts("2026-W41", snapshot())
            with (
                mock.patch.object(cli, "stage"),
                mock.patch.object(cli, "package"),
                mock.patch.object(cli, "_music", return_value=None),
                mock.patch.object(
                    cli,
                    "_produce",
                    side_effect=lambda chart, week, *, kind, bed=None: rendered.append(chart.slug),
                ),
                contextlib.redirect_stderr(complaints),
            ):
                code = cli.build("2026-W41", only)

        return code, rendered, complaints.getvalue()

    def test_the_one_chart_the_week_built_is_the_one_that_renders(self):
        """⚠️ The snapshot holds `bengali` alone, and asking for it renders it — the narrowed run is the ordinary case
        now, not an edge one.
        """
        code, rendered, complaints = self._build(("bengali",))

        self.assertEqual(code, 0)
        self.assertEqual(rendered, ["bengali", "bengali"], "a thumbnail and then a video")
        self.assertEqual(complaints, "")

    def test_a_chart_the_week_could_not_build_is_said_rather_than_silently_skipped(self):
        """⚠️ ⚠️ **The sentence this filter exists for.** Asking for a chart that is absent must not look like success —
        and today it is the *ordinary* case, because `comics` and `all-language` depend on a source that cannot be
        date-verified and are therefore absent every week.
        """
        code, rendered, complaints = self._build(("english",))

        self.assertEqual(code, 1, "nothing rendered, so nothing succeeded")
        self.assertEqual(rendered, [])
        self.assertIn("english: not in this week's bundle", complaints)

    def test_a_name_that_is_not_a_chart_says_which_ones_are(self):
        """⚠️ A typo is answered with the list — not with a traceback, and not with silence."""
        code, rendered, complaints = self._build(("hindi",))

        self.assertEqual(code, 1)
        self.assertEqual(rendered, [])
        self.assertIn("not a chart", complaints)
        self.assertIn("english", complaints)

    def test_asking_for_two_charts_renders_the_one_the_week_has(self):
        """⚠️ **Partial delivery**, and the run is still a success — because one of the two answered. The absent one is
        still named, so *"did I ask for comics"* is answered on screen rather than by opening a folder.
        """
        code, rendered, complaints = self._build(("english", "bengali"))

        self.assertEqual(code, 0)
        self.assertEqual(rendered, ["bengali", "bengali"])
        self.assertIn("english: not in this week's bundle", complaints)


class TheCoversAChartNeeds(unittest.TestCase):
    """⚠️ `_covered` reads the bundle, and a narrowed run should not stage a cover nobody is going to draw."""

    def test_only_the_asked_for_charts_covers_are_staged(self):
        bundle = snapshot()
        widened = {
            **bundle,
            "charts": {
                **bundle["charts"],
                "english": {"ranked": [{"isbn": "9780000000002", "cover": "covers/x.jpg"}]},
            },
        }

        # ⚠️ `bengali`'s own row records no cover, so asking for it stages nothing — which is the assertion that proves
        # the filter reads the *asked-for* chart rather than merely the bundle.
        self.assertEqual(cli._covered(widened, only=("bengali",)), [])
        self.assertEqual(cli._covered(widened, only=("english",)), ["9780000000002"])
        self.assertEqual(cli._covered(widened), ["9780000000002"], "no filter means every chart")


class ProducingOneArtefact(unittest.TestCase):
    def test_the_render_goes_to_scratch_and_moves_into_place_only_once_it_exists(self):
        """⚠️ **Remotion's `--overwrite` unlinks its target before writing it.**

        Rendering straight at the package file would let a render that dies at 90% — or is killed — destroy last week's
        good delivery while the folder still looked like a package. ⚠️ And the scratch file is removed **even on
        success**, because a leftover in a package folder is an unexplained file where a human looks for the week's
        deliverable.
        """
        seen: list[str] = []

        def fake_run(argv):
            seen.append(pathlib.Path(argv[5]).name)
            pathlib.Path(argv[5]).write_bytes(b"a video")

        with temporary_store() as root:
            with (
                mock.patch.object(paths, "data_root", return_value=root),
                mock.patch.object(render, "run", side_effect=fake_run),
            ):
                target = cli._produce(charts.get("bengali"), "2026-W41", kind="video")

                # ⚠️ **Asserted inside the store's lifetime**, and the first version of this test was not: the temp
                # directory is deleted on exit, so `is_file()` after the block is false whatever the code did.
                self.assertEqual(seen, [".bengali-2026-W41.mp4"], "the render must write to scratch")
                self.assertEqual(target.name, "bengali-2026-W41.mp4")
                self.assertTrue(target.is_file())
                self.assertEqual(
                    [
                        entry.name
                        for entry in target.parent.iterdir()
                        if entry.name.startswith(".")
                    ],
                    [],
                )

    def test_the_scratch_name_keeps_an_extension_remotion_will_render_to(self):
        """⚠️ ⚠️ **The bug this test exists for, and it cost a whole gather to find.**

        Remotion refuses h264+aac unless the output filename ends in `.mp4`, `.mkv` or `.mov` — so a scratch file named
        `…mp4.part` fails **after** the composition has bundled, with a `TypeError` about the *filename*. ⚠️ And a still
        has no codec to validate, so every thumbnail rendered and only the videos died — the worst shape a bug can have,
        because the run looked like it was working.

        ⚠️ Asserted on the name the renderer is actually handed, because that is the thing Remotion reads.
        """
        seen: list[str] = []

        def fake_run(argv):
            seen.append(pathlib.Path(argv[5]).name)
            pathlib.Path(argv[5]).write_bytes(b"a video")

        with temporary_store() as root:
            with (
                mock.patch.object(paths, "data_root", return_value=root),
                mock.patch.object(render, "run", side_effect=fake_run),
            ):
                cli._produce(charts.get("bengali"), "2026-W41", kind="video")

        for name in seen:
            with self.subTest(scratch=name):
                self.assertTrue(name.startswith("."), "the scratch file has to be hidden")
                self.assertTrue(
                    name.endswith((".mp4", ".mkv", ".mov")),
                    "Remotion validates the extension, and `.part` is not one it accepts",
                )

    def test_a_render_that_reports_success_and_writes_nothing_is_refused(self):
        """⚠️ **The failure worth having an error type for.** A `remotion render` that exits zero and leaves no file
        would otherwise be discovered at upload time, by which point the run has moved on.
        """
        with temporary_store() as root:
            with (
                mock.patch.object(paths, "data_root", return_value=root),
                mock.patch.object(render, "run", return_value=None),
            ):
                with self.assertRaises(render.RenderError):
                    cli._produce(charts.get("bengali"), "2026-W41", kind="video")

    def test_the_bed_is_muxed_onto_the_finished_video(self):
        """⚠️ **The music is added after the render, and the picture is copied rather than re-encoded.**

        The composition carries no audio at all — the bed is muxed onto the finished file, and `audio.mux`'s `-c:v copy`
        is what makes that cost no frames: the video that lands in the package is bit-for-bit the one the renderer
        produced.
        """
        calls: list[tuple] = []

        def fake_run(argv):
            pathlib.Path(argv[5]).write_bytes(b"a silent video")

        def fake_mux(video, bed, out, **kwargs):
            calls.append((video.name, bed, out.name))
            pathlib.Path(out).write_bytes(b"a video with music")
            return pathlib.Path(out)

        with temporary_store() as root:
            with (
                mock.patch.object(paths, "data_root", return_value=root),
                mock.patch.object(render, "run", side_effect=fake_run),
                mock.patch.object(audio, "mux", side_effect=fake_mux),
            ):
                bed = root / "music.wav"
                target = cli._produce(charts.get("bengali"), "2026-W41", kind="video", bed=bed)

                self.assertEqual(
                    calls,
                    [(".bengali-2026-W41.mp4", bed, "bengali-2026-W41.mp4")],
                    "the render's scratch file is the mux's input, and the package file is its output",
                )
                self.assertTrue(target.is_file())

    def test_a_video_with_no_bed_is_moved_into_place_silent(self):
        """⚠️ **No `music.*` supplied is a supported state, not an error** — the brief's own contract, and the reason this
        product could ship before a bed existed. The video is moved into place and no mux is attempted.
        """

        def fake_run(argv):
            pathlib.Path(argv[5]).write_bytes(b"a silent video")

        with temporary_store() as root:
            with (
                mock.patch.object(paths, "data_root", return_value=root),
                mock.patch.object(render, "run", side_effect=fake_run),
                mock.patch.object(audio, "mux") as mux,
            ):
                target = cli._produce(charts.get("bengali"), "2026-W41", kind="video")

                mux.assert_not_called()
                self.assertTrue(target.is_file())


class GatheringTheSources(unittest.TestCase):
    """⚠️ Ticket 18's spine rule, with ticket 10's freshness guard acting *through* it.

    ⚠️ **The guard is useless on its own.** Dropping a stale vendor's rows and building the chart from the survivors is
    the silent wrong answer: the chart ships, smaller, claiming to rank the lists it declares. So the guard's finding has
    to reach the spine rule — a vendor that produced no usable evidence is a **missing source**, and the chart that
    needed it goes absent.
    """

    def _client(
        self, vendor: str, rows: list[corroborate.Row], *, error: Exception | None = None
    ) -> mock.Mock:
        """A stub source client.

        ⚠️ **The contract is two functions, and a stub that fakes only one is a stub that tests nothing.**
        `fetch(chart) -> Iterable[Page]` is the boundary and `parse(payload, *, listing) -> rows` is the seam — so this
        yields a `Page` per list **the vendor owns**, and parses each back to the rows tagged with that list.

        ⚠️ **And the first version of this helper returned rows from `fetch`, which made three tests pass vacuously** —
        `gather` tried `page.name` on a `Row`, every vendor "did not answer", every chart went absent, and the assertions
        on *"the chart is absent"* were satisfied for entirely the wrong reason. The one test that failed was the one
        asserting a chart *built*.
        """
        client = mock.Mock()
        if error is not None:
            client.fetch = mock.Mock(side_effect=error)
            return client

        client.fetch = mock.Mock(
            side_effect=lambda chart, *, week: [
                # ⚠️ **The name uses the segment *after* the slash, not the slug** — a slug is `amazon-in/comics` and a
                # filename cannot hold a slash. My first version passed the slug and the write failed with
                # `No such file or directory: …/raw/amazon-in-rokomari/leaderboard.html`, which is the very thing
                # `Page.name`'s docstring warns about.
                fetch.Page(
                    listing=entry,
                    name=f"{vendor}-{entry.slug.partition('/')[2]}.html",
                    payload=b"<html></html>",
                )
                for entry in chart.lists
                # ⚠️ A vendor reads **its own** lists — the same guard `nyt.fetch` keeps.
                if entry.slug.startswith(f"{vendor}/")
            ]
        )
        client.parse = mock.Mock(
            side_effect=lambda payload, *, listing, published="": [
                row for row in rows if row.list == listing.slug
            ]
        )
        return client

    def _bengali(self, *, rokomari: str, boichitro: str) -> dict[str, mock.Mock]:
        """`bengali`'s **two** vendors — the pair ticket 30 restored, and the chart where **neither** states a date.

        ⚠️ **It was three vendors until ticket 29** (Amazon.in, Anandabazar, Rokomari) and **one until ticket 30** — two
        corrections, both about *sources* rather than about code. Amazon.in publishes no Bengali list at all, and
        Anandabazar's had **no address to give** (⚠️ ticket 31 has since *located* the list — it is an archive, so the
        answer stands); ⚠️ BoiChitro is a bookseller whose hundred-deep popularity ranking is a **JSON endpoint**, so the
        chart has an Indian vendor that can actually be declared.
        """
        return {
            "rokomari": self._client("rokomari", [row("rokomari/best-sellers", rokomari)]),
            "boichitro": self._client("boichitro", [row("boichitro/bestsellers", boichitro)]),
        }

    def _comics(self, *, nyt: str, amazon_in: str) -> dict[str, mock.Mock]:
        """`comics`' vendors, as stubs — the chart the spine rule is shown on.

        ⚠️ The two stubs answer with the **same ISBN**, so they corroborate each other and the chart can admit a title.
        ⚠️ **`amazon-us` is declared by the chart and deliberately absent from this registry** (2026-10-15): a declared
        vendor with no client is scaffolding rather than a source that failed, which is a rule this class tests
        separately — and a stub that answered for it would hide that rule behind this one.
        """
        return {
            "nyt": self._client("nyt", [row("nyt/graphic-books-and-manga", nyt)]),
            "amazon-in": self._client("amazon-in", [row("amazon-in/comics", amazon_in)]),
        }

    def _gather(self, clients: dict[str, mock.Mock]) -> tuple[dict, str]:
        """Run `gather` against stub clients, returning the bundle and whatever it said on stderr."""
        complaints = io.StringIO()

        with temporary_store():
            with (
                mock.patch.object(cli, "CLIENTS", clients),
                mock.patch.object(cli, "_band", return_value=None),
                mock.patch.object(cli, "_details", return_value={}),
                contextlib.redirect_stderr(complaints),
            ):
                bundle = cli.gather("2026-W41")

        return bundle, complaints.getvalue()

    def test_a_stale_vendor_makes_the_chart_absent_rather_than_smaller(self):
        """⚠️ **The whole point, and the reason the guard is not merely a filter.**

        `comics`' NYT stub answered with **September's** list while its other vendor answered for this week. Dropping the
        stale rows and building from the survivor would produce a chart quietly missing a source — plausible,
        complete-looking, and wrong. ⚠️ Ticket 18: *"the chart that needed it goes absent."*

        ⚠️ ⚠️ **The stale vendor is `nyt`, and the date has moved twice.** This test used to stale `amazon-in` — but an
        Amazon page states no date, so `amazon-in` is `LIVE` (`charts.LIVE`) and is **exempt from the date check**.
        ⚠️ And it used to say `2026-10-04`, *last week* — which stopped being stale the moment NYT's
        `graphic-books-and-manga` was declared **monthly** (`charts.CADENCES`), because a monthly list is fresh for its
        whole month. ⚠️ **A previous month is what stale means for that list now**, so the date moved with the rule and
        the assertion did not weaken: the chart still goes absent.
        """
        bundle, complaints = self._gather(
            self._comics(nyt="2026-09-05", amazon_in="")
        )

        self.assertNotIn("comics", bundle["charts"])
        # ⚠️ And it is **said**, because a chart that simply vanishes from four is indistinguishable from one that was
        # never declared — which is the difference between an operator checking NYT and an operator re-reading the chart
        # table.
        self.assertIn("nyt", complaints)

    def test_a_monthly_list_is_still_fresh_weeks_after_it_was_published(self):
        """⚠️ ⚠️ **The case that was failing in production, asserted at the conductor** (2026-10-15).

        NYT's graphic-books list is dated the **first Saturday of the month** — the recorded `2026-W41` payload says
        `bestsellers_date: 2026-10-03` — and the weekly span for that week is `2026-10-05 … 2026-10-14`. ⚠️ So the list
        was four days "stale" on the very week it describes, `comics` went **absent** for three weeks in four, and
        `./build books` answered *"comics: not in this week's bundle — it could not be built"* while Amazon.in had
        answered it thirty rows. ⚠️ Declared monthly, that same date builds the chart — and September's still does not,
        which is the assertion above.
        """
        bundle, complaints = self._gather(
            self._comics(nyt="2026-10-03", amazon_in="")
        )

        self.assertIn("comics", bundle["charts"], complaints)
        self.assertNotIn("comics:", complaints)

    def test_a_live_vendor_is_not_asked_for_a_date_it_never_states(self):
        """⚠️ ⚠️ **The exemption, seen from the conductor** (2026-10-15).

        `amazon-in` answers with **no date at all** — which is exactly what a real Amazon page does — and the chart still
        builds. ⚠️ Before the exemption this precise input made `comics` absent, which is why that chart never shipped and
        why the English chart could not have gained an international list.
        """
        bundle, complaints = self._gather(
            self._comics(nyt="2026-10-14", amazon_in="")
        )

        self.assertIn("comics", bundle["charts"])
        # ⚠️ **`comics` is not among the complaints** — the point is that *its* live vendor was not refused. ⚠️ Other
        # charts in this patched registry can still complain (the stub answers only for the lists it owns), so the
        # assertion names `comics` rather than the string `amazon-in`.
        self.assertNotIn("comics:", complaints)

    def test_a_vendor_that_raised_takes_the_same_path_as_one_that_was_stale(self):
        """⚠️ **One condition, two causes.** From the chart's side *"the vendor produced no usable evidence"* is the same
        fact whether the client timed out or answered with last week's list — and it must not be possible for one to be
        treated as a refusal while the other ships a short chart.
        """
        bundle, complaints = self._gather(
            self._comics(nyt="2026-10-14", amazon_in="2026-10-14")
            | {"amazon-in": self._client("amazon-in", [], error=OSError("no route to host"))}
        )

        self.assertNotIn("comics", bundle["charts"])
        self.assertIn("amazon-in", complaints)

    def test_a_vendor_with_no_client_is_not_a_vendor_that_failed(self):
        """⚠️ **And the reason an unregistered scraper does not refuse everything.**

        ⚠️ **`rokomari` was the example here and it is a registered vendor now** (ticket 30) — the point this test makes
        is about the **registry a run was handed**, not about that vendor: a declared vendor with **no client in this
        registry** is scaffolding rather than a source that failed, so `gather` must not report it missing —
        *"a vendor it has no client for simply does not contribute."* ⚠️ So the stub registry below is deliberately
        incomplete, which is a situation the real one no longer produces for `bengali`.

        ⚠️ `bengali` is the case that proves it: neither of its declared vendors has a client here, so the chart is absent
        for having **no rows** rather than absent for a missing source — and nothing is blamed for it.
        """
        _, complaints = self._gather(
            {"nyt": self._client("nyt", [row("nyt/hardcover-fiction", "2026-10-14")])}
        )

        self.assertNotIn("rokomari", complaints)
        self.assertNotIn("boichitro", complaints)
        self.assertNotIn("anandabazar", complaints)

    def test_the_bengali_chart_builds_from_two_vendors_neither_of_which_states_a_date(self):
        """⚠️ ⚠️ **Ticket 30's whole point, seen from the conductor.**

        `bengali` declares Rokomari (Bangladeshi) and BoiChitro (Indian), and **neither list carries a date** — so before
        `charts.LIVE` named them, `freshness.guard` refused every row from both and the chart was **absent every week**.
        ⚠️ That absence is exactly the message the operator was reading:

            books · 2026-W41 · bengali
            bengali: not in this week's bundle — it could not be built

        ⚠️ And the two stubs answer with the **same ISBN**, so the chart's title carries **two sources** — which is what
        ticket 17's arithmetic counts, and what this chart has not had since ticket 29 removed its Indian half.
        """
        bundle, complaints = self._gather(self._bengali(rokomari="", boichitro=""))

        self.assertIn("bengali", bundle["charts"])
        self.assertNotIn("bengali:", complaints)
        self.assertEqual(len(bundle["charts"]["bengali"]["ranked"]), 1)
        self.assertEqual(
            bundle["charts"]["bengali"]["ranked"][0]["isbn"], "9788172151234"
        )

    def test_a_client_shared_by_several_vendors_is_asked_once_per_chart(self):
        """⚠️ ⚠️ **The registry is keyed by *vendor*; `fetch` works per *client* — and the difference was 64 requests.**

        ⚠️ `CLIENTS` maps eight Amazon storefronts to **one module**, and `amazon.fetch(chart, week=…)` reads **every list
        the chart declares for it**. ⚠️ So calling `fetch` once per *vendor* fetched every store once per store:
        **64 requests for the comics chart instead of 8**, with every row arriving **eight times**.

        ⚠️ **The duplicates were not merely slow, which is what makes this a correctness test.** `_weekly` collapses a
        work's rows *per list*, so the sum survived — but it sizes a list by **counting its rows**, and `rank.weight`
        scales a list by its depth (`min(1, size / N_REF)`). ⚠️ A thirty-card storefront was sized **240**, which lifts
        it from a **0.3** weight to a full **1.0**: the chart ranked that vendor far above the weight ticket 03 gives it,
        and the error grew with every store added — 4× on the English chart, 8× on comics.

        ⚠️ **It was invisible because the stubs register one client per vendor.** A registry of distinct `Mock`s cannot
        show a shared client being asked twice, so this test hands **one client to two vendors on purpose** — which is
        exactly what the real registry does for Amazon.
        """
        shared = self._client("amazon-us", [row("amazon-us/comics", "2026-10-14")])
        uses_it = [
            chart for chart in charts.ALL if {"amazon-us", "amazon-in"} & set(chart.vendors)
        ]

        with temporary_store():
            with (
                mock.patch.object(cli, "CLIENTS", {"amazon-us": shared, "amazon-in": shared}),
                mock.patch.object(cli, "_band", return_value=None),
                mock.patch.object(cli, "_details", return_value={}),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                cli.gather("2026-W41")

        # ⚠️ **One call per *chart*, never per vendor** — the vendor count is what used to multiply it.
        self.assertEqual(shared.fetch.call_count, len(uses_it))

    def test_the_raw_response_is_written_before_it_is_parsed(self):
        """⚠️ **The reason the client contract changed, asserted.**

        Ticket 18: *"the raw response is snapshotted **even when parsing fails** — at that point the evidence of what was
        actually received is exactly what is needed."* ⚠️ A response written *after* a successful parse is a response the
        parser already vouched for, so it can never show what the parser was **given** on the day the parser was what
        broke.

        ⚠️ **Asserted with a page the parser rejects**, which is the only way to prove the order: if the write happened
        after the parse, nothing would be on disk at all. This is the books' copy of the brief's own test for the same
        rule.
        """
        client = self._client("amazon-in", [row("amazon-in/comics", "2026-10-14")])
        client.parse = mock.Mock(side_effect=ValueError("the parser is what broke"))

        with temporary_store() as root:
            with (
                mock.patch.object(cli, "CLIENTS", {"amazon-in": client}),
                mock.patch.object(cli, "_band", return_value=None),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                cli.gather("2026-W41")

            written = root / "store" / "2026-W41" / "raw" / "amazon-in-comics.html"
            self.assertTrue(written.is_file(), "the evidence must survive a failed parse")
            self.assertEqual(written.read_bytes(), b"<html></html>")

    def test_a_client_that_parses_its_own_response_is_no_longer_the_contract(self):
        """⚠️ **`fetch` hands back `Page`s, and a client returning rows is now a client that fails loudly.**

        That is the point rather than a side effect: a client that had already parsed could only ever offer a response
        its own parser had vouched for, so the evidence rule could not be honoured at all. ⚠️ And the failure is
        **caught by the conductor** like any other vendor failure, so a stale client makes its chart absent rather than
        crashing the run.
        """
        client = self._client("amazon-in", [row("amazon-in/comics", "2026-10-14")])
        client.fetch = mock.Mock(return_value=[row("amazon-in/comics", "2026-10-14")])

        bundle, complaints = self._gather({"amazon-in": client})

        self.assertNotIn("comics", bundle["charts"])
        self.assertIn("did not answer", complaints)

    def test_the_date_a_client_cannot_put_in_its_payload_is_handed_to_its_parser(self):
        """⚠️ ⚠️ **The other half of the same defect — the one that kept `english` unbuildable.**

        `indie`'s list is dated **in its own address**, so the response carries no date a parser could read. ⚠️ Called
        without it, `indie.parse` returns rows whose `published` is empty — which `freshness` correctly refuses, so the
        chart was absent every week and the vendor looked like it had failed. ⚠️ `Page.published` is the only route by
        which a URL-borne date reaches a row, so this asserts the conductor actually hands it on.
        """
        seen: list[str] = []

        client = mock.Mock()
        client.fetch = mock.Mock(
            side_effect=lambda chart, *, week: [
                fetch.Page(
                    listing=entry,
                    name=f"indie-{entry.slug.partition('/')[2]}.html",
                    payload=b"<html></html>",
                    published="2026-10-14",
                )
                for entry in chart.lists
                if entry.slug.startswith("indie/")
            ]
        )
        client.parse = mock.Mock(
            side_effect=lambda payload, *, listing, published="": seen.append(published) or []
        )

        self._gather(
            {
                "indie": client,
                "nyt": self._client("nyt", [row("nyt/hardcover-fiction", "2026-10-14")]),
            }
        )

        self.assertEqual(seen, ["2026-10-14"], "the page's date has to reach the parser")

    def test_a_fresh_vendor_keeps_its_rows(self):
        """The other half of the guard: freshness must not be so strict that a normal week refuses.

        ⚠️ **Asserted positively, and my first version was not.** It asserted that `amazon-in` was *absent from the
        complaints*, which the stub satisfies only by accident — a stub carrying rows for one list and not for another
        makes the *other* chart complain, and the assertion caught that instead of the question it meant to ask. ⚠️ The
        question is *did the chart build*, so that is what it now checks.
        """
        bundle, complaints = self._gather(
            self._comics(nyt="2026-10-14", amazon_in="2026-10-14")
        )

        self.assertIn("comics", bundle["charts"], complaints)
        self.assertNotIn("comics:", complaints)


if __name__ == "__main__":
    unittest.main()
