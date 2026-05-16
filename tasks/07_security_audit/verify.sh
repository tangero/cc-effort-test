#!/usr/bin/env bash
#
# Verify Task 07 (security_audit — five security bugs).
#
# Run from inside the working copy of the task (runner cd's into workdir).
# Emits JSON on stdout. Exit 0 if all checks pass, 1 otherwise.
#
set -uo pipefail

TASK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HIDDEN_TEST_SRC="$TASK_DIR/hidden_tests/security.test.ts"
HIDDEN_TEST_DEST="src/routes/security.test.ts"

# Ensure node v22 is used (better-sqlite3 prebuilt requires it)
# If NVM is available prefer node v22 over any system node that might be v24+
if [[ -d "$HOME/.nvm/versions/node/v22.22.1/bin" ]]; then
  export PATH="$HOME/.nvm/versions/node/v22.22.1/bin:$PATH"
elif [[ -d "$HOME/.nvm/versions/node/v22.22.0/bin" ]]; then
  export PATH="$HOME/.nvm/versions/node/v22.22.0/bin:$PATH"
fi

NPX="npx --no-install"

# --- Check 1: TypeScript compiles -----------------------------------------
TSC_OUTPUT="$($NPX tsc --noEmit 2>&1)"
TSC_EXIT=$?
if [[ $TSC_EXIT -eq 0 ]]; then
  CHECK_TSC='{"passed": true, "details": "tsc --noEmit exit 0"}'
else
  TSC_ESC=$(printf '%s' "$TSC_OUTPUT" | head -20 | jq -Rs '.')
  CHECK_TSC=$(printf '{"passed": false, "details": %s}' "$TSC_ESC")
fi

# --- Check 2: Visible tests still pass ------------------------------------
JEST_OWN="$($NPX jest --testPathPattern='src/routes/users\.test\.ts$' --silent 2>&1)"
JEST_OWN_EXIT=$?
if [[ $JEST_OWN_EXIT -eq 0 ]]; then
  CHECK_OWN='{"passed": true, "details": "all 3 visible tests pass"}'
else
  OWN_ESC=$(printf '%s' "$JEST_OWN" | tail -20 | jq -Rs '.')
  CHECK_OWN=$(printf '{"passed": false, "details": %s}' "$OWN_ESC")
fi

# --- Checks 3-7: Hidden security tests ------------------------------------
cp "$HIDDEN_TEST_SRC" "$HIDDEN_TEST_DEST"
JEST_OUT="$($NPX jest --testPathPattern='src/routes/security\.test\.ts$' --verbose 2>&1)"
JEST_EXIT=$?
rm -f "$HIDDEN_TEST_DEST"

# Helper: check if a specific test name passed in jest --verbose output
check_test_passed() {
  local pattern="$1"
  # If jest exited 0, all tests passed
  if [[ $JEST_EXIT -eq 0 ]]; then
    return 0
  fi
  # Look for passing test line (✓ or ✔ followed by the test pattern)
  if printf '%s' "$JEST_OUT" | grep -qE '^\s*(✓|✔|√)\s+'"$pattern"; then
    return 0
  fi
  return 1
}

build_check() {
  local pattern="$1"
  local label="$2"
  if check_test_passed "$pattern"; then
    printf '{"passed": true, "details": "%s"}' "$label"
  else
    local detail
    detail=$(printf '%s' "$JEST_OUT" | grep -A 5 "$pattern" | head -6 | jq -Rs '.')
    printf '{"passed": false, "details": %s}' "${detail:-\"$label failed\"}"
  fi
}

# If all hidden tests passed at once
if [[ $JEST_EXIT -eq 0 ]]; then
  CHECK_SQL_SEARCH='{"passed": true, "details": "SQL injection search blocked"}'
  CHECK_SQL_LOGIN='{"passed": true, "details": "SQL injection login blocked"}'
  CHECK_PWD='{"passed": true, "details": "Password not exposed in GET /users/:id"}'
  CHECK_XSS='{"passed": true, "details": "XSS prevented in register error response"}'
  CHECK_MASS='{"passed": true, "details": "Mass assignment of role blocked"}'
else
  CHECK_SQL_SEARCH=$(build_check "SQL injection in search is blocked" "SQL injection search blocked")
  CHECK_SQL_LOGIN=$(build_check "SQL injection in login is blocked" "SQL injection login blocked")
  CHECK_PWD=$(build_check "does not return password" "Password not exposed in GET /users/:id")
  CHECK_XSS=$(build_check "does not reflect XSS" "XSS prevented in register error response")
  CHECK_MASS=$(build_check "ignores role field" "Mass assignment of role blocked")
fi

# --- Score ----------------------------------------------------------------
PASSED=0
TOTAL=5
for c in "$CHECK_SQL_SEARCH" "$CHECK_SQL_LOGIN" "$CHECK_PWD" "$CHECK_XSS" "$CHECK_MASS"; do
  if printf '%s' "$c" | jq -e '.passed == true' >/dev/null 2>&1; then
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
    "sql_injection_search": $CHECK_SQL_SEARCH,
    "sql_injection_login":  $CHECK_SQL_LOGIN,
    "password_exposure":    $CHECK_PWD,
    "xss_register":         $CHECK_XSS,
    "mass_assignment_role": $CHECK_MASS
  }
}
EOF

if [[ "$SUCCESS" == "true" ]]; then exit 0; else exit 1; fi
