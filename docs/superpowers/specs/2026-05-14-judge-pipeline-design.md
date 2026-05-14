# Judge Pipeline Design

**Datum:** 2026-05-14
**Status:** Schváleno, připraveno k implementaci

## Cíl

Přidat LLM-as-judge hodnocení ke všem benchmark runům. Judge hodnotí subjektivní dimenze kvality, které objective verify.sh nezachytí — zejména over-engineering, scope compliance a přístup modelu. Výstup se integruje do existujícího CSV pipeline.

## Přístup

**Per-task session (Approach C):** Jeden Codex Desktop session na úlohu. Judge vidí všechny runy dané úlohy najednou a hodnotí je relativně vůči sobě. Relativní srovnání (low vs. max v rámci stejné úlohy) je přesnější než absolutní hodnocení izolovaných runů.

## Architektura

```
scripts/prepare_judge_input.py --task <task_id>
  → results/judge_inputs/<task_id>_input.md

[Codex Desktop: otevřít repo, zadat prompt]
  → results/judge/<task_id>_judge.json

scripts/aggregate.py  (aktualizovaný)
  → results/summary.csv  (s judge sloupci)
```

## Komponenty

### 1. `scripts/prepare_judge_input.py`

**Vstup:** `--task <task_id>` (např. `01_rename`), volitelně `--runs-dir` a `--out`

**Výstup:** `results/judge_inputs/<task_id>_input.md`

**Co čte pro každý run v `results/runs/<task_id>_*`:**
- `run_meta.json` — effort, run_number, wall_clock_ms, total_cost_usd, exit_code
- `metrics.json` — tool_call_count, tool_breakdown, num_turns, output_tokens
- `verify_result.json` — success, score, checks
- `diff_stat.txt` — přehled změn
- `final_diff.patch` — celý diff (klíčový pro hodnocení over-engineeringu)

**Řazení runů:** podle effort levelu (low → medium → high → xhigh → max), pak run_number.

**Formát výstupu** (Markdown):

```markdown
# Judge input: <task_id> — N runs

## Rubrika

Hodnoť každou dimenzi na škále 1–5. Porovnávej runy relativně v rámci této úlohy.

- **scope_compliance** (1–5): Držel se model přesně zadání?
  5 = nic navíc, přesně v scope
  1 = výrazně přesáhl scope, přidal nesouvisející změny

- **code_quality** (1–5): Čistota kódu, pojmenování, konzistence s repozitářem
  5 = čisté, konzistentní, dobře pojmenované
  1 = chaotické, nekonzistentní se zbytkem repo

- **approach_efficiency** (1–5): Zvolil model rozumnou strategii?
  5 = přímočará, efektivní cesta k řešení
  1 = zbytečně složitá, mnoho slepých uliček

- **over_engineering** (1–5): Přidal model abstrakce/refaktoring mimo zadání?
  5 = žádný over-engineering
  1 = výrazný over-engineering (nové třídy, refaktoring, extra funkce)

## Output JSON schema

Ulož výsledek jako JSON do `results/judge/<task_id>_judge.json`:

{
  "task": "<task_id>",
  "judge_model": "<model name>",
  "judged_at": "<ISO timestamp>",
  "runs": [
    {
      "run_id": "<run_id>",
      "effort": "<effort>",
      "run_number": <N>,
      "dimensions": {
        "scope_compliance":    { "score": <1-5>, "reasoning": "<text>" },
        "code_quality":        { "score": <1-5>, "reasoning": "<text>" },
        "approach_efficiency": { "score": <1-5>, "reasoning": "<text>" },
        "over_engineering":    { "score": <1-5>, "reasoning": "<text>" }
      },
      "overall_score": <průměr dimenzí, 2 desetinná místa>,
      "summary": "<1-2 věty o tomto runu>"
    }
  ],
  "comparative_analysis": "<volný text: trend low→max, hlavní pozorování>"
}

---

## Run 1: <effort> / run<N>

**Metadata:** wall=Xs  cost=$Y  turns=Z  tools=A

**Verify:** success=true/false  score=X.XXXX

**Diff stat:**
<obsah diff_stat.txt>

**Final diff:**
```diff
<obsah final_diff.patch>
```

---
```

### 2. Codex Desktop workflow

1. Otevřít repozitář v Codex Desktop
2. Zadat prompt:

> *"Read the file `results/judge_inputs/<task_id>_input.md`. It contains benchmark run artifacts and a rubric. Evaluate each run according to the rubric. Save the structured JSON result to `results/judge/<task_id>_judge.json` using exactly the schema defined in the input file."*

3. Codex Desktop přečte soubor, provede hodnocení, uloží JSON
4. Opakovat pro každou úlohu

### 3. Aktualizace `scripts/aggregate.py`

Přidat do `COLUMNS` pět nových sloupců:
- `judge_scope_compliance`
- `judge_code_quality`
- `judge_approach_efficiency`
- `judge_over_engineering`
- `judge_overall`

V `row_for()`: hledat `results/judge/<task_id>_judge.json`, najít run podle `run_id`, doplnit skóre. Pokud soubor neexistuje nebo run není nalezen — prázdná buňka (bez chyby).

## Datový tok

```
results/runs/01_rename_*/
  run_meta.json
  metrics.json
  verify_result.json
  diff_stat.txt
  final_diff.patch
        │
        ▼
prepare_judge_input.py
        │
        ▼
results/judge_inputs/01_rename_input.md
        │
        ▼  [Codex Desktop — manuální invokace]
        │
        ▼
results/judge/01_rename_judge.json
        │
        ▼
aggregate.py
        │
        ▼
results/summary.csv  (s judge sloupci)
```

## Omezení a caveats

- **Manuální invokace** — jeden Codex Desktop session per task; není plně automatický
- **Pozični bias** — Codex může hodnotit první/poslední run jinak; pořadí je fixní (low→max), což je konzistentní ale ne neutrální
- **Kontextová délka** — pro úlohy s velkými diffy může být input_md dlouhý; případně zkrátit diff na prvních 200 řádků
- **Reproducibilita** — různé Codex sessions mohou dát jiné skóre; pro větší validitu hodnotit každou úlohu 2× a průměrovat
- **judge_model pole** — zaznamenat přesný model použitý v Codex Desktop pro každé hodnocení

## Soubory ke změně / vytvoření

| Soubor | Akce |
|--------|------|
| `scripts/prepare_judge_input.py` | Vytvořit |
| `scripts/aggregate.py` | Upravit (5 nových sloupců) |
| `results/judge_inputs/` | Adresář (vytvořit) |
| `results/judge/` | Adresář (vytvořit) |
