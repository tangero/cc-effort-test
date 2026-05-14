#!/usr/bin/env bash
#
# Run the full Phase 1 benchmark matrix.
#
# Iterates over (task × effort × run_n) cells, invoking runner/run_single.sh
# for each. Failures in one cell don't stop the matrix — they are logged
# and the run continues. Final summary printed at end.
#
# Usage:
#   bash scripts/run_matrix.sh [options]
#
# Options:
#   -t, --tasks <csv>        Tasks to run (default: all dirs under tasks/)
#                            Pass dir names like "01_rename", not full paths.
#   -e, --efforts <csv>      Effort levels (default: low,medium,high,xhigh,max)
#   -n, --runs <int>         Replications per cell (default: 3)
#   -m, --model <id>         Model ID (default: claude-opus-4-7)
#       --dry-run            Print what would be run, don't invoke claude
#       --resume             Skip cells whose result dir already exists
#   -h, --help               This help
#
# Example:
#   bash scripts/run_matrix.sh                           # full Phase 1
#   bash scripts/run_matrix.sh -e low,max -n 1 --dry-run # smoke check
#   bash scripts/run_matrix.sh -t 01_rename --resume     # continue after crash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# --- Defaults ---------------------------------------------------------------
TASKS_CSV=""
EFFORTS_CSV="low,medium,high,xhigh,max"
N_RUNS=3
MODEL="claude-opus-4-7"
DRY_RUN=0
RESUME=0

# --- Arg parsing ------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        -t|--tasks)    TASKS_CSV="$2"; shift 2 ;;
        -e|--efforts)  EFFORTS_CSV="$2"; shift 2 ;;
        -n|--runs)     N_RUNS="$2"; shift 2 ;;
        -m|--model)    MODEL="$2"; shift 2 ;;
        --dry-run)     DRY_RUN=1; shift ;;
        --resume)      RESUME=1; shift ;;
        -h|--help)
            sed -n '3,28p' "$0"
            exit 0
            ;;
        *) echo "Unknown arg: $1" >&2; exit 2 ;;
    esac
done

# --- Resolve task list ------------------------------------------------------
if [[ -n "$TASKS_CSV" ]]; then
    IFS=',' read -ra TASKS <<< "$TASKS_CSV"
else
    TASKS=()
    while IFS= read -r d; do
        [[ -d "$d" ]] && TASKS+=("$(basename "$d")")
    done < <(find "$REPO_ROOT/tasks" -mindepth 1 -maxdepth 1 -type d | sort)
fi

IFS=',' read -ra EFFORTS <<< "$EFFORTS_CSV"

TOTAL=$(( ${#TASKS[@]} * ${#EFFORTS[@]} * N_RUNS ))
echo "Matrix plan: ${#TASKS[@]} task(s) × ${#EFFORTS[@]} effort(s) × $N_RUNS run(s) = $TOTAL cells"
echo "  tasks:   ${TASKS[*]}"
echo "  efforts: ${EFFORTS[*]}"
echo "  model:   $MODEL"
echo "  resume:  $RESUME    dry-run: $DRY_RUN"
echo

# --- Run loop ---------------------------------------------------------------
PASS=0
FAIL=0
SKIP=0
CELL_LOG="$REPO_ROOT/results/matrix_$(date +%s).log"
mkdir -p "$REPO_ROOT/results"

for task in "${TASKS[@]}"; do
    task_dir="$REPO_ROOT/tasks/$task"
    if [[ ! -d "$task_dir" ]]; then
        echo "[skip] task dir not found: $task_dir" | tee -a "$CELL_LOG"
        continue
    fi

    for effort in "${EFFORTS[@]}"; do
        for n in $(seq 1 "$N_RUNS"); do
            CELL_LABEL="$task / $MODEL / $effort / run$n"

            # --resume check: skip if any results dir matches this cell prefix.
            if [[ "$RESUME" -eq 1 ]]; then
                pattern="${task}_${MODEL}_${effort}_run${n}_"
                if compgen -G "$REPO_ROOT/results/runs/${pattern}*" >/dev/null; then
                    echo "[skip] $CELL_LABEL (resume: already exists)" | tee -a "$CELL_LOG"
                    SKIP=$((SKIP+1))
                    continue
                fi
            fi

            if [[ "$DRY_RUN" -eq 1 ]]; then
                echo "[dry ] $CELL_LABEL" | tee -a "$CELL_LOG"
                continue
            fi

            echo "[run ] $CELL_LABEL"
            cell_start=$(date +%s)
            if bash "$REPO_ROOT/runner/run_single.sh" \
                "$task_dir" "$effort" "$n" "$MODEL" \
                >> "$CELL_LOG" 2>&1
            then
                cell_dur=$(( $(date +%s) - cell_start ))
                echo "[ ok ] $CELL_LABEL (${cell_dur}s)" | tee -a "$CELL_LOG"
                PASS=$((PASS+1))
            else
                rc=$?
                cell_dur=$(( $(date +%s) - cell_start ))
                echo "[fail] $CELL_LABEL (exit=$rc, ${cell_dur}s) — see $CELL_LOG" | tee -a "$CELL_LOG"
                FAIL=$((FAIL+1))
            fi
        done
    done
done

echo
echo "Matrix done: pass=$PASS  fail=$FAIL  skip=$SKIP  total=$TOTAL"
echo "Log: $CELL_LOG"

if [[ "$DRY_RUN" -eq 0 ]]; then
    echo
    echo "Next: python3 scripts/aggregate.py > results/summary.csv"
fi

[[ "$FAIL" -eq 0 ]]
