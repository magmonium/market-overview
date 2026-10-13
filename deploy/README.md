# Running the brief on a server

Builds and publishes the Market Brief **every day after the close**, unattended. The decision and its costs are in
[`docs/adr/0006`](../docs/adr/0006-a-server-runs-the-daily-brief.md); this file is the install.

```
market-brief.timer  →  market-brief.service  →  daily-brief.sh
                                                  ├── uv run --extra publish mo build   --lang bn en
                                                  └── uv run --extra publish mo publish --lang bn en
```

## Docker

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

⚠️ **The volumes in `compose.yaml` are not optional, and the reason is not size.** `output/` holds
`.published-<lang>.json` — the record that stops the next run re-uploading the same brief. `store/` is what makes a
re-render possible without re-fetching (ADR 0003). `var/` is where the run's log lands, and without it a scheduled
run is **completely silent**, because the wrapper redirects everything into that file. The container is disposable;
those three directories are not.

⚠️ **The timezone is pinned twice over, and both pins matter.** `compose.yaml` sets `TZ=Asia/Kolkata` on the
scheduler, because a cron expression is read in the container's local time and the container's default is UTC — a
run at 22:00 IST is one the session guard refuses every night, so the schedule would look healthy and publish
nothing. `Dockerfile` and `compose.yaml` carry a comment at each site; they are the pair that has to agree.

⚠️ **On the containerised schedule, `MARKET_OVERVIEW_PRIVACY` is read from `deploy/crontab`, not from the
environment.** A cron job is given a minimal environment and never sees the container's variables, so on that path
the crontab *is* the configuration. The one-shot path (`docker compose run --rm brief`) uses the environment
variable as you would expect. One source per path, deliberately — two that can disagree is how a schedule ends up
publishing publicly without anyone deciding to.

### What is different inside a container

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

## What the host needs (bare metal)

| | Why |
|---|---|
| **Linux**, x86-64 or arm64 | The window-server objection in ADR 0004 was macOS's. Linux renders headless with Remotion's bundled Chromium. |
| **`uv`**, and **Python ≥ 3.14** via it | `pyproject.toml`. |
| **Node ≥ 24** | The render layer. |
| **Chrome or Chromium** | ⚠️ Remotion's bundled `chrome-headless-shell` cannot be relied on — it SIGABRTs on the operator's machine, which is why `render.py` searches for a real browser. On a server: `apt-get install -y google-chrome-stable`, or Chromium. |
| Chromium's shared libraries | `libnss3 libdbus-1-3 libatk1.0-0 libgbm-dev libasound2 libxrandr2 libxkbcommon-dev libxfixes3 libxcomposite1 libxdamage1 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2` |
| **No ffmpeg, no fonts, no GPU** | ffmpeg ships with Remotion; the typeface is vendored (ADR 0005); nothing needs a display. |

Roughly: 4+ cores, 8 GB RAM, 20 GB disk for `store/` and `output/`. The render is CPU-bound and takes over an
hour for two editions.

## One-time setup

```bash
sudo useradd --create-home --shell /bin/bash market-brief
sudo -u market-brief git clone https://github.com/magmonium/market-overview.git /srv/market-overview
cd /srv/market-overview
sudo -u market-brief uv sync --extra publish
sudo -u market-brief npx remotion browser ensure     # optional; only if the bundled shell works
```

Assets and credentials, **never committed**:

```bash
sudo -u market-brief install -m 644 /path/to/logo.svg  /srv/market-overview/resource/logo.svg
sudo -u market-brief install -m 644 /path/to/music.mp3 /srv/market-overview/resource/music.mp3
sudo -u market-brief install -d -m 700 /home/market-brief/.config/market-overview
sudo -u market-brief install -m 600 /path/to/client-secret.json \
    /home/market-brief/.config/market-overview/client-secret.json
```

⚠️ **Where `/path/to/client-secret.json` comes from is its own walkthrough** — enabling the YouTube Data API, the
consent screen, the **Desktop app** client type and the seven-day *Testing* trap — in the main
[`README.md`](../README.md#creating-the-oauth-client-once). It is written for a laptop but it is the same client.

Then authorise **once**, on a machine with a browser — the server cannot open a consent window:

```bash
# on a laptop, with the same client-secret.json
uv run --extra publish mo publish --authorise
# copy the token it writes (~/.config/market-overview/token.json) to the same path on the server
```

⚠️ **Publish the OAuth consent screen before you rely on this.** A token from a client whose consent screen is
still in *Testing* **expires after seven days**, and nothing here can warn you in advance — `mo publish` starts
refusing with `invalid_grant`, a week after everything looked fine. This is the likeliest way this schedule fails.

## Install the timer (bare metal)

```bash
sudo cp deploy/market-brief.service deploy/market-brief.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now market-brief.timer
systemctl list-timers market-brief.timer      # confirm the next run
sudo systemctl start market-brief.service     # or fire it now, and watch:
journalctl -fu market-brief.service
```

Set `/srv/market-overview` in the `.service` file if you clone somewhere else.

## Reading the log

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

## Doing it by hand

The timer is a thin wrapper around two commands that work on their own:

```bash
uv run --extra publish mo build   --date 2026-10-12 --lang bn en   # re-renders from store/, no network
uv run --extra publish mo publish --date 2026-10-12 --lang bn en --privacy public
uv run --extra publish mo publish --date 2026-10-12 --lang bn --force   # re-upload after deleting the old video
```

⚠️ `mo publish` will **not** silently re-upload a rebuilt day: if the facts bundle changed, it refuses and says so,
because YouTube has no replace and two videos under one title is worse than none. Delete the old video, then pass
`--force`. The record of what went up is in `output/<date>/.published-<lang>.json`.
