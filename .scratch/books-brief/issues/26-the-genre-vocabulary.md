# The genre vocabulary

Type: task
Status: resolved

## Question

*"also mention type of book poem novel fiction non fiction business etc"* — a **third label**, beside country and
language (ticket 20). ⚠️ It is the first label that **always varies**, so it always renders.

But a genre is not a fact a source hands over; it is a **classification**, and every source uses its own:

| Source | Its own taxonomy |
|---|---|
| **NYT** | its **list names** — `hardcover-fiction`, `business`, `advice-how-to-and-miscellaneous` |
| **Amazon.in** | its **browse-node category** — the list a title ranked *inside* |
| **PW / Indie Bestsellers** | their **category lists** |
| **Google Books** | `volumeInfo.categories` — a BISAC-ish array, free and no-auth |
| **Rokomari** | its own Bangla category tree |

⚠️ **So "genre" is a normalisation problem, not a field.** Five taxonomies, one label.

## Answer

### The vocabulary — stable slugs, display strings in the renderer

The brief's discipline (ADR 0003), applied to classification: **`facts.json` carries a slug; the label table carries
the words.** So a vendor renaming a category is a one-line mapping change, not a re-render of the meaning.

```
poetry · novel · fiction · non-fiction · business · self-help · biography
history · religion · children · comics · academic · reference · other
```

⚠️ **`novel` and `fiction` are both present, deliberately** — the brief named both, and a novel is not a short-story
collection. The distinction earns its extra slug precisely because the brief drew it.

⚠️ **`other` is a real value, not a failure.** A title that maps nowhere is labelled honestly rather than forced into
the nearest wrong bucket — the same rule as `identity: unresolved` (ticket 05).

### The mapping is written down, never inferred

Each source's category maps to **exactly one** slug through an **explicit table** in the spec — the discipline ticket 17
requires of every field. ⚠️ A runtime "best guess" at a category name would make the label **non-deterministic**, and a
non-deterministic label cannot be replayed (ticket 03).

### The priority, joining ticket 17's table

⚠️ **The ranking source wins**, not Google Books — and the reason is specific: a title is on the *business* list because
the **vendor put it there**. Overriding that with a BISAC code would make the label disagree with the chart it labels.

### One primary, the rest kept

⚠️ Google Books returns an **array** of categories, and a book genuinely can be two things. The **slide shows one** — a
label is a glance, not a taxonomy — and the **full list stays in the snapshot**, so a later surface can show more
without a re-fetch.

### ⚠️ Not in the description, for ticket 20's reason

Ticket 15's rows already sit at **≈4,600 of 5,000 characters**. A genre on 100 rows adds ~1,000 and blows it. The labels
are a **slide** affordance — **all three of them** — and the description keeps its compact rows.
