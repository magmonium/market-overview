"""The copy budget — 0085_08's hard gate.

Ticket 01 sets the reading budget: **≈2.5–3.5 s per on-screen line**, and "a card that cannot be read
inside its slot gets **cut, not sped up**". Ticket 20 makes it binding: the timeline is **identical**
across editions and every slot must hold the **longer** of Bengali and English.

⚠️ **The model, as settled with the operator:** for a table-ish card a **row is the unit** — the name and
its figures are read together, not one figure at a time — and prose and strips are costed at ticket 01's
per-line rate. Without that rule a 13-row × 8-column scoreboard reads as 104 units, which would cost it
260 s against an 18 s slot, and a rule that makes every card impossible is not a rule.

⚠️ **Furniture is not content.** Card titles, table headers and the persistent footer disclosure are the
frame the content sits in, not copy to be read; the footer's own line is charged **once**, to the
disclosure pre-roll that exists to carry it. Charging it per card would add 14 units to a brief that has
no room, for a line the viewer reads once and then stops seeing.

⚠️ **Width is measured in a real browser, not estimated.** Only the browser knows Kohinoor Bangla's
metrics, and Bengali conjuncts make width-per-character nothing like English's. The first measurement
already overturned an assumption in the map: Bengali and English are **the same average width** (ratio
0.998 over 40 labels), and the widest strings are frequently the *English* ones.
"""
from __future__ import annotations

import json
import math
import pathlib
import re
import subprocess
from dataclasses import dataclass

from market_overview import store
from market_overview import display

# Ticket 01's band. `FLOOR` is what a slot must clear; `COMFORT` is what it should clear to breathe.
FLOOR = 2.5
COMFORT = 3.5

CAP_SECONDS = 180

FONT = '"Kohinoor Bangla", system-ui, -apple-system, sans-serif'
DEFAULT_BROWSERS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)

# The card's own content box, from `Card`'s padding at 1920x1080: 1920 - 2x96.
CONTENT_WIDTH = 1728
# The two full-bleed cards (`Disclosure`, `ColdOpen`) set their own padding: 1920 - 2x160.
FULL_BLEED_WIDTH = 1600


class BrowserMissing(RuntimeError):
    """No browser to measure with. The budget cannot be guessed."""


def _browser(explicit: str | None = None) -> str:
    for candidate in ([explicit] if explicit else []) + list(DEFAULT_BROWSERS):
        if candidate and pathlib.Path(candidate).exists():
            return candidate
    raise BrowserMissing(
        "no Chrome or Chromium found to measure text with — pass chrome=... or install one. "
        "The budget is not something to estimate: Bengali and English differ per string, not per language."
    )


@dataclass(frozen=True)
class Run:
    """One line of text to measure: what it says, how big, and how much room it has."""

    key: str
    text: str
    size: int
    weight: int = 400
    width: int = CONTENT_WIDTH


# --- what each card shows ---------------------------------------------------------------
# These mirror the components. ⚠️ Two of them are the renderer's own caps, and a test asserts they still
# match `blocks.tsx` — a silent cap change would otherwise move the budget without moving the timeline.

def _calendar_caps() -> tuple[int, int]:
    source = (store.root() / "remotion" / "blocks.tsx").read_text(encoding="utf-8")
    actions = re.search(r"\(corporate_actions \?\? \[\]\)\.slice\(0, (\d+)\)", source)
    announcements = re.search(r"\(announcements \?\? \[\]\)\.slice\(0, (\d+)\)", source)
    if not actions or not announcements:
        raise AssertionError("the calendar's caps moved — the budget no longer knows what is on the card")
    return int(actions.group(1)), int(announcements.group(1))


