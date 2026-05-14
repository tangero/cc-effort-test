# PRD — Effort Benchmark Framework (Phase 1)

**Status:** Draft v0.1 (po sokratovskem dotazování s autorem)
**Datum:** 2026-05-14
**Vstupní dokument:** `effort-benchmark-spec.md`
**Autor:** Claude Code (na základě zadání Patricka Zandla)

---

## 1. Stručné shrnutí

Postavit lokálně spustitelný framework, který automaticky změří, jak `--effort`
parametr v Claude Code (Opus 4.7) ovlivňuje spotřebu tokenů, čas, úspěšnost
úlohy a chování modelu. Výstupem je CSV tabulka napříč matrix
(úloha × effort × repetice), použitelná pro článek s reálnými čísly místo
komunitních anekdot.

Tento PRD pokrývá **Phase 1** (kvantitativní měření, Opus 4.7). Phase 2
(Sonnet 4.6, LLM judges pro kvalitativní hodnocení, reálné OSS forky) je
vědomě odložená — viz §9.

---

## 2. Cíle a non-cíle

### 2.1 Cíle Phase 1

1. **Naměřit** pro každou kombinaci (úloha, effort, repetice) tyto metriky:
   - input / output / cache-read / cache-creation / thinking tokens
   - celkový cost v USD (z `usage` v stdout JSON)
   - wall-clock čas běhu
   - počet tool callů a jejich rozložení
   - počet subagent spawn eventů
   - exit code Claude Code
   - výsledek `verify.sh` (success/fail + dílčí checks)
2. **Agregovat** výsledky do `results/analysis/aggregated.csv`.
3. **Reprodukovat** matici druhým spuštěním v rámci ≤20% variance per buňka.
4. Pokrýt **6 úloh** definovaných ve spec, ale Task 04 (open design) bude mít
   pouze objective verify (existence souboru, struktura, word count). Žádné
   LLM-as-judge skórování v Phase 1.

### 2.2 Explicitní non-cíle Phase 1

- Sonnet 4.6 (odloženo do Phase 2 — config je už připraven, jen runs se
  neprovádí).
- LLM-as-judge framework (GPT-5.5, Gemini 3.1 Pro). Bez judges nemá smysl
  pairwise comparison, position bias kontrola, Cohen's kappa atd.
- Real OSS forky jako `initial_repo`. Phase 1 jede na syntetickych projektech
  (rozběhání pipeline), Phase 2 swapne za reálné OSS.
- Cross-language testing (jen TypeScript).
- Bedrock / Vertex / Foundry providers.
- MCP overhead, hooks, CLAUDE.md auto-discovery (`--bare` to záměrně vyřazuje).

---

## 3. Architektura (Phase 1)

```
effort-benchmark/
├── PRD.md                          # tento dokument
├── README.md                       # public-facing intro
├── effort-benchmark-spec.md        # původní spec (uchováno pro audit trail)
├── LICENSE                         # MIT (framework code)
├── pyproject.toml                  # uv-managed
├── .gitignore
│
├── tasks/
│   ├── 01_rename/                  # MVP, fully implemented
│   │   ├── prompt.txt
│   │   ├── meta.yaml
│   │   ├── verify.sh
│   │   ├── README.md
│   │   ├── initial_repo/           # synthetic TS project (~10 souborů)
│   │   └── expected_solution/      # reference rename pro validate_verifier
│   ├── 02_implement_ico/           # připraveno až po MVP smoke
│   ├── 03_debug_pagination/        # později
│   ├── 04_design_catalog/          # objective-only verify v Phase 1
│   ├── 05_find_validation_gaps/    # později
│   └── 06_strict_scope/            # později
│
├── runner/
│   ├── run_single.sh               # jeden běh: setup → claude → verify → record
│   ├── run_matrix.sh               # matice s randomizací (po MVP smoke)
│   └── lib/
│       └── parse_session.py        # JSON parser pro claude -p output
│
├── scripts/
│   ├── validate_verifier.sh        # ověří verify.sh proti expected_solution
│   ├── aggregate.py                # runs/* → aggregated.csv (později)
│   └── pack_initial_repo.sh        # initial_repo/ → initial_repo.tar.gz (volitelně)
│
├── config/
│   ├── matrix.yaml                 # definice celé matice
│   └── env.example                 # ANTHROPIC_API_KEY šablona
│
├── results/
│   ├── runs/                       # gitignored, raw output každého běhu
│   └── analysis/                   # gitignored, aggregated.csv + grafy
│
└── docs/                           # později (METHODOLOGY, INTERPRETING, LIMITS)
```

