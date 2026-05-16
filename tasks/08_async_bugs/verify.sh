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

# Copy hidden tests, run with JSON reporter, delete
cp "$TASK_DIR/hidden_tests/async.test.ts" src/
JEST_OUT="$(npx jest --testPathPattern='async\.test\.ts' --json --forceExit 2>/dev/null || true)"
rm -f src/async.test.ts

# Parse Jest JSON output for individual test results
test_passed() {
  local pattern="$1"
  # Jest JSON: testResults[].testResults[].{fullName, status}
  echo "$JEST_OUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
pattern = '$pattern'
for suite in data.get('testResults', []):
  for t in suite.get('assertionResults', []):
    if pattern.lower() in t.get('fullName','').lower():
      print('pass' if t.get('status') == 'passed' else 'fail')
      sys.exit(0)
print('fail')
" 2>/dev/null || echo "fail"
}

r1=$(test_passed "processSingle")
r2=$(test_passed "parallel")
r3=$(test_passed "propagates")
r4=$(test_passed "race")
r5=$(test_passed "combined")

make_check() {
  local result="$1"; local name="$2"
  if [[ "$result" == "pass" ]]; then
    echo "{\"passed\": true, \"details\": \"$name\"}"
  else
    echo "{\"passed\": false, \"details\": \"$name\"}"
  fi
}

C1=$(make_check "$r1" "processSingle correct result")
C2=$(make_check "$r2" "processBatch parallel")
C3=$(make_check "$r3" "safeProcess propagates errors")
C4=$(make_check "$r4" "incrementAndGet race-free")
C5=$(make_check "$r5" "processBatch correct values")

for r in "$r1" "$r2" "$r3" "$r4" "$r5"; do
  [[ "$r" == "pass" ]] && PASS=$((PASS+1))
done

SCORE=$(awk -v p="$PASS" -v t="$TOTAL" 'BEGIN{printf "%.4f", p/t}')
[[ "$PASS" -eq "$TOTAL" ]] && SUCCESS="true" || SUCCESS="false"
cat <<EOF
{"success": $SUCCESS, "score": $SCORE, "checks": {"processSingle": $C1, "processBatch_parallel": $C2, "safeProcess_errors": $C3, "race_condition": $C4, "processBatch_values": $C5}}
EOF
[[ "$SUCCESS" == "true" ]] && exit 0 || exit 1
