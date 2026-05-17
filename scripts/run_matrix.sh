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
#   -p, --provider <name>    Runner provider: claude or codex (default: claude)
#       --seed <int>         Seed used to shuffle the matrix (default: current epoch)
#       --dry-run            Print what would be run, don't invoke claude
#       --resume             Skip cells whose result dir already exists
#   -h, --help               This help
#
# Example:
#   bash scripts/run_matrix.sh                           # full Phase 1
#   bash scripts/run_matrix.sh -e low,max -n 1 --dry-run # smoke check
#   bash scripts/run_matrix.sh -t 01_rename --resume     # continue after crash

set -euo pipefail

# For line-buffered output when redirecting to a file, run this script via:
#   stdbuf -oL bash scripts/run_matrix.sh ...
# or use: script -q /dev/null -c "bash scripts/run_matrix.sh ..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# --- Defaults ---------------------------------------------------------------
TASKS_CSV=""
EFFORTS_CSV="low,medium,high,xhigh,max"
N_RUNS=3
MODEL="claude-opus-4-7"
PROVIDER="claude"
SEED="$(date +%s)"
DRY_RUN=0
RESUME=0

# --- Arg parsing ------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        -t|--tasks)    TASKS_CSV="$2"; shift 2 ;;
        -e|--efforts)  EFFORTS_CSV="$2"; shift 2 ;;
        -n|--runs)     N_RUNS="$2"; shift 2 ;;
        -m|--model)    MODEL="$2"; shift 2 ;;
        -p|--provider) PROVIDER="$2"; shift 2 ;;
        --seed)        SEED="$2"; shift 2 ;;
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
if [[ "$PROVIDER" != "claude" && "$PROVIDER" != "codex" ]]; then
    echo "Error: provider must be 'claude' or 'codex' (got '$PROVIDER')" >&2
    exit 2
fi

