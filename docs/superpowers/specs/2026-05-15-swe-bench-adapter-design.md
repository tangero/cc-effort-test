# SWE-bench Adapter Design

**Datum:** 2026-05-15
**Status:** Schváleno, připraveno k implementaci

## Cíl

Vytvořit obecný adaptér který stáhne libovolnou instanci z SWE-bench Lite (Python) nebo Multi-SWE-bench (TypeScript/JavaScript) a převede ji na standardní task formát tohoto benchmarku. Tím umožnit testování effort levelů na reálných bugách z open-source projektů.

## Přístup

`scripts/swe_bench_import.py` je jednorázový CLI nástroj. Výsledné `initial_repo.tar.gz` je gitignored — každý uživatel ho generuje lokálně. Git obsahuje pouze metadata (`swe_instance.json`, `prompt.txt`, `meta.yaml`, `verify.sh`). Runner funguje beze změn v logice, pouze s rozšířením pro Python setup.

## Architektura

```
scripts/swe_bench_import.py        ← nový: adaptér
runner/run_single.sh               ← úprava: language-aware setup
tasks/swe_<instance_id>/
  swe_instance.json                ← commitováno
  prompt.txt                       ← commitováno
  meta.yaml                        ← commitováno
  README.md                        ← commitováno
  verify.sh                        ← commitováno
  initial_repo.tar.gz              ← gitignored, generuje importér
.gitignore                         ← přidat initial_repo.tar.gz pattern
```

## Komponenty

### 1. `scripts/swe_bench_import.py`

**CLI:**
```bash
# SWE-bench Lite (Python)
python3 scripts/swe_bench_import.py --instance django__django-11099

# Multi-SWE-bench (TypeScript/JS)
python3 scripts/swe_bench_import.py --instance vuejs__core-1234 --dataset multi-swe-bench

# Seznam dostupných instancí
python3 scripts/swe_bench_import.py --list --dataset swe-bench-lite --limit 20
```

**Závislosti:** `datasets` (HuggingFace), `gitpython`

**Postup per instance:**
1. Načíst instanci z HuggingFace dataset
2. `git clone --filter=blob:none <repo_url> <tmpdir>` (blobless clone — rychlejší než full)
3. `git checkout <base_commit>`
4. Zazipovat jako `initial_repo.tar.gz` — vyloučit: `.git/`, `node_modules/`, `__pycache__/`, `*.pyc`, `*.egg-info/`, `.tox/`, `dist/`, `build/`
5. Uložit `swe_instance.json`
6. Vygenerovat `prompt.txt` z `problem_statement`
7. Vygenerovat `verify.sh` z `FAIL_TO_PASS` + `PASS_TO_PASS`
8. Vygenerovat `meta.yaml`
9. Vygenerovat `README.md`

### 2. `tasks/swe_<instance_id>/swe_instance.json`

```json
{
  "instance_id": "django__django-11099",
  "dataset": "SWE-bench_Lite",
  "repo": "django/django",
  "base_commit": "abc123...",
  "language": "python",
  "python_version": "3.9",
  "node_version": null,
  "fail_to_pass": ["tests/test_x.py::TestClass::test_method"],
  "pass_to_pass": ["tests/test_y.py::TestClass::test_other"],
  "install_cmd": "pip install -e .[test]",
  "test_cmd": "python -m pytest"
}
```

Pro TypeScript instance:
```json
{
  "instance_id": "vuejs__core-1234",
  "dataset": "Multi-SWE-bench",
  "repo": "vuejs/core",
  "base_commit": "def456...",
  "language": "typescript",
  "python_version": null,
  "node_version": "18",
  "fail_to_pass": ["packages/reactivity/__tests__/effect.spec.ts"],
  "pass_to_pass": [],
  "install_cmd": "npm install",
  "test_cmd": "npx vitest run"
}
```

### 3. `verify.sh` — generovaný template

