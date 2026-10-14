# The declarations the sources do not support

Type: grilling
Status: resolved

## Question

⚠️ **Three of the four charts declare source lists that the vendors do not publish.** All three were found by fetching
the sites rather than by reasoning about them, and all three were written from **assumption** — which is what ticket 02's
own source table did, and why it names sources without ever naming an address.

| Chart | Declared | What the vendor publishes |
|---|---|---|
| **All-language** | `amazon-in/hindi`, `…/bengali`, `…/tamil`, … ×9 | ⚠️ **one** mixed-language list, `…/gp/bestsellers/books/86946561031/` |
| **Bengali** | `amazon-in/bengali` | ⚠️ **no list exists** — the books nav has no language category, and the only per-language address is an unordered search with **no rank badges at all** |
| **English** | `pw/fiction`, `pw/nonfiction` | ⚠️ `pw/bestsellers/hardcover-fiction.html` and `hardcover-nonfiction.html` |

⚠️ **A fourth is unfound rather than wrong**: the Bengali chart's other two vendors — Anandabazar (`/bestseller` **404s**)
and Rokomari (`/book/bestsellers` **404s**) — are the *only* genuinely weekly Bengali lists, and neither address is known.

## What is already known, so the decision is not made blind

- ✅ **The code is finished.** `fetch/amazon.py` has a parser **and** a fetch; `fetch/nyt.py` is complete; the contract is
  `fetch → snapshot → parse`; every response is written to `store/<week>/raw/` before it is read.
- ✅ **Indie Bestsellers is a real list** — `indiebound.org/indie-bestsellers`, 361 KB, **79 ranked nodes**.
- ✅ **PW's real lists are known** — `hardcover-fiction`, `hardcover-nonfiction`, `trade-paper`, `graphic-novels`, and
  `/pw/nielsen/top100.html`, which is a **Top 100**.
- ✅ **The all-language list is already parsable** — 30 cards with ranks, prices and ratings, in Hindi, Tamil, Telugu and
  Urdu, read by the existing parser.
- ⚠️ **None of the drifts fails silently.** A list with no address is refused, or yields no rows; either way the vendor is
  **missing** and the chart is **absent** (ticket 18). The failure is a chart that does not ship, never one that ships
  wrong.

## ⚠️ And PW is not free to read — which changes ticket 19's arithmetic

⚠️ **This was found by fetching the page rather than by trusting the source table**, and it is the sharpest finding of
the set. `publishersweekly.com/pw/bestsellers/hardcover-fiction.html` answers **200** with a clean table — rank, title,
author, publisher, price, page count and **a real ISBN-13**, which is better than Amazon's ASIN — and ⚠️ **it is a 2012
archive page**:

```
1  Stolen Prey        John Sandford, Author. Putnam Adult, $27.95 (416) 978-0-399-15768-4
2  11th Hour          James Patterson, Author. Little Brown, $27.99 (407) 978-0-316-09…
3  The Columbus Affair Steve Berry, Author. Ballantine Books, $27 (448) 978-0-345-52651-9

the only date on the page:   05/28/2012
the page's own words:        "the Bestseller Archive. To view, [subscribe]"
and its login blurb:         "You are NOT a current subscriber to Publishers Weekly magazine."
```

⚠️ **Ticket 02 lists PW as *"free to read"*, and ticket 19's flip to US English rests on it** — *"three weekly vendors,
**all free**, all carrying `rank_last_week`."* ⚠️ **Two of those three claims are now in question**: the lists are behind a
subscription, and the free pages are an **archive** rather than this week's list.

⚠️ **What this does to the arithmetic.** The English chart declares three vendors, and against ticket 17's two-vendor
rule:

| Vendor | Status |
|---|---|
| **NYT** | ✅ free, keyed, weekly, and already complete |
| **Indie Bestsellers** | ✅ free to view — a real list, 79 ranked nodes |
| **Publishers Weekly** | ⚠️ **paywalled**, and the free pages are fourteen years old |

✅ **So the English chart still reaches two vendors** — which is exactly the gate's requirement, and one more than the
Bengali or all-language charts have. ⚠️ But it reaches them with **PW removed**. ⚠️ **PW is declared by the English chart
alone** — the comics chart declares `nyt` and `amazon-in` — so nothing else is affected.

⚠️ ⚠️ **And a paywalled page is not a small failure — it is a refusal.** A declared vendor whose client produces no rows
is a **missing source**, and a chart missing a source is **absent** (ticket 18). So leaving PW in the English chart's
declaration would make the English chart **permanently absent** — the exact outcome ticket 19 flipped the chart to avoid.
⚠️ **The guard catches it, and the guard is right; the declaration is what is wrong.**

