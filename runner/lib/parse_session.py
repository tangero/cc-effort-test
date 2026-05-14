#!/usr/bin/env python3
"""
Parse Claude Code -p stream-json output into normalized metrics.

Usage:
    python3 parse_session.py <path_to_stdout.json>

Emits a single JSON object on stdout with these fields:
    input_tokens, output_tokens,
    cache_read_input_tokens, cache_creation_input_tokens,
    thinking_tokens, total_cost_usd,
    tool_calls (list of {name, ...}),
    tool_call_count, tool_call_count_by_type,
    subagent_spawn_count, num_turns,
    model_used, session_id, stop_reason,
    result_text_length, parse_errors (list).

The parser handles both:
  - stream-json (NDJSON): one event per line, with system/assistant/user/result types.
  - single-JSON (json output-format): a single object with .result and .usage.

Missing fields fall back to None. The script always exits 0 unless the input
file cannot be opened; partial parses are reported via parse_errors.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def _read_events(path: Path) -> tuple[list[dict], list[str]]:
    """Read events from file. Returns (events, parse_errors)."""
    errors: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return [], ["empty stdout"]

    # Try parsing as single JSON object first.
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return [obj], errors
        if isinstance(obj, list):
            return [e for e in obj if isinstance(e, dict)], errors
    except json.JSONDecodeError:
        pass

    # Fall back to NDJSON.
    events: list[dict] = []
    for line_num, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                events.append(obj)
        except json.JSONDecodeError as e:
            errors.append(f"line {line_num}: {e.msg}")
    return events, errors


def _extract_usage(d: dict | None) -> dict[str, int]:
    """Pull token counts from a usage dict, defensively."""
    if not isinstance(d, dict):
        return {}
    return {
        "input_tokens": int(d.get("input_tokens") or 0),
        "output_tokens": int(d.get("output_tokens") or 0),
        "cache_read_input_tokens": int(d.get("cache_read_input_tokens") or 0),
        "cache_creation_input_tokens": int(d.get("cache_creation_input_tokens") or 0),
        # Thinking tokens may live under different keys depending on API version.
        "thinking_tokens": int(
            d.get("thinking_tokens")
            or d.get("output_tokens_details", {}).get("reasoning_tokens", 0)
            if isinstance(d.get("output_tokens_details"), dict)
            else (d.get("thinking_tokens") or 0)
        ),
    }


def _walk_for_tool_uses(node: Any, out: list[dict]) -> None:
    """Recursively scan a content node for tool_use blocks."""
    if isinstance(node, dict):
        if node.get("type") == "tool_use":
            out.append(
                {
                    "name": node.get("name"),
                    "id": node.get("id"),
                }
            )
        for v in node.values():
            _walk_for_tool_uses(v, out)
    elif isinstance(node, list):
        for v in node:
            _walk_for_tool_uses(v, out)


def parse(path: Path) -> dict:
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

    # We accumulate usage across all assistant messages and prefer the final
    # `result` event's totals when present.
    accumulated_usage = Counter()
    final_usage: dict | None = None
    final_cost: float | None = None

    for ev in events:
        etype = ev.get("type")

        # Capture system/init events for session_id and model.
        if etype == "system" and ev.get("subtype") == "init":
            metrics["session_id"] = ev.get("session_id") or metrics["session_id"]
            metrics["model_used"] = ev.get("model") or metrics["model_used"]

        # Assistant messages can contain tool_use blocks and usage.
        if etype == "assistant":
            metrics["num_turns"] += 1
            msg = ev.get("message") or {}
            if not metrics["model_used"]:
                metrics["model_used"] = msg.get("model")
            # Tool uses inside content.
            _walk_for_tool_uses(msg.get("content"), metrics["tool_calls"])
            # Per-message usage (cumulative-ish — we'll prefer result.usage).
            u = msg.get("usage")
            if isinstance(u, dict):
                accumulated_usage["input_tokens"] += int(u.get("input_tokens") or 0)
                accumulated_usage["output_tokens"] += int(u.get("output_tokens") or 0)
                accumulated_usage["cache_read_input_tokens"] += int(
                    u.get("cache_read_input_tokens") or 0
                )
                accumulated_usage["cache_creation_input_tokens"] += int(
                    u.get("cache_creation_input_tokens") or 0
                )
            # Stop reason of last assistant message.
            sr = msg.get("stop_reason")
            if sr:
                metrics["stop_reason"] = sr

        # Final result event holds authoritative usage + cost.
        if etype == "result":
            metrics["session_id"] = ev.get("session_id") or metrics["session_id"]
            if isinstance(ev.get("usage"), dict):
                final_usage = ev["usage"]
            if isinstance(ev.get("total_cost_usd"), (int, float)):
                final_cost = float(ev["total_cost_usd"])
            if isinstance(ev.get("num_turns"), int):
                metrics["num_turns"] = ev["num_turns"]
            if isinstance(ev.get("result"), str):
                metrics["result_text_length"] = len(ev["result"])
            metrics["stop_reason"] = ev.get("subtype") or metrics["stop_reason"]

        # Some installations emit single-JSON with top-level usage + result.
        if etype is None and ("usage" in ev or "result" in ev or "total_cost_usd" in ev):
            if isinstance(ev.get("usage"), dict):
                final_usage = ev["usage"]
            if isinstance(ev.get("total_cost_usd"), (int, float)):
                final_cost = float(ev["total_cost_usd"])
            if isinstance(ev.get("result"), str):
                metrics["result_text_length"] = max(
                    metrics["result_text_length"], len(ev["result"])
                )
            metrics["session_id"] = ev.get("session_id") or metrics["session_id"]
            metrics["model_used"] = ev.get("model") or metrics["model_used"]

    # Prefer final usage; fall back to accumulated.
    chosen = _extract_usage(final_usage) if final_usage else dict(accumulated_usage)
    for k in (
        "input_tokens",
        "output_tokens",
        "cache_read_input_tokens",
        "cache_creation_input_tokens",
        "thinking_tokens",
    ):
        if k in chosen:
            metrics[k] = chosen[k]

    if final_cost is not None:
        metrics["total_cost_usd"] = final_cost

    # Tool call counts.
    metrics["tool_call_count"] = len(metrics["tool_calls"])
    counts: Counter[str] = Counter()
    for tc in metrics["tool_calls"]:
        name = tc.get("name") or "unknown"
        counts[name] += 1
    metrics["tool_call_count_by_type"] = dict(counts)
    # "Agent" tool calls are subagent spawns in Claude Code.
    metrics["subagent_spawn_count"] = counts.get("Agent", 0) + counts.get("Task", 0)

    return metrics


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: parse_session.py <stdout.json>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 2

    try:
        metrics = parse(path)
    except Exception as e:
        print(json.dumps({"parse_errors": [f"fatal: {e!r}"]}), file=sys.stdout)
        return 1

    json.dump(metrics, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
