# The worldwide comics market

Type: research
Status: resolved

## Question

*"top 100 comics all over world lang and country mention"* — the comics chart is **worldwide**, not India-market as
ticket 12 had it. So the source set ticket 02 named for it is the wrong one, and this ticket finds the right one.

## Answer

### ⚠️ The finding: a worldwide *weekly* comics ranking has almost no vendors

The trade charts are **monthly**, and that is the whole problem:

| Vendor | Cadence | Scope | Verdict |
|---|---|---|---|
| **NYT `graphic-books-and-manga`** | **weekly** | US, via the Books API — covers and `rank_last_week` | ✅ the one weekly *ranking* vendor |
| **ICv2** Top 50 Comics / Top 20 Graphic Novels | **monthly** | US comic-store POS (ComicHub, Comic Shop Assistant) | ❌ cannot rank a week |
| **Amazon.in** Comics & Graphic Novels | updated frequently | **India** | ⚠️ weekly-capable, but not a *world* view |

⚠️ **So a worldwide weekly ranking has exactly one weekly vendor — NYT — and one vendor cannot corroborate itself**
(ticket 17). As specified, the chart would be **permanently absent**.

### ⚠️ The distinction that rescues it: **ranking and corroboration are different jobs**

Ticket 17 asks whether a title is *real*, not whether two vendors agree about *this week's order*. So:

- **Ranking** comes from the **weekly** vendors — NYT, plus Amazon.in where a title is stocked in India.
- **Corroboration** comes from **any** vendor that carries the title — **including ICv2**, whose monthly chart is
  perfectly good evidence that a comic is a real seller, even though it cannot rank a week.

⚠️ That separates **existence** from **freshness**, and it is the same split ticket 18 already makes: the freshness
guard governs the *ranking* vendors (a chart's spine), while a corroborating vendor only has to *know the title*.

### Consequences

- ⚠️ **The worldwide chart skews US.** NYT is a US list, so a genuinely global weekly ranking does not exist — and the
  chart must **say so** rather than imply coverage it does not have. The **footer's source list** is what makes that
  honest on screen (ticket 07).
- ⚠️ **Indian-only comics lose their place.** A title stocked only on Amazon.in is single-vendor and goes to the
  **watchlist** (ticket 11) — the right outcome for a *worldwide* chart, and the wrong one for the India-market chart it
  replaces.
- ✅ **The country and language labels now genuinely earn their place** — on a worldwide chart both vary a lot, which is
  exactly what ticket 20's table predicted for comics.