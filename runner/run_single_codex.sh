#!/usr/bin/env bash
#
# Run a single (task, reasoning_effort, run_n, model) cell with Codex CLI.
#
# Outputs the same artifact shape as runner/run_single.sh so aggregation and
# reports can compare providers without task-specific branches.
#
set -euo pipefail

if [[ $# -lt 3 ]]; then
    echo "Usage: $0 <task_dir> <effort> <run_n> [model]" >&2
    exit 2
fi

TASK_DIR="$1"
EFFORT="$2"
RUN_N="$3"
MODEL="${4:-gpt-5.5}"

if [[ ! -d "$TASK_DIR" ]]; then echo "Error: task directory not found: $TASK_DIR" >&2; exit 2; fi
if [[ ! -f "$TASK_DIR/prompt.txt" ]]; then echo "Error: missing prompt.txt in $TASK_DIR" >&2; exit 2; fi
if [[ ! -f "$TASK_DIR/verify.sh" ]]; then echo "Error: missing verify.sh in $TASK_DIR" >&2; exit 2; fi
if [[ ! -f "$TASK_DIR/meta.yaml" ]]; then echo "Error: missing meta.yaml in $TASK_DIR" >&2; exit 2; fi

case "$EFFORT" in
    low|medium|high|xhigh|max) ;;
    *) echo "Error: invalid effort '$EFFORT'" >&2; exit 2 ;;
esac

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TASK_DIR_ABS="$(cd "$TASK_DIR" && pwd)"
TASK_ID="$(basename "$TASK_DIR_ABS")"
TIMESTAMP="$(date +%s)"
RUN_ID="${TASK_ID}_${MODEL}_${EFFORT}_run${RUN_N}_${TIMESTAMP}"
RESULT_DIR="$REPO_ROOT/results/runs/$RUN_ID"
mkdir -p "$RESULT_DIR"

ALLOWED_TOOLS="$(yq -r '.allowed_tools | join(",")' "$TASK_DIR_ABS/meta.yaml")"
if [[ -z "$ALLOWED_TOOLS" || "$ALLOWED_TOOLS" == "null" ]]; then
    echo "Error: meta.yaml is missing allowed_tools list" >&2
    exit 2
fi

WORKDIR="$(mktemp -d -t effort-test-codex-XXXXXX)"
cleanup() { rm -rf "$WORKDIR"; }
trap cleanup EXIT

if [[ -d "$TASK_DIR_ABS/initial_repo" ]]; then
    cp -a "$TASK_DIR_ABS/initial_repo/." "$WORKDIR/"
elif [[ -f "$TASK_DIR_ABS/initial_repo.tar.gz" ]]; then
    tar -xzf "$TASK_DIR_ABS/initial_repo.tar.gz" -C "$WORKDIR"
else
    echo "Error: neither initial_repo/ nor initial_repo.tar.gz found in $TASK_DIR_ABS" >&2
    exit 2
fi

LANGUAGE="$(yq -r '.language // "typescript"' "$TASK_DIR_ABS/meta.yaml" 2>/dev/null || echo 'typescript')"
if [[ "$LANGUAGE" == "python" ]]; then
    PYTHON_VERSION_META="$(yq -r '.python_version // "3.11"' "$TASK_DIR_ABS/meta.yaml" 2>/dev/null || echo '3.11')"
    INSTALL_CMD="$(yq -r '.install_cmd // "pip install -e . -q"' "$TASK_DIR_ABS/meta.yaml" 2>/dev/null || echo 'pip install -e . -q')"
    if command -v pyenv >/dev/null 2>&1; then
        export PYENV_VERSION="$PYTHON_VERSION_META"
    fi
    echo "[setup] python $PYTHON_VERSION_META — running: $INSTALL_CMD" >&2
    ( cd "$WORKDIR" && eval "$INSTALL_CMD" ) \
        || { echo "Warning: install_cmd had errors — continuing anyway" >&2; }
elif [[ -f "$WORKDIR/package.json" && ! -d "$WORKDIR/node_modules" ]]; then
    echo "[setup] typescript — npm install" >&2
    ( cd "$WORKDIR" && npm install --silent --no-audit --no-fund --prefer-offline ) \
        || { echo "Error: npm install failed in $WORKDIR" >&2; exit 1; }
