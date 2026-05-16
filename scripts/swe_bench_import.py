#!/usr/bin/env python3
"""
SWE-bench adapter: download an instance and convert to benchmark task format.

Usage:
    # Import from SWE-bench Lite (Python)
    python3 scripts/swe_bench_import.py --instance django__django-11099

    # Import from Multi-SWE-bench (TypeScript/JS)
    python3 scripts/swe_bench_import.py --instance vuejs__core-1234 --dataset multi-swe-bench

    # List available instances
    python3 scripts/swe_bench_import.py --list --dataset swe-bench-lite --limit 20

Output: tasks/swe_<instance_id>/ with swe_instance.json, prompt.txt, verify.sh,
        meta.yaml, README.md, and initial_repo.tar.gz (gitignored).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

DATASETS = {
    "swe-bench-lite": {
        "hf_name": "princeton-nlp/SWE-bench_Lite",
        "split": "test",
        "language": "python",
    },
    "multi-swe-bench": {
        "hf_name": "ByteDance-Seed/Multi-SWE-bench",
        "split": "test",
        "language": "auto",  # detected per instance
    },
}

# Files/dirs to exclude from initial_repo.tar.gz
EXCLUDE_PATTERNS = {
    ".git", "node_modules", "__pycache__", ".tox", ".mypy_cache",
    ".pytest_cache", "dist", "build", ".eggs",
    ".venv", "venv", ".env", ".DS_Store",
}


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instance", help="Instance ID to import (e.g. django__django-11099)")
    ap.add_argument("--dataset", default="swe-bench-lite",
                    choices=list(DATASETS.keys()),
                    help="Dataset to use (default: swe-bench-lite)")
    ap.add_argument("--list", action="store_true", help="List available instances")
    ap.add_argument("--limit", type=int, default=20, help="Limit for --list (default: 20)")
    ap.add_argument("--output-dir", type=Path, default=None,
                    help="Output directory (default: tasks/swe_<instance_id>)")
    ap.add_argument("--force", action="store_true", help="Overwrite existing task directory")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    if args.list:
        return cmd_list(args)
    if not args.instance:
        print("Error: --instance required (or use --list)", file=sys.stderr)
        return 2
    return cmd_import(args)


def cmd_list(args: argparse.Namespace) -> int:
    """List available instances from the dataset."""
    try:
        from datasets import load_dataset
    except ImportError:
        print("Error: datasets not installed. Run: pip install -r scripts/requirements-swe.txt", file=sys.stderr)
        return 1

    ds_config = DATASETS[args.dataset]
    print(f"Loading {ds_config['hf_name']} (this may take a moment)...", file=sys.stderr)
    ds = load_dataset(ds_config["hf_name"], split=ds_config["split"])
    print(f"\nAvailable instances ({args.dataset}) — first {args.limit}:")
    for i, item in enumerate(ds):
        if i >= args.limit:
            break
        iid = item.get("instance_id", "?")
        repo = item.get("repo", "?")
        print(f"  {iid:50s}  {repo}")
    print(f"\nTotal: {len(ds)} instances. Use --limit N to see more.")
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    """Import a single instance as a benchmark task."""
    try:
        from datasets import load_dataset
    except ImportError:
        print("Error: datasets not installed. Run: pip install -r scripts/requirements-swe.txt", file=sys.stderr)
        return 1

    ds_config = DATASETS[args.dataset]
    print(f"[1/7] Loading {ds_config['hf_name']}...", file=sys.stderr)
    ds = load_dataset(ds_config["hf_name"], split=ds_config["split"])

    instance = next((item for item in ds if item.get("instance_id") == args.instance), None)
    if instance is None:
        print(f"Error: instance '{args.instance}' not found in {args.dataset}", file=sys.stderr)
        return 1

    out_dir = args.output_dir or (REPO_ROOT / "tasks" / f"swe_{args.instance}")
    if out_dir.exists() and not args.force:
        print(f"Error: {out_dir} already exists. Use --force to overwrite.", file=sys.stderr)
        return 1
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    print(f"[2/7] Cloning repository...", file=sys.stderr)
    tar_path = out_dir / "initial_repo.tar.gz"
    instance_data = prepare_instance(instance, ds_config, tar_path)

    print(f"[3/7] Writing swe_instance.json...", file=sys.stderr)
    write_instance_json(out_dir, instance_data)

    print(f"[4/7] Writing prompt.txt...", file=sys.stderr)
    write_prompt(out_dir, instance)

    print(f"[5/7] Writing verify.sh...", file=sys.stderr)
    write_verify(out_dir, instance_data)

    print(f"[6/7] Writing meta.yaml...", file=sys.stderr)
    write_meta(out_dir, instance_data)

    print(f"[7/7] Writing README.md...", file=sys.stderr)
    write_readme(out_dir, instance, instance_data)

    print(f"\n✓ Task created: {out_dir}", file=sys.stderr)
    print(f"  initial_repo.tar.gz: {tar_path.stat().st_size // 1024 // 1024}MB", file=sys.stderr)
    print(f"  Next: bash runner/run_single.sh {out_dir} low 1", file=sys.stderr)
    return 0


def _detect_language(instance: dict[str, Any], ds_config: dict[str, Any]) -> str:
    if ds_config["language"] != "auto":
        return ds_config["language"]
    lang = instance.get("language", "")
    if lang:
        return lang.lower()
    ts_repos = {"vuejs/core", "microsoft/TypeScript", "darkreader/darkreader",
                "mui/material-ui", "axios/axios", "dayjs/dayjs",
                "sveltejs/svelte", "expressjs/express"}
    if instance.get("repo", "") in ts_repos:
        return "typescript"
    return "python"


def _detect_install_cmd(instance: dict[str, Any], language: str) -> str:
    cmd = instance.get("install", "") or instance.get("install_cmd", "")
    if cmd:
        return cmd
    if language == "python":
        return "pip3 install -e .[test] -q --break-system-packages 2>/dev/null || pip3 install -e . -q --break-system-packages 2>/dev/null || true"
    return "npm install --silent --no-audit --no-fund --prefer-offline"


def _detect_test_cmd(instance: dict[str, Any], language: str) -> str:
    cmd = instance.get("test_cmd", "")
    if cmd:
        return cmd
    if language == "python":
        return "python3 -m pytest"
    return "npx vitest run"


def _should_exclude(path: str) -> bool:
    parts = Path(path).parts
    for part in parts:
        if part in EXCLUDE_PATTERNS:
            return True
        if part.endswith(".egg-info") or part.endswith(".pyc") or part.endswith(".pyo"):
            return True
    return False


def prepare_instance(
    instance: dict[str, Any],
    ds_config: dict[str, Any],
    tar_path: Path,
) -> dict[str, Any]:
    repo = instance["repo"]
    base_commit = instance["base_commit"]
    language = _detect_language(instance, ds_config)
    install_cmd = _detect_install_cmd(instance, language)
    test_cmd = _detect_test_cmd(instance, language)

    repo_url = f"https://github.com/{repo}.git"
    python_version = str(instance.get("python_version") or "3.11")
    node_version = str(instance.get("node_version") or "18")

    fail_to_pass: list[str] = instance.get("FAIL_TO_PASS", instance.get("fail_to_pass", []))
    pass_to_pass: list[str] = instance.get("PASS_TO_PASS", instance.get("pass_to_pass", []))

    if isinstance(fail_to_pass, str):
        try:
            fail_to_pass = json.loads(fail_to_pass)
        except json.JSONDecodeError:
            fail_to_pass = [fail_to_pass]
    if isinstance(pass_to_pass, str):
        try:
            pass_to_pass = json.loads(pass_to_pass)
        except json.JSONDecodeError:
            pass_to_pass = [pass_to_pass] if pass_to_pass else []

    with tempfile.TemporaryDirectory() as tmpdir:
        clone_dir = Path(tmpdir) / "repo"
        print(f"  Cloning {repo_url} (blobless)...", file=sys.stderr)
        result = subprocess.run(
            ["git", "clone", "--filter=blob:none", "--no-checkout", repo_url, str(clone_dir)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  Warning: blobless clone failed, trying full clone...", file=sys.stderr)
            result = subprocess.run(
                ["git", "clone", repo_url, str(clone_dir)],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"git clone failed: {result.stderr}")

        print(f"  Checking out {base_commit[:12]}...", file=sys.stderr)
        subprocess.run(["git", "checkout", base_commit], cwd=clone_dir,
                       capture_output=True, check=True)

        print(f"  Creating tar.gz...", file=sys.stderr)
        with tarfile.open(tar_path, "w:gz") as tf:
            for item in clone_dir.rglob("*"):
                rel = str(item.relative_to(clone_dir))
                if not _should_exclude(rel):
                    tf.add(item, arcname=rel)

    return {
        "instance_id": instance["instance_id"],
        "dataset": ds_config["hf_name"],
        "repo": repo,
        "base_commit": base_commit,
        "language": language,
        "python_version": python_version if language == "python" else None,
        "node_version": node_version if language in ("typescript", "javascript") else None,
        "fail_to_pass": fail_to_pass,
        "pass_to_pass": pass_to_pass[:10],
        "install_cmd": install_cmd,
        "test_cmd": test_cmd,
    }


def write_instance_json(out_dir: Path, data: dict[str, Any]) -> None:
    (out_dir / "swe_instance.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_prompt(out_dir: Path, instance: dict[str, Any]) -> None:
    problem = instance.get("problem_statement", "").strip()
    (out_dir / "prompt.txt").write_text(problem + "\n", encoding="utf-8")


def write_verify(out_dir: Path, data: dict[str, Any]) -> None:
    language = data["language"]
    if language == "python":
        _write_verify_python(out_dir, data["fail_to_pass"], data["pass_to_pass"], data["test_cmd"])
    else:
        _write_verify_typescript(out_dir, data["fail_to_pass"], data["pass_to_pass"], data["test_cmd"])


def _write_verify_python(
    out_dir: Path,
    fail_tests: list[str],
    pass_tests: list[str],
    test_cmd: str,
) -> None:
    fail_args = " ".join(f'"{t}"' for t in fail_tests)
    pass_args = " ".join(f'"{t}"' for t in pass_tests[:5]) if pass_tests else ""
    total = 1 + (1 if pass_tests else 0)

    p2p_block = f"""
