"""The music bed — the toolchain, the level, and the one encoding. (0085_11)

⚠️ Why these are worth having at all: **the tools this needs are the tools Remotion's ffmpeg does not have.**
That build is `--disable-filters` with an allow-list, so `afade`, `acrossfade`, `volumedetect` and `astats` are all
absent — the obvious way to fade a bed, and the obvious way to *check* that you faded it, are both missing. So the
suite does three things the module cannot do for itself:

1. **Asserts the allow-list directly** (`Toolchain`). A filter this build lacks is a failure here, in a test, rather
   than at 18:00 on the day the operator finally drops in a track.
2. **Measures the fade rather than trusting the filtergraph** (`Level`). A `volume` expression that parses and
   evaluates to `1` everywhere is indistinguishable from one that works — the same silent-failure shape as a
   0-opacity draw. So the bed is measured segment by segment and compared against a bed built without the fade.
3. **Checks the master is untouched** (`Prepare`). "Never modified in place" is the one promise made to the
   operator about the file they supplied, and it is the easiest thing to break by accident.

⚠️ Every test that needs ffmpeg is skipped without it, so the suite still runs on a machine that has never
`npm install`ed. The measurements only mean something with the real encoder, so they are not faked.
"""
import contextlib
import io
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from market_overview import audio, logo, paths, render, store

ROOT = pathlib.Path(__file__).resolve().parents[1]


def ffmpeg_available() -> bool:
    try:
        audio.binary(ROOT)
    except audio.AudioError:
        return False
    return True


HAVE_FFMPEG = ffmpeg_available()
needs_ffmpeg = unittest.skipUnless(HAVE_FFMPEG, "no ffmpeg — Remotion's bundled build or a system one")


def make_bed(path: pathlib.Path, seconds: float = 20.0, *, frequency: int = 220) -> pathlib.Path:
    """A stand-in master. ⚠️ A generated tone, not a shipped asset: the suite must not depend on a licensed file,
    and a sine is exactly what makes the fade measurable — its level is flat by construction, so any variation in
    the output is the pipeline's doing and nothing else.
    """
    audio.run(
        audio.binary(ROOT),
        [
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={frequency}:sample_rate=44100:duration={seconds:g}",
            "-c:a",
            "pcm_s16le",
            "-y",
            str(path),
        ],
    )
    return path