### 3.1 Datový tok jednoho běhu

```
config/matrix.yaml ─┐
                    ├─► run_single.sh ─► claude --bare -p ... ─► stdout.json
tasks/<id>/         ─┤                                            stderr.log
  prompt.txt        ─┤                                            final_diff.patch
  initial_repo/     ─┤                                            run_meta.json
  verify.sh         ─┘                                            verify_result.json
                                                                        │
                                                                        ▼
                                                          results/runs/<run_id>/
                                                                        │
                                                                        ▼
                                                          parse_session.py → metrics row
                                                                        │
                                                                        ▼
                                                          aggregate.py → aggregated.csv
```

### 3.2 Klíčový závazek: izolace běhu

Každý běh dostane čistý tempdir (`mktemp -d`). Initial state je `cp -r`
ze `tasks/<id>/initial_repo/`. Po `claude` se zachycuje `git diff` proti
"initial" commitu, který udělá runner sám. Po `verify.sh` se tempdir maže.
Žádný state mezi běhy nepřetéká.

---

## 4. Test matrix (Phase 1)

```yaml
# config/matrix.yaml
phase: 1

models:
  primary:
    id: "claude-opus-4-7"           # full ID, ne alias
    efforts: [low, medium, high, xhigh, max]
  # secondary (sonnet) připraveno pro Phase 2, ale phase1.enabled = false

repetitions: 3
randomize_seed: 42                   # pro reprodukovatelnost shufflingu
pause_between_runs_seconds: 30       # cache cooldown
max_budget_usd_per_run: 10           # hard cap přes --max-budget-usd

tasks:
  - id: "01_rename"
    efforts: [low, medium, xhigh, max]
  - id: "02_implement_ico"
    efforts: [low, medium, high, max]
  - id: "03_debug_pagination"
    efforts: [medium, high, xhigh]
  - id: "04_design_catalog"
    efforts: [high, xhigh, max]
    # judge_required: false v Phase 1
  - id: "05_find_validation_gaps"
    efforts: [low, medium, high]
  - id: "06_strict_scope"
    efforts: [low, medium, xhigh]
```

**Celkový rozsah Phase 1:** 19 (task, effort) buněk × 3 rep = **57 běhů**.
S průměrnou délkou ~5 min/běh a 30s pauzou = ~5-7 hodin čistého času,
spuštěno v jedné session.

**Cost estimate Phase 1:** ~$70-130 v Anthropic credits (jen Opus 4.7, bez
judges). Bez Phase 2 jsme pod $150.

---

## 5. Klíčová technická rozhodnutí

### 5.1 `--max-turns` neexistuje v Claude Code 2.1.141

Spec § runner uvádí `--max-turns 60`, ale v aktuálním CLI tento flag
neexistuje. Použijeme `--max-budget-usd 10` jako jedinou enforcement
metodu. To znamená:

- Runaway běh se zastaví na ceně, ne na počtu turn.
- $10 hard cap při průměrném runu ~$0.50-2 je bezpečný strop ~10-20×
  očekávaný náklad.
- V `parse_session.py` se zaznamenává `stop_reason` z JSON, takže poznáme,
  jestli běh skončil přirozeně, nebo budget-capped.

### 5.2 `--bare` mode je závazný

Důvod: izolace od user-specific state (CLAUDE.md, hooks, plugins, MCP,
keychain). Spec to vyžaduje pro čistotu testu. `--bare` použijeme společně s:
- `-p` (print/headless mode)
- `--output-format json` (parsovatelný output)
- `--effort <level>`
- `--model <id>`
- `--allowedTools <csv>` (per-task whitelist v `meta.yaml`)
- `--max-budget-usd 10`
- `--permission-mode bypassPermissions` (jinak by interaktivní prompty zablokovaly)
- `ANTHROPIC_API_KEY` env var (vyžadováno `--bare`)

### 5.3 Python tooling: uv

`pyproject.toml` jako single source of truth. `uv venv && uv pip install -e .`
v setup. Lockfile (`uv.lock`) commitován pro deterministické builds.
V Phase 1 jsou Python závislosti minimální (stdlib `json`, `pathlib`),
v Phase 2 přibyde `pandas`, `matplotlib`, `openai`, `google-generativeai`,
`scipy`.

