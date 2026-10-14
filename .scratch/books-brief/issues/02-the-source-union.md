# The source union

Type: research
Status: resolved
Blocked by: 12

## Question

The report is **multi-source**. Which sources join the union, and what does each actually cost — in licence, rate
limit, and fragility?

Candidates already surveyed:

| Source | Weekly | Gives | Caveat |
|---|---|---|---|
| NYT Books API v3 | yes, back to 2008 | `rank`, `rank_last_week`, `weeks_on_list`, `publisher`, `book_image`, `primary_isbn13`, `price`, `amazon_product_url`, `buy_links` | free key, 1,000 req/day, attribution required |
| Publishers Weekly (Circana BookScan) | yes | rank, last-week rank, weeks on list, publisher, price, pub date, **units sold** | HTML scrape, © Circana, and it is a **Top 10, not a Top 100** |
| Indie Bestsellers (ABA) | yes, ~2 days after the week closes | category lists | free to view; **reprint needs ABA permission**; no API |
| Amazon Best Sellers | yes (hourly) | a genuine ordered 100 | no API; scraping carries ToS risk |
| USA Today Best-Selling Books | weekly | ~top 150 | FAQ now paywalled (HTTP 402) — availability unconfirmed |
| Google Books API v1 | n/a | `publishedDate`, `publisher`, `authors`, hi-res `imageLinks`, `saleInfo` prices | enrichment, not a chart |

## Deliverable

The **final source set**, each with its licence/attribution line, its rate limit, and whether it is *fetched* (an
API) or *scraped*. Anything scraped must be named as scraped — that is a decision the reader of the spec is owed.

⚠️ **Four chart domains, not one** (ticket 12). The union has to feed a Bengali chart, an English chart, an Indian
all-language chart and a comics chart — so expect a **different source set per chart**. Expect this ticket to say
plainly which charts can only be scraped, and which **cannot be sourced at all**: Bengali-language and Indian
regional-language bestseller data is scarce and mostly not API-backed, and comics is a separate problem again. A
chart with no source is a *finding*, not a failure — and the honest outcome may be that only some of the four charts
are buildable.

⚠️ **The union corroborates; it does not merely accumulate.** The brief wants the chart *genuine and authentic*, with
the run checking **as many sources as possible** before the list is made — so this ticket must name sources that can
**confirm each other**, not merely five sources that happen to be convenient. A source that can corroborate another is
worth more than one that cannot. The rule that consumes this is ticket 17.

## Answer

### ⚠️ The headline finding: almost nothing Indian is *weekly*

The product is weekly. Most Indian bestseller data is not.

| Source | Cadence | Verdict |
|---|---|---|
| **Amazon.in** bestsellers (per category/language) | "updated frequently" | ✅ the workhorse |
| **Anandabazar Patrika** Bengali bestsellers | **weekly** | ✅ the only weekly Bengali chart |
| **Dainik Jagran + Nielsen BookScan** Hindi | **quarterly** (Jan–Mar, Apr–Jun, …) | ❌ wrong cadence for a weekly chart |
| **Nielsen Bestseller List (India)** (with HWR) | **on sabbatical** | ❌ dead |
| **ICv2** Top 50 Comics / Top 20 Graphic Novels | **monthly** | ❌ wrong cadence |
| **NYT Books API** | **weekly** | ✅ but US/global |

The weekly cadence and the India-market scope are therefore **in tension**, and that tension decides each chart.

### Per chart

**1 — Bengali** ✅ *sourced*
- **Anandabazar Patrika** weekly Bengali bestseller list — genuinely weekly, but ⚠️ **403 to a plain fetcher**: it needs
  the `curl_cffi` impersonation the repo already uses in `fetch/bse.py` for BSE behind Akamai.
- **Amazon.in → Bengali Books** bestsellers — Top 100, updated frequently.
- These two can **corroborate** each other (ticket 17).

**2 — English** ⚠️ *conditional — see ticket 19*
- **India-market English**: essentially **Amazon.in alone**. The authoritative-looking Indian lists are dormant
  (Nielsen/HWR sabbatical) or quarterly (Jagran). ⚠️ **One source cannot corroborate**, which collides head-on with the
  standing preference *"check as many sources as possible"*.
- **Global English**: **NYT Books API + Publishers Weekly (Circana) + Indie Bestsellers** — all weekly, all carrying
  `rank_last_week`, all free to read. Rich enough to corroborate properly.
- ⚠️ **This is new evidence against editorial call 1 in ticket 12**, and it is raised as ticket 19.

