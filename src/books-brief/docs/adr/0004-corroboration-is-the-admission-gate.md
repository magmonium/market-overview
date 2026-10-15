# 0004 — Corroboration is the admission gate

- Status: accepted
- Date: 2026-10-14

## Context

The brief asked for a chart that is **"genuine and authentic"**, built by **"checking as many sources as possible
before creating the list."** That is a requirement about *trust*, and it arrives in a domain with an unusually weak
supply of it:

- ⚠️ **Amazon's bestseller badge can be gamed.** The Himalayan Writing Retreat's own FAQ says a low-selling product can
  top a *narrow* subcategory — and Amazon.in is in **every** chart's source set here.
- ⚠️ **Most of this product is scraping.** Amazon.in has no API; Anandabazar and Rokomari are behind Akamai; the
  Indian lists that *would* be authoritative are dormant or the wrong cadence.
- ⚠️ **"As many sources as possible" is a trap when counted naively.** Amazon.in's nine language categories are nine
  *lists* — and **one vendor**: the same ranking system, the same failure mode.

## Decision

**A title enters a chart only when at least two *vendors* carry it.**

⚠️ **A source is a vendor, not a list.** Counting Amazon.in's nine categories as nine corroborating voices would be *"a
lie told in arithmetic"*, and it is the single distinction this ADR exists to fix in place.

- **A single-vendor title is parked, not discarded.** It goes on the **watchlist**, where the ≤10 newcomer cap's
  overflow also lands — so **one list serves both**, and *"a silent drop is indistinguishable from a title that never
  existed."*
- **A chart whose whole source set is one vendor cannot satisfy the rule** — and that is a **finding, not a bug**. The
  all-language chart is the live case, and it must either find an independent vendor, ship **marked single-source**, or
  not ship.
- ⚠️ **Per-field disagreements resolve by a priority recorded in the spec**, never chosen at runtime: the ranking
  vendor wins the title and author, because the vendor is *why* the title is on that chart.
- ⚠️ **Identity is corroborated too.** ISBN-13, normalised from ISBN-10 and confirmed by two sources; a title with no
  ISBN falls back to `title + author + publisher` and is marked `identity: unresolved` rather than given a synthesised
  key two books could share.

## Consequences

- ⚠️ **The vendors a chart declares are its *spine*.** Losing one makes the chart **absent**, not smaller — *"a
  degraded chart is a wrong chart."*
- ⚠️ **Auditability is more than recording the winner.** Every row carries the **source ids that carried it**, *and*
  the **disagreements** — who said what, and which rule picked. That is the difference between a chart that *asserts* a
  publisher and one that can *show* why it believes it.
- ⚠️ **A chart that cannot be corroborated must not *look* corroborated**, which is why the footer names the sources
  (ADR 0001).

## ⚠️ ⚠️ Amended 2026-10-15 — the gate is *reported*, not required

⚠️ **The decision above is reversed.** A title enters a chart when **any** declared list carries it; corroboration is
carried on the row and expressed through ticket 03's score instead of gating admission. ⚠️ The rule was not wrong so much
as **unsatisfiable**, and the arithmetic is short:

    the `english` chart declares two vendors (NYT, Indie)
    the gate admits a title only when two *different vendors* carry it
    ⇒ the chart can rank only their *intersection* — 16 rows, against a "Top 100" title
    ⇒ a one-vendor chart (`all-language`) can rank **nothing at all**, ever

⚠️ **The evidence is the recorded week.** Replaying 2026-W41's own raw responses through the two vendors the chart
already declared gives **165 list-rows → 134 distinct titles** — 103 carried by one list, 31 by two — where the gate
admitted **16**. ⚠️ Nothing was added to the source set to achieve that; the rule *was* the whole constraint.

⚠️ **What survives, and it is most of it:**

- ⚠️ **A source is still a vendor, not a list.** Amazon.in's several lists are still **one voice** — the distinction this
  ADR exists to fix in place is untouched.
- ⚠️ **Every row still carries the lists that carried it** (`Title.sources`), so the chart can still *show* why it
  believes a thing rather than asserting it. That was the auditability half, and it is now the only thing standing where
  the gate was.
- ⚠️ **The vendors are still the spine**: losing one still makes the chart **absent**, not smaller.
- ⚠️ **Per-field priority and identity corroboration are unchanged.**

⚠️ **And one thing this ADR can no longer claim — recorded rather than glossed.** Ticket 03's score sums each *list*, so a
vendor declaring two lists a title could appear on twice would count twice: the *"lie told in arithmetic"* above. ⚠️ No
declared chart can currently do that — `english`'s two NYT lists are fiction and nonfiction, and one book cannot be on
both — so it is a **guard to add, not a defect to repair**, and it belongs to ticket 03.

⚠️ **What is lost, stated plainly:** a chart no longer *certifies* that two independent sources agree. It **reports how
many did**. ⚠️ That is a weaker claim, and the footer that names the sources (ADR 0001) is now load-bearing for it
rather than decorative.
