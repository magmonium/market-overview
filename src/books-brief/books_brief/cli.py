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
    identity,
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
from .fetch import amazon, google_books, indie, nyt, rokomari, woocommerce
from market_overview import audio, env

#: ⚠️ The source clients, by vendor slug. **Adding a client is one entry here and nothing else** — which is the point
#: of a registry: `gather` stays ignorant of which vendors exist, and a vendor it has no client for simply does not
#: contribute. That is the same degrade-to-omission rule as everywhere else.
#:
#: ⚠️ **The rule is: a client is registered when the lists declared for it resolve** (ticket 29). That is the same rule
#: that keeps a vendor with no client from refusing a chart, applied to the other end of the same wire.
#:
#: ⚠️ **`amazon`, `indie` and the four international Amazon stores are registered**, because their declared addresses
#: resolve — verified rather than assumed. The Amazon books nodes return **30 ranked cards** on every marketplace
#: (`amazon.com`, `.co.uk`, `.ca`, `.com.au` and `.in`, fetched 2026-10-15), and `indie/national` returns **135** for the
#: week the client derives from the address.
#:
#: ⚠️ ⚠️ **And the Amazon stores are `LIVE`** (`charts.LIVE`). Their pages state **no date**, so before 2026-10-15
#: `freshness.guard` discarded every row they produced and made every chart declaring one **absent** — which is why
#: `comics` and `all-language` never built. ⚠️ `gather` now hands `charts.LIVE` to the guard: a live ranking is kept, and
#: a live vendor that answers *nothing* is still missing.
#:
#: ⚠️ ⚠️ **`rokomari` and `boichitro` are registered now, and they are the Bengali chart's two vendors** (ticket 30).
#: `rokomari` was written, tested and left out for one reason — *"the payload carries no date anywhere"* — and that
#: reading of the **source** was the blocker, not the client: a retailer's bestseller category is regenerated per order,
#: so it has **no stale copy to date**, which is exactly the case `charts.LIVE` exists for. ⚠️ Ticket 29's *"finding a
#: date is what makes it usable"* was the right reading of the **guard** and the wrong reading of the vendor.
#:
#: ⚠️ **`boichitro` is a WooCommerce shop, not a scrape**: `/wp-json/wc/store/v1/products?orderby=popularity` returns a
#: hundred-deep JSON ranking with a real ISBN on some rows — so the Bengali chart has an **Indian** list again, and
#: `bengali` builds. ⚠️ See `fetch/woocommerce.py` for the seven candidate addresses that were fetched and the four
#: that turned out not to be sources at all (an Amazon search page, an empty Daraz tag, a Goodreads shelving count and a
#: Flipkart category browse).
#:
#: ⚠️ **`boighar` is the same client and is deliberately not registered** — its ordering is unverifiable and it states no
#: ISBN. ⚠️ And **`anandabazar` has neither a client nor a list**, and under ticket 29's address rule cannot be declared.
CLIENTS: dict[str, object] = {
    "nyt": nyt,
    "indie": indie,
    # ⚠️ **One module under five slugs** — the client is marketplace-aware, so registering a store is *naming* it, not
    # writing a second client. ⚠️ `us`/`uk`/`ca`/`au` arrived with the English chart's move to **worldwide** (2026-10-15).
    "amazon-us": amazon,
    "amazon-uk": amazon,
    "amazon-ca": amazon,
    "amazon-au": amazon,
    "amazon-in": amazon,
    # ⚠️ **The Bengali chart's vendors** (tickets 30, 32) — a Bangladeshi bookseller and **two** Indian ones, which is
    # the bridge ticket 21 asked for and ticket 29 could not build.
    "rokomari": rokomari,
    "boichitro": woocommerce,
    # ⚠️ **The same module under a third slug** — `woocommerce.py` is store-aware, so declaring Bangabani is *naming* it
    # rather than writing a client. ⚠️ It is registered because its lists resolve: 100 products, 54 of them with a real
    # ISBN-13 in `sku`, verified by fetching the address the chart declares (ticket 32).
    "bangabani": woocommerce,
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

    #: ⚠️ ⚠️ **A work's *best position per list*, and only then the sum across lists** (ticket 32).
    #:
    #: ⚠️ **The first version of this summed every listing, and the merge of the committed week caught what that costs.**
    #: BoiChitro lists `Chandmama` **three times** in its own bestseller ranking — three product ids, ranks 92, 95 and 96 —
    #: and summing the three gave that book a score of **2.7**, which put it at **rank 1** on the Bengali chart. ⚠️ That is
    #: not corroboration, it is one shop's duplicate listings counted three times, and it is the very thing
    #: `corroborate`'s docstring calls *"a lie told in arithmetic"*.
    #:
    #: ⚠️ **The rule is ticket 03's own**: *"a title carried by three **lists** accumulates three terms."* A list that
    #: carries a title twice has still ranked it once — at its best position — so a work contributes **at most one term
    #: per list**, and `rank.score`'s sum is then exactly the corroboration bonus it was written to be.
    best: dict[tuple[str, str], corroborate.Row] = {}
    for row in rows:
        key = (identity.work(row.title, row.author), row.list)
        if key not in best or row.rank < best[key].rank:
            best[key] = row

    return {
        work: rank.score(
            [
                rank.Listing(list=row.list, rank=row.rank, size=sizes[row.list])
                for (carried, _), row in best.items()
                if carried == work
            ],
            weights=weights,
        )
        for work in {identity.work(row.title, row.author) for row in rows}
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
        observed = seen.observed.get(title.key)
        candidates.append(
            rank.Candidate(
                key=title.key,
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
    #: ⚠️ **Failures are collected by *message*, never printed per title.** A source-wide outage — Google Books
    #: answering `429 Quota exceeded … Queries per day` to everything, Open Library rate-limiting a backfill — answers
    #: every title identically, and a hundred and thirty copies of one line is not a report. ⚠️ It is worse than noise:
    #: it buries the row that failed *differently*, which is the only one an operator can act on.
    missed: dict[str, list[str]] = {}

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
        details[title.key] = enrich.Details(**placed)

        try:
            volume = google_books.fetch(title.isbn)
        except Exception as error:  # noqa: BLE001 — a failed lookup is an absent field, not a lost book
            missed.setdefault(f"google books did not answer: {error}", []).append(title.isbn)
            volume = None

        # ⚠️ **The list's image first — and it is resolved whether or not Google answered.** The vendor chose the
        # picture that represents the title it ranked, and a cover is the one field where the list's own answer is the
        # better one: Google's edition is not necessarily the edition that is selling.
        #
        # ⚠️ **The list's URL is not Google's to withhold, and this line used to let it be.** The two `continue`s that
        # sat above it sent a title whose lookup failed or 429'd straight past its own cover — so a keyless run threw
        # away every image the list had already handed it, and the row fell to ticket 07's branded tile for a reason
        # that had nothing to do with the cover. ⚠️ That is why the fetch above now *assigns* `None` rather than
        # leaving the loop.
        #
        # ⚠️ **And the source order lives in `covers.url_for`, not here.** Its terminal fallback is Open Library, which
        # needs no key and no quota — the only source left once Google Books has spent the day's `Queries per day` and
        # the list carried no image of its own, which is every NYT, indie and Rokomari row.
        source = covers.url_for(
            title.isbn, listed=title.cover_url, google=volume.cover_url if volume else None
        )
        cover = None
        # ⚠️ No `if source:` guard, and its absence is the point: `url_for` is **total** — it always names a source, so
        # a title that reaches here has a URL to try. A guard would silently restore the old behaviour for any caller
        # that forgot one of the three.
        try:
            cover = covers.download(source, title.isbn)
        except Exception as error:  # noqa: BLE001 — same rule: an absent cover, not an absent row
            missed.setdefault(f"the cover did not download: {error}", []).append(title.isbn)

        if volume is None:
            # ⚠️ **The row keeps its cover and gains nothing else.** There is no volume to merge, and ticket 07's rule
            # is that a field with no value omits — never that the row is dropped, and never that a cover in hand is.
            if cover is not None:
                # ⚠️ Keyed by the **work** (ticket 32) — the entry was created under `title.key` above, so merging
                # under `title.isbn` here would write a *second*, unreachable entry and lose the cover silently.
                details[title.key] = dataclasses.replace(details[title.key], cover=cover)
            continue

        details[title.key] = dataclasses.replace(
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

    _report(missed)

    return details


def _report(missed: dict[str, list[str]]) -> None:
    """Say each distinct failure **once, with its count** — and say nothing at all when there was none.

    ⚠️ **One line per *kind* of failure is the report; a line per title is a log nobody reads.** The 503 wall this
    replaces was a hundred and thirty copies of one sentence, and it hid the only thing worth seeing: a title that
    failed for its *own* reason.

    ⚠️ **The ISBNs stay, capped at three.** *Which* titles a failure hit is the evidence, but all of them on one line is
    the wall again — and the rest are in the snapshot for anyone who wants to check one.

    ⚠️ **The empty case prints nothing.** A run where every source answered has nothing to report, and an unconditional
    summary would put a line of noise in every healthy log — which is how a real warning stops being read.
    """
    for message, isbns in sorted(missed.items()):
        shown = ", ".join(isbns[:3])
        rest = f" and {len(isbns) - 3} more" if len(isbns) > 3 else ""
        print(f"{message} — {len(isbns)} of the week's titles: {shown}{rest}", file=sys.stderr)


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

        # ⚠️ ⚠️ **One call per *client*, not one per *vendor*** (2026-10-15). ⚠️ `CLIENTS` is keyed by vendor, but
        # `fetch(chart, week=…)` reads **every list the chart declares for that client** — eight Amazon storefronts are
        # one module, and both Bengali booksellers are `woocommerce`. ⚠️ So calling it once per vendor re-fetched every
        # store once per store: **64 requests for the comics chart instead of 8**, with every row arriving **eight
        # times**. See `test_a_client_shared_by_several_vendors_is_asked_once`.
        #:
        #: ⚠️ **And the duplicates were not harmless.** `_weekly` collapses a work's rows *per list*, so the sum
        #: survived — but it sizes each list by **counting its rows**, and `rank.weight` scales a list by its depth
        #: (`min(1, size / N_REF)`). ⚠️ A thirty-card storefront was therefore sized **240**, which lifts it from a
        #: **0.3** weight to a full **1.0** and inflates its position scores with it — so the chart ranked that vendor
        #: far above the weight ticket 03 gives it, and **the error grew with every store added**: 4× on the English
        #: chart, 8× on comics. ⚠️ It was invisible for as long as every chart had one store per client.
        #:
        #: ⚠️ The vendor named in a complaint is the **first** vendor this client serves for this chart, because the
        #: failure is the *client's* — naming one of its stores is naming the module that failed.
        clients: dict[object, str] = {}
        for vendor in cliented:
            clients.setdefault(CLIENTS[vendor], vendor)

        rows: list[corroborate.Row] = []
        for client, named in clients.items():
            try:
                # ⚠️ **Fetch, snapshot, parse — in that order, and the conductor owns all three.**
                #
                # This is the brief's `_degrade(day, name, fetch, parse, default)` — *"Fetch one non-spine feed, snapshot
                # it, shape it"* — and the middle step is why a client hands back a `Page` rather than rows. ⚠️ Ticket
                # 18's rule is that the raw response is snapshotted **even when parsing fails**, because *"at that point
                # the evidence of what was actually received is exactly what is needed"* — and a client that had already
                # parsed could only ever offer a response its own parser had vouched for.
                for page in client.fetch(chart, week=week):  # type: ignore[attr-defined]
                    store.write_raw(week, page.name, page.payload)
                    rows.extend(
                        # ⚠️ **`published` is handed on, and it is not decoration.** `indie`'s list is dated *in its
                        # own address*, so the response cannot state it — and a `parse` called without it returns rows
                        # that `freshness` correctly refuses, which is a source that can never be used. ⚠️ A client
                        # whose date is in the payload ignores it; see `Page.published`.
                        client.parse(  # type: ignore[attr-defined]
                            page.payload, listing=page.listing, published=page.published
                        )
                    )
            except Exception as error:  # noqa: BLE001 — a failed vendor is an absent chart, not a crashed run
                print(f"{chart.slug}: {named} did not answer: {error}", file=sys.stderr)

        # ⚠️ **Ticket 10's freshness guard, and it is not a filter.** A stale list's rows are dropped *and* a vendor left
        # with nothing is a **missing source** — ticket 18: *"a stale source is a missing source for that week."*
        # ⚠️ **`live=charts.LIVE`** so the Amazon stores — whose pages state no date — are not refused as stale. See
        # `charts.LIVE` for the distinction and `freshness.guard` for the exact scope of the exemption.
        # ⚠️ **`monthly=` is derived from the chart's own declarations, never spelled here**: cadence is a property of a
        # *list* (`charts.CADENCES`), and a second copy of it in the conductor would be a second place for it to drift —
        # the same reason `KNOWN` is derived from `charts.ALL` rather than listed again.
        guarded = freshness.guard(
            rows,
            week=week,
            vendors=cliented,
            live=charts.LIVE,
            monthly=tuple(entry.slug for entry in chart.lists if entry.cadence == "monthly"),
        )

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
                    # ⚠️ **The work** (ticket 32) — the field `window.observe` keys the week by, and the same one the
                    # snapshot will carry, so the week being built and the weeks already on disk agree about what a row
                    # *is*. ⚠️ `isbn` rides along because it is a field of the row, not its identity.
                    "key": title.key,
                    "isbn": title.isbn,
                    "score": weekly.get(title.key, 0.0),
                    "rating": details[title.key].rating if title.key in details else None,
                    "ratings_count": (
                        details[title.key].ratings_count if title.key in details else None
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

    # ⚠️ ⚠️ **The market band is no longer fetched** (2026-10-15). Ticket 08 put a TradingView scoreboard behind the
    # books — *"the world behind the book"* — and it is not this product's data: a viewer came for a book chart and got
    # an index ticker they never asked for, from a source with nothing to do with the ranking.
    #
    # ⚠️ **Not passing a ticker is the whole change.** An absent `ticker` key is ticket 08's own *designed degrade*, so
    # the composition already draws no band and the render layer needs nothing. ⚠️ `_band` and `ticker.py` stay: they are
    # tested, and a chart is free to want the band back — this is a product decision, not a broken source.
    return facts.build(week, charts=built, window_weeks=_window_weeks(week))


def _covered(bundle: dict, only: tuple[str, ...] | None = None) -> list[str]:
    """Every ISBN whose row records a cover — **across the charts that are about to draw.**

    ⚠️ **One call, not one per chart.** The superset repeats titles (ticket 14), so staging per chart would copy the
    same file up to four times — and the cache is keyed by ISBN precisely so that one copy serves every chart.

    ⚠️ `only` narrows it to the charts a run was *asked* for; `None` means every chart in the bundle. A cover copied
    for a chart nobody is going to render is a slower run and nothing else.
    """
    charts_in_bundle = bundle.get("charts", {})
    slugs = sorted(charts_in_bundle) if only is None else [slug for slug in only if slug in charts_in_bundle]

    return sorted(
        {
            row["isbn"]
            for slug in slugs
            for row in charts_in_bundle[slug].get("ranked", [])
            if row.get("cover") is not None
        }
    )


def _seconds(bundle: dict, slug: str) -> float:
    """One chart's video length, in seconds — **read off the timeline the renderer is handed**, never re-derived.

    ⚠️ The bundle's `timeline.total_frames` is what the composition's `durationInFrames` comes from (ticket 06), so it
    is the only number that is certainly the video's length. Recomputing it from the row count would be a second copy
    of the arithmetic — and the copy that fell behind would be the one the bed was cut to, which shows up as music that
    stops before the close card.
    """
    timeline = bundle["charts"][slug]["timeline"]
    return timeline["total_frames"] / timeline["fps"]


def _music(week: str, chart: charts.Chart, seconds: float) -> tuple[pathlib.Path, str] | None:
    """Normalise the supplied bed for **one chart's** run, or `None` when none was supplied (0085_11).

    ⚠️ **One bed per chart, where the brief has one per run.** The brief's two editions are the same length, so a single
    derived file serves both; four charts are four lengths, and each chart's fade-out is anchored to the end of *its*
    run — so one file cut to the longest would run past the shorter charts' close cards.

    ⚠️ The bed is the **brief's own** (`paths.music_dir()`), and the toolchain is the repository's (`paths.repo_root()`):
    this product borrows both, exactly as it borrows the mark.

    ⚠️ The derived bed lands in the chart's own package folder and is removed by the caller whether the run succeeds or
    not. The master in `resource/` is only ever an input and is never written — see `market_overview.audio`.
    """
    directory = package.dir_for(week, chart.slug)
    directory.mkdir(parents=True, exist_ok=True)
    return audio.prepare(
        directory,
        seconds,
        root=paths.repo_root(),
        resource=paths.music_dir(),
    )


def _produce(
    chart: charts.Chart, week: str, *, kind: str, bed: pathlib.Path | None = None
) -> pathlib.Path:
    """Render one artefact **into scratch, and move it into place only once it is whole.**

    ⚠️ **Remotion's `--overwrite` unlinks its target before writing it.** Rendering straight at the package file would
    therefore let a render that dies at 90% — or is killed — destroy last week's good delivery, while the folder still
    looked like a package. So every render writes a dot-prefixed sibling and is moved into place only once it exists.
    That is the reel's rule, and it is the reason a failed run leaves the previous week untouched.

    ⚠️ ⚠️ **The dot prefix *is* the marker — and the extension has to stay last.** This used to name the scratch file
    `.{name}.part`, and Remotion **refuses to render h264+aac to anything that does not end in `.mp4`, `.mkv` or
    `.mov`**:

        TypeError: When using the h264 codec with the aac audio codec, the output filename must end in one of the
        following: mp4, mkv, mov.

    ⚠️ It fails *after* the composition has bundled, so it looks like a render failure rather than a naming one. ⚠️ And a
    **still has no codec to validate**, which is why every thumbnail rendered happily and only the videos died — the
    worst shape a bug can have. ⚠️ The reel never had it: `.reel-vinyl.mp4` keeps its extension, and that is what this
    matches.

    ⚠️ **`bed` is the chart's already-normalised music, and it is muxed on, never baked in.** The composition carries no
    audio at all; the bed is put on the finished file here (`audio.mux`, `-c:v copy`), so the frames that land in the
    package are bit-for-bit the ones the renderer produced. ⚠️ `None` is a **supported** state — no `music.*` supplied —
    and the video is simply moved into place silent, exactly as the brief behaves without a bed.
    """
    directory = package.dir_for(week, chart.slug)
    directory.mkdir(parents=True, exist_ok=True)

    name = package.filenames(week, chart.slug)[kind]
    target = directory / name
    scratch = directory / f".{name}"

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
        if bed is not None:
            # ⚠️ **The music is added after the render, and the picture is copied rather than re-encoded.** A bed baked
            # into the composition would be encoded once per chart and would skip `audio.prepare`'s loudness
            # normalisation; muxing keeps the render silent and the picture untouched. ⚠️ `audio.mux` writes the target
            # through its own staging file, so the package path is never observable as a half-written one.
            audio.mux(scratch, bed, target, root=paths.repo_root())
        else:
            scratch.replace(target)
    finally:
        # ⚠️ Removed even on failure: a crashed run must not leave scratch where a deliverable belongs.
        scratch.unlink(missing_ok=True)

    return target


def build(week: str, only: tuple[str, ...] = ()) -> int:
    """Build one week's charts — or **replay** the snapshot when the week is already recorded.

    ⚠️ **The order is the run.** The bed is cut first — **per chart**, because an unusable one is a refusal and a refusal
    that arrives after an hour of frames is an hour spent learning nothing — then thumbnails before videos (ticket 16's
    quality gate), and the package last, because the metadata describes artefacts that have to exist and the manifest is
    what says the folder is finished.

    ⚠️ ⚠️ **`only` narrows the *render*, never the *gather*.** The bundle is the week's evidence and the replay path
    (ADR 0003), so a run asked for one chart still fetches, corroborates and snapshots the **whole** week — a partial
    snapshot would leave a later re-render of a different chart with nothing to replay. ⚠️ What the filter buys is the
    expensive half, which is the render.
    """
    snapshot = store.dir_for(week) / store.FACTS

    if snapshot.is_file():
        # ⚠️ The switch. A snapshot is only ever written by a run that got past the refusal below, so finding one means
        # the week is already established — and re-fetching it would produce a *different* chart from the same week.
        recorded = store.read_facts(week)
        # ⚠️ The rows replay as recorded; the **running order** is re-laid by today's schedule (see `facts.retime`),
        # and written back so the staged copy — a byte-for-byte copy of the snapshot — carries it too.
        bundle = facts.retime(recorded)
        if bundle != recorded:
            store.write_facts(week, bundle)
    else:
        bundle = gather(week)
        if not bundle["charts"]:
            print(f"{week}: no chart could be built", file=sys.stderr)
            return 1
        store.write_facts(week, bundle)

    built = {slug: charts.get(slug) for slug in sorted(bundle["charts"])}

    # ⚠️ ⚠️ **A chart that was asked for and is not in the bundle is said out loud.** The alternative is a run that
    # prints nothing, exits zero and produces no video — which reads as success. ⚠️ **The ordinary case is a replayed
    # week**: a snapshot holds the charts that were built when it was written, and asking a recorded week for a chart it
    # does not hold cannot fetch one (ADR 0003 — the snapshot's existence is the switch), so the operator is owed that
    # sentence rather than a folder to go and check. ⚠️ The other case is a chart whose declared sources did not answer
    # this run, which is ticket 18's absent-not-smaller rule arriving one step later.
    wanted = list(built)
    if only:
        asked = list(dict.fromkeys(only))
        for slug in asked:
            if slug in built:
                continue
            print(
                f"{slug}: not in this week's bundle — it could not be built"
                if slug in charts.KNOWN
                else f"{slug}: not a chart — the charts are {', '.join(charts.KNOWN)}",
                file=sys.stderr,
            )
        wanted = [slug for slug in asked if slug in built]

    # ⚠️ **Staged once, before any render.** A composition can only fetch from the render project's `public/`, and one
    # staged bundle serves every render (ticket 13) — the chart id is the only thing that varies. Staging inside the
    # loop would copy the same bytes four times, and worse, would let the first render succeed against a file a later
    # iteration had not written yet.
    stage.snapshot(week, paths.public_dir())
    # ⚠️ The mark rides **beside** the bundle for the same reason the brief keeps its own out of `facts.json`: it is not
    # a fact, and it is identical in all four charts. ⚠️ And it is staged even when there is none — as an explicit
    # `null` — because a fetch that 404s is a failed render, not a chart without branding.
    stage.mark(paths.public_dir())
    # ⚠️ Read off the **snapshot**, not off a live object: a replay reaches here with nothing but the committed facts,
    # and staging has to work identically on that path. ⚠️ Staged for the charts that are about to draw — a cover copied
    # for a chart nobody asked for is a slower run and nothing else.
    stage.covers(_covered(bundle, only=wanted), paths.public_dir())

    rendering = [built[slug] for slug in wanted]

    if not rendering:
        # ⚠️ **Non-zero when nothing is going to be rendered.** The week may well be snapshotted by now, but the operator
        # asked for a video and there is none — and a run that exits zero having produced nothing is the silence ticket
        # 10 refuses.
        return 1

    # ⚠️ **The bed, per chart, before any render** — the brief's own ordering (0085_11), for the brief's own reason: an
    # unusable bed is a **refusal**, and a refusal that arrives after an hour of frames is an hour spent learning that
    # nothing was ever going to work. ⚠️ **Per chart, not per run**: four charts are four lengths, and each chart's
    # fade-out is anchored to the end of its own run (see `_music`).
    beds: dict[str, pathlib.Path] = {}
    try:
        for chart in rendering:
            try:
                prepared = _music(week, chart, _seconds(bundle, chart.slug))
            except audio.AudioError as exc:
                print(f"{week}/{chart.slug}: refusing to render — {exc}", file=sys.stderr)
                return 1
            if prepared is not None:
                beds[chart.slug] = prepared[0]
                print(prepared[1], flush=True)

        # ⚠️ **Every thumbnail before any video.** Four one-frame stills cost seconds, so a chart whose collage reads
        # badly is seen and killed before an hour of frames is spent on it — the reel's own ordering, and its reason.
        for chart in rendering:
            _produce(chart, week, kind="thumbnail")

        # ⚠️ The bed rides **beside** the render, never inside it: it is muxed onto the finished video, so the picture is
        # bit-for-bit what the renderer produced (see `_produce`). A chart with no bed supplied is simply moved silent.
        for chart in rendering:
            _produce(chart, week, kind="video", bed=beds.get(chart.slug))

        # ⚠️ **The package last, per chart** — `metadata-<chart>.json` is the file that says the folder is finished
        # (ticket 13), and it cannot honestly say so until the video and the thumbnail are both there.
        for chart in rendering:
            package.assemble(week, chart)
    finally:
        # ⚠️ The derived bed is scratch, and it lives inside the chart's package folder — the folder a human opens to find
        # the week's deliverable. Left behind it is a file with no explanation, so it goes whether the run succeeded or
        # not. The master in `resource/` is untouched either way; this is a copy.
        for bed in beds.values():
            bed.unlink(missing_ok=True)

    return 0


def main(argv: list[str] | None = None) -> int:
    """`books-brief build --week 2026-W41` · `books-brief publish --week 2026-W41 [--dry-run]`."""
    # ⚠️ **This is the product that needs it.** `NYT_API_KEY` is read straight from the environment by `fetch.nyt`,
    # and the repository's `.env` is what lets a hand-run find it without an `export` in every new shell.
    # ⚠️ Only variables the environment does not already set are filled, so an exported key still wins — and a
    # checkout with no `.env` behaves exactly as it did before. See `market_overview.env`.
    env.load()

    parser = argparse.ArgumentParser(prog="books-brief")
    commands = parser.add_subparsers(dest="command", required=True)

    builder = commands.add_parser("build", help="build one ISO week's charts")
    builder.add_argument("--week", required=True, help="the ISO week, e.g. 2026-W41")
    # ⚠️ Repeatable, and **every chart the week could build by default** — the same shape `publish --chart` keeps, and
    # for the same reason: the default is read off the *snapshot* rather than off the declaration table, because the
    # week may hold two charts and not four (ticket 13's partial delivery).
    #
    # ⚠️ It narrows the **render**, never the gather. The bundle is the week's evidence and the replay path (ADR 0003),
    # so a run asked for one chart still fetches and snapshots the whole week — which is what lets a later re-render of
    # a different chart replay instead of re-fetching. See `build`.
    builder.add_argument(
        "--chart",
        action="append",
        help="one chart to build; repeatable (default: every chart the week could build)",
    )

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
        return build(args.week, tuple(args.chart or ()))

    if args.check:
        return publish.check()

    return publish.run(
        args.week,
        args.chart or publish.charts_in(args.week),
        privacy=args.privacy,
        dry_run=args.dry_run,
    )

