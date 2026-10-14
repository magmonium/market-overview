"""The `market-overview` command line.

One conductor for the whole run: fetch → facts → render → package.
See docs/adr/0002 for why Python owns the run and the JS layer only renders.
"""
from __future__ import annotations

import argparse
import datetime as _datetime
import sys

from . import audio, facts, logo, package, publish, render, session, store, universe
from .fetch import bse, tradingview

# The primary edition renders first, so it is never hostage to the secondary.
LANGUAGES: tuple[str, ...] = ("bn",)

#: Every edition the renderer ships a label table for (`copy.bn.json`, `copy.en.json`) — the vocabulary
#: `--lang` offers. A default run builds `LANGUAGES` above; this is the full set a caller may ask for.
ALL_LANGUAGES: tuple[str, ...] = ("bn", "en")


def _today() -> str:
    """The date a run aims at when no `--date` is given: **today**, in the tool's ISO form.

    ⚠️ This is only the date that is *asked for*. The session guard still has the last word, so
    today being a holiday, a weekend, or not yet past the close refuses exactly as a typed date
    would — the default changes the request, not the contract. A named seam rather than an inline
    `date.today()`, so a test can pin "today" without freezing the clock for everything else.
    """
    return _datetime.date.today().isoformat()


def _editions(requested: list[str] | None) -> tuple[str, ...]:
    """The editions a run builds, in order.

    ⚠️ `--lang` **narrows** the run; it does not reorder the product. With no flag the shipping default
    (`LANGUAGES`) applies, so a bare `build` renders exactly what it always did — the flag is additive.
    Duplicates are dropped and the caller's order kept, so `--lang en bn` renders English first: useful
    when one edition is being re-cut and should land before the other.
    """
    if not requested:
        return LANGUAGES
    return tuple(dict.fromkeys(requested))


def _degrade(day: str, name: str, fetch, parse, default):
    """Fetch one non-spine feed, snapshot it, shape it — or omit it.

    ⚠️ A failure here is **never** an abort: a missing corporate-action card is a smaller failure
    than a brief that refuses to publish because a secondary feed was down.

    The raw response is snapshotted **even when parsing fails**, because at that point the
    evidence of what was actually received is exactly what is needed.
    """
    try:
        result = fetch()
    except bse.BseError as exc:
        print(f"{name} omitted: {exc}", file=sys.stderr)
        return default
    store.write_raw(day, f"{result.name}.json", result.raw)
    try:
        return parse(result.payload)
    except bse.BseError as exc:
        print(f"{name} omitted: {exc}", file=sys.stderr)
        return default