**3 — Indian all-language** ⚠️ *the weakest chart*
- No authoritative list exists. Assembled from **Amazon.in per-language bestseller categories** (Hindi, Tamil, Marathi,
  Malayalam, Telugu, Kannada, Gujarati, Bengali, English), each a Top 100.
- ⚠️ Cross-language ranks are **not comparable** as they stand: a #1 in a narrow Gujarati category is not a #1 in
  Hindi. The chart logic (ticket 03) must normalise per category, exactly as it normalises across sources.
- Corroboration is available only where a regional newspaper list exists — Anandabazar for Bengali, nothing for most.

**4 — Comics** ✅ *sourced*
- **Amazon.in → Comics & Graphic Novels** — Top 100, updated frequently, and *already* the Indian + manga + global mix
  ticket 12 settled on.
- **NYT `graphic-books-and-manga`** — weekly via the Books API, with covers and `rank_last_week`. ⚠️ A **US** list, so it
  corroborates the *global* half of the chart and not the Indian half.
- **ICv2** — ⚠️ **monthly**, so it can only be a periodic cross-check, never a weekly input.

### Fetched vs scraped — stated plainly

| Chart | Fetched (API) | Scraped |
|---|---|---|
| Bengali | — | Anandabazar (⚠️ 403, needs `curl_cffi`), Amazon.in |
| English | NYT *(if global)* | Amazon.in, PW, Indie |
| All-language | — | Amazon.in ×N languages |
| Comics | NYT `graphic-books-and-manga` | Amazon.in, ICv2 |

⚠️ **Most of this chart product is scraping**, and Amazon's bestseller list is the very one HWR warns "can be gamed".
That makes the corroboration gate (ticket 17) load-bearing rather than decorative.

### Licence and attribution

- **NYT** — free key, 1,000 req/day, **attribution required**.
- **Open Library** — courtesy link back; 100 req/IP per 5 min.
- **Amazon.in** — no API for bestsellers; scraping is contrary to its conditions of use. **Named as scraped**, as this
  ticket promised.
- **Anandabazar Patrika** — scraped news content; **named as scraped**.
- **Indie Bestsellers** — free to view; **reprint needs ABA permission**.
- **ICv2 / Circana** — © Circana; periodic cross-check only.

### ⚠️ Recorded — what the sources actually answered (2026-10-14)

This ticket named the sources and their caveats but **never their addresses**, which is what left the five parsers
blocked. Recording them turned up four things that change the plan, so they are here rather than in a commit message.

**All five roots answer 200 to `curl_cffi` impersonating Chrome.** No address needs a different trick from the one this
ticket already names for Anandabazar:

| Root | Status | Bytes |
|---|---|---|
| `amazon.in/gp/bestsellers/books/` | 200 | 457,701 |
| `anandabazar.com/` | 200 | 196,716 |
| `rokomari.com/` | 200 | 1,309,173 |
| `publishersweekly.com/` | 200 | 95,264 |
| `indiebound.org/` | 200 | 246,157 |

⚠️ **1 — Amazon.in's books nav has no language categories.** The root lists thirty subjects — *Literature & Fiction*,
*Comics & Mangas*, *Romance* — and **not one of them is Bengali, Hindi, Tamil or any other language**. So the Bengali
chart's Amazon.in source and the all-language chart's nine lists are **not at the addresses this ticket assumed**, and
finding them is un-done work. ⚠️ It also means the all-language chart — already *"the weakest chart"* — has no located
source at all.

⚠️ **2 — Amazon.in's key is an ASIN, not an ISBN.** A card carries `data-asin="9390093953"`, and that is the only
identifier on it. ⚠️ **Ticket 05's rule is that the ISBN is the key everything hangs on** — and the good news is that a
book's ASIN **is** its ISBN-10, so `enrich.isbn13` already converts it. ⚠️ The bad news is the Kindle case: an ASIN like
`B08N67G4CC` is not an ISBN at all, and `enrich.isbn13` returns `""` for it — which ticket 05 already handles as
**unresolved**, so such a row is *marked* rather than dropped. No new mechanism is needed; the existing one is exercised
for the first time.

⚠️ **3 — Everything ticket 23 needs is on the card.** The real markup carries the rank (`#1`), the title, the publisher,
the cover, the format, the price — and **`aria-label="4.5 out of 5 stars, 3,661 ratings"`**, which is ticket 23's review
signal arriving from the source rather than from a second lookup. ⚠️ So ticket 04's price is **available after all**:
the earlier reading of this ticket's own "no API; scraping carries ToS risk" line made the price look blocked, and it was
never blocked — only unlocated.

