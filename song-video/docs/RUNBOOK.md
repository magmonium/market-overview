# Runbook — the Song Reel, step by step

Every command in this project, in the order it is used, with what a good result looks like. ⚠️ **Everything runs
from `song-video/`** — never from the repository above it, for the reason in [Traps](#traps-each-one-cost-something).

```bash
cd /Users/dibyendudas/Documents/magmonium/market-overview/song-video
```

## The whole pipeline at a glance

| | |
|---|---|
| **in** | `resource/song/<name>.<audio>` + an optional `<name>.<image>` cover |
| **asked once** | song · title · themes (many) · wave form (one) — recorded in `store/<song>/run.json` |
| **guarded** | the master's `sha256`; a changed master refuses |
| **rendered** | every **thumbnail** first, then every **reel** |
| **out** | `output/<song>/<theme>/` — `song-reel-<song>-<theme>.mp4` + `thumbnail-<song>-<theme>.jpg` |

## 1. Setup

```bash
uv sync                                        # the reel's own venv, and the brief as an editable path dep
cp ../resource/music.mp3 resource/song/music.mp3   # a master; drop a cover beside it if you have one
ls resource/song/                              # music.mp3 — the name here is the song *id* everywhere else
```

⚠️ `resource/song/` is gitignored: the licence is the operator's, and committing a master publishes it.

## 2. The Python suite

```bash
uv run pytest -q                    # 46 passed
uv run pytest tests/test_cli.py -q  # one module
uv run pytest tests/test_render.py -q -k command   # one idea
```

⚠️ **Where the tests never go:** no test in the suite reaches Remotion. The render fakes are installed in
`setUp`, so a test added later cannot quietly start an hour of frames. Anything a *fake* cannot check — that the
composition ids exist, that the audio is in the file — is checked by running the thing (§7, §8).

## 3. The JS layer: tests, then the typecheck

```bash
npm test              # node --test remotion/*.test.ts   → 18 tests
npm run typecheck     # tsc --noEmit                     → exit 0
npm run studio        # Remotion studio, for designing a theme by hand
```

⚠️ **Both, always.** `node --test` cannot load a `.tsx` file at all — JSX is not erasable TypeScript — so the
geometry lives in `.ts` (tested) and the drawings in `.tsx` (compiled, and *looked at*). The typecheck catches a
class of bug no test can: it caught a missing import on the evening when 14 tests were green.

## 4. What the menu will offer

```bash
uv run python -c "from song_video import catalogue; print([e.id for e in catalogue.themes()], catalogue.forms())"
# ['vinyl', 'neon', 'parchment', 'aurora'] ('bars', 'ribbon', 'ring', 'bloom')
```

That list is **read out of the renderer** (`remotion/themes.ts`, through node's type stripping), never mirrored —
so a theme the composition cannot draw cannot appear in the menu.

## 5. Build a reel

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

1. **discover** the song from `resource/song/`
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

### Sound, measured — and never adjusted

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
| **crystal clear** | the ceiling is the master. A `wav`/`flac` in `resource/song/` is the single change that raises it — ⚠️ and if both are there, the lossless one is already the master (the suffix order in `library.py`) |
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

### What the package carries — including the words

⚠️ **Every package is four files, and two of them are text.** Issue 07's contract is that a folder can be handed to its
own uploader, and an uploader asks for a title and a description as much as for a video and a still:

```
output/<song>/<theme>/
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
$ cat "output/…/vinyl/title-….txt"
বেশরম লতার মতো | ৩:০২ | বাংলা গান

$ cat "output/…/vinyl/description-….txt"
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

## 6. Refusals are part of the interface

| Command | What it says, and why that is right |
|---|---|
| `uv run sv build` (no songs) | `no songs in …/resource/song — drop a master in and run again` |
| `uv run sv build --song nope …` | `'nope' is not in …/resource/song — the songs there are music` (an ambiguous folder names the songs too) |
| `uv run sv build --theme sparkle` | `unknown theme "sparkle" — the catalogue is vinyl, neon, parchment, aurora` |
| `uv run sv build --wave zigzag` | `unknown wave form "zigzag" — the catalogue is bars, ribbon, ring, bloom` |
| `uv run sv build --lang fr` | `unknown language "fr" — the languages are bn, en` (the caption's script is refused for the same reason a theme is) |
| `uv run sv build --cover nope.png` | `no image "nope.png" in …/resource/song — the images there are poster.jpg` (the list *is* the fix) |
| `uv run sv build --cover some/path.png` | `--cover takes the image's name, not a path` (a record holds a name in the folder, not somebody's desktop) |
| several images, no terminal | `3 images in …/resource/song pair with no master, so choosing one is a decision rather than a default — say which one rides music with --cover (…)` |
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

| in `resource/song/` | what happens |
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

## 7. Look at a theme without spending twenty minutes

The pipeline already does this — the thumbnails land before the first reel. For an ad-hoc frame, write the props
by hand (the flat object `remotion/props.ts` describes) and render one:

⚠️ **What to look at, because *attractive* and *eye-soothing* are not one setting.** Four things decide it, and only the
last two belong to a theme:

| | |
|---|---|
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

## 8. Spot-check a reel in a minute, instead of twenty

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

## 9. Read back what was made

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

## 10. Where everything lands

```
resource/song/<name>.<audio>   the master (+ an optional <name>.<image>)    read-only, gitignored
store/<song>/run.json          the recorded run — the rebuild contract      committed
public/<name>.<audio>          staging: the copy a composition can fetch    scratch,  gitignored
output/<song>/<theme>/         the package: the reel and its thumbnail      build output, gitignored
```

```bash
find output -type f | sort        # the packages
find output -name '.*' | sort     # ⚠️ must be empty after a run: no scratch and no props left behind
ls store/*/run.json               # the records — these are the ones to commit
```

## 11. Traps (each one cost something)

| Symptom | Cause, and what to do |
|---|---|
| `Could not find composition with ID SongReelThumbnail. Available compositions: MarketBrief, Thumbnail, IndexCard` | The render ran from the **repository** — and both projects have a `remotion/index.ts`. Run from `song-video/`: `render.where()` is the reel's own tree, and a test asserts the ids it invokes are registered there |
| `SIGABRT` (signal 6) from `ffprobe` | A bare call needs the loader path. Use `market_overview.audio.run` / `.duration`, never the binary directly |
| `Protocol error (Target.createTarget): Target closed` at `Getting composition` | Remotion's browser died. `--browser-executable` (a full Chrome) is required on this machine, and a sporadic death still happens roughly once in seven renders — the run fails cleanly, and thumbnails-first makes it cheap |
| `remotion render (…) failed (-1)` | The process was killed by a signal. `nohup … &` from a shell that later closes gets `SIGHUP` — not a render failure |
| The ledger appears *after* the first render lines | stdout is block-buffered on a pipe; the conductor flushes before rendering. If it regresses, this is what it looks like |
| pytest collects the brief's tests as well | pytest resolves `rootdir` upward; the reel owns its own `testpaths` |
| Reel media got committed | The parent's `.gitignore` does not reach into this folder — a pattern containing a slash is anchored to its own directory, so the reel owns its own ignore file |
| `VIRTUAL_ENV … does not match the project environment path .venv` | Harmless: an outer `market-overview` venv is active while `uv` uses the reel's own. Add `--active` only if you want the outer one |
| Re-running repeats themes that already finished | There is **no resume and no retry** (ADR 0004). A `--only <theme>` is the obvious next addition |

## 12. How it was built — the order, and the loop

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
| 15 | Docs | `CONTEXT.md`, six ADRs, this runbook | `ls docs/adr/ CONTEXT.md` |

### The two commands every step ends with

```bash
uv run pytest -q                       # 46 passed
npm test && npm run typecheck          # 18 tests, and exit 0
```

⚠️ **Never one without the other.** `node --test` cannot see a `.tsx`, and the typecheck cannot see a behaviour —
the evening that found the missing `Audio` element had both green, and only a *real render* (§9) caught it.
