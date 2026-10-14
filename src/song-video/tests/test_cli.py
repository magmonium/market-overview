"""0087_01, 0087_04 — the conductor: what `sv build` refuses, what it records, and what it replays.

⚠️ **The refusal is built first, on purpose.** A run with no song has nothing to make, and the honest outcome is a
reason and a non-zero exit — never a silent film.

⚠️ **Every test here fails if the run asks a question the flags or the record should have answered.** The `input`
seam raises unless a test supplies answers, so "a recorded song asks nothing" is *asserted* rather than assumed —
and that is the entire point of recording the menu.
"""
import contextlib
import io
import pathlib
import tempfile
import unittest
from unittest import mock

from song_video import master, package, paths, plan, record, render
from song_video.cli import main

from support import write_wav

SONG = "dure-kothay"
TITLE = "দূরে কোথায় (Dure Kothay)"


def _no_questions(*_args: object) -> str:
    """The `input` seam: a question nobody was supposed to be asked is a failed test, not a hang."""
    raise AssertionError("the run asked a question — the flags or the record should have answered it")


class Reel(unittest.TestCase):
    """A temporary project root, with one song in it."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name)
        #: ⚠️ The songs live under the shared data root's reel namespace — `resource/reel/song/` — and every
        #: fixture writes there. One spelling of the folder in this file, so the next test cannot quietly
        #: re-invent the old in-project path.
        self.songs = self.root / "resource" / "reel" / "song"
        self.songs.mkdir(parents=True)
        self.master = write_wav(self.songs / f"{SONG}.wav", seconds=1.5)

        # ⚠️ **Three seams, deliberately.** The reel's *data* (the songs and the packages) is temporary, through
        # `data_root`; its recorded run and its render staging stay in a temporary `project_root`; and the brief's
        # toolchain is **not** temporary — `repo_root()` is where `node_modules` lives, and a fixture cannot invent
        # an ffprobe.
        toolchain = paths.repo_root()
        for name, value in (
            ("data_root", self.root),
            ("project_root", self.root),
            ("repo_root", toolchain),
        ):
            patcher = mock.patch.object(paths, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

        # ⚠️ **No test in this file may reach Remotion**, so the fakes are installed for *every* test rather than
        # for the ones that need them: a test added later cannot quietly start rendering an hour of frames. They
        # are also what makes the *order* visible — which is the whole content of the quality gate.
        self.rendered: list[str] = []
        self.stages: list[render.Stage] = []
        self.fail_on: str | None = None
        for name, stand_in in (("thumbnail", self._still), ("video", self._reel)):
            patcher = mock.patch.object(render, name, stand_in)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _still(self, place: render.Stage, job: plan.Job) -> pathlib.Path:
        return self._render(place, job, "thumbnail", package.thumbnail, b"jpeg")

    def _reel(self, place: render.Stage, job: plan.Job) -> pathlib.Path:
        return self._render(place, job, "reel", package.reel, b"mp4")

    def _render(self, place: render.Stage, job: plan.Job, kind: str, where, body: bytes) -> pathlib.Path:
        """What Remotion would do, as far as the conductor can see — and it fails where a test says it should."""
        self.stages.append(place)
        if self.fail_on == job.theme:
            raise render.RenderError(f"remotion {kind} ({job.theme}) failed (1):\nTarget closed")
        path = where(place.output_dir, job)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        self.rendered.append(f"{kind}:{job.theme}")
        return path

    def placed(self, theme: str) -> pathlib.Path:
        """Where a theme's package would be."""
        return paths.output_dir() / SONG / theme

    def build(self, *argv: str, answered: list[str] | None = None, terminal: bool = False):
        """Run `sv build`, capturing both streams — and refusing to let it ask unless a test says it may."""
        out, err = io.StringIO(), io.StringIO()
        with (
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
            mock.patch("sys.stdin", mock.Mock(isatty=lambda: terminal)),
            mock.patch("builtins.input", side_effect=answered if answered is not None else _no_questions),
        ):
            code = main(["build", *argv])
        return code, out.getvalue(), err.getvalue()

    def answered_by_flags(self, *extra: str):
        """The same run the menu would collect, answered by flags instead."""
        return self.build("--song", SONG, "--title", TITLE, "--theme", "vinyl", "--wave", "ribbon", *extra)

    def recorded(self) -> record.Run:
        return record.load(paths.store_dir(), SONG)

    def record_text(self) -> str:
        return (paths.store_dir() / SONG / record.RUN).read_text(encoding="utf-8")


