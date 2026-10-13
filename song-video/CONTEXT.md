# Context — song-video

The vocabulary for the tool and the product it produces. Decisions live in `docs/adr/`; this file is a glossary
and nothing else.

## The two names

**song-video** — the **tool**: this nested project, its Python package and its CLI (`sv`). It discovers the song,
collects the answers, records the run, drives Remotion and assembles the packages.

**the Song Reel** — the **product the tool produces**: one supplied song as a full-length 16:9 music video and its
own thumbnail, in one or more themes. Output filenames carry the product's name
(`song-reel-<song>-<theme>.mp4`), because the artefact is the reel, not the tool that made it.

## The run

**run** — one execution for one **song**: the recorded answers, N themes, N packages. ⚠️ Never a batch of songs —
the menu is one song at a time, because "the piece's length is the song's length" is a statement about *one*
master.

**song** — the operator's master under `resource/song/<name>.<audio>`. ⚠️ The name is an **id**: it is the menu
entry, the `store/<song>/` folder and the `<song>` segment of every filename. Nothing displays it — the title does
that.

**ceiling** — what the master's own quality allows, and ⚠️ **the one number no pipeline step can raise.** A lossy
master is a lossy delivery, so the run reports the codec, the bitrate, the integrated loudness and the true peak —
measured, in the ledger — and supplying a lossless master is the only change that moves it. ⚠️ Nothing here
normalises, limits or re-masters: the level is the artist's (issue 09), and the pipeline owns only the *loss*.

**master** — that file, **unmodified**: the audio source of truth, the thing the digest guards and the thing the
rendering hears. ⚠️ Not the staged copy.

**staging** — `public/`, where the master and the cover are **copied** so a composition can fetch them. Scratch:
gitignored, and deleted with the run that made it.

**title** — the string shown on screen and in the thumbnail, **typed at run time**. ⚠️ Never parsed from a filename
or an ID3 tag.

**cover** — the image the frame is built around: the artwork the still shows, and the face the reel's record turns.
⚠️ **Chosen three ways, in this order**: `--cover "<file>"` — a name in `resource/song/`, and one that names nothing
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

**recorded run** — `store/<song>/run.json`: the answers and the master's digest. ⚠️ An interface and a contract, not
a cache — a run replays it rather than asking again, and a master whose digest has changed is refused.

## What is built

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

**package** — `output/<song>/<theme>/`: one self-contained delivery of one theme — the reel and its thumbnail.
Either can be handed to its own uploader. ⚠️ Not the song folder.

**thumbnail** — the package's still, `thumbnail-<song>-<theme>.jpg`, at 1280×720. ⚠️ Its **own composition**, never
a frame grabbed from the video: it shows the mark at its largest, the title, the **caption**, and the cover art (or
the theme's motif when there is none), and it has no clock, so it cannot misrepresent the song's shape.

⚠️ **The badge is gone from both artefacts, and the mark is not a badge at all any more.** The still draws it raw —
no chip — because at thumbnail size a badge reads as a sticker on the artwork; the reel draws it as the **record's
label**: at the centre of the disc, on a plated circle, **turning with it**, where it sits *on* something and needs
no box. The plate is the colour the brief's loader already computes from the mark's own ink — the same decision,
worn as a label rather than as a corner bug — and it is needed because a cover passes behind it.

## Two words that are not here

⚠️ **`beat`.** It was in the ask and is deliberately gone ([the envelope](docs/adr/0006-the-envelope-is-the-only-clock.md)):
there is no beat grid and nothing cuts on a beat, so the word would describe a product this is not.

⚠️ **`variant`.** The ask used *theme* and *variant* interchangeably; a glossary keeping both would guarantee two
words for one thing. **N videos = N themes.**
