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

⚠️ ⚠️ **And that summary is superseded — every clause of it** (tickets 30–33). `bengali` found **two more vendors** and
builds (ticket 30/32); `all-language` builds because **corroboration stopped being a gate** (ticket 17, reversed — see
`corroborate`); and `comics` gained a **third vendor**. ⚠️ **What kept `comics` off the shelf was not a missing source
either**: the note above assumed its NYT list was weekly, and the payload says `MONTHLY`, so the guard's ten-day span was
the thing refusing it. ⚠️ The corrections are recorded here rather than deleted because the *shape* of each mistake is the
same one this table keeps finding: a **source's** cadence and address were written from assumption and only the fetch
settled them. See `CADENCES`.

⚠️ ⚠️ **And a scraped list now declares its *address*.** `Listing.address` is required of every vendor in `SCRAPED`, and
the constructor **refuses** a scraped list that states none — because *"the address is the list's identity"*, and a slug
is a name nobody can check. ⚠️ That rule is what removed `anandabazar/bengali`: it had no address to give. ⚠️ **A comment
in a ticket is read once; a constructor that refuses is read on every run.**

⚠️ **And ticket 20's example moved.** The Bengali chart was the one whose country varied row to row (`in`, `bd`); with
Anandabazar gone it is `bd` throughout, and **`comics` is now the chart whose country varies** (`us`, `in`). ⚠️ The *rule*
is unchanged — a label draws only where it varies — and only the chart that demonstrates it changed.

⚠️ ⚠️ **CORRECTED AGAIN 2026-10-15 — the English chart is no longer a US chart.** Ticket 19 named it `us` on the evidence
it had (NYT, PW and Indie are all US lists) and refused to call a US-list chart *global*, which was right. ⚠️ **What
changed is the sources, not the rule**: the English chart now reads the **four Amazon Books bestsellers** — `amazon.com`,
`amazon.co.uk`, `amazon.ca` and `amazon.com.au` — alongside NYT and Indie, so its rows carry `us`, `gb`, `ca` and `au`
and its market is **`worldwide`**.

⚠️ **And that move needed one more distinction, `LIVE` below.** An Amazon bestseller page carries **no date**, so
`freshness` — which treats *undated* as *stale* — refused every Amazon row and made every chart declaring one **absent**.
⚠️ That is why `comics` and `all-language` were absent, and why the English chart could not have gained an international
list under the old rule. ⚠️ A live ranking has no stale version to catch; a live vendor that answers *nothing* is still
missing, and its chart is still absent. See `LIVE`.

