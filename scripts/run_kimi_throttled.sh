#!/usr/bin/env bash
#
# Throttled kimi runner — spouští běhy s pauzou mezi nimi a detekuje rate limit.
# Použití: bash scripts/run_kimi_throttled.sh [task1,task2,...] [efforts] [runs]
#
# Default: dokončí všechny chybějící kimi běhy s pauzou 20s mezi nimi.
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

TASKS_CSV="${1:-01_rename,02_implement_ico,03_debug_order,06_strict_scope,07_security_audit,08_async_bugs,swe_django__django-16379,swe_sympy__sympy-22840}"
EFFORTS_CSV="${2:-low,medium,high,max}"
N_RUNS="${3:-2}"
PAUSE_SECONDS="${4:-20}"
RATE_LIMIT_PAUSE="${5:-90}"

IFS=',' read -ra TASKS <<< "$TASKS_CSV"
IFS=',' read -ra EFFORTS <<< "$EFFORTS_CSV"

echo "Throttled kimi runner"
echo "  pause between runs: ${PAUSE_SECONDS}s"
echo "  rate-limit backoff: ${RATE_LIMIT_PAUSE}s"
echo ""

TOTAL=0
DONE=0
SKIP=0
FAIL=0

for task in "${TASKS[@]}"; do
    for effort in "${EFFORTS[@]}"; do
        for n in $(seq 1 "$N_RUNS"); do
            TOTAL=$((TOTAL + 1))
            pattern="${task}_kimi-k2.6_${effort}_run${n}_"
            if compgen -G "$REPO_ROOT/results/runs/${pattern}*" >/dev/null; then
                echo "[SKIP] $task / $effort / run$n (exists)"
                SKIP=$((SKIP + 1))
                continue
            fi

            echo ""
            echo "[RUN ] $task / $effort / run$n  (done=$DONE skip=$SKIP fail=$FAIL / total=$TOTAL)"
            
            if bash "$REPO_ROOT/runner/run_single_kimi.sh" "$REPO_ROOT/tasks/$task" "$effort" "$n"; then
                # Check if it was actually rate-limited
                RESULT_DIR=$(ls -td "$REPO_ROOT/results/runs/${pattern}"* 2>/dev/null | head -1)
                if [[ -f "$RESULT_DIR/stdout.json" ]]; then
                    if grep -q "429\|rate_limit\|usage limit" "$RESULT_DIR/stdout.json" 2>/dev/null; then
                        echo "[RATE] Rate limit detected! Waiting ${RATE_LIMIT_PAUSE}s..."
                        rm -rf "$RESULT_DIR"
                        sleep "$RATE_LIMIT_PAUSE"
                        # Retry once immediately
                        echo "[RETRY] $task / $effort / run$n"
                        if bash "$REPO_ROOT/runner/run_single_kimi.sh" "$REPO_ROOT/tasks/$task" "$effort" "$n"; then
                            RESULT_DIR=$(ls -td "$REPO_ROOT/results/runs/${pattern}"* 2>/dev/null | head -1)
                            if [[ -f "$RESULT_DIR/stdout.json" ]] && grep -q "429\|rate_limit\|usage limit" "$RESULT_DIR/stdout.json" 2>/dev/null; then
                                echo "[RATE] Still rate limited after retry. Stopping."
                                rm -rf "$RESULT_DIR"
                                exit 1
                            else
                                DONE=$((DONE + 1))
                            fi
                        else
                            FAIL=$((FAIL + 1))
                        fi
                    else
                        DONE=$((DONE + 1))
                    fi
                else
                    DONE=$((DONE + 1))
                fi
            else
                FAIL=$((FAIL + 1))
            fi

            echo "[WAIT] Pausing ${PAUSE_SECONDS}s..."
            sleep "$PAUSE_SECONDS"
        done
    done
done

echo ""
echo "=== Done ==="
echo "  completed: $DONE"
echo "  skipped:   $SKIP"
echo "  failed:    $FAIL"
echo "  total:     $TOTAL"
