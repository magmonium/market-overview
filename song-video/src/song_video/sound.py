"""What the delivery actually sounds like — measured, reported, and **never adjusted** (issue 09).

⚠️ **Sound is not a setting, it is a measurement.** A pipeline that "improves" the audio has taken a decision the
artist owns: the level, the dynamics and the length are theirs (issue 09), and the brief's `loudnorm` is deliberately
absent for that reason. What is *not* theirs — and not visible anywhere either — is **what the file has already
lost** and **what the encode is about to lose**, and that is what this module puts a number on.

| It answers | With |
|---|---|
| how good is the source? | codec, sample rate, channels, bitrate, integrated loudness, true peak |
| is it lossy already? | the codec — a delivery can never be clearer than its master, so that is a **ceiling**, not a setting |
| will the encode clip? | true peak against `PEAK_CEILING` — a lossy encoder overshoots, and above 0 dBTP it overshoots into distortion |
| did the delivery lose anything? | the delivered stream against the staged master's, in `shortfalls` |

⚠️ **The toolchain is the brief's**, exactly as `master.py` uses it: `audio.binary` finds the operator's ffmpeg (or
Remotion's bundled one), and that bundled build is `--enable-shared`, so it is **never** invoked without
`audio.binary_env()`'s loader path — a plain `subprocess` call against it dies with `SIGABRT`, which is an afternoon
already lost and written down in the brief for that reason.

⚠️ **A failed measurement is a printed sentence, not a refusal.** The *length* is load-bearing — a piece whose length
nobody chose is not a piece (`master.py`) — but loudness is a diagnostic: `measure` returns what it could read, and
`None` fields mean *unknown* rather than zero. The one exception is a file with **no audio stream at all**, which is
not a measurement anybody can shrug at: the whole product is the music.
"""
from __future__ import annotations

import dataclasses
import json
import math
import os
import pathlib
import subprocess

from market_overview import audio

from . import paths

#: ⚠️ The codecs that have **already thrown information away**. A delivery re-encodes whatever it is given, so a lossy
#: master is a *ceiling* rather than a starting point — the most useful thing the ledger can say about sound, and the
#: reason a lossless master is the only change that raises it.
LOSSY = frozenset({"mp3", "aac", "opus", "vorbis", "wmav2"})

#: ⚠️ **A ceiling that is reported, never enforced.** −1 dBTP is the usual delivery headroom, and a file already at or
#: above it will be clipped by the lossy encode that follows — but capping it means turning the music down, and that
#: decision is the artist's (issue 09). So this number produces a *sentence*, and the run carries on.
PEAK_CEILING = -1.0

#: ⚠️ **YouTube's reference level, borrowed from the brief rather than re-typed** — the −14 LUFS that
#: `market_overview.audio.TARGET_LUFS` normalises the bed to. It is a *reference* for the analysis only: nothing here
#: changes a level, and the number is what says how far the song sits from what a feed plays at.
REFERENCE_LUFS = audio.TARGET_LUFS

#: `loudnorm` in measurement mode. ⚠️ **That filter is on the bundled build's allow-list** — `afade`, `volumedetect`
#: and `astats` are *not*, so "measure the peak the obvious way" is exactly what does not work here.
ANALYSIS = f"loudnorm=I={REFERENCE_LUFS:g}:TP=-1.5:LRA=11:print_format=json"


@dataclasses.dataclass(frozen=True)
class Audio:
    """One file's sound, as measured. ⚠️ `None` means *unknown*, never zero."""

    codec: str
    sample_rate: int
    channels: int
    bitrate: int | None = None
    #: Integrated loudness in LUFS, and the true peak in dBTP.
    integrated: float | None = None
    peak: float | None = None
    #: Loudness range, in LU — how much the piece asks of a listener's volume control.
    range_lu: float | None = None

    @property
    def lossless(self) -> bool:
        return self.codec.lower() not in LOSSY

    def spoken(self) -> str:
        """One line for the ledger: what the file *is*, and what it measures."""
        parts = [
            self.codec or "unreadable",
            f"{self.sample_rate / 1000:g} kHz",
            "stereo" if self.channels == 2 else f"{self.channels} ch",
        ]
        if self.bitrate:
            parts.append(f"{self.bitrate / 1000:.0f} kbps")
        if self.integrated is not None:
            parts.append(f"{self.integrated:.1f} LUFS")
        if self.peak is not None:
            parts.append(f"{self.peak:+.1f} dBTP")
        if self.range_lu is not None:
            parts.append(f"range {self.range_lu:.1f} LU")
        return " · ".join(parts)

    def complaints(self) -> list[str]:
        """What is wrong with this file **as a master** — the facts nobody can see by looking.

        ⚠️ Every one of them is phrased as something the operator owns. This module diagnoses; issue 09 keeps the cure
        on the artist's side of the line, and that is the whole point of measuring rather than "fixing".
        """
        wrong: list[str] = []
        if not self.lossless:
            kbps = f" at {self.bitrate / 1000:.0f} kbps" if self.bitrate else ""
            wrong.append(
                f"the master is {self.codec}{kbps} — lossy, so the delivery can be no clearer than this. A lossless "
                f"master (WAV or FLAC) is the one change that raises the ceiling"
            )
        if self.peak is not None and self.peak > PEAK_CEILING:
            wrong.append(
                f"the master already peaks at {self.peak:+.2f} dBTP, above the {PEAK_CEILING:g} dBTP delivery "
                f"ceiling — a lossy encode overshoots further, so it distorts where the uploader re-encodes it. "
                f"Lowering it is a level change, the level is the artist's (issue 09), and this run only says so"
            )
        if self.integrated is not None and self.integrated < REFERENCE_LUFS - 1:
            quieter = REFERENCE_LUFS - self.integrated
            wrong.append(
                f"the master sits at {self.integrated:.1f} LUFS, {quieter:.1f} dB below the {REFERENCE_LUFS:g} LUFS a "
                f"feed plays at — YouTube turns loud material *down* to it and leaves quiet material alone, so this "
                f"song will play quieter than the songs beside it"
            )
        return wrong


