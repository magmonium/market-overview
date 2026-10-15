"""Ticket 32 — the identity of a title: **the work, not the product**.

⚠️ **A chart of "Top 100 books" is a chart of *works*, and until this module it was keyed by *products*.** Ticket 14's
rule was `chart + ISBN`, which is exact and stable and says nothing about editions — so a book with a US and a UK
edition is two ISBNs, and the English chart ranked it **twice** (measured 2026-10-15: 100 rows holding **92 distinct
titles**, eight of them pairs). ⚠️ That is not a rounding error in a tie-break; it is the chart telling a reader that one
book is two books, and it is invisible unless you count the titles.

⚠️ ⚠️ **What replaces it, and why it is not a fuzzy match.** The key is `normalised(title) + normalised(author)` —
**exact**, not similar, and the author is part of it. ⚠️ Ticket 05 §3 refused *"a single fuzzy title search"* for identity
resolution, and the reason holds here for the same reason: **an under-merge is a duplicate, and an over-merge is a wrong
chart.** Only one of those can be repaired after the fact, so the rule errs toward keeping two rows.

⚠️ **And the cost of that is real and measured**: Dey's spells two authors differently from BoiChitro — `Saradindu
Bandopadhyay` against `Sharadindu Bandyopadhyay`, `Satyajit Roy` against `Satyajit Ray` — so an exact key merges **3 of
the 5** titles the two shops share, where a title-only key would merge 5.

⚠️ **Hence `SPELLINGS`, and it is data rather than a rule** — the same shape as `genre.py`'s vocabulary table, and for
the same reason: *"the vendors disagree about category names, and a runtime guess would not be replayable."* ⚠️ **An entry
exists only where two vendors' lists were measured to carry the *same title* under two spellings of one author**, so the
justification is a work match rather than a resemblance between names. ⚠️ A table like this can rot: a third vendor's
third spelling is a new entry, not a looser rule.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Mapping

#: ⚠️ ⚠️ **The author spellings two vendors disagree about, with the evidence for each.** Keys and values are both
#: **normalised** (see `normalise`), so an entry is written the way the comparison sees it rather than the way a reader
#: would — and a caller never has to remember which spelling is canonical.
#:
#: | Normalised variant | Canonical | Measured where |
#: |---|---|---|
#: | `saradindubandopadhyay` | `sharadindubandyopadhyay` | `Byomkesh Samagra` — Dey's `Saradindu Bandopadhyay`, BoiChitro `Sharadindu Bandyopadhyay` |
#: | `satyajitroy` | `satyajitray` | `Galpa 101` — Dey's `Satyajit Roy`, BoiChitro `Satyajit Ray` |
#:
#: ⚠️ Both are the **same person** spelled two ways (শরদিন্দু বন্দ্যোপাধ্যায়, সত্যজিৎ রায়), and both were found by
#: comparing what the two shops say about **one book** rather than by comparing the names.
#:
#: ⚠️ ⚠️ **And the canonical value has to be a spelling a vendor actually uses** — this table's first draft pointed
#: `saradindubandopadhyay` at `sharindubandyopadhyay`, which is neither vendor's spelling (the `a` in *Sharadindu* was
#: dropped), and the entry therefore resolved to a key no row could ever produce. ⚠️ `tests/test_identity.py` caught it
#: on the first run, which is the argument for the table being data with a test rather than a rule with a comment.
SPELLINGS: dict[str, str] = {
    "saradindubandopadhyay": "sharadindubandyopadhyay",
    "satyajitroy": "satyajitray",
}

#: ⚠️ **Everything that is not a letter or a digit goes**, and the Bengali block is kept **whole** — including its
#: combining marks, which carry the vowel signs. ⚠️ A normaliser that kept only `a-z0-9` would turn every Bengali title
#: into the empty string, and every Bengali row on a chart into **one row**.
_UNKEPT = re.compile(r"[^a-z0-9\u0980-\u09ff]+")


def normalise(text: str) -> str:
    """A string reduced to what two vendors can be expected to agree on.

    ⚠️ **Four reductions, and each one is a measured disagreement rather than a preference:** `NFKD` folds a composed
    character into its parts (so two encodings of the same Bengali vowel sign compare equal), `casefold` folds case
    (`TENIDA SAMAGRA` is `Tenida Samagra` on BoiChitro), and punctuation and whitespace go — a shop writes
    `Putul Nacher Itikatha` where another writes `Putul Nacher Itikatha` with a colon.

    ⚠️ **Deliberately not a stemmer and not a fuzzy distance.** `Galpa 101` and `Galpa 102` must stay different books,
    and so must `A Court of Splintered Harmony` and `A Court of Forgotten Melody` — which a similarity threshold would
    happily merge.
    """
    folded = unicodedata.normalize("NFKD", text or "").casefold()
    return _UNKEPT.sub("", folded)


def spelling(author: str) -> str:
    """`author`, normalised and resolved through `SPELLINGS` — **the one place a spelling is decided**.

    ⚠️ **Applied to the author and not to the title**, and that asymmetry is the point: two vendors transliterate *a
    person's name* differently far more often than they disagree about a title, and every entry here was justified by a
    title that already agreed.
    """
    normalised = normalise(author)
    return SPELLINGS.get(normalised, normalised)


#: ⚠️ The ISBN-13 prefix for a title that was published as ISBN-10. A book that was *only* ever ISBN-13 carries its own
#: prefix (978 or 979) and must not be re-prefixed.
PREFIX = "978"


def _check_digit(body: str) -> str:
    """The EAN-13 check digit for a twelve-digit body.

    ⚠️ **Recomputed, never carried over.** An ISBN-10's check digit is computed by a different rule and is not valid
    for a thirteen-digit ISBN — so an implementation that prefixed `978` and kept the old digit would produce a
    plausible string matching no real book, and nothing downstream could tell.
    """
    total = sum(
        int(digit) * (1 if position % 2 == 0 else 3)
        for position, digit in enumerate(body)
    )
    return str((10 - total % 10) % 10)


def isbn13(raw: str) -> str:
    """The ISBN-13 for a ten- or thirteen-digit ISBN, or `""` when the input is not one.

    ⚠️ **`""` rather than a guess.** A caller that gets an empty string knows the identity is unresolved and can mark
    the row; a caller handed a fabricated key would have no way to tell.

    ⚠️ ⚠️ **It lives here rather than in `enrich`, where ticket 05 wrote it, because two *decisions* need it and only
    one of them is enrichment** (ticket 32): `corroborate.admit` uses it to tell a real ISBN from a synthetic key when
    it unions two groups, and `enrich` uses it to mark a row's identity resolved. ⚠️ The gate cannot import `enrich`
    without a cycle — `enrich` imports `rank`, which imports `corroborate` — so the function moved to the module that
    has no local imports at all, and `enrich.isbn13` remains a re-export so no caller changes.
    """
    digits = "".join(
        character for character in raw if character.isdigit() or character in "Xx"
    )

    if len(digits) == 13:
        return digits
    if len(digits) != 10:
        return ""

    body = f"{PREFIX}{digits[:9]}"
    return body + _check_digit(body)


def from_row(row: Mapping[str, object]) -> str:
    """The identity a **snapshot row** carries — `key`, or `isbn` for a week recorded before ticket 32.

    ⚠️ **The fallback is not a convenience, it is the migration.** The store holds weeks written under ticket 14's
    `chart + ISBN` rule, and a window or a Δ that could not read them would score every title in them at zero — which is
    indistinguishable from those weeks not existing, and would report a whole chart as NEW on the first week after the
    change. ⚠️ `isbn` *was* the key then, so reading it is reading the same fact under its old name rather than guessing.

    ⚠️ **It lives here rather than in `window` or `delta`** because both need it and one of them importing the other is
    a cycle — `window` already imports `delta` for `previous_week`.
    """
    return str(row.get("key") or row.get("isbn") or "")


def work(title: str, author: str = "") -> str:
    """The chart's identity for a title — **`title|author`, both normalised.**

    ⚠️ **The author is part of the key even when it is empty**, so a row whose vendor states no author produces
    `title|` — which **cannot merge** with `title|author` from a vendor that does. ⚠️ That is the conservative
    direction on purpose: two rows that fail to merge are two rows on the chart, while two rows wrongly merged are a
    book that does not exist.

    ⚠️ **The separator is `|`**, which `normalise` strips from every input — so no title can forge a key boundary.
    """
    return f"{normalise(title)}|{spelling(author)}"
