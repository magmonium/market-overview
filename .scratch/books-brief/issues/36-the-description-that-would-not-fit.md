# The description that would not fit — and the rupees in it

Type: task
Status: resolved
Found by: 34

## Question

The comics chart built, rendered, and then refused to be packaged:

```
books_brief.metadata.MetadataError: the description is 9295 characters, over the 5000 YouTube keeps —
shorten the rows rather than shipping a list whose tail is cut off
```

⚠️ **Ticket 15's refusal was right and useless.** *"A list that will not fit is a list to shorten"* does not say **what**
to shorten, and the chart had been built, rendered and paid for by the time it was refused. So: what gives?

## Answer

### ⚠️ The titles give, not the fields — and that is measurable

⚠️ Measured against the real snapshot, each candidate shape's length:

| Shape | Characters | |
|---|---|---|
| current — top 10 full, tail `rank. title — author` | **9,332** | ❌ over by 4,332 |
| tail drops the author | 9,059 | ❌ over by 4,059 — ⚠️ **273 characters, for every author in the list** |
| tail = `rank. title` truncated to 45 | 5,198 | ❌ over by 198 |
| **every row `rank. title` truncated to 45** | **4,754** | ✅ fits |

⚠️ **The authors are not the problem; the titles are** (*The Long-Lived King: An Original The Owl House Graphic Novel*),
and five thousand characters holds a hundred of them only at about forty-five. ⚠️ So the shortening is done where it
costs least, and **the search is what makes it safe**: the shapes are tried **cheapest loss first** — every title whole
and with its author, then without the author, then cut to a narrowing width — and the first that fits is the one shipped.

⚠️ **Two things are deliberately not given up.** The list stays **whole at 100 rows**, and the **top ten keep every
field**, because those are the ranks the video dwells on (ticket 06). ⚠️ And **the refusal stays**, as the *last rung*
rather than the first: a list whose top ten will not fit even with a fragment for every tail title is still refused,
because YouTube cuts the **tail** — the part of the list nobody would check.

### ⚠️ And the assembled text was pricing Canadian books in rupees

⚠️ Assembling it printed **`₹31` for a `CAD 30.60`** row. `package._rows` built every price with `_rupees(amount)` — a
hard-coded `₹` — which was true while every chart was **India-anchored** (ticket 12) and has been false since ticket 19:
the English chart's rows are `USD`, `CAD` and `AUD`, and the comics chart's are `CAD` and `INR`.

⚠️ ⚠️ **It is the `₹24.99`-for-`$24.99` failure again — this time in the upload text**, where nothing had looked: the
slides were checked, the description was not. ✅ Fixed with a symbol table keyed by the row's own `currency`, and ⚠️ a
currency with no symbol is written as its **code** (`SEK 240`) rather than as a bare number, because a bare number is the
ambiguity this product keeps refusing.

### ✅ The evidence

```
comics description: 4982 characters (limit 5000)
1. The Boy, the Mole, the Fox and the Horse… —  — Charlie Mackesy — CA$23
2. How Lucky Am I —  — Christian Watson — CA$31
9. 101 Tales The Great Panchatantra Collection… —  — Wonder House Books — ₹329
11. Dog Man: Big Jim Believes: A Graphic…      ← the tail, cut visibly

package assembled: Metadata(title='Top 100 Comics | Week 41 | 5 Oct, 2026', …)
   comics-2026-W41.mp4                31,279,131 bytes
   metadata-comics.json                    5,762 bytes   ← the completeness marker
   metadata-comics.txt                     5,321 bytes
   thumbnail-2026-W41-comics.jpg         144,205 bytes
```

⚠️ **The video was already rendered**, and the description lives only in the two metadata files — so re-assembling was
enough and nothing was re-rendered. ⚠️ **355 tests pass**, including the two the change is pinned by: a week of
comics-length titles is *shortened rather than refused*, and a week that fits keeps **every title whole and every
author** (the ladder's first rung, which is what makes this invisible to every other chart).

### ⚠️ What this leaves open, recorded rather than tidied

- ⚠️ ⚠️ **And `bb publish` does not compare a package's `bundle_hash` with the snapshot's** — found by running the
  dry-run after the re-gather. `publish.run` compares the manifest's hash with its own **publish record** (so a *rebuilt*
  week refuses), but it never checks the manifest against **`store/<week>/facts.json`**, which is the bundle the package
  claims to describe. ⚠️ `metadata.py`'s own docstring says *"a package whose JSON named a different bundle from the one
  on disk is a package built from something else"* — and nothing enforces it at upload time. ⚠️ Measured: the dry-run
  lists **`all-language` and `bengali`** as ready to upload, and both were assembled at **17:10** from the snapshot that
  the re-gather replaced. ⚠️ **The remedy before publishing is a re-render of those charts**, and the fix is a
  comparison in `publish` — recorded here rather than made, because it changes what a publish is allowed to do.
- ⚠️ **The other three charts' packages are now stale.** The re-gather replaced `facts.json`, and `english`, `bengali` and
  `all-language` still hold packages assembled from the **previous** snapshot — their `bundle_hash` names facts that are
  no longer on disk. ⚠️ A re-render of each is what refreshes them; ⚠️ and the **English chart is publishable for the
  first time** (its 7,677 characters now shorten like the comics chart's).
- ⚠️ **`—  — Charlie Mackesy` reads oddly, and it is the source's ambiguity rather than a new defect.** Amazon's card
  carries one byline node that is sometimes a publisher (`Wonder House Books`) and sometimes an author (`Jeff Kinney`) —
  `amazon.parse` files it under `publisher`, and its own test asserts both cases. ⚠️ With Google Books rate-limited the
  `author` field is empty, so the byline shows in the publisher's slot. ⚠️ Reading it as an *author* is a change to
  ticket 17's per-field priority, so it is recorded here and not made.
- ⚠️ **`window: 1 weeks`** — correct, and the window really is one week (no earlier week is on disk), but it reads as a
  plural bug. ⚠️ Left alone because ticket 23's rule is that the number is *reported* rather than rounded up.