def measure(path: pathlib.Path, *, root: pathlib.Path | None = None, timeout: float = 300.0) -> Audio | None:
    """Measure one file's audio, or `None` when it has no audio stream this toolchain can read.

    ⚠️ **Two passes, and they answer different questions.** `ffprobe` gives the stream's *shape* — codec, rate,
    channels, bitrate — which is instant, and is what the delivery guard compares. `loudnorm` gives the *loudness* —
    integrated LUFS, true peak, range — which costs a full decode, and is worth paying for on the master and nothing
    else.
    """
    where = paths.repo_root() if root is None else root
    ffmpeg = audio.binary(where)
    probe = audio.probe_binary(ffmpeg)
    if probe is None:
        return None

    try:
        # ⚠️ `audio.run`, never a bare `subprocess`: the bundled binaries need the loader path, or they SIGABRT.
        reported = json.loads(
            audio.run(
                probe,
                [
                    "-v", "error",
                    "-select_streams", "a",
                    "-show_entries", "stream=codec_name,sample_rate,channels,bit_rate",
                    "-of", "json",
                    str(path),
                ],
                timeout=timeout,
            )
        )["streams"]
    except (audio.AudioError, subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
        return None
    if not reported:
        return None

    stream = reported[0]
    return Audio(
        codec=str(stream.get("codec_name", "")),
        sample_rate=int(stream.get("sample_rate") or 0),
        channels=int(stream.get("channels") or 0),
        bitrate=int(stream["bit_rate"]) if stream.get("bit_rate") else None,
        **loudness(path, ffmpeg=ffmpeg, timeout=timeout),
    )


def loudness(path: pathlib.Path, *, ffmpeg: pathlib.Path, timeout: float = 300.0) -> dict[str, float | None]:
    """The three numbers `loudnorm` can report — or `None` for each, when it cannot report them.

    ⚠️ **Read off stderr, which is why this is not `audio.run`.** `audio.run` returns stdout, and `print_format=json`
    produces a *diagnostic*: it lands on stderr, surrounded by the usual banner. The block is taken from its last `{`
    to its last `}` rather than parsed in place, because ffmpeg keeps talking afterwards.
    """
    blank: dict[str, float | None] = {"integrated": None, "peak": None, "range_lu": None}
    try:
        done = subprocess.run(
            [str(ffmpeg), "-hide_banner", "-nostats", "-i", str(path), "-af", ANALYSIS, "-f", "null", "-"],
            capture_output=True,
            text=True,
            timeout=timeout,
            # ⚠️ The loader path, again — without it this is a SIGABRT rather than a measurement.
            env={**os.environ, **audio.binary_env(ffmpeg)},
        )
    except (subprocess.SubprocessError, OSError):
        return blank

    floor, ceiling = done.stderr.rfind("{"), done.stderr.rfind("}")
    if floor < 0 or ceiling < floor:
        return blank
    try:
        measured = json.loads(done.stderr[floor : ceiling + 1])
    except json.JSONDecodeError:
        return blank

    def number(key: str) -> float | None:
        try:
            value = float(measured[key])
        except (KeyError, TypeError, ValueError):
            return None
        # ⚠️ A silent file measures `-inf` LUFS — a number JSON carries happily and prose cannot, so it becomes
        # *unknown* rather than a complaint about "−inf dB below the reference".
        return value if math.isfinite(value) else None

    return {"integrated": number("input_i"), "peak": number("input_tp"), "range_lu": number("input_lra")}


def shortfalls(source: Audio | None, delivered: Audio | None) -> list[str]:
    """What the delivery **lost** against the master — the guard, and the only part of this module that refuses.

    ⚠️ **A re-encode may cost bits; it may not cost a channel, a rate, or the music.** So the comparisons are exact
    where the format cannot silently absorb them: the delivered rate must be at least the master's, the channel count
    must match, and — ⚠️ **only when the master is lossy** — the bitrate must not fall *below* it, which is the
    difference between an honest re-encode and a cheaper second generation of the same artefacts. A lossless master is
    always delivered lossily (an mp4 carries no PCM), so no bitrate comparison there would mean anything.
    """
    if delivered is None:
        return ["the delivery has no audio stream this toolchain can read — the song would be silent"]
    if source is None:
        return []

    lost: list[str] = []
    if delivered.sample_rate < source.sample_rate:
        lost.append(f"the delivery is {delivered.sample_rate} Hz against the master's {source.sample_rate} Hz")
    if delivered.channels != source.channels:
        lost.append(f"the delivery has {delivered.channels} channels against the master's {source.channels}")
    if not source.lossless and source.bitrate and delivered.bitrate and delivered.bitrate < source.bitrate:
        lost.append(
            f"the delivery is {delivered.bitrate / 1000:.0f} kbps against the master's "
            f"{source.bitrate / 1000:.0f} kbps — a lossy master re-encoded below its own rate is a second "
            f"generation of the same artefacts"
        )
    return lost
