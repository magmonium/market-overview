"""The repository's `.env` — the courtesy that lets a hand-run find a key without an `export` in every new shell.

⚠️ **What is worth testing here is not the parsing but the *rule*.** The format is a few lines of code; the thing that
can go wrong is a `.env` that quietly outranks the environment — because then a stale key looks like a live one, and
nothing on screen says so. So most of these assertions are about what is **left alone**.
"""
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from market_overview import env, store


class TheFileFormat(unittest.TestCase):
    """⚠️ `parse` is pure, so the format is pinned without touching a filesystem."""

    def test_a_pair_is_read(self):
        self.assertEqual(env.parse("NYT_API_KEY=abc123"), {"NYT_API_KEY": "abc123"})

    def test_blank_lines_and_comments_are_skipped(self):
        """⚠️ The two things every operator writes, and neither of them is a variable."""
        text = "\n# a note about the key\n\nKEY=value\n   \n# another\n"

        self.assertEqual(env.parse(text), {"KEY": "value"})

    def test_a_shell_export_is_accepted(self):
        """⚠️ Pasting `export KEY=…` out of a shell is the ordinary mistake, and accepting it costs nothing."""
        self.assertEqual(env.parse("export KEY=value"), {"KEY": "value"})

    def test_matching_quotes_are_stripped_and_only_one_layer(self):
        """⚠️ **One layer, and only a matching pair.** A token that genuinely begins and ends with the same character
        has to survive, so a lone quote is left exactly as it was typed — and an inner pair stays inner.
        """
        self.assertEqual(env.parse('A="quoted"'), {"A": "quoted"})
        self.assertEqual(env.parse("B='quoted'"), {"B": "quoted"})
        self.assertEqual(env.parse("""C="'inner'\""""), {"C": "'inner'"})
        self.assertEqual(env.parse('D="'), {"D": '"'})

    def test_a_value_keeps_its_own_equals_sign(self):
        """⚠️ **`partition`, not `split`.** A base64 key very often ends in `=`, and truncating it would produce a key
        that looks entirely correct and is refused by the vendor.
        """
        self.assertEqual(env.parse("KEY=aGVsbG8="), {"KEY": "aGVsbG8="})

    def test_a_line_that_is_not_a_pair_is_skipped_rather_than_fatal(self):
        """⚠️ The rule everywhere else in this product, applied to a courtesy: a malformed line is not a reason to
        lose a run.
        """
        self.assertEqual(env.parse("just some prose\n=nothing\nKEY=value"), {"KEY": "value"})


class FillingInTheEnvironment(unittest.TestCase):
    """⚠️ **The rule that matters: the environment wins.**

    A `.env` that could override an exported variable would be a *second* source of truth, and *"why is it using the
    old key"* would be a question with no visible answer. Every assertion below is about a variable being left alone.
    """

    def _with_file(self, text: str) -> mock._patch:
        """Point `env.path()` at a temporary file — the same seam discipline `store.root()` keeps."""
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = pathlib.Path(directory.name) / ".env"
        path.write_text(text, encoding="utf-8")
        return mock.patch.object(env, "path", return_value=path)

    def test_an_unset_variable_is_filled_in(self):
        with self._with_file("NYT_API_KEY=abc123\n"):
            with mock.patch.dict(os.environ, {}, clear=True):
                applied = env.load()

                self.assertEqual(os.environ["NYT_API_KEY"], "abc123")
                self.assertEqual(applied, {"NYT_API_KEY": "abc123"})

    def test_an_exported_variable_is_never_overridden(self):
        """⚠️ **The whole design in one assertion.** The file says one thing, the environment says another, and the
        environment is what the run uses.
        """
        with self._with_file("NYT_API_KEY=from-the-file\n"):
            with mock.patch.dict(os.environ, {"NYT_API_KEY": "from-the-shell"}):
                applied = env.load()

                self.assertEqual(os.environ["NYT_API_KEY"], "from-the-shell")
                self.assertEqual(applied, {})

    def test_an_empty_export_counts_as_unset(self):
        """⚠️ Matching `fetch.nyt`'s own `if not key:` — an empty export is not a key, so the file may supply one
        rather than leaving the run to fail on a blank.
        """
        with self._with_file("NYT_API_KEY=abc123\n"):
            with mock.patch.dict(os.environ, {"NYT_API_KEY": ""}):
                applied = env.load()

                self.assertEqual(os.environ["NYT_API_KEY"], "abc123")
                self.assertEqual(applied, {"NYT_API_KEY": "abc123"})

    def test_no_file_is_a_no_op(self):
        """⚠️ **The ordinary case, and it must be silent.** The environment alone is a complete configuration, so a
        checkout with no `.env` behaves exactly as it did before this module existed.
        """
        missing = pathlib.Path(tempfile.gettempdir()) / "definitely-not-a-real-dotenv-file"
        with mock.patch.object(env, "path", return_value=missing):
            with mock.patch.dict(os.environ, {}, clear=True):
                self.assertEqual(env.load(), {})
                self.assertEqual(dict(os.environ), {})

    def test_the_file_is_the_repositorys_and_not_a_projects(self):
        """⚠️ **One file, one answer.** `store/` sits at the repository root, so this has to be the same folder — two
        anchors that agree today is the shape of a bug that appears when one of them moves.
        """
        self.assertEqual(env.root(), store.root())
        self.assertEqual(env.path(), store.root() / ".env")


if __name__ == "__main__":
    unittest.main()
