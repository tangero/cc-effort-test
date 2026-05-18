# Judge Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementovat judge pipeline — skript pro přípravu vstupu pro Codex Desktop a rozšíření aggregate.py o judge sloupce.

**Architecture:** `prepare_judge_input.py` přečte artefakty runů pro jednu úlohu a vygeneruje Markdown soubor s rubrikou a daty pro Codex Desktop. Po manuálním hodnocení v Codex Desktop `aggregate.py` načte výsledný JSON a přidá judge skóre do CSV.

**Tech Stack:** Python 3.11, stdlib only (json, pathlib, argparse, csv)

---

## Struktura souborů

```
scripts/prepare_judge_input.py   ← nový skript
scripts/aggregate.py             ← přidat 5 judge sloupců
results/judge_inputs/            ← adresář pro vstupy (vytvořit)
results/judge/                   ← adresář pro judge JSON výstupy (vytvořit)
```

---

## Task 1: `scripts/prepare_judge_input.py`

**Files:**
- Create: `scripts/prepare_judge_input.py`

- [ ] **Krok 1: Vytvořit `scripts/prepare_judge_input.py`**

```python
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
```

- [ ] **Krok 2: Ověřit skript syntakticky**

```bash
python3 -c "import py_compile; py_compile.compile('scripts/prepare_judge_input.py', doraise=True)" && echo "OK"
```

Očekávaný výstup: `OK`

- [ ] **Krok 3: Spustit pro 01_rename a ověřit výstup**

```bash
python3 scripts/prepare_judge_input.py --task 01_rename
```

Očekávaný stderr: `Written N runs → results/judge_inputs/01_rename_input.md`

```bash
head -60 results/judge_inputs/01_rename_input.md
```

Očekávaný výstup: začíná `# Judge input: 01_rename`, obsahuje `## Rubrika`, `## Output JSON schema`, `## Run 1: low`.

- [ ] **Krok 4: Spustit pro 02_implement_ico**

```bash
python3 scripts/prepare_judge_input.py --task 02_implement_ico
```

Očekávaný stderr: `Written 12 runs → results/judge_inputs/02_implement_ico_input.md`

- [ ] **Krok 5: Commit**

```bash
git add scripts/prepare_judge_input.py results/judge_inputs/
git commit -m "feat(judge): add prepare_judge_input.py and generated inputs"
```

---

## Task 2: Rozšíření `scripts/aggregate.py` o judge sloupce

**Files:**
- Modify: `scripts/aggregate.py`

Judge JSON má strukturu:
```json
{
  "task": "01_rename",
  "runs": [
    {
      "run_id": "01_rename_claude-opus-4-7_low_run1_...",
      "dimensions": {
        "scope_compliance":    {"score": 5},
        "code_quality":        {"score": 4},
        "approach_efficiency": {"score": 4},
        "over_engineering":    {"score": 5}
      },
      "overall_score": 4.5
    }
  ]
}
```

Aggregate načte judge JSON dle `task` a vyhledá run dle `run_id`.

- [ ] **Krok 1: Přidat judge sloupce do `COLUMNS`**

Najít řádek `"parse_errors",` v `scripts/aggregate.py` a nahradit:

```python
    "parse_errors",
    "judge_scope_compliance",
    "judge_code_quality",
    "judge_approach_efficiency",
    "judge_over_engineering",
    "judge_overall",
```

- [ ] **Krok 2: Přidat modul-level cache a pomocnou funkci**

Za `REPO_ROOT = Path(__file__).resolve().parent.parent` přidat:

```python
# Cache pro načtené judge JSON soubory: task_id → {run_id: run_data}
_judge_cache: dict[str, dict[str, Any]] = {}


def _judge_scores(task: str, run_id: str) -> dict[str, Any]:
    """Return judge dimension scores for a run, or empty dict if unavailable."""
    if task not in _judge_cache:
        judge_path = REPO_ROOT / "results" / "judge" / f"{task}_judge.json"
        raw = _load_json(judge_path)
        if raw and isinstance(raw.get("runs"), list):
            _judge_cache[task] = {r["run_id"]: r for r in raw["runs"] if "run_id" in r}
        else:
            _judge_cache[task] = {}
    run_data = _judge_cache[task].get(run_id, {})
    dims = run_data.get("dimensions", {})
    return {
        "judge_scope_compliance": dims.get("scope_compliance", {}).get("score", ""),
        "judge_code_quality": dims.get("code_quality", {}).get("score", ""),
        "judge_approach_efficiency": dims.get("approach_efficiency", {}).get("score", ""),
        "judge_over_engineering": dims.get("over_engineering", {}).get("score", ""),
        "judge_overall": run_data.get("overall_score", ""),
    }
```

- [ ] **Krok 3: Volat `_judge_scores` v `row_for()`**

V `row_for()` najít řádek `"parse_errors": ";".join(...)` a rozšířit return dict:

```python
        "parse_errors": ";".join(metrics.get("parse_errors") or []),
        **_judge_scores(meta.get("task", ""), meta.get("run_id") or run_dir.name),
```

