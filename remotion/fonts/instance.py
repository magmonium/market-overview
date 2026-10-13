"""Bake the three weights the brief uses out of Google's variable subsets.

Kept as a record of how `remotion/fonts/*.woff2` were produced, not as a pipeline step: the
instances are committed, so a render never needs fontTools. Run with
`uv run --with fonttools --with brotli python remotion/fonts/instance.py`.
"""
import pathlib

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = pathlib.Path(__file__).parent
SUBSETS = ("bengali", "latin-ext", "latin")
WEIGHTS = (400, 600, 700)


def main() -> None:
    for subset in SUBSETS:
        source = HERE / f"NotoSansBengali-{subset}.woff2"
        for weight in WEIGHTS:
            font = TTFont(source)
            static = instancer.instantiateVariableFont(
                font, {"wght": weight}, inplace=False, updateFontNames=True
            )
            static.flavor = "woff2"
            out = HERE / f"NotoSansBengali-{subset}-{weight}.woff2"
            static.save(out)
            print(f"{out.name}  {out.stat().st_size} bytes")


if __name__ == "__main__":
    main()
