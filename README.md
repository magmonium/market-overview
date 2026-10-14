# market-overview — the repository

⚠️ **Two products are built from here, from one `src/`, sharing one data root and one render toolchain.** This is
the repository's README and it documents both. [Install](#install), [Configuration](#configuration) and
[Running](#running) cover each of them; everything after those is reference.

| Product | Tool | Source | What it makes |
|---|---|---|---|
| the **Market Brief** | `market-overview` — `mo` | `src/market_overview/` | one day's silent, music-backed, ≤3 min, 16:9 video about the Indian market, in Bengali and English |
| the **Song Reel** | `song-video` — `sv` | `src/song-video/` | one supplied song as a full-length 16:9 music video and its thumbnail, in one or more themes |

⚠️ **`./build` is the front door** — one command over both. It asks which product, then what that product needs, and
hands the answers to `mo` or `sv` as flags, so neither product's own CLI changes: see [Running](#running).

⚠️ **The data lives outside the repository.** Both products' assets and packages share one root —
`~/.local/share/market-overview` by default — namespaced per product, so a brief and a reel can render at the same
time without a lock: see [Configuration](#configuration).

## Where everything is

⚠️ **This is the repository's only README, and it is the whole document.** How to run both products, where their
data lives, what their assets are, what every term means, and how to put the brief on a server — all of it is
below, in this file.

The only other documents are the **decision records**: `docs/adr/` (the brief's seven) and
`src/song-video/docs/adr/` (the reel's six). They are kept separate deliberately — they record *why* a choice was
made and *when*, they are cited by name from the code (`docs/adr/0006`, `ADR 0003`, `publish.py`), and interleaving
them with instructions would make both harder to read.

## Install

### Common

| | Why |
|---|---|
| **Python ≥ 3.14** and [`uv`](https://docs.astral.sh/uv/) | both products are uv projects |
| **Node ≥ 24** | the render layer — installed once, used by both |
| **Chrome or Chromium** | ⚠️ Remotion's bundled `chrome-headless-shell` cannot be relied on — it aborts at "Getting composition" on some machines — so `render.py` searches for a real browser first |
| **No system `ffmpeg`** | Remotion ships its own, and both products use it — see below |
| **No fonts, no GPU** | the typeface is vendored, and nothing needs a display |

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

### The brief

```bash
uv sync --extra publish      # the brief's environment, with the publisher's libraries
npm install                  # the render layer
```

⚠️ `--extra publish` is what makes `mo publish` work. `mo build` needs none of it.

### The Song Reel

```bash
cd src/song-video
uv sync                      # its own environment; the brief arrives as an editable path dependency
```

⚠️ **It installs no second runtime and no second `ffmpeg`** — the reel renders with the brief's `node_modules` and
finds the toolchain through the brief's `audio` module, so those two `uv sync`s are the whole install.

## Configuration

### Common — one data root, one variable

Both products read their assets and write their packages into **one root outside the repository**, namespaced per
product so a brief and a reel can render at the same time:

| | |
|---|---|
| the default root | `~/.local/share/market-overview/` |
| the override | `MARKET_OVERVIEW_DATA` |
| what is in it | `resource/brief/` · `resource/reel/song/` · `output/brief/<date>/<lang>/` · `output/reel/<song>/<theme>/` |

⚠️ **Not the repository, and not `~/Documents`.** The root holds licensed assets and hundreds of megabytes of
rendered video, and a laptop may be syncing `~/Documents`. The one folder that *does* stay committed in the
repository is `store/` — the rebuild evidence — because a clone should be able to rebuild a day without
re-fetching it. See [Layout](#layout) and [ADR 0007](docs/adr/0007-the-data-lives-outside-the-repository.md).

### The brief — `mo`

| What | Where | Set by |
|---|---|---|
| the mark and the music bed | `$MARKET_OVERVIEW_DATA/resource/brief/` | dropping the files in — see the asset contract below |
| the YouTube client secret and token | `~/.config/market-overview/` | `MARKET_OVERVIEW_CREDENTIALS` |
| which `ffmpeg` to use | — | `MARKET_OVERVIEW_FFMPEG` |
| the mark's ink, for a raster | — | `MARKET_OVERVIEW_LOGO_INK=light` or `=dark` |
| the browser Remotion drives | — | `MARKET_OVERVIEW_BROWSER` |
| render parallelism | — | `MARKET_OVERVIEW_CONCURRENCY` |
| whether `mo publish` goes public | — | `MARKET_OVERVIEW_PRIVACY` — **defaults to `private`** |

### The Song Reel — `sv`

| What | Where | Set by |
|---|---|---|
| the songs, and their covers | `$MARKET_OVERVIEW_DATA/resource/reel/song/` | dropping the files in — see the asset contract below |
| the title, the themes, the wave form | `store/<song>/run.json` | asked once at the first run, then replayed |
| the data root | — | `MARKET_OVERVIEW_DATA` — the same variable as the brief |

⚠️ **The reel has no credentials and no privacy switch.** It builds; the upload is yours to do, by hand
([ADR 0004](src/song-video/docs/adr/0004-the-run-is-manual.md)).

## Running

⚠️ **One front door, and two tools behind it.** `./build` resolves the answers and passes them on as flags; `mo`
and `sv` remain the scriptable path, unchanged.

### Both — `./build`

⚠️ **`./build` is the front door** — one command over *both* products, which asks which one and then what it
needs, and hands the answers to the tool that owns them (ADR 0007's two products, `src/song-video/song_video/menu.py`):

```bash
./build                    # ask: project → language → that product's own questions
./build brief --lang bn en # …or answer with flags and see no questions at all
./build reel --song music --title "…" --theme vinyl --wave ribbon
```

⚠️ **It is a front end, never the only way.** Everything the menu asks, a flag answers, and every product's own CLI
is unchanged and still scriptable — `deploy/daily-brief.sh` runs `mo build --lang bn en` on a timer, and `sv build
--replay` is the reel's rebuild path. Publishing is deliberately **not** in the menu: it is the one step that cannot
be tidied up afterwards, so it stays a separate act.

The brief's own command, if you would rather be explicit:

```bash
uv run mo build --date YYYY-MM-DD
```

`mo` is the short name; `uv run market-overview build …` is the same CLI under its long name.

### The brief — `mo`

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

#### Rendering speed

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

#### Fetch, or re-render

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

#### Refusal cases

A run can legitimately refuse, and refusing is the correct outcome. ⚠️ **Every refusal exits non-zero and writes
nothing** — `1` for a refusal, `2` for a malformed `--date`.

| Case | Exit | Why it refuses |
|---|---|---|
| **Holiday**, weekend, or a mistyped date | 1 | *"asked for X but the newest session is Y"*. A holiday produces no error at all — only *yesterday's* numbers, which would publish under today's date. |
| **Mid-session** | 1 | *"session X has not finished printing"*. The india feed is ~15 min delayed, so "final" waits ten minutes past the close — 15:40 IST, under the earliest final write measured. Before that the numbers are still moving. |
| **Spine down** | 1 | The india scan is the spine. A brief with no market in it is not a degraded brief, it is a wrong one. |
| **Unusable mark** | 1 | `resource/brief/logo.svg` has text that is not outlined, so it depends on a font being installed. Rendering it would look right here and different elsewhere (0085_10). |
| **Unmixable bed** | 1 | `resource/brief/music.*` is not a container the tool's `ffmpeg` can read (0085_11). |
| **Incomplete package** | 1 | An artefact is missing. Assembly refuses to write metadata for a folder that would *look* complete (0085_13). |
| **Over a limit** | 0 | ⚠️ Reported, not refused. A title two characters long is truncated by YouTube and loses the move — bad, but not a reason to publish nothing. The run prints `warning: …` and carries on. |

Missing `logo.svg` or `music.*` is **not** a refusal: no mark and a silent brief are supported states. See Assets.

#### Verifying a delivery

`tests/test_frame_identity.py` proves the property on the committed snapshot by rendering ten mid-brief frames
twice and comparing them — cheap enough to run in the default suite. To check an actual delivered file:

```bash
DATA="${MARKET_OVERVIEW_DATA:-$HOME/.local/share/market-overview}"
cp "$DATA/output/brief/2026-10-12/bn/market-brief-2026-10-12-bn.mp4" /tmp/delivered.mp4
uv run market-overview build --date 2026-10-12      # re-renders from the snapshot
cmp /tmp/delivered.mp4 "$DATA/output/brief/2026-10-12/bn/market-brief-2026-10-12-bn.mp4"
```

⚠️ **Frame-identity is the requirement; byte-identity is the bonus.** A re-render that decodes to the same frames
is correct even if the container differs by a byte, because what an audience and a platform see are frames. If
`cmp` reports a difference, compare decoded frames before treating it as a fault:

```bash
D=node_modules/@remotion/compositor-darwin-arm64
DYLD_LIBRARY_PATH=$D $D/ffmpeg -i /tmp/delivered.mp4 -vsync 0 /tmp/a/%03d.png   # and the same for the new file
```

#### Before you publish

The run cannot judge these, and they are the reason a human runs it:

- **The Bengali reads as Bengali, not as translated English.** The label tables are written per language, but
  *native phrasing* is not something a test can assert. This applies to the labels, the metadata and the
  description — three surfaces.
- **The music is audible at the right level.** The bed is normalised to −14 LUFS, which is a measurement, not a
  judgement about how it sits under nothing.
- **The cold open and the close carry the mark once `resource/brief/logo.svg` is supplied.**
- **Numeral consistency** — the brief's Bengali numerals against the figures quoted from the sources.
- **The whole thing looks like a market brief**, which is the one check that has no proxy.

### The Song Reel — `sv`

⚠️ **Its own tool, its own environment, one command by hand.** The reel is not on a schedule
([ADR 0004](src/song-video/docs/adr/0004-the-run-is-manual.md)) and has no upload step — the package is what it
makes.

```bash
cd src/song-video
uv run sv build                                    # asks the four questions, records the answers
uv run sv build --song music --title "Dure Kothay" \
                --theme vinyl --theme neon --wave ribbon   # the same run, scriptable
uv run sv build --replay                           # re-runs the recorded answers; asks nothing
```

Or through the front door, from the repository root:
`./build reel --song music --title "…" --theme vinyl --wave ribbon`.

⚠️ **A recorded song replays rather than re-asks**, and a master whose `sha256` has changed is **refused** — the
recorded title, themes and wave form describe the take that was approved. To answer again, remove
`store/<song>/run.json`.

### On a schedule

⚠️ **The brief only.** It is built and published every weekday after the close — by a systemd timer on the host, or
by a container with its own scheduler. The commands and the install are
[below](#running-the-brief-on-a-server), and [`docs/adr/0006`](docs/adr/0006-a-server-runs-the-daily-brief.md) says
why that time, why Mon–Fri, and why the privacy default is what it is.

## Status — the Market Brief

**End to end, both editions, rebuildable.** A run fetches, computes the bundle, renders the video and the thumbnail
for each language, and assembles `output/brief/<date>/<lang>/`. Re-running a date re-renders from the snapshot without
touching the network, so a delivery can be reproduced and verified after the numbers have moved on. The design is
fully specified, and the specification is the source of truth for **what** to build:
`ideas/.scratch/market-brief/map.md` — 25 tickets, 24 decisions, none open. Build
order lives in `ideas/tasks/0085_market-brief_plan.md`. ⚠️ **Those two files are the only link to this repo** — it is
not a submodule, so nothing in `ideas/` points here (see `docs/adr/0001`).

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
up is recorded in `output/brief/<date>/.published-<lang>.json` — *beside* the package, never inside it, because a package
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
  video        …/output/brief/2026-10-12/bn/market-brief-2026-10-12-bn.mp4 (34.6 MB)
  thumbnail    …/output/brief/2026-10-12/bn/thumbnail-2026-10-12-bn.jpg (0.1 MB)
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
window; the server section below covers copying `token.json` to one. Both files live outside the repository and are never
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
DATA="${MARKET_OVERVIEW_DATA:-$HOME/.local/share/market-overview}"
cat "$DATA/output/brief/2026-10-12/.published-bn.json"   # video_id · url · privacy · bundle_hash · published_at
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

`docs/adr/0006` says why that time, why Mon–Fri, and why the privacy default is what it is; the server section below is
the install, including the one thing that is easy to get wrong: **the data root must persist**, because that is where
the record of what has already been uploaded lives.

## Running the brief on a server

Builds and publishes the Market Brief **every day after the close**, unattended. The decision and its costs are in
[`docs/adr/0006`](docs/adr/0006-a-server-runs-the-daily-brief.md); this file is the install.

```
market-brief.timer  →  market-brief.service  →  daily-brief.sh
                                                  ├── uv run --extra publish mo build   --lang bn en
                                                  └── uv run --extra publish mo publish --lang bn en
```

### Docker

```bash
cd deploy
mkdir -p ../credentials          # client-secret.json + token.json — see One-time setup below
docker compose run --rm brief    # one run, now
```

Or leave a scheduler running:

```bash
docker compose --profile scheduled up -d
docker compose logs -f scheduler
```

⚠️ **The `scheduler` service is optional.** If you already have a cron or a systemd timer, point it at
`docker compose run --rm brief` — that is the whole integration, and the host-timer path below needs no Docker
socket, no privileges and no second image.

⚠️ **The volumes in `compose.yaml` are not optional, and the reason is not size.** The **data root** — mounted at
`/data` — holds `output/brief/<date>/.published-<lang>.json`, the record that stops the next run re-uploading the same
brief. `store/` is what makes a re-render possible without re-fetching (ADR 0003). `var/` is where the run's log
lands, and without it a scheduled run is **completely silent**, because the wrapper redirects everything into that
file. The container is disposable; those three directories are not.

⚠️ **The data root is one mount, and `MARKET_OVERVIEW_DATA=/data` is what points the run at it** (ADR 0007). Leave
that variable out and the default — `~/.local/share/market-overview`, which inside the image is `/root/...` — writes
the day's package into the container's own writable layer, so the deliverable and its publish record are discarded
with the container and the next run posts the same day twice.

⚠️ **The timezone is pinned twice over, and both pins matter.** `compose.yaml` sets `TZ=Asia/Kolkata` on the
scheduler, because a cron expression is read in the container's local time and the container's default is UTC — a
run at 22:00 IST is one the session guard refuses every night, so the schedule would look healthy and publish
nothing. `Dockerfile` and `compose.yaml` carry a comment at each site; they are the pair that has to agree.

⚠️ **On the containerised schedule, `MARKET_OVERVIEW_PRIVACY` is read from `deploy/crontab`, not from the
environment.** A cron job is given a minimal environment and never sees the container's variables, so on that path
the crontab *is* the configuration. The one-shot path (`docker compose run --rm brief`) uses the environment
variable as you would expect. One source per path, deliberately — two that can disagree is how a schedule ends up
publishing publicly without anyone deciding to.

#### What is different inside a container

- **No fonts are installed, on purpose.** The face is vendored (`docs/adr/0005`), so a fontless image is a *test*
  of that rather than a risk to it: if any glyph had to come from the system, `useFonts` refuses the render instead
  of quietly falling back.
- **Chrome runs as root and that is fine.** Remotion passes `--no-sandbox` unconditionally
  (`@remotion/renderer/dist/open-browser.js`), so there is no flag to add and no capability to grant.
- **Remotion renders `--single-process` on Linux by default**, unless `enableMultiProcessOnLinux` is set. Rendering
  works either way; the flag is a *speed* knob:
  ```ts
  // remotion.config.ts — the place this project keeps render settings
  import {Config} from '@remotion/cli/config';
  Config.setChromiumMultiProcessOnLinux(true);
  ```
  ⚠️ **It is deliberately not set here.** It changes how Chromium is launched on Linux, I could not measure what it
  does to the frames, and a render setting nobody has measured is the kind of thing this project refuses
  elsewhere. Measure it, then set it.
- ⚠️ **`uv run` is not used inside the image.** `daily-brief.sh` calls `mo` directly when it is on `PATH`, because
  `uv run` re-syncs the environment — which in a container is slow *and* can strip the `publish` extra the image
  installed, so a schedule would work once and then start failing.

### What the host needs (bare metal)

| | Why |
|---|---|
| **Linux**, x86-64 or arm64 | The window-server objection in ADR 0004 was macOS's. Linux renders headless with Remotion's bundled Chromium. |
| **`uv`**, and **Python ≥ 3.14** via it | `pyproject.toml`. |
| **Node ≥ 24** | The render layer. |
| **Chrome or Chromium** | ⚠️ Remotion's bundled `chrome-headless-shell` cannot be relied on — it SIGABRTs on the operator's machine, which is why `render.py` searches for a real browser. On a server: `apt-get install -y google-chrome-stable`, or Chromium. |
| Chromium's shared libraries | `libnss3 libdbus-1-3 libatk1.0-0 libgbm-dev libasound2 libxrandr2 libxkbcommon-dev libxfixes3 libxcomposite1 libxdamage1 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2` |
| **No ffmpeg, no fonts, no GPU** | ffmpeg ships with Remotion; the typeface is vendored (ADR 0005); nothing needs a display. |

Roughly: 4+ cores, 8 GB RAM, 20 GB disk for `store/` and the data root. The render is CPU-bound and takes over an
hour for two editions.

### One-time setup

```bash
sudo useradd --create-home --shell /bin/bash market-brief
sudo -u market-brief git clone https://github.com/magmonium/market-overview.git /srv/market-overview
cd /srv/market-overview
sudo -u market-brief uv sync --extra publish
sudo -u market-brief npx remotion browser ensure     # optional; only if the bundled shell works
```

Assets and credentials, **never committed**:

```bash
DATA=/home/market-brief/.local/share/market-overview       # the data root, outside the checkout (ADR 0007)
sudo -u market-brief install -d -m 755 "$DATA/resource/brief" "$DATA/output/brief"
sudo -u market-brief install -m 644 /path/to/logo.svg  "$DATA/resource/brief/logo.svg"
sudo -u market-brief install -m 644 /path/to/music.mp3 "$DATA/resource/brief/music.mp3"
sudo -u market-brief install -d -m 700 /home/market-brief/.config/market-overview
sudo -u market-brief install -m 600 /path/to/client-secret.json \
    /home/market-brief/.config/market-overview/client-secret.json
```

⚠️ **Only if you have left `MARKET_OVERVIEW_DATA` unset.** Set it (`Environment=` in the unit, or compose's
interpolation) and the run reads that folder instead — but then it must also *be* a real folder on the host, because
nothing creates the data root for you.

⚠️ **Where `/path/to/client-secret.json` comes from is its own walkthrough** — enabling the YouTube Data API, the
consent screen, the **Desktop app** client type and the seven-day *Testing* trap — in the main
[the OAuth walkthrough](#creating-the-oauth-client-once). It is written for a laptop but it is the same client.

Then authorise **once**, on a machine with a browser — the server cannot open a consent window:

```bash
# on a laptop, with the same client-secret.json
uv run --extra publish mo publish --authorise
# copy the token it writes (~/.config/market-overview/token.json) to the same path on the server
```

⚠️ **Publish the OAuth consent screen before you rely on this.** A token from a client whose consent screen is
still in *Testing* **expires after seven days**, and nothing here can warn you in advance — `mo publish` starts
refusing with `invalid_grant`, a week after everything looked fine. This is the likeliest way this schedule fails.

### Install the timer (bare metal)

```bash
sudo cp deploy/market-brief.service deploy/market-brief.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now market-brief.timer
systemctl list-timers market-brief.timer      # confirm the next run
sudo systemctl start market-brief.service     # or fire it now, and watch:
journalctl -fu market-brief.service
```

Set `/srv/market-overview` in the `.service` file if you clone somewhere else.

### Reading the log

One file per day, `var/log/daily-<date>.log`, written by the wrapper. It answers the one question the exit code
cannot:

| In the log | Meaning | Action |
|---|---|---|
| `no new session — nothing to publish` | A holiday, a weekend, or the run fired before the close. **The guard working.** | None. This is expected several times a month. |
| `already published` | The same bundle was shipped already. | None. |
| `BUILD FAILED` | The spine was down, or an edition failed. | Look at the log — the reason is at the end. |
| `publish FAILED` / `refused` | Credentials, quota, or the consent screen. | `invalid_grant` almost always means the token expired: see above. |

⚠️ **Unattended means silent when it breaks.** Nothing here sends an alert. The cheapest thing that works is a
`OnFailure=` unit on `market-brief.service` — but wire it to something you will actually see, because the failure
mode of this schedule is a log nobody reads.

### Doing it by hand

The timer is a thin wrapper around two commands that work on their own:

```bash
uv run --extra publish mo build   --date 2026-10-12 --lang bn en   # re-renders from store/, no network
uv run --extra publish mo publish --date 2026-10-12 --lang bn en --privacy public
uv run --extra publish mo publish --date 2026-10-12 --lang bn --force   # re-upload after deleting the old video
```

⚠️ `mo publish` will **not** silently re-upload a rebuilt day: if the facts bundle changed, it refuses and says so,
because YouTube has no replace and two videos under one title is worse than none. Delete the old video, then pass
`--force`. The record of what went up is in `output/brief/<date>/.published-<lang>.json` under the data root.

## Layout

⚠️ **The repository holds code and evidence. The data lives outside it** — both products' assets and packages, in
one shared root, namespaced so neither can write the other's files. See
[ADR 0007](docs/adr/0007-the-data-lives-outside-the-repository.md).

```
store/      per-date snapshots: raw source responses + facts.json — **committed**, the rebuild evidence
src/        the Python package — `market_overview` — and, inside it, the **Song Reel's** own project:
            `src/song-video/` is a separate tool and product, a nested uv project of its own,
            never in the brief's image (see `.dockerignore`)
remotion/   the render layer (React/TS), and the vendored typeface in remotion/fonts/
deploy/     the systemd units and the wrapper that run it daily
docs/adr/   the thirteen decision records — the brief's seven and the reel's six
tests/      tests
```

The **data root** defaults to `~/.local/share/market-overview`; `MARKET_OVERVIEW_DATA` overrides it. A brief and a
reel may render at the same time, because each writes only its own namespace:

```
$MARKET_OVERVIEW_DATA/resource/brief/logo.*         the mark — read, never written
$MARKET_OVERVIEW_DATA/resource/brief/music.*        the bed — read, normalised into the run, never written
$MARKET_OVERVIEW_DATA/resource/reel/song/*          the reel's masters, beside the brief's assets
$MARKET_OVERVIEW_DATA/output/brief/<date>/<lang>/   the deliverable, four files and nothing else:
                                                    market-brief-<date>-<lang>.mp4 · metadata-<lang>.txt ·
                                                    metadata-<lang>.json · thumbnail-<date>-<lang>.jpg
$MARKET_OVERVIEW_DATA/output/reel/<song>/<theme>/   the reel's packages, beside the brief's
```

A run writes its **snapshot into the repository**, and that is the one part of the layout that is not data:

```
store/<date>/raw/*.json        the source responses, verbatim — written *before* parsing, so if the
                               parser is what broke, the evidence of what it was given is already on disk
store/<date>/facts.json        the computed bundle — the sole interface to the render layer, and the
                               only thing a re-render reads
```

⚠️ The snapshot lives **outside** `output/` — a different root now, not merely a sibling — so a package contains
exactly what a viewer should see and no plumbing, and the evidence a dispute would need is in version control. The
raw responses are the only evidence if a figure is ever disputed, which is the second reason they exist — the first
being that a video has to be rebuildable without re-fetching.

### Moving an older checkout's data

⚠️ **One-time, manual, and not done for you.** The assets and the packages used to be in the repository; they are a
`mv` away. Nothing is lost by skipping it — `store/` stayed put, so every date can be rebuilt — but the move saves
you rendering those days again. From the repository root:

```bash
DATA="${MARKET_OVERVIEW_DATA:-$HOME/.local/share/market-overview}"
mkdir -p "$DATA/resource/brief" "$DATA/resource/reel/song" "$DATA/output/brief" "$DATA/output/reel"

mv resource/logo.* resource/music.*   "$DATA/resource/brief/"
mv output/*                           "$DATA/output/brief/"
mv src/song-video/resource/song/*         "$DATA/resource/reel/song/"
mv src/song-video/output/*                "$DATA/output/reel/"
```

⚠️ There is deliberately **no fallback in the code**: a run reads the data root and nothing else, because "where
does output live?" having two answers is exactly the ambiguity the namespacing exists to remove. A glob that matches
nothing makes `mv` say so, which is the whole of the error handling this needs.

⚠️ **The two `output/*` and `resource/*` rules stay in `.gitignore` (and the reel's copy) for now, and they are
deliberately inert here.** They exist for this window only: a checkout that has *not* run the move above still has
the old folders on disk, and a bare `git add -A` there would commit licensed assets and unpublished videos. Delete
them once **every** checkout has migrated — this one, any other clone, and the deploy box.

## The typeface — Noto Sans Bengali, vendored

**These files are the brief's face, committed, because the alternative is a face that belongs to the machine.**

Until `docs/adr/0005`, the renderer named macOS's own *Kohinoor Bangla* and let the system font directory
resolve it. That made the rendered pixels a property of the host: the same `facts.json` rendered different
glyphs on Linux, where the name resolves to nothing and the stack quietly supplies something else. It broke two
guarantees at once — ADR 0003's "a re-render from the snapshot is a guaranteed match", and
`tests/test_frame_identity.py`.

### What is here

| File | What it is |
|---|---|
| `NotoSansBengali-<subset>-<weight>.woff2` | The face, **one file per subset per weight** — 3 subsets × 3 weights |
| `instance.py` | How the nine were produced. A record, not a pipeline step |
| `../fonts.json` | The manifest: family, every face, its weight and its `unicode-range` |
| `OFL.txt` | SIL Open Font License 1.1, Copyright 2022 The Noto Project Authors |

The manifest is read by **both** sides — `../fonts.ts` builds the renderer's `@font-face` rules from it and
`src/market_overview/copybudget.py` builds the measuring browser's from the same file — because the copy-budget
gate's whole premise is that it measures the face the brief is *set* in. `tests/test_fonts.py` pins the manifest
against the imports.

### The three subsets, and why they are three

Google ships the family split by script, and **the split is not decorative**:

- `bengali` carries Bengali and `₹` — and **no Latin at all**.
- `latin` carries the digits, the index slugs, `DII`, and the `−` (U+2212) the brief prints.
- `latin-ext` carries the European diacritics the copy does not currently use, kept so a missing glyph is never
  the reason a future string renders in a different face.

Dropping either of the first two leaves half of an edition in a fallback face, on some machines and not others.

### Why the weights are baked rather than interpolated

Google serves this family as one **variable** font with a `wght` axis of 100–900, and the `wght@400;600;700`
query returns the *same file* three times. Letting the browser instance that axis at render time was measured
**not to be stable**: the large figure — 200 px at weight 700 — moved by about a hundred pixels at ±2/255 along
its glyph edges between a cold and a warm browser cache. Nothing a viewer could see, and enough to break a
byte-for-byte rebuild.

`instance.py` bakes the three weights out of the variable file, so the browser is handed a static face and never
touches an axis. That also removes a browser capability from the determinism story, which is the point: a
Chromium on a Linux server has to produce the same glyphs as one on the operator's laptop, and a static face
leaves it nothing to decide.

### Regenerating

```bash
uv run --with fonttools --with brotli python remotion/fonts/instance.py
```

⚠️ Run `instance.py` **before** deleting the variable files it reads — it takes
`NotoSansBengali-<subset>.woff2` as input, and those are no longer committed now that the instances are.

To move version, change the URL in `instance.py`'s source fetch (see the file) and re-bake every subset; the
`unicode-range`s in `../fonts.json` come from Google's own CSS and must be refreshed from it at the same time.

## Tests

```bash
uv run pytest -q
```

No network, no ffmpeg, and the tests that would need a browser stub it — so the suite is hermetic and fast. The
exceptions are deliberate and skip themselves when they cannot mean anything.

`tests/test_frame_identity.py` is the one that renders for real: ten mid-brief frames, twice, decoded and compared
frame by frame. It is the guard on the product's central claim, so it runs by default rather than behind an
environment variable — and it is why the suite needs Chrome present to be at full strength.

## resource/brief/ — the brief's operator-supplied assets

⚠️ **This document used to live inside the folder it describes. It cannot any more**, because that folder is no
longer in the repository: the assets moved to the shared data root outside it (see
[ADR 0007](docs/adr/0007-the-data-lives-outside-the-repository.md)). The folder is
`$MARKET_OVERVIEW_DATA/resource/brief/` — default `~/.local/share/market-overview/resource/brief/`.

Drop licensed assets there. **The tool reads this folder and never fetches or generates these** — they are inputs,
not outputs. Nothing in it is committed, because committing a music bed publishes it.

### Expected files

| File | Purpose | Used by |
|---|---|---|
| `logo.svg` | the product mark | **both** the video and the thumbnail |
| `music.*` | the background bed | the video |

**`logo.svg` is preferred over PNG** — deliberate, not a preference. The mark is rendered at two very
different scales: a corner bug inside a 1920×1080 frame, and a thumbnail seen at roughly **210 px** in a
feed. A raster that looks right at one of those softens at the other; a vector holds both. If only a raster
exists, supply **≥1024 px with transparency**.

⚠️ **All text inside the SVG must be outlined to paths.** A mark depending on an embedded webfont renders
differently wherever that font is absent, which breaks the determinism every other element is held to. If
outlining is impossible, supply a **2× PNG** and treat that as the asset.

**`music.*` may be any container or codec `ffmpeg` reads.** The pipeline normalises rather than demanding a
format, so there is no right answer to guess at.

⚠️ **Where the toolchain comes from.** There is **no system `ffmpeg` prerequisite** — the tool uses the build
Remotion already ships in `node_modules/@remotion/compositor-*/ffmpeg`, which is present on any machine that can
render. To use a different one, set `MARKET_OVERVIEW_FFMPEG=/path/to/ffmpeg`.

⚠️ **Supply the longest master you have.** A track at least as long as the brief (currently ~175 s) is used as
supplied and simply faded out. Anything shorter has to be **looped**, and a loop point is audible in a way a fade
is not — the bundled build has no `acrossfade` filter, so the join cannot be smoothed. If you can only supply a
short bed, supply one that is written to loop.

### What the pipeline does to the bed

| Step | Value | Why |
|---|---|---|
| trim | to the brief's real length, from its own frame count | the music ends with the picture, not at the track's mercy |
| loudness | **−14 LUFS**, single-pass `loudnorm` | YouTube's own reference level — it turns loud down and never turns quiet up, so hitting it means the level shipped is the level heard |
| true peak | −1.5 dBTP | headroom for the AAC encode; clipping is unrecoverable |
| fade in | 1.5 s | |
| fade out | 4 s | the bed leaves before the music does — the long tail keeps the close card from sounding cut off |
| output | 48 kHz stereo, AAC 192 kbps | |

**One file, both editions.** The normalised bed is written once, above `bn/` and `en/`, and both editions mux from
it. So "both editions carry the same bed" is a fact about one file rather than a claim about two encodes matching.
It is removed when the run ends — it is scratch, and it lives in the folder a human opens to find the day's
deliverable.

To raise or lower the bed, change `TARGET_LUFS` in `src/market_overview/audio.py`.

### No variant is needed

The mark is drawn on a **chip whose fill the pipeline controls**, so it is never composited over arbitrary
card colours or the raw 3D scene. **One asset serves every card, both editions, the video and the still.**

The mark's **ink polarity is auto-detected** — there is nothing to declare up front:

| | |
|---|---|
| auto-detection | reads the SVG's dominant `fill` (or a gradient's `stop-color`) and takes its luminance |
| override | `MARKET_OVERVIEW_LOGO_INK=light` or `=dark` — needed only for a **raster**, whose ink cannot be read |

A light mark gets a dark chip and a dark mark gets a light chip, so contrast is computed rather than judged.
**Nothing needs declaring** unless you supply a PNG.

### Absent is a supported state

With no `logo.*` and no `music.*`, **the brief still renders** — no mark, no music. That is deliberate: the assets
are yours to drop in, and a missing one is a brief without branding, or a silent one, rather than a failed run.
Adding either later changes nothing else about the output.

The day the music lands, the run starts printing what it did — `music: music.wav → .bed.wav (-14 LUFS, 175s,
fade 1.5/4s)` — because a bed at the wrong level is the one defect that is invisible in a still and in a diff.

### Two products, two asset folders — and one mark between them

⚠️ **The reel's songs are not these.** The nested `src/song-video/` product keeps its masters in
`resource/reel/song/` **beside this folder** under the same shared data root. Two folders, two products, two
licence decisions — and one mark: the reel draws the `logo.*` from *this* folder, through the brief's own loader,
so there is one licensed file to replace rather than two that can disagree.

### Rules

- **Never modified in place.** The pipeline reads, normalises and writes derived audio into the run's temp
  directory. The supplied file is the master.
- **Language-neutral.** Both editions use the same bed and the same mark — no per-language variants. This is
  what keeps the bilingual pair honest at the branding layer.
- **Licence is the operator's.** The pipeline records no licence metadata and enforces nothing. The operator
  declares these assets are licensed for this product **including publication**.
- **Determinism.** The bed's start offset is a **constant**, and the trim, the level and the fades are all pure
  functions of (master, run length) — no clock and no randomness — so a re-render lands the music identically.
  Measured, not assumed: two normalisations of the same master are compared byte for byte in `tests/test_audio.py`.

## resource/reel/ — the reel's own inputs

⚠️ **This document used to live inside the folder it describes. It cannot any more**, because that folder is no
longer in the repository: the songs moved to the shared data root outside it (see
[ADR 0007](docs/adr/0007-the-data-lives-outside-the-repository.md)). The folder is
`$MARKET_OVERVIEW_DATA/resource/reel/` — default `~/.local/share/market-overview/resource/reel/`.

Only the **songs** live here. ⚠️ The **mark does not**: the logo is the brief's own operator asset, at
`resource/brief/logo.*` under the same data root — read through the brief's own loader, so one licensed file
serves both products and there is one place to change it.

Nothing here is committed — committing a master song publishes it.

### Expected files

| File | Purpose | Required |
|---|---|---|
| `song/<name>.<audio>` | **the master** — the song the reel is built from | yes, at least one |
| `song/<name>.<image>` | the cover, sharing the master's basename | no |

```
~/.local/share/market-overview/resource/          ← MARKET_OVERVIEW_DATA
├── brief/                                        ← the brief's assets: logo.*, music.*
└── reel/
    └── song/
        ├── dure-kothay.mp3      ← master
        └── dure-kothay.jpg      ← optional cover
```

`<name>` **is** the song's identity: it is the menu entry, the `store/<name>/` folder, and the `<song>`
segment of every output filename.

⚠️ **The name is an id, not a title.** Nothing displays it. The title shown on the video, the disc and the
thumbnail is **typed at run time**, so `dure-kothay_128kbps_final_mix.mp3` never becomes a caption.

### Formats

**Any audio format the toolchain reads.** The pipeline never re-encodes the master, and the toolchain is the
one Remotion already ships, so there is no system `ffmpeg` prerequisite. An extension list exists only so
the menu can tell a song from a stray file.

⚠️ **A file the toolchain cannot decode fails the run loudly** when that song is chosen. It never renders a
silent video.

### The master is never touched

⚠️ **No normalisation, no trimming, no fades, no looping.** The brief normalises its music bed to −14 LUFS
and trims it to the video's length, because a bed is furniture. **A song is not furniture**: its level, its
opening, its ending and its length are the artist's, and the reel is exactly as long as the song is.

The pipeline reads the master, copies it into the renderer's staging folder for the duration of the run, and
deletes that copy afterwards. **This folder is read and never written.**

### Absent is a supported state — with one exception

- **No cover** — the disc gets a plain label in the theme's palette, and the thumbnail is composed from the
  mark and the title alone. A designed state, not a degraded one.
- ⚠️ **A cover whose name belongs to no master** — `man-poreche-preme.png` in a folder holding only
  `beshorom.mp3` — is **not** a cover, and it is never guessed at as one: the pairing is by **name**, so with two
  masters here a loose image belongs to neither. The run **names the file** in its ledger instead of passing it
  over in silence. Either add the master it belongs to, or rename it to the master's basename
  (`beshorom.png`), which is the whole of the rule.
- **No songs at all** — ⚠️ **the run refuses**, with a reason and a non-zero exit. Unlike a missing bed, an
  absent song means there is no product to make.

### Licence is the operator's

The pipeline records no licence metadata and enforces nothing. By placing a file here the operator declares
it is **licensed for this product including publication** — for both the song and the cover image.

### Rules

- **Never modified in place.** The supplied file is the master; staged files are scratch and are removed when
  the run ends.
- **Discoverable, not declared.** No manifest, no index and no sidecar JSON — adding a song is dropping a
  file in.
- **One song per run.** A run makes one song into one or more reels; it is not a batch tool.

## song-video — the Song Reel

One supplied song in → **a full-length 16:9 music video** and **its own thumbnail** out, in one or more of a
predefined set of visual themes, driven entirely by the song's own **amplitude envelope**.

**The tool is `song-video`. The product is the Song Reel.** Output filenames carry the product's name:
`song-reel-<song>-<theme>.mp4`.

### Where this lives, and what it reuses

⚠️ **A nested sub-project of `market-overview`, not a sibling repository** — reversed from the original
design by decision, so both products live in one repository. This folder is its **own uv project** with its
own `store/` and `public/`; its **assets and packages moved out of the repository** to the shared data root
(`~/.local/share/market-overview`, or `MARKET_OVERVIEW_DATA`), under a `reel/` namespace beside the brief's
`brief/`. See [ADR 0007](docs/adr/0007-the-data-lives-outside-the-repository.md).

It **imports the brief's resources rather than copying them**:

| Reused | From |
|---|---|
| the operator's mark (the same `logo.*`) | `market_overview.logo`, reading `resource/brief/` under the shared data root |
| the bundled `ffmpeg`/`ffprobe` discovery and its loader-path trap | `market_overview.audio` |
| the vendored fonts and the seeded PRNG | `market-overview/remotion/` |
| Remotion itself | the **parent's `node_modules`** — no second runtime is installed |

The cost is explicit: `song-video` depends on the `market-overview` package, so it inherits its dependency
tree. The alternative was re-implementing ~250 lines of tested mark handling.

### Status

**The pipeline is built end to end.** `sv build` discovers the song, takes or asks the four answers, guards the
master's digest, records the run, prints the ledger — and then renders **every thumbnail before any video** and
assembles one self-contained package per theme under `output/reel/<song>/<theme>/`. A failed theme fails the run, and
nothing lands at a package path until it is whole.

⚠️ **A full-length reel is ~20 minutes** (7201 frames for a 4-minute song, at Remotion's default concurrency), which
is exactly why the thumbnails come first: a theme that reads badly costs seconds to find and an hour to discover
otherwise.

The specification is `ideas/.scratch/song-video/map.md` (11 tickets, 11 decisions, 0 open), with build order in
`ideas/tasks/0087_song-video_plan.md`.

### Vocabulary and decisions

- the glossary, below — run, song, master, staging, title, cover, recorded run, theme, motif, wave form,
  catalogue, envelope, ledger, quality gate, package, thumbnail.
- the runbook, below — **every step and every command**: setup, both test suites, the menu, the refusals, how to
  look at a theme without spending twenty minutes, how to read back what was made, and the traps.
- `src/song-video/docs/adr/` — the six load-bearing decisions: **0001** where the tool lives (and the reversal it records) ·
  **0002** a Python CLI conducts the run · **0003** the recorded run is the interface · **0004** the run is manual ·
  **0005** the typeface is vendored · **0006** the envelope is the only clock.
- ⚠️ `beat` and `variant` are **not** in the vocabulary: there is no beat grid (ADR 0006), and N videos are
  N *themes*.

### Where the song goes

Drop the master into **`resource/reel/song/`** — under the shared data root, outside this project. ⚠️ **The folder
*is* the interface** — no manifest, no index and no sidecar JSON, so adding a song is dropping a file in:

```
~/.local/share/market-overview/        ← MARKET_OVERVIEW_DATA overrides it
├── resource/
│   ├── brief/                         ← the brief's: logo.*, music.*
│   └── reel/song/                     ← here
│       ├── dure-kothay.mp3            ← the master. At least one, or the run refuses
│       └── dure-kothay.jpg            ← the optional cover, sharing the master's basename
└── output/
    ├── brief/<date>/<lang>/           ← the brief's packages
    └── reel/<song>/<theme>/           ← the reel's packages
```

⚠️ **The filename stem is the song's *id*, not its title.** The id is the menu entry, the `store/<id>/` folder and
the `<song>` segment of every output filename — nothing displays it. The title is a separate thing, **typed at run
time** (or passed with `--title`), which is why `dure-kothay_128kbps_final_mix.mp3` never becomes a title:

```bash
cd src/song-video
cp ~/Music/dure-kothay.mp3 "${MARKET_OVERVIEW_DATA:-$HOME/.local/share/market-overview}/resource/reel/song/"
uv run sv build                               # it appears in the menu as `dure-kothay`
```

⚠️ **Any audio format the bundled toolchain reads** (when two encodes of one song are present, the lossless one is
chosen as the master), and **no cover is a designed state** rather than a hole — the disc gets a plain label and the
thumbnail is composed from the mark, the title and the **caption**: the word *music* and the piece's length,
`সংগীত · ৩:০২`, written in the script the title is typed in.

⚠️ **The mark is not here.** The logo is the brief's own operator asset at `resource/brief/logo.*` under the same
shared data root, read through the brief's loader, so one licensed file serves both products.

⚠️ **This folder is read, never written, and never committed** — committing a master publishes it, and by dropping a
file in you declare it licensed for this product including publication. The full contract, including the
no-normalisation rule and what happens when the folder is empty, is the reel's asset contract, below.

### Install and run

⚠️ **Both are at the top of this file now** — the reel's requirements are the [common ones](#install) plus its own
`uv sync`, and its commands are under [Running](#running), in *The Song Reel*. What is particular to this tool:

- **No scheduler and no upload step.** One command, by hand ([ADR 0004](docs/adr/0004-the-run-is-manual.md)) — the
  package is what it makes.
- **A recorded song replays rather than re-asks**, and a master whose `sha256` has changed is **refused**: the
  recorded title, themes and wave form describe the take that was approved. To answer again, remove
  `store/<song>/run.json`.

## Runbook — the Song Reel, step by step

Every command in this project, in the order it is used, with what a good result looks like. ⚠️ **Everything runs
from `src/song-video/`** — never from the repository above it, for the reason in [Traps](#11-traps-each-one-cost-something).

```bash
cd /Users/dibyendudas/Documents/magmonium/market-overview/src/song-video
```

### The whole pipeline at a glance

| | |
|---|---|
| **in** | `resource/reel/song/<name>.<audio>` + an optional `<name>.<image>` cover |
| **asked once** | song · title · themes (many) · wave form (one) — recorded in `store/<song>/run.json` |
| **guarded** | the master's `sha256`; a changed master refuses |
| **rendered** | every **thumbnail** first, then every **reel** |
| **out** | `output/reel/<song>/<theme>/` — `song-reel-<song>-<theme>.mp4` + `thumbnail-<song>-<theme>.jpg` |

### 1. Setup

```bash
uv sync                                        # the reel's own venv, and the brief as an editable path dep

DATA="${MARKET_OVERVIEW_DATA:-$HOME/.local/share/market-overview}"   # the shared data root
cp "$DATA/resource/brief/music.mp3" "$DATA/resource/reel/song/music.mp3"   # a master; drop a cover beside it too
ls "$DATA/resource/reel/song/"                 # music.mp3 — the name here is the song *id* everywhere else
```

⚠️ `resource/reel/song/` is **outside the repository now**, so it is not gitignored — it is simply not there to
commit (ADR 0007). The licence is still the operator's: committing a master would publish it, which is one reason the
folder left.

### 2. The Python suite

```bash
uv run pytest -q                    # 46 passed
uv run pytest tests/test_cli.py -q  # one module
uv run pytest tests/test_render.py -q -k command   # one idea
```

⚠️ **Where the tests never go:** no test in the suite reaches Remotion. The render fakes are installed in
`setUp`, so a test added later cannot quietly start an hour of frames. Anything a *fake* cannot check — that the
composition ids exist, that the audio is in the file — is checked by running the thing (§7, §8).

### 3. The JS layer: tests, then the typecheck

```bash
npm test              # node --test remotion/*.test.ts   → 18 tests
npm run typecheck     # tsc --noEmit                     → exit 0
npm run studio        # Remotion studio, for designing a theme by hand
```

⚠️ **Both, always.** `node --test` cannot load a `.tsx` file at all — JSX is not erasable TypeScript — so the
geometry lives in `.ts` (tested) and the drawings in `.tsx` (compiled, and *looked at*). The typecheck catches a
class of bug no test can: it caught a missing import on the evening when 14 tests were green.

### 4. What the menu will offer

```bash
uv run python -c "from song_video import catalogue; print([e.id for e in catalogue.themes()], catalogue.forms())"
# ['vinyl', 'neon', 'parchment', 'aurora'] ('bars', 'ribbon', 'ring', 'bloom')
```

That list is **read out of the renderer** (`remotion/themes.ts`, through node's type stripping), never mirrored —
so a theme the composition cannot draw cannot appear in the menu.

### 5. Build a reel

⚠️ **Or type `./build` from the repository root** and answer the menu — it asks which product first, then the same
questions below (plus the brief's, if that is what you picked), and hands the answers to `sv` as flags. Everything
here is the explicit form and stays the scriptable one: the menu never does anything a flag cannot, and nothing is
reachable *only* through it.

```bash
./build reel                                       # project → song → title → themes → wave form
./build reel --song music --title "Dure Kothay" --theme vinyl --wave ribbon   # no questions at all
```

```bash
uv run sv build                                     # asks the four questions, records the answers
uv run sv build --song music --title "Dure Kothay" \
                --theme vinyl --theme neon --wave ribbon    # the same run, scriptable
uv run sv build --song music --title "Dure Kothay" --lang bn    # the still's caption script, when the title
                                                                # cannot say: an instrumental, or a transliteration
uv run sv build --song music --cover "poster.png"               # answer the image question without a menu, and
                                                                # override the master's-basename rule
uv run sv build --song music --title "Dure Kothay" --artist "…" # the artist, for the upload text only —
                                                                # never drawn, never read out of a file
uv run sv build --replay                            # re-runs the recorded answers; asks nothing
```

What happens, in order — and the order is the design:

1. **discover** the song from `resource/reel/song/`
2. **resolve** the answers: flags, else the menu, else the record (a recorded song replays, and never re-asks) — and
   **which image rides it**: `--cover`, else the master's basename, else the one loose image, else a question
3. **probe** the master with the brief's `ffprobe` — the piece's length *is* the song's
4. **guard** the digest; a changed master refuses before anything is planned
5. **record** the run to `store/<song>/run.json`
6. **print the ledger** — the title, the caption's language and duration, the master's digest, **what the master
   sounds like**, the toolchain, the length → frames, the **cover** (or that none paired), and the paths that appear
7. **stage** the master (and cover) into `public/`
8. **render every thumbnail** (seconds each — the quality gate; Ctrl-C here is safe)
9. **render every reel** (~20 minutes each for a 4-minute song)
10. **print what was made** and exit `0`

#### Sound, measured — and never adjusted

⚠️ **The music is the product, so the run measures it.** A master is whatever was supplied, and this pipeline does not
improve it: the level, the dynamics and the length are the artist's (issue 09), and the brief's `loudnorm` is absent
from the reel on purpose. What the run *does* own is the **loss**, and what nobody can see by looking is the
**ceiling**. Both are one line and a few sentences, printed before a frame is spent:

```
  audio    mp3 · 48 kHz · stereo · 172 kbps · -16.3 LUFS · +0.0 dBTP · range 7.3 LU
  ⚠️ the master is mp3 at 172 kbps — lossy, so the delivery can be no clearer than this. A lossless master
     (WAV or FLAC) is the one change that raises the ceiling
  ⚠️ the master already peaks at +0.01 dBTP, above the -1 dBTP delivery ceiling — a lossy encode overshoots
     further, so it distorts where the uploader re-encodes it. Lowering it is a level change, the level is the
     artist's (issue 09), and this run only says so
  ⚠️ the master sits at -16.3 LUFS, 2.3 dB below the -14 LUFS a feed plays at — YouTube turns loud material
     *down* to it and leaves quiet material alone, so this song will play quieter than the songs beside it
```

| | |
|---|---|
| **crystal clear** | the ceiling is the master. A `wav`/`flac` in `resource/reel/song/` is the single change that raises it — ⚠️ and if both are there, the lossless one is already the master (the suffix order in `library.py`) |
| **world class** | 48 kHz stereo in, 48 kHz stereo out, 320k AAC, and the rate is never resampled down |
| **attractive** | the level, honestly reported: a master 2.3 dB under the reference plays 2.3 dB under its neighbours in a feed, because YouTube turns loud material *down* and never turns quiet material *up* |

⚠️ **The delivery is checked, not assumed** — and it is checked *before* the file reaches the package, so a reel that
lost the song cannot replace the previous good one:

| The guard | Because |
|---|---|
| the delivered file has an audio stream at all | *"a song that is analysed but never heard"* is the one defect every still in this project looks perfectly good through |
| its rate is not below the master's, and its channels match | a re-encode may cost bits; it may not cost a channel or a rate |
| ⚠️ **only when the master is lossy**, its bitrate is not below the master's | re-encoding a 172 kbps mp3 to 128k is a second generation of the same artefacts — the opposite of a refinement |

⚠️ A **quiet, lossy or clipping master is not a refusal.** It is a supported state and it is printed as what it is: the
fix belongs to the master, and pretending otherwise would mean the pipeline mastering the artist's work (issue 09).

#### What the package carries — including the words

⚠️ **Every package is four files, and two of them are text.** Issue 07's contract is that a folder can be handed to its
own uploader, and an uploader asks for a title and a description as much as for a video and a still:

```
output/reel/<song>/<theme>/
├── song-reel-<song>-<theme>.mp4
├── thumbnail-<song>-<theme>.jpg
├── title-<song>-<theme>.txt              ← what a search result shows
└── description-<song>-<theme>.txt        ← the paragraph under it, in the song's own script
```

The ledger prints the title before it prints anything expensive, because it is the one line of that screen which is
**published** — and a title longer than the 100 characters a search result shows is a **refusal**, not a snippet that
ends mid-word:

```
  title    বেশরম লতার মতো
  upload   বেশরম লতার মতো | ৩:০২ | বাংলা গান
```

```bash
$ cat "output/reel/…/vinyl/title-….txt"
বেশরম লতার মতো | ৩:০২ | বাংলা গান

$ cat "output/reel/…/vinyl/description-….txt"
বেশরম লতার মতো
দৈর্ঘ্য ৩:০২ (৩ মিনিট ২ সেকেন্ড) · সম্পূর্ণ গান, কোনও কাটছাঁট নেই

গানটি অপরিবর্তিত — মূল রেকর্ডিং যেমন আছে তেমনই, শুধু একটি স্থির চিত্রের সঙ্গে।
Song Reel · বাংলা গান (Bangla song)
#বাংলাগান #BanglaSong #বাংলাসংগীত #BanglaMusic
```

| | |
|---|---|
| **the song's name leads** | it is the query. Then the artist *if* one was given, then the length, then the genre — and the length and genre stay even when the title is long |
| **both scripts** | `বাংলা গান` and `Bangla song`, because a Bengali search and a Latin one are two different queries — that is coverage, not stuffing |
| **the length, twice** | `৩:০২` exactly as the video, the still and the ledger write it, and `৩ মিনিট ২ সেকেন্ড` because that is how somebody types it into a search box |
| **nothing invented** | the one sentence of editorial copy is true of every reel by construction — the song is the master, complete and untouched (issue 09). No mood, no story, no "official audio": none of that was supplied |
| **`--artist` or nothing** | an artist is the only fact the folder cannot supply (a filename is not metadata, a cover is a picture), so `--artist` is the only way in — and its absence **drops the line** rather than leaving a placeholder to edit |

⚠️ The copy is **authored**, like a theme's palette, and lives in `seo.py` — Python's, not the render layer's, because
it is never drawn: it is written to a file and pasted into a form, which is also what makes it testable (ADR 0002) and
what makes a rebuild write the same two files (ADR 0003).

### 6. Refusals are part of the interface

| Command | What it says, and why that is right |
|---|---|
| `uv run sv build` (no songs) | `no songs in …/resource/reel/song — drop a master in and run again` |
| `uv run sv build --song nope …` | `'nope' is not in …/resource/reel/song — the songs there are music` (an ambiguous folder names the songs too) |
| `uv run sv build --theme sparkle` | `unknown theme "sparkle" — the catalogue is vinyl, neon, parchment, aurora` |
| `uv run sv build --wave zigzag` | `unknown wave form "zigzag" — the catalogue is bars, ribbon, ring, bloom` |
| `uv run sv build --lang fr` | `unknown language "fr" — the languages are bn, en` (the caption's script is refused for the same reason a theme is) |
| `uv run sv build --cover nope.png` | `no image "nope.png" in …/resource/reel/song — the images there are poster.jpg` (the list *is* the fix) |
| `uv run sv build --cover some/path.png` | `--cover takes the image's name, not a path` (a record holds a name in the folder, not somebody's desktop) |
| several images, no terminal | `3 images in …/resource/reel/song pair with no master, so choosing one is a decision rather than a default — say which one rides music with --cover (…)` |
| a replay whose image has gone | `music was built with the cover "poster.png", and no image of that name is in …` |
| a swapped image under the same name | `poster.png is not the image music was recorded with … stops rather than drawing different art under the same name` |
| `uv run sv build --theme neon` (recorded `vinyl`) | `… the run replays what was approved, so remove store/music/run.json to answer again` |
| `uv run sv build --replay` (never recorded) | `music has no record at store/music/run.json — --replay rebuilds a recorded run` |
| `uv run sv build` (no tty, no flags) | one refusal naming **every** missing flag, before the first question |
| a reel whose audio is missing or worse than the master | `remotion render (vinyl): the delivery lost the song — … so the run stops rather than shipping it` (⚠️ checked **before** the package file is replaced, so the previous good reel survives) |
| a title too long for a search result | `the upload title is 118 characters, over the 100 a search result shows — shorten the title itself, rather than dropping the length and the genre: …` (⚠️ and it costs seconds: nothing is rendered and nothing is recorded) |
| a swapped master | `music.mp3 has changed since music was recorded … stops rather than re-cutting it under that name` |

All of them exit `1`, write nothing, and print the reason on **stderr** — stdout stays the ledger, so
`uv run sv build > ledger.txt` captures the plan and not the conversation.

⚠️ **An image no master answers to is no longer a warning — it is the cover, or a question.** The rule is *use the
image, and ask when there is a choice*:

| in `resource/reel/song/` | what happens |
|---|---|
| one image sharing the master's basename | **used**, silently: the folder's own answer |
| exactly one image that matches no master | **used**, and named in the ledger — one candidate is not a choice |
| several images that match no master | **asked**, numbered, with `— none: the theme's motif` as the last answer |
| no image at all | the theme's motif — a supported state (issue 08) |

```
  cover    মন পড়েছে প্রেমে — Live Concert.png  2009269 bytes  sha256 …dd460a78abfe
  cover — pick one (1-4):
   1  a.png
   2  b.png
   3  c.png
   4  — none: the theme's motif
```

⚠️ **A question nobody can be asked is a refusal, never a coin toss.** With several candidates and no terminal the
run stops, naming the images and `--cover` — the same discipline as a folder holding several songs.

| | |
|---|---|
| **name one** | `--cover "poster.png"` — the answer for a script, and the way to override the folder's own pairing |
| **add the master** | if the image belongs to a song that is not in the folder yet, drop that master in under this basename |
| **rename the image** | to the master's basename, if the image *is* this song's cover and only the name was wrong |

⚠️ What the old rule was protecting is kept: nothing is guessed at **silently**. Whichever image is used, the ledger
prints it and the record pins it — with its digest, like the master — so a rebuild replays the same artwork without
asking, and a replay whose image has **gone** or been **replaced** is refused. To change the artwork of a run that is
already recorded, answer again:

```bash
rm store/music/run.json      # ⚠️ the record is committed; removing it is a reviewable act
uv run sv build --title "Dure Kothay" --cover "poster.png" --theme vinyl --wave ribbon
```

**To answer again** (deliberately, because the record is the take somebody approved):

```bash
rm store/music/run.json      # ⚠️ the record is committed; removing it is a reviewable act
uv run sv build
```

### 7. Look at a theme without spending twenty minutes

The pipeline already does this — the thumbnails land before the first reel. For an ad-hoc frame, write the props
by hand (the flat object `remotion/props.ts` describes) and render one:

⚠️ **What to look at, because *attractive* and *eye-soothing* are not one setting.** Four things decide it, and only the
last two belong to a theme:

| | |
|---|---|
| **the record turns — in every theme** | twelve seconds a revolution — `motif.ts`'s `SECONDS_PER_TURN`. A *rate*, so a longer song simply gets more revolutions; six turns across a whole piece is ~11° a second, which reads as a disc standing still. ⚠️ The `disc`/`notes` split decides whether glyphs also drift in the field, **not** whether the artwork moves |
| **the progress is a dial** | directly above the landscape and the same width as it: the theme's `ink` as a hairline track, its authored `progress` red as a thin **needle** travelling it. Same `travelled` as the playhead, so the needle lands on the playhead's own x — one instrument, not two progress marks |
| **the motion settles** | the pulse and the light average over `theme.smooth` frames, so a transient becomes a swell rather than a frame-rate strobe. `aurora`/`parchment` settle most, `neon` least |
| **the light is a warmth, not a lamp** | three pools at 42% of full strength, plus one of the theme's own `glow`, then a vignette reaching in to 46% so the corners settle back into the theme's field |
| **the landscape stays readable ahead** | the unplayed half is *quiet*, never erased — the shape in front of the playhead is the design's own claim, and a shape nobody can see is not a narrative |
| **nothing is pure** | the played half is graded rather than switched, the halo is a glow rather than an outline, and the title is the only high-contrast thing in the frame — which is exactly where contrast belongs |

```bash
cat > /tmp/props.json <<'JSON'
{"title": "Dure Kothay", "song": "music.mp3", "theme": "vinyl", "cover": null, "frames": 7201, "mark": null,
 "lang": "en", "duration": "4:00", "seed": ""}
JSON

# the thumbnail's own composition: 1280×720, one frame, no entrance to be caught in
npx remotion still remotion/index.ts SongReelThumbnail /tmp/thumb.png \
  --props=/tmp/props.json --frame=0 --image-format=jpeg --jpeg-quality=88 --overwrite \
  --browser-executable="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# a frame of the reel — you pick the frame; it is a 7201-frame piece
npx remotion still remotion/index.ts SongReel /tmp/frame.png \
  --props=/tmp/props.json --frame=1044 --image-format=png --overwrite \
  --browser-executable="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

Good looks like `Bundling 100%` → `Getting composition` → `Composition SongReel` → `Rendered 1/1` → `+ /tmp/…png`.
⚠️ `song` must name a file **inside `public/`**: stage it the way a run does, by copying the master there.
⚠️ `mark: null` and `cover: null` are supported states, not holes — that is what the motifs are designed for.
⚠️ `seed` is the master's **recorded digest**, and it is what makes two songs two colours: it chooses the piece's
**accent** — which of the theme's four authored colours lights the field and draws the title's rule — and the paths
that light drifts along. `""` is supported and lands on the theme's first accent; a run always passes the real one, so
one song rebuilds byte-identical and two songs do not.

### 8. Spot-check a reel in a minute, instead of twenty

```bash
npx remotion render remotion/index.ts SongReel /tmp/spot.mp4 \
  --props=/tmp/props.json --frames=0-29 \
  --codec=h264 --pixel-format=yuv420p --audio-bitrate=320k --overwrite \
  --browser-executable="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

⚠️ **`--frames` is a spot check, never a delivery.** The product's own run renders the whole piece; a partial render
written to a package path would be a file that looks finished, which is the one thing this pipeline refuses to
produce. Point it at `/tmp`, and note that the other flags are exactly the ones `render.py` passes — so what you
check is what would ship.

### 9. Read back what was made

```bash
uv run python -c "
from market_overview import audio
from song_video import paths

where = paths.repo_root()                                  # where node_modules, and the toolchain, live
ffmpeg = audio.binary(where)
out = paths.output_dir() / 'music' / 'vinyl' / 'song-reel-music-vinyl.mp4'

print('duration:', audio.duration(out, ffmpeg=ffmpeg), 's')
print(audio.run(audio.probe_binary(ffmpeg), ['-v', 'error', '-show_entries',
      'stream=codec_type,codec_name,sample_rate,channels,bit_rate', '-of', 'json', str(out)]))
"
```

Expected: an `h264` stream **and** an `aac` one at 48000 Hz, 2 channels, ~192000 bps — the pinned bitrate. That is
how "the song is really in the file" is checked rather than assumed: the reel is analysed and drawn from the song,
so every still in this project looks perfect if the audio was never attached.

⚠️ **Never call the bundled `ffprobe` directly.** A bare `subprocess.run([...])` on it dies with `SIGABRT`
(signal 6); the loader path `market_overview.audio` applies is the whole reason that module exists.

### 10. Where everything lands

```
$MARKET_OVERVIEW_DATA/resource/reel/song/<name>.<audio>   the master (+ an optional <name>.<image>)   read-only, outside the repo
store/<song>/run.json          the recorded run — the rebuild contract      committed
public/<name>.<audio>          staging: the copy a composition can fetch    scratch,  gitignored
$MARKET_OVERVIEW_DATA/output/reel/<song>/<theme>/         the package: the reel and its thumbnail      outside the repo
```

```bash
find "${MARKET_OVERVIEW_DATA:-$HOME/.local/share/market-overview}/output/reel" -type f | sort   # the packages
find output -name '.*' | sort     # ⚠️ must be empty after a run: no scratch and no props left behind
ls store/*/run.json               # the records — these are the ones to commit
```

### 11. Traps (each one cost something)

| Symptom | Cause, and what to do |
|---|---|
| `Could not find composition with ID SongReelThumbnail. Available compositions: MarketBrief, Thumbnail, IndexCard` | The render ran from the **repository** — and both projects have a `remotion/index.ts`. Run from `src/song-video/`: `render.where()` is the reel's own tree, and a test asserts the ids it invokes are registered there |
| `SIGABRT` (signal 6) from `ffprobe` | A bare call needs the loader path. Use `market_overview.audio.run` / `.duration`, never the binary directly |
| `Protocol error (Target.createTarget): Target closed` at `Getting composition` | Remotion's browser died. `--browser-executable` (a full Chrome) is required on this machine, and a sporadic death still happens roughly once in seven renders — the run fails cleanly, and thumbnails-first makes it cheap |
| `remotion render (…) failed (-1)` | The process was killed by a signal. `nohup … &` from a shell that later closes gets `SIGHUP` — not a render failure |
| The ledger appears *after* the first render lines | stdout is block-buffered on a pipe; the conductor flushes before rendering. If it regresses, this is what it looks like |
| pytest collects the brief's tests as well | pytest resolves `rootdir` upward; the reel owns its own `testpaths` |
| Reel media got committed | The parent's `.gitignore` does not reach into this folder — a pattern containing a slash is anchored to its own directory, so the reel owns its own ignore file |
| `VIRTUAL_ENV … does not match the project environment path .venv` | Harmless: an outer `market-overview` venv is active while `uv` uses the reel's own. Add `--active` only if you want the outer one |
| Re-running repeats themes that already finished | There is **no resume and no retry** (ADR 0004). A `--only <theme>` is the obvious next addition |

### 12. How it was built — the order, and the loop

Every row was a cycle: **the test first** (red), then the implementation, then green — with
`uv run pytest -q`, `npm test` and `npm run typecheck` run at each step.

| # | Layer | Step | What proved it |
|---|---|---|---|
| 1 | Python | the skeleton, and its first refusal (no song → refuse, build nothing) | `uv run pytest tests/test_cli.py -q` |
| 2 | Python | the pair: a master, and the cover sharing its basename | `uv run pytest tests/test_library.py -q` |
| 3 | Python | the master's length, the one ceiling rule, the digest | `uv run pytest tests/test_master.py -q` |
| 4 | Python | the record, and the guard it exists for | `uv run pytest tests/test_record.py tests/test_guard.py -q` |
| 5 | Python | the plan: N themes → N jobs, one shared wave form | `uv run pytest tests/test_plan.py -q` |
| 6 | Python | staging: byte-identical, and the master untouched | `uv run pytest tests/test_stage.py -q` |
| 7 | JS | the clock and the landscape (envelope, waves) | `npm test` |
| 8 | JS | the catalogue, its refusal, and the themes' curves | `npm test` |
| 9 | JS | the motifs: the disc's angle, the notes' flow | `npm test` |
| 10 | Python | the catalogue, **read from the renderer** rather than mirrored | `uv run pytest tests/test_catalogue.py -q` |
| 11 | JS | the reel, and the still's own composition | `npm run typecheck` + looking at a frame |
| 12 | Python | the render step: the command, the props, the atomic move | `uv run pytest tests/test_render.py -q` |
| 13 | Python | the conductor: flags, menu, record, guard, ledger, render | `uv run pytest tests/test_cli.py -q` |
| 14 | Python + JS | the package names, the audio in the file | `uv run sv build …`, then §9 |
| 15 | Docs | the README, six ADRs | `ls docs/adr/` |

#### The two commands every step ends with

```bash
uv run pytest -q                       # 46 passed
npm test && npm run typecheck          # 18 tests, and exit 0
```

⚠️ **Never one without the other.** `node --test` cannot see a `.tsx`, and the typecheck cannot see a behaviour —
the evening that found the missing `Audio` element had both green, and only a *real render* (§9) caught it.

## Glossary — market-overview

The vocabulary for the tool and the product it produces. Decisions live in `docs/adr/`; this file is a
glossary and nothing else.

### The two names

**market-overview** — the **tool**: this repository, its Python package and its CLI. It fetches market data,
computes a facts bundle, drives the render and assembles the day's output.

**Market Brief** — the **product the tool produces**: one day's silent, music-backed, ≤3 min, 16:9 video
about the Indian market, in two language editions. Output filenames carry the product's name
(`market-brief-<date>-<lang>.mp4`), because the artefact is the brief, not the tool.

### The run

**run** — one execution for one **session date**. A run either produces a complete pair of packages, or
produces nothing.

**session date** — the trading session a brief covers: the last **completed** one. Not the wall-clock date —
a run fired on a holiday, or before the close, has no new session to report.

### What crosses the boundary

**facts bundle** — `store/<date>/facts.json`, the **sole interface** between the Python layer and the render
layer. It carries **values and label keys, never display strings**.

**label table** — the static, hand-authored per-language strings. Labels live in the render layer, not in the
bundle: a label that changed with the data would be a template, not a label.

**value slot** — a position in a label table that a bundle value fills.

### The brief's structure

**card** — one screenful of the brief; also **block**. Card identity, order and screen furniture are constant
daily — only the contents vary.

**disclosure** — the standing *"educational only, not investment advice or a recommendation"* statement. It is
never a recommendation.

### The output

**edition** — one language's complete deliverable: `bn` or `en`.

**package** — one edition's folder, `output/brief/<date>/<lang>/`, self-contained: the video, its metadata text and
its thumbnail. Either package can be uploaded without touching the other.

**snapshot** — `store/<date>/`: the raw source responses and the facts bundle, kept so a video can be
rebuilt.

### Where it lives

**data root** — the folder **outside the repository** holding both products' assets and packages:
`~/.local/share/market-overview` unless `MARKET_OVERVIEW_DATA` says otherwise. ⚠️ The **snapshot** is deliberately
not in it, and neither is the reel's recorded run: the data root is *data*, a snapshot is *evidence*, and only the
evidence is committed.

**namespace** — one product's half of the data root: the brief's is `brief`. It is what makes the root shareable —
two products cannot write the same file, so nothing needs a lock to keep them apart.

### The sources

**spine** — the single TradingView scan carrying prices, indices, the six return windows, the moving
averages, the sector label and index membership. **Its failure aborts the run.**

**degrade to omission** — the rule for every source that is not the spine: a missing feed drops its own card
instead of failing the run.

**BSENSE** — the combined BSE + NSE scope used for the FII/DII figures — the number Indian media quotes.

## Glossary — song-video

The vocabulary for the tool and the product it produces. Decisions live in `docs/adr/`; this file is a glossary
and nothing else.

### The two names

**song-video** — the **tool**: this nested project, its Python package and its CLI (`sv`). It discovers the song,
collects the answers, records the run, drives Remotion and assembles the packages.

**the Song Reel** — the **product the tool produces**: one supplied song as a full-length 16:9 music video and its
own thumbnail, in one or more themes. Output filenames carry the product's name
(`song-reel-<song>-<theme>.mp4`), because the artefact is the reel, not the tool that made it.

### The run

**run** — one execution for one **song**: the recorded answers, N themes, N packages. ⚠️ Never a batch of songs —
the menu is one song at a time, because "the piece's length is the song's length" is a statement about *one*
master.

**song** — the operator's master under `resource/reel/song/<name>.<audio>`. ⚠️ The name is an **id**: it is the menu
entry, the `store/<song>/` folder and the `<song>` segment of every filename. Nothing displays it — the title does
that.

**ceiling** — what the master's own quality allows, and ⚠️ **the one number no pipeline step can raise.** A lossy
master is a lossy delivery, so the run reports the codec, the bitrate, the integrated loudness and the true peak —
measured, in the ledger — and supplying a lossless master is the only change that moves it. ⚠️ Nothing here
normalises, limits or re-masters: the level is the artist's (issue 09), and the pipeline owns only the *loss*.

**master** — that file, **unmodified**: the audio source of truth, the thing the digest guards and the thing the
rendering hears. ⚠️ Not the staged copy.

**staging** — `public/`, where the master and the cover are **copied** so a composition can fetch them. Scratch:
gitignored, and deleted with the run that made it. ⚠️ Still **in the project**, because it is scratch for a render
that runs from this tree — it is not data, and it is the one folder of the old three that did not move.

**title** — the string shown on screen and in the thumbnail, **typed at run time**. ⚠️ Never parsed from a filename
or an ID3 tag.

**cover** — the image the frame is built around: the artwork the still shows, and the face the reel's record turns.
⚠️ **Chosen three ways, in this order**: `--cover "<file>"` — a name in `resource/reel/song/`, and one that names nothing
there is refused · the image sharing the **master's basename**, which is the folder's own answer and needs no
question · otherwise the folder's **loose** images, where *one* is taken (one candidate is not a choice, exactly as
one song needs no menu), *several* are **asked** with *none* among the answers, and *none at all* means the motif.
⚠️ Whichever it was, it is **recorded with a digest**, like the master: the art in a still is part of the delivery,
so a *different* image under the same name is refused rather than drawn under an approval given for the old one.

**orphan cover** — an image there whose name **no master answers to**. ⚠️ Not a cover *by the pairing rule*, because
with two masters a loose image belongs to neither — so **one** is taken (a folder holding exactly one is not
ambiguous), **several** become a question, and any left over are **named** in the ledger with the `--cover` command
that would attach them. What the pairing rule was protecting survives as *never guessed at **silently***: every one
of those outcomes is printed, and the chosen one is recorded.

**caption** — the line under the title on the thumbnail: the word **music** and the piece's **duration** —
`সংগীত · ৩:০২`. ⚠️ Assembled from two halves that are deliberately written in two places: the word is a label in
the render layer's table, the duration is Python's formatting of Python's measurement. Neither side can invent the
other's half.

**caption language** — which script that line is written in: `bn` or `en`. ⚠️ It follows the script of the **title**
the operator typed — a Bengali title above an English caption reads like a template nobody translated — and
`--lang` settles it when the title cannot (an instrumental, a Latin transliteration). The numerals follow the same
choice: a Bengali caption counts in Bengali digits, `৩:০২`, which are different characters rather than `3:02` in a
font.

**time line** — the reel's line under the title: the piece's **elapsed time, counting** — `০:৪২ / ৩:০২`. ⚠️ Not the
**envelope** (that is the clock the *picture* runs on) and not a second caption. The still states the length, because
a fact is what a still can carry; the reel walks through that same number, because a reel has a clock. The total is
Python's string and is never recomputed, and the elapsed half is a pure function of the frame — so a rebuild ticks
identically (ADR 0003).

**progress dial** — the reel's line directly above the landscape: a **white hairline** the landscape's own width, with
the piece's progress as a **thin red needle** travelling it. The operator's own words, twice: *"white line … progress is
with red bar"* — and then the correction that settled the shape: *"the bar will be vertical and thin like radio
indicator"*, which is exactly what a tuning needle is.
⚠️ **It sits above the landscape at the landscape's width for a reason**: the needle's position and the landscape's
playhead are the *same* number (`travelled`), so giving them the same x makes the frame read as **one instrument** — a
dial over the song's shape — rather than two progress marks pointing at different places. ⚠️ **Every theme authors its
own red** (`palette.progress`), because one that reads as a marker on `parchment`'s paper is lurid on `neon`'s
near-black; the line the needle travels is the theme's own `ink` at low strength, so the pair belongs to the theme's
world on the light theme and the dark ones. ⚠️ **Not on the still**: a thumbnail has no progress to report, and a
needle frozen at a third would be a small lie about a song nobody has heard yet.

**recorded run** — `store/<song>/run.json`: the answers and the master's digest. ⚠️ An interface and a contract, not
a cache — a run replays it rather than asking again, and a master whose digest has changed is refused.

### What is built

**theme** — a named, authored identity: palette, type treatment, **motif** and motion grammar. ⚠️ Not a colour
scheme, and adding one is new code.

**accent** — one of a theme's **four authored colours**, chosen per piece: it lights the backdrop and draws the
title's rule. ⚠️ **Authored, never generated** (a cover-derived palette is the map's own fog), and chosen from the
master's **recorded digest** rather than from a random number — so two songs look different and one song rebuilds
byte-identical. ⚠️ It is *not* a second palette: `field`, `ink` and `wave` are never chosen, so a `vinyl` reel is
recognisably `vinyl` in all four.

**motif** — the theme's own moving object — the disc, the notes. ⚠️ Not a wave form. It is the frame's **artwork**,
and the structure around it is shared by every theme: **the artwork on the left, the song written on the right, the
landscape beneath** — a theme changes its palette, its type and how its colour moves, never where the eye goes.
⚠️ **The disc turns at a *rate*, not across the piece** — twelve seconds a revolution (5 RPM, and exactly one degree
per frame at 30 fps, the finest step the renderer can draw). A record has a speed, so a longer song simply gets more
revolutions; six turns spread over a whole piece was ~11° a second, and *"the disc is not rotating"* was a fair reading
of a disc that was.
⚠️ **And the artwork turns in *every* theme.** The `disc`/`notes` split decides the theme's *motif* — a record it turns,
or glyphs drifting in the field — and nothing else. `neon` and `aurora` used to draw it as a card that only floated,
and a round thing with a centre label **is** a record on screen whatever the code calls it, so the one difference the
card produced was a disc that stood still. The operator read it as a fault, twice, and was right both times.

**wave form** — the envelope's **geometry**: `bars`, `ribbon`, `ring`, `bloom`. ⚠️ Not a theme — it is one choice,
shared by every theme in a run.

**catalogue** — the predefined, committed set of themes and wave forms, authored in the render layer. ⚠️ Not the
discovered song list.

**envelope** — one amplitude per frame: the only clock the picture has. ⚠️ Not a beat, a tempo or a grid.

**settle** — how many frames of that envelope a theme **averages** the *pulse* and the light over — ⚠️ **the eye's
filter, never the clock's.** The landscape keeps its peaks (that is the song's shape, and it has to stay honest), but a
halo or a pool of light fed a true peak changes by tens of pixels between one frame and the next, which the eye reads
as a **strobe** rather than a swell. The average is **centred**, so the picture can never anticipate the music, and the
window shrinks at the ends instead of wrapping. ⚠️ It is a theme's own number because how calm the motion should be *is*
taste: `parchment` and `aurora` settle over most of a second, `neon` stays the punchiest of the four.

**ledger** — what a run prints before it renders: the song, the title, the themes, the wave form, the frame count
and the paths that will appear. It exists so a mis-tick costs seconds.

**quality gate** — ⚠️ the **thumbnails first**: every theme's thumbnail is rendered before any video, because N
one-frame stills cost seconds and a full-length reel costs about twenty minutes.

**delivery guard** — ⚠️ the check that the reel's **audio** survived the encode: that there is a stream at all, that
its rate is not below the master's, that the channel count matches, and — when the master is lossy — that the bitrate
did not fall below the master's own. It runs **before** the file reaches the package, so a delivery that lost the song
cannot replace a good one. ⚠️ The **level** is the artist's (issue 09); the **loss** is the pipeline's, and so is
catching it: the stills are size-checked and the masters are digest-checked, and the audio inside the reel was the one
thing nothing looked at.

**upload text** — the two files every package carries besides the video and the still: `title-….txt`, the line a search
result shows, and `description-….txt`, the paragraph under it — both in the **song's own script**. ⚠️ Built from the
recorded answers and nothing else, so a rebuild publishes the same words (ADR 0003), and ⚠️ **authored copy in Python**
(`seo.py`), not the render layer's label table, because it is never *drawn*: it is written to a file and pasted into a
form. The song's name leads (it is the query), then the artist when `--artist` gave one, then the length twice — `৩:০২`
and `৩ মিনিট ২ সেকেন্ড` — and both scripts' words for the genre, which is coverage rather than stuffing. ⚠️ A title over
YouTube's 100 characters is a **refusal**, never a truncation.

**package** — `output/reel/<song>/<theme>/`: one self-contained delivery of one theme — the reel and its thumbnail.
Either can be handed to its own uploader. ⚠️ Not the song folder.

**thumbnail** — the package's still, `thumbnail-<song>-<theme>.jpg`, at 1280×720. ⚠️ Its **own composition**, never
a frame grabbed from the video: it shows the mark at its largest, the title, the **caption**, and the cover art (or
the theme's motif when there is none), and it has no clock, so it cannot misrepresent the song's shape.

⚠️ **The badge is gone from both artefacts, and the mark is not a badge at all any more.** The still draws it raw —
no chip — because at thumbnail size a badge reads as a sticker on the artwork; the reel draws it as the **record's
label**: at the centre of the disc, on a plated circle, **turning with it**, where it sits *on* something and needs
no box. The plate is the colour the brief's loader already computes from the mark's own ink — the same decision,
worn as a label rather than as a corner bug — and it is needed because a cover passes behind it.

### Where it lives

**data root** — the folder **outside both projects** holding the reel's assets and packages, and the brief's beside
them: `~/.local/share/market-overview` unless `MARKET_OVERVIEW_DATA` says otherwise. The reel's half is
`resource/reel/song/` and `output/reel/`. ⚠️ The **recorded run** is deliberately not in it: the data root is
*data*, a record is *evidence*, and only the evidence is committed.

**namespace** — one product's half of the data root: the reel's is `reel`. ⚠️ It is what lets a reel and a brief
render **at the same time** — they cannot write the same file, so nothing needs a lock — and it is why the reel can
still read the brief's mark from `resource/brief/` without either product owning the other.

### Two words that are not here

⚠️ **`beat`.** It was in the ask and is deliberately gone ([the envelope](src/song-video/docs/adr/0006-the-envelope-is-the-only-clock.md)):
there is no beat grid and nothing cuts on a beat, so the word would describe a product this is not.

⚠️ **`variant`.** The ask used *theme* and *variant* interchangeably; a glossary keeping both would guarantee two
words for one thing. **N videos = N themes.**