**Python:**
```bash
#!/usr/bin/env bash
set -uo pipefail

PASS=0; TOTAL=2

# Check 1: FAIL_TO_PASS tests now pass
PYTEST_OUT="$(python -m pytest tests/test_x.py::TestClass::test_method -x --tb=short 2>&1)"
if [[ $? -eq 0 ]]; then
  CHECK_F2P='{"passed": true, "details": "fail_to_pass tests now pass"}'
  PASS=$((PASS+1))
else
  ESC=$(printf '%s' "$PYTEST_OUT" | tail -20 | jq -Rs '.')
  CHECK_F2P=$(printf '{"passed": false, "details": %s}' "$ESC")
fi

# Check 2: PASS_TO_PASS tests still pass
PYTEST_P2P="$(python -m pytest tests/test_y.py::TestClass::test_other --tb=short 2>&1)"
if [[ $? -eq 0 ]]; then
  CHECK_P2P='{"passed": true, "details": "pass_to_pass tests still pass"}'
  PASS=$((PASS+1))
else
  ESC=$(printf '%s' "$PYTEST_P2P" | tail -20 | jq -Rs '.')
  CHECK_P2P=$(printf '{"passed": false, "details": %s}' "$ESC")
fi

SCORE=$(awk -v p="$PASS" -v t="$TOTAL" 'BEGIN{printf "%.4f", p/t}')
[[ "$PASS" -eq "$TOTAL" ]] && SUCCESS="true" || SUCCESS="false"
cat <<EOF
{"success": $SUCCESS, "score": $SCORE, "checks": {"fail_to_pass": $CHECK_F2P, "pass_to_pass": $CHECK_P2P}}
EOF
[[ "$SUCCESS" == "true" ]] && exit 0 || exit 1
```

**TypeScript** — stejný vzor, jen s `npx vitest run <test_file>` místo pytest.

### 4. Rozšíření `runner/run_single.sh`

Přidat do meta.yaml nové pole `language`. Runner ho načte a větví setup:

```bash
LANGUAGE="$(yq -r '.language // "typescript"' "$TASK_DIR_ABS/meta.yaml")"

if [[ "$LANGUAGE" == "python" ]]; then
    PYTHON_VERSION="$(yq -r '.python_version // "3.11"' "$TASK_DIR_ABS/meta.yaml" 2>/dev/null || echo '3.11')"
    if command -v pyenv >/dev/null 2>&1; then
        ( cd "$WORKDIR" && pyenv local "$PYTHON_VERSION" ) || true
    fi
    INSTALL_CMD="$(yq -r '.install_cmd // "pip install -e .[test]"' "$TASK_DIR_ABS/meta.yaml")"
    ( cd "$WORKDIR" && pip install -q $INSTALL_CMD 2>/dev/null ) || \
        { echo "Error: pip install failed" >&2; exit 1; }
elif [[ -f "$WORKDIR/package.json" && ! -d "$WORKDIR/node_modules" ]]; then
    ( cd "$WORKDIR" && npm install --silent --no-audit --no-fund --prefer-offline ) || \
        { echo "Error: npm install failed" >&2; exit 1; }
fi
```

### 5. `.gitignore` rozšíření

```
tasks/*/initial_repo.tar.gz
```

## Datový tok

```
HuggingFace Dataset
      │
      ▼
swe_bench_import.py
      │
      ├── git clone --filter=blob:none <repo>
      ├── git checkout <base_commit>
      ├── tar czf initial_repo.tar.gz (gitignored)
      ├── swe_instance.json (commitováno)
      ├── prompt.txt (commitováno)
      ├── verify.sh (commitováno)
      └── meta.yaml (commitováno)
                    │
                    ▼
            runner/run_single.sh
                    │
            (language-aware setup)
                    │
                    ▼
              verify.sh → JSON výstup
```

## Omezení

- `initial_repo.tar.gz` není v gitu — sdílení vyžaduje spuštění importéru nebo ruční distribuci
- Reprodukovatelnost závisí na dostupnosti repo na GitHubu (archivovaná/smazaná repa selžou)
- Python závislosti bez Dockeru mohou selhat na systémové knihovny (numpy/C extensions)
- Multi-SWE-bench TypeScript instance mají komplexní build toolchain (Vitest, Vite) — ne všechny instance budou fungovat bez Docker

## Doporučené první instance

**Python (SWE-bench Lite) — menší, self-contained bugy:**
- `astropy__astropy-*` — pure Python astronomická knihovna
- `sympy__sympy-*` — pure Python matematika
- `requests__requests-*` — HTTP knihovna

**TypeScript (Multi-SWE-bench):**
- `axios__axios-*` — HTTP klient, jednoduchý testovací setup
- `dayjs__dayjs-*` — date library, malý repo

## Soubory ke změně / vytvoření

| Soubor | Akce |
|--------|------|
| `scripts/swe_bench_import.py` | Vytvořit |
| `runner/run_single.sh` | Upravit (language-aware setup) |
| `.gitignore` | Upravit |
| `tasks/swe_*/` | Generováno importérem |
