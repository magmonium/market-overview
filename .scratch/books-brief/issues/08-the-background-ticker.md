# The background ticker

Type: grilling
Status: resolved
Blocked by: 06

## Question

*"In background there will be misc like stock brief"* — what exactly, and where does it come from?

The cheap, elegant answer: **reuse the existing brief's `facts.json`** — its index scoreboard is already computed,
already committed per date, and already has a bilingual label table. But that couples `books-brief` to whether the
brief ran that day.

1. **Reuse the brief's `facts.json`** for the date — free, but needs the brief to have run.
2. **Fetch independently** through the same `fetch/tradingview.py` client — decoupled, one more moving part.
3. **Static / decorative** — a texture, not live numbers — no data dependency at all.

⚠️ **The layout reserves your region** (ticket 07): a **band in the lower frame, below the book block and above the
footer**, sitting in the part of the scrim that is thinnest — which is exactly where the backdrop is meant to show
through. The ticker must read as *background*: `MUTED`, tabular numerals, never competing with the book.

⚠️ The ticker must also stay out of the **top-right `260 × 160` mark region** and off the footer's disclosure register.

Also to settle: which indices appear, how they are styled so they read as *background* and never compete with the
book, and what happens on a week the market data is missing or stale.

## Answer

### Depend on the **library**, not on another product's **artefact**

The host repo already sanctions the sibling direction: `song-video`'s `pyproject.toml` says *"The one dependency is the
brief itself, on purpose"* and pulls `market-overview` in as an **editable path source**, reusing
`market_overview.logo` and `market_overview.audio`.

But there are two different things to depend on, and they are **not** equivalent:

| Depend on | It is | Verdict |
|---|---|---|
| `market_overview.fetch.tradingview` — the **client** | a library | ✅ **chosen** |
| `store/<date>/facts.json` — the brief's **run artefact** | another product's output | ❌ |

⚠️ Reusing the brief's committed `facts.json` would save one HTTP call and buy a **failure mode with no upside**:
books-brief could not run on a day the brief did not. And the ticker must be *as of **this** run*, not as of whatever
the brief last did.

### So: fetch independently, snapshot it, and date it

- Fetch the index scoreboard through **`market_overview.fetch.tradingview`** — same client, same tickers.
- Commit the raw response as `store/<week>/raw/tradingview.json`, **before parsing** — the brief's evidence habit.
- ⚠️ **The band carries the session clock.** Reuse the brief's `stamps()` idea: the session open and last-update from
  the clock row (`NSE:NIFTY`). A ticker that cannot say *when* it is from is a ticker that can lie.

### Which rows

The brief's **index scoreboard** — `NSE:NIFTY`, `NSE:CNX500`, `NSE:BANKNIFTY`, `BSE:SENSEX`, `NSE:NIFTYJR` — which is
already a stock brief in miniature. Label keys follow the brief's discipline: **stable slugs in `facts.json`, display
strings in the renderer's label tables** (ADR 0003), so a vendor renaming a symbol is a one-line change.

⚠️ If `*INR` pairs are ever added (USDINR, EURINR…), they must use `NEUTRAL`, **not** `tone()` — for a currency pair
*up* means the rupee is **weaker**, so colouring by sign would say the opposite of the truth. That is the brief's own
rule and it transfers unchanged.

### ⚠️ Missing data: degrade — and deliberately *unlike* the brief

The brief treats a short index scoreboard as **fatal**: `facts.build()` raises `MissingTickersError`, because *"an
unresolvable index comes back as an absent row with HTTP 200 and no error, so a short scoreboard is otherwise
completely silent"*. For the brief, the scoreboard **is the content**.

⚠️ **For us it is decoration, so it must not be fatal.** A failed fetch **omits the band entirely** — never zeros,
never stale, never a placeholder. That is still the brief's *degrade to omission* principle; only the **abort
threshold** moves, because the ticker is background. The layout absorbs the omission without a hole, because the book
block is `flex: 1`.

### What this hands to ticket 09

⚠️ books-brief depends on `market_overview` as a **library** (editable path source), inheriting its dependency tree
(`curl_cffi`) — the same explicit trade `song-video` documents. Flagged into ticket 09, which owns where it lives.

### Aside recorded for ticket 15

`song-video` already ships **`seo.py`** — prior art for the title / description / tags work.
