# The four charts

Type: grilling
Status: resolved

## Question

The report carries **four** Top-100 charts, named by the brief as:

1. **Bengali** — a Bengali-language Top 100
2. **English** — an English-language Top 100
3. **Indian all-language** — Indian books across all languages
4. **Comics** — a Top 100 of comics

⚠️ **The relationship between the three book charts is already settled** — *all-language* is a **superset** that may
contain Bengali and English titles, and a title may appear in more than one chart (ticket 14). What remains is the
**definition of each chart**, and every gap still changes the source union (ticket 02):

- Is the **English** chart *global English* (NYT, PW, Indie Bestsellers) or **India-market English** (Amazon.in,
  Crossword, Flipkart)? These are two different charts with two different source sets.
- What are **comics** — Indian comics, translated manga, graphic novels, or all of them? And where is that data even
  published, week by week?
- Are all four **Top 100**, or does a chart have its own size?
- Which language does each chart *render* in? The host repo is bilingual, so the Bengali chart could carry Bengali
  labels while the comics chart carries English ones.

## Deliverable

One paragraph per chart: **what qualifies, what language, what market, and what "100" means.** That definition is
what the source union is then researched against — so this ticket comes before ticket 02, not after it.

## Answer

**Resolved on the evidence below, with the two genuinely editorial calls flagged.**

### The research first — it decides most of the definitions

- ✅ **A weekly Bengali chart exists.** *Anandabazar Patrika* publishes a weekly Bengali bestseller list
  (`anandabazar.com/culture/book-reviews/best-seller-bengali-books-of-this-week-…`). ⚠️ It returns **403 to a plain
  fetcher** — it needs the same `curl_cffi` impersonation the host repo already uses for BSE behind Akamai.
- ⚠️ **The best-known Indian all-language list is dead.** The *Nielsen Bestseller List (India)* — run with the
  Himalayan Writing Retreat, built on Nielsen BookScan **print** sales across Amazon, Flipkart and physical stores —
  is **"currently on a sabbatical"**. So the all-language chart has **no single authoritative source** and must be
  assembled from per-language retail categories plus regional newspaper lists.
- ✅ **Amazon.in publishes real Top 100 charts** per language and category, updated frequently, 50 per page. Its
  *Comics & Graphic Novels* Top 100 is **inherently mixed** — Marvel/DC, manga (*Attack on Titan*), and Indian comics
  (*Amar Chitra Katha*, *Tinkle*, *Chacha Chaudhary*, *Mahabharata*) all in one list.
- ✅ **NYT publishes a weekly `graphic-books-and-manga` list** through the Books API — a clean, keyed, weekly comics
  source with covers and `rank_last_week`.
- ⚠️ **HWR's own FAQ warns that Amazon's bestseller badge "can be gamed"** — a low-selling product can top a narrow
  subcategory. That is a direct input to the corroboration gate (ticket 17).

### The definitions

| # | Chart | Qualifies | Market | Size |
|---|---|---|---|---|
| 1 | **Bengali** | Bengali-language titles | India | 100 |
| 2 | **English** | English-language titles | ⚠️ **India market** *(recommended)* | 100 |
| 3 | **Indian all-language** | Every language, **incl. Bengali and English** — the superset (ticket 14) | India | 100 |
| 4 | **Comics** | ⚠️ **Comics & graphic novels as India buys them** *(recommended)* — Indian, manga and global in one chart | India | 100 |

**Render language** — the Bengali chart in Bengali; English, all-language and comics in English, with book titles in
their own script. Reuses the host repo's `copy.<lang>.json` label tables.

### ⚠️ Editorial call 1 — the English chart

Recommended: **India-market English**, *not* global. The all-language chart is the **whole Indian market** (ticket
14), and a product whose Bengali edition is Indian while its English edition is a NYT list would be incoherent — a NYT
hardcover #1 is not comparable to an Amazon.in #1. If the intent is a **global** English chart, say so: the source set
changes entirely (NYT + PW + Indie Bestsellers) and ticket 02 is re-aimed.

⚠️ **Revisited, and now in doubt.** Ticket 02's research found India-market English to be **effectively single-source**
(Amazon.in), because the Indian lists are dormant or quarterly — which cannot satisfy the brief's *"as many sources as
possible"*. This call is open again as **ticket 19**.

### ⚠️ Editorial call 2 — comics

Recommended: **what the market sells** (Amazon.in's *Comics & Graphic Novels*), which is inherently Indian + manga +
global. The alternative is a **global** comics chart (NYT `graphic-books-and-manga` + ICv2's monthly Top 50) — cleaner
to source, but containing almost no Indian comics.

### ⚠️ What this means for feasibility — carried into ticket 02

The **all-language** chart is the hardest (no authoritative list), the **Bengali** chart is a protected scrape, and the
**comics** chart is the easiest (NYT's API plus Amazon.in).

### ⚠️ Amended — the Bengali chart is no longer India-only

The brief has asked that the Bengali chart **include Bangladeshi titles**, so its market is the **Bengali-language
market across India and Bangladesh**, not the Indian market alone. That changes this ticket's own table, and it is
tracked as **ticket 20** (what the new dimensions are) with the Bangladeshi sources as **ticket 21**.

### ⚠️ Amended again — the comics chart is **worldwide**

*"top 100 comics all over world lang and country mention"*. So the comics row is **not** *"as India buys them"* either:
it is a **worldwide** chart, and the source set ticket 02 named for it is the wrong one — tracked as **ticket 22**.

⚠️ **Two of the four charts are no longer India-market**, and that is worth naming rather than absorbing: the coherence
argument this ticket used for an India-market English chart — *"a NYT hardcover #1 is not comparable to an Amazon.in
#1"* — is now much weaker, because the product is no longer uniformly Indian. See **ticket 19**.
