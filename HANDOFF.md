# Handoff: Effort Benchmark Data Collection

**Datum:** 2026-05-17
**Repo:** https://github.com/tangero/cc-effort-test
**Live report:** https://patrickzandl--7768c20a501f11f1afc4ee650bb23af1.web.val.run

## Co je hotovo

### Framework
- `runner/run_single.sh` — isolated single-cell runner (subscription mode, žádné API credits navíc)
- `scripts/run_matrix.sh` — matrix orchestrace s `--resume` po crash/API výpadku
- `scripts/swe_bench_import.py` — import z SWE-bench Lite + **automaticky aplikuje `test_patch`** (per SWE-bench protokol)
- `scripts/aggregate.py` — CSV agregace
- `scripts/generate_report.py` — generuje `results/report.val.ts` z `results/runs/`
- Per-task `verify.sh` skripty s **per-test scoringem** (granular partial credit pro multi-aspect bugy)

### Tasky (13 total, vidí `tasks/`)
**Syntetické (6):** 01_rename, 02_implement_ico, 03_debug_order, 06_strict_scope, 07_security_audit, 08_async_bugs
**SWE-bench (7):** sympy-24909, sympy-22840, django-16379, django-16408, django-16820, django-16910, django-17051

### Data
- **145 runů celkem**, $115 cost
- Hlavně Opus 4.7 na low/medium/high/max
- `results/runs/` (gitignored) obsahuje plné per-run data
- `results/summary.csv` agregovaná

## Klíčové insights (cenné pro článek/handoff)

| Kategorie | Zjištění |
|-----------|----------|
| **Syntetické tasky** | Effort nediferenciuje na well-specified úlohách (01, 02, 07, 08 → 100% i u low) |
| **Single-aspect SWE-bench** | Ostrý práh — low ~25%, medium+ 100% (django-16408, 16820) |
| **Multi-aspect SWE-bench** | Pozvolný gradient — medium/high uváznou na 67% (1/3 testů), max prolomí na 60% full fix (sympy-22840) |
| **Debug bez failing testu** | `03_debug_order` Bug B nenalezen ani max effortem (název maskoval intent) |
| **Failure módy low effort** | Underexploration (16408), Overconfidence (16820 — 73-řádkový broken fix), Indecision (sympy-22840 — popíše ale neprovede) |
| **Max má hodnotu jen někdy** | Pro single-aspect: 2–4× dražší bez benefitu; pro multi-aspect: jediná cesta na 100% |

### Nejcennější instance pro článek
- **django-16408** — nejostřejší gradient (low 25% → medium+ 100%, n=3 každé)
- **django-16820** — sharp gradient + extreme outlier wall time (low run trval 142 minut)
- **sympy-22840** — multi-aspect bug, demonstruje "max má hodnotu"

## Co je nedokončeno (TODO)

### Krátkodobé
1. ✅ **Drill-down v reportu** — overview tabulka je plně klikatelná. Každý task otevírá detailní panel s pass rate grafem, cost grafem, per-run tabulkou, tool breakdownem, token stacked barem, iteracemi a per-check breakdownem. Původní pevná Django-16910 sekce byla nahrazena dynamickým pohledem.
2. ✅ **Kompletní sběr metrik v reportu** — `scripts/generate_report.py` nyní sbírá všechna dostupná data: input/output/cache-read/cache-creation/thinking tokens, num_turns, subagent_spawn_count, stop_reason, parse_errors, result_text_length, claude_version, exit_code, verify checks. Vizuálně zobrazuje Pareto scatter (cost vs quality), token stacked bar, iterace per effort a per-check breakdown pro multi-aspect tasky.
3. **Validace 03_debug_order při různých efforts** — máme jen low+max. Chybí medium, high. (Bug B pravděpodobně stejně nenajdeš, ale stojí za doplnění.)

### Střednědobé
4. **Sonnet 4.6 srovnání** — runner už podporuje, jen spustit `bash scripts/run_matrix.sh -m claude-sonnet-4-6`. Pozor: Sonnet nepodporuje xhigh, runner už to filtruje.
5. **Judge pipeline** — `scripts/prepare_judge_input.py` generuje Markdown pro Codex Desktop. Nikdy nespustěno → subjektivní hodnocení chybí.
6. **More multi-aspect SWE instances** — sympy-22840 je jediný náš multi-aspect case. Stojí za to najít další (např. django s víc f2p testy).