def build(args: argparse.Namespace) -> int:
    """Build one date's editions: Bengali first, then English, sequentially.

    ⚠️ `--date` is **optional and defaults to today**, so the common case — publish the newest session —
    is a bare `build`. The guard is unaffected: today is still only the date *asked for*, and a holiday,
    a weekend or a mid-session clock refuses it exactly as it would a typed date.
    """
    requested = args.date if args.date is not None else _today()
    try:
        date = _datetime.date.fromisoformat(requested).isoformat()
    except ValueError:
        print(f"--date must be YYYY-MM-DD, got {requested!r}", file=sys.stderr)
        return 2

    # Which editions this run builds — the shipping pair narrowed by `--lang` (see `_editions`).
    editions = _editions(args.lang)

    # ── Fetch, or re-render from the snapshot. ────────────────────────────────────────
    # ⚠️ The snapshot's **existence** is the switch — which is what `--date`'s help has always
    # claimed. A snapshot is only ever written *after* the session guard admits the date, so
    # finding one means the day was already established as final, and the guard is deliberately
    # skipped on this path: re-checking a past date against the *live* bar would refuse every
    # rebuild, because the newest session has moved on. That is exactly the trap that made
    # "re-render from the snapshot" impossible to perform before this ticket.
    #
    # It also keeps a re-publish honest. Rendering again must not quietly swap the numbers that
    # were published for newer ones, so the store — not the wire — is what a second run reads.
    # To force a fresh fetch, delete `store/<date>/`; the runbook says so.
    snapshot = store.dir_for(date) / store.FACTS
    if snapshot.exists():
        print(f"re-render: reading {snapshot.relative_to(store.root())} — not fetching", flush=True)
    else:
        refusal = _fetch(date)
        if refusal:
            return refusal

    # ⚠️ One read path for both branches, so the renderer can only ever see what is on disk.
    bundle = store.read_facts(date)
    day = date

    # ⚠️ The bed is normalised **once for the run, before the edition loop**, and the same file is handed to both
    # editions. Prepared per edition it would be prepared twice — which is not merely wasteful: it would make
    # "both editions carry the same bed" a claim about two runs of ffmpeg matching, rather than a fact about one
    # file. See `audio.prepare`.
    try:
        prepared = audio.prepare(
            render.date_dir(day), render.run_seconds(bundle), root=store.root()
        )
    except audio.AudioError as exc:
        print(f"refusing to publish {day}: {exc}", file=sys.stderr)
        return 1
    bed = prepared[0] if prepared is not None else None
    if prepared is not None:
        print(prepared[1], flush=True)

    # One bundle, one render pass per edition. Bengali first, so the primary edition is
    # never hostage to the secondary; and a failed edition fails the run, because a
    # half-populated date folder looks complete.
    try:
        for lang in editions:
            try:
                # ⚠️ Announced **before** the render, not only after it. The render is the hour-long step, and
                # this line is what tells a watching operator *which edition* the progress that follows belongs
                # to. `flush=True` because stdout is buffered whenever it is redirected — the very silence the
                # progress forwarding exists to remove. The renderer's own `Rendered x/y` lines follow from
                # `render._stream`.
                print(f"rendering {lang} …", flush=True)
                video = render.render(day, lang, bed=bed)
                print(f"rendered: {video}", flush=True)
                # ⚠️ The still is rendered **per edition, straight after its own video** — issue 13's package is
                # self-contained, so a language folder missing its thumbnail is an incomplete package, and a failed
                # still has to fail the run rather than leave a folder that looks finished. It re-reads the bundle
                # from `store/`, so it is a re-render from the snapshot like everything else (ADR 0003).
                print(f"thumbnail: {render.still(day, lang)}", flush=True)
                # ⚠️ Assembly is **last and inside this try**, because it is what marks the package complete: a folder
                # with a video and no `metadata-<lang>.json` is visibly unfinished, and one that failed *after* writing
                # the JSON would be worse than either. See the note in package.py.
                published = package.assemble(day, lang)
                print(
                    f"package: {render.out_dir(day, lang)} "
                    f"(bundle {published.bundle_hash[:12]}, "
                    f"title {len(published.title)} chars, "
                    f"{len(published.tags)} tags)",
                    flush=True,
                )
                # ⚠️ Limits are reported, not enforced by refusal: a title two characters over is truncated by YouTube
                # and loses the move, which is bad — but it is not a reason to publish nothing at all. The run says so
                # and carries on, which is the same trade the session guard makes in the other direction.
                for warning in published.warnings:
                    print(f"warning: {warning}", file=sys.stderr)
            # ⚠️ `LogoError` is a **refusal**, not a crash, and it belongs in this except: an SVG whose text is not
            # outlined depends on a font being installed, so rendering it would produce a video that looks right
            # here and different elsewhere (0085_10). `AudioError` is the same shape of refusal for the bed
            # (0085_11). Catching them here is what makes each a message the operator can act on rather than a
            # traceback.
            except (render.RenderError, logo.LogoError, audio.AudioError) as exc:
                print(f"refusing to publish {day}: {exc}", file=sys.stderr)
                return 1
    finally:
        # ⚠️ The derived bed is scratch, and it lives inside `output/brief/<date>/` — the folder a human opens to find the
        # day's deliverable. Left behind it is a file with no explanation, so it goes whether the run succeeded or
        # not. The master in `resource/` is untouched either way; this is a copy.
        if bed is not None:
            bed.unlink(missing_ok=True)

    return 0


