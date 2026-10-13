# market-overview

Builds the **Market Brief** — one day's silent, music-backed, ≤3 min, 16:9 video about the Indian market, in
two language editions (Bengali and English), each with its own metadata and thumbnail.

**The tool is `market-overview`. The product is the Market Brief.** Output filenames carry the product's
name: `market-brief-<date>-<lang>.mp4`.

## Status

**End to end, both editions, rebuildable.** A run fetches, computes the bundle, renders the video and the thumbnail
for each language, and assembles `output/<date>/<lang>/`. Re-running a date re-renders from the snapshot without
touching the network, so a delivery can be reproduced and verified after the numbers have moved on. The design is
fully specified, and the specification is the source of truth for **what** to build:
`ideas/.scratch/market-brief/map.md` — 25 tickets, 24 decisions, none open. Build
order lives in `ideas/tasks/0085_market-brief_plan.md`. ⚠️ **Those two files are the only link to this repo** — it is
not a submodule, so nothing in `ideas/` points here (see `docs/adr/0001`).

## Vocabulary and decisions

- `CONTEXT.md` — the glossary: run, session date, facts bundle, label table, card, edition, package,
  snapshot, spine, degrade-to-omission.
- `docs/adr/` — the six load-bearing decisions.

## Requirements

Python ≥ 3.14 and [`uv`](https://docs.astral.sh/uv/). Node ≥ 24 for the render layer.

✅ **No system `ffmpeg` is required, and that question is settled.** Remotion ships its own build in
`node_modules/@remotion/compositor-*/ffmpeg`, and the pipeline uses that one — so the music mux, the thumbnail and the
loudness normalisation all work on a machine that has never installed ffmpeg. To use a different build, set
`MARKET_OVERVIEW_FFMPEG=/path/to/ffmpeg`.

⚠️ Two consequences worth knowing. The bundled binary is **`--enable-shared`**, so it will not start without
`DYLD_LIBRARY_PATH` pointing at its own directory — `audio.binary_env` supplies that, and anything invoking it
directly must too (run bare, it **aborts with nothing on stdout**, which is a silent failure if the exit code is
ignored). And it is a **stripped** build: `--disable-filters` with an allow-list, so `afade`, `acrossfade`,
`volumedetect` and `astats` are all **absent** — the obvious way to fade a bed, and the obvious way to check you
faded it, are exactly the two that are missing. `tests/test_audio.py` asserts the allow-list, and the absence.

## The typeface

**Noto Sans Bengali, vendored into `remotion/fonts/` — committed, not installed and not fetched**
(`docs/adr/0005`). The renderer used to name macOS's own *Kohinoor Bangla* and let the host resolve it, which
made the rendered pixels a property of the machine: the same `facts.json` drew different glyphs on Linux, and
that broke ADR 0003's rebuild promise and `tests/test_frame_identity.py` in the same silent stroke.

⚠️ **The weights are baked, not interpolated.** The face ships as a *variable* font, and leaving the browser to
instance `wght` 400/600/700 was measured to move the large figure's glyph edges by a couple of anti-aliasing
levels between a cold and a warm cache — invisible, and enough to break a byte-for-byte rebuild.
`remotion/fonts/README.md` carries the provenance and how to regenerate; `remotion/fonts.json` is the manifest,
read by **both** the renderer and the copy-budget gate, so the gate measures the face the brief is actually set
in.

## Run

```bash
uv run mo build --date YYYY-MM-DD
```

`mo` is the short name; `uv run market-overview build …` is the same CLI under its long name.

**`--date` is optional and defaults to today**, so the common case — publish the newest session — is a bare:

```bash
uv run mo build
```

⚠️ The default is a *request*, not an exemption: the session guard still refuses if today is a holiday, a
weekend, or not yet past the close, exactly as it would a typed date.

**`--lang` selects which edition(s) to build**, in the order given — one or more of `bn`, `en`. Omitted, the run
builds the shipping default (`bn`), so the flag is additive: re-cutting one edition should not mean re-rendering
the other.

```bash
uv run mo build --lang en          # English only
uv run mo build --lang en bn       # English first, then Bengali
```

One command, by hand — there is no scheduler, deliberately (`docs/adr/0004`).

⚠️ **Run it in the foreground, and expect it to take a long time.** A full brief is ~4,500 frames per edition plus
a still, so a two-edition run is well over an hour of rendering. **You will see progress while it works:** the tool
prints `rendering <lang> …` before each edition, and the renderer's own lines — `Bundling …`, `Rendered x/y, time
remaining …`, `Encoded x/y` — are forwarded live as they arrive (`render._stream`). Every one of those lines is
flushed, so a redirected run is legible too and nothing depends on setting `PYTHONUNBUFFERED`. A working run still
looks *slow* — it is an hour of rendering — but it no longer looks hung.

To keep a copy and watch it:

```bash
uv run mo build > /tmp/run.log 2>&1 &
tail -f /tmp/run.log
```

Interrupting is safe: every write is atomic or staged, so a killed run leaves the previous delivery intact and the
date folder visibly unfinished.

### Rendering speed

The render is the whole cost. It is dominated by how each frame gets *out* of the browser, and by how many run at
once — in rough order of value:

1. **Shared-memory capture.** Remotion's own `chrome-headless-shell` hands each frame to ffmpeg as a bitmap
   instead of JPEG-encoding it first, which skips real work per frame (Remotion ≥ 4.0.534 on Apple Silicon, macOS
   15+). It is **currently unavailable on this machine**: the bundled shell dies at "Getting composition"
   (`Target closed`, at `Getting composition`), so `render._browser_flag` falls back to system Chrome — and a
   browser without Remotion's patch uses JPEG screenshots. Restoring it is the single biggest win available, and
   it is worth a spike anywhere the shell launches:
   ```bash
   node_modules/.remotion/chrome-headless-shell/*/chrome-headless-shell-*/chrome-headless-shell --version
   ```
2. **Concurrency.** Remotion defaults to about half the cores. Measure it, then pin it — the number is a property
   of the machine, not of the product:
   ```bash
   npx remotion benchmark --concurrencies=6,8,10,12
   MARKET_OVERVIEW_CONCURRENCY=10 uv run mo build
   ```
   ⚠️ This **changes no frame**: the backdrop is a pure function of the frame index, so more tabs render the same
   picture sooner. That is what makes it safe to tune per machine. Absent, Remotion's own default stands.
3. **The composition.** The animated backdrop (`remotion/Backdrop.tsx`) is the per-frame cost, and it is now plain
   CSS — gradients, drifting lobes and a scrolling grid — rather than a WebGL canvas, so it is dramatically
   cheaper than the three.js world it replaced. `--log=verbose` lists the slowest frames if that is ever worth
   attacking.

⚠️ **What is deliberately not on the table:** `--scale` (renders a different picture) and
`--hardware-acceleration` (H.264 through VideoToolbox changes the encoded bytes, and Remotion warns the file is
significantly larger) — both trade the product for speed.

What a run does: **fetch or re-render** → compute the facts bundle → render both editions → assemble the
packages.

- **Bengali renders first**, so the primary edition is never hostage to the secondary.
- **A failed spine aborts and writes nothing.** Prices are the spine; every other source degrades to
  omission, dropping its own card.
- **A failed edition fails the run** — a half-populated date folder would look complete.
- **Writes are atomic** and run-scoped temporary directories are cleaned only on success.
- **A package is complete when `metadata-<lang>.json` exists**, and that file is written last. It is removed before
  the rest of the package is written, so a run that dies leaves a folder that visibly is not finished, rather than
  one that merely looks small. See the note in `src/market_overview/package.py`.

### Fetch, or re-render

**If `store/<date>/facts.json` exists, the run re-renders from it and never touches the network.** That is the
whole rebuild promise (`04-data-ownership.md`: *"a video must be rebuildable without re-fetching — the numbers will
have moved by the time anyone looks at it"*), and the log says which path it took:

```
re-render: reading store/2026-10-12/facts.json — not fetching
```

Two consequences worth knowing, because both are deliberate:

- **A past date can only be rebuilt, never re-fetched.** The session guard compares the date asked for against the
  *newest* session, which has moved on by definition — so on the fetch path Tuesday's date refuses on Wednesday.
  The snapshot is what makes yesterday reachable at all.
- **A re-publish cannot silently change the numbers.** Rendering the same date again reads what was published,
  not what the market looks like now. To force a fresh fetch, **delete the snapshot first**:

```bash
rm -rf store/2026-10-12 && uv run market-overview build --date 2026-10-12
```

That is the only way to refetch a date, and it is not reversible — `store/<date>/raw/` is the only evidence of
what the sources actually returned.

### Refusal cases

A run can legitimately refuse, and refusing is the correct outcome. ⚠️ **Every refusal exits non-zero and writes
nothing** — `1` for a refusal, `2` for a malformed `--date`.

| Case | Exit | Why it refuses |
|---|---|---|
| **Holiday**, weekend, or a mistyped date | 1 | *"asked for X but the newest session is Y"*. A holiday produces no error at all — only *yesterday's* numbers, which would publish under today's date. |
| **Mid-session** | 1 | *"session X has not finished printing"*. The india feed is ~15 min delayed, so "final" waits ten minutes past the close — 15:40 IST, under the earliest final write measured. Before that the numbers are still moving. |
| **Spine down** | 1 | The india scan is the spine. A brief with no market in it is not a degraded brief, it is a wrong one. |
| **Unusable mark** | 1 | `resource/logo.svg` has text that is not outlined, so it depends on a font being installed. Rendering it would look right here and different elsewhere (0085_10). |
| **Unmixable bed** | 1 | `resource/music.*` is not a container the tool's `ffmpeg` can read (0085_11). |
| **Incomplete package** | 1 | An artefact is missing. Assembly refuses to write metadata for a folder that would *look* complete (0085_13). |
| **Over a limit** | 0 | ⚠️ Reported, not refused. A title two characters long is truncated by YouTube and loses the move — bad, but not a reason to publish nothing. The run prints `warning: …` and carries on. |

Missing `logo.svg` or `music.*` is **not** a refusal: no mark and a silent brief are supported states. See Assets.

### Verifying a delivery

`tests/test_frame_identity.py` proves the property on the committed snapshot by rendering ten mid-brief frames
twice and comparing them — cheap enough to run in the default suite. To check an actual delivered file:

```bash
cp output/2026-10-12/bn/market-brief-2026-10-12-bn.mp4 /tmp/delivered.mp4
uv run market-overview build --date 2026-10-12      # re-renders from the snapshot
cmp /tmp/delivered.mp4 output/2026-10-12/bn/market-brief-2026-10-12-bn.mp4
```

⚠️ **Frame-identity is the requirement; byte-identity is the bonus.** A re-render that decodes to the same frames
is correct even if the container differs by a byte, because what an audience and a platform see are frames. If
`cmp` reports a difference, compare decoded frames before treating it as a fault:

```bash
D=node_modules/@remotion/compositor-darwin-arm64
DYLD_LIBRARY_PATH=$D $D/ffmpeg -i /tmp/delivered.mp4 -vsync 0 /tmp/a/%03d.png   # and the same for the new file
```

### Before you publish

The run cannot judge these, and they are the reason a human runs it:

- **The Bengali reads as Bengali, not as translated English.** The label tables are written per language, but
  *native phrasing* is not something a test can assert. This applies to the labels, the metadata and the
  description — three surfaces.
- **The music is audible at the right level.** The bed is normalised to −14 LUFS, which is a measurement, not a
  judgement about how it sits under nothing.
- **The cold open and the close carry the mark once `resource/logo.svg` is supplied.**
- **Numeral consistency** — the brief's Bengali numerals against the figures quoted from the sources.
- **The whole thing looks like a market brief**, which is the one check that has no proxy.

## Publish

```bash
uv sync --extra publish
uv run mo publish --date YYYY-MM-DD --lang bn en
```

Uploads each edition's video and thumbnail to the channel named by the operator's OAuth credentials, using the
package's own `metadata-<lang>.json` — the file `metadata.py` calls *"the JSON the deferred upload step will read"*.
So the upload cannot describe a video the tool did not make.

⚠️ **The client libraries are an optional extra.** `mo build` never imports them, so a build-only install stays at
one dependency; `mo publish` refuses with a message naming the extra rather than failing on an `ImportError`.

⚠️ **It lands `private` unless you say otherwise, and `--privacy public` is a decision rather than a default.**
ADR 0004's real protection was never the window server — it is the "Before you publish" list above, *"the reason a
human runs it"*. The schedule in `deploy/` inherits whatever you choose, so choosing nothing keeps the human in.

**It is idempotent**, keyed on the facts bundle's per-edition hash. A second run over the same day uploads nothing;
a *rebuilt* day **refuses** rather than putting a second video under a title a viewer has already seen. What went
up is recorded in `output/<date>/.published-<lang>.json` — *beside* the package, never inside it, because a package
is four files and nothing else.

### Rehearsing the upload

```bash
uv run mo publish --date YYYY-MM-DD --lang bn en --dry-run
```

⚠️ **`--dry-run` needs no credentials and no channel**, which is what makes it the way to test the flow on a
machine that has neither. It reads each package, validates it, builds the request body and prints the video, the
thumbnail, the title, the tags and the status that *would* go up — then stops. Nothing is sent and nothing is
recorded, so no `.published-<lang>.json` appears and the real run that follows still uploads:

```
bn: dry run — nothing was sent and nothing was recorded
  video        …/output/2026-10-12/bn/market-brief-2026-10-12-bn.mp4 (34.6 MB)
  thumbnail    …/output/2026-10-12/bn/thumbnail-2026-10-12-bn.jpg (0.1 MB)
  title        বাজার ব্রিফ | 12 অক্টোবর 2026 | নিফটি ৫০ −0.70%
  tags         শেয়ার বাজার, দৈনিক বাজার ব্রিফ, ভারতীয় শেয়ার বাজার, …
  description  17 lines — the whole text is the package's metadata-bn.txt
  status       category 27 · language bn · private · made for kids False
```

It is deliberately **not** a parallel code path. The package check and the already-published check are the same
ones the real run makes, so a rehearsal cannot pass where the upload would refuse — on an edition that has already
gone up it prints `already published` and no plan at all, because uploading nothing is what the next real run
would do.

The first run needs credentials; one step needs a browser:

```bash
uv run mo publish --authorise      # writes ~/.config/market-overview/token.json
```

⚠️ A token from an OAuth client whose consent screen is still in **"Testing" expires in seven days**. Publish the
consent screen first. It is the likeliest way a scheduled run dies, and it dies a week after everything looked fine.

### Creating the OAuth client (once)

This is the only part of the tool that cannot be done from the command line, and the console's menu names drift —
so the two things that actually matter are: **enable YouTube Data API v3**, then create an OAuth client of type
**Desktop app**.

1. **A Google Cloud project.** Create one (or reuse one) at <https://console.cloud.google.com>. It exists only to
   hold this client and is not otherwise tied to the channel.
2. **Enable the API.** *APIs & Services → Library*, search **YouTube Data API v3**, open it, **Enable**.
3. **Configure the consent screen.** *APIs & Services → OAuth consent screen* — the console now calls this *Google
   Auth Platform*, so if you see tabs named *Audience* and *Data Access* you are on the newer one, and it is the
   same three fields:
   - User type **External**. *Internal* is available only inside a Google Workspace domain.
   - An app name, a user-support email and a developer contact email. ⚠️ None of this is shown to viewers.
   - ⚠️ **Add your own Google account as a test user.** Until the app is published, only test users can authorise
     it — and a consent window that refuses the only account you have is a confusing place to discover that.
4. **Create the client.** *APIs & Services → Credentials → Create credentials → OAuth client ID*, application type
   **Desktop app**.
   ⚠️ **It has to be `Desktop app`, not `Web application`.** The tool runs Google's *installed app* flow and asks
   the OS for a random free port — `InstalledAppFlow.run_local_server(port=0)` in `publish.py` — so there is no
   fixed `http://localhost:<port>` to register, which is precisely what a Web client demands.
5. **Download the JSON.** The download icon beside the new client ID, or *Download JSON*. It arrives named
   `client_secret_<numbers>.apps.googleusercontent.com.json`; **rename it `client-secret.json`**, which is the
   filename `publish.py` looks for.
6. **Put it where the tool looks, and authorise:**

   ```bash
   mkdir -p ~/.config/market-overview          # or point MARKET_OVERVIEW_CREDENTIALS somewhere else
   cp ~/Downloads/client_secret_*.json ~/.config/market-overview/client-secret.json
   uv run --extra publish mo publish --authorise    # opens a browser; writes token.json beside it
   uv run --extra publish mo publish --check        # proves the token works — no package needed
   ```

⚠️ **`client-secret.json` is not what the upload authenticates with — the refresh token in `token.json` is.**
`--authorise` is the one step that must run on a machine with a browser, because a server cannot open a consent
window; `deploy/README.md` covers copying `token.json` to one. Both files live outside the repository and are never
committed.

⚠️ **The trap that bites a week later: a consent screen left in *Testing* expires the refresh token after seven
days.** Google caps a *Testing* app at **100 test users** and applies *"the 7-day refresh token expiration limit for
apps in the Testing status"*, so an uploader that worked today refuses with `invalid_grant` next week — having
looked healthy the entire time. Two ways out: re-run `--authorise` weekly, or set **Publishing status → Publish
app** to move the app *In production*, which lifts the limit. Publishing an unverified app is permitted: your own
consent screen then shows *"Google hasn't verified this app"*, and you click **Advanced → Go to …**. Nothing about
the upload changes — you are simply the only user it has.

### Testing against the channel, by hand

⚠️ **`deploy/` is not involved in any of this.** The timer exists only to *fire* the same `mo build` and
`mo publish` you would type yourself, so a local test needs nothing from it — no Docker, no cron, no systemd, no
`.timer` enabled.

```bash
uv sync --extra publish                                     # the client libraries are an optional extra

uv run --extra publish mo publish --check                   # is the token good? seconds, no package needed
uv run --extra publish mo publish --date 2026-10-12 --lang bn --dry-run   # what would go up; nothing is sent
uv run --extra publish mo publish --date 2026-10-12 --lang bn             # the real upload
```

⚠️ **`--extra publish` on every `uv run`, not only on the `uv sync`.** `uv run` re-syncs the environment to the
project's *default* set, so a bare `uv run` can remove the extra the line above just installed — the same trap
`deploy/daily-brief.sh` documents for the container. On a development checkout the two libraries also arrive
through the `dev` group, which is why a bare `uv run mo publish …` appears to work; the extra is what a build-only
install needs, and a missing one produces a refusal naming it rather than an `ImportError`.

Credentials are the **one-time** part — `client-secret.json` and `--authorise` — and they are their own section
above: [Creating the OAuth client](#creating-the-oauth-client-once).

⚠️ **`--check` belongs before a build, not after one.** A build is over an hour per edition and the token is the
part most likely to be wrong, so it is the difference between finding out in a second and finding out in an hour. It
proves the *token*, not the whole account — a scope the client was never granted would surface only at the upload
itself, and `--dry-run` is the one that walks the upload.

⚠️ **`--lang` defaults to `bn` alone**, so a bare `mo publish` ships one edition. Pass `--lang bn en` for both, and
note that `2026-10-12`'s English package is incomplete — only a thumbnail — so start with `--lang bn` or rebuild it
first:

```bash
uv run mo build --date 2026-10-12 --lang en     # re-renders from store/ — no network, but it is a render
```

The upload lands **`private`** unless you add `--privacy public`. What went up is recorded *beside* the package:

```bash
cat output/2026-10-12/.published-bn.json      # video_id · url · privacy · bundle_hash · published_at
```

⚠️ **Because that record is what makes the upload idempotent, a real run changes what the `--dry-run` afterwards
prints** — it reports `already published` rather than a plan. That is the next real run's actual behaviour, not a
bug. To upload again deliberately, delete the video on YouTube and pass `--force`.

### Every day, after the close

`deploy/` runs the whole thing on a timer — `OnCalendar=Mon..Fri 16:30:00 Asia/Kolkata`, `Persistent=true` —
either as a **systemd timer** on the host or as a **container with its own scheduler**:

```bash
docker compose -f deploy/compose.yaml run --rm brief              # one run
docker compose -f deploy/compose.yaml --profile scheduled up -d   # or leave a scheduler running
```

`docs/adr/0006` says why that time, why Mon–Fri, and why the privacy default is what it is; `deploy/README.md` is
the install, including the one thing that is easy to get wrong: **`output/` must persist**, because that is where the
record of what has already been uploaded lives.

## Layout

```
resource/   operator-supplied licensed assets (logo, music) — never committed
output/     generated packages, output/<date>/<lang>/ — never committed
store/      per-date snapshots: raw source responses + facts.json — rebuild a day from these
src/        the Python package
remotion/   the render layer (React/TS), and the vendored typeface in remotion/fonts/
deploy/     the systemd units and the wrapper that run it daily — see deploy/README.md
docs/adr/   decisions
tests/      tests
song-video/ the Song Reel — a separate tool and product, nested as its own uv project:
            song-video/README.md
```

A run writes to exactly two places, and neither is ever committed:

```
store/<date>/raw/*.json        the source responses, verbatim — written *before* parsing, so if the
                               parser is what broke, the evidence of what it was given is already on disk
store/<date>/facts.json        the computed bundle — the sole interface to the render layer, and the
                               only thing a re-render reads
output/<date>/<lang>/          the deliverable, four files and nothing else:
                               market-brief-<date>-<lang>.mp4 · metadata-<lang>.txt ·
                               metadata-<lang>.json · thumbnail-<date>-<lang>.jpg
```

⚠️ The snapshot lives **outside** `output/`, so a package contains exactly what a viewer should see and no
plumbing. The raw responses are the only evidence if a figure is ever disputed, which is the second reason they
exist — the first being that a video has to be rebuildable without re-fetching.

## Tests

```bash
uv run pytest -q
```

No network, no ffmpeg, and the tests that would need a browser stub it — so the suite is hermetic and fast. The
exceptions are deliberate and skip themselves when they cannot mean anything.

`tests/test_frame_identity.py` is the one that renders for real: ten mid-brief frames, twice, decoded and compared
frame by frame. It is the guard on the product's central claim, so it runs by default rather than behind an
environment variable — and it is why the suite needs Chrome present to be at full strength.

## Assets

Two files are dropped into `resource/` when they are available — **both optional**, see below:

- `logo.svg` — the product mark. **One asset, no light/dark variant needed.**
- `music.*` — the background bed. Any container `ffmpeg` reads.

See `resource/README.md`. The licence is yours; the pipeline records nothing and enforces nothing.

⚠️ **The Song Reel's songs are not these.** The nested `song-video/` product keeps its own `resource/song/` for the
masters it turns into reels — the **brief's** `resource/music.*` here is its music bed, and the **reel's** song goes
there. Two folders called `resource/`, two products, one licence decision each: `song-video/README.md` says where
the mp3 goes.

⚠️ **Both are optional, and the tool runs without them** — a markless, silent brief is a supported state, not a
degraded one, so a missing asset is never a refusal. What *is* a refusal is an asset the tool cannot use:
a `logo.svg` whose text is not outlined, or a `music.*` in a container the bundled `ffmpeg` cannot read. Both
are listed in the refusal table above.
