# The Bangladeshi Bengali market

Type: research
Status: resolved
Blocked by: 20

## Question

Ticket 02 named the Bengali chart's sources — and **every one of them is Indian**: Anandabazar Patrika's weekly list
and Amazon.in's Bengali category. A chart that includes **Bangladeshi** titles needs Bangladeshi sources, and they are
a different set entirely.

To find, and to state plainly:

- **A Bangladeshi Bengali bestseller source.** The counterparts of Anandabazar are the Dhaka papers and the **Ekushey
  Boi Mela** ecosystem — and the first question is which of them publishes a **weekly** list at all.
- ⚠️ **Whether it is weekly.** Ticket 02's headline finding was that *almost nothing Indian is weekly*. Bangladesh may
  be worse, and a monthly list — or a Boi-Mela-only one — cannot feed a weekly chart.
- **Amazon.in's coverage of Bangladeshi titles.** It is an Indian storefront; whether it stocks and ranks Bangladeshi
  publishers decides whether the two countries can be merged into **one** ranking at all.
- **The retail reality.** Bangladesh's book market runs through **Rokomari**, Boi Mela and Dhaka's Nilkhet — not Amazon.
- ⚠️ **The corroboration consequence** (ticket 17). Two vendors are required, and if the Indian and Bangladeshi vendors
  never overlap, **no title is corroborated** — the same trap the all-language chart is already in.

## Deliverable

The Bangladeshi source set, its cadence, and an honest statement of whether a **merged India + Bangladesh Bengali
chart** can be corroborated at all — or whether it is two charts, or one chart marked single-source.

## Answer

### ⚠️ The finding: Bangladesh has no *weekly editorial* chart

Ticket 02's Bengali sources are all Indian, and the search for Bangladeshi counterparts found a **different shape of
thing**. What exists:

| Candidate | What it actually is | Verdict |
|---|---|---|
| **Rokomari** — Bangladesh's largest online bookstore, with a **leaderboard** and a **Bestseller Award** | a **retailer's own popularity ordering**, not an editorial chart. ⚠️ **403 to a plain fetcher** — the `curl_cffi` pattern again | ✅ usable, with caveats |
| **Boi Mela** (Ekushey Boi Mela) | annual / festival seller data | ❌ not weekly |
| **BookVandar** "Best Selling Books" | ⚠️ **not a chart at all** — a merchandising category sorted by popularity, whose own copy says the books are *worldwide* bestsellers | ❌ not a source |
| **Prothom Alo**, **New Age** | they **report on** bestsellers (awards, features) | ❌ no weekly ranked list |
| **Nielsen BookData** | UK and US | ❌ not Bangladesh |

⚠️ The honest statement is therefore: **Bangladesh has no verified weekly Bengali bestseller chart.** Rokomari is the
only weekly-capable Bangladeshi vendor, and it is a *retailer ranking its own sales* — precisely the "single vendor,
gameable" case ticket 17 exists to guard against.

### ⚠️ And the vendors do not overlap — so the merged chart works in **one direction**

Rokomari is Bangladeshi; Amazon.in is an Indian storefront. So:

- **An Indian Bengali title**: Anandabazar + Amazon.in = **2 vendors** ✅
- **A Bangladeshi Bengali title**: Rokomari **alone** = **1 vendor** ❌ → the **watchlist** (ticket 11)

⚠️ **Rokomari is still worth adding, because it is the bridge.** A Bangladeshi title that Amazon.in *also* stocks has
**Rokomari + Amazon.in** = two vendors and is admitted. Without Rokomari it would have one.

### ⚠️ What the chart must therefore say

The merged Bengali chart is achievable, and its **Bangladeshi portion is thin by construction** — it holds only the
Bangladeshi titles that also have **Indian retail presence**. A chart called *"Top 100 Bengali Books"* that quietly
covered that would be implying a Bangladeshi coverage it does not have.

So, exactly as the comics chart (ticket 22) and the English chart (ticket 19) already require: **the footer's source
list and the description's attribution name the vendors**, and the chart **states the boundary**.

⚠️ **Three charts now carry a scope caveat, and that is the product's honest shape rather than three defects.** A weekly
chart built from free sources is a **US-and-India view of the world** — and saying so is what makes it trustworthy.

### The Bengali chart's source set, final

| Vendor | Cadence | Role |
|---|---|---|
| **Anandabazar Patrika** | weekly | the Indian ranking — `curl_cffi` |
| **Amazon.in** Bengali Books | updated frequently | the Indian bridge **and** the Bangladeshi bridge |
| **Rokomari** leaderboard | ⚠️ retailer ordering | the Bangladeshi bridge — `curl_cffi` |

### ⚠️ And it discharges a trigger left in ticket 19

Ticket 19 said its flip to US English was **reversible if a second Indian ranking vendor surfaced here**. ⚠️ **It did
not** — no Indian English weekly list was found. So ticket 19's flip **stands**, and the trigger is **discharged**
rather than left pending.
