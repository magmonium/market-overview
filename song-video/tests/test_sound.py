"""0087_09, 0087_10 — sound: what the delivery measures, and what it must not lose.

⚠️ **The second half is the important one.** A master is whatever the operator supplied, and this module has no
business improving it (issue 09): the level, the dynamics and the length are the artist's. What it *does* own is the
**loss** — so the assertions that matter are that a lossy master is named as a ceiling, that a clipped master is named
as a risk, and that a delivery which drops a channel, a rate or the music itself **fails** rather than shipping.
"""
import pathlib
import tempfile
import unittest

from song_video import sound

from support import write_wav


class Measurement(unittest.TestCase):
    """The pass that touches a real file, against a real toolchain."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.where = pathlib.Path(self._tmp.name)

    def test_a_wav_is_measured_as_what_it_is(self):
        """⚠️ Silence is a legitimate fixture: the *shape* is what this asserts, and loudness on silence is `-inf` —
        which must arrive as *unknown* rather than as a number that would then be printed at an operator."""
        path = write_wav(self.where / "dure-kothay.wav", seconds=1.0, rate=44100)

        measured = sound.measure(path)

        self.assertIsNotNone(measured, "the brief's toolchain is in the suite — test_guard proves it")
        self.assertEqual(measured.codec, "pcm_s16le")
        self.assertEqual(measured.sample_rate, 44100)
        self.assertEqual(measured.channels, 1)
        self.assertTrue(measured.lossless, "a WAV has thrown nothing away")

    def test_a_file_with_no_audio_at_all_is_not_measured_rather_than_guessed(self):
        nothing = self.where / "notes.txt"
        nothing.write_text("not audio", encoding="utf-8")

        self.assertIsNone(sound.measure(nothing))


class TheCeiling(unittest.TestCase):
    """What the master *is*, said out loud — the facts nobody can see by looking."""

    def test_a_lossy_master_is_named_as_the_ceiling_it_is(self):
        whispered = sound.Audio(codec="mp3", sample_rate=48000, channels=2, bitrate=171960)

        complaints = whispered.complaints()

        self.assertEqual(len(complaints), 1)
        self.assertIn("lossy", complaints[0])
        self.assertIn("172 kbps", complaints[0], "the number is the point")
        self.assertIn("lossless", complaints[0], "…and so is the one change that raises it")

    def test_a_master_at_the_ceiling_is_a_clipping_risk_and_says_so(self):
        """⚠️ Their own master measures +0.01 dBTP. Nothing here turns it down — the artist owns the level — but a
        lossy encode overshoots further, so the sentence is the whole value of the measurement."""
        hot = sound.Audio(codec="mp3", sample_rate=48000, channels=2, bitrate=171960, peak=0.01)

        complaints = hot.complaints()

        self.assertTrue(any("dBTP" in one and "distort" in one for one in complaints))
        self.assertTrue(any("the level is the artist's" in one for one in complaints), "diagnosis, not mastering")

    def test_a_quiet_master_is_reported_against_what_a_feed_plays_at(self):
        quiet = sound.Audio(codec="wav", sample_rate=48000, channels=2, integrated=-22.0)

        complaints = quiet.complaints()

        self.assertEqual(len(complaints), 1)
        self.assertIn("22.0 LUFS", complaints[0])
        self.assertIn("quieter", complaints[0])

    def test_a_good_master_has_nothing_said_about_it(self):
        master = sound.Audio(codec="flac", sample_rate=48000, channels=2, integrated=-14.2, peak=-1.4)

        self.assertEqual(master.complaints(), [])
        self.assertEqual(
            master.spoken(), "flac · 48 kHz · stereo · -14.2 LUFS · -1.4 dBTP", "one line, and every number in it"
        )


class TheDeliveryGuard(unittest.TestCase):
    """⚠️ **A re-encode may cost bits; it may not cost a channel, a rate, or the music.**"""

    def test_a_delivery_that_lost_the_audio_is_refused(self):
        complaints = sound.shortfalls(sound.Audio(codec="mp3", sample_rate=48000, channels=2, bitrate=171960), None)

        self.assertEqual(len(complaints), 1)
        self.assertIn("silent", complaints[0], "the one thing that is not a shrug")

    def test_a_rate_or_a_channel_lost_is_named(self):
        source = sound.Audio(codec="flac", sample_rate=48000, channels=2)
        delivered = sound.Audio(codec="aac", sample_rate=44100, channels=1)

        complaints = sound.shortfalls(source, delivered)

        self.assertEqual(len(complaints), 2)
        self.assertIn("44100 Hz against the master's 48000 Hz", complaints[0])
        self.assertIn("1 channels against the master's 2", complaints[1])

    def test_a_lossy_master_may_not_be_re_encoded_below_its_own_rate(self):
        source = sound.Audio(codec="mp3", sample_rate=48000, channels=2, bitrate=171960)
        cheap = sound.Audio(codec="aac", sample_rate=48000, channels=2, bitrate=128000)

        complaints = sound.shortfalls(source, cheap)

        self.assertEqual(len(complaints), 1)
        self.assertIn("128 kbps against the master's 172 kbps", complaints[0])
        self.assertIn("second generation", complaints[0])

    def test_a_lossless_master_is_allowed_a_lossy_delivery(self):
        """⚠️ **An mp4 carries no PCM**, so a lossless master is always delivered lossily — and 320k from a WAV is a
        single generation, not a shortfall. Comparing bitrates here would refuse every honest run."""
        source = sound.Audio(codec="flac", sample_rate=48000, channels=2, bitrate=1411200)
        delivered = sound.Audio(codec="aac", sample_rate=48000, channels=2, bitrate=317374)

        self.assertEqual(sound.shortfalls(source, delivered), [])

    def test_the_delivery_they_already_have_passes(self):
        """Their own numbers, measured: an mp3 master at 172 kbps, delivered as 317k AAC at the same rate and width."""
        source = sound.Audio(codec="mp3", sample_rate=48000, channels=2, bitrate=171960)
        delivered = sound.Audio(codec="aac", sample_rate=48000, channels=2, bitrate=317374)

        self.assertEqual(sound.shortfalls(source, delivered), [])


if __name__ == "__main__":
    unittest.main()

