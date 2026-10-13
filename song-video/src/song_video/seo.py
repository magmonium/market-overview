"""The upload text — a title and a description, written for the song and for search.

⚠️ **Copy is the render layer's, values are Python's — except here, where the copy is a *file*.** The caption's word
(`সংগীত`) lives in the render layer because it is *drawn*; this text is never drawn. It is written beside the reel to be
pasted into an uploader, so it is Python's — which is also what makes it reachable from pytest (ADR 0002) and what
makes it reproducible.

⚠️ **A pure function of the answers, byte for byte.** The title and the description come from the string the operator
typed, the **recorded** duration, the language, and the artist if one was given — no clock, no random choice, and
nothing read out of the cover art. A rebuild writes the same two files, which is the same promise the frames keep
(ADR 0003).

⚠️ **SEO, honestly.** The strongest signal a Bengali music video has is the song's own title, so it leads, in the
script it was typed in. Then the duration, because *"how long is it"* is a real search. Then both scripts' words for
what this is — `বাংলা গান` **and** `Bangla song` — because people search in both, and neither is stuffing. And nothing
here claims anything about the music the pipeline could not know: the one sentence of editorial copy states the thing
that is literally true of every reel this tool makes — the song is the master, complete and unaugmented (issue 09).

⚠️ **The artist is optional and never guessed.** Nothing in `resource/song/` carries one: a filename is not metadata
and a cover is a picture (issue 04's rule). So `--artist` is the only way in, and its absence **drops the line**
rather than leaving a placeholder for somebody to edit — a file that needs editing is not a generated file.
"""
from __future__ import annotations

import dataclasses

from . import caption

#: ⚠️ YouTube's ceiling on a title, so the fit is **checked** rather than hoped for. The reel's own rule applies here
#: too: a title that will not fit is a title to shorten, never a layout to bend.
TITLE_LIMIT = 100

#: ⚠️ **Authored copy, like a theme's palette** — not generated, and *not* one idea translated twice: a Bengali search
#: and a Latin one are two different queries, which is why both are spelled out rather than derived from each other.
LABELS: dict[str, dict[str, str]] = {
    "bn": {
        "genre": "বাংলা গান",
        "artist": "শিল্পী",
        "length": "দৈর্ঘ্য",
        "minutes": "মিনিট",
        "seconds": "সেকেন্ড",
        "uncut": "সম্পূর্ণ গান, কোনও কাটছাঁট নেই",
        "line": "গানটি অপরিবর্তিত — মূল রেকর্ডিং যেমন আছে তেমনই, শুধু একটি স্থির চিত্রের সঙ্গে।",
        "reel": "Song Reel · বাংলা গান (Bangla song)",
        "tags": "#বাংলাগান #BanglaSong #বাংলাসংগীত #BanglaMusic",
    },
    "en": {
        "genre": "Bengali song",
        "artist": "Artist",
        "length": "Length",
        "minutes": "min",
        "seconds": "sec",
        "uncut": "the full song, uncut",
        "line": "The song plays exactly as it was recorded — never normalised, trimmed or re-mastered.",
        "reel": "Song Reel · Bengali song",
        "tags": "#BengaliSong #BanglaSong #BanglaMusic",
    },
}


class SeoError(RuntimeError):
    """The upload text cannot be written from these answers, so the run stops before it renders an hour of frames."""


def labels(lang: str) -> dict[str, str]:
    """The copy for one script. ⚠️ An unknown language is a refusal rather than an English fallback: a Bengali song
    described in English, or the reverse, is the template nobody translated that `caption.py` already refuses."""
    if lang not in LABELS:
        raise SeoError(f"unknown language {lang!r} — the languages are {', '.join(sorted(LABELS))}")
    return LABELS[lang]


def duration_words(seconds: float, *, lang: str) -> str:
    """`৩ মিনিট ২ সেকেন্ড` — the length *spelled out*, because that is how somebody searches for it.

    ⚠️ The numerals are `caption.DIGITS`', the same table the caption and the reel's time line use: one place decides
    that ০ is U+09E6, and a description that counted differently from the video it describes would be an obvious tell.
    """
    whole = int(round(seconds))
    minutes, remainder = divmod(whole, 60)
    digits = caption.DIGITS[lang] if lang in caption.DIGITS else caption.DIGITS["en"]

    def written(number: int) -> str:
        return "".join(digits[int(digit)] for digit in f"{number:d}")

    copy = labels(lang)
    return f"{written(minutes)} {copy['minutes']} {written(remainder)} {copy['seconds']}"


@dataclasses.dataclass(frozen=True)
class Upload:
    """The two strings an uploader asks for — and the two files the package writes."""

    title: str
    description: str


def title_for(title: str, *, lang: str, seconds: float, artist: str = "") -> str:
    """The line a search result shows.

    ⚠️ **Song first, because the song's name is the query.** Then the artist when one was given, then the length, then
    the genre — and the length and the genre stay even when the title is long, because they are the parts somebody who
    does not already know the song would be searching for.
    """
    copy = labels(lang)
    parts = [title.strip()]
    if artist.strip():
        parts.append(artist.strip())
    parts.append(caption.duration_at(seconds, lang=lang))
    parts.append(copy["genre"])

    line = " | ".join(parts)
    if len(line) > TITLE_LIMIT:
        raise SeoError(
            f"the upload title is {len(line)} characters, over the {TITLE_LIMIT} a search result shows — shorten the "
            f"title itself, rather than dropping the length and the genre: {line!r}"
        )
    return line


def upload_for(title: str, *, lang: str, seconds: float, artist: str = "") -> Upload:
    """Both strings, from the recorded answers and nothing else.

    ⚠️ **The description says only what this pipeline knows.** The song's name as it was typed, the length it measured,
    who the operator says the artist is, and one sentence that is true of every reel by construction: the song is the
    master, complete and untouched (issue 09). Nothing about the music's mood, meaning or origin appears here, because
    none of that was supplied and a generated file that guesses is worse than no file.
    """
    copy = labels(lang)
    head = [title.strip()]
    if artist.strip():
        head.append(f"{copy['artist']}: {artist.strip()}")
    head.append(
        f"{copy['length']} {caption.duration_at(seconds, lang=lang)} "
        f"({duration_words(seconds, lang=lang)}) · {copy['uncut']}"
    )
    body = [copy["line"], copy["reel"], copy["tags"]]
    return Upload(title=title_for(title, lang=lang, seconds=seconds, artist=artist),
                  description="\n\n".join(["\n".join(head), "\n".join(body)]) + "\n")