def figures(key: str, bundle: dict) -> int:
    """Rows, tiles or standalone figures on a card — the units that are not prose."""
    if key == "disclosure":
        return 0
    if key == "cold_open":
        return 1  # the headline percentage
    if key == "indexes":
        return len(bundle.get("indexes", []))
    if key == "leaders":
        leaders = bundle.get("leaders") or {}
        return len(leaders.get("gainers", [])) + len(leaders.get("losers", []))
    if key == "most_active":
        return 1 if bundle.get("most_active") else 0
    if key in ("sectors", "heat_map"):
        # ⚠️ Ticket 26's "one list serves both blocks": the heat map is the scoreboard again, so it costs
        # the same as the scoreboard. That is the fact this gate exists to surface, not a rounding error.
        return len(bundle.get("sectors", []))
    if key == "breadth":
        return 2 if bundle.get("breadth") else 0
    if key == "dma":
        return 3 if bundle.get("dma") else 0
    if key == "flows":
        return 2 if bundle.get("flows") else 0
    if key == "dependencies":
        return len(bundle.get("dependencies", []))
    if key == "broader":
        return len(bundle.get("broader", []))
    if key == "calendar":
        actions, announcements = _calendar_caps()
        return (
            min(actions, len(bundle.get("corporate_actions", [])))
            + len(bundle.get("ipos", []))
            + min(announcements, len(bundle.get("announcements", [])))
        )
    if key == "close":
        return 0

def _percent(value: float | None) -> str:
    """⚠️ Kept as a thin alias: the budget's own callers and tests name it, and it delegates so there is still one
    implementation. See `display.py` for why the mirrors exist at all."""
    return display.percent(value)


def _hardest_label(bundle: dict) -> str:
    """⚠️ Likewise a thin alias — the slug, as the budget's own tests expect."""
    row = display.headline(bundle)
    return "" if row is None else row.get("label_key", "")


def prose(key: str, bundle: dict, labels: dict) -> list[Run]:
    """The lines of real copy on a card. Its furniture — title, headers, footer — is not charged."""
    date = (bundle.get("meta") or {}).get("date", "")
    if key == "disclosure":
        return [Run("disclosure.line", labels["disclosure"], 44, width=FULL_BLEED_WIDTH)]
    if key == "cold_open":
        # ⚠️ The rule now lives in `display.py` (0085_13) rather than as a private copy here. The metadata needs the
        # same figure, and two Python copies of "the day's headline" is the drift this codebase spent 0085_12
        # removing on the JavaScript side.
        return [Run("cold_open.heading", f"{display.headline_label(bundle, labels)} · {date}", 40, width=FULL_BLEED_WIDTH)]
    if key == "close":
        first = (bundle.get("indexes") or [{}])[0]
        return [
            Run("close.as_on", f"{labels['furniture']['as_on']} · {date}", 40),
            Run(
                "close.headline",
                f"{labels['indexes'][first.get('label_key', '')]} "
                f"{(first.get('window') or {}).get('change') and display.percent((first['window'])['change']) or ''}".strip(),
                76,
            ),
            Run("close.tomorrow", f"{labels['blocks']['close']} →", 34),
        ]
    return []


_PAGE = """<!doctype html><meta charset="utf-8"><pre id="out">pending</pre>
<script>
const RUNS = %s;
const FAMILY = %s;
const ctx = document.createElement('canvas').getContext('2d');
const width = (t, s, w) => { ctx.font = `${w} ${s}px ${FAMILY}`; return ctx.measureText(t).width; };
// Greedy wrap at the real box, with the browser's own metrics — an estimate would be exactly the thing
// this harness exists to avoid.
const lines = (t, s, w, box) => {
  ctx.font = `${w} ${s}px ${FAMILY}`;
  if (ctx.measureText(t).width <= box) return 1;
  let count = 1, line = '';
  for (const word of t.split(/\\s+/)) {
    const next = line ? line + ' ' + word : word;
    if (line && ctx.measureText(next).width > box) { count += 1; line = word; }
    else { line = next; }
  }
  return count;
};
const out = RUNS.map(r => ({
  key: r.key,
  width: width(r.text, r.size, r.weight),
  lines: lines(r.text, r.size, r.weight, r.width),
  box: r.width,
}));
document.getElementById('out').textContent = 'RESULT' + JSON.stringify(out) + 'END';
</script>"""


