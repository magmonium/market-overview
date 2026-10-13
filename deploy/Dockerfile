# syntax=docker/dockerfile:1
# check=skip=SecretsUsedInArgOrEnv
#
# ⚠️ The line above silences exactly one lint rule, and it is a false positive worth naming: Docker's checker flags
# `ENV MARKET_OVERVIEW_CREDENTIALS` because the *variable name* reads like a secret. Its value is a **directory
# path**. The actual secrets are the OAuth client and token, which are bind-mounted read-only from
# `../credentials/` and excluded from the build context by `.dockerignore` — they are never in the image.
# Silencing it deliberately, in one line, keeps a real warning from being lost in the noise of a standing one.
#
# The Market Brief as a **one-shot job**: build the day's editions, publish them, exit. There is no scheduler in
# this image — see compose.yaml, or deploy/README.md for the host-timer alternative.
#
# ⚠️ Adapted from Remotion's own Docker recipe (remotion.dev/docs/docker). Four things are this project's and not
# Remotion's:
#
#   - **Node 24**, where their recipe says 22. `package.json` requires >= 24.
#   - **A real Google Chrome.** Remotion's bundled `chrome-headless-shell` SIGABRTs at "Getting composition" on
#     some machines, so `render.py` searches for a full browser *before* falling back to the bundled one. Chrome
#     running as root is fine here: Remotion passes `--no-sandbox` unconditionally
#     (`@remotion/renderer/dist/open-browser.js`), so there is no sandbox flag to add.
#   - **Python 3.14 via uv**, because bookworm's `python3` is 3.11 and `pyproject.toml` requires >= 3.14.
#   - **No fonts at all**, deliberately. The typeface is vendored (`docs/adr/0005`), so a fontless image is not a
#     risk to the render — it is a *test* of it: if any glyph had to come from the system, `useFonts` would refuse
#     rather than quietly fall back to something else.
FROM node:24-bookworm-slim

# ⚠️ `cron` is here for the containerised schedule, and it is **Debian's own** rather than a third-party scheduler
# image — one apt package from the repository this file already uses, instead of another registry to trust and pin.
# The one-shot job never starts it; see the `scheduler` service in compose.yaml.
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl gnupg cron \
      libnss3 libdbus-1-3 libatk1.0-0 libgbm-dev libasound2 libxrandr2 libxkbcommon-dev \
      libxfixes3 libxcomposite1 libxdamage1 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://dl.google.com/linux/linux_signing_key.pub \
      | gpg --dearmor -o /usr/share/keyrings/google.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/google.gpg] \
https://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /uvx /usr/local/bin/

ENV UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

RUN uv python install 3.14

WORKDIR /app

# Dependencies first, so editing a module does not re-resolve the whole graph. `--no-install-project` because the
# source is not here yet.
COPY pyproject.toml uv.lock package.json package-lock.json ./
RUN uv sync --frozen --extra publish --no-install-project \
    && npm ci

COPY remotion ./remotion
COPY src ./src
COPY deploy ./deploy
COPY tsconfig.json remotion.config.ts ./
RUN uv sync --frozen --extra publish

# ⚠️ The containerised schedule is a `/etc/cron.d/` file, **not** the image's `CMD`. Debian's cron requires that
# file to be root-owned and mode **0644** — a `cron.d` entry with the execute bit set is *silently ignored*, and the
# symptom is a schedule that never fires and logs nothing at all. That is why the chmod is here, next to the copy,
# rather than in an install step somewhere down the line.
COPY deploy/crontab /etc/cron.d/market-brief
RUN chmod 0644 /etc/cron.d/market-brief \
    && chmod +x /app/deploy/daily-brief.sh

# ⚠️ `/app/.venv/bin` on PATH is what makes the wrapper call `mo` directly instead of `uv run` — see the note in
# `daily-brief.sh` for why that difference matters on a schedule.
ENV PATH="/app/.venv/bin:${PATH}" \
    MARKET_OVERVIEW_ROOT=/app \
    MARKET_OVERVIEW_CREDENTIALS=/credentials

CMD ["/app/deploy/daily-brief.sh"]
