"""Tickets 13 and 23 — the bundle: **one file per week, four chart keys.**

⚠️ **A chart whose sources failed is an *absent key*, not an empty one.** The brief's rule is *"a missing strip is an
absent key, never an empty card full of zeros pretending the world was flat"* — and here it buys **partial delivery**:
three charts ship, the fourth refuses, and nothing is fabricated to fill the gap.
⚠️ **And the bundle carries the rows the slide prints, not just their ranks.** This is the interface the render layer
reads (ADR 0003), so a bundle of `isbn`/`rank` pairs is a bundle a slide cannot draw from.
"""
import unittest

from books_brief import covers, enrich, facts, identity, prices, rank, ticker


def chart(*isbns: str, watchlist: tuple[str, ...] = ()) -> facts.Chart:
    """One chart, one row per ISBN, so a bundle can be built without a network."""
    return facts.Chart(
        books=enrich.build(
            (
                rank.Ranked(key=isbn, isbn=isbn, rank=number + 1, weeks_on_chart=0, is_new=False)
                for number, isbn in enumerate(isbns)
            ),
            details={},
            previous=None,
        ),
        watchlist=watchlist,
    )


class TheBundle(unittest.TestCase):
    def test_a_chart_whose_sources_failed_is_an_absent_key_not_an_empty_one(self):
        """⚠️ Ticket 13 — and the difference matters, because an empty chart *renders*.

        `None` says *we asked and it failed*; a missing key says *we never asked*. Both leave no key in the bundle, and
        neither leaves a chart full of zeros that looks like a real week.
        """
        bundle = facts.build(
            "2026-W41",
            charts={"bengali": chart("9788172151234"), "comics": None},
            window_weeks=7,
        )

        self.assertNotIn("comics", bundle["charts"])
        self.assertEqual(list(bundle["charts"]), ["bengali"])

    def test_the_bundle_states_the_window_it_actually_has(self):
        """⚠️ Ticket 23 — the six-month window is **accumulated from our own snapshots**, so weeks 1–25 cannot have it.

        A chart that said *"six months"* while holding seven weeks would be stating something untrue, so the real
        number rides in the bundle — and the version stamp rides beside it, because a change to the ranking rule
        changes the chart (ticket 03).
        """
        bundle = facts.build(
            "2026-W41", charts={"bengali": chart("9788172151234")}, window_weeks=7
        )

        self.assertEqual(bundle["meta"]["week"], "2026-W41")
        self.assertEqual(bundle["meta"]["window_weeks"], 7)
        # ⚠️ **Asserted against the constant, not a literal** (ticket 32): the stamp is *meant* to move when the ranking
        # rule does, and a test that pinned `1` would have to be edited every time the rule changed — which is the
        # opposite of what a version stamp is for.
        self.assertEqual(bundle["meta"]["chart_logic"], facts.CHART_LOGIC)


class TheRowsTheRendererReads(unittest.TestCase):
    def test_the_bundle_carries_the_rows_the_slide_prints_and_not_just_their_ranks(self):
        """⚠️ **The gap this closes, stated as a test.**

        A `rank.Ranked` row is `isbn`, `rank`, `weeks_on_chart`, `is_new`. Ticket 07's slide prints eight fields, so a
        bundle built from `Ranked` rows alone would render a hundred rank numerals beside blank space — and the fields
        would be missing from the *committed evidence*, so no later render could recover them.

        ⚠️ Asserted on the **serialised bundle**, not on the dataclass: the renderer reads JSON, and a field that
        survives `asdict` but not `json.dumps` would pass a test that never left Python.
        """
        bundle = facts.build(
            "2026-W41",
            charts={
                "bengali": facts.Chart(
                    books=enrich.build(
                        (
                            rank.Ranked(
                                # ⚠️ The work key, and the details map below uses the **same expression** (ticket 32)
                                # — `enrich.build` joins them, so a test that keyed them differently would silently
                                # exercise the "no details" path.
                                key=identity.work("Ekti Shonar Boi", "Sunil Gangopadhyay"),
                                isbn="9788172151234",
                                rank=1,
                                weeks_on_chart=2,
                                is_new=False,
                                # ⚠️ **The week's own sales term** — ticket 23's window reads this back on the next run,
                                # and a snapshot that did not carry it would contribute nothing to the six months.
                                score=1.4,
                            ),
                        ),
                        details={
                            identity.work("Ekti Shonar Boi", "Sunil Gangopadhyay"): enrich.Details(
                                title="Ekti Shonar Boi",
                                author="Sunil Gangopadhyay",
                                publisher="Ananda Publishers",
                                published="2026-10",
                                category="Literature & Fiction",
                                price=prices.Price(
                                    amount=399.0,
                                    retailer="amazon-in",
                                    edition="paperback",
                                    retailers=("amazon-in", "flipkart"),
                                ),
                                cover=covers.Cover(
                                    url="https://example.test/a.jpg", sha256="a"
                                ),
                                rating=4.3,
                                ratings_count=180,
                            )
                        },
                        previous={identity.work("Ekti Shonar Boi", "Sunil Gangopadhyay"): 4},
                    )
                )
            },
            window_weeks=7,
        )

        row = bundle["charts"]["bengali"]["ranked"][0]
        self.assertEqual(row["title"], "Ekti Shonar Boi")
        self.assertEqual(row["author"], "Sunil Gangopadhyay")
        self.assertEqual(row["publisher"], "Ananda Publishers")
        self.assertEqual(row["published"], "2026-10")
        self.assertEqual(row["genre"], "fiction")
        self.assertEqual(row["move"], 3)
        # ⚠️ **Ticket 23's evidence for the six-month window**, committed so the *next* run can accumulate it: the week's
        # sales term, and the review signal that cannot be re-fetched once the week is over.
        self.assertEqual(row["score"], 1.4)
        self.assertEqual(row["rating"], 4.3)
        self.assertEqual(row["ratings_count"], 180)
        self.assertEqual(row["price"]["amount"], 399.0)
        # ⚠️ The **count**, because it is what decides whether the slide may say "best" at all (ticket 04).
        self.assertEqual(len(row["price"]["retailers"]), 2)
        self.assertEqual(row["cover"]["url"], "https://example.test/a.jpg")
        self.assertEqual(row["identity"], "resolved")


