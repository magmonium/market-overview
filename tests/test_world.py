"""The 3D world — 0085_09.

⚠️ These tests read the renderer's **source**, not a running browser. That is a deliberate limit and worth
naming: a WebGL canvas cannot be inspected from pytest, so what is checked here is the *contract* — the
station table, the closed primitive set, the camera rules, the rail's continuity, the scrim's translucency
and the off switch — while the frames themselves were verified by rendering and looking.

The two failure modes this file exists to catch are both silent:

- **A card that hides the world.** Every card used to paint an opaque `#0b0e13`. Reverting one would leave
  the brief rendering perfectly, with the entire layer behind it invisible and no error anywhere.
- **A station that jumps.** The camera's continuity is what makes twelve scenes read as one world. A station
  whose `from` no longer equals its predecessor's `to` is a hard cut nobody asked for.

⚠️ Issue 12's own ceilings are asserted against the **golden bundle's** slots, so a future re-cut that
shrinks a slot below its settle fails here rather than at render time.
"""
import json
import re
import unittest

from market_overview import store

DATE = "2026-10-12"
REMOTION = store.root() / "remotion"
STATIONS_SOURCE = (REMOTION / "world" / "stations.tsx").read_text(encoding="utf-8")
WORLD_SOURCE = (REMOTION / "world" / "World.tsx").read_text(encoding="utf-8")
THEME_SOURCE = (REMOTION / "theme.ts").read_text(encoding="utf-8")
BLOCKS_SOURCE = (REMOTION / "blocks.tsx").read_text(encoding="utf-8")
FURNITURE_SOURCE = (REMOTION / "Furniture.tsx").read_text(encoding="utf-8")
MARKET_BRIEF_SOURCE = (REMOTION / "MarketBrief.tsx").read_text(encoding="utf-8")

BUNDLE = json.loads((store.dir_for(DATE) / store.FACTS).read_text(encoding="utf-8"))
BLOCKS = BUNDLE["timeline"]["blocks"]
FPS = BUNDLE["timeline"]["fps"]

PRIMITIVES = {"terrain", "column", "tile", "ring", "particle", "rig"}
SETTLE_CEILING = 1.5

#: The station table's own order, which is also the camera's order along the rail.
ORDER = [
    "cold_open",
    "indexes",
    "leaders",
    "most_active",
    "sectors",
    "breadth",
    "dma",
    "flows",
    "dependencies",
    "broader",
    "calendar",
    "close",
]

#: ⚠️ Named rail points, resolved so continuity can be compared as text: the wide the orbit opens from, and
#: the wide it closes on.
ALIAS = {"OPEN_WIDE": "rail(0, 30, 3.6)", "WIDE": "rail(0, 26, 3.2)"}

_STATION = re.compile(r"\ndefine\('([a-z_]+)', \{(.*?)\n\}\);", re.S)


def _field(body: str, name: str) -> str:
    match = re.search(rf"{name}: ([\w()., ]+?),", body, re.S)
    assert match, f"{name} not found in station body"
    return " ".join(match.group(1).split())


def stations() -> dict:
    """Every station, parsed from the table. `from`/`to` are kept as source text."""
    found = {}
    for match in _STATION.finditer(STATIONS_SOURCE):
        key, body = match.group(1), match.group(2)
        primitives = re.search(r"primitives: \[([^\]]*)\]", body)
        found[key] = {
            "primitives": re.findall(r"'([a-z]+)'", primitives.group(1)),
            "settle": float(re.search(r"settle: ([0-9.]+)", body).group(1)),
            "from": _field(body, "from"),
            "to": _field(body, "to"),
        }
    return found


def resolved(name: str) -> str:
    return ALIAS.get(name, name)


_COMMENT = re.compile(r"/\*.*?\*/|//[^\n]*", re.S)


def code_only(source: str) -> str:
    """⚠️ Source with comments removed.

    Several of these tests scan for a **forbidden** pattern, and a comment explaining why that pattern is
    forbidden contains the pattern — so scanning raw source fails on the documentation rather than on the
    code. The first run of this file failed exactly that way, on the note above `seeded()` explaining that
    `Math.random()` would break reproducibility.
    """
    return _COMMENT.sub("", source)


WORLD_CODE = code_only(WORLD_SOURCE)


STATIONS = stations()


