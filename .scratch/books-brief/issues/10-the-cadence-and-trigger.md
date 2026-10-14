# The cadence and the trigger

Type: task
Status: resolved
Blocked by: 02, 09

## Question

Weekly — but on which day, and driven by what?

Source publication days differ (NYT on Wednesday; PW and the Indie lists Monday–Tuesday), so the run must happen
**after every source in the union has published**, or a late source silently drops out of the chart and the Top 100
is quietly wrong. The union's slowest member sets the run day.

Also:

- `store/<week>/raw/*.json` then `store/<week>/facts.json`, committed — what keys a week, and how a re-run of the
  same week is detected rather than duplicated.
- Does a re-render **replay** the committed snapshot or re-fetch? (The brief replays — `facts.json` is the only
  thing a re-render reads.)
- The `deploy/` unit: a weekly `systemd` timer beside `market-brief.timer`, or a manual run at first?

## Answer

### The shape is already decided by the repo — manual first, scheduled later

ADR 0004 (**the run is manual**) and ADR 0006 (**a server runs it daily**) are not in conflict; they are two stages of
one thing, and ADR 0004 says so: *"A schedule can be added later without moving anything, because the command is
already the interface."*

⚠️ **The split is macOS vs Linux, and it is the WebGL one.** A scheduled non-interactive run on the operator's Mac has
no window server — a real risk for the Metal/ANGLE path. On Linux, Remotion renders headless with its bundled Chromium
and no GPU. So:

- **Stage one — manual**: `books-brief build --week 2026-W41` by hand, on the Mac, inside an interactive session.
- **Stage two — a timer** on a Linux host: `OnCalendar=Tue 09:00 Asia/Kolkata`, `Persistent=true`, the same wrapper
  shape as `daily-brief.sh`.

### ⚠️ What keys a week: the **ISO week** — which also settles ticket 15's ambiguity

`2026-W41`, zero-padded, so it sorts as a string and needs **no state**: any date derives its week id, and nothing has
to remember when the product launched.

- `store/2026-W41/raw/*.json` — written **before** parsing, the evidence
- `store/2026-W41/facts.json` — the committed bundle, the sole interface to the renderer (ADR 0003)

⚠️ **This is also the answer to ticket 15's *"Week 10 — which week?"*** It is the **ISO week number**, so a video built
in October says *Week 41*, not *Week 10*. The alternative — a counter of weeks since launch — needs state that can
drift, and produces a title that disagrees with the folder it came from.

### ⚠️ The guard is load-bearing, not defensive — and it transfers

ADR 0004's real cost: *"A hand-run can be fired on a holiday… So the **session-date guard is load-bearing, not
defensive**: the run must refuse rather than publish stale numbers."*

The books equivalent is a **freshness guard per source**, and it is *more* necessary here, because a books chart has no
session clock to check against. Each source must be verified to have published **for the week being built** — not
trusted because the calendar says it is Tuesday. ⚠️ A stale Amazon.in scrape would otherwise yield a chart that is
quietly last week's, and the week-over-week diff (ticket 01) would report **zero movement** — a silent, plausible,
wrong result.

⚠️ **The mechanism belongs to ticket 18**; this ticket fixes only that the guard exists, and that a failure **refuses
and writes nothing**.

### ⚠️ No holiday calendar, ever

ADR 0006 refused to invent one — *"inventing a second source of truth about which days trade is how the first one
starts disagreeing with the exchange"* — and scheduled **Mon–Fri** rather than daily, because *"two refusals a week
trains an operator to ignore the log."* Both transfer:

- Schedule **on a weekday**, not every day.
- ⚠️ A refusal **exits non-zero and writes nothing** — not an error to be swallowed.
- The fire time is a **configured value, not arithmetic** — ADR 0006's own lesson: *"it never was arithmetic, it was a
  coincidence of round numbers."* Recommended **Tuesday 09:00 IST** (a Sun–Sat sales week closes Sunday; lists compiled
  from it land Monday–Tuesday), to be confirmed against the sources at implementation.

### Re-render replays; a re-run is explicit — and the publish is idempotent

- ⚠️ **A re-render reads `facts.json` and does not re-fetch** (ADR 0003). That is what makes `--week` the normal way to
  rebuild a past week.
- ⚠️ **The upload is idempotent, keyed on the bundle's hash** — ADR 0006's rule, transferring exactly: a re-run of the
  same week posts nothing, and a **rebuilt** week (different hash) **refuses** rather than putting two different charts
  under one title.
- ⚠️ `output/books/` must **persist across runs** — that is where the published-marker lives, and an ephemeral
  `output/` re-uploads the week on every firing.

### ⚠️ And the privacy default stays `private`

ADR 0006's sharpest line: *"ADR 0004's real protection was never the window server; it is the README's 'Before you
publish' list… the reason a human runs it. Uploading straight to `public` on a timer deletes that check without saying
so."* For a chart product the human check is the same kind — **is the Bengali chart actually Bengali, are the covers
the right books, is the rank plausible** — so the default stays `private` until the operator decides otherwise.
