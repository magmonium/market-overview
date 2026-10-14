# 0005 — "Best price" names its retailer, and a label never claims more than its data

- Status: accepted
- Date: 2026-10-14

## Context

The brief asks each slide to show the book's **"best price"**. Taken at face value that promises a comparison across
the Indian retail market, and **no free source provides one**:

- **Amazon PA-API 5.0** returns real prices, but needs an **approved Associates account with qualifying sales** — not a
  cold start.
- **Flipkart** has a documented Affiliate API — and it needs affiliate registration and approval, which is an
  *operator* act.
- **Google Books `saleInfo.retailPrice`** is Google Play only, and country-dependent.
- **NYT's `price` and PW's** are the publisher's **list price** — a string, not a comparison.
- **Direct scraping** of Flipkart, Crossword and the rest is contrary to their terms and a maintenance treadmill.

⚠️ And the risk is not that the price is *missing* — it is that the label says **"best"** when only one shop was
consulted. That is a claim larger than its evidence, which is the one thing this product's other decisions (ADR 0004)
exist to prevent.

## Decision

**"Best price" means the lowest verified offer across the retailers we can legitimately reach — and the retailer is
named beside it.**

- **Primary: Amazon.in's lowest offer**, which arrives **free with the chart source** — the bestseller listing already
  carries *"N offers from ₹X"*, so the price costs no extra fetch.
- **Second retailer: the Flipkart Affiliate API**, which is what turns *a* price into *the best* price. ⚠️ Its approval
  is an **operator prerequisite**, not something the code can conjure.
- **Fallback: the publisher's list price**, ⚠️ **labelled MRP** — never "best".
- ⚠️ **The bundle carries the retailers that were compared**, so the renderer can see that one entry means there was no
  comparison to make and simply name the shop.

## Consequences

- ⚠️ **The label can never overclaim, because the fact it needs is in the data.** A slide reading *"Best price ₹399"*
  off a single Amazon listing is now impossible to produce by accident.
- ⚠️ **The format is named too.** The same title differs threefold between paperback, hardcover and ebook, so **a price
  without its format is not a price**.
- ⚠️ **A missing price is a dash, never `₹0`** — the host repo's rule, *"a missing value and a real zero are different
  facts"* — and an offer that *arrives* without an amount is the same case, not a different one.
- ⚠️ **Price is never a ranking input.** The chart ranks sales (ADR 0006); a cheap book does not rank higher.
- ⚠️ **The honest limit is stated**: "best" means **Amazon and Flipkart**, not every Indian retailer.
