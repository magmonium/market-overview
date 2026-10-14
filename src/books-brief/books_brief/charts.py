"""The four charts (ticket 12), as data.

⚠️ **A chart declares its *lists* and its *vendors*, and they are not the same number.** Ticket 17 counts
corroboration by **vendor**: Amazon.in's nine language categories are nine *lists* and **one source**, so the
all-language chart cannot satisfy the two-vendor gate on its own. That is not a defect in this table — it is the
finding, and it is why that chart has to state its scope (ticket 20's rule, and ticket 17's rule 3).

⚠️ ⚠️ **CORRECTED 2026-10-14 — these declarations now name lists the vendors actually serve.**

⚠️ **Three of the four charts used to declare lists their vendors do not publish.** The addresses had been written from
assumption — the same assumption ticket 02's source table made — and **every one was falsified by fetching the page**. The
corrections below are recorded because each one **changes what a chart ranks**, and a reader is owed the difference
between a repair and a choice:

| Was | Is now | Why, and what it costs |
|---|---|---|
| `pw/fiction` · `pw/nonfiction` | **removed** | ⚠️ **PW is paywalled**; its free pages are a 2012 archive. ⚠️ The English chart keeps NYT + Indie — still **two vendors**, which is ticket 17's gate, but with **no margin**: the chart ships only while both answer |
| `indie/fiction` · `indie/nonfiction` | `indie/national` | ⚠️ The site serves **one dated national list**, not two per-genre ones. ⚠️ Two lists became one, which is a smaller chart than the declaration claimed |
| `amazon-in/hindi` … `×9` | `amazon-in/indian-languages` | ⚠️ The nine do not exist; Amazon publishes **one mixed-language ranking**. ⚠️ **This takes the all-language chart from nine sources to one**, so it can never satisfy the two-vendor gate — which `charts.py` already said about it, and which is now **permanent** rather than accidental |
| `amazon-in/bengali` | **removed** | ⚠️ Amazon publishes **no Bengali list at all** — only an unordered search with no rank badges |
| `anandabazar/bengali` | **removed** | ⚠️ **No weekly list was ever located, and no client was ever written for it.** ⚠️ Under the address rule below it cannot be declared at all, so the Bengali chart loses its Indian half — and with it the `in`/`bd` country split ticket 20 demonstrated on |
| `rokomari/leaderboard` | `rokomari/best-sellers` | ⚠️ **The slug named neither address its client used.** The list is the **Best Seller category** — 60 `product` records when fetched — while `/list/38927`, which ticket 29 named, holds **none** |

⚠️ **Nothing was invented to fill a gap.** Where a source does not exist it is **absent** rather than substituted, because
a substituted list is a chart of the wrong books that looks entirely correct.

⚠️ **What this leaves:** `english` and `comics` have the **two vendors** ticket 17 requires and can build; `all-language`
has one and cannot corroborate itself; `bengali` has **one Bangladeshi list**, and it is **undated**, so the freshness
guard refuses it. ⚠️ **Two charts ship. Two do not**, and the two that do not are the ones whose sources do not exist
rather than the ones whose code is unfinished.

⚠️ ⚠️ **And a scraped list now declares its *address*.** `Listing.address` is required of every vendor in `SCRAPED`, and
the constructor **refuses** a scraped list that states none — because *"the address is the list's identity"*, and a slug
is a name nobody can check. ⚠️ That rule is what removed `anandabazar/bengali`: it had no address to give. ⚠️ **A comment
in a ticket is read once; a constructor that refuses is read on every run.**

⚠️ **And ticket 20's example moved.** The Bengali chart was the one whose country varied row to row (`in`, `bd`); with
Anandabazar gone it is `bd` throughout, and **`comics` is now the chart whose country varies** (`us`, `in`). ⚠️ The *rule*
is unchanged — a label draws only where it varies — and only the chart that demonstrates it changed.

⚠️ See **ticket 29**, which holds the evidence, the arithmetic and the decision this table now reflects.
"""
from __future__ import annotations

