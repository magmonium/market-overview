# Context — market-overview

The vocabulary for the tool and the product it produces. Decisions live in `docs/adr/`; this file is a
glossary and nothing else.

## The two names

**market-overview** — the **tool**: this repository, its Python package and its CLI. It fetches market data,
computes a facts bundle, drives the render and assembles the day's output.

**Market Brief** — the **product the tool produces**: one day's silent, music-backed, ≤3 min, 16:9 video
about the Indian market, in two language editions. Output filenames carry the product's name
(`market-brief-<date>-<lang>.mp4`), because the artefact is the brief, not the tool.

## The run

**run** — one execution for one **session date**. A run either produces a complete pair of packages, or
produces nothing.

**session date** — the trading session a brief covers: the last **completed** one. Not the wall-clock date —
a run fired on a holiday, or before the close, has no new session to report.

## What crosses the boundary

**facts bundle** — `store/<date>/facts.json`, the **sole interface** between the Python layer and the render
layer. It carries **values and label keys, never display strings**.

**label table** — the static, hand-authored per-language strings. Labels live in the render layer, not in the
bundle: a label that changed with the data would be a template, not a label.

**value slot** — a position in a label table that a bundle value fills.

## The brief's structure

**card** — one screenful of the brief; also **block**. Card identity, order and screen furniture are constant
daily — only the contents vary.

**disclosure** — the standing *"educational only, not investment advice or a recommendation"* statement. It is
never a recommendation.

## The output

**edition** — one language's complete deliverable: `bn` or `en`.

**package** — one edition's folder, `output/<date>/<lang>/`, self-contained: the video, its metadata text and
its thumbnail. Either package can be uploaded without touching the other.

**snapshot** — `store/<date>/`: the raw source responses and the facts bundle, kept so a video can be
rebuilt.

## The sources

**spine** — the single TradingView scan carrying prices, indices, the six return windows, the moving
averages, the sector label and index membership. **Its failure aborts the run.**

**degrade to omission** — the rule for every source that is not the spine: a missing feed drops its own card
instead of failing the run.

**BSENSE** — the combined BSE + NSE scope used for the FII/DII figures — the number Indian media quotes.
