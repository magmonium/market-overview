"""The still's caption — the duration, and the language it is written in. (Map issue 08)

⚠️ **A duration is a *value*; "সংগীত" is a *word*.** The value is formatted here, because Python decides and pytest
can reach it (ADR 0002), and the word stays in the render layer's label table — the same split the brief makes
between its facts bundle and its `copy.<lang>.json`. Two halves of one line, assembled in two places **on purpose**,
so neither side can quietly invent copy.

⚠️ **The language is chosen from the title's own script, and that is a *default* rather than a rule.** A Bengali
title above an English caption reads like a template somebody forgot to translate, so the caption follows the
script the operator typed — and `--lang` overrides it, because the reel does not know what language a song is in
and must not pretend to.
"""
from __future__ import annotations

#: The Bengali block. One codepoint anywhere in the title is enough to choose the caption's script: a title that is
#: *mostly* Bengali with a Latin artist name is still a Bengali title.
BENGALI = range(0x0980, 0x0A00)

#: The languages a caption can be written in. ⚠️ The same two the render layer's label table covers, and the test
#: that keeps them in step is the one that fails when a language is added on one side only.
LANGUAGES: tuple[str, ...] = ("bn", "en")

#: ⚠️ **Bengali has its own digits, and a Bengali caption written in ASCII numerals looks unfinished.** This is a
#: translation table rather than arithmetic so nobody has to know that ০ is U+09E6.
DIGITS: dict[str, str] = {
    "bn": "০১২৩৪৫৬৭৮৯",
    "en": "0123456789",
}


def language_of(title: str) -> str:
    """`bn` when the title is written in Bengali, `en` otherwise — the caption's default script."""
    return "bn" if any(ord(character) in BENGALI for character in title) else "en"


def duration_at(seconds: float, *, lang: str) -> str:
    """The piece's length as a caption: `৪:০০`, or `4:00`.

    ⚠️ **Minutes and seconds, because a song is minutes long.** An hour-long piece would print `61:03` rather than
    growing an hours field nobody would ever see — and rounding to the nearest second is the honest reading of a
    length only a container knows exactly.
    """
    if lang not in LANGUAGES:
        raise ValueError(f"unknown language {lang!r} — the languages are {', '.join(LANGUAGES)}")

    whole = int(round(seconds))
    minutes, remainder = divmod(whole, 60)
    digits = DIGITS[lang]

    def written(number: int, width: int = 1) -> str:
        """⚠️ **Digits only.** Translating the whole `4:00` string would send the colon through the digit table as
        well — which raises, and did."""
        return "".join(digits[int(digit)] for digit in f"{number:0{width}d}")

    return f"{written(minutes)}:{written(remainder, 2)}"
