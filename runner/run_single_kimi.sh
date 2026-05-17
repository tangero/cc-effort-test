#!/usr/bin/env bash
#
# POC runner for kimi-cli (kimi-k2.6).
# Fork of run_single.sh adapted for kimi-cli differences.
#
# Usage:
#   bash runner/run_single_kimi.sh <task_dir> <effort> <run_n>
#
# Effort simulation (kimi has no native --effort):
#   low  = --no-thinking, --max-steps-per-task 10
#   max  = --thinking, no step limit
#
set -euo pipefail

if [[ $# -lt 3 ]]; then
    echo "Usage: $0 <task_dir> <effort> <run_n>" >&2
    exit 2
fi

TASK_DIR="$1"
EFFORT="$2"
RUN_N="$3"
MODEL="kimi-k2.6"

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

case "$EFFORT" in
    low|medium|high|max) ;;
    *) echo "Error: invalid effort '$EFFORT' (valid: low, medium, high, max)" >&2; exit 2 ;;
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

# --- Setup isolated working directory ---------------------------------------
WORKDIR="$(mktemp -d -t effort-test-kimi-XXXXXX)"
cleanup() { rm -rf "$WORKDIR"; }
trap cleanup EXIT

if [[ -d "$TASK_DIR_ABS/initial_repo" ]]; then
    cp -a "$TASK_DIR_ABS/initial_repo/." "$WORKDIR/"
elif [[ -f "$TASK_DIR_ABS/initial_repo.tar.gz" ]]; then
    tar -xzf "$TASK_DIR_ABS/initial_repo.tar.gz" -C "$WORKDIR"
else
    echo "Error: neither initial_repo/ nor initial_repo.tar.gz found" >&2
    exit 2
fi

LANGUAGE="$(yq -r '.language // "typescript"' "$TASK_DIR_ABS/meta.yaml" 2>/dev/null || echo 'typescript')"

if [[ "$LANGUAGE" == "python" ]]; then
    PYTHON_VERSION="$(yq -r '.python_version // "3.11"' "$TASK_DIR_ABS/meta.yaml" 2>/dev/null || echo '3.11')"
    INSTALL_CMD="$(yq -r '.install_cmd // "pip install -e . -q"' "$TASK_DIR_ABS/meta.yaml" 2>/dev/null || echo 'pip install -e . -q')"
    if command -v pyenv >/dev/null 2>&1; then
        export PYENV_VERSION="$PYTHON_VERSION"
    fi
    echo "[setup] python $PYTHON_VERSION — running: $INSTALL_CMD" >&2
    ( cd "$WORKDIR" && eval "$INSTALL_CMD" ) \
        || { echo "Warning: install_cmd had errors — continuing anyway" >&2; }
elif [[ -f "$WORKDIR/package.json" && ! -d "$WORKDIR/node_modules" ]]; then
    echo "[setup] typescript — npm install" >&2
    ( cd "$WORKDIR" && npm install --silent --no-audit --no-fund --prefer-offline ) \
        || { echo "Error: npm install failed in $WORKDIR" >&2; exit 1; }
fi

# Git init for diff tracking
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
KIMI_VERSION="$(kimi --version 2>/dev/null | head -1 || echo 'unknown')"
NODE_VERSION="$(node --version 2>/dev/null | head -1 || echo 'unknown')"
PYTHON_VERSION_ACTUAL="$(python3 --version 2>/dev/null | head -1 || echo 'unknown')"
NPM_VERSION="$(npm --version 2>/dev/null | head -1 || echo 'unknown')"
UNAME="$(uname -a 2>/dev/null || echo 'unknown')"

# --- Build kimi flags based on effort ---------------------------------------
KIMI_FLAGS=()
if [[ "$EFFORT" == "low" ]]; then
    KIMI_FLAGS+=("--no-thinking")
    KIMI_FLAGS+=("--max-steps-per-turn" "10")
elif [[ "$EFFORT" == "medium" ]]; then
    KIMI_FLAGS+=("--no-thinking")
    KIMI_FLAGS+=("--max-steps-per-turn" "30")
elif [[ "$EFFORT" == "high" ]]; then
    KIMI_FLAGS+=("--thinking")
    KIMI_FLAGS+=("--max-steps-per-turn" "100")
else
    KIMI_FLAGS+=("--thinking")
    # No step limit for max
fi

# --- Execute kimi-cli -------------------------------------------------------
echo "[$(date -Iseconds)] Starting run: $RUN_ID" >&2
echo "  task=$TASK_ID  model=$MODEL  effort=$EFFORT  run=$RUN_N" >&2
echo "  workdir=$WORKDIR" >&2

START_NS="$(date +%s%N)"
set +e
(
    cd "$WORKDIR"
    kimi \
        --yolo \
        --print \
        --output-format stream-json \
        --final-message-only \
        --work-dir "$WORKDIR" \
        "${KIMI_FLAGS[@]}" \
        --prompt "$PROMPT" \
        > "$RESULT_DIR/stdout.json" \
        2> >(tee "$RESULT_DIR/stderr.log" >&2)
)
EXIT_CODE=$?
set -e
END_NS="$(date +%s%N)"
WALL_CLOCK_MS=$(( (END_NS - START_NS) / 1000000 ))

echo "[$(date -Iseconds)] kimi exited code=$EXIT_CODE wall=${WALL_CLOCK_MS}ms" >&2

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

# --- Metrics (kimi-cli doesn't expose token/cost metrics like Claude) ------
# We write a minimal metrics.json with what we know.
# Step count can be inferred from stderr if kimi logs it.
STEP_COUNT=$(grep -c '\[step\|Step\|STEP' "$RESULT_DIR/stderr.log" 2>/dev/null || echo 0)

cat > "$RESULT_DIR/metrics.json" <<EOF
{
  "model_used": "$MODEL",
  "num_turns": $STEP_COUNT,
  "stop_reason": "$(if [[ $EXIT_CODE -eq 0 ]]; then echo "success"; else echo "error"; fi)",
  "total_cost_usd": 0,
  "input_tokens": 0,
  "output_tokens": 0,
  "cache_read_input_tokens": 0,
  "cache_creation_input_tokens": 0,
  "thinking_tokens": 0,
  "tool_call_count": 0,
  "tool_call_count_by_type": {},
  "result_text_length": 0,
  "parse_errors": [],
  "session_id": ""
}
EOF

# --- Write run_meta.json ----------------------------------------------------
cat > "$RESULT_DIR/run_meta.json" <<EOF
{
  "run_id": "$RUN_ID",
  "task": "$TASK_ID",
  "provider": "kimi",
  "model": "$MODEL",
  "effort": "$EFFORT",
  "reasoning_effort": "$EFFORT",
  "run_number": $RUN_N,
  "exit_code": $EXIT_CODE,
  "verify_exit_code": $VERIFY_EXIT,
  "parse_exit_code": 0,
  "wall_clock_ms": $WALL_CLOCK_MS,
  "started_at_ns": $START_NS,
  "ended_at_ns": $END_NS,
  "timestamp": "$(date -Iseconds)",
  "kimi_version": "$KIMI_VERSION",
  "node_version": "$NODE_VERSION",
  "python_version": "$PYTHON_VERSION_ACTUAL",
  "npm_version": "$NPM_VERSION",
  "uname": "$UNAME",
  "auth_mode": "subscription"
}
EOF

echo "[$(date -Iseconds)] Completed: $RUN_ID" >&2
echo "  results: $RESULT_DIR" >&2
exit 0
