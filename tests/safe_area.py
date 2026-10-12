"""Is the reserved mark area actually clear? — a measuring tool, not a test.

0085_10's Done When is "nothing in any block draws into the reserved top-right region", and eyeballing a
1080p still is not a check. This reads the actual pixels.

⚠️ **The region is the frame's top-right corner — 260 x 160, `x >= 1660`, `y <= 160`** (issue 21's verdict
table). Not the card's padded content box: `Card`'s padding happens to put content near it, which is what
makes the mistake easy to make.

Usage:

    .venv/bin/python tests/safe_area.py <still.png> [<still.png> ...]

Standard library only — there is no Pillow in this project, and a check that needs a new dependency to run
is a check that will not be run.
"""
import struct
import sys
import zlib

#: The reserved safe area, quoted verbatim from issue 21's verdict table:
#: **top-right 260 x 160 px, `x >= 1660`, `y <= 160`** — anchored to the **frame corner**, not to the card's
#: padded content box.
#:
#: ⚠️ An earlier revision of this tool measured a box derived from `Card`'s padding instead
#: (`x 1564..1824`, `y 64..224`), which is a *different* region: it missed the top 64 rows and the right 96
#: columns of the real one, and included 96 columns and 64 rows that are outside it. The measurement it
#: produced was therefore not a measurement of the reserved area at all.
LEFT = 1660
TOP = 0
RIGHT = 1920
BOTTOM = 160


def decode_through(path: str, last_row: int):
    """Width channels, and the decoded rows up to and including `last_row`.

    Row filters are cumulative, so decoding must start at row 0 — but it can stop as soon as it clears the
    region, which is why this is seconds rather than minutes in pure Python.
    """
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos, idat = 8, b""
    while pos < len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        ctype = data[pos + 4 : pos + 8]
        chunk = data[pos + 8 : pos + 8 + length]
        if ctype == b"IHDR":
            width, height, depth, color, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
        elif ctype == b"IDAT":
            idat += chunk
        elif ctype == b"IEND":
            break
        pos += 12 + length

    assert depth == 8 and interlace == 0, "only 8-bit non-interlaced PNGs"
    assert color in (2, 6), f"unexpected colour type {color}"
    channels = 3 if color == 2 else 4
    stride = width * channels
    raw = zlib.decompress(idat)

    rows, offset, previous = {}, 0, bytearray(stride)
    for y in range(min(last_row + 1, height)):
        kind = raw[offset]
        offset += 1
        line = bytearray(raw[offset : offset + stride])
        offset += stride
        if kind == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 255
        elif kind == 2:
            for i in range(stride):
                line[i] = (line[i] + previous[i]) & 255
        elif kind == 3:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((left + previous[i]) >> 1)) & 255
        elif kind == 4:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                b = previous[i]
                c = previous[i - channels] if i >= channels else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        elif kind != 0:
            raise AssertionError(f"bad filter {kind} on row {y}")
        rows[y] = line
        previous = line
    return channels, rows


def brightest(path: str, box: tuple[int, int, int, int] | None = None) -> int:
    """The brightest pixel in `box` (default the reserved area), summed over RGB — 765 is white."""
    left, top, right, bottom = box or (LEFT, TOP, RIGHT, BOTTOM)
    channels, rows = decode_through(path, bottom)
    top_value = 0
    for y in range(top, min(bottom, len(rows))):
        line = rows[y]
        for x in range(left, right):
            i = x * channels
            top_value = max(top_value, line[i] + line[i + 1] + line[i + 2])
    return top_value


DEFAULT = (LEFT, TOP, RIGHT, BOTTOM)


def _parse(argv: list[str]) -> tuple[tuple[int, int, int, int], list[str]]:
    """`--box=x0,y0,x1,y1` to measure somewhere else — the only way to show this tool *can* see."""
    box, files = DEFAULT, []
    for arg in argv:
        if arg.startswith("--box="):
            box = tuple(int(part) for part in arg[6:].split(","))  # type: ignore[assignment]
        else:
            files.append(arg)
    return box, files


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    box, files = _parse(sys.argv[1:])
    for name in files:
        best = brightest(name, box)
        if box == DEFAULT:
            flag = "clean" if best < 150 else "NOT CLEAR — something is drawing there"
        else:
            flag = f"box {box}"
        print(f"{name}: brightest = {best} of 765  -> {flag}")
