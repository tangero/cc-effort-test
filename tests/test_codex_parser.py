import json
import tempfile
import unittest
from pathlib import Path

from runner.lib import parse_codex_session


class CodexParserTests(unittest.TestCase):
    def test_parses_codex_jsonl_into_common_metrics(self):
        events = [
            {"type": "session.started", "session_id": "s1", "model": "gpt-5.5"},
            {
                "type": "response.output_item.done",
                "item": {"type": "function_call", "name": "exec_command"},
            },
            {
                "type": "response.completed",
                "response": {
                    "usage": {
                        "input_tokens": 10,
                        "output_tokens": 6,
                        "input_tokens_details": {"cached_tokens": 3},
                        "output_tokens_details": {"reasoning_tokens": 2},
                    },
                    "model": "gpt-5.5",
                    "status": "completed",
                },
            },
            {"type": "agent_message", "message": "hotovo"},
        ]

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "stdout.json"
            path.write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")

            metrics = parse_codex_session.parse(path)

        self.assertEqual(metrics["model_used"], "gpt-5.5")
        self.assertEqual(metrics["session_id"], "s1")
        self.assertEqual(metrics["input_tokens"], 10)
        self.assertEqual(metrics["output_tokens"], 6)
        self.assertEqual(metrics["cache_read_input_tokens"], 3)
        self.assertEqual(metrics["thinking_tokens"], 2)
        self.assertEqual(metrics["tool_call_count"], 1)
        self.assertEqual(metrics["tool_call_count_by_type"], {"exec_command": 1})
        self.assertEqual(metrics["result_text_length"], len("hotovo"))
        self.assertEqual(metrics["stop_reason"], "completed")


if __name__ == "__main__":
    unittest.main()
