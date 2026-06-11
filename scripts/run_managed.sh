#!/usr/bin/env bash
#
# run_managed.sh — managed long-run launcher (WP6.2 G3)
#
# Long measurements must NEVER live inside an agent session (the
# agent-dies-measurement-dies failure occurred 3x; AGENTS.md rule 4).
# This script starts a command in its own session via setsid, so it survives
# the launching terminal/agent, and materializes the full run state on disk:
#
#   <run_dir>/command.txt   the exact argv that was launched
#   <run_dir>/pid           PID of the detached process (session leader)
#   <run_dir>/run.log       merged stdout+stderr, line-buffered append
#   <run_dir>/exit_code     written when the command finishes (poll for this)
#
# Usage:
#   scripts/run_managed.sh <run-name> -- <command> [args...]
#
# Examples:
#   scripts/run_managed.sh wp0-degraded-sweep -- \
#     env PYTHONPATH=src OMP_NUM_THREADS=1 \
#     python scripts/feasibility_audit/wp0_degraded_sweep.py --full \
#       --output-dir runs/feasibility_audit/wp0_degraded_sweep
#
#   # monitor:
#   tail -f runs/managed/wp0-degraded-sweep_<UTC>/run.log
#   # completion + exit code (absent until the process exits):
#   cat runs/managed/wp0-degraded-sweep_<UTC>/exit_code
#   # stop:
#   kill -TERM -- -"$(cat runs/managed/wp0-degraded-sweep_<UTC>/pid)"
#
# Environment:
#   MANAGED_RUN_ROOT  root directory for run dirs (default: runs/managed)
#
# Notes:
# - Commands needing env vars should use `env KEY=VALUE ... cmd` (see example)
#   so the assignments survive the argv handoff.
# - Pair long runs with their own progress.jsonl + --resume support; this
#   wrapper guarantees survival and exit-code capture, not checkpointing.
# - Prints the run dir on stdout; exits 0 once the process is launched.

set -euo pipefail

usage() {
  sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//'
}

if [[ $# -lt 3 ]]; then
  usage >&2
  echo "error: expected <run-name> -- <command> [args...]" >&2
  exit 2
fi

RUN_NAME="$1"
shift
if [[ "$1" != "--" ]]; then
  echo "error: second argument must be '--' (got: $1)" >&2
  exit 2
fi
shift

if [[ ! "$RUN_NAME" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "error: run-name must match [A-Za-z0-9._-]+ (got: $RUN_NAME)" >&2
  exit 2
fi

RUN_ROOT="${MANAGED_RUN_ROOT:-runs/managed}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="$RUN_ROOT/${RUN_NAME}_${STAMP}"
mkdir -p "$RUN_DIR"

printf '%q ' "$@" > "$RUN_DIR/command.txt"
printf '\n' >> "$RUN_DIR/command.txt"

# Detach: new session (setsid) + background; the inner shell records its own
# PID, runs the command appending to run.log, and persists the exit code.
RUN_DIR="$RUN_DIR" setsid bash -c '
  echo "$$" > "$RUN_DIR/pid"
  "$@" >> "$RUN_DIR/run.log" 2>&1
  status=$?
  echo "$status" > "$RUN_DIR/exit_code"
  exit "$status"
' managed-run "$@" < /dev/null &
LAUNCHER_PID=$!

# Wait briefly for the pidfile so callers can rely on it existing.
for _ in $(seq 1 50); do
  [[ -s "$RUN_DIR/pid" ]] && break
  sleep 0.1
done
if [[ ! -s "$RUN_DIR/pid" ]]; then
  echo "$LAUNCHER_PID" > "$RUN_DIR/pid"
fi

echo "run_dir=$RUN_DIR"
echo "pid=$(cat "$RUN_DIR/pid")"
echo "log=$RUN_DIR/run.log"
echo "exit_code_file=$RUN_DIR/exit_code (absent until the process exits)"