### 5.4 Synthetic initial_repo místo OSS forku (Phase 1)

Per dohoda: syntetický TS projekt pro Task 01 jako bring-up. Konkrétně
"users API" — Express-style controller + service + repository + Jest testy,
~10 souborů, ~30 výskytů `userId`. V Phase 2 swapneme za reálný OSS fork,
aby výsledky byly representativnější (real codebases mají noise, dead code,
inconsistent patterns).

### 5.5 Anonymizace pro budoucí judges (Phase 2 příprava)

Phase 1 anonymizaci nepotřebuje (žádní judges). Phase 2 implementuje
**regex strip + normalize headers**: odstranění zmínek o Claude/Anthropic/Opus
a normalizace `# <title>` na konstantní text. Triviální preprocessing, žádný
LLM-rewriter (aby se nezkreslil obsah designu).

---

## 6. Specifikace úloh

Detailní prompts, verify checks, hypotézy a expected solutions zůstávají
shodné se spec § "Specifikace testovacích úloh" — viz `effort-benchmark-spec.md`
sekce 4. Pro Phase 1 platí tyto úpravy:

| Task | Phase 1 zacházení | Poznámka |
|------|-------------------|----------|
| 01 rename | MVP, plná implementace | Synthetic TS repo |
| 02 IČO | Plná implementace, sprint 3 | Hidden test suite |
| 03 pagination | Plná implementace, sprint 3 | Pre-seeded failing test |
| 04 design | **Objective-only verify** | Žádný judge skóring; hypotézy o kvalitě zůstávají, ale neověřujeme empirické judges |
| 05 validation gaps | Plná implementace, sprint 3 | Ground truth list |
| 06 strict scope | Plná implementace, sprint 3 | Klíčové pro Opus 4.7 claim |

### 6.1 Task 01 (MVP) — synthetic repo specifikace

Aby measurement na Task 01 dával smysl, syntetický TS projekt musí:

- Obsahovat **~30 výskytů identifikátoru `userId`** napříč **10 soubory**:
  - `src/types.ts` — `UserId` type alias, field v `User` interface
  - `src/repositories/userRepository.ts` — DB-style metody
  - `src/services/userService.ts` — business logic
  - `src/controllers/userController.ts` — HTTP handlery
  - `src/middleware/auth.ts` — JWT extract
  - `src/utils/logger.ts` — log context
  - `src/__tests__/userRepository.test.ts`
  - `src/__tests__/userService.test.ts`
  - `src/__tests__/userController.test.ts`
  - `package.json`, `tsconfig.json`, `jest.config.js` (config bez `userId`)
- **Distraktory, které se NESMÍ přejmenovat:**
  - `userIdentifier` (jiný koncept, např. external login string)
  - `useridx` (Postgres-style column name v komentáři)
  - `UserID` v JSDoc komentáři (vysvětlení staré API verze)
  - `userId` v `node_modules/` (nikdy by se tam neměl model dostat, ale
    pojistka v case verify.sh narazí)
- **Tests must pass** v initial state (`npm install && npm test`).
- **TypeScript musí kompilovat** v initial state (`npx tsc --noEmit`).

Verify checks viz `tasks/01_rename/verify.sh`.

---

## 7. Měřené metriky

`parse_session.py` extrahuje ze `stdout.json`:

```python
{
  "input_tokens": int,
  "output_tokens": int,
  "cache_read_input_tokens": int,
  "cache_creation_input_tokens": int,
  "thinking_tokens": int,               # ze server_tool_use nebo usage
  "total_cost_usd": float,
  "tool_calls": [{"name": str, ...}],
  "tool_call_count": int,
  "tool_call_count_by_type": dict,
  "subagent_spawn_count": int,          # Agent tool calls
  "model_used": str,
  "stop_reason": str,                   # "end_turn" / "budget_limit_reached" / ...
  "session_id": str,
  "num_turns": int                      # iterations
}
```

`run_meta.json` doplňuje:

```json
{
  "run_id": "<task>_<model>_<effort>_run<N>_<timestamp>",
  "task": "01_rename",
  "model": "claude-opus-4-7",
  "effort": "low",
  "run_number": 1,
  "exit_code": 0,
  "wall_clock_ms": 87234,
  "timestamp": "2026-05-14T10:23:45+02:00",
  "claude_version": "2.1.141",
  "started_at": "...",
  "ended_at": "..."
}
```

