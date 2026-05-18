#!/usr/bin/env python3
"""Extract token and step metrics from a Kimi session export ZIP."""
import json
import sys
import zipfile
from pathlib import Path


def iter_jsonl(zf: zipfile.ZipFile, name: str):
    try:
        with zf.open(name) as f:
            for raw in f:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    except KeyError:
        return


def parse_export(path: Path) -> dict:
    metrics = {
        "input_other": 0,
        "output": 0,
        "input_cache_read": 0,
        "input_cache_creation": 0,
        "context_tokens": 0,
        "max_context_tokens": 0,
        "num_turns": 0,
        "tool_call_count": 0,
        "tool_call_count_by_type": {},
        "status_update_count": 0,
        "parse_errors": [],
    }

    with zipfile.ZipFile(path) as zf:
        for row in iter_jsonl(zf, "wire.jsonl"):
            msg = row.get("message") or {}
            msg_type = msg.get("type")
            payload = msg.get("payload") or {}

            if msg_type == "StatusUpdate":
                metrics["status_update_count"] += 1
                metrics["num_turns"] += 1
                usage = payload.get("token_usage") or {}
                for key in ("input_other", "output", "input_cache_read", "input_cache_creation"):
                    value = usage.get(key, 0) or 0
                    if isinstance(value, (int, float)):
                        metrics[key] += int(value)
                metrics["context_tokens"] = max(
                    metrics["context_tokens"],
                    int(payload.get("context_tokens", 0) or 0),
                )
                metrics["max_context_tokens"] = max(
                    metrics["max_context_tokens"],
                    int(payload.get("max_context_tokens", 0) or 0),
                )

            if msg_type == "ToolCall":
                metrics["tool_call_count"] += 1
                fn = payload.get("function") if isinstance(payload.get("function"), dict) else {}
                tool_name = str((payload.get("tool") or payload.get("name") or fn.get("name") or "unknown"))
                by_type = metrics["tool_call_count_by_type"]
                by_type[tool_name] = by_type.get(tool_name, 0) + 1

        for row in iter_jsonl(zf, "context.jsonl"):
            if row.get("role") == "_usage":
                value = row.get("token_count", 0) or 0
                if isinstance(value, (int, float)):
                    metrics["context_tokens"] = max(metrics["context_tokens"], int(value))

    return metrics


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: parse_kimi_export.py <session_export.zip>", file=sys.stderr)
        return 2

    try:
        metrics = parse_export(Path(sys.argv[1]))
    except Exception as exc:
        metrics = {
            "input_other": 0,
            "output": 0,
            "input_cache_read": 0,
            "input_cache_creation": 0,
            "context_tokens": 0,
            "max_context_tokens": 0,
            "num_turns": 0,
            "tool_call_count": 0,
            "tool_call_count_by_type": {},
            "status_update_count": 0,
            "parse_errors": [str(exc)],
        }

    json.dump(metrics, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
