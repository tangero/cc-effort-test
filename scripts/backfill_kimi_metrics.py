#!/usr/bin/env python3
"""Backfill Kimi token metrics from local `kimi export` session archives."""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RUNS = REPO / "results" / "runs"
SESSION_RE = re.compile(r"kimi -r ([0-9a-f-]+)")
sys.path.insert(0, str(REPO))

from runner.lib.parse_kimi_export import parse_export  # noqa: E402


def find_session_id(run_dir: Path) -> str | None:
    for name in ("stderr.log", "stdout.json"):
        path = run_dir / name
        if not path.exists():
            continue
        matches = SESSION_RE.findall(path.read_text(errors="replace"))
        if matches:
            return matches[-1]
    return None


def update_metrics(run_dir: Path, parsed: dict, session_id: str) -> None:
    metrics_path = run_dir / "metrics.json"
    try:
        metrics = json.loads(metrics_path.read_text())
    except Exception:
        metrics = {}

    metrics.update({
        "num_turns": parsed.get("num_turns", 0),
        "input_tokens": parsed.get("input_other", 0),
        "output_tokens": parsed.get("output", 0),
        "cache_read_input_tokens": parsed.get("input_cache_read", 0),
        "cache_creation_input_tokens": parsed.get("input_cache_creation", 0),
        "thinking_tokens": 0,
        "tool_call_count": parsed.get("tool_call_count", 0),
        "tool_call_count_by_type": parsed.get("tool_call_count_by_type", {}),
        "parse_errors": parsed.get("parse_errors", []),
        "session_id": session_id,
    })
    metrics.setdefault("model_used", "kimi-k2.6")
    metrics.setdefault("stop_reason", "success")
    metrics.setdefault("total_cost_usd", 0)
    metrics.setdefault("result_text_length", 0)

    metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n")
    (run_dir / "kimi_export_metrics.json").write_text(
        json.dumps(parsed, indent=2, sort_keys=True) + "\n"
    )


def backfill_run(run_dir: Path, force: bool) -> str:
    metrics_path = run_dir / "metrics.json"
    if not metrics_path.exists():
        return "skip:no-metrics"
    if not force:
        try:
            metrics = json.loads(metrics_path.read_text())
            if metrics.get("session_id") and (
                metrics.get("input_tokens", 0)
                or metrics.get("output_tokens", 0)
                or metrics.get("cache_read_input_tokens", 0)
            ):
                return "skip:has-token-metrics"
        except Exception:
            pass

    session_id = find_session_id(run_dir)
    if not session_id:
        return "skip:no-session-id"

    tmpdir = Path(tempfile.mkdtemp(prefix="kimi-export-"))
    try:
        export_zip = tmpdir / "session.zip"
        result = subprocess.run(
            ["kimi", "export", session_id, "-o", str(export_zip)],
            cwd=REPO,
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0 or not export_zip.exists():
            return f"fail:export:{result.returncode}"
        parsed = parse_export(export_zip)
        update_metrics(run_dir, parsed, session_id)
        return "updated"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="rewrite existing token metrics")
    parser.add_argument("--limit", type=int, default=0, help="limit processed run directories")
    args = parser.parse_args()

    counts: dict[str, int] = {}
    processed = 0
    for run_dir in sorted(RUNS.glob("*kimi*")):
        if not run_dir.is_dir():
            continue
        status = backfill_run(run_dir, args.force)
        counts[status] = counts.get(status, 0) + 1
        processed += 1
        print(f"{status}\t{run_dir.name}")
        if args.limit and processed >= args.limit:
            break

    print(json.dumps(counts, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
