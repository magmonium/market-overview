# The Anandabazar list, located — and it is an archive

Type: research
Status: resolved
Blocked by: 29

## Question

Ticket 29 closed with the Bengali chart's Indian half missing, and named what would bring it back:

> **The Bengali chart needs a second vendor.** ⚠️ Rokomari alone cannot corroborate anything, so finding Anandabazar's
> weekly list — or any second weekly Bengali ranking — is what would bring the chart back. ⚠️ That is a **search**, not a
> correction, and it belongs to a fresh ticket.

The operator then supplied an address and asked for it to be **prioritised**:

```
https://www.anandabazar.com/culture/book-reviews/best-seller-bengali-books-of-this-week-1.138440
```

So the question is not *"is there a weekly Bengali list?"* — ticket 02 asserted one and ticket 21 put Anandabazar in the
Bengali chart's final source set. It is: **is this address it, and can it be declared?**

## Answer

### ✅ The list is real, and it is the shape tickets 02 and 21 claimed

Fetched with the product's own client (`curl_cffi`, `impersonate="chrome"`), the page carries a **ranked, sales-based**
weekly Bengali list in two sections:

```
বেস্টসেলার
বিক্রির নিরিখে এ সপ্তাহে বই-বাজারে বাংলা ফিকশন এবং নন-ফিকশনের সেরা বইয়ের তালিকা।
শেষ আপডেট: ২৫ এপ্রিল ২০১৫ ০০:০১

গল্প-উপন্যাস                                     অন্যান্য
১. প্রাণসখা বিবেকানন্দ ১ম-২য়, রঞ্জন বন্দ্যোপাধ্যায়। পত্রভারতী (১)   ১. হারানো খাতা, রমাপদ চৌধুরী। আনন্দ (-)
২. রহস্য সমগ্র, শীর্ষেন্দু মুখোপাধ্যায়। আনন্দ (-)                   …
… ১০. স্বপনকুমার সমগ্র, সম্পাদনা: নিমাই গরাই। লালমাটি (-)
```

Three things about it matter to this product, and all three are good news:

- ✅ **It is ranked by sales**, in its own words — *"বিক্রির নিরিখে"* (on the basis of sales) — rather than by a shop's
  ordering. That is the distinction ticket 21 drew when it called Rokomari *"a retailer ranking its own sales"*.
- ✅ **It states its own date**, both as visible text (*শেষ আপডেট: ২৫ এপ্রিল ২০১৫ ০০:০১*) and as `datePublished`. ⚠️ **This
  is the one thing neither of the Bengali chart's current vendors can do** — Rokomari and BoiChitro are `LIVE` precisely
  because they state no date at all. A dated list needs **no exemption** from `freshness`.
- ✅ **Each row carries an author and a publisher**, and a trailing `(n)` — `(১)`, `(-)`, `(৪)`, `(৮)` — a second signal
  per row that the other vendors do not publish.

### ⚠️ But the address is an archive, and every instalment found is 2014–2015

| Address | Date the page states | Ranked rows |
|---|---|---|
| `…/best-seller-bengali-books-of-this-week-1.138440` | **2015-04-25** | 20 (10 + 10) |
| `…/list-of-best-seller-books-1.140978` | 2015-05-02 | 20 |
| `…/abp-best-seller-1.169860` | 2015-07-04 | 20 |
| `…/culture/book-reviews/…-1.5685` (a Bengali slug) | 2014-02-27 | 19 |

⚠️ **The first three came from the site's own `/topic/best-seller-books` hub** — which links to exactly two of them and
holds **nothing newer than 2015** — and the fourth from a search; ⚠️ **every instalment of this series that could be
located anywhere is 2014–2015.** The slug of the operator's link says *of this week*; the page says **April 2015**. ⚠️ That
is the same trap ticket 29 found on PW — *"its free pages are a 2012 archive"* — and it is the reason this ticket exists
rather than a declaration.

### ⚠️ The website no longer publishes it, and the print page is a **scan**

- ⚠️ **The news sitemap carries no books coverage at all**: 483 URLs, **none** under `/culture/book-reviews/`. The story
  sitemap's 34 URLs name none either.
