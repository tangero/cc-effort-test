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
# Auth: defaults to subscription mode (OAuth/keychain via `claude /login`).
# If ANTHROPIC_API_KEY is set in env, Claude Code uses it instead (pay-per-token).
# Either way, auth_mode is recorded in run_meta.json.
#
# Outputs into results/runs/<run_id>/:
#   stdout.json          - raw Claude Code stream-json output (NDJSON)
#   stderr.log           - stderr stream
#   final_diff.patch     - git diff between initial and final state
#   diff_stat.txt        - git diff --stat
#   verify_result.json   - output of tasks/<id>/verify.sh
#   verify.log           - stderr of verify.sh
#   run_meta.json        - timing, exit code, claude version, auth_mode
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

# Subscription mode: Claude Code uses OAuth/keychain. ANTHROPIC_API_KEY is
# only needed if you want pay-per-token API auth. Warn about residual
# state that subscription mode cannot fully suppress.
if [[ -f "$HOME/.claude/CLAUDE.md" ]] && [[ -s "$HOME/.claude/CLAUDE.md" ]]; then
    echo "Warning: ~/.claude/CLAUDE.md is non-empty; it will be auto-loaded into" >&2
    echo "         every run and may pollute results. Consider temporarily moving it" >&2
    echo "         aside before running the matrix (mv ~/.claude/CLAUDE.md{,.bench-bak})." >&2
fi

case "$MODEL" in
    *opus-4-7*) _valid_efforts="low|medium|high|xhigh|max" ;;
    *)          _valid_efforts="low|medium|high|max" ;;
esac
case "$EFFORT" in
    low|medium|high|xhigh|max) ;;
    *) echo "Error: invalid effort '$EFFORT'" >&2; exit 2 ;;
esac
if [[ ! "$EFFORT" =~ ^($_valid_efforts)$ ]]; then
    echo "Error: effort '$EFFORT' not supported for model '$MODEL' (valid: ${_valid_efforts//|/, })" >&2
    exit 2
fi

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

# Language-aware dependency setup.
LANGUAGE="$(yq -r '.language // "typescript"' "$TASK_DIR_ABS/meta.yaml" 2>/dev/null || echo 'typescript')"

if [[ "$LANGUAGE" == "python" ]]; then
    PYTHON_VERSION="$(yq -r '.python_version // "3.11"' "$TASK_DIR_ABS/meta.yaml" 2>/dev/null || echo '3.11')"
    INSTALL_CMD="$(yq -r '.install_cmd // "pip install -e . -q"' "$TASK_DIR_ABS/meta.yaml" 2>/dev/null || echo 'pip install -e . -q')"
    if command -v pyenv >/dev/null 2>&1; then
        export PYENV_VERSION="$PYTHON_VERSION"
    fi
    echo "[setup] python $PYTHON_VERSION — running: $INSTALL_CMD" >&2
    # Python install failures are non-fatal: complex envs (C-extensions, missing
    # system libs) often fail partially; we still want benchmark data.
    ( cd "$WORKDIR" && eval "$INSTALL_CMD" ) \
        || { echo "Warning: install_cmd had errors — continuing anyway" >&2; }
elif [[ -f "$WORKDIR/package.json" && ! -d "$WORKDIR/node_modules" ]]; then
    echo "[setup] typescript — npm install" >&2
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
NODE_VERSION="$(node --version 2>/dev/null | head -1 || echo 'unknown')"
PYTHON_VERSION_ACTUAL="$(python3 --version 2>/dev/null | head -1 || echo 'unknown')"
NPM_VERSION="$(npm --version 2>/dev/null | head -1 || echo 'unknown')"
UNAME="$(uname -a 2>/dev/null || echo 'unknown')"
USER_CLAUDE_MD_PRESENT="false"
if [[ -f "$HOME/.claude/CLAUDE.md" && -s "$HOME/.claude/CLAUDE.md" ]]; then
    USER_CLAUDE_MD_PRESENT="true"
fi

# --- Execute Claude Code ----------------------------------------------------
echo "[$(date -Iseconds)] Starting run: $RUN_ID" >&2
echo "  task=$TASK_ID  model=$MODEL  effort=$EFFORT  run=$RUN_N" >&2
echo "  workdir=$WORKDIR" >&2

# Subscription mode invocation. Isolation flags substitute for what --bare
# would have done in API-key mode:
#   --setting-sources project   skip user-level ~/.claude/settings.json
#   --strict-mcp-config + empty --mcp-config   disable all MCP servers
#   --disable-slash-commands    skip skills (otherwise loaded from user dir)
#   --agents '{}'               no custom agents
#   --no-session-persistence    don't write session to ~/.claude
# Residual state we cannot suppress without --bare: ~/.claude/CLAUDE.md
# auto-discovery, plugin sync, hooks. See README § Isolation caveats.
START_NS="$(date +%s%N)"
set +e
(
    cd "$WORKDIR"
    claude -p "$PROMPT" \
        --effort "$EFFORT" \
        --model "$MODEL" \
        --output-format stream-json \
        --verbose \
        --allowedTools "$ALLOWED_TOOLS" \
        --max-budget-usd "$MAX_BUDGET_USD" \
        --permission-mode bypassPermissions \
        --no-session-persistence \
        --setting-sources project \
        --strict-mcp-config \
        --mcp-config '{"mcpServers": {}}' \
        --disable-slash-commands \
        --agents '{}' \
        > "$RESULT_DIR/stdout.json" \
        2> >(tee "$RESULT_DIR/stderr.log" >&2)
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
# Auth mode: subscription (OAuth/keychain) if no API key in env; api-key otherwise.
if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
    AUTH_MODE="api-key"
else
    AUTH_MODE="subscription"
fi

cat > "$RESULT_DIR/run_meta.json" <<EOF
{
  "run_id": "$RUN_ID",
  "task": "$TASK_ID",
  "provider": "claude",
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
  "claude_version": "$CLAUDE_VERSION",
  "node_version": "$NODE_VERSION",
  "python_version": "$PYTHON_VERSION_ACTUAL",
  "npm_version": "$NPM_VERSION",
  "uname": "$UNAME",
  "user_config_present": $USER_CLAUDE_MD_PRESENT,
  "matrix_seed": "${MATRIX_SEED:-}",
  "matrix_manifest": "${MATRIX_MANIFEST:-}",
  "matrix_index": "${MATRIX_INDEX:-}",
  "max_budget_usd": $MAX_BUDGET_USD,
  "allowed_tools": "$ALLOWED_TOOLS",
  "auth_mode": "$AUTH_MODE"
}
EOF

echo "[$(date -Iseconds)] Completed: $RUN_ID" >&2
echo "  results: $RESULT_DIR" >&2
exit 0
