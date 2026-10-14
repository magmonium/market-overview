# 0001 — The four charts, and the markets they actually cover

- Status: accepted
- Date: 2026-10-14

## Context

The brief asked for four Top-100 charts — **Bengali**, **English**, **Indian all-language** and **Comics** — and the
natural first reading is that all four are *India-market*. That reading survived until the sources were actually
looked at.

Three findings killed it:

- ⚠️ **Almost nothing Indian is weekly.** Amazon.in's bestseller lists are the workhorse; Anandabazar Patrika publishes
  the *only* weekly Bengali chart; the Nielsen India list is on sabbatical; Dainik Jagran's Hindi list is **quarterly**;
  ICv2 is **monthly**. A weekly product and an India-only scope are in tension, and the tension had to be resolved
  rather than absorbed.
- ⚠️ **India-market English cannot be built at all.** It has exactly **one** weekly vendor, and ADR 0004 requires two.
  The chart would be permanently absent — not weak, *absent*.
- **The brief then moved two boundaries itself**: the Bengali chart was asked to include **Bangladeshi** titles, and
  the comics chart to be **worldwide**.

## Decision

Four charts, and each one's market is what its sources can honestly support:

| Chart | Market | Why |
|---|---|---|
| **Bengali** | **India and Bangladesh** | what the language spans; the brief asked for it |
| **English** | **US** | NYT, PW and Indie Bestsellers are all US lists — the only weekly English vendors that exist |
| **Indian all-language** | **India** | Amazon.in's per-language categories, which is one vendor |
| **Comics** | **Worldwide** | NYT's `graphic-books-and-manga` plus Amazon.in |

⚠️ **And every chart states its scope** — the **footer's source list** and the **description's attribution** name the
vendors, so a reader can see what was and was not consulted.

## Consequences

- ⚠️ **Three charts carry a scope caveat, and that is the product's honest shape rather than three defects.** A weekly
  chart built from free sources is a **US-and-India view of the world**; saying so is what makes it trustworthy.
- ⚠️ **"Global" is never claimed.** The English chart is *US* English and the comics chart *skews US*, because calling
  either "global" would claim coverage no free weekly source provides.
- ⚠️ **The all-language superset holds over the Indian portion only.** A Bangladeshi Bengali title sits in the Bengali
  chart and **not** in the all-language chart, so the Bengali chart carries an **overhang** — and the dedupe key is
  **chart + ISBN**, never ISBN alone.
- ⚠️ **The country and language labels render only where they vary** (ADR 0005's sibling rule), which is why the
  English chart shows neither.
