# The title, description and tags

Type: grilling
Status: resolved
Blocked by: 12, 13

## Question

Every package ships three pieces of front matter, and the brief has now specified all three:

1. **Title** — *"Top 100 Bengali Books | Week 10 | 14 Oct, 2026"*, and its siblings, one per chart.
2. **Description** — carries the **full list** — all 100 titles, not a summary.
3. **Tags** — SEO-optimised.

Open questions:

- ⚠️ **"Week 10" — which week? — SETTLED by ticket 10.** It is the **ISO week number**: `2026-W41`. Unambiguous,
  stateless (any date derives it), and it matches the `store/2026-W41/` folder the package came from. The alternative —
  a counter of weeks since launch — needs state that can drift. So a video built in October reads *Week 41*, not
  *Week 10*.
- Does the title name the **chart** (`Top 100 Bengali Books`) or the product? And what does the all-language chart's
  title say — `Top 100 Indian Books (All Languages)`?
- ⚠️ **A 100-title description** — a plain list, a numbered list, or a list carrying rank, price and a link? Does it fit
  the platform's character limit (YouTube's is 5,000) with the *full* list intact?
- Which chart's package is the primary one when the run publishes (ticket 13)?
- Where does the metadata live? The brief writes `metadata-<lang>.txt` **and** `metadata-<lang>.json` beside the video —
  does this product mirror that pair?
- Are the tags generated from the chart itself (top authors, publishers, chart name, year, "bestseller") or curated by
  hand?

⚠️ Title, description and tags are **per chart**, like everything else (ticket 12) — unless ticket 13 says the four
charts are one package.

## Answer

### The title — the brief's scheme, with the fit checked

```
Top 100 Bengali Books | Week 41 | 14 Oct, 2026
Top 100 English Books | Week 41 | 14 Oct, 2026
Top 100 Indian Books (All Languages) | Week 41 | 14 Oct, 2026
Top 100 Comics | Week 41 | 14 Oct, 2026
```

⚠️ The longest is **64 characters** against YouTube's **100** (`metadata.TITLE_LIMIT` — the same constant the brief
uses), so the fit is *checked* rather than hoped for. The reel's rule applies: *"a title that will not fit is a title
to shorten, never a layout to bend."*

⚠️ **The basis is six-month sales and reviews** (ticket 23), so the **title and description must say so** —
`Top 100 Bengali Books` no longer states what it ranks. The row template and the character budget are unchanged; the
**basis line joins the header**.

⚠️ **No chart is primary.** Four videos, four packages (ticket 13), so the question dissolves.

⚠️ **The comics chart is worldwide** (ticket 22). The scheme needs no change — `Top 100 Comics` is already scope-neutral
— but ⚠️ the **description's source attribution and the footer** must name the worldwide sources, because that ranking
**skews US** and the chart must not imply global coverage it does not have.

⚠️ **The English chart is US-market, not global** (ticket 19) — NYT, PW and Indie Bestsellers are all US lists, so the
same honesty applies, and the same remedy: the attribution names the sources. ⚠️ And on that chart **neither new label
renders** (the country is constant, the language is in the header) — which is ticket 20's rule working, not a gap.

### ⚠️ The description — and the arithmetic that decides its shape

The brief asks for the **full list**, all 100. Here is what that actually costs against `DESCRIPTION_LIMIT = 5000`:

| Row template | Per row | × 100 | Verdict |
|---|---|---|---|
| `1. Title — Author` | ~38 | ~3,800 | ✅ fits |
| `1. Title — Author — ₹399` | ~48 | ~4,800 | ⚠️ fits, with nothing left for header, attribution or hashtags |
| `1. Title — Author — Publisher — ₹399` | ~68 | ~6,800 | ❌ **over** |

⚠️ **"The full list with all the fields" does not fit — that is arithmetic, not opinion.** So the rows mirror the
**video's own dwell weighting** (ticket 06): the detail follows the same interest curve.

```
TOP 100 BENGALI BOOKS · WEEK 41

1.  Ekti Shonar Boi — Sunil Gangopadhyay — Ananda Publishers — ₹399 — Oct 2026
2.  ...                                          (full rows, ranks 1–10)
11. Bishkanta — Humayun Ahmed — Ananda
12. ...                                          (compact rows, ranks 11–100)

Sources: Amazon.in · Anandabazar        Covers: Google Books / Open Library
#Top100Books #BengaliBooks #Bestsellers
```

Ten full rows (~800) + ninety compact (~3,400) + header/footer ≈ **4,600 characters**, leaving ~400 of headroom.

⚠️ **And the fit is checked, not hoped for.** If a week's titles run long and the block will not fit, the run
**refuses** — because *"the full list"* is the product's promise and a silently truncated list breaks it. That is the
reel's rule (`SeoError`: *"the run stops before it renders an hour of frames"*), not the brief's warn-and-ship.

⚠️ **The description carries its own attribution.** The brief's reason: *"the description is the surface that survives
somewhere other than the video — quoted, screenshotted, syndicated — so it carries its own copy of the attribution."*
Here that is the source list and the **cover credit** (ticket 05).

### Tags — a **character** budget, not a tag count

⚠️ The brief's trap, quoted: *"The tag budget is in **characters**, not tags... a handful of long sector names blows it
without anything looking wrong."* `TAG_BUDGET = 500`.

Tags are therefore appended **while the joined length stays inside it** — never "the first N", because *"a slice of the
first N would look right and blow the limit on a day of long names."* Seeded with the fixed four (channel, chart name,
"bestseller", year), then the week's notable authors and publishers while they fit.

### Hashtags — exactly three

⚠️ `HASHTAGS_MAX = 15` is *"a cliff, not a budget"*: **exceed 15 and YouTube ignores all of them.** Three is also all
that displays above the title, so the count is fixed and unbreakable.

### The pair, and the rules it inherits

`metadata-<chart>.txt` **and** `metadata-<chart>.json`, beside the video — mirroring the brief's `metadata-<lang>.*`.

- ⚠️ The **`.json`** names the video and thumbnail **explicitly** and carries the **`bundle_hash`** (ticket 10's
  idempotence key), so an uploader needs nothing but the chart folder — *"self-contained by construction."*
- ⚠️ The **`.txt`** is **plain text only** — *"no Markdown, no markup… a heading marker or an asterisk pastes in as
  literal junk"* — with fields labelled, because a human pastes them into three separate boxes.

⚠️ **The copy is a pure function of the bundle** — no clock, no random choice, nothing read from the cover art — so a
rebuild writes the same two files byte for byte (ADR 0003).

⚠️ **Authored, not translated.** The reel's rule transfers: *"a Bengali search and a Latin one are two different
queries, which is why both are spelled out rather than derived from each other."* The Bengali chart's keywords are
authored in Bengali, and both scripts may appear in the description — where they are real searches, never stuffing.
