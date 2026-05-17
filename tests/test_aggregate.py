import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts import aggregate


class AggregateTests(unittest.TestCase):
    def test_row_exports_scores_checks_and_validity_for_complete_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run1"
            run_dir.mkdir()
            (run_dir / "run_meta.json").write_text(
                json.dumps(
                    {
                        "run_id": "run1",
                        "task": "01_rename",
                        "model": "claude-opus-4-7",
                        "effort": "low",
                        "provider": "claude",
                        "reasoning_effort": "low",
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "metrics.json").write_text(
                json.dumps({"total_cost_usd": 0.12, "tool_call_count": 4}),
                encoding="utf-8",
            )
            (run_dir / "verify_result.json").write_text(
                json.dumps(
                    {
                        "success": True,
                        "score": 0.8,
                        "functional_score": 1.0,
                        "scope_score": 0.5,
                        "checks": {"hidden": {"passed": True, "details": "ok"}},
                    }
                ),
                encoding="utf-8",
            )

            row = aggregate.row_for(run_dir)

            self.assertEqual(row["run_valid"], "true")
            self.assertEqual(row["provider"], "claude")
            self.assertEqual(row["reasoning_effort"], "low")
            self.assertEqual(row["score"], 0.8)
            self.assertEqual(row["functional_score"], 1.0)
            self.assertEqual(row["scope_score"], 0.5)
            self.assertIn('"hidden"', row["checks_json"])

    def test_incomplete_run_is_kept_with_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "broken_run"
            run_dir.mkdir()
            (run_dir / "stderr.log").write_text("boom", encoding="utf-8")

            row = aggregate.row_for(run_dir)

            self.assertEqual(row["run_id"], "broken_run")
            self.assertEqual(row["run_valid"], "false")
            self.assertIn("missing run_meta.json", row["incomplete_reason"])
            self.assertIn("missing metrics.json", row["incomplete_reason"])
            self.assertIn("missing verify_result.json", row["incomplete_reason"])

    def test_main_writes_new_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            runs_dir = Path(tmp) / "runs"
            out_path = Path(tmp) / "summary.csv"
            runs_dir.mkdir()
            (runs_dir / "broken").mkdir()

            rc = aggregate.main(["--runs-dir", str(runs_dir), "--out", str(out_path)])

            self.assertEqual(rc, 0)
            with out_path.open(encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(rows[0]["run_valid"], "false")
            self.assertIn("checks_json", rows[0])


if __name__ == "__main__":
    unittest.main()