class Coverage(unittest.TestCase):
    """Every scheduled block has a scene, and nothing else does."""

    def test_every_block_in_the_running_order_has_a_station(self):
        missing = [block["key"] for block in BLOCKS if block["key"] not in STATIONS]
        self.assertEqual(missing, [], f"blocks rendered with no world behind them: {missing}")

    def test_no_station_is_defined_for_a_block_that_never_renders(self):
        """A station for a block 0085_08 cut — the heat map — would be dead geometry the render still pays
        for, and it would hide the fact that the cut had happened."""
        scheduled = {block["key"] for block in BLOCKS}
        self.assertEqual(sorted(set(STATIONS) - scheduled), [])

    def test_twelve_stations_for_thirteen_blocks(self):
        """⚠️ Thirteen scheduled blocks and twelve stations: the pre-roll shares the cold open's shot rather
        than getting one of its own (issue 12), so the table has thirteen entries."""
        self.assertEqual(len(BLOCKS), 13)
        self.assertEqual(len(ORDER), 12)
        self.assertEqual(len(STATIONS), len(ORDER) + 1)

    def test_only_the_six_primitives_are_used(self):
        used = {name for station in STATIONS.values() for name in station["primitives"]}
        self.assertEqual(used - PRIMITIVES, set(), "a seventh shape would make the world read as demos")


class Camera(unittest.TestCase):
    """Issue 12's four camera rules, to the extent source can carry them."""

    def test_the_rail_is_continuous(self):
        """Each station starts where the last one ended. This *is* the transition, so a break here is a
        hard cut the design did not ask for."""
        for previous, following in zip(ORDER, ORDER[1:]):
            self.assertEqual(
                resolved(STATIONS[previous]["to"]),
                resolved(STATIONS[following]["from"]),
                f"{following} starts somewhere other than where {previous} ended",
            )

    def test_the_orbit_closes_on_the_establishing_wide(self):
        """The brief ends where it started: the close finishes on the wide the cold open opened on."""
        self.assertEqual(resolved(STATIONS["close"]["to"]), resolved(STATIONS["cold_open"]["to"]))
        self.assertNotEqual(
            resolved(STATIONS["cold_open"]["from"]), resolved(STATIONS["close"]["to"]), "the move must be a move"
        )

    def test_the_pre_roll_holds_still_and_has_no_move_of_its_own(self):
        """Issue 12: block 0 gets no station of its own, so the piece opens on the world before it speaks —
        and the pre-roll's render cost stays at nothing."""
        pre = STATIONS["disclosure"]
        self.assertEqual(pre["settle"], 0)
        self.assertEqual(resolved(pre["from"]), resolved(pre["to"]))
        self.assertEqual(resolved(pre["from"]), resolved(STATIONS["cold_open"]["from"]))

    def test_no_station_ever_zooms(self):
        """Rule 1: depth comes from moving, never from zooming. A written focal length anywhere but the
        shared constant would be a zoom."""
        self.assertNotIn("camera.zoom", WORLD_CODE)
        self.assertNotIn("fov =", WORLD_CODE)
        self.assertEqual(len(re.findall(r"fov: FOCAL_LENGTH\b", WORLD_CODE)), 1)

    def test_no_station_ever_rolls(self):
        """Rule 2: rotation about the viewer's own axis is the strongest nausea trigger there is, so the
        camera's up vector is never touched.

        ⚠️ `\\b` matters: without it this matches `camera.updateMatrixWorld()`.
        """
        self.assertIn("camera.lookAt(", WORLD_CODE)
        self.assertIsNone(re.search(r"camera\.up\b", WORLD_CODE))
        self.assertNotIn("rotation.z", WORLD_CODE)

    def test_every_move_is_eased_in_and_out(self):
        """Rule 3: bounded angular velocity. The easing is the whole of it."""
        self.assertIn("const ease = ", WORLD_SOURCE)
        self.assertIn("ease(local / (station.settle * fps))", WORLD_SOURCE)

    def test_every_settle_fits_inside_its_own_slot(self):
        """⚠️ **Rule 4, and 0085_08's consequence.** The re-cut sized every slot to its measured reading
        time, which leaves no room for an entrance that runs past it. So the establishing move must finish
        well inside the slot — measured here against the golden bundle, not against a remembered number."""
        for block in BLOCKS:
            station = STATIONS[block["key"]]
            slot = block["duration"] / FPS
            self.assertLessEqual(
                station["settle"], SETTLE_CEILING, f"{block['key']} settles for longer than issue 12 allows"
            )
            self.assertLess(
                station["settle"], slot, f"{block['key']}: a {station['settle']}s settle cannot fit a {slot}s slot"
            )

    def test_the_camera_settles_and_then_holds(self):
        """The camera reaches its destination and stays: a move that kept drifting would never let the
        viewer finish reading the frame it drifted to."""
        self.assertIn("Math.min(Math.max(t, 0), 1)", WORLD_SOURCE)


