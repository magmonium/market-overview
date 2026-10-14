# The English chart's market, revisited

Type: grilling
Status: resolved

## Question

Ticket 12 resolved the English chart as **India-market**, on coherence grounds. Ticket 02's research has now produced
evidence that pushes the other way:

- **India-market English** has essentially **one** usable weekly source — Amazon.in. The authoritative-looking Indian
  lists are dormant (Nielsen/HWR *"on sabbatical"*) or the wrong cadence (Dainik Jagran + Nielsen Hindi is
  **quarterly**).
- **Global English** has **three** weekly sources with `rank_last_week` built in — NYT Books API, Publishers Weekly
  (Circana), Indie Bestsellers — and is free to read.

⚠️ The brief's own standing preference is *"check as many sources as possible"* before the list is made.
**India-market English cannot satisfy that**: one source cannot corroborate itself, and the corroboration gate
(ticket 17) would have nothing to work with. The chart would be the weakest of the four *by construction*.

⚠️ **Strengthened again — the coherence argument for India-market English has collapsed.** Ticket 12 justified it with
*"a NYT hardcover #1 is not comparable to an Amazon.in #1"*, but the product is no longer uniformly Indian: the
**Bengali chart spans India and Bangladesh** (ticket 20) and the **comics chart is worldwide** (ticket 22). The reason to
keep English Indian is therefore gone, while the reason to make it global — **three weekly vendors that already carry
`rank_last_week`** — remains.

## Options

1. **Flip to global English** — NYT + PW + Indie Bestsellers. Rich, weekly, corroborating, and the strongest chart in
   the set. *(now recommended)*
2. **Keep India-market English** — accept that this chart is single-source and therefore the **weakest** of the four,
   and say so in the spec rather than pretending it is corroborated.
3. **Both** — a global English chart as the headline, with an India-market view as a secondary block.
4. **Global chart, Indian product** — the English chart is global, while the branding, ticker and the other three
   charts stay Indian.

## Answer

### ⚠️ Flip to global English — and the honest name for it is **US English**

Three things now point the same way, and one of them is fatal to the alternative:

1. ⚠️ **India-market English cannot be built.** Ticket 17 requires **two vendors**; ticket 02 found exactly **one**
   (Amazon.in). The chart would be **permanently absent** — not weak, *absent*.
2. ⚠️ **The coherence argument for keeping it Indian has collapsed.** Ticket 12 justified India-market with *"a NYT
   hardcover #1 is not comparable to an Amazon.in #1"* — but the product is no longer uniformly Indian: the **Bengali
   chart spans India and Bangladesh** (ticket 20) and the **comics chart is worldwide** (ticket 22).
3. ✅ **Global English has three weekly vendors**, all free, all carrying `rank_last_week`: the **NYT Books API**,
   **Publishers Weekly (Circana)** and **Indie Bestsellers (ABA)**. That is the richest, best-corroborated source set on
   the map — and the only chart that gets **three** vendors rather than two.

### ⚠️ But "global" is a claim these sources cannot support — so say **US**

⚠️ **NYT, PW and Indie Bestsellers are all US lists.** There is no weekly vendor for UK, Australian, Indian or Nigerian
English. A chart built from them is therefore **US-market English**, which happens to be the largest English-language
market. Calling it "global" would be the same overclaim the comics chart is warned against (ticket 22) — and the remedy
is the same: **the footer's source list and the description's attribution name the sources**, so the reader can see the
scope for themselves.

### What changes

- **The source set** becomes NYT + PW + Indie Bestsellers; ticket 02's India-market English line is **superseded**.
- ⚠️ **The two-vendor rule is satisfied with room to spare** — three vendors means one can be missing and the chart
  still ships (ticket 18's spine rule, met comfortably).
- ⚠️ **Neither new label renders on this chart.** A US list's rows are all US, so the country slot stays empty; the
  language is in the header. By ticket 20's rule that is **correct rather than a gap** — the English chart is the one
  chart where *neither* of the brief's labels appears, and that is the rule working.
- **The title is unchanged in shape** — `Top 100 English Books | Week 41 | …` — but the **description's attribution**
  must name the sources.

### ⚠️ One thing that would reverse this

**If ticket 21's research surfaces a second Indian English ranking vendor** — a weekly Crossword or similar list —
India-market English becomes viable again. So the flip is **reversible**, and the trigger is named here rather than left
to memory.

### ⚠️ Amended — one of the three premises was wrong, and the conclusion survives (2026-10-14)

This ticket's case rests on *"three weekly vendors, **all free**, all carrying `rank_last_week`"*. ⚠️ **Fetching them
showed that is two out of three:**

- ✅ **NYT** — free, keyed, weekly, and already implemented.
- ✅ **Indie Bestsellers** — free to view, and a **real list**: `indiebound.org/indie-bestsellers`, 361 KB, 79 ranked nodes.
- ⚠️ **Publishers Weekly** — **paywalled**. The free pages under `/pw/bestsellers/` are an **archive**: the only date on
  `hardcover-fiction.html` is **05/28/2012**, the page points at *"the Bestseller Archive"* and asks the reader to
  subscribe, and its own login blurb says *"You are NOT a current subscriber."*

⚠️ **The conclusion holds and the margin narrows.** Ticket 17 needs **two** vendors, and NYT + Indie are two — so
US English is still the only chart that reaches the gate without a single source being asked to corroborate itself.
⚠️ But it does so **only once PW is removed from the declaration**: a declared vendor whose client answers nothing is a
**missing source**, and a chart missing a source is **absent** — which is exactly the outcome this ticket flipped the
chart to avoid.

⚠️ **And the "three vendors means one can be missing and the chart still ships" line above is now wrong.** With two, the
chart ships only while *both* answer — a materially thinner margin than this ticket claimed, recorded here rather than
left for a run to discover. The ticket that owns the correction is **29**.
