"""0087_03, 0087_07, 0087_08 — the render step: what it runs, and what it refuses to break.

⚠️ **No test here renders anything.** What is pinned is the *subprocess boundary* — the command, the props file,
and the order the output moves in — and the fakes are what make the failure cases reachable at all: Remotion cannot
be made to die at 90% on demand, and the property that matters most is precisely what happens when it does.

⚠️ The failure fake raises **the brief's** `RenderError`, not the reel's, so the translation is covered rather
than assumed: one boundary, one error type, and the message survives it.
"""
import json
import pathlib
import tempfile
import unittest
from unittest import mock

from market_overview import audio
from market_overview.render import RenderError as BriefRenderError
from song_video import package, plan, render, sound

SONG = "dure-kothay"

#: The master's digest, as a record holds it. ⚠️ The seed of everything per-song, which is why the tests pass a
#: *digest* rather than a title: the look has to follow the record, not the string a human typed.
DIGEST = "78ff162da9dcaf902ca5bca4fe90276d8cfefe02866e4c1f1ff3cba8cc8683f6"


def a_job(theme: str = "vinyl") -> plan.Job:
    return plan.Job(
        song=SONG,
        title="দূরে কোথায় (Dure Kothay)",
        theme=theme,
        wave="ribbon",
        fps=30,
        duration_seconds=214.556,
    )


