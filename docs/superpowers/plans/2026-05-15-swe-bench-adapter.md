# SWE-bench Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementovat `scripts/swe_bench_import.py` — CLI adaptér který stáhne libovolnou instanci z SWE-bench Lite nebo Multi-SWE-bench a převede ji na standardní task formát benchmarku.

**Architecture:** Skript stáhne instanci z HuggingFace datasets, blobless-clone repo na base_commit, zazipuje jako `initial_repo.tar.gz` (gitignored), a vygeneruje `swe_instance.json`, `prompt.txt`, `verify.sh`, `meta.yaml`, `README.md`. Verify.sh se větví dle jazyka (Python→pytest, TypeScript→vitest/jest).

**Tech Stack:** Python 3.11, `datasets` (HuggingFace), subprocess (git), tarfile, argparse

---

## Struktura souborů

```
scripts/swe_bench_import.py      ← nový: hlavní adaptér
scripts/requirements-swe.txt     ← nový: závislosti adaptéru
.gitignore                       ← upravit: přidat initial_repo.tar.gz pattern
```

---

## Task 1: Závislosti a .gitignore

**Files:**
- Create: `scripts/requirements-swe.txt`
- Modify: `.gitignore`

- [ ] **Krok 1: Vytvořit `scripts/requirements-swe.txt`**

```
datasets>=2.19.0
huggingface_hub>=0.22.0
```

- [ ] **Krok 2: Přidat do `.gitignore`**

Přečíst aktuální `.gitignore` a přidat:
```
# SWE-bench generated artifacts (large, gitignored — regenerate with swe_bench_import.py)
tasks/swe_*/initial_repo.tar.gz
tasks/swe_*/initial_repo/
```

- [ ] **Krok 3: Ověřit instalaci závislostí**

```bash
pip install -r scripts/requirements-swe.txt -q
python3 -c "from datasets import load_dataset; print('OK')"
```

Očekávaný výstup: `OK`

- [ ] **Krok 4: Commit**

```bash
git add scripts/requirements-swe.txt .gitignore
git commit -m "feat(swe): add HuggingFace dependency + gitignore for tar.gz artifacts"
```

---

## Task 2: Kostra skriptu + argument parsing

**Files:**
- Create: `scripts/swe_bench_import.py`

- [ ] **Krok 1: Vytvořit `scripts/swe_bench_import.py` s kostrou**

```python
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
import os
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
    ".pytest_cache", "dist", "build", "*.egg-info", ".eggs",
    ".venv", "venv", ".env", "*.pyc", "*.pyo", ".DS_Store",
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


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Krok 2: Ověřit syntaxi**

```bash
python3 -c "import py_compile; py_compile.compile('scripts/swe_bench_import.py', doraise=True)" && echo "OK"
```

Očekávaný výstup: `OK`

- [ ] **Krok 3: Commit**

```bash
git add scripts/swe_bench_import.py
git commit -m "feat(swe): add swe_bench_import.py skeleton with CLI + dataset listing"
```

---

## Task 3: Clone + tar.gz generování

**Files:**
- Modify: `scripts/swe_bench_import.py` — přidat `prepare_instance()`

- [ ] **Krok 1: Přidat helper `_detect_language()`**

Přidat za `EXCLUDE_PATTERNS`:

```python
def _detect_language(instance: dict[str, Any], ds_config: dict[str, Any]) -> str:
    """Detect language from dataset config or instance metadata."""
    if ds_config["language"] != "auto":
        return ds_config["language"]
    # Multi-SWE-bench has a 'language' field or infer from repo name
    lang = instance.get("language", "")
    if lang:
        return lang.lower()
    # Fallback: infer from known TypeScript/JS repos
    repo = instance.get("repo", "")
    ts_repos = {"vuejs/core", "microsoft/TypeScript", "darkreader/darkreader",
                "mui/material-ui", "axios/axios", "dayjs/dayjs",
                "sveltejs/svelte", "expressjs/express"}
    if repo in ts_repos:
        return "typescript"
    return "python"


