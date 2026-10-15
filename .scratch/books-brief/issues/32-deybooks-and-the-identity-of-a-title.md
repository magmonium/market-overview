# Dey's best-seller collection, and what "a title" means

Type: grilling
Status: resolved

⚠️ **Resolved in two halves, and the second was the bigger one.** **C** — the chart's identity is now the **work**, not the
ISBN — is implemented, verified against the week's own recorded responses, and the committed week has been migrated.
**A** — the source half — **Bangabani was declared** rather than Dey's, because it needs no new client and states 54 real
ISBNs where Dey's states none. ⚠️ Dey's and Sahojpath are **evaluated and not declared**, with the reason recorded below.

## Question

The operator supplied `https://deybooks.com/collections/best-seller` for the Bengali chart. It is the strongest Indian
Bengali candidate found so far — and declaring it raises a question the product has never actually answered: **is a chart
of "Top 100 books" a hundred *products* or a hundred *works*?**

## What the fetch says — all verified 2026-10-15, one request per address

- ✅ **Shopify, and machine-readable**: `…/collections/best-seller/products.json?limit=250` answers **200 JSON** with
  **56 products** — no key, no scrape, no auth, no browser.
- ✅ ✅ **The collection is sorted `best-selling`** — `value="best-selling" selected="selected"` in *both* the desktop and
  the mobile sort selects, and `/collections/best-seller.json` reports `products_count: 56`. ⚠️ So the JSON's order **is** a
  sales ranking rather than a merchandising one — and that is exactly the property `boighar` was refused for lacking
  (*"its ordering is unverifiable"*).
- ✅ **India, INR, Kolkata** (`/meta.json`); **covers on 56 of 56**; prices present (`300.00`).
- ✅ **A shop's ranking, not a publisher's own list** — 12 publishers appear (Ananda 38, Mitra & Ghosh 5, Kakoli 3,
  Bishwabani 2, then one each). ⚠️ But **68% of it is one publisher**, which is worth stating before the chart is built
  on it.
- ✅ **Permissive policy**: robots.txt declares public product and collection JSON crawlable, and the store publishes
  `/agents.md` *inviting* agent access — the opposite of Anandabazar's blocklist.
- ⚠️ **No ISBN anywhere**: `variants[].sku` is null, `barcode` is null, and no ISBN-shaped string appears in any
  `body_html` or `tags`.
- ⚠️ **No date** → it would be `LIVE`, like the other two Bengali vendors.
- ⚠️ The top best-seller's variant reports `available: false` — an out-of-stock #1.

## ⚠️ The defect: with no ISBN, its rows can never merge with anyone's

`corroborate.admit` keys the union **by ISBN**:

```python
by_isbn.setdefault(row.isbn, []).append(row)
```

A vendor with no ISBN gets a **vendor-prefixed synthetic key** instead — `rokomari:890`, `boichitro:Falcon
Books(New Delhi)10657` — which `fetch/woocommerce.py::_key` documents as *"the store's own id last — prefixed, as
`rokomari`'s is, because a bare `5826` is a number that could collide with any other store's numbering."* ⚠️ **That prefix
is what stops a collision — and it is also what guarantees that two vendors can never agree about the same book.**

⚠️ **Measured, not argued**: **5 of Dey's 56 titles are already on the shipped Bengali chart.**

| Dey's title | already on the chart as |
|---|---|
| `Galpa 101` | Galpa 101 |
| `Shanku Samagra` | Shanku Samagra |
| `TENIDA SAMAGRA` | Tenida Samagra |
| `COMPASS` | Compass |
| `Byomkesh Samagra` | Byomkesh Samagra |

⚠️ So declaring `deybooks` today would put **those five books on the chart twice** — and unlike a corroborated title, the
two rows could never be merged, because neither key is an ISBN.

## ⚠️ And the same phenomenon is *already* shipping — this is not a Dey's defect

| Chart | Rows | Distinct titles | The repeats |
|---|---|---|---|
| `bengali` | 100 | **98** | **`Chandmama` three times** (ranks 92, 95, 96) — all BoiChitro, three product ids |
| `english` | 100 | **92** | **8 repeats**, e.g. `Protocols: An Operating Manual for the Human` at ranks 2 and 33 with **different real ISBNs** (9781668032145, 9781529921298) |
| `all-language` | 30 | 30 | none |