import dataclasses

#: The vendor slugs. ⚠️ A vendor is a **source**, not a list — the distinction ticket 17 turns on, and the reason
#: `vendors` and `lists` are separate fields rather than one.
ANANDABAZAR = "anandabazar"
AMAZON_IN = "amazon-in"
ROKOMARI = "rokomari"
NYT = "nyt"
PW = "pw"
INDIE = "indie"

#: ⚠️ **The vendors whose lists are *scraped*, and the reason `Listing.address` exists.**
#:
#: ⚠️ **An API vendor's list is *named*; a scraped vendor's list is *located*.** `nyt/hardcover-fiction` carries its own
#: name — the client sends it and the response says it back (`list_name_encoded`). ⚠️ A scraped list carries **no name at
#: all**: `amazon-in/comics` and `amazon-in/indian-languages` differ only by a node id nobody can guess from the slug, and
#: `rokomari/best-sellers` was declared for months under a slug that named **neither** address its client fetched.
#:
#: ⚠️ **So a scraped list must state its address, and `Listing` refuses one that does not** — the rule ticket 29 reached,
#: and the reason `anandabazar/bengali` could not survive it. ⚠️ `anandabazar` is listed here even though no chart declares
#: it any more: the refusal has to be waiting for whoever declares it next.
SCRAPED: frozenset[str] = frozenset({ANANDABAZAR, AMAZON_IN, ROKOMARI, INDIE})

#: Amazon.in's Indian-language bestseller categories, **as `(the vendor's word, the ISO code)`**.
#:
#: ⚠️ ⚠️ **NINE LISTS THAT DO NOT EXIST.** The all-language chart used to be built from these — one per language — and
#: **Amazon publishes no per-language bestseller list at all**: the books nav has no language category, the
#: Indian-languages node has no children, and the only per-language address is an unordered **search** with no rank
#: badges. ⚠️ Amazon publishes **one** mixed-language ranking instead, and the chart now ranks that.
#:
#: ⚠️ **Kept rather than deleted**, because it is the record of what was assumed and what was checked — and because the
#: distinction it carries is still real: the vendor's segment and the language's code are **not the same string**
#: (`english` vs `en`), which is the trap a future per-language source would hit again.
INDIAN_LANGUAGES: tuple[tuple[str, str], ...] = (
    ("hindi", "hi"),
    ("bengali", "bn"),
    ("tamil", "ta"),
    ("marathi", "mr"),
    ("malayalam", "ml"),
    ("telugu", "te"),
    ("kannada", "kn"),
    ("gujarati", "gu"),
    ("english", "en"),
)


@dataclasses.dataclass(frozen=True)
class Listing:
    """One list a chart reads — **where it is, and the two labels ticket 20 puts on its rows.**

    ⚠️ **Declared rather than derived, and the difference is real.** A slug carries its *vendor* — `amazon-in/comics` —
    but nothing in `rokomari/best-sellers` says *Bangladesh*, and nothing in `nyt/graphic-books-and-manga` says *US*.

    ⚠️ **And they cannot be chart-level fields either.** `comics` reads a US list and an Indian one, so a chart-level
    country would be wrong for it; a chart reading several Amazon.in language lists would have several languages.
    Declared per list, no chart is a special case.

    ⚠️ **So a list cannot be declared without them** — the discipline that makes `vendors` the spine (ticket 18), applied
    one level down, and what stops a label table drifting away from the sources it labels.

    ⚠️ ⚠️ **And a scraped list cannot be declared without its *address* either** (ticket 29). See `SCRAPED`: the
    constructor below is the rule, and this docstring is only its explanation.
    """

    slug: str
    #: ⚠️ ISO 3166-1 alpha-2, lower case — `in`, `bd`, `us`. **A value, never a name** (ADR 0003): the words are the
    #: renderer's, which is what lets *India & Bangladesh* become *ভারত ও বাংলাদেশ* without re-running a week.
    country: str
    #: ⚠️ The same shape for the language — `bn`, `hi`, `en`. ⚠️ **Empty means *unknown*, not *English***: a mixed-language
    #: ranking states no single language, and by ticket 20's rule an unknown label draws nothing rather than guessing.
    language: str
    #: ⚠️ **Where the list actually lives**, for a vendor in `SCRAPED`. An API vendor leaves it empty, because its list is
    #: named by the slug the client sends and the response says the name back; a scraped one must state it, because the
    #: slug is a name nobody can check.
    address: str = ""

    def __post_init__(self) -> None:
        """⚠️ **Refuse a scraped list that cannot say where it is** (ticket 29).

        ⚠️ This is the whole mechanism, and it is a refusal rather than a warning on purpose. The drift ticket 29 found
        was a table of slugs naming pages that do not exist — and every one of them **parsed, rendered and looked
        correct**. ⚠️ A list that cannot state its address is a list nobody can fetch, and learning that at *declaration*
        time is the difference between a spec that is wrong and a run that refuses.
        """
        vendor, _, _ = self.slug.partition("/")
        if vendor in SCRAPED and not self.address:
            raise ValueError(
                f"{self.slug} is a scraped list and states no address — a scraped list's slug is a name nobody can "
                f"check, so its address is its identity (ticket 29)"
            )


