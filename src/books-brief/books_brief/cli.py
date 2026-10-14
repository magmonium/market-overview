"""The `books-brief` command line — one conductor for the whole run.

⚠️ **The snapshot's existence is the switch** (ticket 18, quoting the brief). With `store/<week>/facts.json` present the
run **replays** — it does not fetch — which is what makes a past week rebuildable and a re-render byte-identical.

⚠️ **A chart whose sources failed is an absent key, and a week where every chart is absent refuses and writes
nothing.** ⚠️ The *writing nothing* half is load-bearing: because the snapshot's existence is the switch, a week
written empty would be read back later as a real week containing no charts, and the next run would refuse to fetch.
"""
from __future__ import annotations

import argparse
import dataclasses
import sys

from . import (
    charts,
    corroborate,
    covers,
    delta,
    enrich,
    facts,
    freshness,
    paths,
    package,
    publish,
    rank,
    render,
    stage,
    store,
    ticker,
    window,
)
from .fetch import amazon, google_books, indie, nyt

#: ⚠️ The source clients, by vendor slug. **Adding a client is one entry here and nothing else** — which is the point
#: of a registry: `gather` stays ignorant of which vendors exist, and a vendor it has no client for simply does not
#: contribute. That is the same degrade-to-omission rule as everywhere else.
#:
#: ⚠️ **The rule is: a client is registered when the lists declared for it resolve** (ticket 29). That is the same rule
#: that keeps a vendor with no client from refusing a chart, applied to the other end of the same wire.
#:
#: ⚠️ **`amazon` and `indie` are registered as of 2026-10-14, because their declared addresses now resolve** — both were
#: fetched and parsed: `amazon-in/indian-languages` and `amazon-in/comics` return **30 rows** each, and `indie/national`
#: returns **135** for the week the client derives from the address. ⚠️ That is what gives `english` (NYT + Indie) and
#: `comics` (NYT + Amazon.in) the **two vendors** ticket 17 requires, where before they built from NYT alone.
#:
#: ⚠️ **`rokomari` is written, tested, and deliberately *not* registered.** Its list resolves and parses — 60 `product`
#: records at the Best Seller category — but the payload carries **no date anywhere**, so every row is undated and
#: `freshness.guard` discards the lot. ⚠️ Registering it would not make `bengali` build; it would only add a vendor to a
#: chart that is absent either way. ⚠️ **Finding a date is what makes it usable, and that is not a client change.**
#:
#: ⚠️ **`anandabazar` has neither a client nor a list**, and under ticket 29's address rule it cannot even be declared.
CLIENTS: dict[str, object] = {
    "nyt": nyt,
    "indie": indie,
    "amazon-in": amazon,
}

#: ⚠️ The default vendor weight (ticket 03, step 2). Per-vendor tuning is a data change, and the weights are recorded
#: in the bundle so a reader can see what was applied.
DEFAULT_WEIGHT = 1.0


def _weekly(rows: list[corroborate.Row], chart: charts.Chart) -> dict[str, float]:
    """This week's sales term per admitted title — **ticket 03's score, and it does not need the window.**

    ⚠️ **This is what breaks the circle.** The window's sales term is the *accumulated* weekly score, so if the weekly
    score needed the window there would be no way in. It does not: `rank.score` is a pure function of this week's rows,
    and the window is a pure function of the weekly scores.
    """
    sizes: dict[str, int] = {}
    for row in rows:
        sizes[row.list] = sizes.get(row.list, 0) + 1

    weights = {vendor: DEFAULT_WEIGHT for vendor in chart.vendors}

    return {
        isbn: rank.score(
            [
                rank.Listing(list=row.list, rank=row.rank, size=sizes[row.list])
                for row in rows
                if row.isbn == isbn
            ],
            weights=weights,
        )
        for isbn in {row.isbn for row in rows}
    }


def _candidates(
    weekly: dict[str, float], admitted: corroborate.Result, seen: window.Window
) -> list[rank.Candidate]:
    """The admitted titles as scored candidates — **the six-month sales term and the review term** (ticket 23).

    ⚠️ **The sales term is the window's, not this week's**, and that is the whole change this ticket makes: *"what sold
    most over six months"* is not *"what is selling this week"*. ⚠️ A title the window has never seen scores zero — and
    that is right rather than harsh, because on a fresh build the window includes the week being built, so every
    admitted title is in it by construction.
    """
    candidates = []
    for title in admitted.admitted:
        observed = seen.observed.get(title.isbn)
        candidates.append(
            rank.Candidate(
                isbn=title.isbn,
                score=observed.sales if observed else 0.0,
                rating=observed.rating if observed else None,
                ratings_count=observed.ratings_count if observed else None,
            )
        )
    return candidates