# --- Check 2: PASS_TO_PASS tests still pass --------------------------------
PYTEST_P2P="$({test_cmd} {pass_args} --tb=short 2>&1)"
if [[ $? -eq 0 ]]; then
  CHECK_P2P='{{"passed": true, "details": "pass_to_pass tests still pass"}}'
  PASS=$((PASS+1))
else
  P2P_ESC=$(printf '%s' "$PYTEST_P2P" | tail -15 | jq -Rs '.')
  CHECK_P2P=$(printf '{{"passed": false, "details": %s}}' "$P2P_ESC")
fi""" if pass_tests else """
CHECK_P2P='{"passed": true, "details": "no pass_to_pass tests defined"}'
PASS=$((PASS+1))"""

    script = f"""#!/usr/bin/env bash
# Verify task (Python / pytest). Generated by swe_bench_import.py.
set -uo pipefail

# Suppress setuptools-scm version detection failures (no .git in workdir).
export SETUPTOOLS_SCM_PRETEND_VERSION="0.0.1"

PASS=0; TOTAL={total}

# --- Check 1: FAIL_TO_PASS tests now pass ----------------------------------
PYTEST_OUT="$({test_cmd} {fail_args} -x --tb=short 2>&1)"
if [[ $? -eq 0 ]]; then
  CHECK_F2P='{{"passed": true, "details": "fail_to_pass tests now pass"}}'
  PASS=$((PASS+1))
