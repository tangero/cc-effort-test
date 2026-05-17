#!/usr/bin/env bash
set -uo pipefail

TASK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HIDDEN_DEST="src/__tests__"

TSC_OUT="$(npx --no-install tsc --noEmit 2>&1)"
if [[ $? -eq 0 ]]; then CHECK_TSC='{"passed": true, "details": "tsc --noEmit exit 0"}'; else ESC=$(printf '%s' "$TSC_OUT" | tail -20 | jq -Rs '.'); CHECK_TSC=$(printf '{"passed": false, "details": %s}' "$ESC"); fi
OWN_OUT="$(npx --no-install jest --testPathPattern='src/.*\.test\.ts$' --silent 2>&1)"
if [[ $? -eq 0 ]]; then CHECK_OWN='{"passed": true, "details": "visible tests pass"}'; else ESC=$(printf '%s' "$OWN_OUT" | tail -20 | jq -Rs '.'); CHECK_OWN=$(printf '{"passed": false, "details": %s}' "$ESC"); fi
mkdir -p "$HIDDEN_DEST"
cp "$TASK_DIR"/hidden_tests/*.test.ts "$HIDDEN_DEST"/
HIDDEN_OUT="$(npx --no-install jest "$HIDDEN_DEST" --silent 2>&1)"
HIDDEN_EXIT=$?
rm -rf "$HIDDEN_DEST"
if [[ $HIDDEN_EXIT -eq 0 ]]; then CHECK_HIDDEN='{"passed": true, "details": "hidden tests pass"}'; else ESC=$(printf '%s' "$HIDDEN_OUT" | tail -30 | jq -Rs '.'); CHECK_HIDDEN=$(printf '{"passed": false, "details": %s}' "$ESC"); fi
TEST_DIFF="$(git diff HEAD --name-only -- 'src/**/*.test.ts' 2>/dev/null || true)"
if [[ -z "$TEST_DIFF" ]]; then CHECK_SCOPE='{"passed": true, "details": "test files untouched"}'; SCOPE_SCORE="1.0000"; else ESC=$(printf '%s' "$TEST_DIFF" | jq -Rs '.'); CHECK_SCOPE=$(printf '{"passed": false, "details": %s}' "$ESC"); SCOPE_SCORE="0.0000"; fi
PASSED=0; TOTAL=4
for c in "$CHECK_TSC" "$CHECK_OWN" "$CHECK_HIDDEN" "$CHECK_SCOPE"; do echo "$c" | jq -e '.passed == true' >/dev/null 2>&1 && PASSED=$((PASSED+1)); done
FUNCTIONAL_PASSED=0; FUNCTIONAL_TOTAL=3
for c in "$CHECK_TSC" "$CHECK_OWN" "$CHECK_HIDDEN"; do echo "$c" | jq -e '.passed == true' >/dev/null 2>&1 && FUNCTIONAL_PASSED=$((FUNCTIONAL_PASSED+1)); done
SCORE=$(awk -v p="$PASSED" -v t="$TOTAL" 'BEGIN{printf "%.4f", p/t}')
FUNCTIONAL_SCORE=$(awk -v p="$FUNCTIONAL_PASSED" -v t="$FUNCTIONAL_TOTAL" 'BEGIN{printf "%.4f", p/t}')
[[ "$PASSED" -eq "$TOTAL" ]] && SUCCESS="true" || SUCCESS="false"
cat <<EOF
{"success": $SUCCESS, "score": $SCORE, "functional_score": $FUNCTIONAL_SCORE, "scope_score": $SCOPE_SCORE, "checks": {"tsc_compiles": $CHECK_TSC, "visible_tests_pass": $CHECK_OWN, "hidden_tests_pass": $CHECK_HIDDEN, "test_files_untouched": $CHECK_SCOPE}}
EOF
[[ "$SUCCESS" == "true" ]] && exit 0 || exit 1
