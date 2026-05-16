#!/usr/bin/env bash
set -uo pipefail

TASK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PASS=0; TOTAL=5

# TypeScript check
TSC_OUT="$(npx tsc --noEmit 2>&1)"
if [[ $? -ne 0 ]]; then
  ESC=$(printf '%s' "$TSC_OUT" | tail -5 | jq -Rs '.')
  cat <<EOF
{"success": false, "score": 0.0, "checks": {"tsc": {"passed": false, "details": $ESC}, "hidden": {"passed": false, "details": "skipped due to tsc error"}}}
EOF
  exit 1
fi

# Copy hidden tests, run, delete
cp "$TASK_DIR/hidden_tests/async.test.ts" src/
JEST_OUT="$(npx jest --testPathPattern='async\.test\.ts' --verbose --forceExit 2>&1)"
JEST_EXIT=$?
rm -f src/async.test.ts

# Count passed tests
PASSED=$(echo "$JEST_OUT" | grep -c '✓\|✔\|√\| ✓ \| ✔ ' 2>/dev/null || echo 0)
FAILED=$(echo "$JEST_OUT" | grep -c '✕\|✗\|×\| ✕ \| ✗ ' 2>/dev/null || echo 0)

if [[ $JEST_EXIT -eq 0 ]]; then
  PASS=5
fi

# Try to get individual results
get_check() {
  local pattern="$1"
  local name="$2"
  if echo "$JEST_OUT" | grep -qE "[✓✔√] .*$pattern"; then
    echo "{\"passed\": true, \"details\": \"$name passed\"}"
  else
    echo "{\"passed\": false, \"details\": \"$name failed\"}"
  fi
}

C1=$(get_check "processSingle" "processSingle correct result")
C2=$(get_check "parallel" "processBatch parallel")
C3=$(get_check "propagates" "safeProcess propagates errors")
C4=$(get_check "race" "incrementAndGet race-free")
C5=$(get_check "combined" "processBatch correct values")

# Recount based on individual checks
PASS=0
for c in "$C1" "$C2" "$C3" "$C4" "$C5"; do
  if echo "$c" | grep -q '"passed": true'; then PASS=$((PASS+1)); fi
done

SCORE=$(awk -v p="$PASS" -v t="$TOTAL" 'BEGIN{printf "%.4f", p/t}')
[[ "$PASS" -eq "$TOTAL" ]] && SUCCESS="true" || SUCCESS="false"
cat <<EOF
{"success": $SUCCESS, "score": $SCORE, "checks": {"processSingle": $C1, "processBatch_parallel": $C2, "safeProcess_errors": $C3, "race_condition": $C4, "processBatch_values": $C5}}
EOF
[[ "$SUCCESS" == "true" ]] && exit 0 || exit 1
