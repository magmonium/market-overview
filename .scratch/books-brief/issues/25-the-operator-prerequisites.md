# The operator prerequisites

Type: task
Status: resolved

## Question

A run cannot start without several things **code cannot conjure**, and they are scattered across the map rather than
collected in one place. A checklist:

| Prerequisite | Needed by | Note |
|---|---|---|
| **NYT API key** | the English chart (19) and comics (22) | free, 1,000 req/day, **attribution required** |
| **Flipkart affiliate approval** | the price layer (04) | without it, "best price" is **Amazon-only** and must say so |
| **The logo / mark** | every slide and thumbnail | the brief's `resource/brief/` — **one mark for every product** (09) |
| **The music bed** | every video (06) | the brief's bed contract |
| **`curl_cffi` reachability** | Anandabazar (02) and Rokomari (21) | ⚠️ **two sources now depend** on the impersonation `fetch/bse.py` already proves works |
| **A real browser** | every render | ⚠️ Remotion's bundled `chrome-headless-shell` **aborts** on the operator's machine, so `render.py` searches for one |

## Deliverable

One list, and for each item **what happens without it**. ⚠️ Several **degrade** rather than block — no Flipkart means a
narrower price claim, no logo means no mark — and the difference between a **blocker** and a **degradation** is the whole
value of this ticket.

## Answer

### The table — and the column that matters

| Prerequisite | Needed by | ⚠️ Without it |
|---|---|---|
| **Amazon.in reachable** | ⚠️ **every chart** (02) | ⚠️ **the run refuses — all four charts** — Amazon.in is in every source set |
| **A real browser** | every render | ⚠️ **blocker** — Remotion's bundled `chrome-headless-shell` **aborts** on this machine, so `render.py` searches for one |
| **NYT API key** | the English chart (19), comics (22) | ⚠️ **two different answers** — English **degrades** to PW + Indie (still two vendors, still ships); comics goes **absent**, because NYT is its *only* weekly ranking vendor (22) |
| **`curl_cffi` working** | Anandabazar (02), Rokomari (21) | ⚠️ **the Bengali chart goes absent** — without Anandabazar it has Amazon.in alone; without Rokomari the Bangladeshi bridge is gone |
| **YouTube OAuth client + token** | the publish (24) | ⚠️ **`build` is unaffected** — the package is written; only `publish` refuses. File-only is the fallback, and it needs no key |
| **Flipkart affiliate approval** | the price layer (04) | ✅ **degrades** — "best price" becomes Amazon-only, and the label **says so** (ticket 04's rule) |
| **The logo / mark** | every slide and thumbnail | ⚠️ **a blocker by the brief's precedent** — `logo.py` refuses on a bad mark, and the reserved top-right region exists for it. A markless video is *possible*, but that would be a product decision, not a fallback |
| **The music bed** | every video (06) | ✅ **degrades** — ship it silent. ⚠️ A deliberate divergence: the brief refuses on an audio failure because its bed is part of its identity; a chart's bed is not |

### ⚠️ And the uncomfortable finding

**The most load-bearing prerequisite is the one with no contract.**

Amazon.in is in **every** chart's source set — it is the Indian ranking vendor, the Bangladeshi bridge **and** the price
source — and it has **no API**. It is a scrape, contrary to its own conditions of use (ticket 02 named that rather than
hiding it), and HWR's FAQ says its bestseller list *"can be gamed"* (ticket 17).

⚠️ So **the single point of failure for the whole product is the least supported dependency in it.** That is not a
reason not to build it — it is the reason the **corroboration gate** (17), the **freshness guard** (10) and the
**scope caveat on the footer** (19, 21, 22) are all load-bearing rather than decorative. Every one of them exists
because this dependency cannot be trusted on its own.

### What this means operationally

- ⚠️ **A pre-flight check, not a surprise.** The run should verify the browser, the sources' reachability and the
  credentials **before** it spends a render — the reel's own ordering rule: *"every thumbnail before any video… a theme
  that reads badly should be seen and killed before an hour of frames is spent on it."*
- ⚠️ **The checklist is the operator's; the map is the spec's.** A hand-run (ticket 10) is *"the reason a human runs
  it"* (ADR 0006) — and this list is what that human is checking.
