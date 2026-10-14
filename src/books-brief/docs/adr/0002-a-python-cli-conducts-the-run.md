# 0002 — A Python CLI conducts the run, and only the parse is tested

- Status: accepted
- Date: 2026-10-14

## Context

A run has to fetch five vendors, corroborate what they said, rank it, snapshot it, render four videos and package
them. The host repo already settles *who* conducts: `docs/adr/0002` gives the brief a Python CLI that owns the run
while the JS layer only renders, and `song-video` does the same. This product inherits that shape rather than
re-deciding it.

What is *not* inherited is where the tests go, and that is this ADR's real subject.

Every source here is an external boundary: an API, or an HTML page behind Akamai. A suite that reached the network
would be slow, flaky, and would fail for reasons that are not the product's fault — and the host repo's rule is
explicit: *"the suite stays hermetic — nothing in it reaches the network."*

## Decision

**One conductor — `cli` — and every source client split into `fetch()` and `parse(payload)`.**

⚠️ **The `parse` is the seam; the `fetch` is the boundary.** The brief draws the same line in
`_degrade(day, name, fetch, parse, default)` — *"Fetch one non-spine feed, snapshot it, shape it"* — for two reasons: a
parser is a **pure function of bytes**, and a pure function can be tested against a **committed fixture**.

- Every client exposes `parse(payload) -> list[Row]` and `fetch(chart) -> list[Row]`.
- ⚠️ **Only `parse` is tested.** `fetch` is the network call, and it is deliberately untested.
- ⚠️ Fixtures are **recorded responses, committed** — the habit this repo already keeps, where `store/<date>/raw/*.json`
  is committed *"so a day can be rebuilt without re-fetching"*.
- ⚠️ A fixture that is **hand-built rather than recorded says so in the test that uses it**, so a parser is never
  trusted on an invented shape. `tests/test_fetch_nyt.py` carries exactly that note.

## Consequences

- ✅ **The suite is hermetic and fast** — 38 tests in under 0.1 s, no network, no browser, no fixtures larger than a
  few kilobytes.
- ⚠️ **The five scrape parsers cannot be finished without a recording.** Amazon.in, Anandabazar, Rokomari, PW and
  Indie all serve HTML whose shape is undocumented and changes; a fixture built from the *rendered text* would produce
  a parser that passes its test and fails on the real page. **The honest fixtures come from a recording the operator
  makes, once, deliberately** — and until then those parsers are not written.
- ⚠️ **`fetch` failures degrade rather than crash.** A vendor that does not answer makes its chart **absent**; the run
  refuses only when nothing could be built.
