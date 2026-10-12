"""The package's SEO text — issue 13. (0085_13)

⚠️ **Written natively per language, not translated.** The two tables below are separate trees: Bengali and English
search behaviour does not map one-to-one, so the keyword that earns an impression in one is not the translation of the
keyword that earns it in the other. What *is* shared is the logic — which figures get quoted, in what order — because a
second copy of that logic is where a wrong number would enter the product under time pressure.

⚠️ **Generated from the bundle, never written by hand.** Every number here traces to a `facts.json` key through the
label-and-slot discipline the video uses, so the description cannot disagree with the video. Daily hand-writing is not
viable and would be the single most likely place for a wrong figure to appear, because it would be done last.

⚠️ **The disclaimer is repeated here, not just on screen.** The description is the surface that survives somewhere
other than the video — quoted, screenshotted, syndicated — so it carries its own copy of the attribution and the
not-advice line. Same rule as the card furniture, one surface further out.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Any

from market_overview import display, store

#: YouTube's limits. ⚠️ The tag budget is in **characters**, not tags, which is the trap: a handful of long sector
#: names blows it without anything looking wrong.
TITLE_LIMIT = 100
DESCRIPTION_LIMIT = 5000
TAG_BUDGET = 500

#: ⚠️ **Exceed 15 hashtags and YouTube ignores *all* of them** — so a long hashtag block is worse than a short one.
#: This emits exactly three, which is also all that displays above the title.
HASHTAGS_MAX = 15
HASHTAGS_SHOWN = 3

#: How many rows a list section quotes. Enough to be useful, short enough that the description stays scannable.
LIST_ROWS = 6


@dataclass(frozen=True)
class Metadata:
    """One edition's package text, and the JSON the deferred upload step will read."""

    lang: str
    date: str
    title: str
    description: str
    tags: list[str]
    hashtags: list[str]
    thumbnail: str
    video: str
    bundle_hash: str
    warnings: list[str] = field(default_factory=list)

    def as_json(self) -> dict[str, Any]:
        """⚠️ The thumbnail and video are **named explicitly**, so an uploader needs nothing but the language folder.
        That is what "self-contained by construction" means, and it is why the filenames carry date and language too.
        """
        return {
            "lang": self.lang,
            "date": self.date,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "hashtags": self.hashtags,
            "video": self.video,
            "thumbnail": self.thumbnail,
            "bundle_hash": self.bundle_hash,
        }

    def as_text(self) -> str:
        """⚠️ **Plain text only — no Markdown, no markup.** YouTube descriptions are plain text, so a heading marker
        or an asterisk pastes in as literal junk. What is in this string is exactly what goes in the box.

        Fields are labelled because a human is pasting them into three separate boxes, and the tags are on one line so
        the whole block can be selected in one gesture.
        """
        return "\n".join(
            (
                f"TITLE\n{self.title}",
                "",
                f"DESCRIPTION\n{self.description}",
                "",
                f"TAGS\n{', '.join(self.tags)}",
                "",
            )
        )


# ── the two native trees ──────────────────────────────────────────────────────────────────────────────────
#
# ⚠️ **Sentence shapes, per language, authored natively.** Both trees have exactly the same keys — a test asserts it —
# so the *structure* of the description is identical across editions while the wording is each language's own. That
# split is the point: parity is about which facts are stated and in what order, not about the words used to state
# them, and a translation layer would quietly optimise the Bengali for English queries.