else
  F2P_ESC=$(printf '%s' "$PYTEST_OUT" | tail -20 | jq -Rs '.')
  CHECK_F2P=$(printf '{{"passed": false, "details": %s}}' "$F2P_ESC")
fi
{p2p_block}

SCORE=$(awk -v p="$PASS" -v t="$TOTAL" 'BEGIN{{printf "%.4f", p/t}}')
[[ "$PASS" -eq "$TOTAL" ]] && SUCCESS="true" || SUCCESS="false"
cat <<EOF
{{"success": $SUCCESS, "score": $SCORE, "checks": {{"fail_to_pass": $CHECK_F2P, "pass_to_pass": $CHECK_P2P}}}}
EOF
[[ "$SUCCESS" == "true" ]] && exit 0 || exit 1
"""
    p = out_dir / "verify.sh"
    p.write_text(script, encoding="utf-8")
    p.chmod(0o755)


def _write_verify_typescript(
    out_dir: Path,
    fail_tests: list[str],
    pass_tests: list[str],
    test_cmd: str,
) -> None:
    fail_args = " ".join(f'"{t}"' for t in fail_tests)
    pass_args = " ".join(f'"{t}"' for t in pass_tests[:3]) if pass_tests else ""
    total = 1 + (1 if pass_tests else 0)

    p2p_block = f"""