⚠️ **And the raw evidence is what made this findable.** `store/<week>/raw/` holds what the vendor actually served, so the
2012 date is in the record rather than in somebody's memory of a page.

## ⚠️ The arithmetic, stated before it is chosen

Ticket 17 needs **two vendors** before any title is admitted. Against that rule:

| Chart | Vendors declared | Vendors that can actually answer |
|---|---|---|
| **English** | NYT · PW · Indie | ⚠️ **two** — NYT is complete and Indie is free to view; ⚠️ **PW is paywalled** |
| **Comics** | NYT · Amazon.in | ✅ **two** — NYT complete, and the Comics node parses |
| **All-language** | Amazon.in | ⚠️ **one** — and one vendor cannot corroborate itself, which is what `charts.py` already says |
| **Bengali** | Anandabazar · Amazon.in · Rokomari | ⚠️ **one plausible, unlocated** |

⚠️ **So two charts can be built and two cannot** — and the two that cannot are the **Bengali chart the product is named
after** and the all-language chart. ⚠️ And English reaches its two **only once PW is removed from the declaration** —
leaving it in makes the chart permanently absent, because a declared vendor that answers nothing is a missing source.

## Options

1. **Correct the declarations to what exists.** English drops PW (paywalled) and keeps NYT + Indie — which is two
   vendors and therefore a buildable chart; all-language ranks the one mixed list; Bengali drops Amazon.in. ⚠️ This is
   honest but it leaves all-language **permanently absent** (one vendor cannot
   corroborate) and Bengali with one unlocated source.
2. **Find the missing addresses first, then correct.** Anandabazar and Rokomari are the only weekly Bengali lists that
   exist, so the Bengali chart's future depends entirely on them — and neither has been located.
3. **Change the charts, as ticket 19 changed the English chart.** If a chart cannot be corroborated, the answer may be to
   change what it *is* — a Bengali chart sourced from Bangladeshi and Indian lists that are not weekly, a two-week
   cadence, or an all-language chart that accepts a single-vendor list and says so.
4. **Drop the charts that cannot be sourced, and ship two.** ⚠️ Ticket 02 already allows this: *"a chart with no source is
   a **finding**, not a failure — and the honest outcome may be that only some of the four charts are buildable."*

⚠️ **What is not an option** is what the declarations do today: naming a list that does not exist, and letting the
absence be discovered by a run that refuses.

## ⚠️ And the Bengali chart's two weekly vendors, checked

⚠️ **Both were searched for rather than guessed at, and both turned out to be something other than a scrapable list.**

### ✅ Rokomari — the records **are** there, and I said they were not

⚠️ **This section was wrong for one turn, and how it was wrong is the useful part.** The first probe searched the flight
for `/book/<id>` URLs, found none, and concluded *"there is no book URL … the titles and ranks are either in a chunk this
probe did not reach or arrive after hydration."* ⚠️ **Both halves of that were false.** Searching for the one shape I
expected and reading its absence as a fact is the same mistake as a `bytes.replace` that silently no-ops — it produces a
confident answer about a question that was never actually asked.

⚠️ **A price is unambiguous, so read *around* one.** Doing that finds the record immediately:

```json
["$","$L62","890",{"product":{"id":890,"categoryId":0,"price":180,
                              "title":"ময়ূরাক্ষী","subTitle":"হুমায়ূন আহমেদ"},
                   "productType":"book"}]
```

⚠️ **`productType: "book"`, a price, a title and a subtitle that is the author** — a **self-contained JSON record**,
which is the thing the parser needed and the thing the first probe declared absent. ⚠️ And the file it is in is **705 KB
of Next.js flight chunks** that `selectolax` cannot see, which is why the DOM probe said `ranked=0`.

### ✅ And the bestseller list has an address

```
rokomari.com/list/38927     200 · 411 KB
  <title>বেস্ট সেলার ২০০+ টি বই | Rokomari.com</title>     ← "Best Seller, 200+ books"
  flight: 162,588 chars · 39 `/book/<id>` links
```

⚠️ **It is the list the site's own footer links**, and its title states its size: **200+ books**, which is the shape this
product ranks. ⚠️ So `charts.py`'s `rokomari/leaderboard` is a slug pointing at a page that is not the list, while
`/list/38927` is the list — the fifth declaration to be wrong about an address, and the first one where the correct
address was **linked from the page the wrong one named**.

### ⚠️ What that means, corrected

| Vendor | Verdict |
|---|---|
| **Amazon.in** | ⚠️ **no Bengali list exists** — only an unordered search, no rank badges |
| **Rokomari** | ✅ **readable** — JSON records inside a flight payload, and a 200-book list at `/list/38927` |
| **Anandabazar** | ⚠️ **no weekly list found** — a news topic, and editorial round-ups |

