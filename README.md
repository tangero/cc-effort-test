# cc-effort-test

Empirický benchmark framework pro měření dopadu parametru `--effort` v [Claude Code](https://claude.ai/code) na výkon, cenu a kvalitu výsledků.

**Live výsledky:** https://patrickzandl--7768c20a501f11f1afc4ee650bb23af1.web.val.run

## Co měříme

Parametr `--effort` ovlivňuje, kolik "přemýšlení" Claude věnuje každé úloze. Framework měří:

- **Úspěšnost** (objective verify skripty — pass/fail)
- **Skóre** (partial credit: kolik checks prošlo)
- **Wall-clock čas** a **náklady** (USD)
- **Počet tool calls** a iterací

Cíl: dataset s reálnými čísly místo anekdot.

---

## Rychlý start

### Předpoklady

```bash
node --version   # 20+
python3 --version # 3.11+
claude --version  # 2.1.100+, přihlášen přes 'claude /login'
brew install yq jq  # macOS
```

### Setup

```bash
git clone https://github.com/tangero/cc-effort-test
cd cc-effort-test
python3 -m venv .venv && source .venv/bin/activate
pip install -r scripts/requirements-swe.txt  # pro SWE-bench import
```

### Jeden run

```bash
bash runner/run_single.sh tasks/01_rename low 1
# args: <task_dir> <effort> <run_number> [model]
# model default: claude-opus-4-7
```

Výstup: `results/runs/<task>_<model>_<effort>_run<n>_<ts>/`

### Matice runů

```bash
bash scripts/run_matrix.sh -t 01_rename -e low,medium,high,max -n 3
bash scripts/run_matrix.sh --dry-run        # náhled bez spuštění
bash scripts/run_matrix.sh --resume         # pokračování po přerušení
```

### Agregace výsledků

```bash
python3 scripts/aggregate.py > results/summary.csv
```

### Generování reportu

```bash
python3 scripts/generate_report.py  # → results/report.val.ts
```

---

## Struktura projektu

```
tasks/              ← benchmark úlohy
  01_rename/
    prompt.txt      ← zadání pro Claude
    meta.yaml       ← konfigurace (allowed_tools, language, ...)
    verify.sh       ← objektní scoring (→ JSON výstup)
    initial_repo/   ← výchozí stav repozitáře
    hidden_tests/   ← testy nepřístupné modelu
    expected_solution/ ← referenční řešení

runner/
  run_single.sh     ← izolovaný run jedné buňky matice
  lib/
    parse_session.py ← parsování stream-json výstupu Claude

scripts/
  run_matrix.sh         ← spuštění matice (task × effort × n)
  aggregate.py          ← agregace výsledků do CSV
  generate_report.py    ← generování HTML reportu
  swe_bench_import.py   ← import instancí z SWE-bench Lite
  validate_verifier.sh  ← ověření verify.sh vs. expected_solution

results/
  runs/             ← výstupy runů (gitignored)
  summary.csv       ← agregovaná data
  report.val.ts     ← HTML report pro val.town
```

---

## Aktuální benchmark tasky

| Task | Typ | Popis | Obtížnost |
|------|-----|-------|-----------|
| `01_rename` | Mechanický | Přejmenovat `userId` → `accountId` (57 výskytů, TS) | Snadná |
| `02_implement_ico` | Implementace | Český IČO validační algoritmus v TypeScript | Snadná |
| `03_debug_order` | Debugging | 2 bugy v OrderService — Bug B záměrně skrytý | Střední |
| `06_strict_scope` | Scope compliance | Přidat validaci jen do jednoho souboru, nerozšiřovat scope | Střední |
| `07_security_audit` | Security | 5 bezpečnostních chyb v Express API (SQL injection, XSS, ...) | Střední-těžká |
| `08_async_bugs` | Debugging | 4-5 async/Promise bugů v TypeScript pipeline | Střední |
| `swe_sympy__sympy-24909` | SWE-bench | Reálný bug: `milli*W == 1` vrací True | Snadná |
| `swe_django__django-16910` | SWE-bench | Reálný bug: `only()` + `select_related()` na reverse OneToOne | **Těžká** |
| `swe_django__django-17051` | SWE-bench | Reálný bug: `bulk_create(update_conflicts=True)` nevrací IDs | Snadná |

---

## Jak přidat nový task

### Minimální struktura

```
tasks/<id>_<nazev>/
  prompt.txt          ← povinné
  meta.yaml           ← povinné
  verify.sh           ← povinné, musí produkovat JSON na stdout
  initial_repo/       ← povinné (nebo initial_repo.tar.gz)
  README.md           ← doporučené
  hidden_tests/       ← volitelné
  expected_solution/  ← volitelné, potřeba pro validate_verifier.sh
```

### 1. prompt.txt

Zadání pro Claude — přesně to, co dostane jako `-p` argument. Buď specifické (`Fix the bug in src/orders.ts`) nebo open-ended (`Find and fix all security vulnerabilities`).

### 2. meta.yaml

```yaml
id: 09_my_task
type: debugging          # synthetic | debugging | security | swe_bench
language: typescript     # typescript | python
description: "Stručný popis pro lidi"

allowed_tools:
  - Read
  - Edit
  - Write
  - Glob
  - Grep
  - Bash

# Pro Python SWE-bench tasky navíc:
# python_version: "3.11"
# install_cmd: "pip3 install -e . -q --break-system-packages"
# test_cmd: "python3 -m pytest"
```

### 3. verify.sh

Klíčový soubor. Spouštěn z `$WORKDIR` (rozbalená `initial_repo`). Musí:
- Vrátit JSON na stdout
- Ukončit se kódem 0 (success) nebo 1 (failure)

**Minimální template:**

```bash
#!/usr/bin/env bash
set -uo pipefail

TASK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PASS=0; TOTAL=3

# Check 1
if npx tsc --noEmit > /dev/null 2>&1; then
  C1='{"passed": true, "details": "TypeScript compiles"}'
  PASS=$((PASS+1))
else
  C1='{"passed": false, "details": "TypeScript compilation failed"}'
fi

# Check 2 — hidden tests
cp "$TASK_DIR/hidden_tests/my.test.ts" src/
JEST_OUT="$(npx jest --testPathPattern='my\.test\.ts' --forceExit 2>&1)"
JEST_EXIT=$?
rm -f src/my.test.ts
if [[ $JEST_EXIT -eq 0 ]]; then
  C2='{"passed": true, "details": "hidden tests pass"}'
  PASS=$((PASS+1))
else
  ESC=$(printf '%s' "$JEST_OUT" | tail -10 | jq -Rs '.')
  C2=$(printf '{"passed": false, "details": %s}' "$ESC")
fi

# Check 3 — specifická podmínka (grep v kódu, apod.)
if grep -q 'expectedPattern' src/myfile.ts 2>/dev/null; then
  C3='{"passed": true, "details": "pattern found"}'
  PASS=$((PASS+1))
else
  C3='{"passed": false, "details": "pattern not found"}'
fi

SCORE=$(awk -v p="$PASS" -v t="$TOTAL" 'BEGIN{printf "%.4f", p/t}')
[[ "$PASS" -eq "$TOTAL" ]] && SUCCESS="true" || SUCCESS="false"
cat <<EOF
{"success": $SUCCESS, "score": $SCORE, "checks": {"tsc": $C1, "tests": $C2, "pattern": $C3}}
EOF
[[ "$SUCCESS" == "true" ]] && exit 0 || exit 1
```

### 4. Ověření verify.sh

```bash
# Ověř, že expected_solution dostane success: true
bash scripts/validate_verifier.sh tasks/09_my_task

# Ověř, že initial_repo dostane success: false (task je správně navržen)
cd tasks/09_my_task/initial_repo
bash ../verify.sh
```

### 5. Tipy pro dobrý task

**Effort diferenciace:** Nejlepší tasky mají bugy kde:
- `low` konzistentně selhává (chybí mu reasoning nebo průzkum)
- `medium`/`high` uspívá
- Příklad: více skrytých bugů, kde jeden je zřejmý a jeden vyžaduje hlubší analýzu

**Scoring:** Preferuj partial credit (5 checks → score 0.0–1.0) před binárním pass/fail. Umožňuje vidět i neúplné opravy.

**Hidden tests:** Testy které model nevidí jsou klíčové — zabraňují tomu, aby model "cheatingoval" tím, že testy hardcoduje.

**Visible tests:** Musí projít s buggy kódem (jinak task nedává smysl — model nemůže vůbec spustit testy).

---

## SWE-bench import

Import reálného bugu z [SWE-bench Lite](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite):

```bash
# Instalace závislostí
pip3 install -r scripts/requirements-swe.txt --break-system-packages

# Výpis dostupných instancí
python3 scripts/swe_bench_import.py --list --dataset swe-bench-lite --limit 50

# Import konkrétní instance
python3 scripts/swe_bench_import.py --instance sympy__sympy-24909

# Výsledek: tasks/swe_sympy__sympy-24909/ (metadata commitnutá)
# initial_repo.tar.gz je gitignored — každý si ho generuje lokálně
```

### Omezení SWE-bench na macOS s Python 3.13+

- **Pre-2022 Django** (`<= django-15xxx`): nekompatibilní — chybí modul `cgi`
- **Pre-2021 Sympy** (`<= sympy-13xxx`): nekompatibilní — chybí modul `distutils`
- **Doporučené projekty:** Django 4.2+ (issue `16xxx`+), Sympy 1.11+ (issue `22xxx`+)
- **Vyhnout se:** astropy, matplotlib (C extensions — install selže bez Dockeru)

---

## Výsledky (Phase 1+SWE)

Klíčová zjištění po 100 runech:

| Finding | Detail |
|---------|--------|
| SWE-bench diferencuje effort | django-16910: low 33% → high 75% → max 100% pass rate |
| Max ≠ lepší výsledek | Max stojí 2–4× více než high, ale výsledek je stejný |
| Syntetické tasky nediferenciují | 01_rename, 02_implement_ico: 100% při všech effort úrovních |
| Debug bez testu = nulový efekt | 03_debug_order Bug B: nenalezen ani max effortem |

**Doporučení:**
- `low` — refaktoring, rename, jednoduché implementace
- `medium` / `high` — implementace dle spec, běžné bugy  
- `high` — reálné bugy (SWE-bench úroveň)
- `max` — scope compliance; u ostatních úloh nepřidává hodnotu

---

## Licence

- **Framework:** MIT
- **Dataset** (`results/runs/`): CC-BY-4.0

## Reference

- [Anthropic Effort docs](https://platform.claude.com/docs/en/build-with-claude/effort)
- [SWE-bench Lite](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite)
- [Multi-SWE-bench](https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-bench)
