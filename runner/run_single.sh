#!/usr/bin/env bash
#
# Run a single (task, effort, run_n, model) cell of the benchmark matrix.
#
# Usage:
#   bash runner/run_single.sh <task_dir> <effort> <run_n> [model]
#
# Example:
#   bash runner/run_single.sh tasks/01_rename low 1 claude-opus-4-7
#
# Outputs into results/runs/<run_id>/:
#   stdout.json          - raw Claude Code -p output
#   stderr.log           - stderr stream
#   final_diff.patch     - git diff between initial and final state
#   diff_stat.txt        - git diff --stat
#   verify_result.json   - output of tasks/<id>/verify.sh
#   verify.log           - stderr of verify.sh
#   run_meta.json        - timing, exit code, claude version, identifiers
#   metrics.json         - parsed metrics from parse_session.py
#
set -euo pipefail

if [[ $# -lt 3 ]]; then
    echo "Usage: $0 <task_dir> <effort> <run_n> [model]" >&2
    exit 2
fi

TASK_DIR="$1"
EFFORT="$2"
RUN_N="$3"
MODEL="${4:-claude-opus-4-7}"

# --- Validate inputs --------------------------------------------------------
if [[ ! -d "$TASK_DIR" ]]; then
    echo "Error: task directory not found: $TASK_DIR" >&2
    exit 2
fi
if [[ ! -f "$TASK_DIR/prompt.txt" ]]; then
    echo "Error: missing prompt.txt in $TASK_DIR" >&2
    exit 2
fi
if [[ ! -f "$TASK_DIR/verify.sh" ]]; then
    echo "Error: missing verify.sh in $TASK_DIR" >&2
    exit 2
fi
if [[ ! -f "$TASK_DIR/meta.yaml" ]]; then
    echo "Error: missing meta.yaml in $TASK_DIR" >&2
    exit 2
fi
if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
    echo "Error: ANTHROPIC_API_KEY env var is required (--bare ignores OAuth/keychain)" >&2
    exit 2
fi

case "$EFFORT" in
    low|medium|high|xhigh|max) ;;
    *) echo "Error: invalid effort '$EFFORT' (low|medium|high|xhigh|max)" >&2; exit 2 ;;
esac

# --- Setup paths ------------------------------------------------------------
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TASK_DIR_ABS="$(cd "$TASK_DIR" && pwd)"
TASK_ID="$(basename "$TASK_DIR_ABS")"
TIMESTAMP="$(date +%s)"
RUN_ID="${TASK_ID}_${MODEL}_${EFFORT}_run${RUN_N}_${TIMESTAMP}"
RESULT_DIR="$REPO_ROOT/results/runs/$RUN_ID"

mkdir -p "$RESULT_DIR"

# --- Load task meta ---------------------------------------------------------
ALLOWED_TOOLS="$(yq -r '.allowed_tools | join(",")' "$TASK_DIR_ABS/meta.yaml")"
MAX_BUDGET_USD="${MAX_BUDGET_USD:-10}"

if [[ -z "$ALLOWED_TOOLS" || "$ALLOWED_TOOLS" == "null" ]]; then
    echo "Error: meta.yaml is missing allowed_tools list" >&2
    exit 2
fi

# --- Setup isolated working directory ---------------------------------------
WORKDIR="$(mktemp -d -t effort-test-XXXXXX)"
cleanup() { rm -rf "$WORKDIR"; }
trap cleanup EXIT

# Copy initial repo into working directory.
if [[ -d "$TASK_DIR_ABS/initial_repo" ]]; then
    cp -a "$TASK_DIR_ABS/initial_repo/." "$WORKDIR/"
elif [[ -f "$TASK_DIR_ABS/initial_repo.tar.gz" ]]; then
    tar -xzf "$TASK_DIR_ABS/initial_repo.tar.gz" -C "$WORKDIR"
else
    echo "Error: neither initial_repo/ nor initial_repo.tar.gz found in $TASK_DIR_ABS" >&2
    exit 2
fi

