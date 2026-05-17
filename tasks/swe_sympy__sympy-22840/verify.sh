#!/usr/bin/env bash
# Verify: sympy-22840 (cse() MatrixSymbol indexing bug)
# Per-test scoring: each FAIL_TO_PASS test is a separate check.
set -uo pipefail

export SETUPTOOLS_SCM_PRETEND_VERSION="0.0.1"

run_test() {
  local target="$1"
  local out
  out="$(python3 -m pytest "$target" -x --tb=line --ignore=sympy/parsing/tests/test_ast_parser.py --ignore=bin 2>&1)"
  local rc=$?
  if [[ $rc -eq 0 ]]; then
    echo "pass||"
  else
    local esc
    esc=$(printf '%s' "$out" | tail -10 | jq -Rs '.')
    echo "fail||$esc"
  fi
}

# FAIL_TO_PASS tests
R1=$(run_test "sympy/simplify/tests/test_cse.py::test_cse_MatrixSymbol")
R2=$(run_test "sympy/utilities/tests/test_codegen.py::test_multidim_c_argument_cse")

# PASS_TO_PASS tests (jako group)
P2P_OUT="$(python3 -m pytest \
  sympy/simplify/tests/test_cse.py::test_numbered_symbols \
  sympy/simplify/tests/test_cse.py::test_preprocess_for_cse \
  sympy/simplify/tests/test_cse.py::test_postprocess_for_cse \
  --tb=line --ignore=sympy/parsing/tests/test_ast_parser.py --ignore=bin 2>&1)"
P2P_RC=$?

make_check() {
  local res="$1"
  local name="$2"
  local status="${res%%||*}"
  local detail="${res#*||}"
  if [[ "$status" == "pass" ]]; then
    echo "{\"passed\": true, \"details\": \"$name\"}"
  else
    if [[ -n "$detail" ]]; then
      printf '{"passed": false, "details": %s}' "$detail"
    else
      echo "{\"passed\": false, \"details\": \"$name failed\"}"
    fi
  fi
}

C1=$(make_check "$R1" "test_cse_MatrixSymbol")
C2=$(make_check "$R2" "test_multidim_c_argument_cse")

if [[ $P2P_RC -eq 0 ]]; then
  C3='{"passed": true, "details": "pass_to_pass tests still pass"}'
else
  ESC=$(printf '%s' "$P2P_OUT" | tail -10 | jq -Rs '.')
  C3=$(printf '{"passed": false, "details": %s}' "$ESC")
fi

# Skóre: 3 checks (2 f2p + 1 p2p)
TOTAL=3; PASS=0
[[ "${R1%%||*}" == "pass" ]] && PASS=$((PASS+1))
[[ "${R2%%||*}" == "pass" ]] && PASS=$((PASS+1))
[[ $P2P_RC -eq 0 ]] && PASS=$((PASS+1))

SCORE=$(awk -v p="$PASS" -v t="$TOTAL" 'BEGIN{printf "%.4f", p/t}')
[[ "$PASS" -eq "$TOTAL" ]] && SUCCESS="true" || SUCCESS="false"
cat <<EOF
{"success": $SUCCESS, "score": $SCORE, "checks": {"test_cse_MatrixSymbol": $C1, "test_multidim_c_argument_cse": $C2, "pass_to_pass": $C3}}
EOF
[[ "$SUCCESS" == "true" ]] && exit 0 || exit 1