@dataclasses.dataclass(frozen=True)
class Chart:
    """One chart: what it ranks, where, in which language, and from which sources."""

    slug: str
    #: The renderer's label key — a stable slug, never the display text (ADR 0003).
    label_key: str
    #: The market this chart covers, spelled out because the chart has to **state** it (tickets 19, 21, 22).
    market: str
    #: The language the slide is set in.
    language: str
    #: ⚠️ The **spine** (ticket 18). Losing one of these makes the chart **absent**, not smaller — *"a degraded chart
    #: is a wrong chart."*
    vendors: tuple[str, ...]
    #: The lists the chart reads. One vendor may contribute several — and each carries its own country and language
    #: (ticket 20), because neither is a property of the chart.
    lists: tuple[Listing, ...]


ALL: tuple[Chart, ...] = (
    Chart(
        slug="bengali",
        label_key="bengali",
        market="bangladesh",
        language="bn",
        # ⚠️ **One vendor, and it is Bangladeshi** (corrected 2026-10-14). Ticket 21 built this chart as a bridge across two
        # countries — Anandabazar ranking India, Rokomari the Bangladeshi side — but ⚠️ **Anandabazar's weekly list was
        # never located and no client was ever written for it**, so under ticket 29's address rule it cannot be declared.
        #
        # ⚠️ **Amazon.in is removed too** (2026-10-14): it publishes **no Bengali list at all**, so the vendor could only
        # ever be a missing source — and a declared vendor that cannot answer makes the chart **absent**, which is the
        # outcome this correction is meant to *name* rather than leave implicit.
        #
        # ⚠️ **And the market narrows to what the sources support.** Ticket 19 refused to call a US-list chart *global*
        # for exactly this reason, and the same rule applies here: a chart ranking one Bangladeshi list is a
        # Bangladeshi chart, not an India-and-Bangladesh one.
        vendors=(ROKOMARI,),
        lists=(
            # ⚠️ **The one list in the whole set that is not Indian.** ⚠️ And it is **undated** — the payload carries no
            # date anywhere — so `freshness.is_fresh("")` is False and the chart goes **absent** every week until a date
            # is found. ⚠️ That is the guard working rather than a bug: ticket 10 requires a source to be *verified* to
            # have published for the week, and this one cannot be.
            Listing(
                slug="rokomari/best-sellers",
                country="bd",
                language="bn",
                address="https://www.rokomari.com/book/category/72/best-seller-books",
            ),
        ),
    ),
    Chart(
        slug="english",
        label_key="english",
        market="us",
        language="en",
        # ⚠️ Named `us` and not `world`, because all three are US lists (ticket 19) — and that is also why **neither of
        # ticket 20's labels appears on this chart**: a US list's rows are all US, and the language is in the header.
        #
        # ⚠️ **PW is removed** (2026-10-14): it is **paywalled**, and its free pages are a 2012 archive. ⚠️ That leaves
        # **two vendors**, which is exactly ticket 17's gate and **no margin at all** — the chart ships only while both
        # answer, where ticket 19 claimed three vendors meant one could be missing.
        vendors=(NYT, INDIE),
        lists=(
            Listing(slug="nyt/hardcover-fiction", country="us", language="en"),
            Listing(slug="nyt/hardcover-nonfiction", country="us", language="en"),
            # ⚠️ **One list, not two.** The site serves a single dated national list rather than per-genre ones, and the
            # date is part of its address — which is what makes its freshness verifiable (`indie.published_on`).
            # ⚠️ **The address is the *undated* form and the client appends the week's date**, because only the client
            # knows the week (ticket 29) — see `indie.fetch`.
            Listing(
                slug="indie/national",
                country="us",
                language="en",
                address="https://www.indiebound.org/bestseller-list-v2/national",
            ),
        ),
    ),
    Chart(
        slug="all-language",
        label_key="all_language",
        market="india",
        language="en",
        # ⚠️ One vendor. One list. The chart that cannot corroborate itself.
        vendors=(AMAZON_IN,),
        # ⚠️ **One mixed-language ranking, not nine per-language lists** (corrected 2026-10-14). Amazon's books nav has
        # no language category at all, and the nine this chart used to declare **do not exist**. ⚠️ **The nine became
        # one**, which is what takes this chart from nine sources to one — and makes its inability to satisfy the
        # two-vendor gate **permanent** rather than accidental.
        #
        # ⚠️ **And the language is empty, because the list does not state one.** A mixed ranking carries Hindi, Tamil,
        # Telugu and Urdu rows side by side, so a single `Listing.language` would be confidently wrong on most of them —
        # and by ticket 20's rule a *constant* label **renders**, which would put the wrong language on a hundred rows.
        # ⚠️ Empty means *unknown*, and unknown draws no label.
        lists=(
            Listing(
                slug="amazon-in/indian-languages",
                country="in",
                language="",
                # ⚠️ **Amazon's own node id is the list's identity** — the slug above is only a name (ticket 29), and the
                # address is what `amazon.fetch` actually requests.
                address="https://www.amazon.in/gp/bestsellers/books/86946561031/",
            ),
        ),
    ),
    Chart(
        slug="comics",
        label_key="comics",
        market="worldwide",
        language="en",
        vendors=(NYT, AMAZON_IN),
        # ⚠️ **And this is now the chart whose country varies** (`us`, `in`) — ticket 20's example, moved here when the
        # Bengali chart lost its Indian list (ticket 29). ⚠️ The rule is unchanged: a label draws only where it varies.
        lists=(
            Listing(slug="nyt/graphic-books-and-manga", country="us", language="en"),
            Listing(
                slug="amazon-in/comics",
                country="in",
                language="en",
                address="https://www.amazon.in/gp/bestsellers/books/1318104031/",
            ),
        ),
    ),
)


#: ⚠️ **The chart slugs, in declaration order** — for a caller that has to offer them or report them.
#:
#: ⚠️ **Derived, never spelled twice.** A menu that listed the charts itself would be a second place to keep them right,
#: and a `--chart` flag that named one the table does not have would be a typo the run only discovers mid-gather.
KNOWN: tuple[str, ...] = tuple(chart.slug for chart in ALL)


def get(slug: str) -> Chart:
    """One chart by slug.

    ⚠️ An unknown slug is a **refusal**, not a default: a chart that silently fell back to another chart's sources
    would be the kind of quiet wrong answer this product exists not to give.
    """
    for chart in ALL:
        if chart.slug == slug:
            return chart
    known = ", ".join(chart.slug for chart in ALL)
    raise KeyError(f"unknown chart {slug!r} — the charts are {known}")