PHRASES: dict[str, dict[str, str]] = {
    "en": {
        "headline": "{pct} · {index} — the biggest index move of the {date} session",
        "indices": "Indices: {items}",
        "sectors": "Sectors: {items}",
        "cues": "Global cues: {items}",
        "breadth": "Advance/decline: {rising} up, {falling} down, {flat} unchanged — of {counted} stocks.",
        "dma": "Above moving averages: {sma50} above the 50-day, {sma100} the 100-day, {sma200} the 200-day, of {eligible} stocks.",
        "flows": "FII/FPI net {fii}, DII net {dii} (crore rupees).",
        "gainers": "Top gainers: {items}",
        "losers": "Top losers: {items}",
        "most_active": "Most active: {symbol} {change} · {relative}",
        "actions": "Corporate actions: {items}",
        "ipos": "IPOs opening: {items}",
        "announcements": "Company announcements: {items}",
        # ⚠️ The closing line is the **full** statement with attribution, against the one compact line at the top.
        # Issue 13: a description whose risk warning is only findable after "more" is not really carrying one.
        "closing": "{attribution} · {disclosure}",
    },
    "bn": {
        "headline": "{pct} · {index} — {date} সেশনের সবচেয়ে বড় সূচক পরিবর্তন",
        "indices": "সূচক: {items}",
        "sectors": "সেক্টর: {items}",
        "cues": "বৈশ্বিক নির্দেশক: {items}",
        "breadth": "উত্থান-পতন: {rising}টি বেড়েছে, {falling}টি কমেছে, {flat}টি অপরিবর্তিত — মোট {counted}টি শেয়ারে।",
        # ⚠️ The classifier `টি` cannot follow a percent sign — `21%টি` is not Bengali. The count moves to the clause
        # head where it belongs, and the three figures stay unadorned.
        "dma": "গড় দামের উপরে (মোট {eligible}টি শেয়ারে): ৫০ দিনে {sma50}, ১০০ দিনে {sma100}, ২০০ দিনে {sma200}।",
        "flows": "বিদেশি (FII/FPI) নিট {fii}, দেশি প্রতিষ্ঠান (DII) নিট {dii} (কোটি টাকা)।",
        "gainers": "শীর্ষ লাভ: {items}",
        "losers": "শীর্ষ ক্ষতি: {items}",
        "most_active": "সবচেয়ে সক্রিয়: {symbol} {change} · {relative}",
        "actions": "কর্পোরেট অ্যাকশন: {items}",
        "ipos": "আইপিও খুলছে: {items}",
        "announcements": "কোম্পানির ঘোষণা: {items}",
        "closing": "{attribution} · {disclosure}",
    },
}


# ── the shape of the description ──────────────────────────────────────────────────────────────────────────


def _join(items: list[str], separator: str = " · ") -> str:
    return separator.join(items)


def formatted_date(date: str, labels: dict[str, Any]) -> str:
    """`2026-10-12` → `12 Oct 2026` / `12 অক্টোবর 2026`.

    ⚠️ **Latin digits with a native month name**, which is the hybrid the video already uses — its labels are Bengali
    and its figures are numerals (the review item 0085_10 raised). Writing the day as `১২` here would make the
    description the one surface where a reader has to convert.
    """
    year, month, day = date.split("-")
    return f"{int(day)} {labels['metadata'][f'month_{int(month)}']} {year}"


def _rows(rows: list[dict[str, Any]], labels: dict[str, Any], group: str, digits: int = 2) -> list[str]:
    """`Label +0.30%` per row, label from the shared glossary.

    ⚠️ A row whose value is `None` is **omitted, never zero-filled** — the video's degrade-to-omission rule, applied
    to prose. A `+0.00%` the exchange never printed is a fabricated number.
    """
    out = []
    for row in rows:
        amount = (row.get("window") or {}).get("change")
        if amount is None:
            continue
        key = row.get("label_key") or row.get("sector_key") or ""
        out.append(f"{(labels.get(group) or {}).get(key, key)} {display.percent(amount, digits)}")
    return out


def _quotes(rows: list[dict[str, Any]] | None) -> list[str]:
    out = []
    for row in rows or []:
        if row.get("change") is None:
            continue
        out.append(f"{row.get('symbol', '')} {display.percent(row['change'])}")
    return out


def _truncate(text: str, limit: int = 70) -> str:
    """Cut on a **word boundary** and mark it.

    ⚠️ A bare slice ends mid-word — the first run produced `... of SEBI (` — which reads as a corrupted feed rather
    than as an abbreviation, and it does so in the surface a search engine indexes.
    """
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "…"


def _whole_percent(value: float | None) -> str:
    """`21%` — ⚠️ **not** `display.percent`, because `dma.above` is already a percentage and the video prints it as a
    whole number (`Dma` in `blocks.tsx`: `${value.toFixed(0)}%`). Signing and decimalising it here would make the
    description disagree with the card about the same number.
    """
    return display.DASH if value is None else f"{value:.0f}%"


