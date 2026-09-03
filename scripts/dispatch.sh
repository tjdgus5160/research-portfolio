#!/usr/bin/env bash
# dispatch.sh <terminal-handle> <brief.md> [target-file]
#
# Sends one bounded piece of work to the local worker and leaves a record of it.
#
# Two things this exists to get right, both learned the hard way:
#
#   1. The brief travels as a FILE. A prompt containing HTML sent through the
#      terminal gets eaten by the shell — `parse error near '<'`.
#   2. The brief carries its task_id and dispatch_id, so the worker's
#      worker_done is accepted. Without them Orca rejects the report with
#      `missing_task_id` and the work leaves no provenance, even when it
#      succeeded.
#
# Each dispatch also restarts the agent, because every brief is self-contained
# and a small context is speed at ~17 tok/s.
set -euo pipefail

H="$1"; BRIEF="$2"; TARGET="${3:-}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SPEC="$(head -1 "$BRIEF" | sed 's/^#\s*//')"
TASK=$(orca orchestration task-create --spec "$SPEC" --json | python3 -c 'import json,sys;print(json.load(sys.stdin)["result"]["task"]["id"])')
DISP=$(orca orchestration dispatch --task "$TASK" --to "$H" --json | python3 -c 'import json,sys;print(json.load(sys.stdin)["result"]["dispatch"]["id"])')
echo "task=$TASK dispatch=$DISP"

mkdir -p "$ROOT/.orca"
{
  echo "    task_id     = $TASK"
  echo "    dispatch_id = $DISP"
  echo
  echo "When finished, report exactly once:"
  echo
  echo '```bash'
  echo "orca orchestration send --type worker_done \\"
  echo "  --subject \"<short status>\" --body \"<what changed>\" \\"
  echo "  --task-id $TASK --dispatch-id $DISP \\"
  echo "  --outcome succeeded --files-modified \"<paths>\" --json"
  echo '```'
  echo
  echo "Use --outcome failed if it did not work. Then stop and idle."
  echo
  echo "---"
  echo
  cat "$BRIEF"
} > "$ROOT/.orca/task-current.md"

orca terminal send --terminal "$H" --interrupt --json >/dev/null 2>&1 || true
orca terminal send --terminal "$H" --interrupt --json >/dev/null 2>&1 || true
orca terminal wait --terminal "$H" --for tui-idle --timeout-ms 45000 --json >/dev/null 2>&1 || true
orca terminal send --terminal "$H" --text "" --enter --json >/dev/null 2>&1
orca terminal send --terminal "$H" --text "opencode" --enter --json >/dev/null 2>&1
orca terminal wait --terminal "$H" --for tui-idle --timeout-ms 90000 --json >/dev/null 2>&1 || true
sleep 6
orca terminal send --terminal "$H" \
  --text "Read .orca/task-current.md and do exactly what it says. Do not read any other file unless it names one." \
  --enter --json >/dev/null 2>&1

echo "dispatched. wait with:"
echo "  orca orchestration check --wait --types worker_done,escalation,question --timeout-ms 900000 --json"
[ -n "$TARGET" ] && echo "  watch:  $TARGET"
