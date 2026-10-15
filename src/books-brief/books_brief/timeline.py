"""Ticket 06 — how long each slide gets, and ticket 07's entrance ceiling.

⚠️ **The dwell follows the interest curve, not a flat reading time.** A hundred books at a full reading time each does
not fit three minutes, so the top of the chart is *read* and the tail is *glanced* — 6 + 35 + 40 + 42 + 40 + 6 = **169
seconds** against the brief's 180-second cap.

⚠️ **The honest consequence is not hidden.** Below about rank 50 a slide carries more than an eye can take in, which is
exactly why ticket 15's description carries the full list in two tiers. The video gives the shape; the description
gives the data.
"""
from __future__ import annotations

import dataclasses

#: The host repo's frame rate, so both products' timelines are expressed the same way.
FPS = 30

#: ⚠️ The brief's own cap (`timeline.CAP_SECONDS`). Kept as the same number deliberately: this product has no reason to
#: be longer, and ~11 seconds of headroom absorbs a title repeated across charts (the superset, ticket 14).
CAP_SECONDS = 180

INTRO_SECONDS = 6.0
OUTRO_SECONDS = 6.0

#: ⚠️ **The bands, and the ranks are the interest curve.** `(first rank, last rank, seconds each)`.
BANDS: tuple[tuple[int, int, float], ...] = (
    (1, 10, 3.5),
    (11, 30, 2.0),
    (31, 60, 1.4),
    (61, 100, 1.0),
)

#: ⚠️ Ticket 07: the host repo's `enter()` defaults to a 0.4 s entrance, and **its own comment** names the failure —
#: *"an entrance that runs for a fifth of a card eats a fifth of the time there is to read a number."*
ENTER_CEILING = 0.4

#: ⚠️ So the span is capped at **15 % of the dwell**, which is what stops a 1.0 s tail slide from spending 40 % of
#: itself arriving.
ENTER_SHARE = 0.15


def dwell_for(rank: int) -> float:
    """Seconds the slide at `rank` is shown for."""
    for first, last, seconds in BANDS:
        if first <= rank <= last:
            return seconds
    raise KeyError(f"no band covers rank {rank}")


def total_seconds(books: int = 100) -> float:
    """The whole run: the intro, every band, and the outro.

    ⚠️ Summed from `BANDS` rather than written as a literal, so the table and the total cannot drift apart — a total
    that disagreed with the dwells would be a run that overran its cap by exactly the amount nobody checked.
    """
    body = sum(
        seconds * (min(last, books) - first + 1)
        for first, last, seconds in BANDS
        if first <= books
    )
    return INTRO_SECONDS + body + OUTRO_SECONDS


def span_for(dwell: float) -> float:
    """The entrance's span, in seconds, for a slide that is on screen for `dwell`.

    ⚠️ **Motion must fit *inside* the reading window, never consume it** — so the span is the smaller of the dwell's
    15 % and the 0.4 s the host repo's `enter()` already defaults to.
    """
    return min(ENTER_CEILING, dwell * ENTER_SHARE)


@dataclasses.dataclass(frozen=True)
class Block:
    """One slot in the run: what it is, where it starts, and how long it lasts — **in frames**.

    ⚠️ **`enter_frames` rides on the block rather than being recomputed by the renderer.** `span_for` is a rule, and a
    second implementation of it in TypeScript would be a second opinion about how long an entrance lasts — the exact
    drift the brief's own `MarketBrief.tsx` refuses: *"the timeline comes from `props.timeline`, not from this file."*

    ⚠️ `start` rather than `from`, because `from` is a Python keyword. It is the same number either way.
    """

    id: str
    key: str
    start: int
    duration: int
    enter_frames: int
    #: ⚠️ Which book this slot shows — `None` for the intro and the outro, which show no book at all.
    rank: int | None = None


def schedule(books: int = 100) -> tuple[Block, ...]:
    """The whole run, slot by slot — the intro, one slide per book, the outro.

    ⚠️ **A countdown: rank `books` first, rank 1 last.** The chart builds to its number one rather than spending it in
    the opening seconds — and each rank keeps its own dwell, so the read top of the chart is now the run's climax.

    ⚠️ **The dwell is a data decision, so the renderer is handed frames and holds no table of its own** (ticket 06).
    A renderer that recomputed the bands would be a second copy of the interest curve, and the copy that fell behind
    would be the one that shipped.

    ⚠️ **A short chart is a shorter run, not a slower one.** `books` is whatever the chart actually holds, so a chart
    with sixty-three rows starts at rank 63 rather than padding out from a hundred — the same *degrade to omission* rule
    the blocks follow.
    """
    slots: list[Block] = []

    at = 0
    intro = round(INTRO_SECONDS * FPS)
    slots.append(
        Block(
            id="intro",
            key="intro",
            start=at,
            duration=intro,
            enter_frames=round(span_for(INTRO_SECONDS) * FPS),
        )
    )
    at += intro

    for rank in range(books, 0, -1):
        dwell = dwell_for(rank)
        duration = round(dwell * FPS)
        slots.append(
            Block(
                id=f"{rank:03d}-book",
                key="book",
                start=at,
                duration=duration,
                enter_frames=round(span_for(dwell) * FPS),
                rank=rank,
            )
        )
        at += duration

    outro = round(OUTRO_SECONDS * FPS)
    slots.append(
        Block(
            id="outro",
            key="outro",
            start=at,
            duration=outro,
            enter_frames=round(span_for(OUTRO_SECONDS) * FPS),
        )
    )
    return tuple(slots)


def total_frames(books: int = 100) -> int:
    """The run's length in frames — **summed from `schedule`, never written as a literal.**

    ⚠️ Derived rather than declared, so the composition's length and the slots inside it cannot disagree. A run whose
    `durationInFrames` was a frame short would truncate the outro; a frame long would hold on a frozen last frame —
    and both would look like a render problem rather than an arithmetic one.
    """
    slots = schedule(books)
    last = slots[-1]
    return last.start + last.duration
