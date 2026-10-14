"""Ticket 09 — the render's subprocess boundary, and the trap the reel documented in its own source.

⚠️ **Both projects have a `remotion/index.ts`.** The reel's `render.where()` says it plainly: *"Run the render from the
repository and Remotion bundles the **brief's** root, then reports a missing composition and helpfully lists
`MarketBrief, Thumbnail, IndexCard`"* — a confusing failure a long way from its cause.

⚠️ So the entry is named **relative to this project's own tree**, and the chart rides as an **input prop** rather than
as a second bundle (ticket 13) — the same mechanism the brief uses for `lang`.
"""
import json
import pathlib
import unittest

from books_brief import paths, render


class TheCommand(unittest.TestCase):
    def test_the_entry_is_this_projects_not_the_briefs(self):
        """⚠️ The one thing that makes `remotion/index.ts` mean **ours**.

        Asserted against `paths.project_root()` — which is `src/books-brief` — so a future refactor that reached for the
        repository root instead would fail here rather than at render time with a missing-composition error.
        """
        self.assertEqual(
            render.entry(), paths.project_root() / "remotion" / "index.ts"
        )

    def test_the_chart_rides_as_an_input_prop_not_a_second_bundle(self):
        """⚠️ Ticket 13 — one bundle, four charts, the chart id read from props exactly as the brief reads `lang`.

        ⚠️ And the props are **JSON**, parsed here rather than string-matched: a substring check on a serialised dict
        passes for the wrong key order, the wrong nesting, and a `chart` that happens to appear in a filename.
        """
        argv = render.command(
            chart="bengali", week="2026-W41", output=pathlib.Path("/tmp/out.mp4")
        )

        props = argv[argv.index("--props") + 1]
        self.assertEqual(json.loads(props), {"chart": "bengali", "week": "2026-W41"})


if __name__ == "__main__":
    unittest.main()
