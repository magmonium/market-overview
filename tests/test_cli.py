"""0085_03 — the spine, the abort contract, and the session guard.
0085_14 — fetch or re-render: the snapshot is what makes a past date rebuildable.
"""
import contextlib
import datetime as _datetime
import io
import json
import pathlib
import tempfile
import unittest
from unittest import mock

from market_overview import audio, cli, logo, package, metadata as metadata_module, render, store, universe
from market_overview.cli import main
from market_overview.fetch import bse, tradingview

BAR = 1791776700          # 2026-10-12 09:15 IST
MID_SESSION = 1791793800  # 2026-10-12 14:00 IST
FINAL = 1791801917        # 2026-10-12 16:15 IST
SUNDAY_BAR = BAR - 86400  # 2026-10-11 09:15 IST — a day that did not trade
OCT_8_BAR = BAR - 4 * 86400  # 2026-10-08 09:15 IST — an earlier session, for the rebuild test

SESSION = "2026-10-12"


def result(rows=None, *, name="tradingview-scan", total=None) -> tradingview.ScanResult:
    return tradingview.ScanResult(
        name=name, raw=b"{}", rows=dict(rows or {}), total_count=total
    )


def index_rows(*, bar=BAR, updated=FINAL) -> dict[str, dict[str, object]]:
    row = {"close": 22363.35, "change": -0.7, "time": bar, "last_bar_update_time": updated}
    for window in tradingview.WINDOWS:
        row.setdefault(window, 0.0)
    return {ticker: dict(row) for ticker in tradingview.INDEX_TICKERS}


# Fourteen distinct sectors, so the top-13 cut has something to cut and the sector guard passes.
SECTORS = (
    "Finance",
    "Producer Manufacturing",
    "Technology Services",
    "Consumer Durables",
    "Non-Energy Minerals",
    "Energy Minerals",
    "Health Technology",
    "Consumer Non-Durables",
    "Utilities",
    "Process Industries",
    "Communications",
    "Electronic Technology",
    "Transportation",
    "Industrial Services",
)


def world_rows(count: int = 16) -> dict[str, dict[str, object]]:
    """A small but *valid* universe: real members, plus one non-member to prove the floor."""

    def row(index: int, *, member: bool = True) -> dict[str, object]:
        return {
            "name": f"SYM{index}",
            "close": 100.0 + index,
            "change": 1.0 - index * 0.1,
            "volume": 10_000,
            "relative_volume_10d_calc": 2.0 + index * 0.1,
            "Value.Traded": 1.3e9,
            "market_cap_basic": 1e11 - index * 1e9,
            "sector": SECTORS[index % len(SECTORS)],
            "industry": "Something",
            "SMA50": 90.0,
            "SMA100": 80.0,
            "SMA200": 70.0,
            "Perf.W": 0.5,
            "Perf.1M": 1.0,
            "Perf.3M": 1.5,
            "Perf.6M": 2.0,
            "Perf.Y": 2.5,
            "indexes": [{"name": "Nifty 500", "proname": "NSE:CNX500"}] if member else [],
        }

    rows = {f"NSE:SYM{i}": row(i) for i in range(count)}
    rows["NSE:OUTSIDE"] = row(99, member=False)
    return rows


def broader_rows() -> dict[str, dict[str, object]]:
    row = {"close": 50_000.0}
    for window in tradingview.WINDOWS:
        row.setdefault(window, 0.0)
    return {ticker: dict(row) for ticker in universe.BROADER_TICKERS}


def _patched(module, name, value):
    """A return value — or, when handed an exception, a failure."""
    if isinstance(value, Exception):
        return mock.patch.object(module, name, side_effect=value)
    return mock.patch.object(module, name, return_value=value)


