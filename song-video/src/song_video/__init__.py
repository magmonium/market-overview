"""The Song Reel — one supplied song in, a full-length 16:9 music video and its thumbnail out.

**The tool is `song-video`. The product is the Song Reel.** Output filenames carry the product's name
(`song-reel-<song>-<theme>.mp4`), because the artefact is the reel, not the tool.

This package is the **conductor** (ADR 0002): it discovers the song, records the run, drives Remotion, and
assembles the packages. It renders no frame of its own and never touches the master.

⚠️ **A nested sub-project, not a sibling repository.** It lives at `market-overview/song-video/` and reuses
the brief's own resources — `market_overview.logo` for the mark, `market_overview.audio` for toolchain
discovery, the brief's vendored fonts and `seeded()` for the render, and the parent's installed Remotion.

Vocabulary lives in `CONTEXT.md`; decisions live in `docs/adr/`. The specification is
`ideas/.scratch/song-video/map.md` in the planning workspace.
"""
