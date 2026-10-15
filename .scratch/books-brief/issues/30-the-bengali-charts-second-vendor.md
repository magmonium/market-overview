# The Bengali chart's second vendor

Type: research
Status: resolved
Blocked by: 29

## Question

⚠️ **Ticket 29 left `bengali` with one vendor and two open items**, and both were **searches** rather than corrections:

- *"A second weekly Bengali ranking"* — ⚠️ Rokomari alone cannot corroborate anything, and ticket 17's arithmetic is the
  reason the chart was **absent**.
- *"A date for Rokomari"* — the list parses (60 rows), its address is settled, and only its **vintage** is unknown.

⚠️ **And the operator was reading the consequence, not a bug.** `./build books` → week `2026-W41` → chart `1 bengali`:

```
books · 2026-W41 · bengali
bengali: not in this week's bundle — it could not be built
```

⚠️ **The instruction for this ticket was a list of seven addresses to collect from** — `boighar.in`, `boichitro.in`,
`goodreads.com/shelf/show/bengali`, `oxfordbookstore.com`, an Amazon.in **search** URL, `flipkart.com` and
`daraz.com.bd` — and then to build a ranking from what they hold.

## Answer

### ⚠️ Four of the seven are not sources, and the fetch is what says so

| Fetched | What it actually is | Verdict |
|---|---|---|
| `amazon.in/bengali-books-bestsellers/s?k=…` | a **search results page** — *1–16 of over 1,000 results*, and **no rank badge anywhere** | ❌ **confirms ticket 29**, which had already refused it |
| `daraz.com.bd/tag/bengali-novels` | a tag page that ships **no products** in its HTML (57 KB of chrome and footer) | ❌ empty |
| `goodreads.com/shelf/show/bengali` | an **all-time shelving count** — *"shelved 75 times as bengali"*, 5,200 books, sorted by that count | ❌ not sales, not weekly |
| `flipkart.com/books/bengali~language/pr?sid=bks` | a **category browse** of **20,109** products, default-sorted by *Popularity* | ⚠️ a real ordering, undated, no ISBN, 500+ pages — **recorded, not declared** |

⚠️ **Goodreads is the one worth naming as a near-miss**, because it *looks* like a ranking: it is ordered, it is
book-shaped, and it has an author and a rating on every row. ⚠️ But the order is **how many readers shelved a book**, ever
— so it is a chart of *what people say they want to read*, and putting it beside two shops' sales rankings would be a
corroboration that never happened.

### ✅ What *is* a source: the booksellers, and they are JSON

⚠️ **`boichitro.in` and `boighar.in` run WooCommerce, and WooCommerce publishes a Store API** — no scraping, no key, and
an `orderby` that accepts `popularity`:

```
https://boichitro.in/wp-json/wc/store/v1/products?orderby=popularity&per_page=100   → 200, 100 products
https://boighar.in/wp-json/wc/store/v1/products?orderby=popularity&per_page=100     → 200, 100 products
```

⚠️ **The parameter is honoured rather than decorative** — verified by fetching all three orders:

| `orderby` | first three products |
|---|---|
| `popularity` | Jayanta Manik Samagra · Deshantare Baj · Ishwarer Antim Swash |
| `date` | Muktitirtho Andaman · Rabindranather Kishore Galpagucha · Nandan-Sharad 1433 |
| `rating` | Taranath Tantrik Samagra · Manjari Mahal · Iti Tomar Ma |

⚠️ **And the field list is better than a scrape gives.** A Store API record carries `id`, `name`, `sku`, `prices.price`
**with `prices.currency_code`**, `average_rating`, `review_count`, `images[0].src`, and an `attributes` array with
`pa_authorname`, `pa_publisher`, `pa_binding` and — on some records — **`pa_isbn`**.

| | BoiChitro | Boighar |
|---|---|---|
| `pa_isbn` present and a valid ISBN-13 | **18 of the first 100** | **none at all** |
| `pa_authorname` useful | yes, on nearly every record | `N/A` on many; the real one is sometimes `pa_author-2` |
| its own top five | books with 5–150 reviews | **2021 magazines with one review apiece** |

