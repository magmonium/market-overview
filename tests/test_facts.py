"""The bundle contract — values and label keys, never display strings (ADR 0003)."""
import json
import unittest

from market_overview import facts
from market_overview.fetch import tradingview

BAR = 1791776700      # 2026-10-12 09:15 IST
FINAL = 1791801917    # 2026-10-12 16:15 IST


def result(rows=None, *, name="tradingview-indexes", total=None) -> tradingview.ScanResult:
    return tradingview.ScanResult(
        name=name,
        raw=json.dumps({"totalCount": total or 0, "data": []}).encode(),
        rows=dict(rows or {}),
        total_count=total,
    )


def index_rows(change: float = -0.7) -> dict[str, dict[str, object]]:
    row = {
        "close": 22363.35,
        "change": change,
        "time": BAR,
        "last_bar_update_time": FINAL,
    }
    for window in tradingview.WINDOWS:
        row.setdefault(window, 0.0)
    return {ticker: dict(row) for ticker in tradingview.INDEX_TICKERS}


def dependency_rows() -> dict[str, dict[str, object]]:
    row = {"close": 1.0, "change": 0.5, "Perf.W": 0.1, "Perf.1M": 0.2, "Perf.Y": 0.3}
    return {ticker: dict(row) for ticker in tradingview.DEPENDENCY_TICKERS}


def strings(node, path=""):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from strings(value, f"{path}.{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from strings(value, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


class Bundle(unittest.TestCase):
    def test_every_index_carries_all_six_windows(self):
        bundle = facts.build("2026-10-12", indexes=result(index_rows()))
        self.assertEqual(len(bundle["indexes"]), len(tradingview.INDEX_TICKERS))
        for index in bundle["indexes"]:
            self.assertEqual(set(index["window"]), set(tradingview.WINDOWS))

    def test_only_identifiers_are_strings(self):
        """ADR 0003: a display string in the bundle is a bug, not a shortcut."""
        bundle = facts.build("2026-10-12", indexes=result(index_rows()))
        leaves = {path.split(".")[-1].split("[")[0] for path, _ in strings(bundle)}
        self.assertLessEqual(
            leaves, {"ticker", "label_key", "date", "source", "id", "key"}, leaves
        )

    def test_label_keys_are_slugs_not_tickers(self):
        bundle = facts.build("2026-10-12", indexes=result(index_rows()))
        keys = [i["label_key"] for i in bundle["indexes"]]
        self.assertEqual(keys[0], "nifty50")
        self.assertNotIn("NSE:NIFTY", keys)

    def test_a_missing_number_is_null_not_zero(self):
        rows = index_rows()
        rows["NSE:NIFTY"]["change"] = None
        bundle = facts.build("2026-10-12", indexes=result(rows))
        nifty = next(i for i in bundle["indexes"] if i["label_key"] == "nifty50")
        self.assertIsNone(nifty["window"]["change"])

    def test_a_short_spine_is_refused(self):
        rows = index_rows()
        rows.pop("NSE:NIFTYJR")
        with self.assertRaises(tradingview.MissingTickersError) as caught:
            facts.build("2026-10-12", indexes=result(rows))
        self.assertIn("NSE:NIFTYJR", str(caught.exception))

    def test_dependencies_are_omitted_when_absent(self):
        """Degrade to omission — never a card of zeros pretending the world was flat."""
        bundle = facts.build("2026-10-12", indexes=result(index_rows()))
        self.assertNotIn("dependencies", bundle)

    def test_dependencies_carry_their_own_label_keys(self):
        bundle = facts.build(
            "2026-10-12",
            indexes=result(index_rows()),
            dependencies=result(dependency_rows(), name="tradingview-dependencies"),
        )
        keys = [d["label_key"] for d in bundle["dependencies"]]
        self.assertEqual(len(keys), len(tradingview.DEPENDENCY_TICKERS))
        self.assertIn("brent", keys)
        self.assertIn("indiavix", keys)


class Clock(unittest.TestCase):
    def test_the_clock_comes_from_the_indian_bar(self):
        """Not from the dependency strip: TVC:GOLD ran to 18:59 IST on the same day."""
        bar, updated = facts.stamps(result(index_rows()))
        self.assertEqual((bar, updated), (BAR, FINAL))

    def test_no_clock_row_is_refused(self):
        rows = index_rows()
        rows.pop(facts.CLOCK_TICKER)
        with self.assertRaises(tradingview.MissingTickersError):
            facts.stamps(result(rows))

    def test_a_clock_without_timestamps_is_refused(self):
        rows = index_rows()
        rows[facts.CLOCK_TICKER].pop("last_bar_update_time")
        with self.assertRaises(tradingview.ScanShapeError):
            facts.stamps(result(rows))


if __name__ == "__main__":
    unittest.main()
