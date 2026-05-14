# Effort Benchmark Framework

Automatizovaný framework pro empirické změření, jak `--effort` parametr
v [Claude Code](https://code.claude.com) ovlivňuje:

- **spotřebu tokenů** (input, output, cache, thinking),
- **wall-clock čas běhu**,
- **úspěšnost úlohy** (objective verify scripty),
- **chování modelu** (počet tool callů, subagents, iterací).

Cílem je vytvořit dataset s **reálnými čísly** napříč různými effort levely
(low → medium → high → xhigh → max) na Opus 4.7, místo aby se články
o effort parametru opíraly o anekdoty a marketing.

## Status

**Phase 1 (in progress):** kvantitativní matrix na Opus 4.7. Sprint 1 (MVP)
hotovo — Task 01 (rename) end-to-end přes synthetic TS projekt + runner +
parser. Viz `PRD.md` pro detaily.

**Phase 2 (deferred):** Sonnet 4.6 srovnání, LLM-as-judge (GPT-5.5 + Gemini
3.1 Pro) pro kvalitativní úlohy, real OSS forky pro initial_repo.

## Rychlý start

### Předpoklady

- Node.js 20+ a npm (Claude Code dependency)
- Python 3.11+ a [uv](https://docs.astral.sh/uv/)
- Claude Code 2.1.117+ (testováno na 2.1.141), authentikované přes `claude /login`
  (subscription / Max plán). Není potřeba `ANTHROPIC_API_KEY`.
- `yq`, `jq`, `bash 5.x`

### Setup

```bash
# Python env
uv venv && uv pip install -e .

# Pre-install Node deps pro initial_repo Task 01 (zrychli běhy)
( cd tasks/01_rename/initial_repo && npm install --silent )

# Volitelně: dočasně odsuň user-level CLAUDE.md, aby nepolutoval test.
# (subscription mód nemůže CLAUDE.md auto-discovery suprimovat)
# mv ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.bench-bak
```

### Izolace běhu

Spec původně mandátovala `--bare` mód pro úplnou izolaci. Tento framework
běží v **subscription módu** (přes OAuth/keychain — žádné API credits navíc),
což `--bare` vylučuje. Místo toho runner ručně izoluje co lze:

| State | Suprimace |
|-------|-----------|
| User-level `~/.claude/settings.json` | `--setting-sources project` |
| MCP servery | `--strict-mcp-config --mcp-config '{...prázdné...}'` |
| Skills / slash commands | `--disable-slash-commands` |
| Custom agents | `--agents '{}'` |
| Session persistence | `--no-session-persistence` |
| **`~/.claude/CLAUDE.md`** | **NELZE bez `--bare`** — dočasně přesuň |
| Plugin sync, hooks | **NELZE bez `--bare`** |

Pokud potřebuješ tvrdší izolaci (pro publikaci dat), nastav `ANTHROPIC_API_KEY`
a v runneru zapni `--bare` ručně — `run_meta.json` zaznamenává `auth_mode`
do každého běhu, takže obě varianty jsou v datech rozeznatelné.

### Sanity check (validate verifier)

Ověří, že `verify.sh` produkuje `success: true` proti `expected_solution/`:

```bash
bash scripts/validate_verifier.sh tasks/01_rename
```

### Pre-flight check izolace

Před matricí (zejména poprvé):

```bash
bash scripts/check_isolation.sh
```

Reportuje stav `~/.claude/CLAUDE.md`, pluginy, hooks, auth mód a CLI deps.

### Spuštění jednoho běhu

```bash
bash runner/run_single.sh tasks/01_rename low 1 claude-opus-4-7
```

Výstup ve `results/runs/01_rename_claude-opus-4-7_low_run1_<timestamp>/`.

### Spuštění celé matrice (Phase 1)

```bash
bash scripts/run_matrix.sh                    # 1 task × 5 efforts × 3 runs = 15 cells
bash scripts/run_matrix.sh --dry-run          # ukáže, co by se spustilo
bash scripts/run_matrix.sh -e low,max -n 1    # zúžený smoke test
bash scripts/run_matrix.sh --resume           # pokračování po crashi
```

Per-cell stdout/stderr stream-je do `results/matrix_<ts>.log`. Failure
v jednom cellu nezastavuje matrix — pokračuje dál.

### Agregace výsledků

```bash
python3 scripts/aggregate.py --out results/summary.csv
```

Jedna řádka per běh: token counts, wall-clock, verify pass/fail, tool
breakdown, cost USD, auth_mode. Vhodné pro pandas/Excel/Google Sheets.

## Struktura repa

Viz `PRD.md` § 3.

## Test matice (Phase 1)

| Úloha | Typ | Efforts |
|-------|-----|---------|
| 01_rename | mechanický rename | low, medium, xhigh, max |
| 02_implement_ico | implementace dle spec | low, medium, high, max |
| 03_debug_pagination | bounded debugging | medium, high, xhigh |
| 04_design_catalog | open design | high, xhigh, max |
| 05_find_validation_gaps | information retrieval | low, medium, high |
| 06_strict_scope | scope compliance | low, medium, xhigh |

3 repetice per buňka = **57 běhů** Phase 1. Detaily v `effort-benchmark-spec.md`
a `PRD.md`.

## Licence

- Framework code: **MIT** (viz `LICENSE`)
- Dataset (`results/runs/`, až bude publikován): **CC-BY-4.0**

## Reference

- [Anthropic Effort docs](https://platform.claude.com/docs/en/build-with-claude/effort)
- [Claude Code model config](https://code.claude.com/docs/en/model-config)
- Vstupní spec: `effort-benchmark-spec.md`
- Produktové požadavky: `PRD.md`

## Judge Pipeline (LLM-as-judge)

Subjektivní hodnocení runů pomocí Codex Desktop (nebo jiného LLM agenta).

### 1. Připrav vstupní soubor

```bash
python3 scripts/prepare_judge_input.py --task 01_rename
python3 scripts/prepare_judge_input.py --task 02_implement_ico
```

Výstup: `results/judge_inputs/<task>_input.md` — Markdown s rubrikou, JSON schématem a artefakty všech runů dané úlohy.

### 2. Hodnocení v Codex Desktop

1. Otevři repozitář v Codex Desktop
2. Zadej prompt:

> Read the file `results/judge_inputs/<task_id>_input.md`. It contains benchmark run artifacts and a rubric. Evaluate each run according to the rubric. Save the structured JSON result to `results/judge/<task_id>_judge.json` using exactly the schema defined in the input file.

3. Opakuj pro každou úlohu

### 3. Agreguj výsledky

```bash
python3 scripts/aggregate.py --out results/summary.csv
```

CSV nyní obsahuje sloupce `judge_scope_compliance`, `judge_code_quality`, `judge_approach_efficiency`, `judge_over_engineering`, `judge_overall`.