def _fetch(date: str) -> int:
    """Fetch every source and write the day's snapshot. Returns 0, or a refusal code.

    ⚠️ This is the **only** function in the tool that touches the network, and it is skipped
    entirely when a snapshot already exists — which is what makes the rebuild promise real.
    `04-data-ownership.md`: *"a video must be rebuildable without re-fetching — the numbers
    will have moved by the time anyone looks at it."*
    """
    # ── The spine. Prices abort the run, because a brief with no market in it is not a
    # degraded brief — it is a wrong one. ─────────────────────────────────────────────
    try:
        indexes = tradingview.indexes()
    except tradingview.ScanError as exc:
        print(f"refusing to build {date}: {exc}", file=sys.stderr)
        return 1

    # Is this the session that was asked for, and has it finished printing? ⚠️ Load-bearing,
    # because the run is manual: a holiday produces no error, only yesterday's numbers.
    try:
        bar, updated = facts.stamps(indexes)
        session_date = session.ensure_final(bar, updated, date)
    except (tradingview.ScanError, session.StaleSessionError) as exc:
        print(f"refusing to build {date}: {exc}", file=sys.stderr)
        return 1

    # ⚠️ Nothing is written until the run is known valid, and everything is filed under the
    # session the data actually *describes* rather than the date that was asked for.
    # Snapshotting before the guard left a `store/2026-10-11/` behind for a run that refused —
    # a directory that reads as a day that was built.
    day = session_date.isoformat()
    store.write_raw(day, f"{indexes.name}.json", indexes.raw)

    # The rest of the spine: breadth, DMA, sectors and the volume floor all compute over
    # this universe, so a silent truncation would move published percentages. The fetch
    # asserts its own row count against `totalCount` (0085_05 consumes it).
    try:
        world = tradingview.universe()
    except tradingview.ScanError as exc:
        print(f"refusing to build {date}: {exc}", file=sys.stderr)
        return 1
    store.write_raw(day, f"{world.name}.json", world.raw)

    # Block 6's cap tiers are a **separate scan**, so a failure here costs only that card — it is
    # not the universe the breadth and DMA percentages are computed over.
    broader: tradingview.ScanResult | None
    try:
        broader = universe.fetch_broader()
        store.write_raw(day, f"{broader.name}.json", broader.raw)
    except tradingview.ScanError as exc:
        print(f"broader indices omitted: {exc}", file=sys.stderr)
        broader = None

    # ── Everything that is not the spine degrades to omission. ────────────────────────
    dependencies: tradingview.ScanResult | None
    try:
        dependencies = tradingview.dependencies()
        store.write_raw(day, f"{dependencies.name}.json", dependencies.raw)
    except tradingview.ScanError as exc:
        print(f"dependency strip omitted: {exc}", file=sys.stderr)
        dependencies = None

    # The four BSE feeds. A 7-day forward window, counted from the session — both ends
    # inclusive, which is what "in the next 7 days" means to a reader.
    until = session_date + _datetime.timedelta(days=7)
    flows = _degrade(day, "FII/DII flows", bse.flows, bse.net_flows, None)
    actions = _degrade(
        day,
        "corporate actions",
        bse.actions,
        lambda payload: bse.actions_in_window(payload, session_date, until),
        [],
    )
    ipos = _degrade(
        day,
        "IPO calendar",
        bse.ipos,
        lambda payload: bse.openings_in_window(payload, session_date, until),
        [],
    )
    announcements = _degrade(
        day, "announcements", bse.announcements, bse.latest_announcements, []
    )

    bundle = facts.build(
        day,
        indexes=indexes,
        world=world,
        broader=broader,
        dependencies=dependencies,
        flows=flows,
        actions=actions,
        ipos=ipos,
        announcements=announcements,
    )
    path = store.write_facts(day, bundle)
    print(
        f"facts bundle written: {path} "
        f"({len(bundle['indexes'])} indices, "
        f"{len(bundle.get('broader', []))} broader, "
        f"{len(bundle.get('dependencies', []))} dependencies, "
        f"{len(world.rows)} universe rows, "
        f"{len(bundle.get('sectors', []))} sectors, "
        f"breadth {bundle.get('breadth', {}).get('rising', '?')}up/"
        f"{bundle.get('breadth', {}).get('falling', '?')}down, "
        f"{len(bundle.get('corporate_actions', []))} actions, "
        f"{len(bundle.get('ipos', []))} ipos, "
        f"{len(bundle.get('announcements', []))} announcements, no strings)",
        flush=True,
    )

    return 0


