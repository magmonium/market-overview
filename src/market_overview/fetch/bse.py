"""BSE feeds — the four things TradingView does not carry.

⚠️ BSE sits behind Akamai: plain `requests` gets **403**. `curl_cffi` with
`impersonate="chrome"` and the site's own `Referer`/`Origin` gets **200 JSON**. NSE stays ruled
out — impersonation does not defeat it.

Four feeds, and **none of them is the spine**: every one degrades to omission, dropping only its
own card. See ADR 0002 for why the conductor owns that decision rather than the parser.
"""
from __future__ import annotations

import datetime as _datetime
import json
import re
from dataclasses import dataclass

from curl_cffi import requests as _requests

BASE = "https://api.bseindia.com/BseIndiaAPI/api/"

_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.bseindia.com/",
    "Origin": "https://www.bseindia.com",
    "Accept-Language": "en-US,en;q=0.9",
}


class BseError(RuntimeError):
    """A BSE feed could not be read. Degrades — it never aborts a run."""


@dataclass(frozen=True)
class BseResult:
    """A feed's payload **and the bytes it came from**, for the raw snapshot."""

    name: str
    raw: bytes
    payload: object


def _get(endpoint: str, *, timeout: float = 45.0) -> BseResult:
    url = BASE + endpoint
    try:
        response = _requests.get(url, headers=_HEADERS, impersonate="chrome", timeout=timeout)
    except Exception as exc:  # curl_cffi raises its own family of transport errors
        raise BseError(f"{endpoint} failed: {exc}") from exc
    if response.status_code != 200:
        raise BseError(f"{endpoint} returned HTTP {response.status_code}")
    raw = response.content
    try:
        payload = json.loads(raw)
    except ValueError as exc:
        raise BseError(f"{endpoint} did not return JSON: {exc}") from exc
    return BseResult(name=endpoint.replace("/", "-").removesuffix("-w"), raw=raw, payload=payload)


# ── FII / DII flows ──────────────────────────────────────────────────────────────────

# ⚠️ `CategoryTurnovermkt/w` is the trap: one word different, the same response envelope, a
# plausible-looking number — and a *different scope*. It is deliberately never called. On
# 2026-10-12 the headline read -1,708 cr against the mkt variant's -1,196 cr; on 2026-10-09 the
# gap was 42x and the signs disagreed. The headline is `CategoryTurnover/w` only.
FLOWS_ENDPOINT = "CategoryTurnover/w"


def flows() -> BseResult:
    return _get(FLOWS_ENDPOINT)


def net_flows(payload: object) -> dict[str, object]:
    """FII/FPI and DII net, in **crore**.

    ⚠️ Two traps, both measured:

    - **DII is not `*_BSENSE`.** It is `NET_DII` / `PURCHASE_DII` / `SALE_DII`. An earlier note
      read "the same three value columns", which would have returned nothing for every DII field
      and silently blanked the half of the pair that carries the story.
    - The feed is in **raw rupees**, so crore needs **÷ 1e7**. Without it the card renders
      "₹10,37,39,90,000 crore".
    """
    rows = payload.get("Table") if isinstance(payload, dict) else None
    if not rows:
        raise BseError("turnover feed carried no Table")
    row = rows[0]

    def pair(prefix: str) -> dict[str, float | None]:
        return {
            "buy": _crore(row.get(f"PURCHASE_{prefix}")),
            "sell": _crore(row.get(f"SALE_{prefix}")),
            "net": _crore(row.get(f"NET_{prefix}")),
        }

    return {
        "session": str(row.get("REPORTING_DATE", ""))[:10],
        # `*_BSENSE` is the combined BSE+NSE figure — the number Indian media quotes.
        "fii": pair("BSENSE"),
        "dii": pair("DII"),
    }


def _crore(rupees: object) -> float | None:
    if isinstance(rupees, bool) or not isinstance(rupees, (int, float)):
        return None
    return rupees / 1e7


# ── corporate actions ────────────────────────────────────────────────────────────────

ACTIONS_ENDPOINT = "DefaultData/w"

# A stable *kind*, never a display string: the label tables own the words (ADR 0003).
_ACTION_KINDS: tuple[tuple[str, str], ...] = (
    ("income distribution", "income_distribution"),
    ("bonus", "bonus"),
    ("split", "split"),
    ("consolidation", "consolidation"),
    ("right", "rights"),
    ("dividend", "dividend"),
)

