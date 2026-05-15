#!/usr/bin/env bash
#
# Verify Task 05 (find validation gaps).
# Run from workdir. Emits JSON on stdout.
#
set -uo pipefail

# --- Check 1: analysis.json exists ----------------------------------------
if [[ ! -f "analysis.json" ]]; then
  cat <<'EOF'
{"success": false, "score": "0.0000", "metrics": {"precision": 0, "recall": 0, "f1": 0, "tp": 0, "fp": 0, "fn": 5}, "checks": {
  "file_exists":    {"passed": false, "details": "analysis.json not found"},
  "schema_valid":   {"passed": false, "details": "file missing"},
  "recall_pass":    {"passed": false, "details": "file missing"},
  "precision_pass": {"passed": false, "details": "file missing"},
  "f1_pass":        {"passed": false, "details": "file missing"}
}}
EOF
  exit 1
fi
CHECK_FILE='{"passed": true, "details": "analysis.json exists"}'

# --- Check 2: valid JSON with correct schema --------------------------------
SCHEMA_RESULT=$(python3 - <<'PYEOF'
import json, sys
try:
    d = json.load(open('analysis.json'))
    eps = d.get('endpoints_without_validation')
    if not isinstance(eps, list):
        print('FAIL:endpoints_without_validation must be an array')
        sys.exit(0)
    for i, ep in enumerate(eps):
        for key in ['path','method','file','missing_validation']:
            if key not in ep:
                print(f'FAIL:item {i} missing key: {key}')
                sys.exit(0)
    print('OK')
except json.JSONDecodeError as e:
    print(f'FAIL:JSON parse error: {e}')
except Exception as e:
    print(f'FAIL:{e}')
PYEOF
)

if [[ "$SCHEMA_RESULT" == "OK" ]]; then
  CHECK_SCHEMA='{"passed": true, "details": "schema valid"}'
else
  MSG="${SCHEMA_RESULT#FAIL:}"
  ESC=$(printf '%s' "$MSG" | jq -Rs '.')
  CHECK_SCHEMA=$(printf '{"passed": false, "details": %s}' "$ESC")
fi

# --- Compute precision/recall/F1 ------------------------------------------
METRICS=$(python3 - <<'PYEOF'
import json, sys

ground_truth = {
    'POST:/api/users',
    'PUT:/api/users/:id',
    'POST:/api/products',
    'POST:/api/orders',
    'PUT:/api/orders/:id',
}

try:
    d = json.load(open('analysis.json'))
    reported = set()
    for ep in d.get('endpoints_without_validation', []):
        key = f"{ep.get('method','').upper()}:{ep.get('path','')}"
        reported.add(key)

    tp = len(ground_truth & reported)
    fp = len(reported - ground_truth)
    fn = len(ground_truth - reported)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    print(f'{precision:.4f} {recall:.4f} {f1:.4f} {tp} {fp} {fn}')
except Exception:
    print('0.0000 0.0000 0.0000 0 0 5')
PYEOF
)

read -r PRECISION RECALL F1 TP FP FN <<< "$METRICS"

# --- Check 3: Recall >= 0.6 -----------------------------------------------
if python3 -c "import sys; sys.exit(0 if float('$RECALL') >= 0.6 else 1)" 2>/dev/null; then
  CHECK_RECALL=$(printf '{"passed": true, "details": "recall=%.4f (TP=%s FN=%s)"}' "$RECALL" "$TP" "$FN")
else
  CHECK_RECALL=$(printf '{"passed": false, "details": "recall=%.4f < 0.6 (TP=%s FN=%s)"}' "$RECALL" "$TP" "$FN")
fi

# --- Check 4: Precision >= 0.5 --------------------------------------------
if python3 -c "import sys; sys.exit(0 if float('$PRECISION') >= 0.5 else 1)" 2>/dev/null; then
  CHECK_PREC=$(printf '{"passed": true, "details": "precision=%.4f (TP=%s FP=%s)"}' "$PRECISION" "$TP" "$FP")
else
  CHECK_PREC=$(printf '{"passed": false, "details": "precision=%.4f < 0.5 (TP=%s FP=%s)"}' "$PRECISION" "$TP" "$FP")
fi

# --- Check 5: F1 >= 0.65 --------------------------------------------------
if python3 -c "import sys; sys.exit(0 if float('$F1') >= 0.65 else 1)" 2>/dev/null; then
  CHECK_F1=$(printf '{"passed": true, "details": "F1=%.4f"}' "$F1")
else
  CHECK_F1=$(printf '{"passed": false, "details": "F1=%.4f < 0.65"}' "$F1")
fi

# --- Score ----------------------------------------------------------------
PASSED=0; TOTAL=5
for c in "$CHECK_FILE" "$CHECK_SCHEMA" "$CHECK_RECALL" "$CHECK_PREC" "$CHECK_F1"; do
  echo "$c" | jq -e '.passed == true' >/dev/null 2>&1 && PASSED=$((PASSED+1))
done

SCORE=$(awk -v p="$PASSED" -v t="$TOTAL" 'BEGIN{printf "%.4f", p/t}')
[[ "$PASSED" -eq "$TOTAL" ]] && SUCCESS="true" || SUCCESS="false"

cat <<EOF
{
  "success": $SUCCESS,
  "score": $SCORE,
  "metrics": {"precision": $PRECISION, "recall": $RECALL, "f1": $F1, "tp": $TP, "fp": $FP, "fn": $FN},
  "checks": {
    "file_exists":    $CHECK_FILE,
    "schema_valid":   $CHECK_SCHEMA,
    "recall_pass":    $CHECK_RECALL,
    "precision_pass": $CHECK_PREC,
    "f1_pass":        $CHECK_F1
  }
}
EOF
[[ "$SUCCESS" == "true" ]] && exit 0 || exit 1
