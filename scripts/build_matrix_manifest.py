#!/usr/bin/env python3
"""Build a reproducible benchmark matrix manifest."""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path
from typing import Any


def build_plan(
    *,
    tasks: list[str],
    efforts: list[str],
    runs: int,
    model: str,
    provider: str,
    seed: int,
) -> dict[str, Any]:
    cells: list[dict[str, Any]] = []
    for task in tasks:
        for effort in efforts:
            for run_number in range(1, runs + 1):
                cell_id = f"{task}/{provider}/{model}/{effort}/run{run_number}"
                cells.append(
                    {
                        "cell_id": cell_id,
                        "task": task,
                        "provider": provider,
                        "model": model,
                        "effort": effort,
                        "reasoning_effort": effort,
                        "run_number": run_number,
                    }
                )

    random.Random(seed).shuffle(cells)
    for idx, cell in enumerate(cells, start=1):
        cell["index"] = idx

    return {
        "schema_version": 1,
        "created_at_unix": int(time.time()),
        "provider": provider,
        "model": model,
        "efforts": efforts,
        "tasks": tasks,
        "runs_per_cell": runs,
        "seed": seed,
        "total_cells": len(cells),
        "cells": cells,
    }


def _split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _discover_tasks(tasks_dir: Path) -> list[str]:
    return sorted(d.name for d in tasks_dir.iterdir() if d.is_dir())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tasks", default="", help="comma-separated task ids")
    ap.add_argument("--tasks-dir", type=Path, default=Path("tasks"))
    ap.add_argument("--efforts", required=True, help="comma-separated effort levels")
    ap.add_argument("--runs", type=int, required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--provider", choices=["claude", "codex"], default="claude")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)

    tasks = _split_csv(args.tasks) if args.tasks else _discover_tasks(args.tasks_dir)
    plan = build_plan(
        tasks=tasks,
        efforts=_split_csv(args.efforts),
        runs=args.runs,
        model=args.model,
        provider=args.provider,
        seed=args.seed,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