# --- Check 2: PASS_TO_PASS tests still pass --------------------------------
VITEST_P2P="$({test_cmd} {pass_args} 2>&1)"
if [[ $? -eq 0 ]]; then
  CHECK_P2P='{{"passed": true, "details": "pass_to_pass tests still pass"}}'
  PASS=$((PASS+1))
else
  P2P_ESC=$(printf '%s' "$VITEST_P2P" | tail -15 | jq -Rs '.')
  CHECK_P2P=$(printf '{{"passed": false, "details": %s}}' "$P2P_ESC")
fi""" if pass_tests else """
CHECK_P2P='{"passed": true, "details": "no pass_to_pass tests defined"}'
PASS=$((PASS+1))"""

    script = f"""#!/usr/bin/env bash
# Verify task (TypeScript / vitest or jest). Generated by swe_bench_import.py.
set -uo pipefail

PASS=0; TOTAL={total}

# --- Check 1: FAIL_TO_PASS tests now pass ----------------------------------
VITEST_OUT="$({test_cmd} {fail_args} 2>&1)"
if [[ $? -eq 0 ]]; then
  CHECK_F2P='{{"passed": true, "details": "fail_to_pass tests now pass"}}'
  PASS=$((PASS+1))
else
  F2P_ESC=$(printf '%s' "$VITEST_OUT" | tail -20 | jq -Rs '.')
  CHECK_F2P=$(printf '{{"passed": false, "details": %s}}' "$F2P_ESC")
fi
{p2p_block}

SCORE=$(awk -v p="$PASS" -v t="$TOTAL" 'BEGIN{{printf "%.4f", p/t}}')
[[ "$PASS" -eq "$TOTAL" ]] && SUCCESS="true" || SUCCESS="false"
cat <<EOF
{{"success": $SUCCESS, "score": $SCORE, "checks": {{"fail_to_pass": $CHECK_F2P, "pass_to_pass": $CHECK_P2P}}}}
EOF
[[ "$SUCCESS" == "true" ]] && exit 0 || exit 1
"""
    p = out_dir / "verify.sh"
    p.write_text(script, encoding="utf-8")
    p.chmod(0o755)


def write_meta(out_dir: Path, data: dict[str, Any]) -> None:
    lang = data["language"]
    version_line = (
        f'python_version: "{data["python_version"]}"'
        if lang == "python"
        else f'node_version: "{data["node_version"]}"'
    )
    safe_id = data["instance_id"].replace("-", "_").replace(".", "_")
    meta = f"""id: swe_{safe_id}
type: swe_bench
language: {lang}
{version_line}
description: "SWE-bench instance: {data['instance_id']} ({data['repo']})"

allowed_tools:
  - Read
  - Edit
  - Write
  - Glob
  - Grep
  - Bash

install_cmd: "{data['install_cmd']}"
test_cmd: "{data['test_cmd']}"

success_criteria:
  - fail_to_pass tests now pass
  - pass_to_pass tests still pass
"""
    (out_dir / "meta.yaml").write_text(meta, encoding="utf-8")


def write_readme(out_dir: Path, instance: dict[str, Any], data: dict[str, Any]) -> None:
    f2p_list = "\n".join(f"- `{t}`" for t in data["fail_to_pass"])
    readme = f"""# SWE-bench Task: {data['instance_id']}

**Repo:** [{data['repo']}](https://github.com/{data['repo']})
**Dataset:** {data['dataset']}
**Language:** {data['language']}
**Base commit:** `{data['base_commit'][:12]}`

## Problem Statement

{instance.get('problem_statement', '').strip()}

## Failing Tests (must pass after fix)

{f2p_list}

## Setup

```bash
# Generate initial_repo.tar.gz (once):
python3 scripts/swe_bench_import.py --instance {data['instance_id']} --force

# Run benchmark:
bash runner/run_single.sh tasks/swe_{data['instance_id']} low 1
```
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
