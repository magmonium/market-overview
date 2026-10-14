"""Fixtures the reel's tests share.

⚠️ **A WAV written by the standard library, not a supplied song.** `resource/reel/song/` is operator-supplied and
gitignored, so a test that needed a real master would depend on a file the repository does not contain. A
16-bit mono WAV of a known length is tens of kilobytes and byte-identical every time it is written — which is
what lets the digest test assert a literal from `shasum` rather than recomputing the hash the way the module
does.
"""
import pathlib
import wave


def write_wav(path: pathlib.Path, *, seconds: float, rate: int = 8000) -> pathlib.Path:
    """A valid WAV of a known length, built with `wave` alone — no toolchain needed to make a fixture."""
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(b"\x00\x00" * int(round(rate * seconds)))
    return path
