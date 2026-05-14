#!/usr/bin/env bash
#
# Validate a task's verify.sh against its expected_solution/.
#
# Usage:
#   bash scripts/validate_verifier.sh <task_dir>
#
# The expected_solution/ directory must contain the bit-by-bit correct
# answer that the model would ideally produce. We copy it into a tempdir,
# run verify.sh against it, and require success=true. This guards against
# verify.sh bit-rot (e.g. when refactoring initial_repo, the verifier may
# accidentally become unsatisfiable).
#
# Phase 2 extension: also run against wrong_solution/ and require success=false.
#
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <task_dir>" >&2
    exit 2
fi

TASK_DIR="$1"
if [[ ! -d "$TASK_DIR" ]]; then
    echo "Error: task directory not found: $TASK_DIR" >&2
    exit 2
fi
if [[ ! -d "$TASK_DIR/expected_solution" ]]; then
    echo "Error: missing expected_solution/ in $TASK_DIR" >&2
    exit 2
fi
if [[ ! -f "$TASK_DIR/verify.sh" ]]; then
    echo "Error: missing verify.sh in $TASK_DIR" >&2
    exit 2
fi

TASK_DIR_ABS="$(cd "$TASK_DIR" && pwd)"

WORKDIR="$(mktemp -d -t verifier-validate-XXXXXX)"
cleanup() { rm -rf "$WORKDIR"; }
trap cleanup EXIT

cp -a "$TASK_DIR_ABS/expected_solution/." "$WORKDIR/"

# Bring in cached node_modules from initial_repo if present (saves install time).
if [[ ! -d "$WORKDIR/node_modules" && -d "$TASK_DIR_ABS/initial_repo/node_modules" ]]; then
    cp -a "$TASK_DIR_ABS/initial_repo/node_modules" "$WORKDIR/node_modules"
fi

# Otherwise install from scratch.
if [[ -f "$WORKDIR/package.json" && ! -d "$WORKDIR/node_modules" ]]; then
    echo "[validate] running npm install in tempdir (first run; will be slow)..." >&2
    ( cd "$WORKDIR" && npm install --no-audit --no-fund 2>&1 | tail -5 ) \
        || { echo "Error: npm install failed" >&2; exit 1; }
fi

# Init git so verify.sh can compute diff_lines (no-op since no changes vs initial).
(
    cd "$WORKDIR"
    git init -q
    git config user.email "validate@local"
    git config user.name "validate"
    git config commit.gpgsign false
    git config gpg.format openpgp
    git add -A
    git commit -q -m "expected" --allow-empty
)

echo "[validate] running verify.sh against expected_solution/..." >&2
set +e
VERIFY_OUTPUT="$( cd "$WORKDIR" && bash "$TASK_DIR_ABS/verify.sh" )"
VERIFY_EXIT=$?
set -e

echo "$VERIFY_OUTPUT" | jq .
echo ""

if [[ $VERIFY_EXIT -eq 0 ]] && echo "$VERIFY_OUTPUT" | jq -e '.success == true' >/dev/null; then
    echo "[validate] PASS — verify.sh accepts expected_solution/ (exit=$VERIFY_EXIT, success=true)" >&2
    exit 0
fi

echo "[validate] FAIL — verify.sh rejected expected_solution/ (exit=$VERIFY_EXIT)" >&2
echo "[validate]   This means either expected_solution/ is wrong, or verify.sh has a bug." >&2
exit 1