⚠️ See **ticket 29**, which holds the evidence, the arithmetic and the decision this table now reflects.
"""
from __future__ import annotations

import dataclasses

#: The vendor slugs. ⚠️ A vendor is a **source**, not a list — the distinction ticket 17 turns on, and the reason
#: `vendors` and `lists` are separate fields rather than one.
#: ⚠️ ⚠️ **Anandabazar's weekly Bengali list exists — and it is not declared, because every instalment the site serves is
#: an archive** (ticket 31, 2026-10-15). ⚠️ It is the *better* shape of the two: ranked **by sales** in its own words,
#: carrying **its own date**, an author, a publisher and a per-row count — so unlike `ROKOMARI` and `BOICHITRO` it would
#: need **no `LIVE` exemption**. ⚠️ But the four instalments the site serves are **2014–2015**, the live list is a
#: **scan** of the Saturday print page, and the print archive host is **down**. ⚠️ Declaring one would make the Bengali
#: chart **absent rather than smaller** — a stale list makes its vendor *missing*, and a missing vendor makes its chart
#: absent (ticket 18) — so the address waits for a *current* one. ⚠️ 403 to a plain fetcher; `curl_cffi` reads it.
ANANDABAZAR = "anandabazar"
#: ⚠️ ⚠️ **Amazon is one vendor per marketplace, not one vendor** (2026-10-15). `amazon.com` and `amazon.co.uk` are
#: different *stores* publishing different bestseller rankings, so by ticket 17's unit they are different **sources** —
#: and that is what lets the English chart rank several countries without pretending one voice speaks for all of them.
#: ⚠️ `amazon-in` is the one the product started with; the other four arrived with the English chart's move to
#: **worldwide**.
AMAZON_US = "amazon-us"
AMAZON_UK = "amazon-uk"
AMAZON_CA = "amazon-ca"
AMAZON_AU = "amazon-au"
AMAZON_IN = "amazon-in"
#: ⚠️ **The four European storefronts** (ticket 34). One currency between them, and **four vendors rather than one
#: "Europe"** — `amazon.de` and `amazon.fr` rank different countries' editions, which is the unit ticket 17 counts by.
#: ⚠️ `amazon-au` is verified and **not declared** — see the comics chart's own note.
AMAZON_DE = "amazon-de"
AMAZON_FR = "amazon-fr"
AMAZON_IT = "amazon-it"
AMAZON_ES = "amazon-es"
ROKOMARI = "rokomari"
#: ⚠️ ⚠️ **The two Bengali booksellers, and the second vendor the Bengali chart was missing** (ticket 30). They are
#: WooCommerce shops, so a bestseller ranking is a **JSON endpoint** rather than a scrape — one module reads both, as
#: `amazon.py` reads five marketplaces. See `fetch/woocommerce.py` for what the search found and refused.
#:
#: ⚠️ **`boighar` is written, tested, and deliberately not declared**: its ordering is unverifiable (its own top five is
#: 2021 magazines with one review apiece, against BoiChitro's fifty-review books) and it states **no ISBN**, so it could
#: neither corroborate nor be corroborated.
BOICHITRO = "boichitro"
BOIGHAR = "boighar"
#: ⚠️ ⚠️ **The third Bengali bookseller, and the best Indian Bengali source found** (ticket 32). Also WooCommerce, so
#: `woocommerce.py` reads it unchanged — but it is the first Bengali vendor whose titles are in **Bengali script** (all
#: 100 of them, measured) and the first whose ISBNs sit in the payload's **`sku`** rather than in an attribute (**54 of
#: 100**). ⚠️ What it does *not* state is an **author**, so its rows key as `title|` and cannot merge with an authored
#: row — the conservative direction, recorded in `identity`.
BANGABANI = "bangabani"
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
#:
#: ⚠️ **And *scraped* here means *located* rather than *named*, which is what the two booksellers share with a scrape**
#: (ticket 30). A WooCommerce shop's ranking is JSON rather than HTML, but `boichitro/bestsellers` still names nothing a
#: reader could check — the list *is* the `orderby` in its address, exactly as an Amazon list is its node id. ⚠️ So the
#: set is the vendors whose list has to be **stated**, and the constructor's refusal is what turns a store declared
#: without one into a declaration error rather than a run that silently fetches nothing.
SCRAPED: frozenset[str] = frozenset(
    {
        ANANDABAZAR,
        AMAZON_US,
        AMAZON_UK,
        AMAZON_CA,
        AMAZON_AU,
        AMAZON_IN,
        #: ⚠️ The four European stores (ticket 34). Listed for the same reason every Amazon store is: the slug names
        #: nothing, so the **address is the list's identity** and `Listing` refuses one that states none.
        AMAZON_DE,
        AMAZON_FR,
        AMAZON_IT,
        AMAZON_ES,
        ROKOMARI,
        BOICHITRO,
        BANGABANI,
        BOIGHAR,
        INDIE,
    }
)

#: ⚠️ ⚠️ **The vendors whose list is a *live ranking* rather than a compiled weekly list** (2026-10-15).
#:
#: ⚠️ **The distinction is what the freshness guard turns on, and it is a real one rather than a loophole.** A *compiled*
#: list (NYT, Indie) is a **dated artefact**: the page that describes week 41 keeps saying *week 41* next week, so
#: `freshness` can and must check the date the vendor states. ⚠️ An Amazon bestseller page is the opposite — it carries no
#: date **because there is nothing to date**. It is regenerated continuously, and a `200` response **is** the current
#: ranking; there is no stale copy for the guard to catch.
#:
#: ⚠️ **Asking a live list for a date it never states refused the source forever**, and silently: every Amazon row is
#: undated, so the vendor produced nothing usable and *every* chart declaring it went **absent**. That is why `comics` and
#: `all-language` shipped absent, and why the English chart could not have gained an international list at all.
#:
#: ⚠️ **What is *not* relaxed.** A live vendor that returns **nothing** — a block page, a failed render, a wrong address —
#: still counts as *missing* and still makes its chart absent (ticket 18's spine), because *"a degraded chart is a wrong
#: chart."* The guard keeps the half that protects the product and drops only the half that cannot apply.
LIVE: frozenset[str] = frozenset(
    {
        AMAZON_US,
        AMAZON_UK,
        AMAZON_CA,
        AMAZON_AU,
        AMAZON_IN,
        #: ⚠️ ⚠️ **And the four European stores** (ticket 34) — the same argument one locale further out: a bestseller
        #: page is regenerated continuously and states no date **because there is nothing to date**, so asking it for one
        #: discards every row and makes the chart absent. ⚠️ `LIVE` exempts from the *date* check only: a store that
        #: answers nothing is still missing, and its chart is still absent.
        AMAZON_DE,
        AMAZON_FR,
        AMAZON_IT,
        AMAZON_ES,
        # ⚠️ ⚠️ **Rokomari's list is a live ranking too, and that is what brings the Bengali chart back** (ticket 30). It
        # was refused as *undated* for as long as `LIVE` did not exist — and ticket 29 recorded the blocker as *"Rokomari
        # needs a date"*, which was the right reading of the **guard** and the wrong reading of the **source**: a
        # retailer's own bestseller category is regenerated per order, so it has no stale copy for a date to catch.
        # ⚠️ The half that still protects the product is untouched: a Rokomari that answers *nothing* is still missing.
        ROKOMARI,
        # ⚠️ **And the bookseller's Store API**, which states no date for the same reason — see `fetch/woocommerce.py`.
        BOICHITRO,
        # ⚠️ **The third bookseller, for the same reason again** (ticket 32) — `bangabani.in`'s best-seller category is
        # regenerated per order, so there is no dated artefact for the guard to check and asking it for a date would
        # refuse a source that is answering correctly. ⚠️ The half that still protects the product is untouched: a
        # Bangabani that answers *nothing* is still **missing**, and its chart is still absent.
        BANGABANI,
    }
)

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


#: ⚠️ ⚠️ **How often a vendor publishes a list — and it is a property of the *list*, not of the vendor** (2026-10-15).
#:
#: ⚠️ Ticket 22's source table called NYT's `graphic-books-and-manga` **weekly**, and the comics chart was built on that
#: reading. The recorded payload says otherwise: `"updated": "MONTHLY"`, and it dates the list to the **first Saturday of
#: the month** (`bestsellers_date: 2026-10-03`). ⚠️ A guard whose span is ten days wide therefore calls that list stale
#: for **three weeks in four**, and ticket 18's *absent-not-smaller* rule turns a stale vendor into an **absent chart** —
#: so `comics` could only ever build in the week its list happened to be dated, which is why it was missing from
#: `2026-W41` while Amazon.in answered it thirty rows.
#:
#: ⚠️ **The exemption is the smallest one that fits the fact**: a monthly list is fresh for the **month the week falls
#: in**, so a *previous* month is still stale and the guard keeps its meaning. ⚠️ It is declared **per list** rather than
#: per vendor, for the same reason `LIVE` is declared per vendor: NYT publishes weekly lists too, and exempting the
#: vendor would quietly excuse `hardcover-fiction` as well.
CADENCES: frozenset[str] = frozenset({"weekly", "monthly"})


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
    #: ⚠️ **`"weekly"` unless the vendor says otherwise** — see `CADENCES`, and the note there for the chart this field
    #: was added for. ⚠️ **Declared rather than sniffed off the payload**: the client would have to hand the vendor's own
    #: `updated` field back up through `Row`, and a list whose cadence changed would then change the freshness rule
    #: silently, mid-week. ⚠️ A declaration is a claim an operator can check against the page.
    cadence: str = "weekly"

    def __post_init__(self) -> None:
        """⚠️ **Refuse a scraped list that cannot say where it is** (ticket 29), and a cadence nobody recognises.

        ⚠️ This is the whole mechanism, and it is a refusal rather than a warning on purpose. The drift ticket 29 found
        was a table of slugs naming pages that do not exist — and every one of them **parsed, rendered and looked
        correct**. ⚠️ A list that cannot state its address is a list nobody can fetch, and learning that at *declaration*
        time is the difference between a spec that is wrong and a run that refuses.

        ⚠️ **The cadence gets the same treatment**, because it is the same shape of mistake: `"monthly"` misspelt is not
        a freshness rule that fails loudly, it is a list that quietly keeps the weekly one — the stale-for-three-weeks
        behaviour this field exists to remove.
        """
        if self.cadence not in CADENCES:
            raise ValueError(
                f"{self.slug} declares cadence {self.cadence!r} — the cadences are "
                f"{', '.join(sorted(CADENCES))}"
            )

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
        # ⚠️ **`market` is declared below, beside the note that explains why it widened back** (ticket 30) — it cannot
        # be stated twice, and the reason is longer than the field.
        language="bn",
        # ⚠️ ⚠️ **Two vendors again, and they span the two countries ticket 21 built this chart for** (ticket 30). Ticket 21
        # wanted a bridge across India and Bangladesh — Anandabazar ranking India, Rokomari the Bangladeshi side — and
        # ⚠️ **Anandabazar's weekly list could not be declared** — under ticket 29's address rule it had no address to give
        # — so the chart lost its Indian half. ⚠️ ⚠️ **It has since been *located*, and it is still not declared** (ticket
        # 31): the list is real, sales-ranked and dated, and every instalment the site serves is **2014–2015**. The
        # decision survives its own reason, which is why it is worth saying twice — see `ANANDABAZAR` above.
        #
        # ⚠️ **What found it again was a search, not a correction**, and it did not find a *paper*: it found the
        # booksellers. **BoiChitro** publishes a hundred-deep popularity ranking as JSON, with a real ISBN on some rows
        # and its own `pa_authorname` on most — so the Indian half of this chart is a **shop's** ranking rather than an
        # editor's. See `fetch/woocommerce.py` for the seven addresses fetched and the four that are not sources.
        #
        # ⚠️ **Amazon.in is still removed** (2026-10-14): it publishes **no Bengali list at all**, so the vendor could
        # only ever be a missing source — and a declared vendor that cannot answer makes the chart **absent**, which is
        # the outcome that correction was meant to *name* rather than leave implicit.
        #
        # ⚠️ **And the market widens back with the sources.** Ticket 29 narrowed it to `bangladesh` for the same reason
        # ticket 19 once refused to call a US-list chart *global* — *a chart's scope is what its lists can support* — so
        # a chart reading an Indian list and a Bangladeshi one is `india+bangladesh` again. ⚠️ The label was **kept** in
        # `copy.ts` through the narrow interval for exactly this eventuality.
        market="india+bangladesh",
        vendors=(ROKOMARI, BOICHITRO, BANGABANI),
        lists=(
            # ⚠️ **The Bangladeshi side, and the one list in the set that is not Indian.** ⚠️ It is **undated** — the
            # payload carries no date anywhere — which is why `ROKOMARI` is `LIVE`: a retailer's own bestseller category
            # is regenerated per order, so there is no stale copy for the guard to catch, and asking it for a date refused
            # the source forever. ⚠️ A Rokomari that answers *nothing* is still a **missing** vendor (ticket 18).
            Listing(
                slug="rokomari/best-sellers",
                country="bd",
                language="bn",
                address="https://www.rokomari.com/book/category/72/best-seller-books",
            ),
            # ⚠️ **The Indian side, and the address is the list** (ticket 29): `orderby=popularity` is the whole of what
            # separates this ranking from the same shop's newest-arrivals page, and `per_page=100` is what makes it deep
            # enough for a Top 100 (`rank.weight` pays a shallow list less rather than refusing it).
            #
            # ⚠️ ⚠️ **The language is empty, and that is `all-language`'s rule rather than an omission.** BoiChitro is a
            # Bengali bookshop whose bestseller list carries Bengali, English and Hindi rows side by side — its own top
            # ten holds *Strange Weather in Tokyo* beside *দেশান্তরে বাজ* — so a declared `bn` would be confidently wrong
            # on some rows, and by ticket 20's rule a *constant* label **renders**. ⚠️ Empty means *unknown*, and unknown
            # draws no label; the chart's own boundary sentence is where the scope is stated (ticket 21).
            Listing(
                slug="boichitro/bestsellers",
                country="in",
                language="",
                address="https://boichitro.in/wp-json/wc/store/v1/products?orderby=popularity&per_page=100",
            ),
            # ⚠️ ⚠️ **A second Indian vendor, and the one that makes this chart's Indian half a *pair*** (ticket 32).
            # Ticket 29 left the Bengali chart with one Indian list and no margin; ticket 30 gave it one. ⚠️ This gives
            # the chart three vendors across two countries, and its 54 real ISBNs are what let it *corroborate* rather
            # than merely add rows.
            #:
            # ⚠️ **The address carries both the category and the ordering, and both are load-bearing.** The category id
            # is opaque (`143`) and the store's own default order for it is **not** popularity — measured by comparing
            # the two id orders — so `category=143&orderby=popularity` *is* the list, exactly as ticket 29 requires.
            # ⚠️ `fetch/woocommerce.py` refuses to fetch this address without the `orderby`, because without it the same
            # URL is the shop's newest-arrivals page.
            #:
            # ⚠️ ⚠️ **`language="bn"` here, where BoiChitro declares none** — and the difference is measured rather than
            # stylistic: **all 100** of Bangabani's best-sellers carry Bengali-script titles, while BoiChitro's own top
            # ten holds *Strange Weather in Tokyo* beside *দেশান্তরে বাজ*. ⚠️ Ticket 20's rule is what makes this safe:
            # a *constant* label renders, so a `bn` that was wrong on some rows would print the wrong language on them.
            # ⚠️ The chart's own label still does not vary (Rokomari is `bn` too, and BoiChitro's empty is *unknown*
            # rather than a third value), so nothing new is drawn.
            Listing(
                slug="bangabani/best-sellers",
                country="in",
                language="bn",
                address=(
                    "https://bangabani.in/wp-json/wc/store/v1/products"
                    "?category=143&orderby=popularity&per_page=100"
                ),
            ),
        ),
    ),
    Chart(
        slug="english",
        label_key="english",
        # ⚠️ ⚠️ **`worldwide`, where ticket 19 named this chart `us`** (changed 2026-10-15). Ticket 19 was right about the
        # evidence it had — NYT and Indie are US lists, and it refused to call a US-list chart *global* — but the operator
        # has since asked for an **English chart that spans the English-speaking countries**, and the chart now reads
        # lists from the US, the UK, Canada and Australia. ⚠️ **The market follows the sources**, so it is named
        # `worldwide` for exactly the reason ticket 19 named it `us`: a chart's scope is what its lists can support.
        market="worldwide",
        language="en",
        # ⚠️ **Four Amazon marketplaces join NYT and Indie** (2026-10-15). ⚠️ They are four *vendors*, not one: each store
        # publishes its own country's ranking, which is what makes the chart span the English-speaking world rather than
        # four copies of one list. ⚠️ **And they are `LIVE`**, so `freshness` does not ask them for a date they never
        # state — see `LIVE`.
        #
        # ⚠️ **PW stays removed** (2026-10-14): it is **paywalled**, and its free pages are a 2012 archive.
        vendors=(NYT, INDIE, AMAZON_US, AMAZON_UK, AMAZON_CA, AMAZON_AU),
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
            # ⚠️ **The four Amazon Books bestsellers, one per English-speaking marketplace** (2026-10-15). Each is that
            # store's own *Books* ranking, and ⚠️ **each states its own country** — which is what turns ticket 20's country
            # label on for this chart at last: the rows are no longer all `us`, so the label now *varies* and draws.
            # ⚠️ The address is the store's books node, and it is the only place the marketplace is named; `amazon.py`
            # pairs each vendor slug with the currency its store quotes (`amazon.MARKETPLACES`).
            Listing(
                slug="amazon-us/english",
                country="us",
                language="en",
                address="https://www.amazon.com/gp/bestsellers/books/",
            ),
            Listing(
                slug="amazon-uk/english",
                country="gb",
                language="en",
                address="https://www.amazon.co.uk/gp/bestsellers/books/",
            ),
            Listing(
                slug="amazon-ca/english",
                country="ca",
                language="en",
                address="https://www.amazon.ca/gp/bestsellers/books/",
            ),
            Listing(
                slug="amazon-au/english",
                country="au",
                language="en",
                address="https://www.amazon.com.au/gp/bestsellers/books/",
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
        # ⚠️ ⚠️ **Nine lists across four regions, and the breadth is the operator's ask** (ticket 34: *"from different
        # country europe amerika uk india and create list"*). ⚠️ The chart began as NYT + Amazon.in, and **NYT's
        # graphic-books list is monthly** (`CADENCES`) — so it went *absent* for three weeks in four, which is what
        # happened to `2026-W41`: Amazon.in answered 30 rows and the chart still could not be built.
        # ⚠️ **One storefront per country, because a store is a vendor** (ticket 17): `amazon.de` and `amazon.fr` rank
        # different countries' editions, so eight Amazon stores are eight sources rather than one "worldwide" ranking.
        vendors=(NYT, AMAZON_US, AMAZON_UK, AMAZON_CA, AMAZON_DE, AMAZON_FR, AMAZON_IT, AMAZON_ES, AMAZON_IN),
        # ⚠️ **And this is the chart whose country varies** (`us`, `in`) — ticket 20's example, moved here when the
        # Bengali chart lost its Indian list (ticket 29). ⚠️ The rule is unchanged: a label draws only where it varies.
        lists=(
            # ⚠️ ⚠️ **`cadence="monthly"`, and ticket 22's table is why it has to be said out loud.** That ticket named
            # this list **weekly** — *"the one weekly ranking vendor"* — and the chart's whole design rests on the
            # reading. ⚠️ **The recorded payload contradicts it**: `"updated": "MONTHLY"`, and `bestsellers_date`
            # **2026-10-03**, the first Saturday of the month. ⚠️ Declared, the list stays in the chart for the whole
            # month it was published in; undeclared, it took the chart down with it. See `CADENCES`.
            Listing(
                slug="nyt/graphic-books-and-manga",
                country="us",
                language="en",
                cadence="monthly",
            ),
            # ⚠️ ⚠️ **The US store's own comics ranking, added 2026-10-15 — and it is the *print* node, not the Kindle
            # one.** The operator supplied `…/zgbs/digital-text/156104011`, which serves **30 ranked Kindle single
            # issues** (`DNX (2026-) #3 (of 5)`) whose ASINs are **not ISBNs** — 0 of 30 resolved — so every row would
            # key as `title|`, on titles that rotate weekly. ⚠️ `…/gp/bestsellers/books/4366/` is the same list in
            # **print**: 30 ranked cards, **22 of them real ISBN-13s** (Dog Man, Chainsaw Man, Coraline), which is what
            # ticket 05's identity rule needs. ⚠️ Both addresses were fetched; the digital one is recorded here rather
            # than declared, because a list of single issues is a *different chart* and not a bigger one.
            Listing(
                slug="amazon-us/comics",
                country="us",
                language="en",
                address="https://www.amazon.com/gp/bestsellers/books/4366/",
            ),
            # ⚠️ ⚠️ **The United Kingdom, America's second store, four European stores and India — one list each, every
            # one of them fetched before it was declared** (ticket 34). ⚠️ **The node ids are locale-specific and were
            # read off each store's own category tree**, never guessed: `.co.uk` `274081`, `.ca` `13932641`, `.de`
            # `287621`, `.fr` `301133`, `.it` `508784031`, `.es` `902516031`.
            #
            # ⚠️ **Measured on the fetch (2026-10-15)**: 30 ranked cards each, with **28 / 28 / 29 / 20 / 24 / 28** of
            # them carrying a real ISBN-13 — and the content is comics rather than a node's leftovers: *Bunny vs Monkey*
            # (UK), *Dog Man* (CA), *Gregs Tagebuch* (DE), *Lou ! Sonata* (FR), *One Piece* (IT), *Policán* (ES).
            #
            # ⚠️ ⚠️ **And the language is declared per list, because a storefront ranks its own country's editions** —
            # which is what turns ticket 20's language label on for this chart for the first time. ⚠️ The *country*
            # label already drew here (`us`, `in`); it now has six more values.
            #
            # ⚠️ **What each store costs.** Its prices are the store's own where the page states its currency —
            # `amazon.fr`, `.it` and `.es` say **`EUR`**, and `.ca`'s bare `$` is resolved by the declaration — while
            # `amazon.com`, `.co.uk` and `.de` state **`HUF`** to this viewer, so those rows arrive **without a price**
            # rather than with a wrong one. ⚠️ That asymmetry is `amazon.CURRENCIES` working, not a gap.
            Listing(
                slug="amazon-uk/comics",
                country="gb",
                language="en",
                address="https://www.amazon.co.uk/gp/bestsellers/books/274081/",
            ),
            Listing(
                slug="amazon-ca/comics",
                country="ca",
                language="en",
                address="https://www.amazon.ca/gp/bestsellers/books/13932641/",
            ),
            Listing(
                slug="amazon-de/comics",
                country="de",
                language="de",
                address="https://www.amazon.de/gp/bestsellers/books/287621/",
            ),
            Listing(
                slug="amazon-fr/comics",
                country="fr",
                language="fr",
                address="https://www.amazon.fr/gp/bestsellers/books/301133/",
            ),
            Listing(
                slug="amazon-it/comics",
                country="it",
                language="it",
                address="https://www.amazon.it/gp/bestsellers/books/508784031/",
            ),
            Listing(
                slug="amazon-es/comics",
                country="es",
                language="es",
                address="https://www.amazon.es/gp/bestsellers/books/902516031/",
            ),
            # ⚠️ ⚠️ **And `amazon-au` is verified but deliberately not declared** (ticket 34): its node is
            # `…/books/4893847051/`, 30 cards with **26 real ISBN-13s** in `AUD`, and it is one line away. ⚠️ It is
            # **not one of the four regions the operator named** — Australia is neither Europe, America, the UK nor
            # India — so declaring it would be a *choice* presented as an instruction, which is exactly what this
            # table's own history says not to do. ⚠️ Add it when someone asks for Oceania.
            # ⚠️ **The Indian half, and the address is right while the content is Amazon.in's own.** The page's own h1
            # reads *"Bestsellers in Comics & Graphic Novels"* and it returns 30 ranked cards, **26 of them real
            # ISBN-13s** — but what Amazon.in puts in that node is a mixed bag (`101 Tales: The Great Panchatantra
            # Collection`, `Pee-Ka-Boo | Pop-Up Baby Animals`). ⚠️ Recorded rather than corrected: the address is the
            # vendor's own statement of what the list is, and the alternative is a chart with no Indian half at all.
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