⚠️ **So `boichitro` is declared and `boighar` is not.** The client reads both (one module, as `amazon.py` reads five
marketplaces) and `boighar` is one line in `charts.py` — ⚠️ but a vendor with **no ISBN** can neither corroborate nor be
corroborated, and a vendor whose ordering is unverifiable adds **noise** rather than reach. ⚠️ Declaring it would not be a
bigger chart.


### ⚠️ And Rokomari needed no new code — ticket 29's second item was misread

⚠️ Ticket 29 recorded *"Rokomari needs a date … that is the whole of what stands between this chart and the freshness
guard"*. **The guard's complaint was right and the conclusion was wrong.** ⚠️ A **retailer's own bestseller category is
regenerated per order** — there is no dated artefact for a date to be *missing from* — so asking it for one refused the
source forever. ⚠️ That is precisely the case `charts.LIVE` was introduced for on the same day, and the Amazon stores
were already in it.

⚠️ **The half that still protects the product is untouched**: a Rokomari that answers **nothing** is still a missing
vendor and still makes the chart absent (ticket 18).

### ⚠️ And the two vendors share **no ISBN at all** — ticket 21's prediction, confirmed on live data

⚠️ Both vendors were then run **for real** through the product's own clients (`fetch → parse → freshness.guard →
corroborate.admit`), which is the only way this could have been found:

```
rokomari   rokomari-best-sellers.html   bytes=  705,899   rows= 60
boichitro  boichitro-bestsellers.json   bytes=1,083,693   rows=100

