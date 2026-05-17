#!/usr/bin/env python3
"""Parse Codex `exec --json` output into the benchmark metrics schema."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def _read_events(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return [], ["empty stdout"]

    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return [obj], errors
        if isinstance(obj, list):
            return [x for x in obj if isinstance(x, dict)], errors
    except json.JSONDecodeError:
        pass

    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: {exc.msg}")
            continue
        if isinstance(obj, dict):
            events.append(obj)
    return events, errors


def _usage_values(usage: Any) -> dict[str, int]:
    if not isinstance(usage, dict):
        return {}
    input_details = usage.get("input_tokens_details")
    output_details = usage.get("output_tokens_details")
    return {
        "input_tokens": int(usage.get("input_tokens") or 0),
        "output_tokens": int(usage.get("output_tokens") or 0),
        "cache_read_input_tokens": int(
            usage.get("cache_read_input_tokens")
            or (input_details.get("cached_tokens", 0) if isinstance(input_details, dict) else 0)
            or 0
        ),
        "cache_creation_input_tokens": int(usage.get("cache_creation_input_tokens") or 0),
        "thinking_tokens": int(
            usage.get("thinking_tokens")
            or (output_details.get("reasoning_tokens", 0) if isinstance(output_details, dict) else 0)
            or 0
        ),
    }


def _walk_tool_calls(node: Any, out: list[dict[str, str | None]]) -> None:
    if isinstance(node, dict):
        node_type = node.get("type")
        name = node.get("name") or node.get("tool_name")
        if node_type in {"function_call", "tool_call"} or name in {
            "exec_command",
            "apply_patch",
            "view_image",
        }:
            out.append({"name": name or "unknown", "id": node.get("id") or node.get("call_id")})
        for value in node.values():
            _walk_tool_calls(value, out)
    elif isinstance(node, list):
        for value in node:
            _walk_tool_calls(value, out)


def parse(path: Path) -> dict[str, Any]:
    events, errors = _read_events(path)
    metrics: dict[str, Any] = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0,
        "thinking_tokens": 0,
        "total_cost_usd": None,
        "tool_calls": [],
        "tool_call_count": 0,
        "tool_call_count_by_type": {},
        "subagent_spawn_count": 0,
        "num_turns": 0,
        "model_used": None,
        "session_id": None,
        "stop_reason": None,
        "result_text_length": 0,
        "parse_errors": errors,
        "event_count": len(events),
    }
    final_usage: dict[str, int] | None = None

    for event in events:
        metrics["session_id"] = event.get("session_id") or event.get("conversation_id") or metrics[
            "session_id"
        ]
        metrics["model_used"] = event.get("model") or metrics["model_used"]

        if event.get("type") in {"agent_message", "message"} and isinstance(
            event.get("message"), str
        ):
            metrics["result_text_length"] += len(event["message"])

        _walk_tool_calls(event, metrics["tool_calls"])

        response = event.get("response")
        if isinstance(response, dict):
            metrics["model_used"] = response.get("model") or metrics["model_used"]
            metrics["stop_reason"] = response.get("status") or metrics["stop_reason"]
            usage = _usage_values(response.get("usage"))
            if usage:
                final_usage = usage

        usage = _usage_values(event.get("usage"))
        if usage:
            final_usage = usage

        if isinstance(event.get("total_cost_usd"), (int, float)):
            metrics["total_cost_usd"] = float(event["total_cost_usd"])

    if final_usage:
        metrics.update(final_usage)

    counts: Counter[str] = Counter()
    for call in metrics["tool_calls"]:
        counts[call.get("name") or "unknown"] += 1
    metrics["tool_call_count"] = len(metrics["tool_calls"])
    metrics["tool_call_count_by_type"] = dict(counts)
    metrics["subagent_spawn_count"] = counts.get("spawn_agent", 0)
    if not metrics["num_turns"]:
        metrics["num_turns"] = sum(1 for e in events if e.get("type") in {"agent_message", "message"})

    return metrics


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: parse_codex_session.py <stdout.json>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 2
    json.dump(parse(path), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
