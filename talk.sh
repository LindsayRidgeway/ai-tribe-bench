#!/usr/bin/env bash
# Talk to one member.
#
# This is the window path: the human asks, the member reads its own files, writes a file, and the
# exchange ends as a commit. Run it from a Goose window with this repository as the working directory,
# or from a terminal. The keys live in the environment, one per vendor:
#
#   set -a; . ~/LLM/dmitri-bot/bot.env; set +a        # or export DEEPSEEK_API_KEY=...
#   ./talk.sh a "why were you never thrown out of the game?"
#   ./talk.sh a --with letters/2026-11-01-the-window-and-the-vote-log.md "answer this"
#
# The member's voice is in its own state directory (voice.md), not in this script: a member is who its
# files say it is, and the model it borrows is one of those files.
set -euo pipefail
cd "$(dirname "$0")"

usage() { sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; exit 2; }

member="${1:-}"; [ -n "$member" ] || usage; shift
with=""
if [ "${1:-}" = "--with" ]; then with="${2:-}"; shift 2 || usage; fi
question="${1:-}"; [ -n "$question" ] || usage

voice="wake/members/$member/state/voice.md"
[ -f "$voice" ] || { echo "!! no voice file: $voice" >&2; exit 2; }
api="$(grep -E '^api:' "$voice" | head -1 | awk '{print $2}')"
model="$(grep -E '^model:' "$voice" | head -1 | awk '{print $2}')"
[ -n "$api" ] && [ -n "$model" ] || { echo "!! $voice needs an 'api:' and a 'model:' line" >&2; exit 2; }

args=(--member "$member" --api-model "$model" --api-base "$api" --ask "$question")
if [ -n "$with" ]; then
  [ -f "$with" ] || { echo "!! no such file to read: $with" >&2; exit 2; }
  args+=(--read "$with")
fi

python3 wake/wake.py "${args[@]}"

newest="$(ls -t "wake/members/$member/output"/*.md 2>/dev/null | head -1 || true)"
if [ -n "$newest" ]; then
  echo
  echo "=== $member wrote ${newest} ==="
  sed -n '1,120p' "$newest"
fi

# A conversation that is not written down did not happen. The member's file is written by the harness;
# this puts the whole exchange in the repository so the next window can find it.
if git rev-parse --git-dir >/dev/null 2>&1; then
  git add -A
  if git diff --cached --quiet; then echo "nothing to commit"; else
    git commit -q -m "talk: $member answered — ${question:0:70}"
    git push -q 2>/dev/null || echo "(committed locally; push failed — pull and push when you can)"
    echo "committed"
  fi
fi
