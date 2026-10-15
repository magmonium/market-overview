# The comics list, from every country

Type: task
Status: resolved
Blocked by: 33

## Question

The operator's instruction, verbatim:

> from different counrty europe amerika uk india and create list

So the comics chart is to be built from **several countries' own storefronts**, combined into one list — rather than from
one US list and one Indian one, which is what ticket 33 left it with.

## Answer

### ✅ Every store has its own Comics node, and none of the ids could be guessed

⚠️ **Amazon's category node ids are locale-specific.** Ticket 22's mistake was writing a source's properties from
assumption, so none of these were assumed: each store's **own Books bestsellers page** was fetched and its comics
sub-category link read off it.

| Store | Node | The store's own word for it |
|---|---|---|
| `amazon.com` | `4366` | Comics & Graphic Novels |
| `amazon.co.uk` | `274081` | Comics & Graphic Novels |
| `amazon.ca` | `13932641` | Comics & Graphic Novels |
| `amazon.de` | `287621` | Comics & Manga |
| `amazon.fr` | `301133` | Comics |
| `amazon.it` | `508784031` | Comics & Graphic Novels |
| `amazon.es` | `902516031` | Comics & Graphic Novels |
| `amazon.in` | `1318104031` | Comics & Mangas |
| `amazon.com.au` | `4893847051` | Comics, Manga & Graphic Novels — ⚠️ **verified, not declared** |

⚠️ **Every declared one was then fetched with the product's own client**, and the content checked — not just the status
code:

| Store | Rows | Real ISBN-13s | Priced | Currency stated by the page | First titles |
|---|---|---|---|---|---|
| `amazon-us` | 30 | 22 | **0** | **HUF** | *Dog Man*, *Dungeon Crawler Carl*, *Chainsaw Man* |
| `amazon-uk` | 30 | 28 | **0** | **HUF** | *Bunny vs Monkey*, *Diary of a Wimpy Kid* |
| `amazon-ca` | 30 | 28 | 30 | bare `$` → CAD | *Dog Man*, *The Boy, the Mole…* |
| `amazon-de` | 30 | 29 | **0** | **HUF** | *Gregs Tagebuch 21*, *Lesen NERVT!* |
| `amazon-fr` | 30 | 20 | 30 | `EUR` | *Lou ! Sonata*, *Mortelle Adèle* |
| `amazon-it` | 30 | 24 | 30 | `EUR` | *One Piece*, *Miss Kappa* |
| `amazon-es` | 30 | 28 | 29 | `EUR` | *Policán*, *One Piece nº 01* |
| `amazon-in` | 30 | 26 | 30 | `INR` | *101 Tales…*, *Pee-Ka-Boo* |

⚠️ **The HUF column is not noise — it is ticket 33's bug, still live.** `amazon.com`, `.co.uk` **and `.de`** all price
*this viewer* in **Hungarian forint**, so those rows arrive **without a price** rather than with a wrong one. ⚠️ Three of
eight stores therefore contribute no captions, and that is the correct outcome rather than a gap.

### ⚠️ Two defects found by doing it, and both were *invisible* until the list was widened

**1. A store missing from `MARKETPLACES` prints an unsigned number.** ⚠️ `MARKETPLACES` is what gives a store its
currency, and the four European stores were **not in it** — so their rows carried `currency=""`, the documented *unknown*
degrade, in which the price is **kept** and printed as a bare figure. ⚠️ Measured: `amazon.de` would have shipped
`5711.66` with no symbol at all, which is ticket 19's `₹24.99`-for-`$24.99` failure **one step further from being
visible**. ✅ Fixed by naming all four (`EUR`), and ⚠️ **pinned by a test** — the invariant that every Amazon list a chart
declares is in `MARKETPLACES` *and* in `LIVE` now asserts both halves in one place. ⚠️ The rule was written, tested and
correct; the **table** was what fell behind, and only a test that reads both can notice.

**2. Eight requests in a burst get one of them throttled, and one empty store costs the whole chart.** ⚠️ A tight loop
over the eight storefronts returned **`200`, a valid `<title>`, and no `#gridItemRoot` at all** for `amazon.de` — while
the same address answered **30 ranked cards** a few seconds later. ⚠️ A store that produces no rows is a **missing
source**, and ticket 18 makes a chart with a missing source **absent** — so the failure was not "one country missing",
it was **no comics chart**. ✅ `amazon.fetch` now pauses `PAUSE_SECONDS = 1.5` **between** requests (never before the
first). ⚠️ **A pause and not a retry**: a retry would hide *"this store answered nothing"* behind a second attempt and
make a real outage look like latency, and the failure must stay visible.

### ✅ What is declared, and what is deliberately not

- ✅ **Declared**: NYT's `graphic-books-and-manga` (monthly, ticket 33) plus **eight storefronts** — `amazon-us`,
  `amazon-uk`, `amazon-ca`, `amazon-de`, `amazon-fr`, `amazon-it`, `amazon-es`, `amazon-in`.