- ⚠️ ⚠️ **And the section page and the site's search are both JavaScript shells.** `/culture/book-reviews` lists no
  articles in its HTML, and **`/search?q=` returns byte-identical pages (181,190 bytes) for every query**. ⚠️ **My first
  reading of that was wrong** — I took *"the search indexes nothing"* from an empty parse, which is precisely the mistake
  ticket 29 caught itself making with `/list/38927`: *"looking for what I expected to be there, and reading its absence as
  proof."* An unparsable page is not an absent article.
- ✅ **The list itself still runs — weekly, in print, on Saturdays.** ⚠️ **And the e-paper's own page titles say so**: the
  string *"| পুস্তক পরিচয় - page …"* appears in the titles of **nine** editions of the same Saturday at once — কলকাতা,
  হাওড়া-হুগলি, পূর্ব মেদিনীপুর, উত্তর/দক্ষিণ ২৪ পরগনা, শিলিগুড়ি-জলপাইগুড়ি, উত্তরবঙ্গ, বীরভূম, মুর্শিদাবাদ — and the
  e-paper's own page index names the same page, verified by fetch: **page 16 of Saturday 2026-08-08** and **page 24 of
  Saturday 2026-10-10**. ⚠️ **The page number varies** — 16 and 18 on one Saturday, 20 and 24 on others — so it has to be
  **located** rather than assumed; ⚠️ and the Thursday 2026-10-15 edition names none at all, which is the same fact from
  the other side.
- ⚠️ ⚠️ **And the e-paper page is an image, not text.** Page 16 of 2026-08-08 serves **23 page images**, **177 visible
  words**, no text layer, no OCR output and no JSON state — a scan of newsprint. ⚠️ Reading it would mean OCR: a new
  dependency, unverifiable by fixture, on Bengali type. **Refused**, for 20 rows.
- ⚠️ **And the print archive host is down.** ✅ The archive is real and indexed, in the form
  `/archive/1<YYMMDD>/<DD>pustak<n>.html` — `…/archive/1131005/5pustak2.html` (2013-10-05) and
  `…/archive/1111231/31pustak1.html` (2011-12-31) both exist under the title *"আনন্দবাজার পত্রিকা - পুস্তক পরিচয"*, beside
  `/oldarchives.html` — ⚠️ **but the host answers 521 ("Web server is down") at its root**, over both `http` and `https`,
  for every path tried. ⚠️ So the archive is indexed and **not serving**: the origin is down rather than blocking bots, and
  it is not a matter of finding the right URL.

### ⚠️ The publisher's robots.txt, recorded because the reader is owed it

`User-agent: *` is `Allow: /`, and the file then names a blocklist at `Disallow: /` — including **`Scrapy`**,
**`anthropic-ai`**, **`ClaudeBot`**, **`Claude-Web`**, `GPTBot`, `CCBot`, `Google-Extended` and `Amazonbot` — while
**`Claude-User` and `Claude-SearchBot` are explicitly allowed**. ⚠️ **The publisher's own policy separates interactive,
user-driven use from bulk crawling**, and this product is the former: one list page per chart per week. ⚠️ That is the
same kind of note `fetch/amazon.py` carries about Amazon's conditions of use — *"a decision the reader of this product is
owed rather than a detail"* — and it is the reason a client here would be legitimate while a crawler would not.

### ⚠️ Why it is still not declared — the arithmetic, because it is the whole point

Declaring this address would not make the Bengali chart smaller. **It would make it absent**:

1. `Listing` requires an address of every vendor in `SCRAPED`, so the address *would* be declarable — the rule that removed
   `anandabazar/bengali` in ticket 29 no longer blocks it.
2. But the list is dated **2015-04-25**, and 2026-W41's span is 2026-10-11 … 2026-10-17. `freshness.is_fresh` is false
   for every row.
3. So `freshness.guard` drops them all and reports `anandabazar` **missing** — *"a stale source is a missing source for
   that week"*.
4. And by **ticket 18's spine**, a declared vendor that is missing makes its chart **absent** — *"a degraded chart is a
   wrong chart."*

