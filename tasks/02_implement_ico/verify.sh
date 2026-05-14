#!/usr/bin/env bash
#
# Verify Task 02 (implement IČO validation).
#
# Run from inside the working copy of the task (runner cd's into the
# tempdir before invoking us). Emits a JSON document on stdout.
#
# Exit code: 0 if all checks pass, 1 otherwise.
#
set -uo pipefail

TASK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HIDDEN_TEST_SRC="$TASK_DIR/hidden_tests/ico.hidden.test.ts"
HIDDEN_TEST_DEST="src/validators/ico.hidden.test.ts"

# --- Check 1: ico.ts exists ------------------------------------------------
if [[ -f "src/validators/ico.ts" ]]; then
    CHECK_ICO_TS='{"passed": true, "details": "src/validators/ico.ts exists"}'
else
    CHECK_ICO_TS='{"passed": false, "details": "src/validators/ico.ts not found"}'
fi

# --- Check 2: ico.test.ts exists -------------------------------------------
if [[ -f "src/validators/ico.test.ts" ]]; then
    CHECK_ICO_TEST='{"passed": true, "details": "src/validators/ico.test.ts exists"}'
else
    CHECK_ICO_TEST='{"passed": false, "details": "src/validators/ico.test.ts not found"}'
fi

# --- Check 3: TypeScript compiles ------------------------------------------
TSC_OUTPUT="$(npx --no-install tsc --noEmit 2>&1)"
TSC_EXIT=$?
if [[ $TSC_EXIT -eq 0 ]]; then
    CHECK_TSC='{"passed": true, "details": "tsc --noEmit exit 0"}'
else
    TSC_ESC=$(printf '%s' "$TSC_OUTPUT" | head -20 | jq -Rs '.')
    CHECK_TSC=$(printf '{"passed": false, "details": %s}' "$TSC_ESC")
fi

# --- Check 4: Model's own tests pass ---------------------------------------
if [[ -f "src/validators/ico.test.ts" ]]; then
    JEST_OWN_OUTPUT="$(npx --no-install jest src/validators/ico.test.ts --silent 2>&1)"
    JEST_OWN_EXIT=$?
else
    JEST_OWN_OUTPUT="ico.test.ts not found"
    JEST_OWN_EXIT=1
fi
if [[ $JEST_OWN_EXIT -eq 0 ]]; then
    CHECK_OWN='{"passed": true, "details": "model own tests pass"}'
else
    OWN_ESC=$(printf '%s' "$JEST_OWN_OUTPUT" | tail -20 | jq -Rs '.')
    CHECK_OWN=$(printf '{"passed": false, "details": %s}' "$OWN_ESC")
fi

# --- Check 5: Hidden test suite passes -------------------------------------
cp "$HIDDEN_TEST_SRC" "$HIDDEN_TEST_DEST"
JEST_HIDDEN_OUTPUT="$(npx --no-install jest "$HIDDEN_TEST_DEST" --silent 2>&1)"
JEST_HIDDEN_EXIT=$?
rm -f "$HIDDEN_TEST_DEST"
if [[ $JEST_HIDDEN_EXIT -eq 0 ]]; then
    CHECK_HIDDEN='{"passed": true, "details": "all 9 hidden test cases pass"}'
else
    HIDDEN_ESC=$(printf '%s' "$JEST_HIDDEN_OUTPUT" | tail -30 | jq -Rs '.')
    CHECK_HIDDEN=$(printf '{"passed": false, "details": %s}' "$HIDDEN_ESC")
fi

# --- Score -----------------------------------------------------------------
PASSED=0
TOTAL=5
for c in "$CHECK_ICO_TS" "$CHECK_ICO_TEST" "$CHECK_TSC" "$CHECK_OWN" "$CHECK_HIDDEN"; do
    if echo "$c" | jq -e '.passed == true' >/dev/null 2>&1; then
        PASSED=$((PASSED + 1))
    fi
done

SCORE=$(awk -v p="$PASSED" -v t="$TOTAL" 'BEGIN { printf "%.4f", p / t }')
if [[ "$PASSED" -eq "$TOTAL" ]]; then
    SUCCESS="true"
else
    SUCCESS="false"
fi

cat <<EOF
{
  "success": $SUCCESS,
  "score": $SCORE,
  "checks": {
    "ico_ts_exists":      $CHECK_ICO_TS,
    "ico_test_ts_exists": $CHECK_ICO_TEST,
    "tsc_compiles":       $CHECK_TSC,
    "own_tests_pass":     $CHECK_OWN,
    "hidden_tests_pass":  $CHECK_HIDDEN
  }
}
EOF

if [[ "$SUCCESS" == "true" ]]; then exit 0; else exit 1; fi
