# 0003 — The recorded run is the interface

- Status: accepted
- Date: 2026-10-13

## Context

The menu asks four things — song, title, themes, wave form — and a menu that leaves no trace makes a rebuild
impossible: the second run's answers become the product, and the first run's video becomes unreproducible.

The brief answered the same question with a per-date snapshot (`store/<date>/facts.json`, its ADR 0003). The reel's
input is not a fetch, so its snapshot is different in kind: it is a **decision**.

## Decision

**`store/<song>/run.json` is the boundary.** It is committed, it holds the four answers plus `fps`, the measured
duration, the master's name/size/**`sha256`** and the toolchain that measured it — and it is a **contract**, not a
cache:

- the menu writes it **once per song**, when there is no record;
- every later run **replays** it rather than asking again;
- the props file a render is given is **derived from it** and nothing else.

## Consequences

- ⚠️ **A recorded run describes one file.** If the master's digest no longer matches, the run **refuses**. This is
  the brief's session-date guard transplanted: it refuses to publish yesterday's numbers; this refuses to re-cut a
  video under a title somebody approved for a *different* take. Every other artefact would be internally
  consistent, which is exactly why nothing else can see it.
- ⚠️ **A flag that disagrees with the record is refused, not obeyed** — and the refusal names the file to remove to
  answer again. Obeying it would make the first video unreproducible and the second one undocumented: the same
  defect from both ends.
- ⚠️ **The toolchain is recorded but never guarded.** Which `ffprobe` measured the piece is *provenance* — a
  different one is a legitimate rebuild, so a mismatch is printed rather than refused. Identity and provenance are
  different questions, and only one of them is a digest.
- **A record written before a field existed still replays.** An absent provenance is absent, not malformed:
  throwing away answers somebody approved in order to protect a diagnostic would be the wrong trade.
- **N themes become N jobs in the recorded order**, never sorted — so a run that dies halfway leaves a folder whose
  remaining work is predictable from the record alone.

## Addendum — the caption gained a language

⚠️ `run.json` gained **`lang`**: which script the still's caption is written in (*the caption*, in `CONTEXT.md`). It
is a fifth answer that is **never asked for** — the conductor derives it from the script of the title, and `--lang`
settles it when the title cannot speak (an instrumental, or a Latin transliteration of a Bengali song).

It is recorded anyway, for this ADR's own reason: a rebuild whose caption switched language would not be the
delivery somebody approved, and nothing downstream could see it.

⚠️ **A record written before the field existed comes back empty, and the conductor fills it** from the title. The
reader does not choose a language — that is policy, and policy lives in the conductor, exactly as the menu and the
catalogues already do.