`verify_result.json` (formát napříč úlohami):

```json
{
  "success": true,
  "checks": {
    "no_user_id_left": {"passed": true, "details": "0 occurrences"},
    "account_id_present": {"passed": true, "details": "28 occurrences"},
    "tsc_compiles": {"passed": true},
    "tests_pass": {"passed": true, "details": "12/12"},
    "distractors_untouched": {"passed": true},
    "diff_size_reasonable": {"passed": true, "details": "147 lines"}
  },
  "score": 1.0,                         // průměr passed checks, pro číselné srovnání
  "notes": ""
}
```

---

## 8. Plán implementace

### Sprint 1 — MVP (tato session)

- [x] PRD.md, README.md
- [x] `runner/run_single.sh` (basic flow)
- [x] `runner/lib/parse_session.py`
- [x] `tasks/01_rename/` kompletně (synthetic repo + prompt + verify + expected_solution)
- [x] `scripts/validate_verifier.sh`
- [x] `config/matrix.yaml`, `config/env.example`, `.gitignore`, `pyproject.toml`
- [x] Smoke: validate_verifier běží against expected_solution → success=true
- [ ] **Ručně provést jeden ostrý běh** s `ANTHROPIC_API_KEY` (mimo tuto session — neuvolňuju credits autora)

### Sprint 2 — Validace MVP datasetu (autor, 1-2 h)

- [ ] Spustit 4 běhy Task 01 (low, medium, xhigh, max) × 1 rep
- [ ] Ověřit, že `parse_session.py` produkuje očekávané hodnoty pro
  všechny metriky
- [ ] Pokud chybí pole v JSON outputu (např. thinking_tokens, subagents):
  upravit parser

### Sprint 3 — Zbývající úlohy (8-12 h)

- [ ] Task 02 (IČO) + hidden test suite
- [ ] Task 03 (pagination) + pre-seeded failing test
- [ ] Task 04 (design) — pouze objective verify (file exists + headers + word count)
- [ ] Task 05 (validation gaps) + ground truth list
- [ ] Task 06 (strict scope) — klíčové pro 4.7 stricter-respect claim

### Sprint 4 — Matrix runner (2-3 h)

- [ ] `run_matrix.sh` — load matrix.yaml, generate combos, shuffle with seed
- [ ] Progress tracking (per-run log line)
- [ ] Resumability (skip pokud `results/runs/<run_id>` existuje)
- [ ] Pause between runs (30s)
- [ ] Aggregátor po dokončení: `scripts/aggregate.py`

### Sprint 5 — Plný běh + analýza (8-10 h compute + 4-6 h analýzy)

- [ ] Spustit kompletní Phase 1 matrix (57 běhů)
- [ ] `scripts/aggregate.py` → `results/analysis/aggregated.csv`
- [ ] Manual review na anomálie a outliers
- [ ] Předběžné insights pro článek

### Phase 2 (deferred, mimo tento PRD)

- Sonnet 4.6 matrix (přidat ~36 běhů)
- LLM judges (GPT-5.5 + Gemini 3.1 Pro) pro Task 04
- Real OSS forky pro initial_repo
- Visualizace (bar charts, scatter, boxploty, Pareto frontier)
- `statistical_report.md` auto-gen

**Phase 1 timeline:** 20-30 h práce přes 1-2 týdny, ~$70-130 API credits.

---

## 9. Otevřené otázky ze spec — navrhované odpovědi

Spec § "Otevřené otázky k vyjasnění" obsahoval 5 bodů. Mé doporučené
odpovědi (s odůvodněním z pohledu kvality / náklad / složitost):

| # | Otázka | Návrh | Důvod |
|---|--------|-------|-------|
| 1 | Pin na 4.7 vs víc verzí? | **Pin na claude-opus-4-7 v Phase 1.** 4.6 přidat až v Phase 2 jen jako secondary scope. | Article hook je 4.7 stricter-respect claim. Cross-version je zajímavé, ale zdvojnásobuje cost. Tokenizer diff (1.0-1.35×) komplikuje fair comparison — vyžadovalo by extra normalizaci. |
| 2 | Sonnet 4.6 zahrnout? | **Phase 2, deferred.** Config-ready ale runs neprovádět. | Sonnet má jiné effort default (medium) a jinou hypotézu (medium = sweet spot). Smíchat s Opus výsledky v jedné fázi by zmátlo analýzu. |
| 3 | Anonymizace pro judges? | **Phase 2: regex strip + normalize headers.** Phase 1 N/A. | Judge bias je reálné riziko, ale full LLM rewrite by zkreslil obsah. Regex stripping (90% leaks) je dobrý cost/benefit. |
| 4 | Public release dat? | **Ano (autor potvrdil).** `results/runs/` publikované pod CC-BY-4.0. Framework code MIT. | Reprodukovatelnost. Repo už je veřejné. Žádný leak risk (žádná PII v synthetic projektech). |
| 5 | License? | **MIT pro framework, CC-BY-4.0 pro data.** | Standard open-source license + standard data license. MIT už existuje v repu. |