class TheMarketBand(unittest.TestCase):
    def test_the_band_rides_at_the_root_and_is_absent_when_there_is_none(self):
        """⚠️ **Tickets 08 and 13 together: the scoreboard is not chart-specific.**

        It is fetched once and rendered into all four charts, so it belongs at the bundle root — and ⚠️ it is **absent**
        rather than `None`, because an absent key is the same *"we could not build this"* fact the renderer already
        handles for a chart, where a `None` would be a new shape it had to learn to ignore.
        """
        band = ticker.Ticker(
            rows=(ticker.Row(label_key="nifty50", close=24812.35, change=0.42),),
            as_of="2026-10-12",
        )

        with_band = facts.build(
            "2026-W41",
            charts={"bengali": chart("9788172151234")},
            window_weeks=7,
            ticker=band,
        )
        without = facts.build(
            "2026-W41", charts={"bengali": chart("9788172151234")}, window_weeks=7
        )

        self.assertEqual(with_band["ticker"]["as_of"], "2026-10-12")
        self.assertEqual(with_band["ticker"]["rows"][0]["label_key"], "nifty50")
        # ⚠️ **Values, not formatted strings** (ADR 0003) — the renderer decides the grouping and the sign.
        self.assertEqual(with_band["ticker"]["rows"][0]["close"], 24812.35)
        self.assertNotIn("ticker", without)


class TheLabelsInTheSnapshot(unittest.TestCase):
    """⚠️ Ticket 20 — and the snapshot is where they have to **be**, because a render cannot ask a list anything.

    ⚠️ **The renderer has no access to `charts.py`** — that is the entire point of the subprocess boundary (ADR 0003) —
    so a label that is not written into the committed evidence is a label the slide cannot draw, however well the list
    declared it.
    """

    def _row(self, **labels: str) -> dict:
        books = enrich.build(
            (rank.Ranked(key="9788172151234", isbn="9788172151234", rank=1, weeks_on_chart=0, is_new=False),),
            details={"9788172151234": enrich.Details(title="B", **labels)},  # type: ignore[arg-type]
            previous=None,
        )
        bundle = facts.build(
            "2026-W41", charts={"bengali": facts.Chart(books=books)}, window_weeks=1
        )
        return bundle["charts"]["bengali"]["ranked"][0]

    def test_every_row_carries_its_country_and_language(self):
        """⚠️ **Values, not names** — `bd` and `bn`, so the words stay the renderer's and a week built today re-renders
        with whatever the label table says later.
        """
        row = self._row(country="bd", language="bn")

        self.assertEqual(row["country"], "bd")
        self.assertEqual(row["language"], "bn")

    def test_a_row_with_no_labels_carries_empty_strings_rather_than_a_default(self):
        """⚠️ **Empty, and the renderer reads empty as *no label*.** A `None` here would be a key the renderer has to
        know to treat as absent — the same distinction ticket 08 draws for the ticker — and a defaulted `in` would put a
        country on every row of the English chart, where ticket 19 says neither label should appear.
        """
        row = self._row()

        self.assertEqual(row["country"], "")
        self.assertEqual(row["language"], "")


if __name__ == "__main__":
    unittest.main()
