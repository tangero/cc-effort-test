#!/usr/bin/env bash
#
# Verify Task 03 (debug order — two bugs).
#
# Run from inside the working copy of the task (runner cd's into workdir).
# Emits JSON on stdout. Exit 0 if all checks pass, 1 otherwise.
#
set -uo pipefail

TASK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HIDDEN_TEST_SRC="$TASK_DIR/hidden_tests/order.hidden.test.ts"
HIDDEN_TEST_DEST="src/__tests__/order.hidden.test.ts"

# --- Check 1: TypeScript compiles -----------------------------------------
TSC_OUTPUT="$(npx --no-install tsc --noEmit 2>&1)"
TSC_EXIT=$?
if [[ $TSC_EXIT -eq 0 ]]; then
    CHECK_TSC='{"passed": true, "details": "tsc --noEmit exit 0"}'
else
    TSC_ESC=$(printf '%s' "$TSC_OUTPUT" | head -20 | jq -Rs '.')
    CHECK_TSC=$(printf '{"passed": false, "details": %s}' "$TSC_ESC")
fi

# --- Check 2: Model's own tests pass --------------------------------------
JEST_OWN="$(npx --no-install jest src/__tests__/order.test.ts --silent 2>&1)"
JEST_OWN_EXIT=$?
if [[ $JEST_OWN_EXIT -eq 0 ]]; then
    CHECK_OWN='{"passed": true, "details": "all 3 visible tests pass"}'
else
    OWN_ESC=$(printf '%s' "$JEST_OWN" | tail -20 | jq -Rs '.')
    CHECK_OWN=$(printf '{"passed": false, "details": %s}' "$OWN_ESC")
fi

# --- Check 3: PriceCalculator.ts was modified (Bug A fixed) ---------------
CALC_DIFF="$(git diff HEAD -- src/pricing/PriceCalculator.ts 2>/dev/null | wc -l | tr -d ' ')"
if [[ "${CALC_DIFF:-0}" -gt 0 ]]; then
    CHECK_CALC=$(printf '{"passed": true, "details": "%s diff lines in PriceCalculator.ts"}' "$CALC_DIFF")
else
    CHECK_CALC='{"passed": false, "details": "PriceCalculator.ts was not modified — Bug A likely not fixed"}'
fi

# --- Check 4: OrderService.ts was modified (Bug B fixed) ------------------
ORDER_DIFF="$(git diff HEAD -- src/orders/OrderService.ts 2>/dev/null | wc -l | tr -d ' ')"
if [[ "${ORDER_DIFF:-0}" -gt 0 ]]; then
    CHECK_ORDER=$(printf '{"passed": true, "details": "%s diff lines in OrderService.ts"}' "$ORDER_DIFF")
else
    CHECK_ORDER='{"passed": false, "details": "OrderService.ts was not modified — Bug B likely not fixed"}'
fi

# --- Check 5: Hidden tests pass -------------------------------------------
cp "$HIDDEN_TEST_SRC" "$HIDDEN_TEST_DEST"
JEST_HIDDEN="$(npx --no-install jest "$HIDDEN_TEST_DEST" --silent 2>&1)"
JEST_HIDDEN_EXIT=$?
rm -f "$HIDDEN_TEST_DEST"
if [[ $JEST_HIDDEN_EXIT -eq 0 ]]; then
    CHECK_HIDDEN='{"passed": true, "details": "all 3 hidden test cases pass"}'
else
    HIDDEN_ESC=$(printf '%s' "$JEST_HIDDEN" | tail -30 | jq -Rs '.')
    CHECK_HIDDEN=$(printf '{"passed": false, "details": %s}' "$HIDDEN_ESC")
fi

# --- Score ----------------------------------------------------------------
PASSED=0
TOTAL=5
for c in "$CHECK_TSC" "$CHECK_OWN" "$CHECK_CALC" "$CHECK_ORDER" "$CHECK_HIDDEN"; do
    if echo "$c" | jq -e '.passed == true' >/dev/null 2>&1; then
        PASSED=$((PASSED + 1))
    fi
done

SCORE=$(awk -v p="$PASSED" -v t="$TOTAL" 'BEGIN { printf "%.4f", p / t }')
if [[ "$PASSED" -eq "$TOTAL" ]]; then SUCCESS="true"; else SUCCESS="false"; fi

cat <<EOF
{
  "success": $SUCCESS,
  "score": $SCORE,
  "checks": {
    "tsc_compiles":           $CHECK_TSC,
    "own_tests_pass":         $CHECK_OWN,
    "price_calculator_fixed": $CHECK_CALC,
    "order_service_fixed":    $CHECK_ORDER,
    "hidden_tests_pass":      $CHECK_HIDDEN
  }
}
EOF

if [[ "$SUCCESS" == "true" ]]; then exit 0; else exit 1; fi