fi

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

PROMPT="$(cat "$TASK_DIR_ABS/prompt.txt")"
CODEX_VERSION="$(codex --version 2>/dev/null | head -1 || echo 'unknown')"
NODE_VERSION="$(node --version 2>/dev/null | head -1 || echo 'unknown')"
PYTHON_VERSION_ACTUAL="$(python3 --version 2>/dev/null | head -1 || echo 'unknown')"
NPM_VERSION="$(npm --version 2>/dev/null | head -1 || echo 'unknown')"
UNAME="$(uname -a 2>/dev/null || echo 'unknown')"
USER_CODEX_CONFIG_PRESENT="false"
if [[ -f "$HOME/.codex/config.toml" && -s "$HOME/.codex/config.toml" ]]; then
    USER_CODEX_CONFIG_PRESENT="true"
fi

echo "[$(date -Iseconds)] Starting Codex run: $RUN_ID" >&2
echo "  task=$TASK_ID  model=$MODEL  effort=$EFFORT  run=$RUN_N" >&2
echo "  workdir=$WORKDIR" >&2

START_NS="$(date +%s%N)"
set +e
(
    cd "$WORKDIR"
    codex exec \
        --json \
        --ephemeral \
        --ignore-user-config \
        --ignore-rules \
        --skip-git-repo-check \
        -C "$WORKDIR" \
        -m "$MODEL" \
        -c "model_reasoning_effort=\"$EFFORT\"" \
        -s danger-full-access \
        -a never \
        "$PROMPT" \
        > "$RESULT_DIR/stdout.json" \
        2> >(tee "$RESULT_DIR/stderr.log" >&2)
)
EXIT_CODE=$?
set -e
END_NS="$(date +%s%N)"
WALL_CLOCK_MS=$(( (END_NS - START_NS) / 1000000 ))

echo "[$(date -Iseconds)] Codex exited code=$EXIT_CODE wall=${WALL_CLOCK_MS}ms" >&2

(
    cd "$WORKDIR"
    git add -A
    git diff --cached > "$RESULT_DIR/final_diff.patch"
    git diff --cached --stat > "$RESULT_DIR/diff_stat.txt"
) || true

set +e
( cd "$WORKDIR" && bash "$TASK_DIR_ABS/verify.sh" ) \
    > "$RESULT_DIR/verify_result.json" \
    2> "$RESULT_DIR/verify.log"
VERIFY_EXIT=$?
set -e

set +e
python3 "$REPO_ROOT/runner/lib/parse_codex_session.py" "$RESULT_DIR/stdout.json" \
    > "$RESULT_DIR/metrics.json" \
    2>> "$RESULT_DIR/stderr.log"
PARSE_EXIT=$?
set -e

cat > "$RESULT_DIR/run_meta.json" <<EOF
{
  "run_id": "$RUN_ID",
  "task": "$TASK_ID",
  "provider": "codex",
  "model": "$MODEL",
  "effort": "$EFFORT",
  "reasoning_effort": "$EFFORT",
  "run_number": $RUN_N,
  "exit_code": $EXIT_CODE,
  "verify_exit_code": $VERIFY_EXIT,
  "parse_exit_code": $PARSE_EXIT,
  "wall_clock_ms": $WALL_CLOCK_MS,
  "started_at_ns": $START_NS,
  "ended_at_ns": $END_NS,
  "timestamp": "$(date -Iseconds)",
  "codex_version": "$CODEX_VERSION",
  "node_version": "$NODE_VERSION",
  "python_version": "$PYTHON_VERSION_ACTUAL",
  "npm_version": "$NPM_VERSION",
  "uname": "$UNAME",
  "user_config_present": $USER_CODEX_CONFIG_PRESENT,
  "matrix_seed": "${MATRIX_SEED:-}",
  "matrix_manifest": "${MATRIX_MANIFEST:-}",
  "matrix_index": "${MATRIX_INDEX:-}",
  "allowed_tools": "$ALLOWED_TOOLS"
}
EOF

echo "[$(date -Iseconds)] Completed: $RUN_ID" >&2
echo "  results: $RESULT_DIR" >&2
exit 0
