#!/usr/bin/env bash
# Verify: django-16408 (Multi-level FilteredRelation + select_related)
set -uo pipefail
PASS=0; TOTAL=2

F2P_OUT="$(python3 tests/runtests.py \
  known_related_objects.tests.ExistingRelatedInstancesTests.test_multilevel_reverse_fk_cyclic_select_related \
  known_related_objects.tests.ExistingRelatedInstancesTests.test_multilevel_reverse_fk_select_related \
  --verbosity=0 2>&1)"
if [[ $? -eq 0 ]]; then
  CHECK_F2P='{"passed": true, "details": "fail_to_pass tests now pass"}'
  PASS=$((PASS+1))
else
  ESC=$(printf '%s' "$F2P_OUT" | tail -20 | jq -Rs '.')
  CHECK_F2P=$(printf '{"passed": false, "details": %s}' "$ESC")
fi

P2P_OUT="$(python3 tests/runtests.py \
  known_related_objects.tests.ExistingRelatedInstancesTests.test_foreign_key \
  known_related_objects.tests.ExistingRelatedInstancesTests.test_foreign_key_multiple_prefetch \
  known_related_objects.tests.ExistingRelatedInstancesTests.test_foreign_key_prefetch_related \
  --verbosity=0 2>&1)"
if [[ $? -eq 0 ]]; then
  CHECK_P2P='{"passed": true, "details": "pass_to_pass tests still pass"}'
  PASS=$((PASS+1))
else
  ESC=$(printf '%s' "$P2P_OUT" | tail -15 | jq -Rs '.')
  CHECK_P2P=$(printf '{"passed": false, "details": %s}' "$ESC")
fi

SCORE=$(awk -v p="$PASS" -v t="$TOTAL" 'BEGIN{printf "%.4f", p/t}')
[[ "$PASS" -eq "$TOTAL" ]] && SUCCESS="true" || SUCCESS="false"
cat <<EOF
{"success": $SUCCESS, "score": $SCORE, "checks": {"fail_to_pass": $CHECK_F2P, "pass_to_pass": $CHECK_P2P}}
EOF
[[ "$SUCCESS" == "true" ]] && exit 0 || exit 1
