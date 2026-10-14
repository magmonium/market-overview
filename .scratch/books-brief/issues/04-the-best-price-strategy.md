# The best price strategy

Type: research
Status: resolved
Blocked by: 02

## Question

**This is the one requirement with no free, legal, multi-retailer feed.** Every candidate is paid, gated, or a
ToS-violating scrape:

- **Amazon PA-API 5.0** — real prices, but requires an **approved Associates account with qualifying sales**, which
  is not a cold start.
- **Google Books `saleInfo.retailPrice`** — Google Play only, and only if the `country` is honoured.
- **NYT `price` / PW price** — the **publisher list price** as a string, not a comparison.
- **bookbargain** (India) — MIT, but Python 2, `mechanize`, and it admits it ignores `robots.txt`.
- **Direct retailer scraping** (Flipkart / Amazon.in / Crossword) — ToS risk, and a maintenance treadmill.

## Deliverable

A decision on what *"best price"* means for this product and where it comes from. *"It is the publisher list price,
labelled as such"* is an acceptable outcome — but it has to be a **choice**, not an accident. State the currency
(INR / USD), whether the price is per-format (hardcover vs ebook), and what renders when no price is found.

## Answer

### ⚠️ The governing principle, first

**Never label a price "best" unless it was actually compared.** The brief asks for the *best price*; the honest
version of that is *the lowest price we could verify, with the retailer named*. If only one retailer's price is known,
the slide says **"₹399 · Amazon"** — never **"Best price ₹399"**. That is the same discipline as the corroboration gate
(ticket 17): **the label must not claim more than the data supports.**

### Where prices actually come from

| Source | Retailer | Cost | Verdict |
|---|---|---|---|
| **Amazon.in** bestseller listing — *"N offers from ₹X"* | Amazon | **free — already fetched for the chart** (ticket 02) | ✅ the workhorse. ⚠️ The **lowest offer** across sellers, and **absent on some items** |
| **Flipkart Affiliate API 1.0** (Product + Offer APIs) | Flipkart | free, but requires **registered-affiliate** approval | ✅ the second retailer that makes "best" *mean* something |
| **Google Books `saleInfo.retailPrice`** | Google Play | free, no auth | ⚠️ **ebooks only**, country-dependent — a third opinion, rarely the print price |
| **NYT `price` / PW price** | — | free | ⚠️ the **publisher's list price**, a string. A fallback, never a comparison |
| **Amazon PA-API 5.0** | Amazon | needs an **approved Amazon Associates account** (plus the widely-reported qualifying-sales threshold) | ❌ not a cold start |
| **bookbargain** | Flipkart, Amazon.in, Crossword… | MIT | ❌ Python 2, `mechanize`, admits it ignores `robots.txt` |
| **Direct retailer scraping** | any | free | ❌ ToS risk and a maintenance treadmill |

### The decision

**"Best price" = the lowest verified offer across the retailers we can legitimately reach, with the retailer named.**

1. **Primary — Amazon.in's lowest offer.** ⚠️ It arrives **free with the chart source**: the bestseller listing already
   carries *"N offers from ₹X"*, so the price costs **no extra fetch**. The lowest offer across Amazon's sellers is a
   real market price in INR.
2. **Second retailer — Flipkart Affiliate API.** This is what turns *a* price into *the **best*** price. ⚠️ It requires
   **affiliate registration and approval** — an **operator prerequisite**, like the NYT key and the logo, not something
   code can conjure.
3. **Corroboration — Google Books `retailPrice`** where a digital edition exists. It rarely carries the print price, so
   it confirms rather than leads.
4. **Fallback — the publisher's list price**, ⚠️ **labelled MRP**, never "best price".

### The rules that keep it honest

- **Currency: INR**, always — all four charts are India-market (ticket 12).
- **The format is named on the slide.** The price follows the format the chart's source lists (Amazon.in's comics list
  is *Kindle* eBooks; the book charts are print). **A price without its format is not a price.**
- ⚠️ **A missing price renders as a dash — never ₹0, never a guess.** The host repo already holds this line:
  `facts.py` refuses to coerce a missing vendor number to zero, because *"a missing value and a real zero are different
  facts"*.
- ⚠️ **Price is not a ranking input.** The chart ranks sales (tickets 03, 17); a cheap book does not rank higher. Price
  is a caption, not a signal.

### ⚠️ The honest limitation

Even with Flipkart, "best price" means **best price across Amazon and Flipkart** — not across every Indian retailer.
The spec should say that in one sentence rather than implying a comprehensive comparison.

### ⚠️ ⚠️ Amended — the price has no **currency**, and one of the two countries does not use rupees (2026-10-14)

⚠️ **This ticket decided *which* price to show and never asked *what it is denominated in*.** Recording Rokomari settled
that it matters: a Bengali bestseller list from **Bangladesh** quotes **৳180 — Taka**. And `prices.Price` carries
`amount`, `retailer`, `edition` and `retailers`:

⚠️ **There is no currency field anywhere in the model**, and the renderer's `rupees()` draws `₹` unconditionally —
`format.ts:39`, used at `:110` for every price line.

⚠️ **So a Bangladeshi price would print as `₹180` when it is `৳180`** — wrong by roughly a factor of one and a half, on a
chart whose whole premise (ticket 20) is that the Bengali market spans **India and Bangladesh**. ⚠️ And it would do it
while looking completely correct.

⚠️ **Nothing would fail.** The amount parses, the slide renders, the description writes it, and the only way to catch it
is to already know that a Bangladeshi book costs Taka — which is precisely the knowledge the committed evidence exists to
supply rather than to assume.

⚠️ **The remedy is ticket 20's, applied to money**: the **value** belongs in the snapshot and the **symbol** belongs to the
renderer (ADR 0003). A `currency` on `prices.Price` — `inr`, `bdt` — with `format.rupees` becoming a table keyed by it, is
a small change. ⚠️ What is not small is deciding it late: a week committed with `₹180` for a Taka price has **wrong
evidence**, and re-running it would not fix the number, because the number was never the problem.

⚠️ **This is latent rather than live** — Rokomari is the only Taka source in the set and the Bengali chart cannot build
yet. ⚠️ That is the only reason it is an amendment and not an incident, and it is exactly the kind of thing that stops
being latent the moment someone fixes the declarations.

⚠️ **And it is the third assumption this session that the recordings caught and reasoning did not** — after the price
selector and the missing book records. ⚠️ All three had the same cause: **a field nobody asked about, because it had
always been the same.**