TOTAL=$(( ${#TASKS[@]} * ${#EFFORTS[@]} * N_RUNS ))
SECONDS=0
MATRIX_START=$SECONDS

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║  Claude Code Effort Benchmark — Matrix Runner                                ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo "  tasks:   ${TASKS[*]}"
echo "  efforts: ${EFFORTS[*]}"
echo "  provider: $PROVIDER"
echo "  model:   $MODEL"
echo "  runs:    $N_RUNS per cell"
echo "  seed:    $SEED"
echo "  resume:  $RESUME    dry-run: $DRY_RUN"
echo "  total:   $TOTAL cells"
echo ""

# --- Run loop ---------------------------------------------------------------
PASS=0
FAIL=0
SKIP=0
RUN_COUNT=0
MATRIX_TS="$(date +%s)"
CELL_LOG="$REPO_ROOT/results/matrix_${MATRIX_TS}.log"
MANIFEST="$REPO_ROOT/results/matrix_${MATRIX_TS}_manifest.json"
mkdir -p "$REPO_ROOT/results"

python3 "$REPO_ROOT/scripts/build_matrix_manifest.py" \
    --tasks "$(IFS=,; echo "${TASKS[*]}")" \
    --tasks-dir "$REPO_ROOT/tasks" \
    --efforts "$(IFS=,; echo "${EFFORTS[*]}")" \
    --runs "$N_RUNS" \
    --model "$MODEL" \
    --provider "$PROVIDER" \
    --seed "$SEED" \
    --out "$MANIFEST"

echo "  manifest: $MANIFEST"

# Helper: print human-readable duration
fmt_dur() {
    local s=$1
    if (( s < 60 )); then
        echo "${s}s"
    elif (( s < 3600 )); then
        echo "$((s/60))m$((s%60))s"
    else
        echo "$((s/3600))h$(((s%3600)/60))m"
    fi
}

while IFS=$'\t' read -r idx task provider model effort n; do
    task_dir="$REPO_ROOT/tasks/$task"
    if [[ ! -d "$task_dir" ]]; then
        echo "[skip] task dir not found: $task_dir" | tee -a "$CELL_LOG"
        continue
    fi

            CELL_LABEL="$task / $provider / $model / $effort / run$n"
            RUN_COUNT=$((RUN_COUNT + 1))

            # --resume check: skip if any results dir matches this cell prefix.
            if [[ "$RESUME" -eq 1 ]]; then
                pattern="${task}_${model}_${effort}_run${n}_"
                if compgen -G "$REPO_ROOT/results/runs/${pattern}*" >/dev/null; then
                    SKIP=$((SKIP+1))
                    printf "[%s] [%2d/%2d] SKIP  %-55s (already exists)\n" \
                        "$(date '+%H:%M:%S')" "$RUN_COUNT" "$TOTAL" "$CELL_LABEL"
                    continue
                fi
            fi

            if [[ "$DRY_RUN" -eq 1 ]]; then
                printf "[%s] [%2d/%2d] DRY   %-55s\n" \
                    "$(date '+%H:%M:%S')" "$RUN_COUNT" "$TOTAL" "$CELL_LABEL"
                continue
            fi

            # Progress header with ETA
            elapsed=$((SECONDS - MATRIX_START))
            if (( RUN_COUNT > 1 && RUN_COUNT <= TOTAL )); then
                avg_per_run=$(( elapsed / (RUN_COUNT - 1) ))
                remaining_runs=$(( TOTAL - RUN_COUNT + 1 ))
                eta=$(( avg_per_run * remaining_runs ))
                printf "[%s] ┌── Run %2d/%d  (%d%%)  elapsed: %s  ETA: %s\n" \
                    "$(date '+%H:%M:%S')" "$RUN_COUNT" "$TOTAL" \
                    "$(( RUN_COUNT * 100 / TOTAL ))" "$(fmt_dur "$elapsed")" "$(fmt_dur "$eta")"
            else
                printf "[%s] ┌── Run %2d/%d  (%d%%)\n" \
                    "$(date '+%H:%M:%S')" "$RUN_COUNT" "$TOTAL" \
                    "$(( RUN_COUNT * 100 / TOTAL ))"
            fi
            printf "[%s] │   → %s\n" "$(date '+%H:%M:%S')" "$CELL_LABEL"

            cell_start=$SECONDS
            if [[ "$provider" == "codex" ]]; then
                RUNNER="$REPO_ROOT/runner/run_single_codex.sh"
            else
                RUNNER="$REPO_ROOT/runner/run_single.sh"
            fi
            if MATRIX_SEED="$SEED" MATRIX_MANIFEST="$MANIFEST" MATRIX_INDEX="$idx" \
                bash "$RUNNER" \
                "$task_dir" "$effort" "$n" "$model" \
                >> "$CELL_LOG" 2>&1
            then
                cell_dur=$(( SECONDS - cell_start ))
                PASS=$((PASS+1))
                printf "[%s] └── ✓ OK    %s  (pass=%d fail=%d skip=%d)\n" \
                    "$(date '+%H:%M:%S')" "$(fmt_dur "$cell_dur")" "$PASS" "$FAIL" "$SKIP"
            else
                rc=$?
                cell_dur=$(( SECONDS - cell_start ))
                FAIL=$((FAIL+1))
                printf "[%s] └── ✗ FAIL  %s  exit=%d  (pass=%d fail=%d skip=%d)\n" \
                    "$(date '+%H:%M:%S')" "$(fmt_dur "$cell_dur")" "$rc" "$PASS" "$FAIL" "$SKIP"
            fi
done < <(python3 - "$MANIFEST" <<'PY'
import json, sys
manifest = json.load(open(sys.argv[1], encoding="utf-8"))
for c in manifest["cells"]:
    print("\t".join(str(c[k]) for k in ["index", "task", "provider", "model", "effort", "run_number"]))
PY
)

total_dur=$((SECONDS - MATRIX_START))

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║  Matrix complete                                                             ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
printf "  elapsed:  %s\n" "$(fmt_dur "$total_dur")"
printf "  pass:     %d\n" "$PASS"
printf "  fail:     %d\n" "$FAIL"
printf "  skip:     %d\n" "$SKIP"
printf "  total:    %d\n" "$TOTAL"
printf "  log:      %s\n" "$CELL_LOG"
printf "  manifest: %s\n" "$MANIFEST"
echo ""

if [[ "$DRY_RUN" -eq 0 ]]; then
    echo "Next: python3 scripts/aggregate.py > results/summary.csv"
    echo "      python3 scripts/generate_report.py"
fi

[[ "$FAIL" -eq 0 ]]