- ⚠️ **Not declared: `amazon.com.au`** (`4893847051`, 30 cards, 26 ISBNs, `AUD`). It resolves and it is one line — and
  **Australia is not one of the four regions the operator named**. Declaring it would be a *choice presented as an
  instruction*, which is the shape of mistake this chart's history is made of. ⚠️ Add it when someone asks for Oceania.
- ❌ **Not declared: the Kindle node** (`…/zgbs/digital-text/156104011`) — 0 of 30 ASINs are ISBNs, and single issues
  rotate weekly.
- ❌ **Not declared: the StoryGraph / League of Comic Geeks Top 100** — no ranks, no date, no ISBNs.

### ⚠️ The languages, and why the label finally draws here

⚠️ **Each list declares its own country *and* language**, because a storefront ranks **its own country's editions** —
which the titles confirm: *Gregs Tagebuch* (DE), *Lou ! Sonata* (FR), *One Piece* (IT), *Policán* (ES). ⚠️ So ticket 20's
language label turns **on** for this chart for the first time: it has five values where it had one. ⚠️ The *country*
label already drew here (`us`, `in`) and now has eight values.

### ✅ The evidence

Through the product's own `fetch` (so the pauses apply), with the recorded NYT list replayed:

```
nyt/graphic-books-and-manga   15 rows  (recorded, dated 2026-10-03)
amazon-us/comics              30 rows  22 ISBN-13s   0 priced
amazon-uk/comics              30 rows  28 ISBN-13s   0 priced
amazon-ca/comics              30 rows  28 ISBN-13s  30 priced ['CAD']
amazon-de/comics              30 rows  29 ISBN-13s   0 priced
amazon-fr/comics              30 rows  20 ISBN-13s  30 priced ['EUR']
amazon-it/comics              30 rows  24 ISBN-13s  30 priced ['EUR']
amazon-es/comics              30 rows  28 ISBN-13s  29 priced ['EUR']
amazon-in/comics              30 rows  26 ISBN-13s  30 priced ['INR']

guard kept 255 of 255 rows; missing vendors: none
admitted 225 distinct titles
countries: {'us': 18, 'gb': 29, 'ca': 30, 'de': 30, 'fr': 30, 'it': 30, 'es': 29, 'in': 29}
languages: {'en': 106, 'fr': 30, 'de': 30, 'it': 30, 'es': 29}
carried by more than one list: 22
```

⚠️ **The union is what makes the list**: `Absolute Batman Vol. 1` is carried by **Canada, India and the US**,
`Absolute Batman Vol. 3` by **Canada, the US and NYT**, and **22 titles** are carried by more than one list — ticket 17's
corroboration, visible across eight countries. ⚠️ `rank.LIMIT = 100`, so 225 admitted titles fill a full Top 100.

### ⚠️ What this costs a run

- ⚠️ **Thirteen Amazon requests per gather** — eight for `comics`, four for `english`, one for `all-language` — and about
  **4 MB** of committed evidence, against `PAUSE_SECONDS` between each. ⚠️ The pause is the price of not being throttled,
  and it is paid **per chart**, so a chart with one store does not pay for another's eight.
- ⚠️ **Enrichment scales with the union, and it is now *measured* rather than predicted** (2026-10-15, the first
  re-gather that carried all four charts): `_details` makes **one Google Books call and one cover fetch per admitted
  title**, and the week's four charts admit **~600 titles** — so the run logged
  `google books did not answer: HTTP Error 429: Too Many Requests — 256 of the week's titles`. ⚠️ **That is ticket 05's
  documented degrade, not a new failure** — the rows keep everything their own list stated, the missing fields **omit**,
  and the covers fall through to Open Library — ⚠️ but it is the first time the *whole week* has been at the anonymous
  quota, and a **Google Books key** (or a longer pause) is what would fix it.
- ⚠️ ⚠️ **And the upload text did not fit — now fixed, and the measurement is what fixed it** (ticket 36). The re-gather
  built the comics chart and then **refused to package it**:

  ```
  books_brief.metadata.MetadataError: the description is 9295 characters, over the 5000 YouTube keeps —
  shorten the rows rather than shipping a list whose tail is cut off
  ```

  ⚠️ **The refusal is the design working** (ticket 15: *"a list that will not fit is a list to shorten"*), and ticket 32
  already records the **English** chart refusing at **7,677**. ⚠️ Measured against the real snapshot, the ways to shorten
  it are:

  | Shape | Characters | |
  |---|---|---|
  | current — top 10 full, tail `rank. title — author` | **9,332** | ❌ over by 4,332 |
  | tail drops the author (`rank. title`) | 9,059 | ❌ over by 4,059 — ⚠️ **almost nothing**, because the *titles* dominate |
  | tail = `rank. title` truncated to 45 | 5,198 | ❌ over by 198 |
  | **every row `rank. title` truncated to 45** | **4,754** | ✅ fits |

  ⚠️ **So the problem is the titles, not the fields**: comics titles are long (*The Long-Lived King: An Original The Owl
  House Graphic Novel*), and a 5,000-character description holds **100 of them only at about 45 characters each**.