class Depth(unittest.TestCase):
    """The DOM is always in front, and the world is only where the layout says it may be."""

    def test_no_card_paints_an_opaque_background(self):
        """⚠️ The silent failure: a card that fills its frame solidly hides the entire 3D layer, renders
        perfectly, and reports nothing."""
        for name, source in (("blocks.tsx", BLOCKS_SOURCE), ("Furniture.tsx", FURNITURE_SOURCE)):
            self.assertNotIn("background: '#0b0e13'", source, f"{name} would hide the world behind it")

    def test_both_scrims_are_translucent(self):
        """A scrim that is not translucent is an opaque card with extra steps."""
        for name in ("SCRIM", "SCRIM_OPEN"):
            match = re.search(rf"export const {name} =\n((?:.*\n)*?).*?;", THEME_SOURCE)
            self.assertIsNotNone(match, f"{name} is missing")
            self.assertIn("rgba(11,14,19,", match.group(1), f"{name} is not translucent")

    def test_the_open_scrim_goes_only_where_the_lower_frame_is_empty(self):
        """⚠️ The split is the layout's, not a taste call. The cards below hold their content in the upper
        frame, so the world belongs underneath them — and 0085_08 concentrated 70 % of the runtime on exactly
        those cards, which is why the world has to be visible there rather than merely present.

        `sectors` is the counter-example that set the rule: its thirteen rows run to the bottom edge, and a
        thin scrim there put the world behind the heat cells, where it competed with the cells' own colour.
        The tint *is* the heat map's meaning, so nothing may sit behind it."""
        opened = set(re.findall(r"<Card title=\{copy\.blocks\.(\w+)\} scrim=\{SCRIM_OPEN\}>", BLOCKS_SOURCE))
        self.assertEqual(
            opened | {"close"},
            {"most_active", "breadth", "dma", "flows", "dependencies", "calendar", "close"},
        )
        dense = set(re.findall(r"<Card title=\{copy\.blocks\.(\w+)\}>", BLOCKS_SOURCE))
        self.assertEqual(dense, {"indexes", "leaders", "sectors", "heat_map", "broader"})

    def test_every_station_aims_at_the_world_not_at_its_own_height(self):
        """⚠️ The atmosphere band depends on this. Aiming at each camera's own height sent the world out of
        frame from the two high stations — the crane-up and the calendar — because a camera six units above
        the floor tiles looks far too far down. One shared aim point has no height dependence, and the rail
        is built from one `rail()` helper so there is nowhere else for an aim to be written."""
        self.assertIn("const AIM_Y = ", STATIONS_SOURCE)
        self.assertEqual(len(re.findall(r"target: \[0, AIM_Y, 0\]", STATIONS_SOURCE)), 1)
        self.assertEqual(len(re.findall(r"target: \[0, y,", STATIONS_SOURCE)), 0)


class OffSwitch(unittest.TestCase):
    """The world is a prop, so a render machine that cannot do WebGL loses a layer, not the brief."""

    def test_webgl_is_a_prop_defaulting_on(self):
        self.assertIn("webgl?: boolean", MARKET_BRIEF_SOURCE)
        self.assertIn("webgl = true", MARKET_BRIEF_SOURCE)

    def test_turning_it_off_removes_the_world_and_nothing_else(self):
        self.assertIn("{webgl ? <World bundle={bundle} /> : null}", MARKET_BRIEF_SOURCE)

    def test_the_world_is_mounted_once_for_the_whole_brief(self):
        """⚠️ One canvas, not one per block: thirteen WebGL contexts is both the render budget's worst case
        and the opposite of one continuous world."""
        self.assertEqual(MARKET_BRIEF_SOURCE.count("<World "), 1)
        self.assertNotIn("World", BLOCKS_SOURCE)


class Determinism(unittest.TestCase):
    """⚠️ The particle fields must be a pure function of their seed. A shared stateful generator would place
    them differently depending on how often it had been consumed — so a second edition, or a re-render from
    `store/<date>/`, would no longer match (ADR 0003)."""

    def test_the_particle_field_takes_a_seed_not_a_generator(self):
        primitives = (REMOTION / "world" / "primitives.tsx").read_text(encoding="utf-8")
        particle = primitives.split("export const Particles")[1].split("export const Rig")[0]
        self.assertIn("seed: string", particle)
        self.assertIn("const random = seeded(seed)", particle)

    def test_no_render_path_reaches_for_math_random(self):
        for name in ("primitives.tsx", "stations.tsx", "World.tsx", "theme.ts"):
            source = (REMOTION / "world" / name).read_text(encoding="utf-8")
            self.assertNotIn("Math.random", code_only(source), f"{name} would stop the frame being reproducible")


if __name__ == "__main__":
    unittest.main()


