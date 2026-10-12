"""The product mark — read, never modified. (0085_10)

Issue 21 settled that the mark sits on an **opaque chip whose fill the pipeline controls**, which is what
retires the light/dark variant question: the mark is never composited over arbitrary card colours or the raw
scene, so **one asset serves every card, both editions, the video and the still**. What is left is a single
boolean — the mark's **ink polarity** — and even that is derivable.

⚠️ **The derivation lives here rather than in the renderer, on purpose.** It is a decision, and the pipeline
decides (ADR 0002); the JS layer's job is to draw what it is told. It also means the logic is reachable from
pytest, which the renderer's is not — see `tests/test_logo.py`.

⚠️ **`resource/` is read, never written.** Derived output goes to the run's props file. The supplied file is
the master, because the licence is the operator's and a normalising pipeline that edits its inputs in place
destroys the thing it was given.
"""
from __future__ import annotations

import base64
import os
import pathlib
import re
from collections import Counter
from typing import Literal

Polarity = Literal["light", "dark"]

INK_LIGHT: Polarity = "light"
INK_DARK: Polarity = "dark"

#: ⚠️ Opaque, and that is the whole point: an **opaque chip** turns "will the mark be legible over whatever is
#: behind it?" from a hope about the scene into a property the pipeline owns and can test. Issue 21 rejected a
#: low-opacity bug for exactly this reason — over a dark, moving, gradient scene it is neither readable nor
#: consistent, which defeats the point of a permanent mark.
#:
#: Both fills come from the video palette so the chip reads as furniture rather than as a patch.
CHIP_DARK = "#111721"
CHIP_LIGHT = "#f4f6fa"

#: `logo.svg` preferred; a raster is accepted because issue 21 sets the fallback explicitly (≥1024 px with
#: transparency) rather than leaving the operator to guess.
SVG_NAMES = ("logo.svg",)
RASTER_NAMES = ("logo.png", "logo.webp", "logo.jpg", "logo.jpeg")

#: The config override. Only ever *corrects* detection — a plain boolean is not something the operator should
#: have to declare, which is what lets the brief run without asking about variants at all.
POLARITY_ENV = "MARKET_OVERVIEW_LOGO_INK"

_MIME = {
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".webp": "image/webp",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


class LogoError(RuntimeError):
    """The supplied mark cannot be used as-is, so the run stops rather than shipping a wrong-looking one."""


# ── colour ────────────────────────────────────────────────────────────────────────────────────────────────

_NAMED = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "red": (255, 0, 0),
    "lime": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "aqua": (0, 255, 255),
    "magenta": (255, 0, 255),
    "fuchsia": (255, 0, 255),
    "silver": (192, 192, 192),
    "grey": (128, 128, 128),
    "gray": (128, 128, 128),
    "navy": (0, 0, 128),
    "teal": (0, 128, 128),
    "green": (0, 128, 0),
    "purple": (128, 0, 128),
    "orange": (255, 165, 0),
    "maroon": (128, 0, 0),
    "olive": (128, 128, 0),
}

_RGB_FN = re.compile(r"rgba?\(([^)]*)\)", re.I)
_HEX = re.compile(r"^#([0-9a-f]{3,8})$", re.I)


