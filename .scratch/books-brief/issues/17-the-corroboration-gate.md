# The corroboration gate

Type: research
Status: resolved
Blocked by: 02, 12

## Question

The brief is explicit: the chart must be **genuine and authentic**, and the run must **check as many sources as
possible before creating the list**. That is a *gate* on the union, not a property of it — a title is admitted only
once it has been corroborated.

What the gate has to decide:

1. **What "corroborated" means.** How many independent sources must carry a title before it enters a chart — one, two,
   three? *(Proposal: two, with a single-source title held on a `watchlist` until a second source confirms it — which
   pairs naturally with the incumbency rule in ticket 11.)*
2. **Field-level disagreement.** Sources will agree a book *exists* and disagree on its **publisher**, **price**,
   **pub date**, or the **spelling of its title**. Which source wins per field? *(Proposal: an explicit per-field
   priority — the publisher's own page > Circana > NYT > Google Books — recorded in the spec, never chosen at
   runtime.)*
3. **Identity, again.** Corroboration needs the ISBN to line up, but sources disagree on ISBNs and some carry none
   (ticket 05). What confirms identity when the ISBN is missing — normalised title + author + publisher?
4. ⚠️ **Titles only one source has.** A single-source title is the *most likely* to be wrong (a scraper artefact, a
   mis-parse, a pre-order) and also the *most interesting* (a genuine discovery). The rule has to say which it is
   treated as — and that is an editorial call, not a technical one.
5. **Auditability.** ⚠️ Every claim must be traceable to the raw response that made it — the brief writes
   `store/<date>/raw/*.json` *before* parsing for exactly this reason. A reader should be able to see **which sources**
   carried a title, and that evidence must survive into the committed snapshot.

## Deliverable

The corroboration rule, written down, plus the per-field source priority. This is what makes a chart **authentic**
rather than merely **aggregated** — the difference the brief is asking for.

## Answer

### ⚠️ The distinction that makes this rule real: corroboration counts **vendors**, not lists

The brief wants *"as many sources as possible"*. Taken literally, the all-language chart looks rich — Amazon.in's nine
language categories are nine lists. **They are one source.** Amazon.in's Bengali category and its Hindi category are
the same vendor, the same ranking system and the same failure mode, so counting them as two corroborating sources would
be a lie told in arithmetic.

**A source is a vendor.** That one line changes every count below.

### The rule

1. **Admission.** A title enters a chart when **at least two vendors carry it**, with each vendor's raw response
   committed.
2. ⚠️ **A single-vendor title is not discarded — it is parked.** It goes on the **watchlist** (ticket 11), with its
   status recorded, and does not appear in the chart. This is where *"genuine"* is actually enforced: ⚠️ the risk is not
   a fake book, it is **Amazon's own gaming warning** — HWR's FAQ says a low-selling product can top a narrow
   subcategory, so a #1 in a deep subcategory is not a #1.
3. ⚠️ **A chart whose whole source set is one vendor cannot satisfy rule 1 — and that is a finding, not a bug.** The
   **all-language chart is the live case**: Amazon.in ×9 categories is *one* vendor. So either an independent vendor is
   found for it, or it ships **marked single-source**, or it does not ship. ⚠️ **Whichever is chosen, the video must say
   it** — and it already can, because the **footer carries the source list** (ticket 07). A chart that cannot be
   corroborated must not *look* corroborated.

### Per-field priority — recorded, never chosen at runtime

Most of this is already decided across the map; ticket 17's job is to write it in **one** place.

| Field | Priority |
|---|---|
| **Title / author** | the vendor that **published the list** the title ranked on, normalised for comparison |
| **Publisher** | the publisher's own page → Google Books → the list |
| **Price** | Amazon.in lowest offer → Flipkart → Google Books `retailPrice` → publisher list price **labelled MRP** (ticket 04) |
| **Publication date** | Google Books → PW (ticket 05) |
| **Cover** | Google Books → Open Library (ticket 05) |
| **ISBN** | Google Books → Open Library (ticket 05) |
| **Genre** | the **list/category the title ranked in** → Google Books `categories` → `other` (ticket 26) |

⚠️ The priority is **recorded in the spec and in the snapshot**, so a later reader can see *why* a publisher is what it
is — rather than it being chosen at runtime by whoever wrote the merge first.

### Identity

- **ISBN-13**, normalised from ISBN-10, confirmed by **two** sources (ticket 05 — a single fuzzy title search is not
  identity).
- No ISBN → normalised `title + author + publisher` as the key, marked **`identity: unresolved`**.
- ⚠️ A mis-resolved identity **cascades** — wrong cover, wrong pub date, corrupted week-over-week diff — which is why
  identity passes the same two-source discipline as admission.

### ⚠️ Auditability — and the half that is easy to forget

The committed raw responses are the evidence, and the brief's habit is already right: `store/<week>/raw/*.json` is
written **before** parsing, so *"if the parser is what broke, the evidence of what it was given is already on disk."*

⚠️ **But recording only the winner is not auditability.** Each admitted title's row in `facts.json` carries:

- the **source ids that carried it** — which vendors, which lists;
- and, for every field where two sources **disagreed**, the **disagreement** itself: who said what, and which rule
  picked.

That is the difference between a chart that *asserts* a publisher and one that can *show* why it believes it. It is also
what keeps the ticket-04 price label honest — the reader can see that only Amazon was consulted.

### The rule for the awkward cases, stated once

⚠️ **Report, never silently drop.** The reel already holds this line for a cover no master answers to — *"the rule does
not change, the silence does"* — and it transfers. A title parked on the watchlist, a field won by the second-choice
source, a chart below the two-vendor floor: each is **written into the snapshot and surfaced in the run's warnings**,
because a silent drop is indistinguishable from a title that never existed.