def _details(admitted: corroborate.Result) -> dict[str, enrich.Details]:
    """Ticket 05 §3's enrichment lookup, one title at a time — **and it never removes a row.**

    ⚠️ **A title the enrichment source does not know still gets a row**, carrying only what the list said. That is ticket
    07's rule one level down: a field with no value **omits**, so a missing publisher costs a publisher and not a book —
    and a chart that dropped a title because Google Books had never heard of it would be quietly shorter than the list it
    claims to rank.

    ⚠️ **The list's title *and* author win**, per ticket 17's per-field priority (*"title / author: the vendor that
    published the list"*). The volume's are second opinions, and a chart printing a different name from the list it
    ranked would be contradicting its own source. ⚠️ An **empty** author from the list means *this vendor carries no
    author*, not *the book has none* — so Google Books supplies it, which is the live case for every Amazon.in row.

    ⚠️ **The cover is a second fetch with its own failure mode**, and the record is only set once the **bytes** are on
    disk. A `Details` whose cover came from a URL alone would put a row in the snapshot claiming a cover the cache does
    not hold — ⚠️ the exact state that cancels a render, which a render is what taught us.
    """
    details: dict[str, enrich.Details] = {}

    for title in admitted.admitted:
        # ⚠️ **Ticket 20's labels come off the gate's `Title`**, which is where they were decided — from the sorted-first
        # list that carried the title. ⚠️ And they are set on the *first* `Details` as well as the replaced one below:
        # the early `continue`s (no volume, a failed lookup) must still leave the row labelled, because a missing
        # publisher costs a publisher and a missing country costs a country — neither costs the label's *value*.
        placed = {
            "title": title.title,
            "author": title.author,
            "country": title.country,
            "language": title.language,
            # ⚠️ **The list's own fields, which Google Books only gets to second-guess.** Ticket 17's per-field priority
            # runs one way — *"the vendor that published the list the title ranked on"* first — and ⚠️ the two that matter
            # most are the ones Google is worst at: a **price** it reports as a `saleInfo` estimate, and the **rating and
            # count** it does not carry at all.
            "publisher": title.publisher,
            "price": title.price,
            "rating": title.rating,
            "ratings_count": title.ratings_count,
        }
        details[title.isbn] = enrich.Details(**placed)

        try:
            volume = google_books.fetch(title.isbn)
        except Exception as error:  # noqa: BLE001 — a failed lookup is an absent field, not a lost book
            print(f"{title.isbn}: google books did not answer: {error}", file=sys.stderr)
            continue

        if volume is None:
            continue

        # ⚠️ **The list's image first.** The vendor chose the picture that represents the title it ranked, and a cover
        # is the one field where the list's own answer is the better one — Google's edition is not necessarily the
        # edition that is selling.
        source = title.cover_url or volume.cover_url
        cover = None
        if source:
            try:
                cover = covers.download(source, title.isbn)
            except Exception as error:  # noqa: BLE001 — same rule: an absent cover, not an absent row
                print(f"{title.isbn}: the cover did not download: {error}", file=sys.stderr)

        details[title.isbn] = dataclasses.replace(
            google_books.details(volume, cover=cover),
            # ⚠️ The list's title and author win (ticket 17) — and the labels are not Google's to have an opinion on.
            title=title.title,
            author=title.author or volume.author,
            country=title.country,
            language=title.language,
            # ⚠️ And the list's own fields, restored after `replace` — **a `dataclasses.replace` keeps only what it is
            # told**, so the four above would otherwise be the only survivors of the merge and the price and rating
            # would silently revert to Google's, or to nothing at all.
            publisher=title.publisher or volume.publisher,
            price=title.price,
            rating=title.rating if title.rating is not None else volume.rating,
            ratings_count=(
                title.ratings_count if title.ratings_count is not None else volume.ratings_count
            ),
        )

    return details


