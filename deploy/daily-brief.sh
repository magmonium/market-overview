#!/usr/bin/env bash
#
# daily-brief.sh — build the day's brief and put it on the channel.
#
# ⚠️ Run by `market-brief.timer`, not by hand. See docs/adr/0006. Everything here is either a path the
# scheduler does not supply, or a guard against the run overlapping itself — because the build is the
# hour-long part and the upload is the part that cannot be undone.
#
#   ./daily-brief.sh                        # both editions, private
#   MARKET_OVERVIEW_PRIVACY=public ./daily-brief.sh
set -uo pipefail

ROOT="${MARKET_OVERVIEW_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$ROOT" || exit 1

# ⚠️ A timer hands its job a bare environment: `uv` and `node` are not on it, and the failure reads as
# "command not found" in a log nobody is watching at half past four.
export PATH="${HOME}/.local/bin:/usr/local/bin:/usr/bin:/bin"
export MARKET_OVERVIEW_PRIVACY="${MARKET_OVERVIEW_PRIVACY:-private}"

LOG_DIR="${ROOT}/var/log"
mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/daily-$(date +%F).log"

# ⚠️ One run at a time. A two-edition run is well over an hour, so a second firing must not overlap the first,
# and `flock -n` is what makes skipping a *decision* rather than a race.
exec 9>"${LOG_DIR}/.daily-brief.lock"
if ! flock -n 9; then
  echo "$(date -u +%FT%TZ) another run holds the lock — skipping" >>"$LOG"
  exit 0
fi

say() { echo "$(date -u +%FT%TZ) $*" >>"$LOG"; }

# ⚠️ **The tool is invoked through `uv run` on a host and directly inside an image**, and the difference is not
# cosmetic: `uv run` re-syncs the environment, which inside a container is slow *and* can remove the `publish`
# extra that the image installed — so a schedule would work once and then start failing. `mo` on PATH means the
# environment is already the one we want.
if command -v mo >/dev/null 2>&1; then
  TOOL=(mo)
else
  TOOL=(uv run --extra publish mo)
fi

# ⚠️ `--extra publish` on both lines: `uv run` syncs the environment to the default set, so an extra installed
# by hand once would be quietly removed by the next scheduled run.
say "build --lang bn en"
# ⚠️ `--lang bn en`, always. `LANGUAGES` is `("bn",)`, so a schedule that omitted it would build half the
# product — and the half it built would report a complete success.
"${TOOL[@]}" build --lang bn en >>"$LOG" 2>&1
built=$?

if [ "${built}" -ne 0 ]; then
  # ⚠️ Exit 1 means one of two very different things, and this log is the only place that says which.
  # A **refusal** — a holiday, a weekend, or a session that has not finished printing — is the session guard
  # working, and is not an alarm. Anything else is the pipeline failing, and is.
  if grep -qE 'asked for|has not finished printing' "$LOG"; then
    say "no new session — nothing to publish (exit ${built})"
    exit 0
  fi
  say "BUILD FAILED (exit ${built}) — see above"
  exit "${built}"
fi

say "publish --lang bn en --privacy ${MARKET_OVERVIEW_PRIVACY}"
"${TOOL[@]}" publish --lang bn en --privacy "${MARKET_OVERVIEW_PRIVACY}" >>"$LOG" 2>&1
shipped=$?
say "publish exit ${shipped}"
exit "${shipped}"