def _parse_colour(value: str) -> tuple[int, int, int] | None:
    """`#rgb`, `#rrggbb`, `#rrggbbaa`, `rgb(a)(...)` or a small set of names — else `None`.

    Returns `None` for the values that are *not* an ink we can measure: `none`, `currentColor`, `url(#…)`
    (a paint server we would have to resolve), `inherit` and anything unparseable. Silently skipping them is
    right — a wrong luminance would pick the wrong chip, and the whole point of the chip is that contrast is
    not guessed at.
    """
    text = value.strip().strip("\"'").lower()
    if not text or text in {"none", "currentcolor", "inherit", "transparent", "unset"} or text.startswith("url("):
        return None
    if text in _NAMED:
        return _NAMED[text]
    match = _HEX.match(text)
    if match:
        digits = match.group(1)
        # An 8-digit hex is #rrggbbaa — the alpha is not part of the ink's luminance.
        if len(digits) == 8:
            digits = digits[:6]
        if len(digits) == 4:
            digits = digits[:3]
        if len(digits) == 3:
            return tuple(int(c * 2, 16) for c in digits)  # type: ignore[return-value]
        if len(digits) == 6:
            return tuple(int(digits[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
        return None
    match = _RGB_FN.match(text)
    if match:
        parts = [p for p in re.split(r"[,\s/]+", match.group(1)) if p]
        if len(parts) < 3:
            return None
        try:
            channels = []
            for part in parts[:3]:
                # ⚠️ `* 255 / 100` rather than `* 2.55`: the latter is inexact in binary floating point, so
                # `50%` became 127.49999999999999 and rounded to 127 where a browser gives 128. Caught by a
                # test, not by eye — which is the argument for testing the colour parser at all.
                share = float(part[:-1]) * 255 / 100 if part.endswith("%") else float(part)
                channels.append(round(share))
            return (channels[0] & 255, channels[1] & 255, channels[2] & 255)  # type: ignore[return-value]
        except ValueError:
            return None
    return None


def _linear(channel: int) -> float:
    value = channel / 255
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def luminance(rgb: tuple[int, int, int]) -> float:
    """WCAG relative luminance, 0 (black) to 1 (white).

    ⚠️ Not a naive channel average. `#808080` averages to 0.5 but is perceptually dark, and this number is
    what decides whether the chip goes light or dark — so the perceptual weighting is the whole job.
    """
    red, green, blue = (_linear(channel) for channel in rgb)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


# ── the mark's ink ───────────────────────────────────────────────────────────────────────────────────────

#: `fill="#fff"` (attribute), `style="fill:#fff"` and a gradient's `stop-color` are all the mark's ink.
#: `fill-opacity` deliberately does not match — the name is followed by `-`, not `:` or `=`.
_PAINT = re.compile(r"""\b(?:fill|stop-color)\s*[:=]\s*["']?([^"';]+)""", re.I)

#: ⚠️ `<text>` is a determinism failure, not a style preference. A mark depending on an embedded webfont
#: renders differently wherever that font is absent, which breaks the guarantee every other element in this
#: pipeline is held to — the same brief would not be the same brief on another machine.
_TEXT = re.compile(r"<\s*(text|tspan|textPath)\b", re.I)

_COMMENT = re.compile(r"<!--.*?-->", re.S)


def _without_comments(svg: str) -> str:
    """Comments are not drawn, so they are not the mark's text.

    Learned the hard way in `test_world.py`: a check that greps source without stripping comments matches its
    own explanatory note. A designer's commented-out `<text>` is the same trap, and refusing a perfectly good
    asset for it would be the check's fault, not the asset's.
    """
    return _COMMENT.sub("", svg)


def ink(svg: str) -> str | None:
    """The mark's **dominant ink** as `#rrggbb`, or `None` if the SVG declares no measurable fill.

    "Dominant" rather than "first": a mark is usually one colour plus a background plate, in either order, so
    counting occurrences is what finds the ink rather than the plate. Ties resolve by first appearance, which
    is deterministic, and the count is deliberately not exposed — a single-fill mark carries no information
    about *how* dominant its ink is, so reporting a ratio here would be inventing a signal.
    """
    tally: Counter[tuple[int, int, int]] = Counter()
    for raw in _PAINT.findall(svg):
        parsed = _parse_colour(raw)
        if parsed is not None:
            tally[parsed] += 1
    if not tally:
        return None
    return _hex(tally.most_common(1)[0][0])


def polarity(ink_hex: str | None, override: str | None = None) -> Polarity:
    """The mark's ink polarity — which way round the chip goes.

    ⚠️ **Defaults to `light` when the ink cannot be read**, which is the common case on this video: the frame
    is near-black throughout, so most marks drawn for it are drawn light. A raster's ink is genuinely
    unreadable without decoding it (and a wrong guess flips the chip and makes the mark *less* legible, not
    more), so `MARKET_OVERVIEW_LOGO_INK` is the escape hatch — see `resource/README.md`.
    """
    if override in (INK_LIGHT, INK_DARK):
        return override  # type: ignore[return-value]
    if ink_hex is None:
        return INK_LIGHT
    parsed = _parse_colour(ink_hex)
    if parsed is None:
        return INK_LIGHT
    # 0.5 is the midpoint of the perceptual scale, so it is where "darker than mid grey" starts. Every real
    # decision here is far from it — #fff against #000, or a #0b0e13 wordmark against #f4f6fa.
    return INK_LIGHT if luminance(parsed) >= 0.5 else INK_DARK


def chip_for(ink_polarity: Polarity) -> str:
    """Light ink needs a dark chip. The chip's fill is the *only* thing that makes the mark legible."""
    return CHIP_DARK if ink_polarity == INK_LIGHT else CHIP_LIGHT


def assert_outlined(svg: str, name: str) -> None:
    """Refuse a mark whose text depends on a font being present (issue 21's one requirement on the asset).

    ⚠️ Raising rather than warning: a warning here produces a video that looks right on the machine that made
    it and wrong everywhere else, and nothing downstream would ever notice. Issue 21 gives the operator a
    supported way out — rasterise once at 2x and supply the PNG, which this module accepts.
    """
    if _TEXT.search(_without_comments(svg)):
        raise LogoError(
            f"{name} contains <text>, so it depends on a font being installed. Outline the text to paths, "
            f"or supply a 2x PNG instead (see resource/README.md). Refusing to render a mark that would "
            f"differ on another machine."
        )


# ── the asset ────────────────────────────────────────────────────────────────────────────────────────────


def find(resource: pathlib.Path) -> pathlib.Path | None:
    """The supplied mark, SVG preferred over raster. `None` when the operator has not dropped one yet."""
    for names in (SVG_NAMES, RASTER_NAMES):
        for name in names:
            candidate = resource / name
            if candidate.is_file():
                return candidate
    return None


def load(resource: pathlib.Path, *, override: str | None = None) -> dict[str, str] | None:
    """The mark, ready to draw — or `None` if none was supplied.

    ⚠️ **Inlined as a data URI rather than served from a `public/` folder.** The renderer is a subprocess
    pointed at a props file (ADR 0003), so a path would be a second thing to keep in step with the working
    directory — and `--props` already carries the one interface the render has. A data URI keeps the mark on
    that interface, which means a re-render from a snapshot cannot lose its branding.

    ⚠️ Language-neutral: the same dict goes into both editions' props, which is what keeps the bilingual pair
    honest at the branding layer (issue 21).
    """
    path = find(resource)
    if path is None:
        return None

    data = path.read_bytes()
    suffix = path.suffix.lower()
    ink_hex: str | None = None

    if suffix == ".svg":
        text = data.decode("utf-8")
        assert_outlined(text, path.name)
        ink_hex = ink(text)
    # A raster's ink is not readable without decoding it — `polarity` falls back, and the override exists.

    resolved = override if override in (INK_LIGHT, INK_DARK) else os.environ.get(POLARITY_ENV)
    ink_polarity = polarity(ink_hex, resolved)

    return {
        "src": f"data:{_MIME.get(suffix, 'application/octet-stream')};base64,{base64.b64encode(data).decode()}",
        "name": path.name,
        "ink": ink_hex or "",
        "polarity": ink_polarity,
        "chip": chip_for(ink_polarity),
        "declared": resolved if resolved in (INK_LIGHT, INK_DARK) else "",
    }