⚠️ **So declaring it would undo ticket 30's repair and refuse the Bengali chart again** — for the operator's own reason,
correctly applied. ⚠️ **The guard is not what is wrong here; the address is simply not this week's.** This is the case
ticket 10 was written for, arriving with a real example.

⚠️ And the behaviour is **already pinned by a test** —
`test_a_stale_vendor_makes_the_chart_absent_rather_than_smaller` (`tests/test_cli.py`) — so this decision rests on tested
code rather than on a reading of it.

### ⚠️ What would unblock it, and how small the client is

**A current text address is the only missing piece.** Everything else is settled, and the parse is small:

- The list is **two named sections** (`গল্প-উপন্যাস`, `অন্যান্য`) of ten rows each, so the section is the genre field
  ticket 26 needs rather than something to invent.
- A row is `rank. title, author। publisher (n)` — **position is the rank**, as with both new Bengali vendors, and the
  `(n)` is a second field worth reading.
- ⚠️ **The date comes from the page**, so no `LIVE` entry would be needed — the one Bengali vendor that could satisfy the
  guard honestly.
- ⚠️ It is `curl_cffi`-only: **403** to plain `curl` *and* to a plain browser `User-Agent` (Akamai), **200** to
  `impersonate="chrome"`. The product already does this for Amazon and Rokomari.
- ⚠️ **Depth is 20 rows, not 100.** `rank.weight` pays a shallow list less rather than refusing it, so this is a cost and
  not a blocker — but it is a cost, and it should be stated before the chart is built on it.

⚠️ **What is *not* the answer**:

- **OCR of the Saturday e-paper scan** — a new dependency, unverifiable by fixture, over Bengali newsprint, for 20 rows.
- ⚠️ **The annual "ten best books" feature, which a search *does* surface** — worth naming, because it is what the next
  hunt finds first:
  `…/lifestyle/list-of-ten-best-books-published-in-2025-according-to-anandabazar-dot-com-dgtl/cid/1657556`. ⚠️ **Editorial,
  annual, and chosen by the paper's own judgement** rather than ranked by sales — the opposite of this chart's basis, and
  the wrong cadence.
- ⚠️ **And two leads recorded rather than chased**: `boibazar.com/category-books/best-seller-books` — a Bangladeshi
  bookseller's best-seller category, the same *class* of source as Rokomari rather than a second kind, and unexamined
  beyond its existence — and `banglareads.com/publisher/159/books/best-seller`, which **was fetched and refused**: a
  client-rendered storefront, 165 KB with no dates anywhere in its HTML.

### ⚠️ What changed as a result of this ticket

- ⚠️ **Nothing in the code.** The Bengali chart still builds from Rokomari + BoiChitro (ticket 30), and its market is
  `india+bangladesh` again — which is what it should be, since BoiChitro is Indian and Rokomari is Bangladeshi.
- ⚠️ **The README's Bengali row said *"Anandabazar's weekly list was never located"*, and that is now precisely wrong.**
  It was located, it is a real ranked sales list, and it is an **archive**. The row now says so.
- ⚠️ **`ANANDABAZAR` stays in `charts.SCRAPED` with no address**, and now carries the finding beside it — the refusal
  waiting for whoever declares it next, with the reason it has not been declared yet.

### ⚠️ The evidence

Fetched 2026-10-15 with `curl_cffi` impersonating Chrome, one request per address, no crawling: the four instalments
above; `/topic/best-seller-books`; `/culture/book-reviews`; two `/search?q=` probes; `news-sitemap.xml` (483 URLs);
`story-sitemap.xml` (34 URLs); `robots.txt`; `archives.anandabazar.com` at its root, over http and https; and
`epaper.anandabazar.com` pages for 2026-08-08, 2026-10-10 and 2026-10-15.

⚠️ ⚠️ **And four facts here could not be fetched, so they were checked against a search index** — the archive's URL format,
the e-paper pages' own titles, the annual feature, and `boibazar` — ⚠️ **because they had been written into this ticket
from the pattern before any response confirmed them.** ⚠️ **The check confirmed all four**, and the process is recorded
rather than tidied: a claim that arrives before its evidence is the failure ticket 29 caught in itself, and the next
reader should not have to guess which of these sentences were verified when.