⚠️ **4 — This product would be the first here to parse HTML.** Every source the brief reads is a JSON API, so no HTML
parser is in the environment at all. `selectolax` is now a dependency of `books-brief` alone, and ⚠️ **its `parser`
backend is deprecated in 1.0** — the import is `selectolax.lexbor.LexborHTMLParser`, which is the kind of detail that
costs an afternoon if it is discovered by a failing test rather than read off the deprecation.

**The first fixture is committed**: `tests/fixtures/amazon-in-comics.html`, a **verbatim** extract of the Comics &
Mangas list — the first three of its thirty cards, unaltered, with the page's other twenty-seven removed because a whole
scraped page is Amazon's content rather than ours. ⚠️ Verbatim matters: this ticket's own warning is that a fixture
built from rendered text *"would pass its test and fail on the real page."*

### ⚠️ ⚠️ And the all-language chart's source is **one list, not nine**

This ticket says the Indian all-language chart is *"assembled from **Amazon.in per-language bestseller categories**
(Hindi, Tamil, Marathi, Malayalam, Telugu, Kannada, Gujarati, Bengali, English), each a Top 100."* ⚠️ **That is not what
Amazon.in publishes.** The books nav's thirty-four subjects contain **no language at all**, and searching turns up a
different shape entirely:

```
https://www.amazon.in/gp/bestsellers/books/86946561031/     ← "Books in Indian Languages"
  200 · 442,322 bytes · <title>… in undefined</title>       ← Amazon has no display name for it
  30 cards, parsed with `fetch/amazon.py`:
    #1   ₹100  Shri Durgasaptashati Sachitra | Gita Press, Gorakhpur | श्री दुर…
    #2   ₹208  The Psychology of Money (Tamil)
    #3   ₹169  Jaun Elia: Ek Ajab Ghazab Shayar
    #4   ₹200  I Declare - Hindi ( विजय में चलने के लिए रोज़ की घोषणाएँ)
    #5   ₹149  धन संपत्ति का मनोविज्ञान | Dhan Sampatti Ka Manovigyan | The Psy…
    #7   ₹450  Chitramaya Shri Durga Saptashati | Gita Press, Gorakhpur
    #10  ₹277  Atomic Habits: Chote Badlav, Asadharan Parinaam (Hindi)
    #11  ₹220  Ayodhya Cherina Krishna - Telugu Novel
```

⚠️ **It is a single mixed-language ranking** — Hindi, Tamil, Telugu and Urdu books ranked against each other in one list.
There is no per-language node behind it: the node's own nav renders nothing, and the per-language addresses that do exist
are `…/s?rh=n%3A86946561031%2Cp_n_feature_three_browse-bin%3A…` — **search results with a bestseller sort**, which is a
different object from a bestseller list and would be named as something else if it were used.

**Two consequences, and the second is the serious one.**

✅ **The good one.** This ticket's own objection — *"cross-language ranks are **not comparable** as they stand: a #1 in a
narrow Gujarati category is not a #1 in Hindi"* — **is answered by Amazon itself.** This list has already made that
comparison, so ticket 03's per-category normalisation has less to do for this chart than this ticket expected.

⚠️ **The bad one, and it is a defect in what is already built.** Ticket 20 puts a **language label** on each row, and the
parser reads it from `charts.Listing.language`. ⚠️ That is correct for a per-language list and **wrong for this one**:
every row of a mixed list would carry the *same* language, so the label would be confidently wrong on most of a hundred
rows — and by ticket 20's own rule a constant label **renders**, because the chart would appear to vary only if the
values differed. ⚠️ So this is not a missing label; it is a **wrong** one, which is the worse failure.

**What this leaves open**, and it is a decision rather than a lookup:

