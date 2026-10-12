"""The running order: fixed slots, and blocks dropped rather than shown empty."""
import unittest

from market_overview import timeline


def full_bundle(**overrides) -> dict:
    """Every block's needs present, so nothing is dropped unless a test drops it."""
    bundle: dict = {"meta": {}, "indexes": []}
    for needs in timeline.NEEDS.values():
        for need in needs:
            bundle.setdefault(need, [])
    bundle.update(overrides)
    for key in overrides:
        bundle.setdefault(key, [])
    return bundle


class Order(unittest.TestCase):
    def test_the_full_order_is_thirteen_blocks_totalling_the_measured_build(self):
        """⚠️ Thirteen, not fourteen: 0085_08 cut the heat map — see the note in `timeline.py`."""
        order = timeline.running_order(full_bundle())
        self.assertEqual(len(order), 13)
        self.assertEqual(timeline.total_frames(order), timeline.BUILD_SECONDS * timeline.FPS)

    def test_the_build_sits_inside_the_cap(self):
        """175.0 s of a 180 s cap. No longer a judgement: 175.0 is what the cards' reading time sums to, so
        the provisional figure ticket 01 wrote down turned out to be right and is now derived."""
        self.assertEqual(timeline.BUILD_SECONDS, 175)
        self.assertLess(timeline.BUILD_SECONDS, timeline.CAP_SECONDS)

    def test_the_blocks_are_contiguous_from_zero(self):
        order = timeline.running_order(full_bundle())
        expected = 0
        for block in order:
            self.assertEqual(block["from"], expected, block["key"])
            expected += block["duration"]
        self.assertEqual(expected, timeline.total_frames(order))

    def test_the_order_is_the_designed_one(self):
        keys = [block["key"] for block in timeline.running_order(full_bundle())]
        self.assertEqual(
            keys,
            [
                "disclosure",
                "cold_open",
                "indexes",
                "leaders",
                "most_active",
                "sectors",
                "breadth",
                "dma",
                "flows",
                "dependencies",
                "broader",
                "calendar",
                "close",
            ],
        )

    def test_the_ids_are_ticket_ones_stable_ids(self):
        """Deliberately not sequential: block 10 was vacant after insider activity retired."""
        ids = [block["id"] for block in timeline.running_order(full_bundle())]
        self.assertEqual(ids[2:5], ["2", "9", "13"])
        self.assertIn("10", ids)


class Omission(unittest.TestCase):
    def test_a_bundle_without_indexes_keeps_only_the_framing_blocks(self):
        """A bundle with no index scoreboard cannot exist — `facts.build` refuses one — but if it did, the cold open
        and the scoreboard would have no data and are dropped rather than scheduled empty.

        ⚠️ The close is **not** dropped: it quotes no figure any more, so it needs nothing from the bundle and is
        always scheduled. See `timeline.NEEDS`."""
        order = timeline.running_order({"meta": {}})
        self.assertEqual([block["key"] for block in order], ["disclosure", "close"])

    def test_the_minimum_valid_bundle_keeps_the_bookends(self):
        order = timeline.running_order({"meta": {}, "indexes": []})
        self.assertEqual(
            [block["key"] for block in order], ["disclosure", "cold_open", "indexes", "close"]
        )

    def test_the_heat_map_is_not_scheduled(self):
        """⚠️ **0085_08's cut, pinned.** The heat map reads the scoreboard's own list (ticket 26), so it cost
        the same thirteen units — 32.5 s to say the same thirteen sectors twice, in a brief where six cards
        were under their reading time and the cap had 5 s of headroom. With it, the cards needed 207.5 s
        against a 180 s cap.

        The component stays in `blocks.tsx` and stays registered in `MarketBrief`, so putting it back is one
        line. This test exists so that line has to be written deliberately, and so that whoever writes it
        reads the arithmetic first."""
        keys = [block["key"] for block in timeline.running_order(full_bundle())]
        self.assertNotIn("heat_map", keys)
        self.assertNotIn("heat_map", timeline.NEEDS, "a need for a block that is never scheduled is dead config")

    def test_the_calendar_survives_on_any_one_of_its_three_parts(self):
        for present in ("corporate_actions", "ipos", "announcements"):
            with self.subTest(present=present):
                bundle = full_bundle()
                for key in ("corporate_actions", "ipos", "announcements"):
                    bundle.pop(key)
                bundle[present] = [{"one": "row"}]
                keys = [block["key"] for block in timeline.running_order(bundle)]
                self.assertIn("calendar", keys)

    def test_the_calendar_goes_when_all_three_are_empty(self):
        bundle = full_bundle()
        for key in ("corporate_actions", "ipos", "announcements"):
            bundle.pop(key)
        keys = [block["key"] for block in timeline.running_order(bundle)]
        self.assertNotIn("calendar", keys)

    def test_a_thin_day_shortens_the_runtime_rather_than_slowing_it(self):
        """Ticket 01: a dropped block's slot is *removed*, not redistributed — so a thin day produces a
        shorter brief, never a slower one."""
        full = timeline.total_frames(timeline.running_order(full_bundle()))
        thin = timeline.total_frames(timeline.running_order({"meta": {}, "indexes": []}))
        self.assertLess(thin, full)
        # disclosure 5 + cold open 5 + index scoreboard 12.5 + close 7.5
        self.assertEqual(thin, round(30 * timeline.FPS))
        self.assertLess(thin, timeline.CAP_SECONDS * timeline.FPS)


if __name__ == "__main__":
    unittest.main()