class AnsweringTheRun(Reel):
    def test_the_flags_answer_the_whole_menu_and_the_answers_are_recorded(self):
        code, out, err = self.answered_by_flags("--theme", "neon")

        run = self.recorded()
        self.assertEqual(run.song, SONG, "the id is the folder name, not the title")
        self.assertEqual(run.title, TITLE)
        # ⚠️ Never asked for: the caption follows the script the operator typed, and this title is Bengali.
        self.assertEqual(run.lang, "bn")
        self.assertEqual(run.themes, ("vinyl", "neon"), "the order the themes were given is the build order")
        self.assertEqual(run.wave, "ribbon")
        self.assertEqual(run.fps, 30)
        self.assertAlmostEqual(run.duration_seconds, 1.5, places=3)
        self.assertEqual(run.master.name, f"{SONG}.wav")
        self.assertEqual(run.master.bytes, self.master.stat().st_size)
        self.assertEqual(run.master.sha256, master.digest(self.master), "the guard's own digest")
        self.assertTrue(pathlib.Path(run.toolchain.ffprobe).is_file(), "the toolchain is recorded")

        # The ledger, printed before anything expensive: the facts, and the files that will appear.
        self.assertIn(TITLE, out)
        self.assertIn("caption  bn", out, "the language and the number, never the word")
        self.assertIn("45 frames", out, "1.5 s at 30 fps is 45 frames")
        self.assertIn("song-reel-dure-kothay-vinyl.mp4", out)
        self.assertIn("song-reel-dure-kothay-neon.mp4", out)

        # ⚠️ And it is now a *build*, not an admission: exit zero, both packages whole, and the summary printed.
        self.assertEqual(code, 0)
        self.assertTrue((self.placed("vinyl") / "song-reel-dure-kothay-vinyl.mp4").exists())
        self.assertEqual(
            self.rendered,
            ["thumbnail:vinyl", "thumbnail:neon", "reel:vinyl", "reel:neon"],
            "every still first, then every reel — and both in the recorded order",
        )
        self.assertIn("8 files", out, "the ledger of what was made, printed once it is whole")
        self.assertEqual(err, "", "a run that worked says nothing on stderr")

    def test_a_second_run_replays_the_record_and_asks_nothing(self):
        self.answered_by_flags()
        recorded = self.record_text()
        self.rendered.clear()  # ⚠️ the replay is the run under test, not the one that recorded the answers

        # ⚠️ No flags and no terminal, and `input` may not fire: a recorded song **replays**.
        code, out, _err = self.build()

        self.assertEqual(code, 0)
        self.assertIn("replayed from", out)
        self.assertIn(TITLE, out, "the ledger shows the recorded answers")
        self.assertEqual(self.record_text(), recorded, "a replay never rewrites the record")
        self.assertEqual(self.rendered, ["thumbnail:vinyl", "reel:vinyl"], "and it renders the same plan again")

    def test_the_menu_asks_only_what_the_flags_would_have_answered(self):
        # Title, then the themes (1,2), then the wave form (2) — and nothing about the song, because there is one.
        code, out, err = self.build(answered=[TITLE, "1,2", "2"], terminal=True)

        run = self.recorded()
        self.assertEqual(run.title, TITLE)
        self.assertEqual(run.themes, ("vinyl", "neon"), "ticked 1,2 → the catalogue's order, not the typing's")
        self.assertEqual(run.wave, "ribbon", "the second form in the catalogue")

        self.assertIn(TITLE, out, "stdout stays the ledger")
        self.assertIn("Vinyl", err, "the menu itself is on stderr, with the answers it offered")
        self.assertEqual(code, 0)


    def test_the_captions_language_can_be_set_when_the_title_cannot_say(self):
        """⚠️ An instrumental, or a Latin transliteration of a Bengali song: the title cannot choose a script, so
        the operator does — and the answer is **recorded**, because a rebuild must not re-decide it."""
        self.build(
            "--song", SONG, "--title", "Dure Kothay", "--theme", "vinyl", "--wave", "ribbon", "--lang", "en",
        )

        self.assertEqual(self.recorded().lang, "en")
        self.assertEqual(self.stages[0].lang, "en", "and it reaches the render, which owns the word")

    def test_an_unknown_caption_language_is_refused_with_the_ones_that_exist(self):
        code, _out, err = self.answered_by_flags("--lang", "fr")

        self.assertNotEqual(code, 0)
        self.assertIn('unknown language "fr"', err)
        self.assertIn("bn, en", err)
        self.assertFalse((paths.store_dir() / SONG / record.RUN).exists(), "a refusal records nothing")