def _band(week: str) -> ticker.Ticker | None:
    """The market band, or `None` — ⚠️ **and `None` is a designed state, not a failure** (ticket 08).

    ⚠️ **The raw response is snapshotted before it is parsed.** The brief's habit, and its reason: *"at that point the
    evidence of what was actually received is exactly what is needed."* A response written after a successful parse can
    never show what the parser was given on the day the parser was what broke.

    ⚠️ **Nothing here is fatal**, which is the whole difference from the brief. There, a short scoreboard raises
    `MissingTickersError` and stops the run — *the scoreboard is the content*. Here it is decoration behind a book, so a
    failure omits the band and the run carries on. ⚠️ **A chart's vendors are the spine; the market is not a vendor of
    this product at all.**
    """
    try:
        raw = ticker.fetch()
    except Exception as error:  # noqa: BLE001 — decoration must not be able to abort a run
        print(f"the market band is omitted: {error}", file=sys.stderr)
        return None

    store.write_raw(week, "tradingview.json", raw)
    return ticker.parse(raw)


def _previous_chart(week: str, slug: str) -> dict[str, int] | None:
    """The previous week's chart for one chart, as `isbn → rank` — or `None` when that week was never built.

    ⚠️ **`None` means *week one*, and the two are not interchangeable**: `rank.chart` bypasses the newcomer cap on
    `None` (ticket 03), because with no previous week every title reads as new and the cap would ship a "Top 100" of
    ten books.

    ⚠️ **The ranks, not merely the ISBNs**, because ticket 01's Δ needs each title's previous *position* — and a caller
    handed a bare tuple would have to re-derive them from the list's order, which is the assumption a short or
    watchlisted chart breaks.
    """
    try:
        bundle = store.read_facts(delta.previous_week(week))
    except FileNotFoundError:
        return None

    return delta.ranks(bundle, slug)


def _window_weeks(week: str) -> int:
    """How many weeks the window **actually has** — the number the chart states (tickets 23, 15).

    ⚠️ **Reported, not assumed.** The six-month window is *accumulated*, so an early run must state the window it has: a
    chart claiming six months while holding seven weeks would be stating something untrue.

    ⚠️ **And it counts the week being built**, which is not on disk yet — because the window includes it. A count that
    read only the store would be one short for the whole of the run that built it, and `window_weeks` is printed on the
    slide.
    """
    covered = window.weeks(store.root(), ending=week)
    return len(covered) if week in covered else len(covered) + 1


