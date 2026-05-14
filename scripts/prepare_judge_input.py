#!/usr/bin/env python3
"""
Prepare a Markdown judge input file for a given task.

Reads run artifacts from results/runs/<task_id>_* and writes a structured
Markdown file containing rubric, output JSON schema, and per-run artifacts
(metadata, verify result, diff stat, full diff).

Usage:
    python3 scripts/prepare_judge_input.py --task 01_rename
    python3 scripts/prepare_judge_input.py --task 02_implement_ico --out results/judge_inputs/02_input.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
EFFORT_ORDER = ["low", "medium", "high", "xhigh", "max"]
DIFF_LINE_LIMIT = 300

RUBRIC = """\
## Rubrika

Hodnoť každou dimenzi na škále 1–5. Porovnávej runy relativně v rámci této úlohy.

- **scope_compliance** (1–5): Držel se model přesně zadání?
  5 = nic navíc, přesně v scope | 1 = výrazně přesáhl scope

- **code_quality** (1–5): Čistota kódu, pojmenování, konzistence s repozitářem
  5 = čisté, konzistentní | 1 = chaotické, nekonzistentní

- **approach_efficiency** (1–5): Zvolil model rozumnou strategii?
  5 = přímočará, efektivní cesta | 1 = zbytečně složitá, mnoho slepých uliček

- **over_engineering** (1–5): Přidal model abstrakce/refaktoring mimo zadání?
  5 = žádný over-engineering | 1 = výrazný over-engineering
"""


def _schema_block(task_id: str) -> str:
    return f"""\
## Output JSON schema

Ulož výsledek jako validní JSON do `results/judge/{task_id}_judge.json`:

```json
{{
  "task": "{task_id}",
  "judge_model": "<model name>",
  "judged_at": "<ISO timestamp>",
  "runs": [
    {{
      "run_id": "<run_id>",
      "effort": "<effort>",
      "run_number": 1,
      "dimensions": {{
        "scope_compliance":    {{ "score": 1, "reasoning": "<text>" }},
        "code_quality":        {{ "score": 1, "reasoning": "<text>" }},
        "approach_efficiency": {{ "score": 1, "reasoning": "<text>" }},
        "over_engineering":    {{ "score": 1, "reasoning": "<text>" }}
      }},
      "overall_score": 1.0,
      "summary": "<1-2 věty>"
    }}
  ],
  "comparative_analysis": "<trend low→max, hlavní pozorování>"
}}
```
"""


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _load_text(path: Path) -> str:
    if not path.is_file():
        return "(soubor nenalezen)"
    return path.read_text(encoding="utf-8", errors="replace")


def _effort_sort_key(run_dir: Path) -> tuple[int, int]:
    meta = _load_json(run_dir / "run_meta.json") or {}
    effort = meta.get("effort", "unknown")
    run_n = int(meta.get("run_number", 0))
    order = EFFORT_ORDER.index(effort) if effort in EFFORT_ORDER else 99
    return (order, run_n)


def _format_run(run_dir: Path, idx: int) -> str:
    meta = _load_json(run_dir / "run_meta.json") or {}
    metrics = _load_json(run_dir / "metrics.json") or {}
    verify = _load_json(run_dir / "verify_result.json") or {}
    diff_stat = _load_text(run_dir / "diff_stat.txt").strip()
    diff_patch = _load_text(run_dir / "final_diff.patch").strip()

    effort = meta.get("effort", "?")
    run_n = meta.get("run_number", "?")
    wall_s = int(meta.get("wall_clock_ms", 0)) // 1000
    cost = float(metrics.get("total_cost_usd", 0))
    tool_count = metrics.get("tool_call_count", "?")
    turns = metrics.get("num_turns", "?")
    breakdown = metrics.get("tool_call_count_by_type") or {}
    breakdown_str = "; ".join(f"{k}={v}" for k, v in sorted(breakdown.items())) or "?"
    run_id = meta.get("run_id", run_dir.name)
    verify_success = verify.get("success", "?")
    verify_score = verify.get("score", "?")

    diff_lines = diff_patch.splitlines()
    if len(diff_lines) > DIFF_LINE_LIMIT:
        diff_patch = "\n".join(diff_lines[:DIFF_LINE_LIMIT])
        diff_patch += f"\n... ({len(diff_lines) - DIFF_LINE_LIMIT} dalších řádků zkráceno)"

    return f"""\
---

## Run {idx}: {effort} / run{run_n}

**run_id:** `{run_id}`

**Metadata:** wall={wall_s}s  cost=${cost:.3f}  turns={turns}  tool_calls={tool_count}  breakdown={breakdown_str}

**Verify:** success={verify_success}  score={verify_score}

**Diff stat:**
```
{diff_stat}
```

**Final diff:**
```diff
{diff_patch}
```
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--task", required=True, help="Task ID, e.g. 01_rename")
    ap.add_argument(
        "--runs-dir",
        type=Path,
        default=REPO_ROOT / "results" / "runs",
        help="directory containing per-run subdirs (default: results/runs)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="output path (default: results/judge_inputs/<task>_input.md)",
    )
    args = ap.parse_args()

    if not args.runs_dir.is_dir():
        print(f"Error: runs dir not found: {args.runs_dir}", file=sys.stderr)
        return 2

    run_dirs = sorted(
        [d for d in args.runs_dir.iterdir() if d.is_dir() and d.name.startswith(args.task + "_")],
        key=_effort_sort_key,
    )

    if not run_dirs:
        print(f"Error: no runs found for task {args.task!r} in {args.runs_dir}", file=sys.stderr)
        return 2

    out_path = args.out or (REPO_ROOT / "results" / "judge_inputs" / f"{args.task}_input.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    parts: list[str] = [
        f"# Judge input: {args.task} — {len(run_dirs)} runs\n",
        RUBRIC,
        _schema_block(args.task),
    ]
    for i, run_dir in enumerate(run_dirs, 1):
        parts.append(_format_run(run_dir, i))

    out_path.write_text("\n".join(parts), encoding="utf-8")
    print(f"Written {len(run_dirs)} runs → {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