⚠️ The English chart's repeats are **different editions of one work**, which is ticket 14's rule working exactly as
written (`chart + ISBN`): two ISBNs are two products, so they are two rows. ⚠️ **Dey's is simply the case where the two
spellings of a work are the same title text** — and where the identity is synthetic, so nothing can ever join them up.

### ⚠️ C, measured — and the measurement changes what C buys

Before writing any of it, the work key was **measured against the two things it has to fix**. Two findings, and the
second one is the reason this section exists.

**1. A work key fixes the *edition* duplicates — which are the ones the chart is currently wrong about.**

| Chart | Rows | Work keys | Groups collapsing |
|---|---|---|---|
| `english` | 100 | **92** | **8 pairs** — `Protocols`, `A Court of Splintered Harmony`, `A Court of Forgotten Melody`, `Theo of Golden: A Novel` … |
| `bengali` | 100 | **98** | **1 group of 3** — `Chandmama` |
| `all-language` | 30 | 30 | none |

⚠️ And the eight English pairs are **different editions of one work with two real ISBNs** — so today's chart ranks one
book twice, and under a work key those rows **merge into one row carried by two lists**. That is the first time ticket
17's corroboration would be *visible* on a chart: `sources` would hold two lists instead of one.

**2. ⚠️ ⚠️ And it does *not* fix Dey's, because two vendors transliterate the same author two ways.**

Dey's states its author **in the blurb** (`body_html` → `Author : … Publisher : …`), extractable on **53 of 56** products.
But where the work key was expected to merge Dey's five overlapping titles, it merges **three**:

| Title | The chart's author | Dey's author | merges? |
|---|---|---|---|
| `Shanku Samagra` | Satyajit Ray | Satyajit Ray | ✅ |
| `Tenida Samagra` | Narayan Gangopadhyay | Narayan Gangopadhyay | ✅ |
| `Compass` | Smaranjit Chakraborty | Smaranjit Chakraborty | ✅ |
| **`Byomkesh Samagra`** | Sharadindu **Bandyopadhyay** | Saradindu **Bandopadhyay** | ❌ |
| **`Galpa 101`** | Satyajit **Ray** | Satyajit **Roy** | ❌ |

⚠️ Both pairs are the **same person** — শরদিন্দু বন্দ্যোপাধ্যায় and সত্যজিৎ রায় — spelled two ways by two shops. ⚠️ So a
work key of `title + author` merges **3 of 5**, and matching on **title alone** would merge **5 of 5** — but title-only
matching is *"a single fuzzy title search"*, which ticket 05 §3 refuses in as many words.

### The design C needs — and the two decisions it forces

**The rule.** `identity.work(title, author)` — normalised (casefolded, punctuation stripped, Bengali preserved), exact,
with the author included. ⚠️ **Exact, not fuzzy**: an under-merge is a duplicate, an over-merge is a *wrong chart*, and
only one of those is recoverable.

**Decision 1 — how to resolve the transliteration variants.** Two candidates:

| | Mechanism | Precedent |
|---|---|---|
| **(i) an author-spelling table** | a small, recorded mapping (`saradindubandopadhyay → sharindubandyopadhyay`) applied before normalisation, each entry justified by two vendors' measured spellings | ✅ **exactly `genre.py`'s pattern** — *"the vendors disagree about category names, and a runtime guess would not be replayable"* — and it merges 5 of 5 |
| **(ii) match on the title alone** | no table; a title match is a work match | ❌ contradicts ticket 05 §3, and risks merging two different books that share a title |