def _detect_install_cmd(instance: dict[str, Any], language: str) -> str:
    """Get install command from instance or use sensible default."""
    cmd = instance.get("install", "") or instance.get("install_cmd", "")
    if cmd:
        return cmd
    if language == "python":
        return "pip install -e .[test] -q 2>/dev/null || pip install -e . -q 2>/dev/null || true"
    return "npm install --silent --no-audit --no-fund --prefer-offline"


def _detect_test_cmd(instance: dict[str, Any], language: str) -> str:
    """Get test command from instance or use sensible default."""
    cmd = instance.get("test_cmd", "")
    if cmd:
        return cmd
    if language == "python":
        return "python -m pytest"
    return "npx vitest run"
```

- [ ] **Krok 2: Přidat `prepare_instance()`**

Přidat za `_detect_test_cmd()`:

```python
def _should_exclude(path: str) -> bool:
    """Return True if path should be excluded from tar.gz."""
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
    """Clone repo at base_commit, create tar.gz, return instance metadata."""
    repo = instance["repo"]
    base_commit = instance["base_commit"]
    language = _detect_language(instance, ds_config)
    install_cmd = _detect_install_cmd(instance, language)
    test_cmd = _detect_test_cmd(instance, language)

    repo_url = f"https://github.com/{repo}.git"
    python_version = instance.get("python_version", "3.11") or "3.11"
    node_version = instance.get("node_version", "18") or "18"

    fail_to_pass: list[str] = instance.get("FAIL_TO_PASS", instance.get("fail_to_pass", []))
    pass_to_pass: list[str] = instance.get("PASS_TO_PASS", instance.get("pass_to_pass", []))

    # Parse JSON strings if needed (SWE-bench stores them as JSON strings)
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
        "pass_to_pass": pass_to_pass[:10],  # limit to 10 to keep verify.sh manageable
        "install_cmd": install_cmd,
        "test_cmd": test_cmd,
    }
