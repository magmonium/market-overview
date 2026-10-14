"""Fixtures the books-brief tests share.

⚠️ **A temporary `store/` root, so no test writes into the repository.** `store/` is the committed evidence (ADR 0007)
— which is exactly why a test must not touch the real one: a stray write would appear as a diff in the operator's
working tree, and the suite would be editing the very thing it is meant to leave alone.
"""
from __future__ import annotations

import contextlib
import pathlib
import tempfile
from unittest import mock

from books_brief import store


@contextlib.contextmanager
def temporary_store():
    """Point `store.root()` at a temporary directory for the duration of a test.

    ⚠️ Patched on the module attribute rather than passed in, because `dir_for` calls `root()` by that name — the same
    seam discipline `paths.data_root` keeps, and the reason patching one function relocates the whole layout.
    """
    with tempfile.TemporaryDirectory() as name:
        root = pathlib.Path(name)
        with mock.patch.object(store, "root", return_value=root):
            yield root
