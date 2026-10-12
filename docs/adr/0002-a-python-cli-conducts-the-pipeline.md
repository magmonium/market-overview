# 0002 — A Python CLI conducts the pipeline

- Status: accepted
- Date: 2026-12-12

## Context

The pipeline crosses a runtime boundary: market data is fetched and computed in **Python**, and the video is
rendered in **JS/WebGL** by Remotion. Something has to own a run end to end, including its failure rules —
prices are the spine and abort the run, while every other source degrades to omission, and a failed edition
fails the run.

## Decision

A single Python CLI, **`market-overview build --date YYYY-MM-DD`**, conducts:

fetch → compute facts → `store/<date>/facts.json` → the two `npx remotion` renders → the still → atomic
package assembly.

Python shells out to Remotion. Remotion never invokes Python, and never fetches anything.

## Consequences

- **One owner for the abort/degrade contract.** A failure rule spread across two runtimes would have no
  arbiter, and the rule that matters most — *write no package when the spine fails* — has to be enforced in
  the process that decides whether the run succeeded.
- The render layer stays replaceable: it is a command that takes a file and writes files.
- `--date` makes a rebuild a first-class operation: the same command re-renders a past date from
  `store/<date>/` instead of fetching.
- Remotion cannot become the orchestrator later without moving the failure rules, so this is a load-bearing
  choice rather than a convenience.
