# The video format

Type: grilling
Status: resolved

## Question

The shape of the artefact. The brief said *"slide"* **and** *"video"*, which are not the same thing.

1. **Medium** — a 16:9 video (as the Market Brief is), a 4:5 / 1:1 image carousel for social, or both from one
   render?
2. **Books per slide** — 100 slides of one book each, 10 slides of ten, or a hero top-10 then a dense list? A
   one-book slide is beautiful and slow; a ten-book slide is fast and cramped.
3. **Duration** — the brief caps at 3 minutes. What is the cap here, and does a 100-book run fit inside it?
4. **Audio** — reuse the brief's music-bed contract (a bed normalised into the run), or ship it silent?

⚠️ **Four charts** (ticket 12). Does each chart get its own video, or does one video carry four sections? Ticket 13
settles the count; this ticket settles the shape within whatever it decides.

## Answer

### 1 — Medium: one composition, two outputs

**Primary: a 16:9 video.** The SEO tags and the full-list description the brief asks for (ticket 15) are
YouTube-shaped, and 16:9 is what the host repo already renders.

**Secondary, and nearly free: the slides as stills.** ⚠️ Not a second design — Remotion renders a **still** from the
same composition, so a 4:5 / 1:1 carousel is the video's slides at full resolution with **no extra layout work**. A
social artefact for the price of a loop.

### 2 — Books per slide: **one book, all 100, every field** — with rank-weighted dwell

The brief says *every* slide shows the cover, best price, publisher, author, rank, Δ, NEW and pub date. Honoured
literally: **100 slides, one book each, all eight fields on every one.**

The problem that creates is **time** — and the answer is not fewer slides, it is **uneven dwell**:

| Segment | Books | Dwell each | Subtotal |
|---|---|---|---|
| Intro | — | 6 s | 6 s |
| **1–10** | 10 | **3.5 s** | 35 s |
| 11–30 | 20 | 2.0 s | 40 s |
| 31–60 | 30 | 1.4 s | 42 s |
| 61–100 | 40 | 1.0 s | 40 s |
| Outro | — | 6 s | 6 s |
| | | **Total** | **169 s = 2 m 49 s** |

The rank *is* the interest curve, so the dwell follows it.

⚠️ **The honest consequence:** below roughly rank 50 a slide is a **glance, not a read**. Nobody reads a publisher and
a pub date in 1.0 s. That is not a flaw to hide — it is precisely why the **description carries the full list** (ticket
15) with the detail the video cannot dwell on. **The video gives the shape; the description gives the data.**

### 3 — Duration: **3 minutes**, matching the host repo

Reuse the brief's cap (`timeline.CAP_SECONDS = 180`) and its FPS. The table lands at **2 m 49 s** with ~11 s of
headroom — enough for the superset (ticket 14) to repeat a title without the run growing.

### 4 — Audio: **music-backed, no voiceover**

⚠️ Reuse the brief's **music-bed contract** — a bed normalised into the run and muxed by Remotion's bundled ffmpeg
(`audio.py`). The brief calls itself *"silent, music-backed"*: silent means **no narration**, not no sound. Match it.

Narration is a **separate product decision**, not a setting — it would change the copy budget, the dwell times and the
whole voice of the thing.

### ⚠️ 5 — The consequence for ticket 13, and it is a hard one

**Four charts × 100 books = 400 slides.** At the dwell above that is **≈11 minutes**, not 3.

So the 3-minute cap and the four-chart scope **cannot both hold inside one artefact**. Ticket 13 has a constraint it
did not have before:

- **Four separate videos** — each ~2 m 49 s, each with its own title, description, tags and thumbnail (tickets 15, 16).
  *This is what the arithmetic wants.*
- **One long video** (~11 min) — four sections, one publish — but the 3-minute identity is gone and the title scheme
  gets muddier.

⚠️ Flagged into **ticket 13** rather than decided here.