### Dlouhodobé
7. **Dataset publikace** — `results/runs/` se hodí publikovat (CC-BY-4.0), ale je >100 MB. Potřebuje split do release artefaktů.

## Známé problémy a gotchas

### Python 3.14 (macOS Homebrew) má odstraněné moduly
- `cgi` (Django pre-16xxx selže na `import cgi` ve `django/http/request.py`)
- `distutils` (sympy pre-21xxx selže na `from distutils.version import LooseVersion`)
- **Řešení:** používáme jen Django 4.2+ (`>=16xxx`) a Sympy 1.11+ (`>=21xxx`)

### C extensions bez Dockeru selžou
- `astropy` (erfa), `matplotlib`, `scipy`, `numpy build from source`
- **Řešení:** importujeme jen pure-Python projekty

### SWE-bench test_patch musí být aplikován
- Bez `test_patch` některé f2p testy procházejí už v base commitu (test je přidán až patchem)
- `swe_bench_import.py` to dělá automaticky od commitu `45db6d0`
- **Detekce problému:** Pokud low effort dostane 1.0 a tool_call_count=0, podezřele

### Subscription mode má residuální state
- `~/.claude/CLAUDE.md` se auto-loaduje — runner varuje, ale nemůže suppresovat (bez `--bare` módu)
- `--bare` vyžaduje `ANTHROPIC_API_KEY`, což by stálo API credits → použito subscription mode

### Anthropic API občas vrátí 500 chyby
- Stalo se nám během matrix runu — 29/41 cells dostalo "API Error: 500"
- `runner/run_single.sh` to nedetekuje, hlásí success (jen Claude response = error message)
- **Recovery:** `generate_report.py` ignoruje runy s "API Error" ve stdout

### Long-running runs (10–140 minut)
- Občas Claude uvázne v dlouhém průzkumu (max budget=$10 default, žádný wall time limit)
- Žádný timeout, dokud nepřekročí budget nebo neudělá `stop`
- **Pozor:** matrix běží sekvenčně — jeden uvíznutý run blokuje další

## Jak v tom pokračovat

### Pro novou instanci SWE-bench
```bash
python3 scripts/swe_bench_import.py --list --dataset swe-bench-lite --limit 300 | grep <project>
python3 scripts/swe_bench_import.py --instance <id>
# Generated verify.sh může potřebovat manuální fix testovacích cest
# (Django: použij tests/runtests.py místo pytest; sympy: pin path k test souboru)
bash runner/run_single.sh tasks/swe_<id> low 1  # smoke test
```

### Pro nový syntetický task
1. `tasks/NN_name/` se strukturou: `prompt.txt`, `meta.yaml`, `verify.sh`, `initial_repo/`, `hidden_tests/`, `expected_solution/`
2. `bash scripts/validate_verifier.sh tasks/NN_name` — ověří že `expected_solution/` → success=true
3. Smoke test: `bash runner/run_single.sh tasks/NN_name low 1`
4. README popisuje detaily formátu (sekce "Jak přidat nový task")

### Pro spuštění matice
```bash
bash scripts/run_matrix.sh -t task1,task2 -e low,medium,high,max -n 3 --resume
```
Pokud doběhne s API errors, smaž jen ty:
```python
# scripts/cleanup_api_errors.py — nemáme, ale viz konverzace pro one-liner
```

### Pro update val.town reportu
```bash
python3 scripts/generate_report.py
# Pak nahrát výsledek do val.town přes MCP nebo `vt push` z working dir
```

## Klíčové soubory ke čtení

| Soubor | Co tam je |
|--------|-----------|
| `README.md` | Hlavní dokumentace, recap výsledků |
| `effort-benchmark-spec.md` | Původní spec studie |
| `PRD.md` | Produktové požadavky |
| `runner/run_single.sh` | Hlavní runner — language detection, isolation, verify dispatch |
| `scripts/swe_bench_import.py` | SWE-bench importér s test_patch protokolem |
| `scripts/generate_report.py` | Report generator |
| `tasks/swe_django__django-16408/verify.sh` | Referenční Django verify (runtests.py format) |
| `tasks/swe_sympy__sympy-22840/verify.sh` | Referenční per-test scoring (multi-aspect) |
| `docs/superpowers/` | Plans + specs z předchozích iterací |

## Kontakt / kontext

- Vlastník: Patrick Zandl (`zandl@marigold.cz`)
- Cíl: Empirická data pro článek o `--effort` parametru
- Tone: Reálná čísla, ne marketing. Co `--effort` opravdu mění, co je placebo.