# Install Node deps if package.json exists and no cached node_modules.
if [[ -f "$WORKDIR/package.json" && ! -d "$WORKDIR/node_modules" ]]; then
    ( cd "$WORKDIR" && npm install --silent --no-audit --no-fund --prefer-offline ) \
        || { echo "Error: npm install failed in $WORKDIR" >&2; exit 1; }
fi

# Capture starting state via git (ephemeral repo for diff tracking only;
# disable commit signing locally — this tempdir never leaves the runner).
(
    cd "$WORKDIR"
    git init -q
    git config user.email "bench@local"
    git config user.name "bench"
    git config commit.gpgsign false
    git config gpg.format openpgp
    git add -A
    git commit -q -m "initial" --allow-empty
)

# --- Load prompt ------------------------------------------------------------
PROMPT="$(cat "$TASK_DIR_ABS/prompt.txt")"
CLAUDE_VERSION="$(claude --version 2>/dev/null | head -1 || echo 'unknown')"

# --- Execute Claude Code ----------------------------------------------------
echo "[$(date -Iseconds)] Starting run: $RUN_ID" >&2
echo "  task=$TASK_ID  model=$MODEL  effort=$EFFORT  run=$RUN_N" >&2
echo "  workdir=$WORKDIR" >&2

START_NS="$(date +%s%N)"
set +e
(
    cd "$WORKDIR"
    claude --bare -p "$PROMPT" \
        --effort "$EFFORT" \
        --model "$MODEL" \
        --output-format stream-json \
        --verbose \
        --allowedTools "$ALLOWED_TOOLS" \
        --max-budget-usd "$MAX_BUDGET_USD" \
        --permission-mode bypassPermissions \
        --no-session-persistence \
        > "$RESULT_DIR/stdout.json" \
        2> "$RESULT_DIR/stderr.log"
)
EXIT_CODE=$?
set -e
END_NS="$(date +%s%N)"
WALL_CLOCK_MS=$(( (END_NS - START_NS) / 1000000 ))

echo "[$(date -Iseconds)] Claude exited code=$EXIT_CODE wall=${WALL_CLOCK_MS}ms" >&2

# --- Capture final state ----------------------------------------------------
(
    cd "$WORKDIR"
    git add -A
    git diff --cached > "$RESULT_DIR/final_diff.patch"
    git diff --cached --stat > "$RESULT_DIR/diff_stat.txt"
) || true

# --- Run verification -------------------------------------------------------
set +e
( cd "$WORKDIR" && bash "$TASK_DIR_ABS/verify.sh" ) \
    > "$RESULT_DIR/verify_result.json" \
    2> "$RESULT_DIR/verify.log"
VERIFY_EXIT=$?
set -e

# --- Parse session JSON for metrics -----------------------------------------
set +e
python3 "$REPO_ROOT/runner/lib/parse_session.py" "$RESULT_DIR/stdout.json" \
    > "$RESULT_DIR/metrics.json" \
    2>> "$RESULT_DIR/stderr.log"
PARSE_EXIT=$?
set -e

# --- Write run_meta.json ----------------------------------------------------
cat > "$RESULT_DIR/run_meta.json" <<EOF
{
  "run_id": "$RUN_ID",
  "task": "$TASK_ID",
  "model": "$MODEL",
  "effort": "$EFFORT",
  "run_number": $RUN_N,
  "exit_code": $EXIT_CODE,
  "verify_exit_code": $VERIFY_EXIT,
  "parse_exit_code": $PARSE_EXIT,
  "wall_clock_ms": $WALL_CLOCK_MS,
  "started_at_ns": $START_NS,
  "ended_at_ns": $END_NS,
  "timestamp": "$(date -Iseconds)",
  "claude_version": "$CLAUDE_VERSION",
  "max_budget_usd": $MAX_BUDGET_USD,
  "allowed_tools": "$ALLOWED_TOOLS"
}
EOF

echo "[$(date -Iseconds)] Completed: $RUN_ID" >&2
echo "  results: $RESULT_DIR" >&2
exit 0