kept rows: 160 | missing vendors: ()
admitted titles: 160
titles carrying BOTH vendors: 0
titles resolved to a real ISBN: 29
```

⚠️ ⚠️ **Not one title is carried by both vendors.** Ticket 21 said the vendors would not overlap — *"an Indian Bengali
title has Anandabazar + Amazon.in, while a Bangladeshi title has Rokomari alone"* — and ⚠️ **it is now measured rather
than predicted**: BoiChitro ranks Indian-market Bengali books, Rokomari ranks Bangladeshi ones, and they are two
catalogues.

⚠️ **Which is why ticket 17's reversal is load-bearing here rather than theoretical.** Under the old *intersection* gate
this chart would admit **zero** titles — not few, none. ⚠️ Under the union it admits 160, and the two vendors' agreement
is expressed as **weight** (a title on both lists out-scores a title on one) rather than as a filter. ⚠️ Today the weight
does nothing for this chart, because there is nothing to double-count; ⚠️ it would start doing something the moment a
book appears in both shops.

### The decisions

| Was | Is now | Why |
|---|---|---|
| `rokomari` written, tested, **unregistered** | **registered** | the blocker was a misreading of the source, not a defect in the client — see above |
| `rokomari` not in `charts.LIVE` | **in `LIVE`** | a ranking regenerated per order has no stale copy to catch |
| `bengali` vendors `(rokomari,)`, market `bangladesh`, country `bd` throughout | **`(rokomari, boichitro)`**, market **`india+bangladesh`**, country `in` + `bd` | the market follows the sources (ticket 19's rule), and the label ticket 29 kept in `copy.ts` was kept for this |
| the chart absent every week | **builds** | two vendors that exist, neither of which needs a date |

⚠️ **One thing is deliberately *not* done.** BoiChitro is a Bengali bookshop whose bestseller list carries **English rows
too** — its own top ten holds *Strange Weather in Tokyo* beside *দেশান্তরে বাজ* — so the list declares **no language**
(ticket 20's *empty means unknown*, which draws no label) rather than a `bn` that would be confidently wrong on some rows.
⚠️ It is `all-language`'s arrangement, applied to the second list that needs it.

⚠️ **And one near-miss was checked and refused rather than left as a maybe.**
**`oxfordbookstore.com/collections/bengali-books`** is a Shopify store and its `/products.json` answers **200** with
ISBNs inside `body_html` — ⚠️ but a *collection* is a merchandising list, not a ranking, and `sort_by=best-selling` is a
query parameter that has to be verified per store rather than assumed. ⚠️ **Not declared**, because *"the store serves a
best-selling order"* is a claim nobody has checked yet.
### ⚠️ ⚠️ And the build found a second defect — Rokomari's record shape had changed, silently

⚠️ **The first attempt to build the week with both vendors on it failed**, and the message was the guard's:

```
bengali: no fresh list from rokomari — the chart is absent
```

⚠️ **The vendor had answered.** The fetched page was 709,628 bytes, and it held **60** `"productType"` occurrences — the
same sixty records the 2026-10-14 recording had. ⚠️ The parser produced **0 rows**.

⚠️ **The cause was one field, added between the recording and the build:**

```
2026-10-14   {"product":{…},"productType":"book"}
2026-10-15   {"product":{…},"adClickUrl":"$undefined","productType":"book"}
```

⚠️ `rokomari.PRODUCT` was `\{"product":\{([^{}]*)\},"productType":"book"\}`, and its own comment said the flatness was
what made it *"honest here rather than fragile"* — because *"a product record has no nested braces"*. ⚠️ **That was true
when it was written and false one day later**, and the failure mode was **nothing**: no exception, no partial list, no
warning. The vendor was reported *missing*, which is indistinguishable from a block page.

⚠️ **The fix is structural rather than a wider pattern**: `rokomari.records` finds each `{"product":{` and walks to its
matching brace, **string-aware** so a brace inside a quoted title cannot unbalance it, and `json.loads` is the judge.
⚠️ A field added *inside* the product object is survived by the same walk; the old pattern could not have survived either.

⚠️ **And a second fixture was recorded** (`tests/fixtures/rokomari-flight-2026-10-15.html`, one verbatim chunk, 3.5 KB),
because the first recording no longer describes what the vendor serves. ⚠️ **Both are kept**: a parser tested only
against the newest shape is a parser nobody has tested against the shape it was written for.

⚠️ **The lesson is the one this map keeps re-learning, and it is worth stating plainly:** *the parser's assumption was
never wrong in the abstract — it was wrong the moment the vendor changed, and nothing in the product could see that.*
⚠️ A source that returns **nothing** is treated as a missing vendor, which is right; but a source that returns nothing
*because the parser stopped matching* looks exactly the same from the conductor, and only **fetching the page and
counting what it holds** told the two apart.

### ⚠️ And the failed build *recorded a week* — the sequencing hazard the snapshot's existence creates

⚠️ The 12:36 attempt did not write nothing. **`all-language` built** — its only vendor is a live Amazon list, so it needs
no date — so the run got past `if not bundle["charts"]` and **wrote `store/2026-W42/facts.json`** holding one chart.
⚠️ Because the snapshot's existence **is** the switch (ADR 0003), that week then **replayed**, and the next
`build --chart bengali` said *"not in this week's bundle — it could not be built"* **without fetching anything at all**.

⚠️ **That is not a defect** — it is partial delivery working exactly as ticket 13 designed it. ⚠️ But it is a **sequencing
hazard worth naming**: a week gathered while a source is broken is a week that can no longer be gathered, so **the fix has
to land before the run** or the snapshot has to be removed.

⚠️ **And `2026-W42` was the wrong week to reach for anyway.** Its Sunday is 2026-10-18, so the *compiled* lists — NYT and
Indie — do not exist for it yet: `english` was refused for exactly that reason, and only the **live rankings** can answer
this early. ⚠️ `menu.last_buildable_week()` had already said so — it offers **2026-W41**, not this week, for this very
reason — and building ahead of it records a week that will never hold the charts that were missing from it.

⚠️ **The failed experiment's artifacts were removed** — the W42 snapshot and the raw responses it wrote — so the working
tree holds no evidence of a run that failed for a reason that no longer exists.

⚠️ ⚠️ **And `2026-W41` was re-gathered, deliberately, as the operator's call.** The snapshot was written while the
Bengali chart could not be built, so it holds `english` alone; ⚠️ a chart cannot be *added* to a recorded week (the
snapshot's existence is the switch), and the only way to the Bengali chart today was to gather the week again. The
consequences are stated rather than glossed:

- ⚠️ **The committed snapshot is replaced**, and the week's raw responses with it. The previous `facts.json` is kept at
  `/tmp/w41-facts-before-regather.json`, and `git checkout -- src/books-brief/store/2026-W41/` restores the committed
  one.
- ⚠️ **The English chart is re-derived from a fresh fetch**, so it is not the chart the already-rendered
  `output/books/2026-W41/english` video was made from. ⚠️ That is the *product's* guard working rather than a gap:
  `publish` refuses a rebuilt week rather than putting a second, different chart under one title (ticket 24).
- ⚠️ **This is not a precedent.** It is the one-off cost of adding a source to a week that was recorded before the source
  existed, and the next week is gathered once, with every vendor in place.
### ✅ What the re-gathered week actually holds

```
all-language   market=india              rows= 30 countries=['in']
bengali        market=india+bangladesh   rows=100 countries=['bd', 'in']
english        market=worldwide          rows=100 countries=['au', 'ca', 'gb', 'us']
comics: no fresh list from nyt — the chart is absent
```

⚠️ **Three charts, and the Bengali one is the point**: a hundred rows drawn from **two vendors in two countries** — `bd`
rows from Rokomari, `in` rows from BoiChitro — which is the bridge ticket 21 asked for and ticket 29 could not build.

⚠️ Its package is `output/books/2026-W41/bengali/`: a **16.95 MB** video with the music muxed on (the container carries
both a `vide` and a `soun` handler), a thumbnail, and the YouTube metadata — title *"Top 100 Bengali Books | Week 41 |
5 Oct, 2026"*, the full list in the description, 27 tags. ⚠️ **`bengali` was the only chart rendered**, because
`--chart` narrows the render and never the gather: the other three are in the snapshot and render on demand from it.

⚠️ **`comics` is absent, and that is the guard rather than a defect.** NYT's `graphic-books-and-manga` list is not weekly,
so its date falls outside the week and the vendor counts as **not having answered** (ticket 18). ⚠️ It is the finding
ticket 22 recorded, now visible in a snapshot.

⚠️ **And the week's `window_weeks` is 1.** The six-month window is accumulated from our own snapshots, so a chart built in
the week its sources land has one week of it — ⚠️ ticket 23's ramp, stated here rather than discovered later.






### ⚠️ ⚠️ And then the covers were missing for **every** row — three causes, found one at a time

⚠️ The first Bengali chart shipped with **0 of its 100 rows carrying a cover**, while the two charts beside it in the same
snapshot had **100% and 100%**. ⚠️ Three causes, and **the first two wore the same error message** — which is why they took
three probes to separate.

1. ⚠️ ⚠️ **`403 Forbidden`, and it was the User-Agent.** `covers.download` used `urllib`'s default — `Python-urllib/3.14`
   — and BoiChitro's WordPress uploads refuse it, answering **`200` to a browser string**. ⚠️ Verified by fetching one
   image both ways. ⚠️ **And `curl`'s default UA is *not* refused**, which is what made the first probe misleading: the
   same URL answered `200` three times from the shell while the product got `403` ninety-eight times.
2. ⚠️ **`'ascii' codec can't encode character '\u2013'`** — two covers, and a **defect rather than an outage**: the store
   serves filenames carrying an **en dash**, `urllib` writes its request line as ASCII, and `urlopen` raised *before the
   request was made*. ⚠️ A browser percent-encodes the path first.
3. ⚠️ ⚠️ **Rokomari's rows had no cover URL at all.** `rokomari.parse` never recorded one, so those rows had no source to
   fall back to either: `listed` empty, Google Books' quota spent, and Open Library **404s** for the vendor's own keys
   (`rokomari:873`). ⚠️ The picture was in the card the whole time.

⚠️ **And it is `data-src`, not `src`.** Rokomari lazy-loads its cards: `src` is
`/nstatic/images/placeholder-image.gif` and the real file is the `data-src` beside it. ⚠️ A parser reading `src` would put
**the same grey placeholder on every row** — a chart that looks *broken* rather than one that is missing its covers.

⚠️ ⚠️ **The selector that works is the image *host*, not the component's class.** The obvious pattern is
`productContainer_coverImage__…`, and ⚠️ **it appears on only 15 of the 60 cards** — the other forty-five render the same
picture through a different component, so a class-based pattern found a cover for **one row in sixty**. ⚠️ A CSS-module
hash is a **build artefact**; the image host is the source's, and it is the same on every card.

⚠️ **And a cover is attributed by the card, never by proximity.** The window between two records *is* the card, and the
last image in it is that row's — so a card with no image of its own leaves its row **without** a cover rather than
inheriting the previous card's. ⚠️ A wrong cover is worse than a missing one: nobody looking at a slide can tell that the
picture belongs to another book.

⚠️ **The third fix needs the gather to run again** — a cover is recorded in the snapshot, so a chart that already holds
`cover: null` cannot be given one by changing the downloader. ⚠️ It is the same sequencing rule the parser taught, twice
in one ticket: **a fix that lands after the gather cannot change the gather's chart.**

⚠️ **And one finding from that gather is *not* fixed, because it is not ours:** **Google Books' daily quota was spent** —
`429 Too Many Requests` for 6 titles and `503 Service Unavailable` for 66. ⚠️ The product degrades as designed (*"a title
the enrichment source does not know still gets a row"*), so this costs fields and not books — but the Bengali chart's
publishers and genres are thinner than its sources could supply, and no code change makes a spent quota come back.

### ⚠️ ⚠️ How the fix reached a chart that was already built — a repair, not a gather

⚠️ **A cover is *recorded in the snapshot*.** A chart already holding `cover: null` cannot be given one by changing the
downloader, so the week had to be built again — ⚠️ **and the gather would not complete in this environment** (a long job
is killed after a few minutes). So the covers were **repaired from the store's own evidence** instead:

- ⚠️ **The raw responses the week was built from are committed** — `store/2026-W41/raw/boichitro-bestsellers.json` and
  `…/rokomari-best-sellers.html` — so every cover URL is **re-derivable by the product's own parsers**: 160 URLs from the
  two lists.
- ⚠️ **`covers.download` then fetched the ones the chart needs** — the snapshot's covers went **0 → 100 of 100**.
- ⚠️ ⚠️ **No row, rank, score, price or label changed.** A cover is not a ranking input (`rank.py` never reads it) and is
  recorded for the renderer — the same class of field `facts.retime` already re-derives on a replay, and for the same
  reason: *the timeline is presentation, not evidence.*
- ⚠️ **The chart was then re-rendered from that snapshot**, and the package's `bundle_hash` equals the snapshot's
  sha256 — so the video, the thumbnail and the metadata all describe **one** facts file, and the description carries
  every row title in order.
- ⚠️ **A gather would now produce the same covers**, because the downloader is fixed. The repair made the *existing*
  chart whole; it is not a way to avoid gathering.

⚠️ **And a second lesson, learned by doing it twice at once.** A detached run that looked dead was still alive, so **two
builds worked in the same package folder** — ⚠️ and the older one's `finally` **deleted the shared `.bed.wav`**, so the
newer one's `audio.mux` failed with *"No such file or directory"* and **threw away a completed render** (its scratch video
is unlinked by design). ⚠️ **The product assumes one run at a time and nothing enforces it**: the bed's path, the scratch
video's path and the package folder are all week-and-chart-scoped, never run-scoped. ⚠️ That is a **ticket** — a lock, or
a run-scoped scratch name — and it is recorded here because the failure looked like a *missing file* rather than like two
runs colliding.




### ⚠️ And `boierhaat.com` is the most *tempting* source of the set — and still not a source

⚠️ **Fetched 2026-10-15.** Boierhaat is a **Kolkata** Bengali bookshop (₹, `+91 7044472233`, uploads on S3) on a
**custom Laravel storefront** — ⚠️ **not WooCommerce and not Shopify**, so `fetch/woocommerce.py` does not reach it and
`/wp-json/wc/store/v1/products` answers **404**. Its HTML is server-rendered and carries literal Bengali, ⚠️ in a
normalisation that differs from a typed literal, so any parser for it would have to normalise before it compared
anything (the trap `test_fetch_rokomari.py` already documents).

⚠️ **It looks like the best source of the seven**, because it has more than the others do:

| | |
|---|---|
| Ranked list | ✅ **"সর্বাধিক বিক্রীত বই" — *most sold books***, an ordered sales list … of **six** items, with **no dedicated page** (`/most-sold-books`, `/best-selling-books`, `/popular-books`, `/popularity`, `/shop` all **404**) |
| A number per book | ✅ **জনপ্রিয়তা সূচক — *popularity index***, a big seductive integer beside every title |
| Author, publisher, price, cover, stock | ✅ all present, per book |
| ISBN | ❌ **none anywhere** — no `isbn` string, no `978`/`979`; the ten-digit numbers on a product page are epoch timestamps |
| Date | ❌ none → it would be `LIVE` |

⚠️ ⚠️ **And the popularity index is not sales, which is the whole finding.** The site explains it itself at
**`/know-popularity-index`**: the index is *"একটি কৃত্রিম বুদ্ধিমান দ্বারা পরিচালিত নির্দেশক"* — an **AI-driven indicator
of a book's discussion and reviews across the media**, computed from *"বিভিন্ন গণমাধ্যম ও পত্র-পত্রিকায় প্রকাশিত …
আলোচনা-পর্যালোচনা"* (press and review coverage), raised when a book is *"অন্য বই বা গবেষণাপত্রের কৃত্রান্তি স্বীকারে
উল্লিখিত"* (cited in another book's or a paper's acknowledgements), drawn from *"3 টি গণমাধ্যম ও একাধিক প্রতিষ্ঠিত
পত্রিকা"* and about **1.7 million data points** — with **no upper limit** (1 = some reaction, 100 = very good, 500 = very
highly regarded).

⚠️ **So the number that looks most like a sales figure is a media-mention score**, and putting it on a chart whose own
description reads *"Ranked on sales over six months, with user reviews"* would be a **category error wearing a number** —
the exact failure this product refuses everywhere else. ⚠️ **Nothing here is sales except the six-item list**, and six is
not a chart.

⚠️ **The second objection is the one that would apply even if the index were sales: there is no ISBN.** Both Boierhaat and
BoiChitro are Kolkata shops selling the *same* Bengali books, and a row keyed `boierhaat:…` can never merge with a row
keyed `boichitro:…` — so the union would put **one book on the chart twice**, under two vendors. ⚠️ That is the
objection that refused `boighar`, but sharper: there the overlap was incidental, and here it is guaranteed.

⚠️ **Verdict: recorded, not declared.** ⚠️ It is worth the space in this ticket precisely because it is the source that
would have been easiest to *believe* — a real shop, real books, real prices, and a number beside each one.



### ⚠️ What this leaves

- **`boighar` needs an ISBN attribute** before it is worth declaring — *"the address is the list's identity"* one level
  down: a vendor with no identifier is a vendor that cannot join.
- **`flipkart` is a real ordering in search of a parser.** Its default sort *is* popularity and its catalogue is 20,109
  Bengali books — ⚠️ far deeper than any shop's hundred — but it states no ISBN, dates nothing, and paginates 500 pages.
  It is a **ticket**, not a line.
- ⚠️ **A hundred records is about a megabyte** of committed evidence per week
  (`store/<week>/raw/boichitro-bestsellers.json`), because a Store API record carries its whole `description`. ⚠️ Ticket
  28's retention question is now a real one rather than a tidy one.