def _publish(args: argparse.Namespace) -> int:
    """Upload one date's built editions to YouTube.

    ⚠️ **`--authorise` is checked before the date is parsed**, because it is the one subcommand that has nothing to
    do with a date: it opens a consent window, writes a token and exits. Validating a date first would refuse the
    one thing that does not need it.

    ⚠️ **`--check` is checked in the same place, for the same reason** — and because its whole point is to be run
    *before* there is anything to publish. A date would be a requirement nothing in it has.
    """
    if args.authorise:
        return publish.authorise()
    if args.check:
        return publish.check()

    requested = args.date if args.date is not None else _today()
    try:
        date = _datetime.date.fromisoformat(requested).isoformat()
    except ValueError:
        print(f"--date must be YYYY-MM-DD, got {requested!r}", file=sys.stderr)
        return 2
    return publish.run(
        date,
        _editions(args.lang),
        privacy=args.privacy,
        force=args.force,
        dry_run=args.dry_run,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="market-overview",
        description="Builds the daily Market Brief from live market data.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    build_cmd = sub.add_parser(
        "build",
        help="build one date's Bengali and English packages",
        description=(
            "Fetch, compute the facts bundle, render both editions and assemble "
            "output/brief/<date>/<lang>/. Refuses to publish on a stale session."
        ),
    )
    build_cmd.add_argument(
        "--date",
        default=None,
        metavar="YYYY-MM-DD",
        help=(
            "the session date to build — defaults to today "
            "(a re-render reads store/<date>/ instead of fetching)"
        ),
    )
    build_cmd.add_argument(
        "--lang",
        nargs="+",
        choices=ALL_LANGUAGES,
        default=None,
        help=(
            "which edition(s) to build, in the order given — "
            f"default: {' '.join(LANGUAGES)}"
        ),
    )
    build_cmd.set_defaults(func=build)

    publish_cmd = sub.add_parser(
        "publish",
        help="upload one date's built packages to YouTube",
        description=(
            "Upload each edition's video and thumbnail from output/brief/<date>/<lang>/, straight from the "
            "package's own metadata. Idempotent: an edition already uploaded from the same facts bundle "
            "is skipped rather than posted twice."
        ),
    )
    publish_cmd.add_argument(
        "--date",
        default=None,
        metavar="YYYY-MM-DD",
        help="the date whose packages to upload — defaults to today",
    )
    publish_cmd.add_argument(
        "--lang",
        nargs="+",
        choices=ALL_LANGUAGES,
        default=None,
        help=(
            "which edition(s) to upload, in the order given — "
            f"default: {' '.join(LANGUAGES)}"
        ),
    )
    publish_cmd.add_argument(
        "--privacy",
        choices=publish.PRIVACY,
        default=publish.DEFAULT_PRIVACY,
        help=(
            "how the video lands on YouTube — "
            f"default: {publish.DEFAULT_PRIVACY} (see the note in publish.py)"
        ),
    )
    publish_cmd.add_argument(
        "--force",
        action="store_true",
        help="upload again even though this edition has already been posted",
    )
    publish_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "walk the whole upload and print what would be sent, without sending or recording anything — "
            "the way to rehearse the flow on a machine with no credentials"
        ),
    )
    publish_cmd.add_argument(
        "--check",
        action="store_true",
        help=(
            "check that the credentials on disk still work, then exit — needs no package and uploads nothing. "
            "Run it before a build, not after one"
        ),
    )
    publish_cmd.add_argument(
        "--authorise",
        action="store_true",
        help=(
            "run the OAuth consent flow once and store a refresh token, then exit — "
            "the only step that needs a browser"
        ),
    )
    publish_cmd.set_defaults(func=_publish)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