class TheQualityGate(Reel):
    """⚠️ The map's own ordering, which is what makes a bad theme cost seconds instead of an hour (issue 08)."""

    def test_every_thumbnail_is_rendered_before_any_video(self):
        self.build(
            "--song", SONG, "--title", TITLE, "--theme", "vinyl", "--theme", "neon", "--theme", "parchment",
            "--wave", "ribbon",
        )

        self.assertEqual(self.rendered[:3], ["thumbnail:vinyl", "thumbnail:neon", "thumbnail:parchment"])
        self.assertEqual(self.rendered[3:], ["reel:vinyl", "reel:neon", "reel:parchment"])

    def test_the_master_is_staged_byte_for_byte_in_the_one_folder_a_composition_can_fetch_from(self):
        self.answered_by_flags()

        staged = self.root / "public" / f"{SONG}.wav"
        self.assertTrue(staged.exists(), "the renderer fetches from public/, so the song has to be there")
        self.assertEqual(master.digest(staged), master.digest(self.master), "the master, not a re-encode of it")
        self.assertEqual([place.staged for place in self.stages], [f"{SONG}.wav"] * 2, "same stage, both renders")

    def test_the_render_is_given_the_operators_own_mark_and_the_cover_when_there_is_one(self):
        # ⚠️ **The mark is supplied by the fixture now, and that is a fix rather than a convenience.** It used to be
        # read from the repository's own `resource/`, so this assertion passed only on a machine where the operator
        # had happened to drop a logo in — the shape of test that fails for the wrong reason elsewhere. The mark
        # lives outside the repository now, so the fixture stands in for it, exactly as the cover below does.
        brief = self.root / "resource" / "brief"
        brief.mkdir(parents=True, exist_ok=True)
        (brief / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)

        # ⚠️ A stand-in cover rather than a real image: nothing on the Python side may decode it — the renderer
        # does that, and the renderer is what is faked here.
        (self.root / "resource" / "reel" / "song" / f"{SONG}.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)

        code, out, _err = self.answered_by_flags()

        place = self.stages[0]
        self.assertEqual(code, 0)
        self.assertEqual(place.cover, f"{SONG}.png", "the cover travels with the reel")
        self.assertTrue((self.root / "public" / f"{SONG}.png").exists(), "staged, like the master")
        self.assertIn(f"cover    {SONG}.png", out, "and the ledger names what the still will draw")
        self.assertNotIn("pairs with no master", out, "nothing reported that did pair")
        # ⚠️ The seed comes from the **record**, not from the file on disk: a rebuild re-cuts the approved run, and the
        # look has to be a function of what was approved rather than of whatever is in the folder today.
        self.assertEqual(place.seed, self.recorded().master.sha256, "the recorded digest seeds the look")
        self.assertIsNotNone(place.mark, "the brief's own mark, loaded from the shared resource/brief/")
        self.assertTrue(place.mark["chip"].startswith("#"), "with the chip its own polarity decided")

    def test_the_one_loose_image_is_used_rather_than_reported(self):
        """⚠️ The operator's rule, in their words: *use the image*. That file — artwork for another song, under a name
        no master answers to — used to be reported and ignored, so the still drew the theme's motif over it. It is
        taken now, because **one candidate is not a choice** (exactly as one song needs no menu), and it is named in
        the ledger, so the choice is visible rather than silent."""
        (self.songs / "man-poreche-preme.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)

        code, out, _err = self.answered_by_flags()

        self.assertEqual(code, 0, "one loose image is not an ambiguity")
        self.assertEqual(self.stages[0].cover, "man-poreche-preme.png", "it rides the reel")
        self.assertIn("cover    man-poreche-preme.png", out)
        self.assertNotIn("pairs with no master", out, "and it is no longer an image nobody answered to")

    def test_several_loose_images_are_a_question_and_the_answer_is_recorded(self):
        """⚠️ A folder of posters is a **choice**, so the run asks. `none` is one of the answers, because the theme's
        motif is a designed state (issue 08) rather than a hole — and the answer is recorded, so a rebuild replays the
        same artwork without asking again."""
        for name in ("a.png", "b.png", "c.png"):
            (self.songs / name).write_bytes(b"\x89PNG\r\n\x1a\n")

        code, out, err = self.build(
            "--song", SONG, "--title", TITLE, "--theme", "vinyl", "--wave", "ribbon",
            answered=["3"], terminal=True,
        )

        self.assertEqual(code, 0)
        self.assertIn("cover — pick one (1-4)", err, "asked on stderr, like every other question")
        self.assertEqual(self.stages[0].cover, "c.png", "the answer is the image the frame is built around")
        self.assertIn("cover    c.png", out)
        self.assertIn("a.png pairs with no master", out, "the ones it did not use are still named")
        self.assertEqual(self.recorded().cover.name, "c.png", "and the choice is what a rebuild replays")

    def test_the_flag_can_choose_the_other_image_in_the_folder(self):
        """⚠️ The folder's pairing is a *default*, not a cage: `--cover` names any image in the folder, and what it
        names is what the still draws."""
        (self.songs / f"{SONG}.jpg").write_bytes(b"\x89PNG\r\n\x1a\n")
        (self.songs / "poster.png").write_bytes(b"\x89PNG\r\n\x1a\n")

        code, out, _err = self.answered_by_flags("--cover", "poster.png")

        self.assertEqual(code, 0)
        self.assertEqual(self.stages[0].cover, "poster.png", "the flag wins over the basename rule")
        self.assertIn("cover    poster.png", out)

    def test_an_image_for_another_song_is_attached_by_name_and_recorded_with_a_digest(self):
        """⚠️ The complaint this answers: artwork for a *different* song sitting in the folder, a still that drew the
        theme's motif over it, and nothing to type. The pairing rule does not change — the image still answers to no
        master — so the operator attaches it deliberately with `--cover`, and that is recorded like every answer."""
        art = self.songs / "man-poreche-preme.png"
        art.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)

        code, out, _err = self.answered_by_flags("--cover", "man-poreche-preme.png")

        place = self.stages[0]
        self.assertEqual(code, 0)
        self.assertEqual(place.cover, "man-poreche-preme.png", "the attached image is what the still draws")
        self.assertTrue((self.root / "public" / "man-poreche-preme.png").exists(), "staged, like the master")
        self.assertIn("cover    man-poreche-preme.png", out)
        self.assertNotIn("pairs with no master", out, "attached, so it is no longer an image nobody answered to")

        run = self.recorded()
        self.assertEqual(run.cover.name, "man-poreche-preme.png")
        self.assertEqual(run.cover.bytes, art.stat().st_size)
        self.assertEqual(run.cover.sha256, master.digest(art), "the artwork is pinned exactly as the master is")
        self.assertEqual(run.master.sha256, master.digest(self.master), "and the master's own guard is untouched")

    def test_a_recorded_cover_replays_and_a_swapped_image_under_the_same_name_is_refused(self):
        """⚠️ The other half of the digest. A record says which image went into the still; a *different* image at the
        same filename would be drawn under an approval given for the old art — and nothing but the digest can see
        it, because the filename is the one thing a person checks."""
        art = self.songs / "man-poreche-preme.png"
        art.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
        self.answered_by_flags("--cover", "man-poreche-preme.png")
        self.stages.clear()

        code, out, _err = self.build("--song", SONG, "--replay")

        self.assertEqual(code, 0)
        self.assertIn("replayed from", out)
        self.assertEqual(self.stages[0].cover, "man-poreche-preme.png", "the same artwork, asked for once")

        self.stages.clear()
        art.write_bytes(b"\x89PNG\r\n\x1a\n" + b"1" * 64)  # the same filename, different art

        code, _out, err = self.build("--song", SONG, "--replay")

        self.assertNotEqual(code, 0)
        self.assertIn("man-poreche-preme.png", err, "the refusal names the image")
        self.assertIn("record describes", err, "…and says what the record holds instead")
        self.assertIn("approved", err, "…and why it stops rather than re-cutting")
        self.assertEqual(self.stages, [], "and nothing was rendered from it")

    def test_every_package_gets_the_upload_text_beside_its_reel(self):
        """⚠️ **The package's own contract** (issue 07): "hand this folder to its own uploader". An uploader asks for a
        title and a description as much as for the video and the still, so both are written into the folder — and the
        title is a *literal* here, because a file whose content nobody can read is a file nobody can review."""
        code, _out, _err = self.answered_by_flags()

        folder = self.placed("vinyl")
        self.assertEqual(code, 0)
        self.assertEqual(
            (folder / f"title-{SONG}-vinyl.txt").read_text(encoding="utf-8").strip(),
            "দূরে কোথায় (Dure Kothay) | ০:০২ | বাংলা গান",
        )
        page = (folder / f"description-{SONG}-vinyl.txt").read_text(encoding="utf-8")
        self.assertIn("০ মিনিট ২ সেকেন্ড", page, "the length, twice: as a clock face and spelled out")
        self.assertIn("#বাংলাগান", page)

    def test_the_ledger_shows_the_title_a_search_result_will_show(self):
        """⚠️ The one line of the ledger that is *published*, and it is a different string from the title above it."""
        _code, out, _err = self.answered_by_flags()

        self.assertIn("upload   দূরে কোথায় (Dure Kothay) | ০:০২ | বাংলা গান", out)
        self.assertIn("title    দূরে কোথায় (Dure Kothay)", out, "…and the internal title is still printed too")

    def test_the_artist_flag_reaches_the_description_and_the_record(self):
        code, _out, _err = self.answered_by_flags("--artist", "অজয় চক্রবর্তী")

        page = (self.placed("vinyl") / f"description-{SONG}-vinyl.txt").read_text(encoding="utf-8")
        self.assertEqual(code, 0)
        self.assertIn("শিল্পী: অজয় চক্রবর্তী", page)
        self.assertEqual(self.recorded().artist, "অজয় চক্রবর্তী", "published words are recorded answers")

    def test_a_failed_theme_fails_the_run_and_stops_before_the_videos(self):
        self.fail_on = "neon"

        code, out, err = self.build(
            "--song", SONG, "--title", TITLE, "--theme", "vinyl", "--theme", "neon", "--wave", "ribbon",
        )

        self.assertNotEqual(code, 0, "a failed theme must not report success")
        self.assertIn("neon", err, "the failure names the theme it was rendering")
        # ⚠️ The gate working as designed: a theme that cannot even produce a still never reaches a video.
        self.assertEqual(self.rendered, ["thumbnail:vinyl"])
        self.assertNotIn("4 files", out, "no summary of a run that did not finish")
        self.assertFalse((self.placed("neon") / "song-reel-dure-kothay-neon.mp4").exists())


class Refusals(Reel):
    def test_an_empty_song_folder_refuses_and_renders_nothing(self):
        self.master.unlink()

        code, _out, err = self.build()

        self.assertNotEqual(code, 0, "a run with no song must not report success")
        self.assertIn("no songs", err, "the refusal must say why, on stderr")
        # ⚠️ And it must have made nothing at all — no video, no still, no folder that reads as a delivery.
        self.assertEqual(list(self.root.rglob("*.mp4")), [])
        self.assertEqual(list(self.root.rglob("*.jpg")), [])

    def test_no_terminal_and_no_flags_is_one_refusal_naming_every_flag(self):
        """⚠️ Once, and up front — not at the third question, after the operator has typed the first two."""
        code, _out, err = self.build()

        self.assertNotEqual(code, 0)
        for flag in ("--title", "--theme", "--wave"):
            self.assertIn(flag, err, "the refusal lists what would have answered it")
        self.assertFalse((paths.store_dir() / SONG / record.RUN).exists())

    def test_an_unknown_theme_is_refused_in_the_renderers_own_words(self):
        code, _out, err = self.answered_by_flags("--theme", "sparkle")

        self.assertNotEqual(code, 0)
        self.assertIn('unknown theme "sparkle"', err)
        self.assertIn("vinyl, neon, parchment, aurora", err, "the refusal names the catalogue")
        self.assertFalse((paths.store_dir() / SONG / record.RUN).exists(), "a refusal records nothing")

    def test_an_unknown_wave_form_is_refused_with_the_forms_that_exist(self):
        code, _out, err = self.answered_by_flags("--wave", "zigzag")

        self.assertNotEqual(code, 0)
        self.assertIn('unknown wave form "zigzag"', err)
        self.assertIn("bars, ribbon, ring, bloom", err)

    def test_a_cover_that_is_not_in_the_folder_is_refused_with_the_images_that_are(self):
        """⚠️ A refusal whose job is to end in something the operator can type: the images that *are* there."""
        (self.songs / "man-poreche-preme.png").write_bytes(b"\x89PNG\r\n\x1a\n")

        code, _out, err = self.answered_by_flags("--cover", "poster.jpg")

        self.assertNotEqual(code, 0)
        self.assertIn('no image "poster.jpg"', err)
        self.assertIn("man-poreche-preme.png", err, "and it names the images that could have been named")
        self.assertFalse((paths.store_dir() / SONG / record.RUN).exists(), "a refusal records nothing")

    def test_a_cover_given_as_a_path_is_refused_rather_than_looked_up(self):
        """⚠️ A record holds a **name inside `resource/reel/song/`** — it is committed and read on other machines, and an
        absolute path to somebody's desktop is not a rebuild. So a path is refused here, not quietly accepted."""
        code, _out, err = self.answered_by_flags("--cover", "resource/reel/song/poster.jpg")

        self.assertNotEqual(code, 0)
        self.assertIn("not a path", err)

    def test_a_title_that_will_not_fit_a_search_result_is_refused_before_anything_is_built(self):
        """⚠️ **A copy defect costs seconds, not an hour of frames** — and it leaves the store exactly as it was, which
        is what makes answering again free rather than a cleanup."""
        code, _out, err = self.build(
            "--song", SONG, "--title", "গ" * 120, "--theme", "vinyl", "--wave", "ribbon"
        )

        self.assertNotEqual(code, 0)
        self.assertIn("over the 100", err)
        self.assertEqual(self.rendered, [], "nothing was rendered")
        self.assertEqual(list((self.root / "output" / "reel").rglob("title-*.txt")), [], "and no package was started")
        self.assertFalse((paths.store_dir() / SONG / record.RUN).exists(), "a refusal records nothing")

    def test_several_loose_images_with_no_terminal_refuses_rather_than_picking_one(self):
        """⚠️ A choice with nobody to ask is a refusal that names the flag — never a coin toss. The same discipline as
        an ambiguous folder of songs, and the reason the refusal lists the images rather than only complaining."""
        for name in ("a.png", "b.png", "c.png"):
            (self.songs / name).write_bytes(b"\x89PNG\r\n\x1a\n")

        code, _out, err = self.answered_by_flags()

        self.assertNotEqual(code, 0, "an ambiguous folder of images must not be guessed at")
        self.assertIn("pair with no master", err)
        self.assertIn("--cover", err, "and the refusal names the flag that answers it")
        self.assertFalse((paths.store_dir() / SONG / record.RUN).exists(), "a refusal records nothing")

    def test_a_flag_that_disagrees_with_the_record_is_refused_and_the_record_stands(self):
        self.answered_by_flags()
        recorded = self.record_text()

        code, _out, err = self.build("--theme", "neon")

        self.assertNotEqual(code, 0)
        self.assertIn("vinyl", err, "the refusal says what the record says")
        self.assertIn("run.json", err, "…and names the file to remove to answer again")
        self.assertEqual(self.record_text(), recorded, "a refusal never rewrites the record")

    def test_a_swapped_master_is_refused_before_anything_is_built(self):
        self.answered_by_flags()
        reel = self.placed("vinyl") / "song-reel-dure-kothay-vinyl.mp4"
        built = reel.read_bytes()
        write_wav(self.master, seconds=2.0)  # a different take, under the same name

        code, _out, err = self.build("--replay")

        self.assertNotEqual(code, 0)
        self.assertIn("changed since", err)
        self.assertEqual(self.rendered, ["thumbnail:vinyl", "reel:vinyl"], "the refusal rendered nothing new")
        # ⚠️ Stronger than \"no video was made\": the guard refused *and* the reel it refused to re-cut is still
        # exactly the file it was, because nothing is overwritten in place.
        self.assertEqual(reel.read_bytes(), built, "and last run's reel is untouched")

    def test_replay_without_a_record_says_so_rather_than_asking(self):
        # A terminal is available, and it still must not ask: `--replay` means the record, not the menu.
        code, _out, err = self.build("--replay", terminal=True)

        self.assertNotEqual(code, 0)
        self.assertIn("has no record", err)

    def test_two_songs_and_no_song_flag_names_the_songs(self):
        write_wav(self.songs / "other.wav", seconds=1.0)

        code, _out, err = self.build("--title", TITLE, "--theme", "vinyl", "--wave", "ribbon")

        self.assertNotEqual(code, 0)
        self.assertIn("dure-kothay", err, "an ambiguous folder names what it found")
        self.assertIn("other", err)


if __name__ == "__main__":
    unittest.main()