def _sections(date: str, bundle: dict[str, Any], labels: dict[str, Any], lang: str) -> list[str]:
    """The description, in the video's block order. A section whose data is absent is **skipped, not shown empty**.

    ⚠️ **The order mirrors the running order** so a viewer who watches and then reads finds the same sequence, and a
    reader who skims is not surprised by the video. It is one function rather than nine for that reason: the order is
    the contract, and it should not be possible to reorder one edition by accident.
    """
    phrases = PHRASES[lang]
    text = labels["metadata"]
    lines: list[str] = []

    # 1 — the compact disclosure and the headline line, together inside the ~150 characters shown before "more".
    # ⚠️ The warning goes **first**: one findable only after the fold is not really carrying a warning.
    featured = display.headline_label(bundle, labels)
    if featured:
        headline = phrases["headline"].format(
            pct=display.percent(display.headline_change(bundle)),
            index=featured,
            date=formatted_date(date, labels),
        )
        lines.append(f"{text['disclosure_short']}\n{headline}")

    # 2 — the short summary, mirroring blocks 2, 9 and 13.
    indexes = _rows(bundle.get("indexes") or [], labels, "indexes")
    if indexes:
        lines.append(phrases["indices"].format(items=_join(indexes[:LIST_ROWS])))
    gainers = _quotes((bundle.get("leaders") or {}).get("gainers"))
    losers = _quotes((bundle.get("leaders") or {}).get("losers"))
    if gainers:
        lines.append(phrases["gainers"].format(items=_join(gainers[:3])))
    if losers:
        lines.append(phrases["losers"].format(items=_join(losers[:3])))
    active = bundle.get("most_active") or {}
    if active.get("symbol"):
        relative = active.get("relative_volume")
        lines.append(
            phrases["most_active"].format(
                symbol=active["symbol"],
                change=display.percent(active.get("change")),
                # ⚠️ The **relative volume** with its label, mirroring `MostActive` in blocks.tsx: a stock's day change
                # is what *moved*, not what made it active, and the card shows both for that reason.
                relative=(
                    f"{relative:.1f}× {labels['most_active']['relative_volume']}"
                    if relative is not None
                    else labels["most_active"]["relative_volume"]
                ),
            )
        )

    # 3 — sectors and the global cues, mirroring blocks 3 and 5.
    sectors = _rows(bundle.get("sectors") or [], labels, "sectors")
    if sectors:
        lines.append(phrases["sectors"].format(items=_join(sectors[:LIST_ROWS])))
    cues = _rows(bundle.get("dependencies") or [], labels, "dependencies")
    if cues:
        lines.append(phrases["cues"].format(items=_join(cues[:LIST_ROWS])))

    # 4 — breadth and the moving averages, mirroring blocks 7 and 8.
    breadth = bundle.get("breadth") or {}
    if breadth:
        lines.append(
            phrases["breadth"].format(
                rising=breadth.get("rising"),
                falling=breadth.get("falling"),
                flat=breadth.get("flat"),
                counted=breadth.get("counted"),
            )
        )
    dma = bundle.get("dma") or {}
    above = dma.get("above") or {}
    if above:
        lines.append(
            phrases["dma"].format(
                sma50=_whole_percent(above.get("sma50")),
                sma100=_whole_percent(above.get("sma100")),
                sma200=_whole_percent(above.get("sma200")),
                eligible=dma.get("eligible"),
            )
        )

    # 5 — the flows, mirroring block 10. ⚠️ A missing side prints as a dash rather than being skipped: the section
    # states a *pair*, and dropping one half would misrepresent the other.
    flows = bundle.get("flows") or {}
    if flows:
        lines.append(
            phrases["flows"].format(
                fii=display.number((flows.get("fii") or {}).get("net"), 0),
                dii=display.number((flows.get("dii") or {}).get("net"), 0),
            )
        )

    # 6 — the calendar, mirroring block 11, which is the one block with no always-present part.
    actions = bundle.get("corporate_actions") or []
    if actions:
        named = [
            f"{row.get('symbol', '')} {labels['kinds'].get(row.get('kind'), row.get('kind', ''))}"
            for row in actions[:LIST_ROWS]
        ]
        lines.append(phrases["actions"].format(items=_join(named)))
    ipos = bundle.get("ipos") or []
    if ipos:
        lines.append(phrases["ipos"].format(items=_join([row.get("symbol", "") for row in ipos[:LIST_ROWS]])))
    announcements = bundle.get("announcements") or []
    if announcements:
        subjects = _join([_truncate(row.get("subject", "")) for row in announcements[:3]], "; ")
        lines.append(phrases["announcements"].format(items=subjects))

    # 7 — the full statement with attribution, repeated rather than inherited from the video.
    lines.append(
        phrases["closing"].format(
            attribution=labels["furniture"]["attribution"], disclosure=labels["disclosure"]
        )
    )
    return lines



