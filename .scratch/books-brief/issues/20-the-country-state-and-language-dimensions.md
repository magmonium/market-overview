# The country, state and language dimensions

Type: grilling
Status: resolved

## Question

The brief has added three dimensions and moved one boundary. Part of it is unambiguous; part of it is not.

### Clear — the Bengali chart's market changes

*"in bengali book also include bangladeshi book"*. The Bengali chart is **no longer India-market**: it is the
**Bengali-language market across India and Bangladesh**, which is what the language actually spans.

⚠️ **That breaks ticket 14.** The superset rule says the all-language chart contains every Bengali title. If the
all-language chart is *Indian*, it **cannot** contain a Bangladeshi one — so either the superset holds only over the
Indian portion, or the all-language chart stops being Indian. Neither is a detail: both change ticket 03's ranking and
ticket 02's sources.

### Ambiguous — the three new dimensions

*"mention country, top 100 world country, top 100 india state and language"* reads two ways:

1. **More charts.** Add three Top-100 charts — **by world country**, **by Indian state**, **by language** — taking the
   set from four to seven.
2. **Per-row labels.** The four charts keep their shape, and every slide gains a **country / state / language** line —
   *"mention country"* — with the breakdowns shown *inside* the existing charts rather than as separate ones.
3. **Both** — new charts for the big dimensions, plus the labels on every row.
4. **Sub-charts inside the existing four** — e.g. the all-language chart gains per-state and per-language sections.

## Deliverable

One paragraph per dimension: **is it a chart or a label, what does it rank, and what is its "100"?** Plus a decision on
the Bangladeshi boundary and what it does to ticket 14.

⚠️ **And the arithmetic, stated before it is chosen.** Each chart is a **~2 m 49 s** video (ticket 06). Seven charts is
**~20 minutes of video and 700 books per week** — seven renders, seven packages, seven uploads (ticket 13), and seven
source sets to corroborate (ticket 17). The count is a product decision, and this is its price.

## Answer

### The shape: **labels, not charts** — *"in chart just mention country language"*

The set stays **four**, and no new videos appear. The dimensions are **per-row labels**, so they land in the **slide
layout** (ticket 07) and nowhere else.

### ⚠️ The rule that stops a label becoming noise: **show it where it varies**

A label that says the same thing on all 100 rows is not information. Checked against the four charts:

| Chart | Country | Language |
|---|---|---|
| **Bengali** | ⚠️ **varies** — India / Bangladesh (the new boundary) | constant — the header already says Bengali |
| **English** | constant (India-market) | constant |
| **Indian all-language** | constant (India) | ⚠️ **varies** — Hindi, Tamil, Marathi, Malayalam, Bengali, English… |
| **Comics** | varies (Indian / imported) | ⚠️ varies (English, translated manga) |

So the labels earn their place on the **Bengali** chart (country) and the **all-language** and **comics** charts
(language). On a single-language chart the header already says it, and repeating it 100 times is decoration.

⚠️ **The mechanism already exists.** Ticket 07 rules that a field with no value is **omitted without leaving a hole** —
and a constant label is the same case: the slot simply does not render. No new layout rule is needed, which is the test
that this is the right shape.

### ⚠️ And they are **not** added to the description

Ticket 15's description rows already sit at **≈4,600 of YouTube's 5,000 characters**. Adding a country and a language to
100 rows would blow the budget and force the two-tier rows to become three-tier — trading a *reader's* field for a
*scanner's*. The labels are a **slide** affordance; the description keeps its compact rows unchanged.

### The Bangladeshi boundary, and what it does to ticket 14

**The Bengali chart spans India and Bangladesh; the all-language chart stays Indian.** So the superset is *amended*
rather than abandoned:

- all-language ⊇ every **Indian** title in every language — including **Indian Bengali** titles;
- ⚠️ and the Bengali chart carries a **Bangladeshi overhang** — titles present in the Bengali chart and **not** in the
  all-language chart, because that chart is Indian.

The asymmetry is now explicit, and ticket 14's surviving rules still hold: **rank is chart-local**, and the dedupe key
is **chart + ISBN**.

### ⚠️ One point raised but not confirmed: **state**

The earlier message said *"top 100 india state"*; this one says *"country language"*. So **state is not in the label
set** — but the layout's field slot absorbs it with no new rule if it is wanted later. Recorded rather than silently
dropped.

### ⚠️ Amended — a third label, and it is the one that always varies

The brief has since asked the charts to *"also mention type of book poem novel fiction non fiction business etc"*. That
is a **third label**, and it behaves differently from the other two: **genre varies on every chart**, so by this
ticket's own rule its slot **always renders**. The vocabulary and the mapping are **ticket 26**.

### What this hands to the others

- **Ticket 21** (Bangladeshi sources) is now **unblocked** — the boundary it must source for is settled.
- ⚠️ **Ticket 12's** Bengali row is amended (done), and **ticket 14**'s superset is amended as above.
- **Ticket 07** gains two optional label slots; **ticket 15** is explicitly **unchanged**.
