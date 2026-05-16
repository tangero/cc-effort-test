#!/usr/bin/env bash
# Verify: sympy-22840 (cse() MatrixSymbol indexing bug)
set -uo pipefail

export SETUPTOOLS_SCM_PRETEND_VERSION="0.0.1"
PASS=0; TOTAL=2

# Check 1: FAIL_TO_PASS (test_cse_MatrixSymbol in test_cse.py, test_multidim_c_argument_cse in test_codegen.py)
PYTEST_OUT="$(python3 -m pytest \
  sympy/simplify/tests/test_cse.py::test_cse_MatrixSymbol \
  sympy/utilities/tests/test_codegen.py::test_multidim_c_argument_cse \
  -x --tb=short --ignore=sympy/parsing/tests/test_ast_parser.py --ignore=bin 2>&1)"
if [[ $? -eq 0 ]]; then
  CHECK_F2P='{"passed": true, "details": "fail_to_pass tests now pass"}'
  PASS=$((PASS+1))
else
  ESC=$(printf '%s' "$PYTEST_OUT" | tail -20 | jq -Rs '.')
  CHECK_F2P=$(printf '{"passed": false, "details": %s}' "$ESC")
fi

# Check 2: PASS_TO_PASS
PYTEST_P2P="$(python3 -m pytest \
  sympy/simplify/tests/test_cse.py::test_numbered_symbols \
  sympy/simplify/tests/test_cse.py::test_preprocess_for_cse \
  sympy/simplify/tests/test_cse.py::test_postprocess_for_cse \
  --tb=short --ignore=sympy/parsing/tests/test_ast_parser.py --ignore=bin 2>&1)"
if [[ $? -eq 0 ]]; then
  CHECK_P2P='{"passed": true, "details": "pass_to_pass tests still pass"}'
  PASS=$((PASS+1))
else
  ESC=$(printf '%s' "$PYTEST_P2P" | tail -15 | jq -Rs '.')
  CHECK_P2P=$(printf '{"passed": false, "details": %s}' "$ESC")
fi

SCORE=$(awk -v p="$PASS" -v t="$TOTAL" 'BEGIN{printf "%.4f", p/t}')
[[ "$PASS" -eq "$TOTAL" ]] && SUCCESS="true" || SUCCESS="false"
cat <<EOF
{"success": $SUCCESS, "score": $SCORE, "checks": {"fail_to_pass": $CHECK_F2P, "pass_to_pass": $CHECK_P2P}}
EOF
[[ "$SUCCESS" == "true" ]] && exit 0 || exit 1