⚠️ **So the Bengali chart's gap is smaller than this ticket said one turn ago.** It is **one parser** — and a JSON one
rather than a React-tree one — plus the address correction. ⚠️ It is still **one vendor short of the gate**, because
Anandabazar has not been located; but *"readable in principle, unread in practice"* was too pessimistic, and this ticket
said it as a finding rather than as a guess.

⚠️ **The lesson is worth more than the finding.** Three of this session's corrections — the price selector, the title
node, and this — came from the same cause: **looking for what I expected to be there, and reading its absence as proof.**
⚠️ The recordings are the only reason any of them were caught, which is the strongest argument for the raw-evidence rule
this product already keeps.

### ⚠️ Anandabazar — no weekly list found

`anandabazar.com/topic/best-selling` answers **200** with **94 KB**, and a ranked-list probe finds **1** node. ⚠️ Its own
title says what it is: *"Best Selling **News** in Bengali, Videos and Photos about Best Selling"* — a **news topic**, not
a chart.

⚠️ **Every search result for an Anandabazar Bengali list was editorial** — *"the ten best books of 2025"*, *"best books of
the year"* — which is a **different object** from a weekly bestseller ranking, and ⚠️ ticket 02's claim that Anandabazar is
*"the **only** weekly Bengali chart"* is now **unverified**. It may be true and simply not published as HTML; it may be a
yearly feature this ticket mistook for a weekly one.

### ⚠️ What that leaves the Bengali chart

| Vendor | Verdict |
|---|---|
| **Amazon.in** | ⚠️ **no list exists** — only an unordered search with no rank badges |
| **Rokomari** | ✅ **readable** — a flight payload, not DOM, so a parser to write |
| **Anandabazar** | ⚠️ **no weekly list found** — a news topic, and editorial round-ups |