# ── the three fields ──────────────────────────────────────────────────────────────────────────────────────


def labels_for(lang: str) -> dict[str, Any]:
    """The label table for an edition.

    ⚠️ **The render layer's own file, read from Python — deliberately.** Issue 13's rule is one glossary, two
    surfaces: if the description named an index differently from the card, both would still be internally consistent
    and only a reader comparing them would notice. `copybudget.py` already reads these tables, so the pattern is
    established; the alternative is a second glossary in Python, which is a second thing to keep in step.
    """
    path = store.root() / "remotion" / f"copy.{lang}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def title(date: str, bundle: dict[str, Any], labels: dict[str, Any]) -> str:
    """`series · date · the day's headline move` — three parts, always in that order, **front-loaded**.

    ⚠️ Both YouTube search and the truncated display weight the beginning, so the series name and the date are fixed
    and the move is the only variable part. It is the **same figure the cold open leads with**, so the title cannot
    disagree with the video.
    """
    parts = [labels["metadata"]["series"], formatted_date(date, labels)]
    index = display.headline_label(bundle, labels)
    if index:
        parts.append(f"{index} {display.percent(display.headline_change(bundle))}")
    return " | ".join(parts)


def hashtags(labels: dict[str, Any]) -> list[str]:
    """Exactly three — all that displays above the title, and far inside the ceiling.

    ⚠️ **`HASHTAGS_MAX` is a cliff, not a budget.** Exceed 15 and YouTube ignores *all* of them, so a longer block is
    strictly worse than a short one. Emitting a fixed three rather than appending the day's sectors keeps the count
    unbreakable, which matters more than the extra reach a fourth might have.
    """
    return [labels["metadata"][f"hashtag_{name}"] for name in ("series", "market", "india")]


def tags(bundle: dict[str, Any], labels: dict[str, Any]) -> list[str]:
    """The fixed channel tags, then the day's notable sectors **while they fit**.

    ⚠️ The budget is in **characters**, not tags (issue 13's trap), so this adds sectors only while the joined length
    stays inside it. A slice of the first N sectors would look right and blow the limit on a day of long names.
    """
    chosen = [
        labels["metadata"]["tag_channel"],
        labels["metadata"]["tag_daily"],
        labels["metadata"]["tag_india"],
        labels["metadata"]["series"],
    ]
    for row in bundle.get("sectors") or []:
        key = row.get("sector_key", "")
        name = (labels.get("sectors") or {}).get(key, key)
        if name and name not in chosen and len(", ".join([*chosen, name])) <= TAG_BUDGET:
            chosen.append(name)
    return chosen


def build(
    date: str,
    bundle: dict[str, Any],
    lang: str,
    *,
    bundle_hash: str,
    video: str,
    thumbnail: str,
) -> Metadata:
    """One edition's metadata, from the bundle and the shared glossary. No LLM, no hand-writing, no second source."""
    labels = labels_for(lang)
    body = _sections(date, bundle, labels, lang)
    description = "\n".join(body)
    built_title = title(date, bundle, labels)
    chosen = tags(bundle, labels)
    found = hashtags(labels)
    if found:
        description = f"{description}\n\n{' '.join(found)}"

    # ⚠️ Limits are **reported, not silently absorbed**. A title past 100 characters is truncated by YouTube — losing
    # the move, which is the only part a viewer is searching for — and nothing else in the run would ever notice.
    warnings: list[str] = []
    if len(built_title) > TITLE_LIMIT:
        warnings.append(f"{lang}: title is {len(built_title)} characters, over the {TITLE_LIMIT} YouTube shows")
    if len(description) > DESCRIPTION_LIMIT:
        warnings.append(f"{lang}: description is {len(description)}, over {DESCRIPTION_LIMIT}")
    if len(", ".join(chosen)) > TAG_BUDGET:
        warnings.append(f"{lang}: tags are {len(', '.join(chosen))} characters, over the {TAG_BUDGET}-character budget")
    if len(found) > HASHTAGS_MAX:
        warnings.append(f"{lang}: {len(found)} hashtags, over the {HASHTAGS_MAX} after which YouTube ignores all")

    return Metadata(
        lang=lang,
        date=date,
        title=built_title,
        description=description,
        tags=chosen,
        hashtags=found,
        thumbnail=thumbnail,
        video=video,
        bundle_hash=bundle_hash,
        warnings=warnings,
    )