class Build(unittest.TestCase):
    def setUp(self):
        self.err, self.out = io.StringIO(), io.StringIO()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = pathlib.Path(self.tmp.name)

    def _run(
        self,
        argv,
        *,
        indexes=None,
        world=None,
        dependencies=None,
        bse_feeds=None,
        render_result=None,
        still_result=None,
        prepare=None,
        package_result=None,
    ):
        """Every test is hermetic: no network, no Remotion, no ffmpeg, `store/` in a temp dir.

        `prepare` is `None` (no bed supplied — the supported state), an exception (a refusal), or the
        `(path, report)` pair `audio.prepare` returns. ⚠️ It is patched unconditionally, so no test can reach the
        real ffmpeg even by accident. `still_result` and `package_result` are the same shape for the thumbnail
        (0085_12) and the metadata assembly (0085_13).
        """
        if indexes is None:
            indexes = result(index_rows(), name="tradingview-indexes")
        if world is None:
            rows = world_rows()
            world = result(rows, name="tradingview-universe", total=len(rows))
        if dependencies is None:
            dependencies = tradingview.ScanError("global scan down")
        # All four BSE feeds down unless a test says otherwise. "Everything degraded" is the
        # right default: a test must never reach the network, and it is also the state the
        # downgrade rules have to survive.
        feeds = {
            name: bse.BseError(f"{name} down")
            for name in ("flows", "actions", "ipos", "announcements")
        }
        feeds.update(bse_feeds or {})

        with contextlib.ExitStack() as stack:
            stack.enter_context(contextlib.redirect_stderr(self.err))
            stack.enter_context(contextlib.redirect_stdout(self.out))
            stack.enter_context(mock.patch.object(store, "root", return_value=self.store))
            # ⚠️ Recorded, not merely stubbed: the point of the audio tests is *what each edition was handed*, and
            # a `return_value` mock throws that away.
            self.render_calls = []

            def fake_render(*args, **kwargs):
                self.render_calls.append(mock.call(*args, **kwargs))
                if isinstance(render_result, BaseException):
                    raise render_result
                return render_result if render_result is not None else pathlib.Path("/tmp/brief.mp4")

            stack.enter_context(mock.patch.object(render, "render", side_effect=fake_render))
            # ⚠️ The still has to be stubbed too (0085_12). Left unpatched, every CLI test would fall through to a
            # real `remotion still` — slow, network-adjacent, and a test that passes only on a machine with Chrome.
            still_mock = mock.MagicMock(
                side_effect=still_result if isinstance(still_result, BaseException) else None,
                return_value=None
                if isinstance(still_result, BaseException)
                else (still_result or pathlib.Path("/tmp/thumbnail-bn.jpg")),
            )
            stack.enter_context(mock.patch.object(render, "still", still_mock))
            prepare_mock = mock.MagicMock(
                side_effect=prepare if isinstance(prepare, BaseException) else None,
                return_value=None if isinstance(prepare, BaseException) else prepare,
            )
            stack.enter_context(mock.patch.object(audio, "prepare", prepare_mock))
            # ⚠️ Assembly is stubbed with a **real `Metadata`**, not a Mock (0085_13). The CLI reads four of its
            # fields and prints them; a Mock would let a renamed field pass every test and fail in production.
            def fake_assemble(_date, lang):
                if isinstance(package_result, BaseException):
                    raise package_result
                return package_result or metadata_module.Metadata(
                    lang=lang,
                    date=_date,
                    title="title",
                    description="description",
                    tags=["a tag"],
                    hashtags=["#tag"],
                    thumbnail=render.thumbnail_name(_date, lang),
                    video=render.video_name(_date, lang),
                    bundle_hash="0" * 64,
                )

            stack.enter_context(mock.patch.object(package, "assemble", side_effect=fake_assemble))
            stack.enter_context(_patched(tradingview, "indexes", indexes))
            stack.enter_context(_patched(tradingview, "universe", world))
            stack.enter_context(_patched(tradingview, "dependencies", dependencies))
            stack.enter_context(
                mock.patch.object(
                    universe,
                    "fetch_broader",
                    return_value=result(broader_rows(), name="tradingview-broader"),
                )
            )
            for name, value in feeds.items():
                stack.enter_context(_patched(bse, name, value))
            code = main(argv)
        # ⚠️ Read *after* the patching unwinds, so the counts are the whole run's rather than a snapshot mid-call.
        self.prepare_call_count = prepare_mock.call_count
        self.still_calls = still_mock.call_args_list
        return code

    def _day(self, date=SESSION):
        return self.store / "store" / date

    def _snapshot(self, date=SESSION, *, indexes=None):
        """Run the fetch path once so the bundle on disk is a **real** one, and return its path.

        ⚠️ Built by running the tool rather than hand-written: `render.run_seconds` walks the bundle through
        `timeline.running_order`, so a hand-made `facts.json` would have to satisfy the schema anyway — and a
        test bundle that drifts from the real one is a test that quietly stops testing anything.
        """
        code = self._run(["build", "--date", date], indexes=indexes)
        self.assertEqual(code, 0, "the fetch path has to succeed before it can be re-rendered")
        return self._day(date) / store.FACTS

    # ── arguments ────────────────────────────────────────────────────────────────────

    def test_bad_date_shape_is_rejected(self):
        self.assertEqual(self._run(["build", "--date", "12/10/2026"]), 2)
        self.assertIn("YYYY-MM-DD", self.err.getvalue())

    def test_without_a_date_it_targets_today(self):
        """⚠️ `--date` is optional now: a bare `build` aims at **today**, so publishing the newest session is
        the default rather than something to remember to type. The guard is unchanged — today is only the date
        *asked for*, and a holiday refuses it exactly as it would a typed date.

        `_today` is the seam, patched here so the assertion does not depend on the wall clock."""
        with mock.patch.object(cli, "_today", return_value=SESSION):
            code = self._run(["build"])
        self.assertEqual(code, 0)
        self.assertEqual(self.render_calls[0].args[0], SESSION)

    def test_a_defaulted_today_is_still_refused_by_the_guard(self):
        """The default is a request, not an exemption: a `--date`-less run onto a holiday refuses and writes
        nothing, exactly as `build --date 2026-10-11` does."""
        with mock.patch.object(cli, "_today", return_value="2026-10-11"):
            code = self._run(["build"])
        self.assertEqual(code, 1)
        self.assertIn("newest session", self.err.getvalue())
        self.assertFalse((self.store / "store").exists())

    def test_today_is_the_wall_clock_date(self):
        """The seam answers with the real day, in the shape `--date` accepts."""
        self.assertEqual(cli._today(), _datetime.date.today().isoformat())

    # ── the session guard ────────────────────────────────────────────────────────────

    def test_a_holiday_refuses_and_writes_nothing(self):
        """⚠️ A holiday produces no error, only the previous session's numbers.

        The real shape: the operator asks for a day that did not trade, and the newest bar
        is still the last session that did.
        """
        code = self._run(["build", "--date", "2026-10-11"])
        self.assertEqual(code, 1)
        self.assertIn("newest session", self.err.getvalue())
        self.assertIn(SESSION, self.err.getvalue())
        self.assertFalse((self.store / "store").exists(), "a refused run wrote something")
        self.assertFalse((self.store / "output").exists())

    def test_a_clock_from_another_day_refuses(self):
        """The bar dates one session and its last update dates another — incoherent."""
        code = self._run(
            ["build", "--date", SESSION],
            indexes=result(index_rows(bar=SUNDAY_BAR), name="tradingview-indexes"),
        )
        self.assertEqual(code, 1)
        self.assertFalse((self.store / "store").exists())

    def test_a_mid_session_run_refuses(self):
        code = self._run(
            ["build", "--date", SESSION],
            indexes=result(index_rows(updated=MID_SESSION), name="tradingview-indexes"),
        )
        self.assertEqual(code, 1)
        self.assertIn("not finished printing", self.err.getvalue())
        self.assertFalse((self.store / "store").exists())

    def test_a_missing_clock_refuses(self):
        rows = index_rows()
        rows.pop("NSE:NIFTY")
        code = self._run(
            ["build", "--date", SESSION],
            indexes=result(rows, name="tradingview-indexes"),
        )
        self.assertEqual(code, 1)
        self.assertFalse((self.store / "store").exists())

    # ── the abort contract: the spine aborts, everything else degrades ───────────────

    def test_a_spine_failure_aborts_with_nothing_written(self):
        code = self._run(
            ["build", "--date", SESSION],
            indexes=tradingview.ScanError("spine down"),
        )
        self.assertEqual(code, 1)
        self.assertIn("refusing", self.err.getvalue())
        self.assertFalse((self.store / "store").exists())

    def test_a_universe_failure_aborts_too(self):
        """Breadth and DMA compute over it, so a truncation would move published numbers."""
        code = self._run(
            ["build", "--date", SESSION],
            world=tradingview.ScanError("expected 3199 rows, got 3000 — truncated"),
        )
        self.assertEqual(code, 1)
        self.assertIn("truncated", self.err.getvalue())
        self.assertFalse((self.store / "output").exists())

    # ── degrade to omission ──────────────────────────────────────────────────────────

    def test_a_failed_dependency_strip_degrades_and_the_run_still_succeeds(self):
        code = self._run(["build", "--date", SESSION])
        self.assertEqual(code, 0)
        self.assertIn("dependency strip omitted", self.err.getvalue())
        bundle = json.loads((self._day() / "facts.json").read_text(encoding="utf-8"))
        self.assertNotIn("dependencies", bundle)
        self.assertEqual(len(bundle["indexes"]), len(tradingview.INDEX_TICKERS))

    def test_a_failed_dependency_strip_is_absent_from_the_snapshots(self):
        self._run(["build", "--date", SESSION])
        raw = sorted(p.name for p in (self._day() / "raw").iterdir())
        self.assertEqual(
            raw,
            ["tradingview-broader.json", "tradingview-indexes.json", "tradingview-universe.json"],
        )

    # ── the happy path ───────────────────────────────────────────────────────────────

    def test_a_good_run_writes_the_bundle_and_every_snapshot(self):
        deps = result(
            {"NSE:INDIAVIX": {"close": 15.2, "change": 6.1, "Perf.Y": 50.7}},
            name="tradingview-dependencies",
        )
        code = self._run(["build", "--date", SESSION], dependencies=deps)

        self.assertEqual(code, 0)
        bundle = json.loads((self._day() / "facts.json").read_text(encoding="utf-8"))
        self.assertIn("dependencies", bundle)
        self.assertEqual(bundle["meta"]["date"], SESSION)

        raw = sorted(p.name for p in (self._day() / "raw").iterdir())
        self.assertEqual(
            raw,
            [
                "tradingview-broader.json",
                "tradingview-dependencies.json",
                "tradingview-indexes.json",
                "tradingview-universe.json",
            ],
        )

    def test_a_working_flow_feed_lands_in_the_bundle(self):
        """And the three feeds that are down cost only their own cards — never the run."""
        flows = bse.BseResult(
            name="CategoryTurnover",
            raw=b"{}",
            payload={
                "Table": [
                    {
                        "REPORTING_DATE": "2026-10-12T00:00:00",
                        "PURCHASE_BSENSE": 125832100000.0,
                        "SALE_BSENSE": 142916900000.0,
                        "NET_BSENSE": -17084800000.0,
                        "PURCHASE_DII": 155067300000.0,
                        "SALE_DII": 124617100000.0,
                        "NET_DII": 30450200000.0,
                    }
                ]
            },
        )
        code = self._run(["build", "--date", SESSION], bse_feeds={"flows": flows})

        self.assertEqual(code, 0)
        bundle = json.loads((self._day() / "facts.json").read_text(encoding="utf-8"))
        self.assertAlmostEqual(bundle["flows"]["fii"]["net"], -1708.48, places=2)
        self.assertAlmostEqual(bundle["flows"]["dii"]["net"], 3045.02, places=2)
        # the other three feeds are down, and their cards are simply absent
        for absent in ("corporate_actions", "ipos", "announcements"):
            self.assertNotIn(absent, bundle)

    def test_every_feed_down_still_produces_a_brief(self):
        """The spine is all that is required. Everything else can be missing."""
        self.assertEqual(self._run(["build", "--date", SESSION]), 0)

    def test_a_failed_edition_fails_the_run(self):
        code = self._run(
            ["build", "--date", SESSION],
            render_result=render.RenderError("chromium exploded"),
        )
        self.assertEqual(code, 1)
        self.assertIn("refusing to publish", self.err.getvalue())

    def test_an_unusable_mark_refuses_the_run_rather_than_tracebacking(self):
        """⚠️ 0085_10: an SVG whose text is not outlined is a **refusal**, and a refusal has to read like one.

        Uncaught, it would surface as a traceback — which reads as a broken tool rather than as an asset the
        operator can fix, and the fix is theirs to make. Catching it is the difference between "the tool is
        broken" and "outline your text, or send a PNG".
        """
        code = self._run(
            ["build", "--date", SESSION],
            render_result=logo.LogoError("logo.svg contains <text>; outline it to paths"),
        )
        self.assertEqual(code, 1)
        self.assertIn("refusing to publish", self.err.getvalue())
        self.assertIn("outline it to paths", self.err.getvalue())


    def test_an_unmixable_bed_refuses_the_run_rather_than_tracebacking(self):
        """⚠️ 0085_11: `AudioError` is the same shape of refusal as `LogoError`.

        ffmpeg's own message is the only description of *what to fix*, and the operator supplies the asset. A
        traceback reads as a broken tool; the message reads as a track to replace.
        """
        code = self._run(
            ["build", "--date", SESSION],
            prepare=audio.AudioError("music.wav is 4 s and the run is 175 s"),
        )
        self.assertEqual(code, 1)
        self.assertIn("refusing to publish", self.err.getvalue())
        self.assertIn("music.wav is 4 s", self.err.getvalue())

    def test_the_bed_is_prepared_once_and_handed_to_every_edition(self):
        """⚠️ **The whole of "both editions carry the same bed"**, asserted at the conductor (0085_11).

        Two languages are patched in deliberately: with the shipping `LANGUAGES` at one edition, "prepared once"
        would be true for the wrong reason. The requirement is that the two editions are handed *the same file*,
        which makes the guarantee structural rather than a claim about two ffmpeg runs agreeing.
        """
        bed = pathlib.Path("/tmp/.bed.wav")
        with mock.patch.object(cli, "LANGUAGES", ("bn", "en")):
            code = self._run(
                ["build", "--date", SESSION],
                prepare=(bed, "music: music.wav → .bed.wav (-14 LUFS, 175s)"),
            )
        self.assertEqual(code, 0)
        self.assertEqual(self.prepare_call_count, 1)
        self.assertEqual([call.kwargs["bed"] for call in self.render_calls], [bed, bed])

    def test_a_run_with_no_bed_supplied_still_renders_both_editions(self):
        """⚠️ The supported state: no `music.*` means a silent brief, not a failed run."""
        with mock.patch.object(cli, "LANGUAGES", ("bn", "en")):
            code = self._run(
                ["build", "--date", SESSION],
                render_result=None,
                prepare=None,
            )
        self.assertEqual(code, 0)
        self.assertEqual([call.kwargs["bed"] for call in self.render_calls], [None, None])

    def test_every_edition_gets_its_own_still(self):
        """⚠️ 0085_12, and the same argument as the bed but the opposite conclusion.

        The bed is rendered **once** for the run because issue 20 makes parity structural — one file, nothing to
        disagree about. The still is rendered **per edition** because it is *not* shared: issue 14 gives two stills
        whose text language differs, so rendering it once would ship a Bengali thumbnail in the English folder.
        """
        with mock.patch.object(cli, "LANGUAGES", ("bn", "en")):
            code = self._run(["build", "--date", SESSION])
        self.assertEqual(code, 0)
        self.assertEqual([call.args for call in self.still_calls], [(SESSION, "bn"), (SESSION, "en")])

    def test_a_failed_still_refuses_the_run(self):
        """⚠️ A language folder with a video and no thumbnail is an incomplete package — and a folder that *looks*
        finished is worse than one that errors, because nobody goes looking."""
        code = self._run(
            ["build", "--date", SESSION],
            still_result=render.RenderError("remotion still failed (1): jpeg encoder missing"),
        )
        self.assertEqual(code, 1)
        self.assertIn("refusing to publish", self.err.getvalue())
        self.assertIn("jpeg encoder missing", self.err.getvalue())

    def test_the_still_is_asked_for_with_only_the_edition(self):
        """⚠️ `render.still(day, lang)` and nothing more — every other input it needs it reads itself: the bundle from
        `store/<date>/` (ADR 0003) and the mark from `resource/`. A `bed` here would be a second way for the two
        surfaces to disagree, and the still has no audio to put one in anyway."""
        self._run(["build", "--date", SESSION])
        for call in self.still_calls:
            self.assertEqual(call.kwargs, {})


    # ── `--lang`: which editions a run builds ────────────────────────────────────────

    def test_no_lang_flag_builds_the_shipping_default(self):
        """⚠️ `--lang` is **additive**: with no flag the run is exactly what it always was. A flag that
        silently changed the default would be a delivery nobody asked for."""
        code = self._run(["build", "--date", SESSION])
        self.assertEqual(code, 0)
        self.assertEqual([call.args[1] for call in self.render_calls], list(cli.LANGUAGES))

    def test_lang_narrows_the_run_to_the_edition_named(self):
        """The point of the flag: build one edition without editing the module constant."""
        code = self._run(["build", "--date", SESSION, "--lang", "en"])
        self.assertEqual(code, 0)
        self.assertEqual([call.args[1] for call in self.render_calls], ["en"])
        # ⚠️ The still follows the video, not the default — a run for English must not leave a Bengali
        # thumbnail in a folder it never built.
        self.assertEqual([call.args[1] for call in self.still_calls], ["en"])

    def test_lang_takes_several_editions_and_keeps_their_order(self):
        code = self._run(["build", "--date", SESSION, "--lang", "en", "bn"])
        self.assertEqual(code, 0)
        self.assertEqual([call.args[1] for call in self.render_calls], ["en", "bn"])

    def test_a_language_repeated_is_rendered_once(self):
        code = self._run(["build", "--date", SESSION, "--lang", "bn", "bn"])
        self.assertEqual(code, 0)
        self.assertEqual([call.args[1] for call in self.render_calls], ["bn"])

    def test_an_unknown_language_is_a_usage_error(self):
        """⚠️ `choices`, so a typo is refused up front rather than pointed at a label table that is not there —
        and never at a folder nobody will upload."""
        with self.assertRaises(SystemExit) as caught:
            self._run(["build", "--date", SESSION, "--lang", "fr"])
        self.assertEqual(caught.exception.code, 2)


    # ── fetch, or re-render from the snapshot ────────────────────────────────────────

    def test_without_a_snapshot_the_fetch_is_what_writes_one(self):
        """The switch hangs on `exists()`, which is only safe because nothing writes a snapshot *before* the
        session guard admits the date — so finding one means the day was already established as final."""
        self.assertEqual(self._run(["build", "--date", SESSION]), 0)
        self.assertTrue(self._day().joinpath(store.FACTS).exists())
        self.assertIn("facts bundle written", self.out.getvalue())

    def test_a_snapshot_is_re_rendered_without_touching_the_network(self):
        """⚠️ The spine is patched to **fail**, and that is what gives this test teeth: if the re-render path
        reached for the wire even once — including for the session guard — the run would refuse instead of
        building. It builds, so nothing was fetched."""
        self._snapshot()
        code = self._run(["build", "--date", SESSION], indexes=tradingview.ScanError("network down"))
        self.assertEqual(code, 0)
        self.assertTrue(self.render_calls, "a re-render must still render")

    def test_the_re_render_says_which_file_it_read(self):
        """The two paths have to be tellable apart from the log alone: *"did that rebuild from the snapshot, or
        re-fetch?"* is the first question asked of any surprising number."""
        self._snapshot()
        self._run(["build", "--date", SESSION])
        self.assertIn(f"re-render: reading store/{SESSION}/{store.FACTS}", self.out.getvalue())

    def test_a_snapshot_is_what_makes_a_past_date_rebuildable(self):
        """⚠️ The rebuild promise itself, and it was **impossible to perform** before this ticket. On the fetch
        path a past date always refuses: the guard compares the date asked for against the newest session, which
        has moved on by definition. `04-data-ownership.md` — *"a video must be rebuildable without re-fetching;
        the numbers will have moved by the time anyone looks at it."*"""
        self._snapshot(
            "2026-10-08",
            indexes=result(
                index_rows(bar=OCT_8_BAR, updated=FINAL - 4 * 86400),
                name="tradingview-indexes",
            ),
        )
        # ⚠️ And the live scan is deliberately still the 12th, so the guard *would* refuse the 8th outright.
        code = self._run(["build", "--date", "2026-10-08"])
        self.assertEqual(code, 0)
        self.assertEqual(self.render_calls[0].args[0], "2026-10-08")


if __name__ == "__main__":
    unittest.main()
