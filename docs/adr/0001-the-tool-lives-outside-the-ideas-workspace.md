# 0001 — The tool lives outside the `ideas` workspace

- Status: accepted
- Date: 2026-12-12

## Context

The design was specified in the `ideas/` planning workspace, which holds `nx/` and `api/` as git submodules
and, per `SUBMODULES.md`, **"only tracks pointers + planning docs — never source code."**

The tool must be standalone: it is not an `nx/` or `api/` feature and edits neither.

## Decision

`market-overview` is its **own repository**, cloned **outside** the planning workspace at
`~/Documents/magmonium/market-overview` — a sibling of `ideas/`, alongside `api/` and `crawl/`.

It is **not** a third submodule. It is not referenced from `ideas/` by any pointer.

## Consequences

- `ideas/` stays planning-only and gains no pointer, so nothing about the tool's location is recorded by git.
  ⚠️ **The wayfinder map and the task plan are the only link between the two**, and both name the path
  explicitly — losing that sentence would lose the connection.
- The tool owns its whole root, including `resource/`, `output/` and `store/`, with no parent repo to satisfy.
- An earlier revision made it a submodule at `ideas/market-overview/`. Reversed before any code existed,
  because it bought nothing the sibling clone does not and added a pointer to maintain.