def gather(week: str) -> dict:
    """Fetch every declared source and build the week's bundle.

    ⚠️ **A vendor with no client, or a client that fails, does not stop the run** — the chart that needed it goes
    absent, and the run refuses only if *nothing* could be built. That is the spine rule (ticket 18): the vendors a
    chart declares *are* its spine, so losing one makes the chart absent rather than smaller.
    """
    built: dict[str, facts.Chart | None] = {}

    for chart in charts.ALL:
        # ⚠️ **Only the declared vendors that have a client, and the distinction is deliberate.** A vendor with no client
        # is scaffolding rather than a source that failed — the registry comment above fixes that — so it cannot make a
        # chart absent. ⚠️ It self-corrects: once every scraper lands, every declared vendor has a client and the rule
        # tightens by itself, with no second edit here.
        cliented = [vendor for vendor in chart.vendors if vendor in CLIENTS]

        rows: list[corroborate.Row] = []
        for vendor in cliented:
            try:
                # ⚠️ **Fetch, snapshot, parse — in that order, and the conductor owns all three.**
                #
                # This is the brief's `_degrade(day, name, fetch, parse, default)` — *"Fetch one non-spine feed, snapshot
                # it, shape it"* — and the middle step is why a client hands back a `Page` rather than rows. ⚠️ Ticket
                # 18's rule is that the raw response is snapshotted **even when parsing fails**, because *"at that point
                # the evidence of what was actually received is exactly what is needed"* — and a client that had already
                # parsed could only ever offer a response its own parser had vouched for.
                for page in CLIENTS[vendor].fetch(chart, week=week):  # type: ignore[attr-defined]
                    store.write_raw(week, page.name, page.payload)
                    rows.extend(
                        CLIENTS[vendor].parse(page.payload, listing=page.listing)  # type: ignore[attr-defined]
                    )
            except Exception as error:  # noqa: BLE001 — a failed vendor is an absent chart, not a crashed run
                print(f"{chart.slug}: {vendor} did not answer: {error}", file=sys.stderr)

        # ⚠️ **Ticket 10's freshness guard, and it is not a filter.** A stale list's rows are dropped *and* a vendor left
        # with nothing is a **missing source** — ticket 18: *"a stale source is a missing source for that week."*
        guarded = freshness.guard(rows, week=week, vendors=cliented)

        if guarded.missing:
            # ⚠️ **Absent, not smaller.** A chart built from the vendors that did answer is exactly the silent wrong
            # answer the guard exists to prevent: it ships looking complete while claiming to rank the lists it declares.
            print(
                f"{chart.slug}: no fresh list from {', '.join(guarded.missing)} — the chart is absent",
                file=sys.stderr,
            )
            built[chart.slug] = None
            continue

        rows = list(guarded.rows)

        if not rows:
            built[chart.slug] = None
            continue

        admitted = corroborate.admit(rows, chart=chart)
        # ⚠️ **The enrichment runs before the window**, because this week's rows carry the *ratings* the window needs
        # (ticket 23) — and it runs **once**, so the fetch is not repeated for the snapshot below.
        details = _details(admitted)
        previous = _previous_chart(week, chart.slug)

        # ⚠️ **This week's own sales term, and it needs no window** — which is what breaks the circle. The window
        # aggregates *these*; they do not depend on it.
        weekly = _weekly(rows, chart)

        # ⚠️ **Ticket 23's window** — the weeks before this one, plus this one's own rows, which are not on disk yet.
        seen = window.observe(
            store.root(),
            ending=week,
            slug=chart.slug,
            current=[
                {
                    "isbn": title.isbn,
                    "score": weekly.get(title.isbn, 0.0),
                    "rating": details[title.isbn].rating if title.isbn in details else None,
                    "ratings_count": (
                        details[title.isbn].ratings_count if title.isbn in details else None
                    ),
                }
                for title in admitted.admitted
            ],
        )

        board = rank.chart(
            _candidates(weekly, admitted, seen),
            # ⚠️ **`None` and `()` are different questions** (ticket 03): `None` is *week one* and bypasses the cap, while
            # `()` is *a previous chart that was empty* and does not. Collapsing a `None` mapping to `()` here would
            # silently switch the cap back on for a first run — and ship a "Top 100" holding ten books.
            previous=None if previous is None else tuple(previous),
            # ⚠️ The window's own mean — what a thin rating is shrunk toward (ticket 23).
            mean=seen.mean_rating,
        )

        built[chart.slug] = facts.Chart(
            # ⚠️ Ticket 05's fields joined onto ticket 03's ranking, from the enrichment source.
            # ⚠️ **The lookup happens here and not inside `enrich.build`**, because it is a *boundary*: one HTTP call per
            # admitted title, with its own failures and its own retry policy. Keeping it in the conductor is what lets the
            # merge stay a pure function of what the sources returned — and what lets the suite test the merge without a
            # network.
            books=enrich.build(board.ranked, details=details, previous=previous),
            watchlist=board.watchlist,
        )

    # ⚠️ **The band is fetched once, for all four charts** (ticket 13), and its absence is not a run's failure —
    # `_band` returns `None` and the bundle simply has no `ticker` key (ticket 08).
    return facts.build(
        week, charts=built, window_weeks=_window_weeks(week), ticker=_band(week)
    )


def _covered(bundle: dict) -> list[str]:
    """Every ISBN whose row records a cover — **across all four charts at once.**

    ⚠️ **One call, not one per chart.** The superset repeats titles (ticket 14), so staging per chart would copy the
    same file up to four times — and the cache is keyed by ISBN precisely so that one copy serves every chart.
    """
    return sorted(
        {
            row["isbn"]
            for chart in bundle.get("charts", {}).values()
            for row in chart.get("ranked", [])
            if row.get("cover") is not None
        }
    )


def _produce(chart: charts.Chart, week: str, *, kind: str) -> pathlib.Path:
    """Render one artefact **into scratch, and move it into place only once it is whole.**

    ⚠️ **Remotion's `--overwrite` unlinks its target before writing it.** Rendering straight at the package file would
    therefore let a render that dies at 90% — or is killed — destroy last week's good delivery, while the folder still
    looked like a package. So every render writes a dot-prefixed sibling and is moved into place only once it exists.
    That is the reel's rule, and it is the reason a failed run leaves the previous week untouched.
    """
    directory = package.dir_for(week, chart.slug)
    directory.mkdir(parents=True, exist_ok=True)

    name = package.filenames(week, chart.slug)[kind]
    target = directory / name
    scratch = directory / f".{name}.part"

    command = (
        render.still_command(chart=chart.slug, week=week, output=scratch)
        if kind == "thumbnail"
        else render.command(chart=chart.slug, week=week, output=scratch)
    )

    try:
        render.run(command)
        if not scratch.is_file():
            raise render.RenderError(
                f"{chart.slug}: remotion reported success and wrote nothing at {scratch.name}"
            )
        scratch.replace(target)
    finally:
        # ⚠️ Removed even on failure: a crashed run must not leave scratch where a deliverable belongs.
        scratch.unlink(missing_ok=True)

    return target