⚠️ **So the chart still has one vendor, not two** — and ticket 17 needs two before a single title is admitted. ⚠️ The
difference from before is that the gap is now **one parser** (Rokomari's flight payload) rather than two missing sources.

## ⚠️ And the mechanism that would stop a fourth

`charts.Listing` **cannot be declared without a country and a language** — ticket 20's discipline, and it is why the labels
cannot drift. ⚠️ **The address is not modelled at all**, and for a scraped list the address *is* its identity: it is the
only thing that distinguishes `amazon-in/hindi` (which does not exist) from `amazon-in/indian-languages` (which does).

So the same discipline applied once more would be: **a scraped list declares its address, and a list that cannot state one
cannot be declared.** ⚠️ A comment in a ticket is read once; a constructor that refuses is read on every run.

## Answer

### ⚠️ Correct the declarations to what exists — and make the *address* the thing a list must state

All four options assume the drift is in the addresses. ⚠️ **The drift was in the declarations**, and the fetches this
ticket recorded settle it: `amazon-in/hindi` and its eight siblings do not exist, `amazon-in/bengali` does not exist, and
`pw/fiction` is a paywalled 2012 archive. ⚠️ So the correction is **option 1** — and the mechanism that stops a fifth is
the part of this ticket that was worth keeping.

### ⚠️ What changed in `charts.py`

| Chart | Was | Is now |
|---|---|---|
| `english` | NYT · PW · Indie (`indie/fiction`, `indie/nonfiction`) | NYT · Indie (`indie/national`) |
| `all-language` | Amazon.in ×9 per-language lists | Amazon.in ×1 — `amazon-in/indian-languages` |
| `bengali` | Anandabazar · Amazon.in · Rokomari | **Rokomari only** |
| `comics` | NYT · Amazon.in | unchanged |

⚠️ **And the Bengali chart's market narrowed with it**: `india+bangladesh` → `bangladesh`. ⚠️ Ticket 19 refused to call a
US-list chart *global* for exactly this reason — a chart may claim only the market its sources support — and one
Bangladeshi list is not an India-and-Bangladesh chart.

### ⚠️ The arithmetic, now that it is decided

| Chart | Vendors | Verdict |
|---|---|---|
| `english` | NYT · Indie | ✅ **ships** — two vendors, both verified live (`indie/national` returns **135 rows**) |
| `comics` | NYT · Amazon.in | ✅ **ships** — two vendors; the comics node returns **30 rows** |
| `all-language` | Amazon.in | ⚠️ **absent** — one vendor cannot corroborate itself, permanently |
| `bengali` | Rokomari | ⚠️ **absent** — one vendor, and the list is **undated**, so the freshness guard refuses it |

⚠️ **Two charts ship. Two do not** — and the two that do not are the ones whose sources do not exist, not the ones whose
code is unfinished.

### ⚠️ A scraped list must state its address

⚠️ **This is the mechanism, and it is a constructor rather than a comment.** `charts.Listing` gained an `address`, and
`__post_init__` **refuses** to build a list whose vendor is in `SCRAPED` without one. ⚠️ That is what removed
`anandabazar/bengali`: no list was ever located and no client was ever written, so there was no address to give.

⚠️ **And the same rule collapsed the duplication that let this drift happen.** `amazon.NODES`, `indie.LISTS` and
`rokomari.BEST_SELLERS` each held an address *while* the chart declared one, so neither could tell the other it was
wrong — ⚠️ `rokomari/leaderboard` was a slug naming a page that is not the list while the client quietly fetched the
right one. The address now lives in the declaration, and the clients fetch it.

### ⚠️ Two of this ticket's own findings were wrong, and fetching settled both

**1. `/list/38927` is not the list.** The ticket named it as the Rokomari list and said the Best Seller category
"carries no `product` records at all". ⚠️ **The reverse is true**, and both pages were fetched through the product's own
parser:

| URL | `PRODUCT` records | `parse()` rows |
|---|---|---|
| `/book/category/72/best-seller-books` | **60** | **60** |
| `/list/38927` | **0** | **0** |

⚠️ **And the ticket's own evidence says how it went wrong**: it recorded *"flight: 162,588 chars · 39 `/book/<id>` links"*
— and `/list/38927`'s flight is **exactly 162,588 chars**. The links were `<a href>` anchors rather than records, and
their presence was read as proof of a list. ⚠️ That is this ticket's own lesson — *"looking for what I expected to be
there, and reading its absence as proof"* — applied to itself.

**2. `indie/national` is not a fifth drift.** A probe appeared to show the dated address serving a fallback page (200,
identical bytes for three weeks, 0 rank nodes). ⚠️ **The probe used the wrong date** — the Monday rather than
`indie.published_on`'s Wednesday. At the address the client actually builds: **144 rank nodes, 135 rows**, with different
bytes for each of three weeks. ⚠️ The list is real, dated and per-week; nothing needed correcting.

### ⚠️ The registry — the other end of the same wire

⚠️ **`CLIENTS` held one entry (`nyt`) while three clients were written and unregistered.** Its own rule was *"a client is
registered when the lists declared for it resolve"*, and the fetches now say which do:

- ✅ **`amazon-in` registered** — both declared nodes return 30 rows.
- ✅ **`indie` registered** — 135 rows at the address the client derives.
- ⚠️ **`rokomari` deliberately left unregistered** — the list resolves (60 rows) but carries **no date anywhere**, so the
  freshness guard discards every row. ⚠️ Registering it would not make `bengali` build; it would only add a vendor to a
  chart that is absent either way.

⚠️ **That is what gives `english` and `comics` their second vendor** — before this, both built from **NYT alone**, and
the two-vendor gate was never actually exercised.

### ⚠️ One consequence outside this ticket's subject

⚠️ **Ticket 20's example moved.** The Bengali chart was *"the one whose country varies"* (`in`, `bd`); with Anandabazar
gone it is `bd` throughout, and **`comics` is now the chart whose country varies** (`us`, `in`). ⚠️ The *rule* is
unchanged — a label draws only where it varies — and only the chart that demonstrates it changed. ⚠️ Both `copy.ts`
tables gained a `bangladesh` entry, and **`india+bangladesh` was kept**, because a week committed before this correction
still carries it and ADR 0003 promises that a past week re-renders with today's words.

### ⚠️ What is left, and none of it is a declaration

- **The Bengali chart needs a second vendor.** ⚠️ Rokomari alone cannot corroborate anything, so finding Anandabazar's
  weekly list — or any second weekly Bengali ranking — is what would bring the chart back. ⚠️ That is a **search**, not a
  correction, and it belongs to a fresh ticket.
- **Rokomari needs a date.** The list parses and the address is settled; only its vintage is unknown, and ⚠️ that is the
  whole of what stands between this chart and the freshness guard.
- **`amazon-in` is a scrape** contrary to Amazon's terms and ticket 25's single point of failure — now load-bearing for
  `comics`, which is worth re-reading ticket 25 against.

### ⚠️ The evidence

The suite went from **11 failures to zero**, and ⚠️ **all eleven were stale declarations rather than bugs**: they asserted
`amazon-in/hindi`, `indie/fiction`, nine languages, and `amazon-in` as a Bengali vendor. ⚠️ The
`@unittest.expectedFailure` that recorded the ten addressless lists is now a **passing** test, because the lists are gone
and the constructor will not let them back.