def measure(runs: list[Run], *, chrome: str | None = None) -> dict[str, dict]:
    """Width and wrapped-line count per run, measured in a real browser."""
    if not runs:
        return {}
    payload = json.dumps(
        [{"key": r.key, "text": r.text, "size": r.size, "weight": r.weight, "width": r.width} for r in runs],
        ensure_ascii=False,
    )
    page = pathlib.Path(store.root()) / ".measure.html"
    page.write_text(_PAGE % (payload, json.dumps(FONT)), encoding="utf-8")
    try:
        completed = subprocess.run(
            [
                _browser(chrome),
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--virtual-time-budget=10000",
                "--dump-dom",
                f"file://{page}",
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )
    finally:
        page.unlink(missing_ok=True)

    start = completed.stdout.find("RESULT")
    end = completed.stdout.find("END", start)
    if start < 0 or end < 0:
        raise BrowserMissing(f"measurement page produced no result:\n{completed.stderr[-1200:]}")
    return {row["key"]: row for row in json.loads(completed.stdout[start + 6:end])}


@dataclass(frozen=True)
class Card:
    """One block's cost. `units` is the **worse** of the two languages — the timeline is shared, so the
    slot has to hold whichever edition is more expensive (ticket 20)."""

    key: str
    by_language: dict
    slot: int

    @property
    def units(self) -> int:
        return max(self.by_language.values()) if self.by_language else 0

    @property
    def required(self) -> float:
        return self.units * FLOOR

    @property
    def comfort(self) -> float:
        return self.units * COMFORT

    @property
    def verdict(self) -> str:
        if self.slot < self.required:
            return "OVER"
        return "tight" if self.slot < self.comfort else "ok"

    @property
    def longer(self) -> str:
        """Which edition sets the slot. Almost never the whole language — it is string by string."""
        if len(self.by_language) < 2:
            return "-"
        bn, en = self.by_language["bn"], self.by_language["en"]
        return "-" if bn == en else ("bn" if bn > en else "en")


def _runs(key: str, bundle: dict, labels: dict, lang: str) -> list[Run]:
    # ⚠️ The language is baked into the run key. Without it the two editions' runs collide and one
    # silently overwrites the other, which would make the gate report a language it never measured.
    return [Run(f"{lang}:{r.key}", r.text, r.size, r.weight, r.width) for r in prose(key, bundle, labels)]


def report(date: str, *, chrome: str | None = None) -> tuple[list[Card], dict]:
    """Per-card reading cost in both editions, and the build's total against the cap."""
    bundle = json.loads((store.dir_for(date) / store.FACTS).read_text(encoding="utf-8"))
    tables = {
        lang: json.loads((store.root() / "remotion" / f"copy.{lang}.json").read_text(encoding="utf-8"))
        for lang in ("bn", "en")
    }
    slots = {block["key"]: block["seconds"] for block in bundle["timeline"]["blocks"]}

    runs = [r for lang in ("bn", "en") for key in slots for r in _runs(key, bundle, tables[lang], lang)]
    measured = measure(runs, chrome=chrome)

    cards: list[Card] = []
    for key, slot in slots.items():
        per_language = {}
        for lang in ("bn", "en"):
            lines = sum(measured[run.key]["lines"] for run in _runs(key, bundle, tables[lang], lang))
            per_language[lang] = figures(key, bundle) + lines
        cards.append(Card(key, per_language, slot))

    summary = {
        "units": sum(card.units for card in cards),
        "required": sum(card.required for card in cards),
        "comfort": sum(card.comfort for card in cards),
        "slot": sum(card.slot for card in cards),
        "cap": CAP_SECONDS,
        "generated_by": "remotion/copy.{bn,en}.json + store/<date>/facts.json",
    }
    return cards, summary


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Report the per-card copy budget in both editions.")
    parser.add_argument("--date", required=True)
    parser.add_argument("--chrome", default=None, help="browser to measure with")
    args = parser.parse_args(argv)

    cards, summary = report(args.date, chrome=args.chrome)
    print(f"copy budget — {args.date}   {FLOOR}-{COMFORT} s per unit, cap {CAP_SECONDS} s\n")
    print(f"{'block':16} {'bn':>4} {'en':>4} {'units':>6} {'need':>7} {'comfort':>8} {'slot':>6}  longer  verdict")
    for card in cards:
        print(
            f"{card.key:16} {card.by_language['bn']:4} {card.by_language['en']:4} {card.units:6} "
            f"{card.required:7.1f} {card.comfort:8.1f} {card.slot:6}  {card.longer:>6}  {card.verdict}"
        )
    print()
    print(f"units {summary['units']}   need {summary['required']:.1f} s   comfort {summary['comfort']:.1f} s")
    print(f"as built {summary['slot']} s   cap {summary['cap']} s   headroom {summary['cap'] - summary['slot']} s")
    verdict = "FITS" if summary["required"] <= summary["cap"] else "OVER THE CAP"
    print(f"required vs cap: {verdict} by {abs(summary['required'] - summary['cap']):.1f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