# `Interim Dividend - Rs. - 12.0000` — note the stray `-` before the amount.
_AMOUNT = re.compile(r"rs\.?\s*-\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)


def action_kind(purpose: str) -> str:
    """Classify a `Purpose` string.

    ⚠️ `Purpose` arrives dirty, and every quirk below was measured rather than guessed: trailing
    spaces (`'Consolidation of Shares '`), **two** spaces inside `Stock  Split`, and dividends
    either bare (`'Interim Dividend'`) or carrying an amount. Collapsing whitespace first turns
    all of that into one case instead of four.
    """
    text = " ".join(str(purpose).split()).lower()
    for needle, kind in _ACTION_KINDS:
        if needle in text:
            return kind
    return "other"


def action_amount(purpose: str) -> float | None:
    found = _AMOUNT.search(str(purpose))
    return float(found.group(1)) if found else None


def actions() -> BseResult:
    return _get(ACTIONS_ENDPOINT)


def actions_in_window(
    payload: object, since: _datetime.date, until: _datetime.date
) -> list[dict]:
    """Corporate actions whose ex-date falls in `[since, until]`, both inclusive.

    ⚠️ The feed is a **bare list**, not `{"Table": [...]}` — a different envelope from the other
    three, and worth knowing before writing one parser for all of them.
    """
    if not isinstance(payload, list):
        raise BseError("corporate-action feed was not a list")
    picked = []
    for row in payload:
        day = _ex_date(row)
        if day is None or not (since <= day <= until):
            continue
        purpose = row.get("Purpose", "")
        picked.append(
            {
                "symbol": str(row.get("short_name", "")).strip(),
                "kind": action_kind(purpose),
                "amount": action_amount(purpose),
                "ex_date": day.isoformat(),
            }
        )
    return sorted(picked, key=lambda item: (item["ex_date"], item["symbol"]))


def _ex_date(row: dict) -> _datetime.date | None:
    """The ex-date.

    ⚠️ Prefer `exdate` (`'20261012'`, machine-readable, locale-free) over `Ex_date`
    (`'12 Oct 2026'`, which is neither).
    """
    compact = str(row.get("exdate", "")).strip()
    if len(compact) == 8 and compact.isdigit():
        return _datetime.date(int(compact[:4]), int(compact[4:6]), int(compact[6:8]))
    return None


# ── IPOs ─────────────────────────────────────────────────────────────────────────────

IPOS_ENDPOINT = "IPO_HomePageDetail/w"

# ⚠️ Despite the name this is **not** an IPO feed. Its 17 rows on 2026-10-12 broke down as
# BuyBack 5 · RI 4 · Takeover 3 · Book Building 2 · Delisting 1 · Debt Issue 1 · ZCZP 1. Only
# `IR_flag == "IPO"` is an actual public issue — **2 of those 17**. Publishing the rest would
# have announced a delisting and five buybacks as offers opening this week.
IPO_FLAG = "IPO"


def ipos() -> BseResult:
    return _get(IPOS_ENDPOINT)


def openings_in_window(
    payload: object, since: _datetime.date, until: _datetime.date
) -> list[dict]:
    """IPOs **opening** in `[since, until]`, both inclusive."""
    rows = payload.get("Table") if isinstance(payload, dict) else None
    if not rows:
        raise BseError("IPO feed carried no Table")
    picked = []
    for row in rows:
        if str(row.get("IR_flag", "")).strip().upper() != IPO_FLAG:
            continue
        start = _day(row.get("Start_Dt"))
        if start is None or not (since <= start <= until):
            continue
        end = _day(row.get("End_Dt"))
        picked.append(
            {
                "symbol": str(row.get("Scrip_name", "")).strip(),
                "start": start.isoformat(),
                "end": end.isoformat() if end else None,
            }
        )
    return sorted(picked, key=lambda item: (item["start"], item["symbol"]))


def _day(value: object) -> _datetime.date | None:
    """`Start_Dt` arrives as `'2026-10-13T00:00:00'`."""
    text = str(value or "").strip()
    if len(text) < 10:
        return None
    try:
        return _datetime.date.fromisoformat(text[:10])
    except ValueError:
        return None


# ── company announcements ────────────────────────────────────────────────────────────

ANNOUNCEMENTS_ENDPOINT = "CorpAnn/w"


def announcements() -> BseResult:
    return _get(ANNOUNCEMENTS_ENDPOINT)


def latest_announcements(payload: object, limit: int = 8) -> list[dict]:
    """The feed's own latest N.

    ⚠️ The payload is **only** `{Subject, Newsid}` — there is no date field anywhere in it — so
    this cannot be windowed, and the honest framing is *latest*, never *today's*. The feed's own
    order is taken as newest-first; that is **assumed, not verified**, because there is no date to
    check it against.

    The subject is kept **verbatim**: a filing is legally worded, so the card shows the real
    subject with a translation beside it rather than a paraphrase instead of it.
    """
    if not isinstance(payload, list):
        raise BseError("announcement feed was not a list")
    picked = []
    for row in payload[:limit]:
        subject = " ".join(str(row.get("Subject", "")).split())
        if not subject:
            continue
        picked.append({"subject": subject, "ref": str(row.get("Newsid", ""))})
    return picked
