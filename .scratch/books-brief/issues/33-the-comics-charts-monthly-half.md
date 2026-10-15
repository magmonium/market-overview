# The comics chart's monthly half — and the operator's answer to it

Type: task
Status: resolved
Blocked by: 22

## Question

`./build books` was asked for `2026-W41` and `comics`, and answered:

```
books · 2026-W41 · comics
comics: not in this week's bundle — it could not be built
```

⚠️ The chart was **not** missing a source. Replayed from the week's own recorded responses, **Amazon.in answered it
thirty rows**, and the guard still called the chart absent. So the question is not *"where is the comics source?"* — it is
**"why does a chart with an answering source go absent?"**

⚠️ The operator then supplied a source and a directive: an Amazon.com comics address, a StoryGraph list, and
**"combine all links available and create the best list every week."**

## Answer

### ⚠️ The chart was absent because ticket 22's cadence table has one wrong cell

Ticket 22 is the ticket the comics chart was built on, and its source table says:

| Vendor | Cadence | Scope | Verdict |
|---|---|---|---|
| **NYT `graphic-books-and-manga`** | **weekly** | US, via the Books API | ✅ the one weekly *ranking* vendor |

⚠️ **The recorded payload says `"updated": "MONTHLY"`**, and dates the list to the **first Saturday of the month**:
`bestsellers_date: 2026-10-03`. ⚠️ `freshness.span("2026-W41")` is `2026-10-05 … 2026-10-14`, so the list is **four days
"stale" on the very week it describes** — and ticket 18's rule turns a stale vendor into an **absent chart**:

```
nyt/graphic-books-and-manga: 15 rows, dated 2026-10-03      → all 15 dropped
amazon-in/comics: 30 rows (LIVE, exempt)                    → kept
guard: kept 30 rows; missing vendors: ('nyt',)              → comics absent
```

⚠️ Measured, that is **one week in four**:

```
2026-W39 ('2026-09-21', '2026-09-30') STALE
2026-W40 ('2026-09-28', '2026-10-07') fresh    ← the week 2026-10-03 falls in
2026-W41 ('2026-10-05', '2026-10-14') STALE
### ⚠️ And the same replay found a **wrong number live in a shipped bundle**

⚠️ Chasing *"combine all links"* meant fetching Amazon's comics pages, and the fetch returned prices no dollar sign could
describe. The recorded `2026-W41` pages say why:

| Recorded page | Price nodes | `MARKETPLACES` said | The bundle claims |
|---|---|---|---|
| `amazon-us-english.html` | **`HUF 7,249.11`** | USD | **`$7,249.11`** — 13 rows |
| `amazon-uk-english.html` | **`HUF 3,213.63`** | GBP | **`£…`** — 21 rows |
| `amazon-ca-english.html` | `$33.60` | CAD | CAD ✅ |
| `amazon-au-english.html` | `$18.00` | AUD | AUD ✅ |
| `amazon-in-comics.html` | `₹329.00` | INR | INR ✅ |

⚠️ **Amazon.com and Amazon.co.uk price the *viewer*, not the store**, and the constant `MARKETPLACES` — written on the
premise that *"each marketplace quotes its own currency"* — labelled **34 rows of the English chart** with a currency the
page never stated. ⚠️ That is ticket 19's own named failure (the `₹24.99`-for-`$24.99`) **live in the committed week**,
and ticket 19's test was its alibi: it parsed the *Indian* fixture as `amazon-uk` and asserted `GBP`, encoding *"the
declaration wins"* as a virtue so that nothing ever asked what the page said.

### ✅ The links, each fetched, and what each one can contribute

| Address | Status | Content | Verdict |
|---|---|---|---|
| `…/zgbs/digital-text/156104011` (operator) | 200, 30 ranked cards | **Kindle single issues** (`DNX (2026-) #3 (of 5)`), **0 of 30 ASINs are ISBNs** | ❌ **not declared** — no identity, and the titles rotate weekly |
| `…/gp/bestsellers/books/4366/` (**found**) | 200, 30 ranked cards | **print** — Dog Man, Chainsaw Man, Coraline, **22 of 30 real ISBN-13s** | ✅ **declared** as `amazon-us/comics` |
| `…/books/1318104031/` (declared) | 200, 30 ranked cards, **26 ISBN-13s** | the page's own h1 is *"Bestsellers in Comics & Graphic Novels"*; the rows are `101 Tales: The Great Panchatantra Collection`, `Pee-Ka-Boo \| Pop-Up Baby Animals` | ⚠️ **kept** — the address is the vendor's own statement of what the list is |
| StoryGraph reading challenge (operator) | 200 to `curl_cffi` (403 to a plain fetcher) | *"The League of Comic Geeks Top 100 Comics and Manga"* — **12 titles server-rendered of 100, titles + authors only** | ❌ **not declared** — **no ranks, no date, no ISBNs**: a checklist cannot rank a week |
| `leagueofcomicgeeks.com/comics/top-comics`, `/comics/best-sellers` | **404** | — | ⚠️ only `/comics/new-comics` resolves (dated `2026-10-14`) |

