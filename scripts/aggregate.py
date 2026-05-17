#!/usr/bin/env python3
"""
Aggregate per-run artifacts under results/runs/* into a single CSV.

For each run dir, reads run_meta.json + metrics.json + verify_result.json
and emits one CSV row. Missing files don't crash — they yield blank cells
and a non-zero `parse_errors` column.

Usage:
    python3 scripts/aggregate.py [--runs-dir DIR] [--out PATH]

Defaults to results/runs/ → stdout.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

# Cache for loaded judge JSON files: task_id → {run_id: run_data}
_judge_cache: dict[str, dict[str, Any]] = {}


def _judge_scores(task: str, run_id: str) -> dict[str, Any]:
    """Return judge dimension scores for a run, or empty-string values if unavailable."""
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


# Column order — keep stable so downstream pandas/Excel doesn't break.
COLUMNS = [
    "run_id",
    "task",
    "model",
    "effort",
    "run_number",
    "timestamp",
    "provider",
    "auth_mode",
    "reasoning_effort",
    "exit_code",
    "verify_passed",
    "verify_exit_code",
    "run_valid",
    "incomplete_reason",
    "score",
    "functional_score",
    "scope_score",
    "checks_json",
    "wall_clock_ms",
    "input_tokens",
    "output_tokens",
    "cache_read_input_tokens",
    "cache_creation_input_tokens",
    "thinking_tokens",
    "total_tokens",
    "total_cost_usd",
    "num_turns",
    "tool_call_count",
    "subagent_spawn_count",
    "tool_breakdown",
    "model_used",
    "stop_reason",
    "claude_version",
    "result_text_length",
    "parse_errors",
    "judge_scope_compliance",
    "judge_code_quality",
    "judge_approach_efficiency",
    "judge_over_engineering",
    "judge_overall",
]


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"warn: cannot parse {path}: {e}", file=sys.stderr)
        return None


def _missing_inputs(run_dir: Path) -> list[str]:
    required = ["run_meta.json", "metrics.json", "verify_result.json"]
    return [f"missing {name}" for name in required if not (run_dir / name).is_file()]


def _verify_passed(verify: dict[str, Any] | None) -> str:
    if verify is None:
        return ""
    p = verify.get("success") if verify.get("success") is not None else verify.get("passed")
    if isinstance(p, bool):
        return "true" if p else "false"
    return ""


def _tool_breakdown(metrics: dict[str, Any] | None) -> str:
    if not metrics:
        return ""
    b = metrics.get("tool_call_count_by_type") or {}
    if not isinstance(b, dict) or not b:
        return ""
    return ";".join(f"{k}={v}" for k, v in sorted(b.items()))


def row_for(run_dir: Path) -> dict[str, Any]:
    meta = _load_json(run_dir / "run_meta.json") or {}
    metrics = _load_json(run_dir / "metrics.json") or {}
    verify = _load_json(run_dir / "verify_result.json")
    missing = _missing_inputs(run_dir)
    valid = not missing and bool(meta) and bool(metrics) and verify is not None

    total_tokens = (
        (metrics.get("input_tokens") or 0)
        + (metrics.get("output_tokens") or 0)
        + (metrics.get("cache_read_input_tokens") or 0)
        + (metrics.get("cache_creation_input_tokens") or 0)
    )

    return {
        "run_id": meta.get("run_id") or run_dir.name,
        "task": meta.get("task", ""),
        "model": meta.get("model", ""),
        "effort": meta.get("effort", ""),
        "run_number": meta.get("run_number", ""),
        "timestamp": meta.get("timestamp", ""),
        "provider": meta.get("provider", "claude" if meta else ""),
        "auth_mode": meta.get("auth_mode", ""),
        "reasoning_effort": meta.get("reasoning_effort", meta.get("effort", "")),
        "exit_code": meta.get("exit_code", ""),
        "verify_passed": _verify_passed(verify),
        "verify_exit_code": meta.get("verify_exit_code", ""),
        "run_valid": "true" if valid else "false",
        "incomplete_reason": ";".join(missing),
        "score": verify.get("score", "") if verify else "",
        "functional_score": verify.get("functional_score", verify.get("score", ""))
        if verify
        else "",
        "scope_score": verify.get("scope_score", "") if verify else "",
        "checks_json": json.dumps(verify.get("checks", {}), sort_keys=True) if verify else "",
        "wall_clock_ms": meta.get("wall_clock_ms", ""),
        "input_tokens": metrics.get("input_tokens", ""),
        "output_tokens": metrics.get("output_tokens", ""),
        "cache_read_input_tokens": metrics.get("cache_read_input_tokens", ""),
        "cache_creation_input_tokens": metrics.get("cache_creation_input_tokens", ""),
        "thinking_tokens": metrics.get("thinking_tokens", ""),
        "total_tokens": total_tokens,
        "total_cost_usd": metrics.get("total_cost_usd", ""),
        "num_turns": metrics.get("num_turns", ""),
        "tool_call_count": metrics.get("tool_call_count", ""),
        "subagent_spawn_count": metrics.get("subagent_spawn_count", ""),
        "tool_breakdown": _tool_breakdown(metrics),
        "model_used": metrics.get("model_used", ""),
        "stop_reason": metrics.get("stop_reason", ""),
        "claude_version": meta.get("claude_version", ""),
        "result_text_length": metrics.get("result_text_length", ""),
        "parse_errors": ";".join(metrics.get("parse_errors") or []),
        **_judge_scores(meta.get("task", ""), meta.get("run_id") or run_dir.name),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--runs-dir",
        type=Path,
        default=REPO_ROOT / "results" / "runs",
        help="directory containing per-run subdirs",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="output CSV path (default: stdout)",
    )
    args = ap.parse_args(argv)

    if not args.runs_dir.is_dir():
        print(f"Error: runs dir not found: {args.runs_dir}", file=sys.stderr)
        return 2

    run_dirs = sorted(d for d in args.runs_dir.iterdir() if d.is_dir())
    if not run_dirs:
        print(f"warn: no run dirs under {args.runs_dir}", file=sys.stderr)

    out_stream = open(args.out, "w", newline="", encoding="utf-8") if args.out else sys.stdout
    try:
        writer = csv.DictWriter(out_stream, fieldnames=COLUMNS)
        writer.writeheader()
        for d in run_dirs:
            writer.writerow(row_for(d))
    finally:
        if args.out:
            out_stream.close()

    print(f"Aggregated {len(run_dirs)} run(s).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
