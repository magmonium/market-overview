# 0006 — A server builds and publishes the brief, daily, after the close

- Status: accepted
- Date: 2026-12-12

## Context

ADR 0004 made the run manual, and gave two reasons: a scheduled non-interactive run has no window server, which is
a real risk for the macOS Metal/ANGLE path; and the tool fetches its own data, so it cannot live in the platform's
crontabs. The operator now wants the brief built **and uploaded to its YouTube channel every day after the close**,
which a hand-run cannot do.

Three things have changed since ADR 0004 was written:

- **The window-server objection is macOS's, not the pipeline's.** Remotion renders headless on Linux with its own
  bundled Chromium plus a short list of shared libraries — no GPU, no display, no window server. The risk the ADR
  retires *by staying manual* on macOS is retired *by the platform* on Linux. (It is not fully retired, either way:
  `render.py` still needs `--browser-executable`, because Remotion's bundled `chrome-headless-shell` SIGABRTs on
  the operator's machine.)
- **The typeface is vendored** (`docs/adr/0005`), so a render no longer depends on the fonts a host happens to have.
  Without that, a server render would silently not be the same brief.
- **The delayed-feed rule is already enforced in code.** `session.py` refuses a date that is not the newest session,
  and refuses a session that has not finished printing, from the spine's own timestamps — no second source, no
  holiday calendar. That guard is what makes a *dumb* schedule safe.

## Decision

**A Linux host runs the whole pipeline on a timer, and the upload is part of the run.**

```
market-brief.timer  →  market-brief.service  →  daily-brief.sh
                                                  ├── uv run mo build --lang bn en
                                                  └── uv run mo publish --lang bn en --privacy …
```

- **`OnCalendar=Mon..Fri 16:30 Asia/Kolkata`**, `Persistent=true`. 16:30 because `session.FINAL_FROM` is 16:00 —
  the india feed is ~15 minutes delayed, so "final" is the close plus that delay plus a margin. Mon–Fri rather than
  every day because a Saturday cannot have a session, and the guard's refusal is correct but not *informative*:
  two refusals a week trains an operator to ignore the log.
- **⚠️ Holidays are still scheduled, and still refuse.** There is no holiday calendar in this tool and none is
  being added: a refusal exits `1` and writes nothing, which is the correct outcome, and inventing a second source
  of truth about which days trade is how the first one starts disagreeing with the exchange.
- **`--lang bn en`, always.** `LANGUAGES` is `("bn",)`, so a bare command builds and publishes *one* edition. The
  schedule must not rely on a default that was chosen to keep a re-cut cheap.
- **⚠️ `--privacy` defaults to `private`, and the schedule inherits that.** ADR 0004's real protection was never
  the window server; it is the README's "Before you publish" list — the Bengali reading as Bengali, the music
  sitting right, the mark being present — *"the reason a human runs it"*. Uploading straight to `public` on a timer
  deletes that check without saying so. The operator flips it with `MARKET_OVERVIEW_PRIVACY=public` once, having
  decided to.
- **The upload is idempotent** (`publish.py`), keyed on the facts bundle's per-edition hash, so a re-run of the same
  day posts nothing and a *rebuilt* day refuses rather than putting two different briefs under one title.

## Consequences

- **The run is unattended, and the failure mode of unattended is silence.** Every refusal exits non-zero and writes
  nothing; the wrapper logs to `var/log/`, and alerting is the operator's to add. This is the cost of the decision
  and it is not paid anywhere in the tool.
- ⚠️ **A refresh token from an OAuth client still in "Testing" expires in seven days.** Nothing in the tool can
  detect this in advance; `mo publish` will start refusing with `invalid_grant` and the consent screen has to be
  published. This is the single likeliest way this schedule fails, and it fails *after* a week of looking healthy.
- **ADR 0004 is superseded for the server, and kept for the laptop.** A hand-run is still how an edition is re-cut
  and checked before it goes up, and `--date` still rebuilds any past day from `store/`.
- **The two editions take over an hour**, so a 16:30 start lands around 18:15–18:30 IST. The schedule is not a
  deadline and nothing downstream depends on it.
## Addendum — what moving to Linux actually surfaced

Written after the server path was implemented, because two of the three findings were *defects the move exposed*
rather than choices it made.

- ⚠️ **`audio.py` could not have worked on Linux at all.** The bundled ffmpeg is `--enable-shared` and needs its
  library directory on the dynamic loader's search path, and the module named that path with a **hard-coded
  `DYLD_LIBRARY_PATH`** — macOS's variable. On Linux the loader reads `LD_LIBRARY_PATH`, so setting the macOS one is
  a **silent no-op**: no error, no warning, and the only symptom is ffmpeg refusing to start, reported as an ffmpeg
  failure that never mentions a loader. It is now `loader_variable(sys.platform)`, with both branches tested from
  whichever platform the suite runs on. This is exactly the class of bug ADR 0005 was written to eliminate, one
  layer down.
- **Remotion passes `--no-sandbox` unconditionally**, so a real Chrome runs as root in a container with no extra
  flags and no added capabilities. Worth knowing rather than assumed.
- **Remotion renders `--single-process` on Linux unless `enableMultiProcessOnLinux` is set.** It works either way;
  the flag is a speed knob, it is **not** set here, and `deploy/README.md` says how to measure it. The same rule as
  `MARKET_OVERVIEW_CONCURRENCY`: a render setting is a property of the box, and an unmeasured one is a guess.

**Packaging is Docker or a host timer, and it does not change the decision above** — both run the same
`daily-brief.sh`, and the containerised scheduler is the same image with a different command, so the scheduler needs
no Docker socket and no privileges. `deploy/` carries both.

⚠️ **The one consequence that is a consequence:** under any packaging, `output/` must **persist across runs**, because
that is where `.published-<lang>.json` lives. A container whose `output/` is ephemeral re-uploads the day on every
firing — the exact failure `publish.py` exists to prevent, re-introduced by the filesystem rather than by the code.
`deploy/compose.yaml` mounts it, and says why at the top rather than in a comment nobody reads.

## Addendum — the threshold moved to 15:45

- **`session.FINAL_FROM` moved from 16:00 to 15:45**, by the operator, once the daily schedule was in use. 16:00 was
  the close (15:30) plus the feed's ~15 minute delay **plus a further fifteen minutes of margin**; 15:45 is the delay
  alone. The brief therefore ships about a quarter of an hour earlier, and what the margin was insuring against —
  that the delayed feed has actually delivered the closing prints — is now what the threshold trusts.
- **The `OnCalendar` above is unchanged**, and it is no longer *derived* from the constant: it never was arithmetic,
  it was a coincidence of round numbers. At 16:30 it now clears the guard by three quarters of an hour, so the fire
  time carries its own margin instead of inheriting the code's.

## Addendum — the threshold moved to 15:40, because 15:45 refused a whole day

- **`session.FINAL_FROM` moved from 15:45 to 15:40.** The session of 2026-10-13 finalised the clock row
  (`NSE:NIFTY`'s `last_bar_update_time`) at **15:44:03 IST** — 57 seconds under the previous threshold — and then
  stopped writing: three samples over three minutes read the same second. That is the distinction the previous
  addendum missed. A bar that is still *moving* refuses later if you wait; a bar whose final write has already
  happened refuses **forever**, because a re-run re-sends the same request and reads the same record. Every retry
  that afternoon was refused, and `market-brief.timer`'s 16:30 firing would have refused with them — the silent
  unattended failure this ADR warns about, reached through the guard rather than around it.
- **The lesson is about the constant, not about the day.** 15:45 asserts that "the close plus 15 minutes" describes
  when the vendor finishes writing, and the vendor's own record of the same field says otherwise: **16:15 IST for
  2026-10-12** (in `store/2026-10-12/raw/tradingview-indexes.json`, and the value `tests/test_session.py` pinned as
  "finished printing") against 15:44:03 for 2026-10-13. The delay is real; the minute is a round number. A threshold
  that lands inside the spread of a timestamp the vendor controls will refuse on the days the vendor runs early.
- **What this gives up, stated rather than implied.** The guard no longer waits for the feed's full ~15 minutes: a
  run fired between roughly 15:40 and 15:45 now trusts that a final write *is* the closing print. Ten minutes past a
  15:30 close is still clear of the intraday feed — the mistake the guard exists to catch — and it is under every
  final write measured so far, which is the property a threshold needs to have.
- **`OnCalendar` is unchanged**, and 16:30 now clears the guard by fifty minutes. The fire time keeps its own margin
  rather than inheriting the code's, which is what makes moving the constant a one-file decision.
- **`tests/test_session.py` pins the boundary from both sides** (15:39 refused, 15:40 accepted) and pins the
  2026-10-13 write as accepted, so the next move has to move those cases with it.

