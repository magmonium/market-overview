"""The locked running order, and which blocks this date can actually fill.

Ticket 01 fixes fourteen cards in a fixed order at fixed slots. The timings live **in the bundle**
rather than in the renderer for one reason: block durations are a data decision, not a drawing one —
[Copy-budget gate] will later resize each slot to `max(bn, en)`, and that measurement happens in
Python where the label tables are measured.

⚠️ A block whose data is absent is **dropped, not shown empty**, and its slot is removed rather than
redistributed — so a thin day produces a *shorter* brief, never a slower one. That is ticket 01's
rule, enforced here where the data is, so the renderer never has to decide whether it has enough.
"""
from __future__ import annotations

# (ticket-01 block id, renderer key, seconds). Ids are stable and deliberately not sequential:
# block 10 was left vacant when insider activity retired and FII/DII later took it.
#
# ⚠️ **The slots are no longer judgements — they are the measured reading time**, from 0085_08's copy
# budget (`market_overview.copybudget`): units x 2.5 s, where a table-ish card's unit is a **row** and
# prose is a line. Halves are deliberate and exact; `running_order` rounds to whole frames.
#
# ⚠️ **`heat_map` is cut, and it is the only cut.** Ticket 26's rule is that one list serves both the
# scoreboard and the heat map — so the heat map cost the same thirteen units as the scoreboard, 32.5 s to
# say the same thirteen sectors twice. With it in, the brief needed 207.5 s against a 180 s cap; with it
# out, this lands at 175.0 s exactly. The component is still in `blocks.tsx` and still registered in
# `MarketBrief`; re-adding it here is one line, and it is one line because someone should have to decide
# again rather than rediscover it.
TIMELINE: tuple[tuple[str, str, float], ...] = (
    ("0", "disclosure", 5),
    ("1", "cold_open", 5),
    ("2", "indexes", 12.5),
    ("9", "leaders", 25),
    ("13", "most_active", 2.5),
    ("3", "sectors", 32.5),
    ("7", "breadth", 5),
    ("8", "dma", 7.5),
    ("10", "flows", 5),
    ("5", "dependencies", 22.5),
    ("6", "broader", 5),
    ("11", "calendar", 40),
    ("12", "close", 7.5),
)

BUILD_SECONDS = sum(seconds for _, _, seconds in TIMELINE)
CAP_SECONDS = 180

FPS = 30

# Which bundle keys each block needs. A block whose data is absent is dropped whole rather than shown
# empty. ⚠️ `cold_open` and `close` both read the index scoreboard — the cold open picks the day's headline
# (Nifty 50) from it and the close quotes it too — so declaring no dependency would schedule a card whose
# data was absent, which is a crash rather than a dropped block.
NEEDS: dict[str, tuple[str, ...]] = {
    "disclosure": (),
    # ⚠️ The cold open reads the index scoreboard — it is the block that states the day's headline figure — so a
    # bundle without one must not schedule it. Declaring no dependency would let the timeline schedule a card whose
    # data is absent, which is a crash rather than a dropped block.
    "cold_open": ("indexes",),
    "indexes": ("indexes",),
    "leaders": ("leaders",),
    "most_active": ("most_active",),
    "sectors": ("sectors",),
    "breadth": ("breadth",),
    "dma": ("dma",),
    "flows": ("flows",),
    "dependencies": ("dependencies",),
    "broader": ("broader",),
    # ⚠️ Any one of the three is enough — block 11 is the one block with no always-present part.
    "calendar": ("corporate_actions", "ipos", "announcements"),
    # ⚠️ `()`: the close quotes no figure any more — it ends on a thank-you — so it needs nothing from the bundle and
    # is always scheduled. It used to declare `indexes` for the headline it repeated; see the note in `blocks.tsx`.
    "close": (),
}


def block_is_present(key: str, bundle: dict) -> bool:
    needs = NEEDS[key]
    return not needs or any(need in bundle for need in needs)


def running_order(bundle: dict) -> list[dict]:
    """The blocks this date will actually render, in order, with their slots.

    Returns only the present ones, so the renderer's total is the real runtime rather than a
    scheduled one, and `frame` boundaries can be computed from it without a second opinion.
    """
    order: list[dict] = []
    frame = 0
    for block_id, key, seconds in TIMELINE:
        if not block_is_present(key, bundle):
            continue
        # ⚠️ Rounded, not truncated: slots come in halves (a 2.5 s card is 75 frames) and a float frame
        # count would reach the renderer as a non-integer duration.
        frames = round(seconds * FPS)
        order.append(
            {
                "id": block_id,
                "key": key,
                "seconds": seconds,
                "from": frame,
                "duration": frames,
            }
        )
        frame += frames
    return order


def total_frames(order: list[dict]) -> int:
    return sum(block["duration"] for block in order)


def total_seconds(order: list[dict]) -> float:
    """The run's real length, in seconds.

    ⚠️ From the **sum of rounded frames**, not the sum of the scheduled slots: at 30 fps a 2.5 s slot is 75 frames
    exactly, and any slot that were not would otherwise make the bed a fraction of a frame longer or shorter than
    the picture (0085_11's "no drift at the close"). This is the number the bed is trimmed to, so it must be the
    number the renderer actually uses.
    """
    return total_frames(order) / FPS