class Renders(unittest.TestCase):
    """A stage, a job, and a stand-in for the brief's streamer."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.where = pathlib.Path(self._tmp.name)
        self.stage = render.Stage(
            root=self.where,
            output_dir=self.where / "output",
            staged="dure-kothay.mp3",
            cover=None,
            seed=DIGEST,
            lang="bn",
            mark={"src": "data:image/png;base64,AAAA", "chip": "#111721"},
        )
        self.commands: list[list[str]] = []

        # ⚠️ **The delivery guard measures real files, and these fakes write stub bytes.** So the measurement is
        # stubbed for *every* test here, exactly as `_stream` is — otherwise "the render wrote a file" would be
        # indistinguishable from "the render wrote the song", and the guard's own test could never reach its branch.
        def measured(path: pathlib.Path):
            if path.suffix == ".mp4":
                return sound.Audio(codec="aac", sample_rate=48000, channels=2, bitrate=317374)
            return sound.Audio(codec="mp3", sample_rate=48000, channels=2, bitrate=171960)

        patcher = mock.patch.object(render.sound, "measure", side_effect=measured)
        patcher.start()
        self.addCleanup(patcher.stop)

    def fake(self, *, writes: bool = True, size: int = 1024, failure: Exception | None = None):
        """What Remotion would do, as far as this side can see: be handed a command, then write — or die."""

        def stream(command: list[str], *, cwd: pathlib.Path, timeout: float | None, label: str) -> None:
            self.commands.append(command)
            if failure is not None:
                raise failure
            if writes:
                # The output is the argument after the composition id, in both verbs.
                pathlib.Path(command[5]).write_bytes(b"x" * size)

        return mock.patch.object(render, "_stream", stream)


class TheCommand(Renders):
    def test_the_still_is_its_own_composition_at_frame_zero(self):
        job = a_job()
        with self.fake():
            target = render.thumbnail(self.stage, job)

        command = self.commands[0]
        self.assertEqual(command[:4], ["npx", "remotion", "still", render.ENTRY])
        self.assertEqual(command[4], "SongReelThumbnail", "the still's own composition, never a grabbed frame")
        self.assertIn("--frame=0", command, "the still has no entrance, so frame 0 is the settled state")
        self.assertIn("--image-format=jpeg", command)
        self.assertIn("--overwrite", command)
        self.assertEqual(target, package.thumbnail(self.stage.output_dir, job))
        self.assertTrue(target.exists())

    def test_the_reel_renders_with_the_pinned_codec_and_the_songs_own_audio(self):
        with self.fake():
            render.video(self.stage, a_job("neon"))

        command = self.commands[0]
        self.assertEqual(command[4], "SongReel")
        # ⚠️ Named, not defaulted: issue 03 pins these, and a Remotion default change is invisible downstream.
        self.assertIn("--codec=h264", command)
        self.assertIn("--pixel-format=yuv420p", command)
        # ⚠️ And the song is *heard*: the reel has no second audio step, so this is the only place the level of
        # the shipped audio is decided.
        self.assertIn(f"--audio-bitrate={render.AUDIO_BITRATE}", command)
        # ⚠️ **The number, not only the flag.** Issue 09 asks for a *high-bitrate* encode because the music is the
        # content; a test that compared the constant to itself would let 128k through as a one-line change. The
        # brief's own 192k is a bed under speech, and a song is not a bed.
        self.assertEqual(render.AUDIO_BITRATE, "320k")
        self.assertNotEqual(render.AUDIO_BITRATE, audio.BITRATE, "the brief's trade-off is not the song's")
        self.assertNotIn("--mute", command)

    def test_the_props_file_is_the_whole_input_as_one_flat_object(self):
        job = a_job("parchment")
        stage = render.Stage(
            root=self.stage.root,
            output_dir=self.stage.output_dir,
            staged="dure-kothay.mp3",
            cover="dure-kothay.jpg",
            seed=DIGEST,
            lang="bn",
            mark=self.stage.mark,
        )
        wrapper_seen: dict = {}

        def stream(command: list[str], *, cwd: pathlib.Path, timeout: float | None, label: str) -> None:
            wrapper = pathlib.Path(command[6].removeprefix("--props="))
            wrapper_seen["path"] = wrapper
            wrapper_seen["json"] = json.loads(wrapper.read_text(encoding="utf-8"))
            pathlib.Path(command[5]).write_bytes(b"x")

        with mock.patch.object(render, "_stream", stream):
            render.thumbnail(stage, job)

        self.assertEqual(
            wrapper_seen["json"],
            {
                "title": job.title,
                "song": "dure-kothay.mp3",
                "theme": "parchment",
                "cover": "dure-kothay.jpg",
                "frames": 6437,
                "mark": stage.mark,
                # ⚠️ The recorded digest, which is what the render layer derives the piece's accent and its light's
                # paths from — the whole of what makes two songs different and one song reproducible.
                "seed": DIGEST,
                "lang": "bn",
                # ⚠️ The value half of the still's caption, in Bengali numerals — the word half lives in the render
                # layer, and this is the pair that has to meet in the middle.
                "duration": "৩:৩৫",
            },
            "the props are the whole input, and Python's frame count is the piece's length",
        )
        self.assertIn("parchment", wrapper_seen["path"].name, "one props file per render, named for it")
        self.assertTrue(wrapper_seen["path"].name.startswith("."), "hidden: a crash must not leave it legible")
        self.assertFalse(wrapper_seen["path"].exists(), "and it is removed when the render is over")


class WhatIsNeverBroken(Renders):
    def test_the_package_is_not_opened_until_the_render_is_whole(self):
        """⚠️ `--overwrite` unlinks its target, so the render must be pointed at scratch — never at the package."""
        job = a_job()
        target = package.reel(self.stage.output_dir, job)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"the previous run's reel")
        looked_at: list[tuple[str, int]] = []

        def stream(command: list[str], *, cwd: pathlib.Path, timeout: float | None, label: str) -> None:
            output = pathlib.Path(command[5])
            looked_at.append((output.name, target.stat().st_size))
            output.write_bytes(b"the new reel")

        with mock.patch.object(render, "_stream", stream):
            render.video(self.stage, job)

        for name, previous_size in looked_at:
            self.assertTrue(name.startswith("."), "the render writes a scratch name, not the deliverable's")
            self.assertEqual(previous_size, len(b"the previous run's reel"), "the package is untouched as it runs")
        self.assertEqual(target.read_bytes(), b"the new reel", "and it is replaced once the render is whole")
        self.assertEqual(list(target.parent.glob(".*")), [], "no scratch and no props left behind")

    def test_a_render_that_dies_leaves_the_previous_package_exactly_as_it_was(self):
        job = a_job()
        target = package.reel(self.stage.output_dir, job)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"the previous run's reel")

        with self.fake(failure=BriefRenderError("remotion render (vinyl) failed (1):\nTarget closed")):
            with self.assertRaises(render.RenderError) as caught:
                render.video(self.stage, job)

        self.assertIn("Target closed", str(caught.exception), "the reason survives the boundary")
        self.assertEqual(target.read_bytes(), b"the previous run's reel", "the good file is still the good file")
        self.assertEqual(list(target.parent.glob(".*")), [], "and the run left no litter in the package")

    def test_a_render_that_writes_nothing_is_refused(self):
        with self.fake(writes=False):
            with self.assertRaises(render.RenderError) as caught:
                render.video(self.stage, a_job())

        self.assertIn("wrote nothing", str(caught.exception))
        self.assertFalse(package.reel(self.stage.output_dir, a_job()).exists())

    def test_a_delivery_that_lost_the_song_is_refused_before_it_reaches_the_package(self):
        """⚠️ **The check nothing else in this pipeline had.** The master is digest-guarded and the still is
        size-guarded, but the audio *inside* the reel was never looked at: a render that dropped the track, halved the
        rate or re-encoded it cheaply would have shipped a file that is a file. It is refused **before** the move, so a
        bad delivery cannot cost the previous good reel."""
        target = package.reel(self.stage.output_dir, a_job())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"the previous run's reel")

        with mock.patch.object(render.sound, "measure", return_value=None), self.fake():
            with self.assertRaises(render.RenderError) as caught:
                render.video(self.stage, a_job())

        self.assertIn("lost the song", str(caught.exception))
        self.assertIn("silent", str(caught.exception), "and it says which part of it went missing")
        self.assertEqual(target.read_bytes(), b"the previous run's reel", "the good file is still the good file")
        self.assertEqual(list(target.parent.glob(".*")), [], "and the failed render left no litter either")

    def test_a_still_over_the_ceiling_is_refused_rather_than_shipped(self):
        over = render.MAX_STILL_BYTES + 1
        with self.fake(size=over):
            with self.assertRaises(render.RenderError) as caught:
                render.thumbnail(self.stage, a_job())

        self.assertIn("ceiling", str(caught.exception))
        self.assertFalse(package.thumbnail(self.stage.output_dir, a_job()).exists())

    def test_a_missing_toolchain_says_which_directory_it_looked_in(self):
        with mock.patch.object(render, "_stream", side_effect=FileNotFoundError("npx")):
            with self.assertRaises(render.RenderError) as caught:
                render.video(self.stage, a_job())

        self.assertIn("node_modules", str(caught.exception))


class WhereTheRenderRuns(unittest.TestCase):
    def test_the_entry_is_the_reel_s_own_and_registers_the_compositions_this_module_names(self):
        """⚠️ **Both projects have a `remotion/index.ts`.** Running the render from the repository resolves `ENTRY`
        to the *brief's* entry — and Remotion then reports a missing composition, helpfully listing
        `MarketBrief, Thumbnail, IndexCard`. That failure is seconds long and completely convincing, which is why
        this asserts the *tree* rather than the string: the ids invoked here have to be registered there.
        """
        self.assertTrue((render.where() / render.ENTRY).is_file(), "the entry named here is the reel's")

        root = (render.where() / "remotion" / "Root.tsx").read_text(encoding="utf-8")
        for composition in (render.REEL, render.THUMBNAIL):
            self.assertIn(
                f'id="{composition}"',
                root,
                f"{composition} must be registered where this module runs",
            )


if __name__ == "__main__":
    unittest.main()