**Decision 2 — where the key lives.** ⚠️ `Book.isbn` is currently both the chart's identity **and** the cover cache's
filename (`covers.path_for(isbn)`, and the renderer's `coverUrl(book.isbn)`).

| | Mechanism | Cost |
|---|---|---|
| **(a) a separate `key` field** | `Book.key` = the work key (identity, the Δ, the window); `Book.isbn` stays the identifier the cover is named by | ⚠️ a new field in the bundle, and the two committed weeks need `key` added **derived from their own recorded title + author** — no re-fetch |
| **(b) the work key goes into `isbn`** | one field, as today | ⚠️ re-keys every *unresolved* row (`boichitro:…` → the work key), which invalidates ~68 cached Bengali covers **and** breaks the Δ against W41/W42 unless those snapshots are rewritten |

### ✅ C implemented — and the week's own responses caught a defect in the first version

**The rule shipped is the union of two relations**, because one was not enough:

| Relation | What it merges | What it cannot |
|---|---|---|
| **the work key** — `title + author`, normalised | the **editions** of one book | rows whose titles are spelled differently, or whose author is stated by one vendor and not another |
| **a shared real ISBN** | rows two lists disagree about the *title* of | two editions of one work — different ISBNs |

⚠️ ⚠️ **The first version had only the work key, and it was a regression.** Measured on 2026-W41's own recorded
responses (285 English rows): the work key alone produced **246 groups where the ISBN alone produced 223** — it **split
30** ISBN groups in order to merge 11. ⚠️ The examples are exactly the shape one key cannot handle — one book listed
twice under two titles:

```
9781464249648: ['thewitchdeluxeedition|', 'thewitch|freidamcfadden']
9780063577541: ['partitaanovel|', 'partita|', 'partita|barbarakingsolver']
```

⚠️ **And the union is measurably the best of the three**, through `admit` itself:

| Rule | English rows | Bengali rows |
|---|---|---|
| ISBN alone (ticket 14) | 223 | 160 |
| work key alone (C, first draft) | 246 ⚠️ | 158 |
| **their union (shipped)** | **214** ✅ | **158** ✅ |

⚠️ **59 English rows are now carried by more than one list** — ticket 17's corroboration becoming visible for the first
time, because a title on two stores' lists is one row with two sources rather than two rows with one each.

⚠️ **Three things this cost, all recorded rather than smoothed over**: `isbn13` moved from `enrich` to `identity`
(the gate needs it and cannot import `enrich` without a cycle; `enrich.isbn13` is a re-export, not a copy); the group's
key is taken from the **sorted-first row**, the module's existing rule for every other field, because a group merged by
ISBN has several work keys and must pick one; and the spelling table's first draft pointed at a canonical spelling **no
vendor uses** — `tests/test_identity.py` caught it on the first run.

⚠️ **331 tests pass, 63 subtests** (16 new), and the JS suite and `tsc --noEmit` are clean.

### ⚠️ Bangabani — the third link, and the strongest Indian Bengali candidate so far

`https://bangabani.in/product-category/best-seller/` → **WooCommerce**, term `143`, and the Store API answers:

| | |
|---|---|
| **The list** | `…/wp-json/wc/store/v1/products?category=143&orderby=popularity&per_page=100` → **100 products** |
| ⚠️ **The ranking is the `orderby`** | the category's **default** order is *not* popularity (measured: different ids), so ticket 29's rule holds — the address *is* the list |
| ✅ **ISBNs** | **54 of 100** carry a real ISBN-13 — in **`sku`**, which `fetch/woocommerce.py`'s `_key` already tries after `pa_isbn` |
| ✅ **Script** | titles are **Bengali** (`পাতাঝরার মরশুমে`) where every other Bengali vendor's are romanised |
| ✅ | INR, `₹`, sale prices, covers, and a permissive robots.txt (only admin, logs and transients disallowed) |
| ⚠️ | **no author anywhere** (`attributes` empty, blurbs carry no byline) → its rows key as `title|` and cannot merge with an authored row |
| ⚠️ | undated → `LIVE`, like the other two |

⚠️ ⚠️ **And it is the source that shows the work key's own blind spot.** Measured against the shipped Bengali chart:
**0 of its 100 titles match any chart title** — the chart's are romanised and its are Bengali script, and only 7 of the
chart's 100 rows contain Bengali script at all. **2 rows share a real ISBN** with the chart. ⚠️ So a title-based key can
never join the two scripts; **only the ISBN relation can**, which is the second argument for the union above.

### ⚠️ Sahojpath — a real ordering, and the wrong shape of source

`https://sahojpath.com/products` → **a hand-built Laravel shop**, not Shopify and not WooCommerce (`/products.json`,
`/collections.json`, `/meta.json` and `/wp-json/wc/store/…` all 404; `/api/products` 404s with a *Laravel* JSON error).

| | |
|---|---|
| ✅ **A ranking exists** | the `sort_by` select's **first option is `best_seller`** — *"Best Seller"* — and the default is `latest`. ⚠️ So, as with Bangabani, **the address is the ordering**: `/products?sort_by=best_seller` |
| ✅ Verified | the two orderings **differ** (measured), prices are **INR** (`₹163 … ₹250`), and the product cards are in the HTML |
| ✅ Depth | ~140 product links over **10 pages** |
| ⚠️ ⚠️ **No API** | so this needs a **new HTML scrape client** — the fragile kind ADR 0002 insists be built from a *recording*, unlike the two JSON shops above |
| ⚠️ **The ordering's basis is unverifiable** | the label says *Best Seller*; whether that is sales, a manual flag or a counter is not knowable from outside — and ticket 21's bar for a retailer was *"a retailer ranking its own sales"*, which this cannot be shown to be |
| ⚠️ The nav is broken | *Bestsellers*, *New Arrivals* and *Top Publishers* **all point at `/track-order`** — so the menu cannot be trusted for an address |
| ⚠️ **Cloudflare, and it rejects Chrome** | every `impersonate="chrome*"` gets the *"Just a moment…"* challenge (**403**, and it is the same page for `robots.txt`); `impersonate="safari"` and `firefox133` get **200**. ⚠️ Every other client in this product asks as Chrome, so this shop would be the first that needs a different fingerprint — a per-vendor fetch detail, and one worth naming rather than discovering at 2 a.m. |

⚠️ **Verdict: usable in principle, weakest of the three.** It needs a new client *and* an unverifiable ordering, where
Bangabani needs neither and carries 54 real ISBNs.

### ⚠️ BoiChitro's `weekly-best-seller` tag — the name promises a cadence the payload does not have

`https://boichitro.in/product-tag/weekly-best-seller/` → the **already-declared** vendor, so this one was cheap to check,
and it is the fifth link of the session and the **first that claimed the one thing this chart lacks**.

| | |
|---|---|
| ✅ It exists and parses | tag `51792`, slug `weekly-best-seller`, name `#Weekly Best Seller` |
| ⚠️ ⚠️ **Six products** | `count=6` in the Store API and **6** cards on the page — a tag, not a chart. ⚠️ `rank.weight` pays a list by its **depth**: six rows is **0.06** of one position |
| ⚠️ **No new voice** | it is `boichitro`, which the chart already declares — and ticket 17 counts **vendors**, not lists, so a second list from the same shop cannot corroborate anything |
| ⚠️ ⚠️ **Undated, and this was checked rather than assumed** | the only two dates on the page are `WhatsApp-Image-2023-12-26-at-6.51.45-PM.jpeg` and `WhatsApp-Image-2026-01-25-at-23.41.30.webp` — **phone-camera timestamps inside cover filenames**, not a publication date. ⚠️ No `datePublished`, no `Week N`, and the Store API's product shape omits dates entirely |
| ⚠️ **Its membership is editorial** | a hand-applied tag (the page shows `-20% OFF` merchandising), so the *set* is the shop's choice even though its order under `orderby=popularity` is a real popularity order |

⚠️ **Verdict: refused.** Six rows, from a vendor already counted, weighted at 0.06, with no date — and the last of those
is the reason it was worth fetching at all.

⚠️ ⚠️ **And the lesson is the session's second instance of one pattern.** This page is called *weekly* and nothing in it is
weekly; ticket 31's operator link was called *"of this week"* and was dated **2015**. ⚠️ **Two of the five links were named
for a cadence they do not have** — so *"the slug is not the list"* (ticket 29) has a sibling: **the name is not the
cadence**, and only the payload can say.

⚠️ **What this leaves open, stated plainly**: the Bengali chart's three vendors are all `LIVE` **because none of them
states a date**. A dated Bengali list is the one thing this chart still lacks — the guard would rather check a date than
exempt a vendor — and this tag was the most promising candidate for it. It is not it.

### ⚠️ Where this leaves the Bengali chart — five links, and one of them is now on it

| Link | Verdict |
|---|---|
| **Anandabazar** | ✅ real list, ❌ **an archive** (2014–2015, ticket 31) |
| **Dey's** | ✅ Shopify JSON, `best-selling` verified, 56 rows, ❌ **no ISBN** |
| **Bangabani** | ✅ ✅ **declared** — WooCommerce, the client already existed, 100 rows, 54 real ISBNs, Bengali script |
| **Sahojpath** | ✅ a `best_seller` ordering, ❌ **no API**, ordering's basis unverifiable |
| **BoiChitro's `weekly-best-seller` tag** | ✅ real, ❌ **6 rows, the same vendor, undated** |

⚠️ **And the Bengali chart still declares exactly the two vendors it did before this session** — `rokomari` and
`boichitro` — because every candidate above needs a *decision*, not more evaluation. ⚠️ **Bangabani is the one to
declare**: it is the only candidate that adds depth, real ISBNs and Indian coverage without new fetch code.

### ✅ What shipped — the declaration, and the migration

**1. Bangabani is declared** (`charts.py`, `cli.py`, `fetch/woocommerce.py`): a vendor slug, a member of `SCRAPED` and
`LIVE`, one `Listing` on `bengali` — `in`, `language="bn"` (measured: **all 100** titles are Bengali script), address
`…/wc/store/v1/products?category=143&orderby=popularity&per_page=100` — and one line in `CLIENTS`, because the module
already read two shops. ⚠️ `bengali` now declares **three vendors across two countries**, which is the margin ticket 29
left it without.

**2. ⚠️ And a guard came with it.** `woocommerce.fetch` now **refuses an address that does not carry
`orderby=popularity`**. ⚠️ The reason is specific: with a second store declared, the existing test that checked the
declaration only ever looked at *BoiChitro's* address — and an address that lost that parameter is the same shop's
**newest-arrivals page**, which would rank the whole chart by recency and look entirely correct while doing it. ⚠️ The
dead constant became a live refusal, and its error names the missing parameter.

**3. The migration ran, and it touched one field.** W41's **230 rows** gained `key`, recomputed from the `title` and
`author` already in the snapshot and written through `store.write_facts` — the same serialiser a gather uses. ⚠️ **No
re-fetch and no other field changed**; the 7,479-line diff against `HEAD` is the *pre-existing* uncommitted re-gather, and
the migration's own contribution is exactly the 230 added lines. ⚠️ **W42 holds raw responses but no snapshot**, so there
was nothing to migrate there.

⚠️ **Two things the migration deliberately did not do**, both stated rather than implied:

- ⚠️ **It did not merge the committed week's duplicate rows.** Rewriting a published week's ranks is a different decision
  from adding the field the *next* week needs — and the chart that shipped is the chart that shipped.
- ⚠️ **It could not re-key the committed weeks' watchlists.** They hold ISBNs (that is what `rank.chart` appended then),
  and a watchlisted title is *not* in `ranked`, so the snapshot carries no title to recompute from. ⚠️ The watchlist is
  informational — the Δ and the window read `ranked` — so this is a stale label in an old week, not a wrong chart.

**4. Verified after the migration**, on the committed store: all 230 rows keyed; `delta.ranks` returns **work keys**;
`window.observe` sees **98** Bengali titles from 100 rows (the `Chandmama` triple merged, exactly as predicted); and the
chart reads `('rokomari', 'boichitro', 'bangabani')` with `bangabani/best-sellers` at `in`/`bn`.

⚠️ ⚠️ **Two consequences a reader is owed**: the migrated `facts.json` no longer matches the `bundle_hash` recorded in
W41's package, so a re-render would produce a different hash than the delivered video's metadata claims; and **the next
gather is what puts Bangabani's rows on a chart** — at the last check Google Books' daily quota was spent, so a gather now
would fetch the three shops and enrich less.





| | What it means | Cost |
|---|---|---|
| **A. Declare `deybooks`** | a Shopify client, `deybooks/best-sellers` on `bengali`, `LIVE`, address `…/collections/best-seller/products.json?limit=250` | ⚠️ ships **5 known duplicates** on the Bengali chart, and adds a third vendor whose rows can never corroborate |
| **B. Record and do not declare** | the `boighar` shape: written, tested, undeclared, with the reason beside it | ⚠️ loses a **verified sales-ordered** Indian Bengali ranking, which is the best Indian candidate found in two searches |
| **C. Answer the identity question first** | dedupe by **work** (normalised title + author) rather than by ISBN — a chart-logic change (tickets 03, 14) | ⚠️ affects **all four** charts, and would also collapse the English chart's 8 repeats — so it is a product decision, not a vendor one |

⚠️ **The recommendation is C, then A** — because B throws away a source that clears the one bar `boighar` failed
(*"its ordering is unverifiable"*), and A knowingly ships five duplicates onto a chart whose whole claim is that it is
correct. ⚠️ C is the decision the product has been deferring since ticket 14, and Dey's is the source that makes it
visible rather than theoretical.

⚠️ **One thing this ticket does *not* question**: that Dey's rows are *usable*. Under ticket 17 as reversed, the chart
ranks the **union**, so a no-ISBN vendor is admitted and scored on its own position and depth — it raises a chart's
*depth* rather than its *certainty*, and that distinction should be stated wherever the vendor is declared.

## The evidence

Fetched 2026-10-15 with `curl_cffi` impersonating Chrome, one request per address: `/collections/best-seller` (HTML),
`/collections/best-seller/products.json?limit=250`, `/collections/best-seller.json`, `/meta.json`, `robots.txt` and
`/agents.md`; and measured against the committed snapshot `store/2026-W41/facts.json` (three charts, 230 ranked rows) for
the duplicate and overlap counts.


### ✅ And the duplicates are gone from the committed week too

⚠️ The first migration deliberately left them; the operator asked for them removed, so a **second migration** ran — with
the same rule, from the same function: `corroborate.group`, extracted from the gate precisely so a migration cannot
re-implement the rule and drift from it.

| Chart | Before | After | Removed |
|---|---|---|---|
| `english` | 100 | **92** | 8 — the edition pairs |
| `bengali` | 100 | **98** | 2 — `Chandmama`, three rows into one |
| `all-language` | 30 | 30 | none |

✅ **Verified**: no repeated titles in any chart, ranks dense `1..N`, keys unique, `cover_coverage` recomputed, and
`meta.chart_logic` moved **1 → 2** — the stamp exists for exactly this, and a snapshot still claiming `1` would tell a
later reader its rows are ISBN-keyed when they are not.

⚠️ ⚠️ **Two traps the merge caught, and both were mine.**

**1. The chart's order is not `score`.** The first version re-sorted by `score` descending, and the result was visibly
wrong: `Chandmama` has a high position score (**0.97**) and a thin review signal, so it leapt from **rank 92 to rank 4**.
⚠️ The order is `rank.final_score` — the sales term **plus the review term**, times incumbency — and `score` is only its
first component. ⚠️ **Preserving the recorded order is not a shortcut, it is exact**: a merged row inherits the
best-ranked row's `score`, `rating`, `ratings_count` and `weeks_on_chart`, so its `final_score` *is* that row's, and the
only work left is closing the gaps. `Protocols` stayed at **2**, `Chandmama` at **92**.

**2. ⚠️ ⚠️ A work's score counts its best position *per list*, and the first version summed every listing.** That put
`Chandmama` at **rank 1** with a score of **2.7** — the sum of three rows that are all `boichitro/bestsellers`. ⚠️ That is
one shop's duplicate listings counted as three corroborating voices, which is the *"lie told in arithmetic"* ticket 17
forbids and which `corroborate`'s own docstring quotes. ✅ **Fixed in `cli._weekly`** — a work contributes at most one term
per list, at its best position in it — and pinned by a test; ✅ `Title.sources` is deduplicated for the same reason.

⚠️ **The migration itself could not use the corrected sum**, and that is a limitation of the record rather than a
preference: a snapshot row carries **no list** (the bundle has no `sources` field), so a sum cannot tell *"the same book on
two shops"* from *"one shop listing it twice"*. ⚠️ It therefore keeps the **best row's** score — the conservative
direction, because under-counting only ranks a row lower while over-counting makes a false claim of corroboration. ⚠️ The
next gather computes the true sum, because there the lists are known.

**What is on disk now.** The week was re-rendered by replaying the merged snapshot — `build` **replays** a recorded week
rather than re-fetching it, which is what made this possible with Google Books' quota spent:

- ✅ **`bengali`**: video, thumbnail and **package** all written, and its description now lists `Chandmama` **once, at
  92** — 4,801 characters, inside the limit.
- ✅ **`all-language`**: re-rendered and packaged; its rows are unchanged and its timeline re-laid for the row count.
- ⚠️ **`english`**: re-rendered, **but it cannot be packaged** — its description is **7,677** characters against YouTube's
  5,000. ⚠️ ⚠️ **Measured, and it is not this change**: the same description was **8,321** characters *before* the merge,
  so the limit was already blown by the English chart's own content after the worldwide re-gather — the merge *reduced*
  it by 644. ⚠️ `metadata.description_for` refuses rather than truncating (*"a list that will not fit is a list to
  shorten, not one to ship and hope nobody reads the end of"*), so `english` is **built but not publishable**, and its
  folder carries **no manifest** — which is why `publish` will refuse it rather than upload a half-described video.



### ✅ And the new data is finally on a chart — the gather

⚠️ **The declaration alone changed nothing on a chart**, which is what *"new data has not been updated"* was reporting:
`bangabani` was declared and **no run had ever fetched it**. ⚠️ `build` **replays** a recorded week rather than
re-fetching it (ADR 0003), so the only way to gather was to move the snapshot aside first — done, with **two backups**
kept (`/tmp/w41-merged-snapshot.json`, `/tmp/w41-before-regather.json`).

⚠️ **The one trade-off was checked before spending it, and it cost nothing.** Google Books still answers
`429 … Queries per day`, so a gather re-enriches less — ⚠️ **except the committed snapshot was *already* in that state**:
measured across all 220 rows, **0 have a publication date** and **every single genre is `other`**, which are exactly the
fields Google supplies. The gather's own report agrees — *"google books did not answer … 256 of the week's titles"*.

**What the new snapshot holds** (`chart_logic: 2`):

| Chart | Rows | New since the merge | Notes |
|---|---|---|---|
| `bengali` | **100** | 8 new, 6 dropped | **12 titles in Bengali script** (was 7) — Bangabani's rows — and **covers 100/100** |
| `english` | **100** | 18 new, 10 dropped | ⚠️ covers **92/100**: one cover answered `502` and Google was down |
| `all-language` | 30 | 2 new, 2 dropped | covers 30/30 |

✅ **Bangabani-only titles are on the Bengali chart** — `পাতাঝরার মরশুমে`, `ঝাল লজেন`, `কাকাবাবু সমগ্র`, `মিতিনমাসি সমগ্র` —
titles no other declared vendor carries.

⚠️ ⚠️ **And the fresh gather is *better* than the migration it replaces.** The merged week held **92** English rows
because merging removed eight and nothing filled them; a gather ranks the **union** of the lists, so the freed slots go to
the next-ranked works and the chart holds **100 distinct works** — a Top 100 with no duplicates rather than a Top 92.

⚠️ **One cover failed** (`502` on `9780063455887`), which is *the source being unreachable* rather than *this book has no
cover* — the distinction `covers.download` deliberately keeps, and why `english` reads 92/100.

⚠️ ⚠️ **And the operator's shell is worth a line in the record**, because it cost three attempts: the launch command was
being re-run by the terminal integration, and each re-run **restarted the gather before it could finish** — so the run
never got past the fetch and looked like a hang. ⚠️ The fix was a **self-guarding launcher** (`pgrep … || exec …`), which
makes a repeat a no-op. ⚠️ An earlier guess of *App Nap* was wrong and is recorded as wrong: the process was simply young,
because almost no real time had passed between the polls.
