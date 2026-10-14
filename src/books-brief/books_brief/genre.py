"""The genre vocabulary (ticket 26).

⚠️ **Genre is a classification, not a field.** Every source names its categories its own way — Amazon's browse nodes,
NYT's list names, Google Books' BISAC-ish `categories` — so the label is a **normalisation**, and this module is where
the mapping lives.

⚠️ **The mapping is an explicit table, never a runtime guess.** Ticket 03 requires a week to be replayable, and a label
derived by pattern-matching a category name would be non-deterministic: the same week could label a book two ways. So
an unknown category is **`other`**, which is a real value and not a failure.

⚠️ **The ranking source wins** (ticket 17). A title is on the business list because the *vendor* put it there, so this
vocabulary maps whatever the vendor said rather than overriding it with a code from somewhere else.
"""
from __future__ import annotations

#: ⚠️ **The vocabulary, and `other` is one of the values.** These slugs ride in `facts.json`; the words a viewer reads
#: live in the renderer's label table (ADR 0003), so renaming a genre is a copy change and not a data migration.
SLUGS: tuple[str, ...] = (
    "poetry",
    "novel",
    "fiction",
    "non-fiction",
    "business",
    "self-help",
    "biography",
    "history",
    "religion",
    "children",
    "comics",
    "academic",
    "reference",
    "other",
)

#: ⚠️ **Keys are lower-cased**, because the sources disagree about case and a case-sensitive table would silently fall
#: through to `other` on a vendor that shouts.
MAPPING: dict[str, str] = {
    # ── Amazon.in's browse nodes ──────────────────────────────────────────────
    "business & economics": "business",
    "literature & fiction": "fiction",
    "comics & mangas": "comics",
    "children's books": "children",
    "biographies, diaries & true accounts": "biography",
    "religion & spirituality": "religion",
    "history": "history",
    "poetry": "poetry",
    "self-help": "self-help",
    "textbooks & study guides": "academic",
    "reference": "reference",
    "crime, thriller & mystery": "fiction",
    "fantasy, horror & science fiction": "fiction",
    "romance": "novel",
    "historical fiction": "novel",
    "health, family & personal development": "self-help",
    "society & social sciences": "non-fiction",
    "science & mathematics": "non-fiction",
    "arts, film & photography": "non-fiction",
    # ── NYT's list names ──────────────────────────────────────────────────────
    "hardcover-fiction": "fiction",
    "hardcover-nonfiction": "non-fiction",
    "paperback-nonfiction": "non-fiction",
    "trade-fiction-paperback": "fiction",
    "advice-how-to-and-miscellaneous": "self-help",
    "graphic-books-and-manga": "comics",
    "childrens-middle-grade-hardcover": "children",
    "young-adult-hardcover": "children",
    "business": "business",
    "science": "non-fiction",
    # ── Google Books' BISAC-ish `categories` ──────────────────────────────────
    "fiction": "fiction",
    "juvenile fiction": "children",
    "comics & graphic novels": "comics",
    "biography & autobiography": "biography",
    "religion": "religion",
    "study aids": "academic",
    "literary collections": "fiction",
    "true crime": "non-fiction",
}


def slug_for(category: str) -> str:
    """One genre slug for a vendor's category name.

    ⚠️ **An exact lookup, and `other` when there is none.** A "nearest match" would be a guess, and a guess cannot be
    replayed — which is the one thing ticket 03 will not give up.
    """
    return MAPPING.get(category.strip().lower(), "other")
