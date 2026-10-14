"""Tickets 09 and 10 — the snapshot: **the evidence, and it is committed.**

⚠️ `store/` is the one folder that stays in the project. The covers and the packages are *data* and live outside the
repository, under the shared root; this is *evidence*, and ADR 0007's rule is that it is committed — *"`store/` never
was gitignored, and that is the difference between the tool's evidence and its data."*
"""
import unittest

from books_brief import paths, store

from support import temporary_store


class WhereTheSnapshotLives(unittest.TestCase):
    def test_the_snapshot_is_keyed_by_iso_week_and_lives_in_the_project(self):
        """Ticket 10 keys a week by its **ISO week** — `2026-W41` — which sorts as a string and needs no state.

        ⚠️ And ticket 09 puts it in the **project**, not the data root. A `store/` that moved with
        `MARKET_OVERVIEW_DATA` would make the evidence a piece of the operator's data — which is precisely the
        distinction ADR 0007 draws, and the reason the brief's own `store.root()` is not `paths.data_root()`.
        """
        self.assertEqual(store.dir_for("2026-W41"), paths.project_root() / "store" / "2026-W41")


class TheSnapshotRoundTrip(unittest.TestCase):
    def test_a_bundle_written_to_the_snapshot_reads_back_unchanged(self):
        """⚠️ Tickets 18 and ADR 0003 — the snapshot **is** the rebuild path.

        A bundle that did not survive the round trip would make every re-render a re-fetch, and the week unreplayable —
        which is the whole reason `store/` is committed rather than gitignored.
        """
        bundle = {
            "meta": {"schema": 1, "week": "2026-W41", "chart_logic": 1, "window_weeks": 7},
            "charts": {"bengali": {"ranked": [], "watchlist": []}},
        }

        with temporary_store() as root:
            store.write_facts("2026-W41", bundle)

            # ⚠️ `store.root()` is the *project*, and `dir_for` appends `store/` — so the layout under a relocated root
            # is `<root>/store/<week>/`, not `<root>/<week>/`. Getting this wrong in the test rather than the code is
            # the good outcome; the first version of this assertion had it a level too high.
            self.assertTrue((root / "store" / "2026-W41" / "facts.json").is_file())
            self.assertEqual(store.read_facts("2026-W41"), bundle)


if __name__ == "__main__":
    unittest.main()
