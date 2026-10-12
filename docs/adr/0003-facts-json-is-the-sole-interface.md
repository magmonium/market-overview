# 0003 — `facts.json` is the sole interface between the two halves

- Status: accepted
- Date: 2026-12-12

## Context

Python fetches and computes; JS/WebGL renders. The two halves have to agree on something, and whatever that
is becomes the system's real contract.

## Decision

**`store/<date>/facts.json`** is the only thing that crosses.

- It carries **values and label keys only** — never display strings.
- The **label tables** (`copy.bn.json`, `copy.en.json`) are static, hand-authored assets that live in the
  render layer. A label that changed with the data would be a template, and a template was rejected.
- Remotion is invoked with `--props=<file>`, so the renderer never fetches and never re-derives.

## Consequences

- **No Python code knows React; no JS code knows TradingView or BSE.** Each half is testable alone.
- **The two editions cannot disagree about a number, because there is only one number.** Parity is structural
  rather than policed — the strongest property this design has.
- `--props` takes a file, so a re-render from the snapshot is a guaranteed match; the rebuild promise depends
  on this.
- Adding a card means adding a **key** to the bundle and a **label** to two tables — never a string to the
  bundle. A display string that appears in `facts.json` is a bug, not a shortcut.
