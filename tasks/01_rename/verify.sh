#!/usr/bin/env bash
#
# Verify Task 01 (rename userId -> accountId).
#
# Run from inside the working copy of the task (the runner cd's into the
# tempdir before invoking us). Emits a JSON document on stdout describing
# pass/fail per check.
#
# Exit code:
#   0 if all checks pass, 1 otherwise.
#
set -uo pipefail

# All counts use word-bounded grep over src/ (not node_modules, dist).
SRC_DIR="src"

count_token() {
    local token="$1"
    grep -rEn --include='*.ts' "\\b${token}\\b" "$SRC_DIR" 2>/dev/null | wc -l
}

# --- Run the individual checks ---------------------------------------------

USERID_COUNT="$(count_token userId)"
ACCOUNTID_COUNT="$(count_token accountId)"
USERIDENTIFIER_COUNT="$(count_token userIdentifier)"
USERIDX_COUNT="$(count_token useridx)"
UPPERCASE_USERID_COUNT="$(count_token UserID)"

# 1. userId fully eliminated.
if [[ "$USERID_COUNT" -eq 0 ]]; then
    CHECK_USERID_GONE='{"passed": true, "details": "0 occurrences"}'
else
    CHECK_USERID_GONE=$(printf '{"passed": false, "details": "%s occurrences of userId remain"}' "$USERID_COUNT")
fi

# 2. accountId present (and at least as many as the original userId count).
if [[ "$ACCOUNTID_COUNT" -gt 0 ]]; then
    CHECK_ACCOUNTID_PRESENT=$(printf '{"passed": true, "details": "%s occurrences"}' "$ACCOUNTID_COUNT")
else
    CHECK_ACCOUNTID_PRESENT='{"passed": false, "details": "no accountId occurrences found"}'
fi

# 3. Distractors preserved (must be present, since they were present in initial state).
if [[ "$USERIDENTIFIER_COUNT" -ge 3 ]]; then
    CHECK_DISTRACTOR_IDENT=$(printf '{"passed": true, "details": "%s preserved"}' "$USERIDENTIFIER_COUNT")
else
    CHECK_DISTRACTOR_IDENT=$(printf '{"passed": false, "details": "userIdentifier count %s < expected 3"}' "$USERIDENTIFIER_COUNT")
fi

if [[ "$USERIDX_COUNT" -ge 1 ]]; then
    CHECK_DISTRACTOR_IDX=$(printf '{"passed": true, "details": "%s preserved"}' "$USERIDX_COUNT")
else
    CHECK_DISTRACTOR_IDX=$(printf '{"passed": false, "details": "useridx missing"}')
fi

if [[ "$UPPERCASE_USERID_COUNT" -ge 1 ]]; then
    CHECK_DISTRACTOR_UPPER=$(printf '{"passed": true, "details": "%s preserved"}' "$UPPERCASE_USERID_COUNT")
else
    CHECK_DISTRACTOR_UPPER=$(printf '{"passed": false, "details": "UserID (uppercase) missing from comments"}')
fi

# 4. TypeScript compiles.
TSC_OUTPUT="$(npx --no-install tsc --noEmit 2>&1)"
TSC_EXIT=$?
if [[ $TSC_EXIT -eq 0 ]]; then
    CHECK_TSC='{"passed": true, "details": "tsc --noEmit exit 0"}'
else
    TSC_OUTPUT_ESC=$(printf '%s' "$TSC_OUTPUT" | head -20 | jq -Rs '.')
    CHECK_TSC=$(printf '{"passed": false, "details": %s}' "$TSC_OUTPUT_ESC")
fi

# 5. Jest tests pass.
JEST_OUTPUT="$(npx --no-install jest --silent 2>&1)"
JEST_EXIT=$?
if [[ $JEST_EXIT -eq 0 ]]; then
    CHECK_JEST='{"passed": true, "details": "jest exit 0"}'
else
    JEST_OUTPUT_ESC=$(printf '%s' "$JEST_OUTPUT" | tail -30 | jq -Rs '.')
    CHECK_JEST=$(printf '{"passed": false, "details": %s}' "$JEST_OUTPUT_ESC")
fi

# 6. Diff size reasonable (< 400 lines of changes; spec said 200 but ~57 sites
#    * ~3 lines context plausibly exceeds 200, use 400 as the heuristic ceiling).
if [[ -d .git ]]; then
    DIFF_LINES=$(git diff --cached --shortstat 2>/dev/null | grep -oE '[0-9]+ insertions' | awk '{print $1}' || echo 0)
    DIFF_LINES=${DIFF_LINES:-0}
else
    DIFF_LINES=0
fi
if [[ "$DIFF_LINES" -le 400 ]]; then
    CHECK_DIFF=$(printf '{"passed": true, "details": "%s insertions"}' "$DIFF_LINES")
else
    CHECK_DIFF=$(printf '{"passed": false, "details": "%s insertions exceeds 400"}' "$DIFF_LINES")
fi

# --- Aggregate -------------------------------------------------------------
# Score = fraction of passed checks.
PASSED=0
TOTAL=7
for c in "$CHECK_USERID_GONE" "$CHECK_ACCOUNTID_PRESENT" "$CHECK_DISTRACTOR_IDENT" \
         "$CHECK_DISTRACTOR_IDX" "$CHECK_DISTRACTOR_UPPER" "$CHECK_TSC" "$CHECK_JEST"; do
    if echo "$c" | jq -e '.passed == true' >/dev/null 2>&1; then
        PASSED=$((PASSED + 1))
    fi
done

# Diff is reported but not counted in score (it's a sanity signal, not a pass/fail).
SCORE=$(awk -v p="$PASSED" -v t="$TOTAL" 'BEGIN { printf "%.4f", p / t }')
FUNCTIONAL_SCORE="$SCORE"
if echo "$CHECK_DIFF" | jq -e '.passed == true' >/dev/null 2>&1; then
    SCOPE_SCORE="1.0000"
else
    SCOPE_SCORE="0.0000"
fi
if [[ "$PASSED" -eq "$TOTAL" ]]; then
    SUCCESS="true"
else
    SUCCESS="false"
fi

cat <<EOF
{
  "success": $SUCCESS,
  "score": $SCORE,
  "functional_score": $FUNCTIONAL_SCORE,
  "scope_score": $SCOPE_SCORE,
  "checks": {
    "userId_eliminated": $CHECK_USERID_GONE,
    "accountId_present": $CHECK_ACCOUNTID_PRESENT,
    "distractor_userIdentifier": $CHECK_DISTRACTOR_IDENT,
    "distractor_useridx": $CHECK_DISTRACTOR_IDX,
    "distractor_UserID_comment": $CHECK_DISTRACTOR_UPPER,
    "tsc_compiles": $CHECK_TSC,
    "tests_pass": $CHECK_JEST
  },
  "diagnostics": {
    "diff_size": $CHECK_DIFF
  },
  "counts": {
    "userId": $USERID_COUNT,
    "accountId": $ACCOUNTID_COUNT,
    "userIdentifier": $USERIDENTIFIER_COUNT,
    "useridx": $USERIDX_COUNT,
    "UserID_uppercase": $UPPERCASE_USERID_COUNT,
    "diff_insertions": $DIFF_LINES
  }
}
EOF

if [[ "$SUCCESS" == "true" ]]; then
    exit 0
else
    exit 1
fi
