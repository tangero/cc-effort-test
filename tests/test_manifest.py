import unittest

from scripts import build_matrix_manifest


class MatrixManifestTests(unittest.TestCase):
    def test_seeded_plan_is_reproducible_and_contains_provider(self):
        plan1 = build_matrix_manifest.build_plan(
            tasks=["01_rename", "02_implement_ico"],
            efforts=["low", "high"],
            runs=2,
            model="gpt-5.5",
            provider="codex",
            seed=123,
        )
        plan2 = build_matrix_manifest.build_plan(
            tasks=["01_rename", "02_implement_ico"],
            efforts=["low", "high"],
            runs=2,
            model="gpt-5.5",
            provider="codex",
            seed=123,
        )
        plan3 = build_matrix_manifest.build_plan(
            tasks=["01_rename", "02_implement_ico"],
            efforts=["low", "high"],
            runs=2,
            model="gpt-5.5",
            provider="codex",
            seed=456,
        )

        self.assertEqual(plan1, plan2)
        self.assertNotEqual([c["cell_id"] for c in plan1["cells"]], [c["cell_id"] for c in plan3["cells"]])
        self.assertEqual(plan1["provider"], "codex")
        self.assertEqual(plan1["seed"], 123)
        self.assertEqual(len(plan1["cells"]), 8)
        self.assertTrue(all(c["provider"] == "codex" for c in plan1["cells"]))


if __name__ == "__main__":
    unittest.main()
