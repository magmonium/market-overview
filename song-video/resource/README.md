# resource/ — the reel's own inputs

Only the **songs** live here. ⚠️ The **mark does not**: the logo is the brief's own operator asset, read
from `market-overview/resource/logo.png` through the brief's own loader, so one licensed file serves both
products and there is one place to change it.

Everything in this folder is gitignored except this file — committing a master song publishes it.

## Expected files

| File | Purpose | Required |
|---|---|---|
| `song/<name>.<audio>` | **the master** — the song the reel is built from | yes, at least one |
| `song/<name>.<image>` | the cover, sharing the master's basename | no |

```
resource/
├── README.md
└── song/
    ├── dure-kothay.mp3      ← master
    └── dure-kothay.jpg      ← optional cover
```

`<name>` **is** the song's identity: it is the menu entry, the `store/<name>/` folder, and the `<song>`
segment of every output filename.

⚠️ **The name is an id, not a title.** Nothing displays it. The title shown on the video, the disc and the
thumbnail is **typed at run time**, so `dure-kothay_128kbps_final_mix.mp3` never becomes a caption.

## Formats

**Any audio format the toolchain reads.** The pipeline never re-encodes the master, and the toolchain is the
one Remotion already ships, so there is no system `ffmpeg` prerequisite. An extension list exists only so
the menu can tell a song from a stray file.

⚠️ **A file the toolchain cannot decode fails the run loudly** when that song is chosen. It never renders a
silent video.

## The master is never touched

⚠️ **No normalisation, no trimming, no fades, no looping.** The brief normalises its music bed to −14 LUFS
and trims it to the video's length, because a bed is furniture. **A song is not furniture**: its level, its
opening, its ending and its length are the artist's, and the reel is exactly as long as the song is.

The pipeline reads the master, copies it into the renderer's staging folder for the duration of the run, and
deletes that copy afterwards. **This folder is read and never written.**

## Absent is a supported state — with one exception

- **No cover** — the disc gets a plain label in the theme's palette, and the thumbnail is composed from the
  mark and the title alone. A designed state, not a degraded one.
- ⚠️ **A cover whose name belongs to no master** — `man-poreche-preme.png` in a folder holding only
  `beshorom.mp3` — is **not** a cover, and it is never guessed at as one: the pairing is by **name**, so with two
  masters here a loose image belongs to neither. The run **names the file** in its ledger instead of passing it
  over in silence. Either add the master it belongs to, or rename it to the master's basename
  (`beshorom.png`), which is the whole of the rule.
- **No songs at all** — ⚠️ **the run refuses**, with a reason and a non-zero exit. Unlike a missing bed, an
  absent song means there is no product to make.

## Licence is the operator's

The pipeline records no licence metadata and enforces nothing. By placing a file here the operator declares
it is **licensed for this product including publication** — for both the song and the cover image.

## Rules

- **Never modified in place.** The supplied file is the master; staged files are scratch and are removed when
  the run ends.
- **Discoverable, not declared.** No manifest, no index and no sidecar JSON — adding a song is dropping a
  file in.
- **One song per run.** A run makes one song into one or more reels; it is not a batch tool.