### What changed

1. ⚠️ **`amazon.parse` verifies the currency the page states instead of assuming it** (`amazon.CURRENCIES`). A stated
   currency that contradicts the declaration **drops the price and keeps the row** — a wrong number is worse than a
   missing field (ticket 07). ⚠️ **A bare `$` is still not evidence**, so `MARKETPLACES` still decides which dollars, and
   the tests keep that property with a recording that really does print one (`tests/fixtures/amazon-ca-english.html`).
2. ⚠️ **`charts.Listing.cadence`** (`"weekly"` default, `"monthly"` opt-in, refused if unrecognised) and
   **`freshness.guard(monthly=…)`**, which measures a monthly list against **the month the week falls in**. ⚠️ A
   *previous* month is still stale, so the guard keeps its meaning — and the parameter takes **list** slugs where `live`
   takes **vendor** slugs, because cadence belongs to the list.
3. ⚠️ **`comics` declares three vendors** — `nyt` (monthly), `amazon-us` (live, node 4366), `amazon-in` (live) — and the
   NYT list is declared `cadence="monthly"`.
4. ⚠️ **The English chart's 34 wrong-currency rows are recorded, not repaired**: `facts.json` for `2026-W41` is a
   *replayed* snapshot (ADR 0003), so the fix lands with the **next week gathered**, or with a deliberate re-gather.

### ✅ The evidence

Replayed from the committed week, with the new list fetched live (2026-10-15):

```
comics vendors: ('nyt', 'amazon-us', 'amazon-in')
span (weekly): ('2026-10-05', '2026-10-14') | span (monthly): ('2026-10-01', '2026-11-03')
nyt/graphic-books-and-manga: 15 rows, dated 2026-10-03
amazon-us/comics (live, 200): 30 rows, 22 ISBN-13s, 0 with a price
amazon-in/comics (recorded): 30 rows, 26 ISBN-13s, 30 with a price
guard kept 75 rows; missing vendors: none
admitted 67 titles from 75 rows
```

⚠️ **And the union does real work**: `Absolute Batman Vol. 3` is carried by `amazon-us/comics` **and**
`nyt/graphic-books-and-manga`, and `Absolute Batman Vol. 1` by `amazon-in/comics` **and** `amazon-us/comics` — ticket 17's
corroboration, now visible across the chart's three lists.

⚠️ **Two consequences an operator should know before publishing it.** The US rows carry **no price** (their amounts were
HUF, so they are dropped rather than mislabelled), and the Indian half is **Amazon.in's own node content** — children's
and activity books sit in it beside comics. ⚠️ Both are visible in the chart rather than hidden by it, which is the
product's rule, but neither is what a reader expects of a *comics* chart.

⚠️ **And the week is still recorded.** `2026-W41` has a snapshot, so asking it for `comics` will keep answering *"not in
this week's bundle"* until the week is re-gathered or a later week is built — the snapshot's existence is the switch
(ADR 0003), and this ticket does not change that.

### ⚠️ What is *not* the answer

- **Declaring the Kindle node** (`156104011`) — 0 of 30 ASINs are ISBNs, so every row would key as `title|` (ticket 32's
  work key with no author), on single issues that rotate weekly. ⚠️ A chart of one-week-only rows is a *different chart*,
  not a bigger one.
- **Declaring the StoryGraph challenge** — no ranks, no date, no ISBNs, and 12 of its 100 titles are in the HTML.
- **Exempting `nyt` as a `LIVE` vendor** — that would excuse `hardcover-fiction` and `hardcover-nonfiction` too, which
  *are* weekly and *should* be checked. ⚠️ Cadence belongs to the list, which is why it is declared there.

2026-W42 ('2026-10-12', '2026-10-21') STALE
2026-W43 ('2026-10-19', '2026-10-28') STALE
```

⚠️ **So this was never a sourcing failure** — it is the same shape as ticket 30's finding: the *guard* was read correctly
and the *source* was read wrongly.