def build(week: str) -> int:
    """Build one week's charts — or **replay** the snapshot when the week is already recorded.

    ⚠️ **The order is the run.** Thumbnails before videos (ticket 16's quality gate), and the package last — because the
    metadata describes artefacts that have to exist, and the manifest is what says the folder is finished.
    """
    snapshot = store.dir_for(week) / store.FACTS

    if snapshot.is_file():
        # ⚠️ The switch. A snapshot is only ever written by a run that got past the refusal below, so finding one means
        # the week is already established — and re-fetching it would produce a *different* chart from the same week.
        bundle = store.read_facts(week)
    else:
        bundle = gather(week)
        if not bundle["charts"]:
            print(f"{week}: no chart could be built", file=sys.stderr)
            return 1
        store.write_facts(week, bundle)

    # ⚠️ **Staged once, before any render.** A composition can only fetch from the render project's `public/`, and one
    # staged bundle serves all four renders (ticket 13) — the chart id is the only thing that varies. Staging inside the
    # loop would copy the same bytes four times, and worse, would let the first render succeed against a file a later
    # iteration had not written yet.
    stage.snapshot(week, paths.public_dir())
    # ⚠️ The mark rides **beside** the bundle for the same reason the brief keeps its own out of `facts.json`: it is not
    # a fact, and it is identical in all four charts. ⚠️ And it is staged even when there is none — as an explicit
    # `null` — because a fetch that 404s is a failed render, not a chart without branding.
    stage.mark(paths.public_dir())
    # ⚠️ Read off the **snapshot**, not off a live object: a replay reaches here with nothing but the committed facts,
    # and staging has to work identically on that path.
    stage.covers(_covered(bundle), paths.public_dir())

    wanted = [charts.get(slug) for slug in sorted(bundle["charts"])]

    # ⚠️ **Every thumbnail before any video.** Four one-frame stills cost seconds, so a chart whose collage reads badly
    # is seen and killed before an hour of frames is spent on it — the reel's own ordering, and its reason.
    for chart in wanted:
        _produce(chart, week, kind="thumbnail")

    for chart in wanted:
        _produce(chart, week, kind="video")

    # ⚠️ **The package last, per chart** — `metadata-<chart>.json` is the file that says the folder is finished
    # (ticket 13), and it cannot honestly say so until the video and the thumbnail are both there.
    for chart in wanted:
        package.assemble(week, chart)

    return 0


def main(argv: list[str] | None = None) -> int:
    """`books-brief build --week 2026-W41` · `books-brief publish --week 2026-W41 [--dry-run]`."""
    parser = argparse.ArgumentParser(prog="books-brief")
    commands = parser.add_subparsers(dest="command", required=True)

    builder = commands.add_parser("build", help="build one ISO week's charts")
    builder.add_argument("--week", required=True, help="the ISO week, e.g. 2026-W41")

    publisher = commands.add_parser("publish", help="upload a built week's charts to YouTube")
    publisher.add_argument("--week", required=True, help="the ISO week, e.g. 2026-W41")
    # ⚠️ Repeatable, and **every finished package by default** — because the week may hold three charts and not four
    # (ticket 13's partial delivery), so the default is read off the disk rather than off the declaration table.
    publisher.add_argument(
        "--chart", action="append", help="one chart to publish; repeatable (default: every built chart)"
    )
    publisher.add_argument(
        "--privacy",
        default=publish.DEFAULT_PRIVACY,
        choices=publish.PRIVACY,
        help="⚠️ defaults to private — the human check is the reason a human runs it (ticket 24)",
    )
    publisher.add_argument(
        "--dry-run", action="store_true", help="read the packages and report, contacting nothing"
    )
    # ⚠️ **There is no `--authorise` here, and that is deliberate.** The token and the scope are shared with the brief,
    # so `mo publish --authorise` already grants everything this can do — a second consent flow would be a second token
    # for one permission.
    publisher.add_argument("--check", action="store_true", help="verify the shared token and stop")

    args = parser.parse_args(argv)

    if args.command == "build":
        return build(args.week)

    if args.check:
        return publish.check()

    return publish.run(
        args.week,
        args.chart or publish.charts_in(args.week),
        privacy=args.privacy,
        dry_run=args.dry_run,
    )