---

## 10. Rizika a mitigace

| Riziko | Pravděpodobnost | Dopad | Mitigace |
|--------|-----------------|-------|----------|
| Claude Code minor verze se během matrix změní (auto-update) | Střední | Vysoký (invalidates výsledky) | `claude_version` zapisován do `run_meta.json`; pre-flight check že verze odpovídá baseline; doc to v `KNOWN_LIMITATIONS.md` |
| Prompt cache cross-pollination mezi běhy | Vysoká | Střední (zlevní pozdější běhy) | 30s pauza mezi běhy (cooldown). Záznam `cache_read_input_tokens` separátně → cache vliv viditelný v datech, ne skrytý. |
| Anthropic API rate limit | Nízká | Střední | Retry s exponential backoff v `run_single.sh`. Při opakovaném failu skip + log → resume later. |
| `--max-turns` neexistuje (deviace od spec) | Jistá | Nízký | Použít `--max-budget-usd 10` jako hard cap. Stop reason zaznamenán. |
| Thinking tokens neviditelné v JSON | Střední | Střední | `parse_session.py` defensivně reportuje `null` pokud pole chybí. Validovat v MVP smoke run. |
| Verify.sh false positives/negatives | Střední | Vysoký (špatná data) | `validate_verifier.sh` testuje proti `expected_solution/` (must pass) i proti `wrong_solution/` (must fail) — phase 1 zatím jen expected. |
| n=3 nedává statistickou signifikanci | Jistá | Article credibility | Explicitně v článku + `KNOWN_LIMITATIONS.md`. Reportuj jako observational, ne inferenční. |
| Synthetic repo není representativní | Vysoká | Střední | V Phase 2 swap za real OSS fork. V Phase 1 článek to musí přiznat. |

---

## 11. Success criteria Phase 1

1. **Reprodukovatelnost**: Druhý běh stejné buňky produkuje hodnoty
   v rámci ±20% per metrika.
2. **Completeness**: 100% běhů má parsovatelný `stdout.json` a
   `verify_result.json`. Žádné chybějící buňky v CSV.
3. **Validity**: `validate_verifier.sh` projde proti `expected_solution/`
   pro všech 6 úloh.
4. **Insight**: Aggregated CSV umožní formulovat alespoň 3 konkrétní claims
   s reálnými čísly (např. "low effort na Task 01 dosáhne success rate X%
   za Y tokenů, max effort Z% za W tokenů").

---

## 12. Co tento framework explicitně neumí (Phase 1 limity)

Z spec § "Co tento framework nezvládne" + Phase 1 dodatky:

- Měření vlivu velikosti CLAUDE.md (`--bare` to vyřazuje)
- MCP overhead (taktéž)
- Long-running sessions s `/compact`
- Bedrock/Vertex variability
- Multi-language testing
- Kvalitativní hodnocení designu (Task 04) — odloženo do Phase 2
- Cross-model srovnání (Sonnet 4.6) — odloženo

---

## 13. Otevřené otázky pro autora (z této session zbylé)

1. **OSS repo pro Phase 2 Task 01:** jaké konkrétní OSS TS repo preferuješ pro
   swap? Návrhy (po MVP smoke): Express CRUD example, NestJS starter, nebo
   něco z `t3-oss/create-t3-app` typu.
2. **Phase 1 spuštění:** budeš provádět matrix sám lokálně, nebo bych měl
   ještě připravit `run_matrix.sh` s resume schopností? (Sprint 4 stejně dorazí
   po dokončení MVP smoke.)
3. **CI integration:** chceš v Phase 2 přidat GitHub Actions pro alespoň
   `validate_verifier.sh` na PR? (Nízký cost, vysoká hodnota — zabraňuje
   regresi verify scriptu při budoucích úpravách.)

---

**Konec PRD v0.1**