```

- [ ] **Krok 3: Ověřit syntaxi**

```bash
python3 -c "import py_compile; py_compile.compile('scripts/swe_bench_import.py', doraise=True)" && echo "OK"
```

- [ ] **Krok 4: Commit**

```bash
git add scripts/swe_bench_import.py
git commit -m "feat(swe): add repo cloning + tar.gz generation"
```

---

## Task 4: Generování task souborů

**Files:**
- Modify: `scripts/swe_bench_import.py` — přidat `write_*` funkce

- [ ] **Krok 1: Přidat `write_instance_json()`**

```python
def write_instance_json(out_dir: Path, data: dict[str, Any]) -> None:
    (out_dir / "swe_instance.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
```

- [ ] **Krok 2: Přidat `write_prompt()`**

```python
def write_prompt(out_dir: Path, instance: dict[str, Any]) -> None:
    problem = instance.get("problem_statement", "").strip()
    (out_dir / "prompt.txt").write_text(problem + "\n", encoding="utf-8")
```

- [ ] **Krok 3: Přidat `write_verify()`**

```python
def write_verify(out_dir: Path, data: dict[str, Any]) -> None:
    language = data["language"]
    fail_tests = data["fail_to_pass"]
    pass_tests = data["pass_to_pass"]
    test_cmd = data["test_cmd"]

    if language == "python":
        _write_verify_python(out_dir, fail_tests, pass_tests, test_cmd)
    else:
        _write_verify_typescript(out_dir, fail_tests, pass_tests, test_cmd)


def _write_verify_python(
    out_dir: Path,
    fail_tests: list[str],
    pass_tests: list[str],
    test_cmd: str,
) -> None:
    fail_args = " ".join(f'"{t}"' for t in fail_tests)
    pass_args = " ".join(f'"{t}"' for t in pass_tests[:5]) if pass_tests else ""

    checks = 1 + (1 if pass_tests else 0)
    p2p_block = ""
    if pass_tests:
        p2p_block = f"""
# --- Check 2: PASS_TO_PASS tests still pass --------------------------------
PYTEST_P2P="$({test_cmd} {pass_args} --tb=short 2>&1)"
PYTEST_P2P_EXIT=$?
if [[ $PYTEST_P2P_EXIT -eq 0 ]]; then
  CHECK_P2P='{{"passed": true, "details": "pass_to_pass tests still pass"}}'
  PASS=$((PASS+1))
else
  P2P_ESC=$(printf '%s' "$PYTEST_P2P" | tail -15 | jq -Rs '.')
  CHECK_P2P=$(printf '{{"passed": false, "details": %s}}' "$P2P_ESC")
fi"""
    else:
        p2p_block = """
# No pass_to_pass tests defined
CHECK_P2P='{"passed": true, "details": "no pass_to_pass tests defined"}'
PASS=$((PASS+1))"""

    script = f"""#!/usr/bin/env bash
#
# Verify task (Python / pytest).
# Generated by swe_bench_import.py — do not edit manually.
#
set -uo pipefail

PASS=0; TOTAL={checks}

# --- Check 1: FAIL_TO_PASS tests now pass ----------------------------------
PYTEST_OUT="$({test_cmd} {fail_args} -x --tb=short 2>&1)"
PYTEST_EXIT=$?
if [[ $PYTEST_EXIT -eq 0 ]]; then
  CHECK_F2P='{{"passed": true, "details": "fail_to_pass tests now pass"}}'
  PASS=$((PASS+1))
else
  F2P_ESC=$(printf '%s' "$PYTEST_OUT" | tail -20 | jq -Rs '.')
  CHECK_F2P=$(printf '{{"passed": false, "details": %s}}' "$F2P_ESC")
fi
{p2p_block}

# --- Score -----------------------------------------------------------------
SCORE=$(awk -v p="$PASS" -v t="$TOTAL" 'BEGIN{{printf "%.4f", p/t}}')
[[ "$PASS" -eq "$TOTAL" ]] && SUCCESS="true" || SUCCESS="false"

cat <<EOF
{{"success": $SUCCESS, "score": $SCORE, "checks": {{"fail_to_pass": $CHECK_F2P, "pass_to_pass": $CHECK_P2P}}}}
EOF
[[ "$SUCCESS" == "true" ]] && exit 0 || exit 1
"""
    verify_path = out_dir / "verify.sh"
    verify_path.write_text(script, encoding="utf-8")
    verify_path.chmod(0o755)


def _write_verify_typescript(
    out_dir: Path,
    fail_tests: list[str],
    pass_tests: list[str],
    test_cmd: str,
) -> None:
    fail_args = " ".join(f'"{t}"' for t in fail_tests)
    pass_args = " ".join(f'"{t}"' for t in pass_tests[:3]) if pass_tests else ""

    checks = 1 + (1 if pass_tests else 0)
    p2p_block = ""
    if pass_tests:
        p2p_block = f"""
# --- Check 2: PASS_TO_PASS tests still pass --------------------------------
VITEST_P2P="$({test_cmd} {pass_args} 2>&1)"
VITEST_P2P_EXIT=$?
if [[ $VITEST_P2P_EXIT -eq 0 ]]; then
  CHECK_P2P='{{"passed": true, "details": "pass_to_pass tests still pass"}}'
  PASS=$((PASS+1))
else
  P2P_ESC=$(printf '%s' "$VITEST_P2P" | tail -15 | jq -Rs '.')
  CHECK_P2P=$(printf '{{"passed": false, "details": %s}}' "$P2P_ESC")
fi"""
    else:
        p2p_block = """
# No pass_to_pass tests defined
CHECK_P2P='{"passed": true, "details": "no pass_to_pass tests defined"}'
PASS=$((PASS+1))"""

    script = f"""#!/usr/bin/env bash
#
# Verify task (TypeScript / vitest or jest).
# Generated by swe_bench_import.py — do not edit manually.
#
set -uo pipefail

PASS=0; TOTAL={checks}

# --- Check 1: FAIL_TO_PASS tests now pass ----------------------------------
VITEST_OUT="$({test_cmd} {fail_args} 2>&1)"
VITEST_EXIT=$?
if [[ $VITEST_EXIT -eq 0 ]]; then
  CHECK_F2P='{{"passed": true, "details": "fail_to_pass tests now pass"}}'
  PASS=$((PASS+1))
else
  F2P_ESC=$(printf '%s' "$VITEST_OUT" | tail -20 | jq -Rs '.')
  CHECK_F2P=$(printf '{{"passed": false, "details": %s}}' "$F2P_ESC")
fi
{p2p_block}

# --- Score -----------------------------------------------------------------
SCORE=$(awk -v p="$PASS" -v t="$TOTAL" 'BEGIN{{printf "%.4f", p/t}}')
[[ "$PASS" -eq "$TOTAL" ]] && SUCCESS="true" || SUCCESS="false"

cat <<EOF
{{"success": $SUCCESS, "score": $SCORE, "checks": {{"fail_to_pass": $CHECK_F2P, "pass_to_pass": $CHECK_P2P}}}}
EOF
[[ "$SUCCESS" == "true" ]] && exit 0 || exit 1
"""
    verify_path = out_dir / "verify.sh"
    verify_path.write_text(script, encoding="utf-8")
    verify_path.chmod(0o755)
```

- [ ] **Krok 4: Přidat `write_meta()` a `write_readme()`**

```python
def write_meta(out_dir: Path, data: dict[str, Any]) -> None:
    lang = data["language"]
    version_line = (
        f"python_version: \"{data['python_version']}\""
        if lang == "python"
        else f"node_version: \"{data['node_version']}\""
    )
    meta = f"""id: swe_{data['instance_id'].replace('-', '_').replace('.', '_')}
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
```

- [ ] **Krok 5: Ověřit syntaxi**

```bash
python3 -c "import py_compile; py_compile.compile('scripts/swe_bench_import.py', doraise=True)" && echo "OK"
```

Očekávaný výstup: `OK`

- [ ] **Krok 6: Commit**

```bash
git add scripts/swe_bench_import.py
git commit -m "feat(swe): add task file generation (verify.sh, meta, prompt, readme)"
```

---

## Task 5: Runner — language-aware setup

**Files:**
- Modify: `runner/run_single.sh` — přidat Python setup větev

Stávající runner instaluje npm pouze pro TypeScript. Přidáme větev pro Python.

- [ ] **Krok 1: Přečíst aktuální stav npm install sekce v run_single.sh**

```bash
grep -n "npm install\|package.json\|node_modules\|Install" runner/run_single.sh
```

- [ ] **Krok 2: Najít a nahradit npm install blok**

Najít v `runner/run_single.sh` tento blok (kolem řádku 103–107):
```bash
# Install Node deps if package.json exists and no cached node_modules.
if [[ -f "$WORKDIR/package.json" && ! -d "$WORKDIR/node_modules" ]]; then
    ( cd "$WORKDIR" && npm install --silent --no-audit --no-fund --prefer-offline ) \
        || { echo "Error: npm install failed in $WORKDIR" >&2; exit 1; }
fi
```

Nahradit:
```bash
# Language-aware dependency installation.
LANGUAGE="$(yq -r '.language // "typescript"' "$TASK_DIR_ABS/meta.yaml" 2>/dev/null || echo 'typescript')"

if [[ "$LANGUAGE" == "python" ]]; then
    # Python setup: optionally pin version via pyenv, then pip install
    PYTHON_VERSION="$(yq -r '.python_version // "3.11"' "$TASK_DIR_ABS/meta.yaml" 2>/dev/null || echo '3.11')"
    INSTALL_CMD="$(yq -r '.install_cmd // "pip install -e . -q"' "$TASK_DIR_ABS/meta.yaml" 2>/dev/null || echo 'pip install -e . -q')"
    if command -v pyenv >/dev/null 2>&1; then
        ( cd "$WORKDIR" && pyenv local "$PYTHON_VERSION" 2>/dev/null ) || true
    fi
    ( cd "$WORKDIR" && eval "$INSTALL_CMD" ) \
        || { echo "Warning: pip install had errors — continuing" >&2; }
elif [[ -f "$WORKDIR/package.json" && ! -d "$WORKDIR/node_modules" ]]; then
    # TypeScript/JavaScript setup
    ( cd "$WORKDIR" && npm install --silent --no-audit --no-fund --prefer-offline ) \
        || { echo "Error: npm install failed in $WORKDIR" >&2; exit 1; }
fi
```

- [ ] **Krok 3: Ověřit syntaxi run_single.sh**

```bash
bash -n runner/run_single.sh && echo "OK"
```

Očekávaný výstup: `OK`

- [ ] **Krok 4: Commit**

```bash
git add runner/run_single.sh
git commit -m "feat(swe): add language-aware setup to run_single.sh (Python pyenv + pip)"
```

---

## Task 6: End-to-end test — import + smoke run

- [ ] **Krok 1: Nainstalovat HuggingFace závislosti**

```bash
pip install -r scripts/requirements-swe.txt -q
```

- [ ] **Krok 2: Vypsat dostupné instance**

```bash
python3 scripts/swe_bench_import.py --list --dataset swe-bench-lite --limit 10
```

Očekávaný výstup: seznam 10 instancí ve formátu `instance_id   repo`

- [ ] **Krok 3: Importovat jednu Python instanci (sympy — pure Python, menší)**

```bash
python3 scripts/swe_bench_import.py --instance sympy__sympy-20590
```

Očekávaný výstup:
```
[1/7] Loading princeton-nlp/SWE-bench_Lite...
[2/7] Cloning repository...
  Cloning https://github.com/sympy/sympy.git (blobless)...
  Checking out <commit>...
  Creating tar.gz...
[3/7] Writing swe_instance.json...
...
✓ Task created: tasks/swe_sympy__sympy-20590
  initial_repo.tar.gz: NMB
```

- [ ] **Krok 4: Ověřit vygenerované soubory**

```bash
find tasks/swe_sympy__sympy-20590 -type f | sort
```

Očekávaný výstup:
```
tasks/swe_sympy__sympy-20590/README.md
tasks/swe_sympy__sympy-20590/initial_repo.tar.gz
tasks/swe_sympy__sympy-20590/meta.yaml
tasks/swe_sympy__sympy-20590/prompt.txt
tasks/swe_sympy__sympy-20590/swe_instance.json
tasks/swe_sympy__sympy-20590/verify.sh
```

```bash
cat tasks/swe_sympy__sympy-20590/swe_instance.json
cat tasks/swe_sympy__sympy-20590/meta.yaml
head -5 tasks/swe_sympy__sympy-20590/prompt.txt
```

- [ ] **Krok 5: Smoke run — 1 běh na low effort**

```bash
bash runner/run_single.sh tasks/swe_sympy__sympy-20590 low 1
```

Zkontrolovat výstup:
```bash
cat results/runs/swe_sympy__sympy-20590_*/verify_result.json
cat results/runs/swe_sympy__sympy-20590_*/run_meta.json | python3 -m json.tool | grep -E "exit_code|wall_clock"
```

- [ ] **Krok 6: Commitnout commitovatelné soubory (bez tar.gz)**

```bash
git add tasks/swe_sympy__sympy-20590/swe_instance.json \
        tasks/swe_sympy__sympy-20590/prompt.txt \
        tasks/swe_sympy__sympy-20590/meta.yaml \
        tasks/swe_sympy__sympy-20590/verify.sh \
        tasks/swe_sympy__sympy-20590/README.md
git commit -m "feat(swe): add first SWE-bench instance sympy__sympy-20590"
```

- [ ] **Krok 7: Importovat jednu TypeScript instanci**

```bash
python3 scripts/swe_bench_import.py --instance axios__axios-1234 --dataset multi-swe-bench 2>&1 || \
python3 scripts/swe_bench_import.py --list --dataset multi-swe-bench --limit 5
```

Pokud `axios__axios-1234` neexistuje, vypsat seznam a zvolit první dostupnou axios instanci.