- [ ] **Krok 4: Ověřit syntaxi**

```bash
python3 -c "import py_compile; py_compile.compile('scripts/aggregate.py', doraise=True)" && echo "OK"
```

Očekávaný výstup: `OK`

- [ ] **Krok 5: Commit**

```bash
git add scripts/aggregate.py
git commit -m "feat(judge): add judge score columns to aggregate.py"
```

---

## Task 3: End-to-end test se vzorowym judge JSON

**Files:**
- Create: `results/judge/01_rename_judge.json` (dočasný testovací soubor)

Ověříme, že aggregate.py správně načte judge skóre a vloží je do CSV.

- [ ] **Krok 1: Zjistit run_id pro první low run**

```bash
python3 -c "
import json; from pathlib import Path
runs = sorted(Path('results/runs').glob('01_rename_*_low_run1_*'))
meta = json.loads((runs[0] / 'run_meta.json').read_text())
print(meta['run_id'])
"
```

Zapamatuj si výstup — použijeme ho v dalším kroku jako `<RUN_ID_LOW_R1>`.

- [ ] **Krok 2: Vytvořit testovací `results/judge/01_rename_judge.json`**

Nahraď `<RUN_ID_LOW_R1>` skutečným run_id z předchozího kroku:

```bash
mkdir -p results/judge
```

Vytvořit soubor `results/judge/01_rename_judge.json` s obsahem:
```json
{
  "task": "01_rename",
  "judge_model": "test-fixture",
  "judged_at": "2026-05-14T00:00:00+02:00",
  "runs": [
    {
      "run_id": "<RUN_ID_LOW_R1>",
      "effort": "low",
      "run_number": 1,
      "dimensions": {
        "scope_compliance":    {"score": 5, "reasoning": "test"},
        "code_quality":        {"score": 4, "reasoning": "test"},
        "approach_efficiency": {"score": 4, "reasoning": "test"},
        "over_engineering":    {"score": 5, "reasoning": "test"}
      },
      "overall_score": 4.5,
      "summary": "Test fixture run."
    }
  ],
  "comparative_analysis": "Test fixture."
}
```

- [ ] **Krok 3: Spustit aggregate a ověřit judge sloupce**

```bash
python3 scripts/aggregate.py --out results/summary.csv
```

```bash
python3 -c "
import csv
rows = [r for r in csv.DictReader(open('results/summary.csv')) if r.get('judge_overall')]
print(f'Rows with judge data: {len(rows)}')
for r in rows:
    print(r['run_id'], '→ overall:', r['judge_overall'], 'scope:', r['judge_scope_compliance'])
"
```

Očekávaný výstup: 1 řádek s `judge_overall = 4.5`, `judge_scope_compliance = 5`.

- [ ] **Krok 4: Ověřit že ostatní řádky mají prázdné judge sloupce**

```bash
python3 -c "
import csv
rows = [r for r in csv.DictReader(open('results/summary.csv')) if r['task']]
empty = [r for r in rows if not r.get('judge_overall')]
print(f'Rows without judge data: {len(empty)} (expected: {len(rows)-1})')
"
```

Očekávaný výstup: `Rows without judge data: 27 (expected: 27)`

- [ ] **Krok 5: Smazat testovací fixture a commitnout**

```bash
rm results/judge/01_rename_judge.json
python3 scripts/aggregate.py --out results/summary.csv
git add results/judge/ results/judge_inputs/ results/summary.csv
git commit -m "feat(judge): judge pipeline complete — prepare_judge_input + aggregate integration"
```

---

## Task 4: Přidat Codex Desktop prompt do README

**Files:**
- Modify: `README.md`

- [ ] **Krok 1: Zkontrolovat existující README**

```bash
head -5 README.md
```

- [ ] **Krok 2: Přidat sekci Judge Pipeline do README.md**

Přidat na konec souboru `README.md`:

```markdown

## Judge Pipeline (LLM-as-judge)

Subjektivní hodnocení runů pomocí Codex Desktop.

### 1. Připrav vstupní soubor

```bash
python3 scripts/prepare_judge_input.py --task 01_rename
python3 scripts/prepare_judge_input.py --task 02_implement_ico
```

Výstup: `results/judge_inputs/<task>_input.md`

### 2. Hodnocení v Codex Desktop

1. Otevři repozitář v Codex Desktop
2. Zadej prompt:

> Read the file `results/judge_inputs/<task_id>_input.md`. It contains benchmark run artifacts and a rubric. Evaluate each run according to the rubric. Save the structured JSON result to `results/judge/<task_id>_judge.json` using exactly the schema defined in the input file.

3. Opakuj pro každou úlohu

### 3. Agreguj výsledky

```bash
python3 scripts/aggregate.py --out results/summary.csv
```

CSV nyní obsahuje sloupce `judge_scope_compliance`, `judge_code_quality`, `judge_approach_efficiency`, `judge_over_engineering`, `judge_overall`.
```

- [ ] **Krok 3: Commit**

```bash
git add README.md
git commit -m "docs: add judge pipeline usage to README"
```
