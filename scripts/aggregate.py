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

# Column order — keep stable so downstream pandas/Excel doesn't break.
COLUMNS = [
    "run_id",
    "task",
    "model",
    "effort",
    "run_number",
    "timestamp",
    "auth_mode",
    "exit_code",
    "verify_passed",
    "verify_exit_code",
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
]


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"warn: cannot parse {path}: {e}", file=sys.stderr)
        return None


def _verify_passed(verify: dict[str, Any] | None) -> str:
    if verify is None:
        return ""
    p = verify.get("passed")
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
        "auth_mode": meta.get("auth_mode", ""),
        "exit_code": meta.get("exit_code", ""),
        "verify_passed": _verify_passed(verify),
        "verify_exit_code": meta.get("verify_exit_code", ""),
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
    }


def main() -> int:
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
    args = ap.parse_args()

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
