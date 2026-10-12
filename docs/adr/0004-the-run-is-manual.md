# 0004 — The run is manual, not scheduled

- Status: accepted
- Date: 2026-12-12

## Context

The brief is daily and built after the 16:00 IST close. Candidates for firing it: a user LaunchAgent, a
LaunchDaemon, plain `cron`, CI, or the operator running it by hand.

Two facts bear on the choice. The render needs WebGL, and Remotion drives headless Chrome — a **scheduled,
non-interactive run has no window server**, which is a real risk for the Metal/ANGLE path. And the tool
**fetches its own data**, so it has no dependency on the platform's crawl or processor containers and cannot
live in their crontabs.

## Decision

**The operator runs `market-overview build --date YYYY-MM-DD` by hand.** No scheduler: no LaunchAgent, no
cron, no daemon, no CI.

## Consequences

- **A hand-run happens inside an interactive GUI session, so the headless-WebGL question never arises** — the
  WindowServer, ANGLE/Metal fallback chain and SwiftShader escape hatch all become moot. This retires risk
  rather than deferring work.
- The post-close window is not a constraint, so the render can take as long as it takes.
- ⚠️ **A hand-run can be fired on a holiday, or mid-session by mistake** — and a holiday produces no error,
  only yesterday's numbers. So the **session-date guard is load-bearing, not defensive**: the run must refuse
  rather than publish stale numbers. This is the cost of the decision, and it is paid in the fetcher.
- `--date` becomes the normal way to rebuild a past day from `store/<date>/`.
- A schedule can be added later without moving anything, because the command is already the interface.
