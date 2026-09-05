#!/usr/bin/env bash
# dispatch.sh <terminal-handle> <brief.md> [expected-file]
#
# Sends one bounded piece of work to the local worker and leaves a record of it.
#
# The worker is OpenClaw running qwen3.8-27b through LM Studio. OpenClaw takes
# the brief as a file and runs one turn, so there is no TUI to type into — which
# removes the two failure modes the previous setup had: a prompt containing HTML
# destroyed by the shell, and a prompt landing while the previous turn was still
# running.
#
# The brief still carries its task_id and dispatch_id. Without them Orca rejects
# the worker_done with `missing_task_id` and the work leaves no provenance even
# when it succeeded.
set -euo pipefail

H="$1"; BRIEF="$2"; EXPECT="${3:-}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT="${OPENCLAW_AGENT:-portfolio}"

# One active dispatch per terminal. Every "intermittent" dispatch failure in
# this project was this: a previous dispatch left open. Settle it first.
ACTIVE=$(orca orchestration worker-list --json 2>/dev/null | python3 -c "
import json,sys
try: d=json.load(sys.stdin)
except Exception: raise SystemExit
for w in d.get('result',{}).get('workers',[]):
    if w.get('assignee_handle')=='$H' and w.get('status')=='dispatched':
        print(w.get('id') or w.get('dispatch_id')); break
" 2>/dev/null)
[ -n "$ACTIVE" ] && orca orchestration worker-stop --dispatch "$ACTIVE" --json >/dev/null 2>&1

SPEC="$(head -1 "$BRIEF" | sed 's/^#\s*//')"
TASK=$(orca orchestration task-create --spec "$SPEC" --json | python3 -c 'import json,sys;print(json.load(sys.stdin)["result"]["task"]["id"])')
DISP=$(orca orchestration dispatch --task "$TASK" --to "$H" --json | python3 -c 'import json,sys;print(json.load(sys.stdin)["result"]["dispatch"]["id"])')
echo "task=$TASK dispatch=$DISP agent=$AGENT"

mkdir -p "$ROOT/.orca"
{
  echo "    task_id     = $TASK"
  echo "    dispatch_id = $DISP"
  echo
  echo "When finished, run this once:"
  echo
  echo '```bash'
  echo "orca orchestration send --type worker_done \\"
  echo "  --subject \"<short status>\" --body \"<what changed>\" \\"
  echo "  --task-id $TASK --dispatch-id $DISP \\"
  echo "  --outcome succeeded --files-modified \"<paths>\" --json"
  echo '```'
  echo
  echo "Use --outcome failed if it did not work."
  echo
  echo "---"
  echo
  cat "$BRIEF"
} > "$ROOT/.orca/task-current.md"

[ -n "$EXPECT" ] && rm -f "$ROOT/$EXPECT"

orca terminal send --terminal "$H" \
  --text "cd $ROOT && openclaw agent --local --agent $AGENT --message-file .orca/task-current.md 2>&1 | grep -v 'memory\]' | tail -20" \
  --enter --json >/dev/null 2>&1

echo "dispatched."
[ -n "$EXPECT" ] && echo "watching: $EXPECT"
