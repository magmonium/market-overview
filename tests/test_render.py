"""The render subprocess boundary — progress forwarding and the failure tail.

⚠️ `render._stream` exists so a long render **looks alive**: it forwards the renderer's output instead of
swallowing it. That is the behaviour a two-edition run depends on, and it fails silently if it regresses — a
`capture_output` creeping back in would leave every test in the suite green while the operator goes back to
staring at nothing for an hour. So the two properties are pinned directly here, on a real child process rather
than a mock: output is forwarded **as it is produced**, and a non-zero exit still carries a reason.
"""
from __future__ import annotations

import contextlib
import io
import os
import pathlib
import sys
import tempfile
import threading
import unittest
from unittest import mock

from market_overview import render


class Stream(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cwd = pathlib.Path(self.tmp.name)

    @staticmethod
    def _python(script: str) -> list[str]:
        return [sys.executable, "-c", script]

    def _run(self, command, *, timeout=None, label="remotion render") -> str:
        """Drive `_stream` with its stdout captured, returning exactly what it forwarded."""
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            render._stream(command, cwd=self.cwd, timeout=timeout, label=label)
        return captured.getvalue()

    def test_the_renderer_output_is_forwarded(self):
        """The whole point: what the child prints reaches the operator's terminal."""
        printed = self._run(self._python("print('Bundling 100%'); print('Rendered 2/2')"))
        self.assertIn("Bundling 100%", printed)
        self.assertIn("Rendered 2/2", printed)

    def test_progress_is_forwarded_while_the_process_is_still_running(self):
        """⚠️ **Liveness** — the property a `capture_output` regression would break without any other test
        noticing. The child prints one line and then sleeps; that line must be visible *before* the process
        exits. Captured at the end, this test would see the line only after `done` had already been set.
        """
        appeared = threading.Event()
        finished = threading.Event()

        class _Watching(io.StringIO):
            def write(self, text):
                if "Rendered 1/9" in text:
                    appeared.set()
                return super().write(text)

        def worker():
            with contextlib.redirect_stdout(_Watching()):
                render._stream(
                    self._python("import time; print('Rendered 1/9', flush=True); time.sleep(2)"),
                    cwd=self.cwd,
                    timeout=None,
                    label="remotion render",
                )
            finished.set()

        thread = threading.Thread(target=worker)
        thread.start()
        try:
            self.assertTrue(appeared.wait(10), "nothing was forwarded while the render was still running")
            self.assertFalse(
                finished.is_set(),
                "the line only arrived after the process had already exited — that is capture, not stream",
            )
        finally:
            thread.join(timeout=10)

    def test_a_non_zero_exit_keeps_the_reason(self):
        """Forwarding must not cost the failure message: the tail still explains *why*, under the label."""
        with self.assertRaises(render.RenderError) as caught:
            self._run(self._python("import sys; print('the encoder exploded'); sys.exit(3)"))
        message = str(caught.exception)
        self.assertIn("remotion render failed (3)", message)
        self.assertIn("the encoder exploded", message)

    def test_the_failure_tail_is_bounded_but_keeps_the_end(self):
        """⚠️ Bounded on purpose: a run is thousands of progress lines and the reason is always at the end, so
        the buffer keeps the last `TAIL_LINES` and drops the rest."""
        count = render.TAIL_LINES + 5
        script = f"import sys; [print(f'line {{i}}') for i in range({count})]; sys.exit(2)"
        with self.assertRaises(render.RenderError) as caught:
            self._run(self._python(script))
        message = str(caught.exception)
        self.assertIn(f"line {count - 1}", message, "the last line must survive")
        self.assertNotIn("line 0", message, "the tail must be bounded, not a full transcript")

    def test_a_timeout_is_a_render_error_not_a_hang(self):
        """A render that overruns its deadline is refused with a reason, rather than blocking forever."""
        with self.assertRaises(render.RenderError) as caught:
            self._run(self._python("import time; time.sleep(30)"), timeout=0.5)
        self.assertIn("timed out", str(caught.exception))

    def test_a_missing_toolchain_surfaces_as_file_not_found(self):
        """⚠️ Deliberately not swallowed in `_stream`: the call sites name it a `render toolchain missing`
        refusal, and that message is only reachable if this exception escapes."""
        with self.assertRaises(FileNotFoundError):
            self._run([str(self.cwd / "npx-that-is-not-there")])


class Concurrency(unittest.TestCase):
    """`MARKET_OVERVIEW_CONCURRENCY` — parallelism only, never a different picture.

    ⚠️ The point of the knob is that it is **safe**: the world is a pure function of the frame index, so more
    tabs render the same frames sooner. These tests pin the flag's shape and, more importantly, that a bad value
    degrades to "no flag" rather than to a failed run.
    """

    def test_no_variable_means_remotions_own_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(render._concurrency_flag(), [])

    def test_a_number_becomes_the_flag(self):
        with mock.patch.dict(os.environ, {render.CONCURRENCY_ENV: "10"}):
            self.assertEqual(render._concurrency_flag(), ["--concurrency=10"])

    def test_a_nonsense_value_is_ignored_rather_than_fatal(self):
        for bad in ("", "fast", "0", "-2", "   "):
            with self.subTest(value=bad), mock.patch.dict(os.environ, {render.CONCURRENCY_ENV: bad}):
                self.assertEqual(render._concurrency_flag(), [])


if __name__ == "__main__":
    unittest.main()