1. Whether the all-language chart ranks this one mixed list, and therefore **cannot ever satisfy ticket 17's two-vendor
   gate** — which is what `charts.py` already says about it, and which would make the chart *permanently absent* rather
   than merely weak (ticket 19's exact argument for flipping the English chart).
2. Or whether it uses the per-language **search** addresses, accepting that a search result is not a bestseller list.
3. And either way, **where a row's language comes from** when the list does not state one — because `Listing.language` is
   the only answer the code has, and here it is not an answer at all.

### ⚠️ ⚠️ And there is **no Amazon.in Bengali list at all**

This ticket's Bengali row says *"**Amazon.in → Bengali Books** bestsellers — Top 100, updated frequently."* ⚠️ **That list
does not exist**, and the check is decisive rather than a matter of not having found it:

```
https://www.amazon.in/s?rh=n%3A86946561031%2Cp_n_feature_three_browse-bin%3A9495760031
  200 · 968,501 bytes · 51 `data-asin` (most of them empty)

  #gridItemRoot           0 nodes      ← a bestseller card
  span.zg-bdg-text        0 nodes      ← the rank badge
  div.s-result-item      29 nodes      ← search markup
  "Best Seller"           3            ← a badge saying *that* it is one, not *what rank* it is
```

⚠️ **A search result is not a ranking.** The books nav has no language category, the Indian-languages node has no
language children, and the only per-language address that exists is a **relevance-ordered search** whose cards carry no
rank at all. So *"Amazon.in → Bengali Books bestsellers"* is not a list this product can fetch — it is a list this ticket
**assumed** Amazon publishes.

✅ **And the machinery already answers correctly.** `fetch/amazon.py` finds no `gridItemRoot` cards in a search page and
returns **zero rows**, and `freshness.guard` treats a vendor that produced nothing as **missing** — so the chart goes
**absent** (ticket 18) rather than being built from an unordered page. ⚠️ That is the right outcome, and it is worth
noting that it required no new code: the guard written for *staleness* is what catches *this*.

⚠️ **What it leaves for the Bengali chart**, whose three declared vendors are now:

| Vendor | Status |
|---|---|
| **Anandabazar** | ⚠️ the only genuinely weekly Bengali list, and `/bestseller` **404s** — the address is unknown |
| **Amazon.in** | ⚠️ **no list exists** — see above |
| **Rokomari** | ⚠️ the Bangladeshi bridge (ticket 21), and `/book/bestsellers` **404s** — the address is unknown |

So the chart that the whole product is named after has **one plausible source, unlocated** — and ticket 17 needs **two
vendors** for any title to be admitted. ⚠️ That is the same shape as ticket 19's finding about India-market English, and
it deserves the same treatment: **stated plainly rather than worked around**.

**One address did turn up**: `indiebound.org/indie-bestsellers` answers **200** (360,910 bytes), so the English chart's
third vendor has a list page. PW's and Anandabazar's and Rokomari's list pages remain unfound.

### ✅ And then the English chart's two were found — by reading the sites, not by guessing

⚠️ Both were in the **roots already recorded**, so this cost no requests: a hub page links its own lists, and an address a
site publishes is one it intends to be read. ⚠️ Guessing is what hung the first recording run, and it is what produced the
three declaration drifts below.

| | |
|---|---|
| **Publishers Weekly** | `publishersweekly.com/pw/bestsellers/index.html` → a **hub** (41 KB, 2 ranked nodes) linking the real lists |
| ↳ its lists | `/pw/bestsellers/hardcover-fiction.html` · `hardcover-nonfiction.html` · `trade-paper.html` · `graphic-novels.html` · `mass-market-paper.html` · `audio-fiction.html` · … |
| ↳ and | `/pw/nielsen/top100.html` — ⚠️ a **Top 100**, which is the shape this product ranks |
| **Indie Bestsellers** | `indiebound.org/indie-bestsellers` → a **real list** (361 KB, **79 ranked nodes**) |

### ⚠️ ⚠️ Three declarations now name lists the vendors do not publish

This is the pattern rather than three separate mistakes, and it is worth stating plainly:

| Chart | Declared | What the vendor publishes |
|---|---|---|
| **All-language** | `amazon-in/hindi`, `…/bengali`, `…/tamil` ×9 | ⚠️ **one** mixed list, `…/books/86946561031/` |
| **Bengali** | `amazon-in/bengali` | ⚠️ **no list exists** — only an unordered search |
| **English** | `pw/fiction`, `pw/nonfiction` | ⚠️ `pw/bestsellers/hardcover-fiction.html`, `hardcover-nonfiction.html` |

⚠️ **Every one of these was written from assumption rather than from a fetched page** — which is exactly what this
ticket's own table did, and why it says *"expect this ticket to say plainly which charts can only be scraped"* without
ever saying **where**. ⚠️ The remedy is the same in all three cases and it is not a code change: **read the site, then
write the declaration**. `charts.Listing` already cannot be declared without a country and a language; ⚠️ the next step is
the same discipline for the **address**, which is the one field a scraped list's identity actually is.

⚠️ **None of these drifts fails silently today**, which is the one piece of good news: a declared list with no address is
refused by `amazon.fetch` (`MissingNodeError`) or produces no rows, and either way the vendor is **missing** and the chart
is **absent** (ticket 18). The failure is a chart that does not ship, not a chart that ships wrong.




