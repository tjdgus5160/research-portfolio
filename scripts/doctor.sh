#!/usr/bin/env bash
# Run this before dispatching anything. The one time it was skipped, a worker
# sat for nine minutes against a stopped LM Studio server.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LMSTUDIO="${LMSTUDIO_URL:-http://127.0.0.1:1234}"
MODEL="${WORKER_MODEL:-qwen/qwen3.8-27b}"
LMS="$HOME/.lmstudio/bin/lms"

rc=0
ok()   { printf '  \033[32mOK\033[0m    %s\n' "$1"; }
bad()  { printf '  \033[31mFAIL\033[0m  %s\n' "$1"; rc=1; }
note() { printf '        %s\n' "$1"; }

echo "research-portfolio doctor"; echo

echo "Orca runtime"
orca status --json >/dev/null 2>&1 && ok "reachable" || bad "not reachable — run 'orca open'"

echo; echo "LM Studio server (${LMSTUDIO})"
models="$(curl -s --max-time 5 "${LMSTUDIO}/v1/models" 2>/dev/null)"
if [ -z "$models" ]; then
  bad "not responding"
  note "start it:  $LMS server start --port 1234"
elif printf '%s' "$models" | grep -q "\"${MODEL}\""; then
  ok "serving ${MODEL}"
else
  bad "reachable, but ${MODEL} is not listed"
fi

echo; echo "Worker model loaded"
if [ -x "$LMS" ] && "$LMS" ps 2>/dev/null | grep -q "$MODEL"; then
  ok "$($LMS ps 2>/dev/null | grep "$MODEL" | head -1 | awk '{print $1" — "$3}')"
else
  bad "not loaded — the first request will stall while it loads"
  note "load it:  $LMS load $MODEL --yes"
fi

echo; echo "Project"
[ -f "$ROOT/assets/css/tokens.css" ] && ok "tokens.css present" || bad "tokens.css missing"
if (cd "$ROOT" && python3 scripts/validators/validate_site.py >/dev/null 2>&1); then
  ok "site gate passes"
else
  note "site gate does not pass yet — run scripts/validators/validate_site.py"
fi

echo
[ $rc -eq 0 ] && echo "Ready to dispatch." || echo "Fix the above before dispatching."
exit $rc