def measure_lufs(path: pathlib.Path, start: float, length: float) -> float | None:
    """The integrated loudness of one segment, in LUFS.

    ⚠️ `loudnorm`'s analysis mode, because it is the only loudness instrument this build has — `volumedetect` and
    `astats` are both absent. Its "Input Integrated" line *is* a measurement of whatever it was pointed at, which
    makes it usable as a meter when the target is quoted back at you.

    ⚠️ Deliberately **not** `audio.run`: that forces `-loglevel error`, and the summary this reads is emitted at
    INFO. Suppressing it is a quiet way to measure nothing at all and get `None` back — which every assertion here
    would then have to treat as a failure to notice rather than a value to compare.
    """
    ffmpeg = audio.binary(ROOT)
    env = dict(os.environ)
    env.update(audio.binary_env(ffmpeg))
    completed = subprocess.run(
        [
            str(ffmpeg),
            "-hide_banner",
            "-nostats",
            "-ss",
            f"{start:g}",
            "-t",
            f"{length:g}",
            "-i",
            str(path),
            "-af",
            "loudnorm=print_format=summary",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    for line in (completed.stderr or "").splitlines():
        if "Input Integrated" in line:
            value = line.split(":")[-1].strip().split()[0]
            return None if value == "-inf" else float(value)
    return None


#: One scratch directory for the whole module, and one normalised bed built in it. ⚠️ The encode is the slow part,
#: so it happens once: a per-test fixture would make this suite a minute long and start getting skipped in a hurry.
_TMP = tempfile.TemporaryDirectory()
BED_SECONDS = 12.0
_bed: pathlib.Path | None = None


def tearDownModule() -> None:
    _TMP.cleanup()


def bed() -> pathlib.Path:
    """A normalised bed, built on first use. 20 s of master trimmed to `BED_SECONDS`, so the trim has to work."""
    global _bed
    if _bed is None:
        root = pathlib.Path(_TMP.name)
        resource = root / "resource"
        resource.mkdir(exist_ok=True)
        make_bed(resource / "music.wav", 20.0)
        prepared = audio.prepare(
            root / "output" / "2026-10-12", BED_SECONDS, root=ROOT, resource=resource
        )
        assert prepared is not None
        _bed = prepared[0]
    return _bed


def listing(*args: str) -> str:
    """ffmpeg's own capability output, for the assertions below.

    ⚠️ Through `audio.run`, never a bare `subprocess.run`. The bundled build is `--enable-shared` and **aborts with
    nothing on stdout** unless `DYLD_LIBRARY_PATH` points at its own directory — so invoking it directly makes these
    assertions compare against the empty string and pass vacuously in the one direction that matters (a filter
    reported *absent* when it is present). `run` is what applies `binary_env`.
    """
    return audio.run(audio.binary(ROOT), list(args))


class Toolchain(unittest.TestCase):
    """⚠️ The promise the module makes in its docstring, asserted rather than assumed."""

    def test_the_binary_we_find_actually_has_the_filters_we_use(self):
        """A filter the build lacks is a daily `ffmpeg failed (-22)`, not a subtle error.

        ⚠️ And the failure would land at 18:00 on the day the operator first supplies a track, having passed every
        test up to then. `loudnorm` is the one that matters most: it is the whole loudness promise.
        """
        if not HAVE_FFMPEG:
            self.skipTest("no ffmpeg")
        found = listing("-filters")
        self.assertTrue(found.strip(), "ffmpeg produced no listing — the env is wrong, not the build")
        for name in audio.REQUIRED_FILTERS:
            with self.subTest(filter=name):
                self.assertRegex(found, rf"\b{name}\b")

    def test_the_encoders_and_muxers_we_use_are_there(self):
        """⚠️ Queried **separately**: ffmpeg honours only the last of `-encoders -muxers`, so asking for both
        prints one listing and the other's assertions then measure nothing."""
        if not HAVE_FFMPEG:
            self.skipTest("no ffmpeg")
        encoders = listing("-encoders")
        muxers = listing("-muxers")
        for name in audio.REQUIRED_ENCODERS:
            with self.subTest(encoder=name):
                self.assertRegex(encoders, rf"\b{name}\b")
        # ⚠️ `wav` and `mp4` are **muxers**, and they are the pair the module names explicitly with `-f`. That
        # explicitness is the fix for a real failure: a staging file called `x.mp4.muxing` has no extension ffmpeg
        # recognises, so an implicit format made every mux fail with `Unable to choose an output format`.
        for name in ("wav", "mp4"):
            with self.subTest(muxer=name):
                self.assertRegex(muxers, rf"\b{name}\b")

    def test_the_obvious_tools_are_absent_which_is_why_the_graph_looks_like_this(self):
        """A guard on the *reason* the filtergraph is unusual — and a tripwire if a future build adds them.

        ⚠️ If `afade` ever appears, the fade should be rewritten to use it and this test should be deleted rather
        than satisfied. Asserting the absence is asserting a workaround, which is worth doing loudly.
        """
        if not HAVE_FFMPEG:
            self.skipTest("no ffmpeg")
        found = listing("-filters")
        self.assertTrue(found.strip())
        for name in ("afade", "acrossfade", "volumedetect", "astats"):
            with self.subTest(filter=name):
                self.assertNotRegex(found, rf"\b{name}\b")

    def test_the_bundled_build_is_found_from_the_repository_root(self):
        if not HAVE_FFMPEG:
            self.skipTest("no ffmpeg")
        self.assertTrue(str(audio.binary(ROOT)).startswith(str(ROOT)))

    def test_an_explicit_binary_wins(self):
        with mock.patch.dict(os.environ, {audio.FFMPEG_ENV: "/bin/sh"}):
            self.assertEqual(audio.binary(ROOT), pathlib.Path("/bin/sh"))

    def test_an_explicit_binary_that_is_not_there_is_refused(self):
        """⚠️ Refused, not ignored. Silently falling back would make a typo'd override look like it worked."""
        with mock.patch.dict(os.environ, {audio.FFMPEG_ENV: "/nope/ffmpeg"}):
            with self.assertRaises(audio.AudioError):
                audio.binary(ROOT)

    def test_no_toolchain_anywhere_is_a_message_not_a_crash(self):
        with mock.patch.dict(os.environ, {audio.FFMPEG_ENV: ""}, clear=False):
            os.environ.pop(audio.FFMPEG_ENV, None)
            with mock.patch.object(audio, "_bundled", return_value=None):
                with mock.patch.object(shutil, "which", return_value=None):
                    with self.assertRaises(audio.AudioError) as caught:
                        audio.binary(ROOT)
        self.assertIn(audio.FFMPEG_ENV, str(caught.exception))

    def test_the_shared_library_path_is_prepended_not_replaced(self):
        """⚠️ A machine may already need it for something else; clobbering it breaks an unrelated tool."""
        bundled = ROOT / "node_modules" / "@remotion" / "compositor-darwin-arm64" / "ffmpeg"
        with mock.patch.dict(os.environ, {audio._SHARED_LIB_PATH: "/already/here"}):
            env = audio.binary_env(bundled)
        self.assertTrue(env[audio._SHARED_LIB_PATH].startswith(str(bundled.parent)))
        self.assertIn("/already/here", env[audio._SHARED_LIB_PATH])

    def test_a_system_binary_needs_no_library_path_at_all(self):
        self.assertEqual(audio.binary_env(pathlib.Path("/usr/local/bin/ffmpeg")), {})

    def test_the_loader_variable_is_the_platform_s_own(self):
        """⚠️ **Both branches, from whichever platform the suite is running on**, because the consequence of getting
        this wrong is a *silent no-op*: setting `DYLD_LIBRARY_PATH` on Linux raises nothing and warns about nothing,
        and the only symptom is the bundled ffmpeg failing to start with no mention of a loader. See `loader_variable`
        and ADR 0006 — the brief renders on Linux now, so the macOS-only name was a real defect waiting for a server.
        """
        self.assertEqual(audio.loader_variable("darwin"), "DYLD_LIBRARY_PATH")
        self.assertEqual(audio.loader_variable("linux"), "LD_LIBRARY_PATH")

    def test_the_constant_is_one_of_the_two_real_names(self):
        self.assertIn(audio._SHARED_LIB_PATH, ("DYLD_LIBRARY_PATH", "LD_LIBRARY_PATH"))



class TheAsset(unittest.TestCase):
    """`find` — which file is the bed, and what happens when there is none."""

    def test_no_asset_is_a_supported_state_not_an_error(self):
        """⚠️ `None`, never a raise. The brief is silent-with-music, and "not supplied yet" is how that looks before
        the operator acts — refusing would make the pipeline unusable until an asset arrived."""
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(audio.find(pathlib.Path(tmp)))

    def test_the_lossless_master_is_preferred_over_a_lossy_one(self):
        """⚠️ First match wins, and the order is in the module — not in the directory listing, which is arbitrary.

        A lossy master means normalising its artefacts along with its music, and there is nothing to be gained.
        """
        with tempfile.TemporaryDirectory() as tmp:
            resource = pathlib.Path(tmp)
            (resource / "music.mp3").write_bytes(b"")
            (resource / "music.wav").write_bytes(b"")
            self.assertEqual(audio.find(resource).name, "music.wav")

    def test_anything_else_in_the_folder_is_ignored(self):
        """A README is not music, and `music-old.mp3` is not the bed — the name is exact, not a glob."""
        with tempfile.TemporaryDirectory() as tmp:
            resource = pathlib.Path(tmp)
            (resource / "README.md").write_text("hi")
            (resource / "music-old.mp3").write_bytes(b"")
            self.assertIsNone(audio.find(resource))

    def test_a_directory_named_like_the_bed_is_not_the_bed(self):
        with tempfile.TemporaryDirectory() as tmp:
            (pathlib.Path(tmp) / "music.wav").mkdir()
            self.assertIsNone(audio.find(pathlib.Path(tmp)))

    def test_the_derived_bed_sits_above_the_language_folders(self):
        """⚠️ 0085_11's "both editions carry the same bed" is structural: one file, above `bn/` and `en/`.

        Normalised per edition it would be a claim about two ffmpeg runs matching rather than a fact about one file.
        """
        date = pathlib.Path("/out/2026-10-12")
        prepared = audio.prepared_path(date)
        self.assertEqual(prepared, date / audio.BED_NAME)
        for lang in ("bn", "en"):
            self.assertNotIn(lang, prepared.parts)
        self.assertTrue(prepared.name.startswith("."))


class TheFiltergraph(unittest.TestCase):
    """⚠️ The graph is assembled by hand because the standard tool for this job is not in the build."""

    def test_eval_frame_is_present(self):
        """⚠️ **Load-bearing.** `volume` defaults to `eval=once`, which evaluates before any frame exists — `t` is
        undefined, the result is NaN, and ffmpeg fails with `Invalid value NaN for volume`.

        Verified by experiment against this build: the identical expression with the default eval fails to
        configure at all. The failure is loud, but the fix is not guessable from the message.
        """
        self.assertIn("eval=frame", audio.fade_expression(175.0))

    def test_the_run_length_is_a_literal_because_the_variable_does_not_exist(self):
        """⚠️ The obvious `(duration-t)` does not work: `duration` is not in the expression's variable set, and the
        error (`Undefined constant or missing '('`) points nowhere near the cause."""
        expression = audio.fade_expression(175.0)
        self.assertIn("175", expression)
        self.assertNotIn("duration", expression)

    def test_commas_are_escaped(self):
        """⚠️ An unescaped comma inside the expression is a **filter separator**: the graph parses into extra filters
        and the error names a filter nobody intended rather than the expression."""
        expression = audio.fade_expression(175.0)
        self.assertRegex(expression, r"\\,")
        self.assertEqual(expression.count(","), expression.count("\\,"))

    def test_the_level_is_the_bed_and_the_fades_are_applied_to_it(self):
        """⚠️ `loudnorm` **before** the fade, and the order is the difference between two behaviours.

        Normalising after means the fades are measured as part of the programme and the level is raised to
        compensate — so lengthening the fade-out would make the whole bed louder. The target is the level of the
        music, and the fades taper it.
        """
        graph = audio.filtergraph(175.0)
        self.assertLess(graph.index("loudnorm"), graph.index("volume=eval=frame"))

    def test_the_trim_happens_before_the_ramp(self):
        """The fade-out is anchored to the end of the **run**, so the trim must come first — and `asetpts` must
        reset the timestamps the trim leaves behind, or `t` does not start at zero and the fade-in lands nowhere.
        """
        graph = audio.filtergraph(175.0)
        self.assertLess(graph.index("atrim"), graph.index("asetpts"))
        self.assertLess(graph.index("asetpts"), graph.index("volume=eval=frame"))

    def test_the_graph_ends_in_the_output_format(self):
        graph = audio.filtergraph(175.0)
        self.assertTrue(graph.endswith("channel_layouts=stereo"))
        self.assertIn(f"sample_rates={audio.SAMPLE_RATE}", graph)

    def test_a_whole_number_run_length_is_written_without_a_decimal_point(self):
        """⚠️ `_num`, so the command log is stable: `175.0` and `175` are the same filtergraph, and only one of them
        reads like something a person wrote. A half-second slot keeps its point."""
        self.assertIn("end=175", audio.filtergraph(175.0))
        self.assertIn("end=0.5", audio.filtergraph(0.5))

    def test_an_offset_extends_the_trim_rather_than_shortening_the_bed(self):
        """⚠️ `atrim` keeps `[start, end)`, so `end=seconds` yields a bed short by exactly `OFFSET`.

        **Found by reading, not by a test** — every assertion in this class passed while `OFFSET` was 0, because
        `end - 0` is correct. The failure would only ever have appeared for an operator who raised `OFFSET` to skip
        a sting, and it would have appeared as a bed a few seconds too short. Pinned here so the two constants
        cannot drift apart again.
        """
        with mock.patch.object(audio, "OFFSET", 5.0):
            graph = audio.filtergraph(175.0)
        self.assertIn("atrim=start=5:end=180", graph)
        # The ramp is still the run's, not the master's: `t` is relative to the trimmed, reset segment.
        self.assertIn("(175-t)", graph)

    def test_the_target_is_you_tubes_own_reference_level(self):
        """⚠️ YouTube turns loud content down and never turns quiet content up, so landing on its reference is what
        makes the level shipped the level heard."""
        self.assertEqual(audio.TARGET_LUFS, -14.0)
        self.assertIn("I=-14", audio.filtergraph(175.0))
        self.assertLess(audio.TRUE_PEAK, 0.0)



@needs_ffmpeg
class TheRunLength(unittest.TestCase):
    """The number the bed is trimmed to has to be the number the renderer actually uses."""

    def test_it_comes_from_the_sum_of_rounded_frames(self):
        """⚠️ From the sum of **rounded frames**, not the sum of the scheduled slots.

        At 30 fps a 2.5 s slot is 75 frames exactly; any slot that were not would leave the bed a fraction of a
        frame off the picture, which is the drift 0085_11 asks to rule out.
        """
        from market_overview import timeline

        self.assertAlmostEqual(timeline.total_seconds([{"duration": 75}, {"duration": 30}]), 3.5)

    def test_the_real_timeline_is_what_the_bed_is_cut_to_and_it_fits_the_cap(self):
        from market_overview import timeline

        full = [{"key": key, "duration": round(sec * timeline.FPS)} for _, key, sec in timeline.TIMELINE]
        # ⚠️ 12.5, not 5.0: an empty bundle now keeps the **close** as well as the disclosure. The close quotes no
        # figure any more, so it needs nothing from the bundle and is always scheduled — disclosure 5 + close 7.5.
        self.assertAlmostEqual(render.run_seconds({}), 12.5)
        self.assertAlmostEqual(timeline.total_seconds(full), timeline.BUILD_SECONDS)
        self.assertLess(timeline.BUILD_SECONDS, timeline.CAP_SECONDS)


@needs_ffmpeg
class Prepare(unittest.TestCase):
    """The master, the run's own file, and the promise made about the file the operator supplied."""

    def setUp(self):
        self.root = pathlib.Path(_TMP.name)
        self.resource = self.root / "resource"
        self.resource.mkdir(exist_ok=True)
        # ⚠️ Built once and reused. `if not` rather than an unconditional rebuild for speed, which means **no test
        # here may write to the shared master** — a test that did would corrupt every test after it.
        master = self.resource / "music.wav"
        if not master.exists():
            make_bed(master, 20.0)
        # A date folder per test, so one test's derived bed is never another's.
        self.date = self.root / "output" / self._testMethodName

    def test_with_no_asset_supplied_there_is_no_bed_and_no_error(self):
        """⚠️ The supported state. Nothing is written either — a `None` that left a file behind would be a bed."""
        blank = self.root / "no-assets"
        blank.mkdir(exist_ok=True)
        prepared = audio.prepare(self.date, 12.0, root=ROOT, resource=blank)
        self.assertIsNone(prepared)
        self.assertFalse(audio.prepared_path(self.date).exists())

    def test_the_master_is_untouched(self):
        """⚠️ **The one promise made about the supplied file**, and the easiest to break by accident.

        The licence is the operator's, so the file is theirs: a pipeline that normalises its inputs in place
        destroys the thing it was given. Compared byte for byte, because "the same size" is not "the same file".
        """
        master = self.resource / "music.wav"
        make_bed(master, 20.0)
        before = master.read_bytes()

        prepared = audio.prepare(self.date, 12.0, root=ROOT, resource=self.resource)

        self.assertIsNotNone(prepared)
        self.assertEqual(master.read_bytes(), before)

    def test_the_derived_bed_is_not_the_master(self):
        prepared = audio.prepare(self.date, 12.0, root=ROOT, resource=self.resource)
        self.assertNotEqual(prepared[0], self.resource / "music.wav")
        self.assertEqual(prepared[0].parent, self.date)

    def test_the_trim_lands_exactly_on_the_run_not_on_the_track(self):
        """⚠️ A 20 s master trimmed to 12 s, measured. The track's length is the track's business; the brief's is the
        brief's, and the music has to end with the picture rather than at the album's mercy."""
        prepared = audio.prepare(self.date, 12.0, root=ROOT, resource=self.resource)
        measured = audio.duration(prepared[0], ffmpeg=audio.binary(ROOT))
        self.assertIsNotNone(measured)
        self.assertAlmostEqual(measured, 12.0, delta=0.05)

    def test_a_second_run_on_the_same_master_is_byte_identical(self):
        """⚠️ 0085_11: "two renders of the same date produce identical audio placement".

        Byte-identical, not merely the same duration: `loudnorm` is single-pass and `volume` is a pure function of
        `t`, so there is nothing here that could vary — and if something ever does, this is where it shows up.
        """
        prepared = audio.prepare(self.date, 12.0, root=ROOT, resource=self.resource)
        first = prepared[0].read_bytes()
        again = audio.prepare(self.date, 12.0, root=ROOT, resource=self.resource)
        self.assertEqual(again[0].read_bytes(), first)

    def test_a_master_shorter_than_the_run_is_looped_rather_than_left_silent(self):
        """⚠️ Trimming alone would leave the tail silent — the brief's music stopping a minute before its close card,
        which is precisely the "drift at the close" this ticket rules out.

        `acrossfade` is absent from the build, so the join cannot be smoothed; the loop count is bounded and
        computed rather than `-1`, and the report says it happened so the operator can supply a longer track.
        """
        resource = self.root / "short"
        resource.mkdir(exist_ok=True)
        make_bed(resource / "music.wav", 4.0)

        prepared = audio.prepare(self.date, 12.0, root=ROOT, resource=resource)

        self.assertIsNotNone(prepared)
        self.assertIn("looped", prepared[1])
        measured = audio.duration(prepared[0], ffmpeg=audio.binary(ROOT))
        self.assertAlmostEqual(measured, 12.0, delta=0.05)

    def test_a_run_with_no_length_is_refused_rather_than_divided_by(self):
        """⚠️ Its own resource folder: the shared master is reused by every other test in this class, and a 0-byte
        file written over it would fail them all with a confusing reason."""
        empty = self.root / "empty-resource"
        empty.mkdir(exist_ok=True)
        (empty / "music.wav").write_bytes(b"")
        with self.assertRaises(audio.AudioError):
            audio.prepare(self.date, 0.0, root=ROOT, resource=empty)

    def test_the_report_names_the_file_the_level_and_the_fades(self):
        """⚠️ The bed is the one asset whose correctness is inaudible in a still. The run prints what it did, so a
        wrong level is at least *stated* somewhere rather than only heard."""
        prepared = audio.prepare(self.date, 12.0, root=ROOT, resource=self.resource)
        report = prepared[1]
        self.assertIn("music.wav", report)
        self.assertIn("-14 LUFS", report)
        self.assertIn("12s", report)



@needs_ffmpeg
class TheLevel(unittest.TestCase):
    """⚠️ **Measured, not trusted.** A `volume` expression that parses and evaluates to `1` everywhere is
    indistinguishable from one that works — the same silent-failure shape as a draw at zero opacity. So the bed is
    measured segment by segment, and against a bed built without the fade.

    The master is a sine, which is flat by construction: any variation in the output is the pipeline's doing and
    nothing else.
    """

    def test_the_body_of_the_bed_sits_on_the_target(self):
        """The -14 LUFS target is about the *music*, not about the fades — so the middle is where it is measured."""
        self.assertAlmostEqual(measure_lufs(bed(), 3.0, 4.0), audio.TARGET_LUFS, delta=1.0)

    def test_the_head_is_quieter_than_the_body_which_is_the_fade_in(self):
        body = measure_lufs(bed(), 3.0, 4.0)
        head = measure_lufs(bed(), 0.0, 1.0)
        self.assertIsNotNone(head)
        self.assertLess(head, body - 5.0)

    def test_the_tail_is_quieter_than_the_body_which_is_the_fade_out(self):
        """⚠️ The tail is the one that matters: the brief ends on the close card, and the bed has to leave before
        the picture does. A cut-off bed is the most audible defect this pipeline can ship."""
        body = measure_lufs(bed(), 3.0, 4.0)
        tail = measure_lufs(bed(), BED_SECONDS - 1.0, 0.8)
        self.assertIsNotNone(tail)
        self.assertLess(tail, body - 1.0)

    def test_the_control_proves_the_fade_is_what_did_it(self):
        """⚠️ **The load-bearing test.** The same master, the same level, the same encode — and no `volume` filter.

        Without this, the two tests above are satisfied by a bed that is quiet at both ends for some *other*
        reason (a `loudnorm` that never converged, say). With it, the difference between the two files is
        attributable to exactly one thing.
        """
        control = pathlib.Path(_TMP.name) / "no-fade.wav"
        if not control.exists():
            audio.run(
                audio.binary(ROOT),
                [
                    "-i",
                    str(pathlib.Path(_TMP.name) / "resource" / "music.wav"),
                    "-af",
                    ",".join(
                        (
                            f"atrim=start=0:end={BED_SECONDS:g}",
                            "asetpts=PTS-STARTPTS",
                            f"loudnorm=I={audio.TARGET_LUFS:g}:TP={audio.TRUE_PEAK:g}:LRA={audio.LRA:g}",
                            "aformat=sample_rates=48000:channel_layouts=stereo",
                        )
                    ),
                    "-c:a",
                    "pcm_s16le",
                    "-y",
                    str(control),
                ],
            )

        faded_head = measure_lufs(bed(), 0.0, 1.0)
        control_head = measure_lufs(control, 0.0, 1.0)

        self.assertIsNotNone(control_head)
        self.assertAlmostEqual(control_head, audio.TARGET_LUFS, delta=1.0)
        self.assertLess(faded_head, control_head - 5.0)



def stream_duration(path: pathlib.Path, kind: str) -> float | None:
    """One stream's own duration, not the container's.

    ⚠️ The distinction is the whole check: a container reports its longest stream, so a bed a second short of the
    picture is invisible in the container's figure and obvious in the audio stream's.
    """
    ffmpeg = audio.binary(ROOT)
    completed = subprocess.run(
        [
            str(audio.probe_binary(ffmpeg)),
            "-hide_banner",
            "-loglevel",
            "error",
            "-select_streams",
            kind,
            "-show_entries",
            "stream=duration",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
        env={**os.environ, **audio.binary_env(ffmpeg)},
    )
    value = completed.stdout.strip().splitlines()
    if not value or value[0] in ("", "N/A"):
        return None
    return float(value[0])


def streams(path: pathlib.Path) -> str:
    ffmpeg = audio.binary(ROOT)
    completed = subprocess.run(
        [
            str(audio.probe_binary(ffmpeg)),
            "-hide_banner",
            "-loglevel",
            "error",
            "-show_entries",
            "stream=codec_type,codec_name",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
        env={**os.environ, **audio.binary_env(ffmpeg)},
    )
    return completed.stdout


@needs_ffmpeg
class Mux(unittest.TestCase):
    """⚠️ The mux is where 0085_11 is actually delivered, and where the picture could be quietly ruined."""

    @classmethod
    def setUpClass(cls):
        cls.root = pathlib.Path(_TMP.name)
        # A synthetic picture — `nullsrc` is in the allow-list, `color` is not. Cheap, hermetic, and the same
        # duration as the bed, so "covers the runtime" means something.
        cls.picture = cls.root / "picture.mp4"
        if not cls.picture.exists():
            audio.run(
                audio.binary(ROOT),
                [
                    "-f",
                    "lavfi",
                    "-i",
                    f"nullsrc=s=320x180:d={BED_SECONDS:g}",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-y",
                    str(cls.picture),
                ],
            )
        cls.muxed = cls.root / "muxed.mp4"
        if not cls.muxed.exists():
            audio.mux(cls.picture, bed(), cls.muxed, root=ROOT)

    def test_the_result_carries_both_a_picture_and_a_bed(self):
        found = streams(self.muxed)
        self.assertIn("video", found)
        self.assertIn("audio", found)
        self.assertIn("aac", found)

    def test_the_picture_was_copied_not_re_encoded(self):
        """⚠️ `-c:v copy`, checked by extracting the stream and comparing bytes.

        The rendered frames are the expensive artefact, and an audio mux has no business touching them — a
        re-encode here would silently degrade every frame of the day's brief for a container change.
        """
        original = self.root / "v-original.mp4"
        remuxed = self.root / "v-remuxed.mp4"
        for source, target in ((self.picture, original), (self.muxed, remuxed)):
            audio.run(
                audio.binary(ROOT),
                ["-i", str(source), "-map", "0:v", "-c", "copy", "-y", str(target)],
            )
        self.assertEqual(original.read_bytes(), remuxed.read_bytes())

    def test_the_bed_is_still_going_at_the_close(self):
        """⚠️ 0085_11's third Done-When, measured: "audio present for the full runtime, no drift at the close".

        The audio stream is compared to the picture's, not the container's — `-shortest` would happily absorb a bed
        that ran out early, and the container's duration would show the longer of the two either way.
        """
        audio_seconds = stream_duration(self.muxed, "a:0")
        video_seconds = stream_duration(self.muxed, "v:0")
        self.assertIsNotNone(audio_seconds)
        self.assertIsNotNone(video_seconds)
        self.assertAlmostEqual(audio_seconds, video_seconds, delta=0.05)

    def test_muxing_in_place_leaves_no_staging_file_behind(self):
        """⚠️ The `.muxing` sibling is written inside the package folder, so a crash that left one would put an
        unexplained file where a human looks for the day's deliverable."""
        target = self.root / "in-place.mp4"
        shutil.copy(self.picture, target)
        audio.mux(target, bed(), root=ROOT)
        leftovers = [p.name for p in target.parent.glob("*.muxing")]
        self.assertEqual(leftovers, [])
        self.assertIn("audio", streams(target))



class _StubProcess:
    """The slice of `subprocess.Popen` that `render._stream` touches, and nothing more.

    ⚠️ `_stream` **streams** a render rather than capturing it, so the seam tests stub `Popen`, not `run`. The fake
    must therefore be iterable (its `stdout` is read line by line), closeable, and waitable.
    """

    def __init__(self, returncode: int):
        self.stdout = io.StringIO("")
        self.returncode = returncode

    def wait(self, timeout: float | None = None) -> int:
        return self.returncode

    def kill(self) -> None:  # pragma: no cover - the timeout path is covered in tests/test_render.py
        pass


class TheRenderWiring(unittest.TestCase):
    """How the bed reaches the video, asserted on the commands actually issued.

    ⚠️ This is not a rendering test — the render is stubbed. It is a test of the **seam**: which file Remotion writes,
    which file the package is allowed to contain, and what survives a render that dies. That seam is where 0085_11
    is delivered, and no amount of audio unit-testing above it would notice it being wrong.
    """

    def setUp(self):
        self.root = pathlib.Path(_TMP.name) / "wiring"
        self.store_dir = self.root / "store" / "2026-10-12"
        self.store_dir.mkdir(parents=True, exist_ok=True)
        (self.store_dir / "facts.json").write_text(json.dumps({"indexes": []}), encoding="utf-8")
        self.target = (
            self.root / "output" / "brief" / "2026-10-12" / "bn" / "market-brief-2026-10-12-bn.mp4"
        )
        self.target.parent.mkdir(parents=True, exist_ok=True)
        # A delivery that already exists, so "did this run destroy it?" is answerable.
        self.target.write_bytes(b"a previous, good delivery")
        self.commands: list[list[str]] = []

    def _run(self, *, bed=None, returncode=0, writes=True):
        """`render.render` with the renderer stubbed, records the command, and returns nothing."""

        def fake_popen(command, **_kwargs):
            self.commands.append(command)
            if writes and returncode == 0:
                pathlib.Path(command[5]).write_bytes(b"freshly rendered picture")
            return _StubProcess(returncode)

        with contextlib.ExitStack() as stack:
            # ⚠️ **Two seams, and they are no longer the same one.** `store.root` still redirects the snapshot (the
            # repo's committed evidence), while the day's output and the operator's assets now resolve through the
            # shared data root — so patching only `store.root` would leave this test writing into the *real*
            # `output/brief/` folder. The seam split when the data root moved out of the repository; a test that
            # kept the old single patch would still pass while doing exactly that.
            stack.enter_context(mock.patch.object(store, "root", return_value=self.root))
            stack.enter_context(mock.patch.object(paths, "data_root", return_value=self.root))
            stack.enter_context(mock.patch.object(logo, "load", return_value=None))
            stack.enter_context(mock.patch.object(render.subprocess, "Popen", side_effect=fake_popen))
            self.mux = stack.enter_context(mock.patch.object(audio, "mux"))
            render.render("2026-10-12", "bn", bed=bed)
        return self.commands[0]

    def test_remotion_never_writes_the_package_file(self):
        """⚠️ **The rule the whole seam exists for.** The package file is written once, at the end, from a complete
        artefact — so a render that dies cannot leave a partial file where a finished one belongs."""
        command = self._run()
        self.assertNotIn(str(self.target), command)
        self.assertIn(str(self.target.with_name(".silent-bn.mp4")), command)

    def test_the_staging_file_is_cleaned_up_whether_it_worked_or_not(self):
        self._run()
        self.assertEqual(list(self.target.parent.glob(".silent-*")), [])

    def test_a_finished_render_lands_in_the_package(self):
        self._run()
        self.assertEqual(self.target.read_bytes(), b"freshly rendered picture")

    def test_a_failed_render_does_not_take_the_previous_delivery_with_it(self):
        """⚠️ **The bug this seam was made unconditional for, found by losing the file.**

        Remotion's `--overwrite` **unlinks the output path before it renders**. Rendering straight to the package
        file therefore means a render that dies — or is killed, which is how it was found — leaves the package
        *empty*, destroying a delivery that was already good. It is not recoverable by retrying: the previous
        artefact is simply gone.

        With staging, the previous delivery is untouched by a failed run. That is what turns "a run either produces
        a complete pair, or produces nothing" from a hope into a property.
        """
        with self.assertRaises(render.RenderError):
            self._run(returncode=1)
        self.assertEqual(self.target.read_bytes(), b"a previous, good delivery")
        self.assertEqual(list(self.target.parent.glob(".silent-*")), [])

    def test_a_render_that_reports_success_but_writes_nothing_is_refused(self):
        """⚠️ And the previous delivery still survives it: the check happens before the target is touched."""
        with self.assertRaises(render.RenderError):
            self._run(writes=False)
        self.assertEqual(self.target.read_bytes(), b"a previous, good delivery")

    def test_a_bed_is_muxed_from_the_staging_file_into_the_package(self):
        """⚠️ The mux's *input* is the staging file and its *output* is the target — so the package file is only
        ever produced by the mux, and the silent render never appears there even for an instant."""
        bed = self.root / "out" / ".bed.wav"
        self._run(bed=bed)
        self.assertEqual(self.mux.call_count, 1)
        args, kwargs = self.mux.call_args
        self.assertEqual(args[0], self.target.with_name(".silent-bn.mp4"))
        self.assertEqual(args[1], bed)
        self.assertEqual(args[2], self.target)

    def test_no_bed_supplied_means_the_render_is_moved_into_place_unchanged(self):
        """⚠️ The supported state, and the same bytes: no mux, no re-encode, no second pass."""
        self._run(bed=None)
        self.assertEqual(self.mux.call_count, 0)
        self.assertEqual(self.target.read_bytes(), b"freshly rendered picture")

