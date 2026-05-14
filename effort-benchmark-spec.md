# Effort Benchmark Framework - Specifikace projektu

## Cíl projektu

Vytvořit automatizovaný testovací framework pro empirické změření dopadu `effort` parameteru v Claude Code na:

1. **Spotřebu tokenů** (input, output, cache, thinking)
2. **Wall clock time**
3. **Kvalitu odvedené práce** (objektivně přes verify scripts, subjektivně přes LLM-as-judge)
4. **Chování modelu** (počet tool callů, subagentů, iterací)

Výsledkem má být dataset, který umožní vytvořit přehlednou tabulku s reálnými daty, ne pouze s community anekdotami nebo Anthropic doporučeními.

## Dokumentace k Effort od Antrhopic

- https://platform.claude.com/docs/en/build-with-claude/effort.md
- https://code.claude.com/docs/en/model-config.md

## Klíčové faktografické předpoklady

Tyto fakty jsou základem návrhu testu a musí být v implementaci respektovány:

### Dostupnost effort levels podle modelu

| Model | Dostupné levels | API default | Claude Code default |
|-------|-----------------|-------------|---------------------|
| Opus 4.7 | low, medium, high, xhigh, max | high | xhigh (od v2.1.117) |
| Opus 4.6 | low, medium, high, max | high | high |
| Sonnet 4.6 | low, medium, high, max | high | high |

### Doporučení Anthropic (z oficiální dokumentace)

- **Pro Sonnet 4.6**: medium je doporučený default pro většinu aplikací
- **Pro Opus 4.7**: xhigh je doporučený starting point pro coding/agentic, high jako minimum pro intelligence-sensitive workloads
- **max**: explicitně varováno před overthinking a diminishing returns
- **Opus 4.7 respektuje effort levels striktněji** než 4.6, zejména na low/medium

### Tokenizer

Opus 4.7 má nový tokenizer, který stejný vstup mapuje na 1,0-1,35x víc tokenů než 4.6. Pro férové srovnání modelů to musí být zohledněno v interpretaci výsledků.

### max_tokens

Pro xhigh a max efforty doporučuje Anthropic `max_tokens` minimálně 64k. Pro testovací framework nastavit jednotně 128k, aby ani max nehit cap a všechny levely měly stejný strop.

### Ultrathink

Jediný rozpoznávaný keyword v promptu, pinuje effort na high pro daný turn. Variace ("think harder", "think more") nefungují, jsou passed-through jako běžný text. **V testovacích promptech vyloučit jakékoli zmínky o "think" pro čistotu testu.**

## Architektura projektu

```
effort-benchmark/
├── README.md                        # tento dokument
├── tasks/                           # definice testovacích úloh
│   ├── 01_rename/
│   ├── 02_implement_ico/
│   ├── 03_debug_pagination/
│   ├── 04_design_catalog/
│   ├── 05_find_validation_gaps/
│   └── 06_strict_scope/             # nová úloha pro test stricter respect na 4.7
├── runner/
│   ├── run_single.sh
│   ├── run_matrix.sh
│   ├── run_judge.py
│   └── lib/
│       ├── parse_session.py         # parser JSON outputu z claude -p
│       └── git_helpers.sh
├── prompts/
│   ├── judge_design.py              # judge rubric pro design úlohu
│   └── judge_implementation.py
├── results/
│   ├── runs/                        # raw output z každého běhu
│   └── analysis/
│       ├── aggregated.csv
│       ├── charts/
│       └── statistical_report.md
├── scripts/
│   ├── aggregate.py
│   ├── visualize.py
│   └── validate_verifier.sh         # ověří, že verify.sh produkuje očekávané výsledky
├── config/
│   ├── matrix.yaml                  # definice matice běhů
│   └── env.example
└── docs/
    ├── METHODOLOGY.md
    ├── INTERPRETING_RESULTS.md
    └── KNOWN_LIMITATIONS.md
```

## Testovací matice

### Dimenze testu

```yaml
models:
  - claude-opus-4-7
  - claude-sonnet-4-6   # volitelně pro fázi 2

efforts:
  opus_4_7: [low, medium, high, xhigh, max]
  sonnet_4_6: [low, medium, high, max]

repetitions: 3

tasks:
  - id: "01_rename"
    type: "mechanical"
    efforts_to_test: [low, medium, xhigh, max]   # přidán max pro test overthinking hypotézy
    objective_verify: true
    judge_required: false

  - id: "02_implement_ico"
    type: "specified_implementation"
    efforts_to_test: [low, medium, high, max]    # přidán max pro test overthinking
    objective_verify: true
    judge_required: false                         # objektivní testy stačí

  - id: "03_debug_pagination"
    type: "bounded_debugging"
    efforts_to_test: [medium, high, xhigh]
    objective_verify: true
    judge_required: false

  - id: "04_design_catalog"
    type: "open_design"
    efforts_to_test: [high, xhigh, max]
    objective_verify: false
    judge_required: true

  - id: "05_find_validation_gaps"
    type: "information_retrieval"
    efforts_to_test: [low, medium, high]
    objective_verify: true                        # ground truth list
    judge_required: false

  - id: "06_strict_scope"
    type: "scope_compliance"
    efforts_to_test: [low, medium, xhigh]
    objective_verify: true                        # diff size, scope checking
    judge_required: false
```

### Celkový rozsah

- Fáze 1 (jen Opus 4.7): 5 efforts × ~3 efforts per task × 6 tasks × 3 repetitions = **cca 54 běhů**
- Fáze 2 (Sonnet 4.6): ~36 běhů
- **Celkem: 90 běhů** pokud děláme oba modely

### Randomizace

Pořadí běhů musí být randomizováno před spuštěním. Implementace v `run_matrix.sh` přes `shuf` nebo Python `random.shuffle` se seedem pro reprodukovatelnost.

## Specifikace testovacích úloh

### Společné požadavky pro všechny úlohy

Každá úloha musí mít:

- `prompt.txt` - **přesný** prompt pro Claude Code, kopírovaný bit-by-bit do každého běhu
- `initial_repo.tar.gz` - výchozí stav repa, packed pro reprodukovatelnost
- `verify.sh` - bash script produkující JSON s výsledky verifikace
- `meta.yaml` - metadata úlohy (typ, popis, expected duration, success criteria)
- `expected_solution/` - reference řešení pro validaci verify.sh (NE pro porovnávání s output modelu)
- `README.md` - lidsky čitelný popis úlohy

### Úloha 01: Rename (mechanical)

**Popis:** TypeScript projekt s ~30 výskyty identifikátoru `userId` v 8-12 souborech (definice, parametry, return values, JSDoc komentáře, unit testy).

**Prompt:**
```
Rename the identifier `userId` to `accountId` throughout the codebase.
Update all related JSDoc comments to reflect the new naming.
Ensure that all tests still pass after the rename.
Do not modify any logic or behavior, only the identifier name.
```

**Verify checks:**
- Count of `userId` occurrences after rename = 0
- Count of `accountId` occurrences > 0 and matches expected count
- TypeScript compiles without errors (`npx tsc --noEmit`)
- All tests pass (`npm test`)
- Similar identifiers untouched (`userIdentifier`, `useridx`, `UserID` v komentářích)
- Diff size reasonable (< 200 lines změn)

**Hypotéza:** Low effort dosahuje 100% success rate na binární metriky, vyšší efforty produkují srovnatelný výsledek za výrazně víc tokenů. Max může over-engineerovat (přidávat refactory, které nebyly požadovány).

### Úloha 02: Implement IČO validation (specified)

**Popis:** Empty file, model má implementovat funkci podle jasné specifikace.

**Prompt:**
```
Implement a TypeScript function `validateICO(input: string): ValidationResult`
in `src/validators/ico.ts` that validates a Czech company identifier (IČO).

The IČO format is:
- Exactly 8 digits
- The 8th digit is a checksum computed as follows:
  1. Multiply digits 1-7 by weights 8, 7, 6, 5, 4, 3, 2 respectively
  2. Sum the products
  3. Compute the remainder modulo 11
  4. If remainder is 0, checksum is 1
  5. If remainder is 1, checksum is 0
  6. Otherwise, checksum is 11 minus the remainder

The `ValidationResult` type should be:
type ValidationResult =
  | { valid: true }
  | { valid: false; reason: string };

Handle edge cases: empty string, non-digit characters, wrong length.

Write comprehensive unit tests in `src/validators/ico.test.ts` using the existing
test framework (Jest is already configured).
```

**Verify checks:**
- File `src/validators/ico.ts` exists
- File `src/validators/ico.test.ts` exists
- TypeScript compiles
- Predefined hidden test suite (model nezná) passes against implementation:
  - Valid IČO: `25596641`, `27074358`, `45274649`
  - Invalid checksum: `25596642`
  - Wrong length: `123`, `123456789`
  - Non-digits: `abc12345`, `1234567a`
  - Empty: ``
- Model's own tests pass
- No unnecessary additions (e.g. doesn't refactor unrelated files)

**Hypotéza:** Medium produkuje srovnatelný výsledek s high. Max over-engineeruje (přidává Czech-specific logic, lokalizace error messages, atd.).

### Úloha 03: Debug pagination (bounded debugging)

**Popis:** Repo s implementovanou API endpoint pro paginaci, který má off-by-one error v `lastPage` výpočtu. Failing test je připraven.

**Prompt:**
```
The test `test_pagination_last_page_calculation` in `src/api/__tests__/pagination.test.ts`
is failing. Find the root cause and fix it.

Do not modify the test file. The bug is in the implementation, not in the test.

After your fix, ensure that all other tests still pass.
```

**Verify checks:**
- Failing test now passes
- No other tests broken
- Diff doesn't include changes to `pagination.test.ts`
- Diff is reasonably small (< 50 lines)
- Bug fix targets the actual root cause (pre-defined location check)

**Hypotéza:** Rozdíl mezi medium a xhigh je v počtu Read/Grep tool callů pro exploration. Kvalita fixu by měla být stejná napříč levely. xhigh může přidávat zbytečné refactory.

### Úloha 04: Design catalog (open design)

**Popis:** Otevřený design problém, output je Markdown specifikace.

**Prompt:**
```
Design data models and a REST API for a product catalog system with the following requirements:

- Products have variants (size, color, etc.)
- Prices are localized per market (CZ, SK, DE, AT)
- Inventory tracking per variant and per warehouse
- Support for product bundles (one product made of multiple others)
- Migration strategy from a hypothetical existing flat schema where each variant
  is a separate row with denormalized product data

Output your design as a single Markdown document at `docs/design.md` with:
1. Data model definitions (entities, relationships, key fields)
2. Migration strategy from the flat schema
3. REST API endpoints (paths, methods, request/response schemas)
4. Non-functional considerations (performance, scalability, consistency)

This is a design document. Do not implement any code.
```

**Verify checks (objective):**
- File `docs/design.md` exists
- Document has all four required sections (regex match na headers)
- Document length > 500 words (sanity check)
- No code files created (jen design dokument)

**Judge evaluation (LLM-as-judge, GPT-5.5 + Gemini 3.1):**

Rubric:
- Functional completeness (1-5): pokrývá všechny zmíněné požadavky
- Data model quality (1-5): normalizace, foreign keys, type clarity
- API design (1-5): RESTful conventions, error handling, versioning
- Migration strategy (1-5): konkrétní steps, backwards compatibility
- Non-functional concerns (1-5): scalability, consistency, performance

**Hypotéza:** Tady čekáme největší kvalitativní rozdíl. High vs xhigh vs max - xhigh by měl být sweet spot, max může over-engineerovat.

### Úloha 05: Find validation gaps (information retrieval)

**Popis:** Backend repo s ~20 API endpointy, z toho 5 nemá vstupní validaci. Ground truth list problematických endpointů existuje.

**Prompt:**
```
Analyze the API endpoints in this codebase. For each endpoint, determine whether
it validates its input data (request body, query parameters, path parameters).

Output a JSON file at `analysis.json` with the following structure:
{
  "endpoints_without_validation": [
    {
      "path": "/api/...",
      "method": "POST",
      "file": "src/api/...",
      "missing_validation": "description of what should be validated"
    }
  ]
}

Include only endpoints that actually lack validation. Do not include endpoints
that have proper validation already.
```

**Verify checks:**
- File `analysis.json` exists and is valid JSON
- Schema validation passes
- Precision: % správně identifikovaných (TP / (TP + FP))
- Recall: % všech problematických endpointů zachycených (TP / (TP + FN))
- F1 score

**Hypotéza:** Low effort zachytí jen zjevné případy (nízká recall). Medium dosáhne reasonable precision/recall trade-off. High může over-report (nižší precision).

### Úloha 06: Strict scope compliance (test stricter respect Opus 4.7)

**Popis:** Úloha, jejíž prompt je úmyslně narrow, ale codebase nabádá k širším úpravám.

**Prompt:**
```
Add input validation to the `createUser` function in `src/users/create.ts`.
Validate that:
- email is a valid email format
- username is between 3 and 32 characters

Return appropriate error responses for invalid input.
```

**Co repo obsahuje navíc:** podobné funkce `updateUser`, `createOrganization` bez validace. Otevřená pozvání pro model "improve while you're at it."

**Verify checks:**
- `createUser` má požadovanou validaci (objective: pre-defined test passes)
- **Diff netýká se jiných souborů**: changes pouze v `src/users/create.ts` a jeho test souboru
- Diff size < 80 lines
- `updateUser`, `createOrganization` zůstaly netknuté

**Hypotéza klíčová pro článek:** Opus 4.7 na low respektuje scope striktně, na xhigh "over-helpfully" rozšiřuje. Tato úloha přímo testuje Anthropic claim o stricter respect.

## Implementace runneru

### `run_single.sh`

```bash
#!/bin/bash
# Args: $1=task_dir, $2=effort_level, $3=run_number, $4=model

set -euo pipefail

TASK_DIR="$1"
EFFORT="$2"
RUN_N="$3"
MODEL="${4:-claude-opus-4-7}"

TASK_ID="${TASK_DIR##*/}"
TIMESTAMP=$(date +%s)
RUN_ID="${TASK_ID}_${MODEL}_${EFFORT}_run${RUN_N}_${TIMESTAMP}"
RESULT_DIR="results/runs/$RUN_ID"

mkdir -p "$RESULT_DIR"

# Setup isolated working directory
WORKDIR=$(mktemp -d -t effort-test-XXXXXX)
trap "rm -rf $WORKDIR" EXIT

# Extract initial state
tar -xzf "$TASK_DIR/initial_repo.tar.gz" -C "$WORKDIR"

# Capture starting git state for diff later
cd "$WORKDIR"
git init -q 2>/dev/null || true
git add -A
git commit -q -m "initial" 2>/dev/null || true

# Load prompt
PROMPT=$(cat "$TASK_DIR/prompt.txt")

# Determine allowed tools from task meta
ALLOWED_TOOLS=$(yq '.allowed_tools | join(",")' "$TASK_DIR/meta.yaml")

# Execute Claude Code
START_TIME=$(date +%s%N)
set +e
claude --bare -p "$PROMPT" \
    --effort "$EFFORT" \
    --model "$MODEL" \
    --output-format json \
    --allowedTools "$ALLOWED_TOOLS" \
    --max-turns 60 \
    --max-budget-usd 10 \
    > "$RESULT_DIR/stdout.json" \
    2> "$RESULT_DIR/stderr.log"
EXIT_CODE=$?
set -e
END_TIME=$(date +%s%N)

# Capture final state
git diff > "$RESULT_DIR/final_diff.patch"
git diff --stat > "$RESULT_DIR/diff_stat.txt"

# Run verification
bash "$TASK_DIR/verify.sh" > "$RESULT_DIR/verify_result.json" 2>"$RESULT_DIR/verify.log" || true

# Capture run metadata
WALL_CLOCK_MS=$(( (END_TIME - START_TIME) / 1000000 ))
cat > "$RESULT_DIR/run_meta.json" <<EOF
{
  "run_id": "$RUN_ID",
  "task": "$TASK_ID",
  "effort": "$EFFORT",
  "model": "$MODEL",
  "run_number": $RUN_N,
  "exit_code": $EXIT_CODE,
  "wall_clock_ms": $WALL_CLOCK_MS,
  "timestamp": "$(date -Iseconds)",
  "claude_version": "$(claude --version 2>/dev/null | head -1)"
}
EOF

echo "Completed: $RUN_ID"
```

### `run_matrix.sh`

Klíčové vlastnosti:
- Loaduje matici z `config/matrix.yaml`
- Generuje všechny kombinace
- **Randomizuje pořadí** se seedem pro reprodukovatelnost
- Mezi běhy pause (30s) pro cache cooldown
- Tracking progress a možnost resume při přerušení
- Aggregátor po dokončení vytvoří `results/analysis/aggregated.csv`

### `parse_session.py`

Parser pro `stdout.json` z `claude -p`. Extrahuje:

```python
{
    "input_tokens": int,
    "output_tokens": int,
    "cache_read_input_tokens": int,
    "cache_creation_input_tokens": int,
    "thinking_tokens": int,            # z usage breakdown
    "tool_calls": [
        {"name": str, "input_summary": str}
    ],
    "tool_call_count_by_type": dict,
    "subagent_spawn_count": int,
    "total_cost_usd": float,
    "model_used": str,
    "stop_reason": str
}
```

## LLM-as-judge implementace

### `run_judge.py`

Pro úlohy s `judge_required: true` (primárně úloha 04).

**Architektura:**

```python
class Judge:
    def __init__(self, provider: str, model: str, api_key: str):
        self.provider = provider  # "openai" | "google" | "anthropic"
        self.model = model
        self.api_key = api_key

    def evaluate_single(self, proposal: str, rubric: dict) -> dict:
        """Returns scored evaluation with reasoning per criterion."""

    def evaluate_pair(self, proposal_a: str, proposal_b: str,
                       rubric: dict, order: str) -> dict:
        """Pairwise comparison. order = 'ab' or 'ba' for bias control."""
```

**Multi-judge protokol:**

Pro každou pair comparison se spustí:

1. Judge A (GPT-5.5) hodnotí v pořadí (X, Y)
2. Judge A (GPT-5.5) hodnotí v pořadí (Y, X) - position bias control
3. Judge B (Gemini 3.1 Pro) hodnotí v pořadí (X, Y)
4. Judge B (Gemini 3.1 Pro) hodnotí v pořadí (Y, X)

Aggregace:
- Pokud všichni 4 hodnocení souhlasí → high confidence
- 3 z 4 souhlasí → medium confidence
- 2 z 4 → low confidence, závěr = "no clear winner"

**Inter-rater agreement:**

Po dokončení všech hodnocení spočítat Cohen's kappa mezi judges. Pokud kappa < 0.4, výsledky pro úlohu 04 nejsou validní a v článku to musí být explicitně přiznáno.

### Rubric pro úlohu 04 (catalog design)

V `prompts/judge_design.py`:

```python
JUDGE_PROMPT_TEMPLATE = """
You are evaluating an architectural design proposal for a product catalog system.
Score each dimension on a scale of 1-5 based ONLY on the rubric below.

REQUIREMENTS THE PROPOSAL SHOULD ADDRESS:
- Products with variants (size, color, etc.)
- Localized prices per market (CZ, SK, DE, AT)
- Inventory tracking per variant and warehouse
- Product bundles (composition of multiple products)
- Migration from flat denormalized schema

RUBRIC:

1. FUNCTIONAL COMPLETENESS (1-5):
   5 = All 5 requirements explicitly addressed with concrete solutions
   4 = 4 of 5 requirements addressed, one partially
   3 = 3 requirements well, 2 missing or hand-waved
   2 = Major gaps in requirements
   1 = Misses fundamental requirements

2. DATA MODEL QUALITY (1-5):
   - Appropriate normalization for stated requirements
   - Foreign keys and relationships explicit
   - Field types clearly specified
   - Identifies primary keys and uniqueness constraints
   - Handles edge cases (e.g., bundle of bundles)

3. API DESIGN (1-5):
   - Consistent naming conventions
   - RESTful where appropriate (or justified deviation)
   - Error handling specified
   - Request/response schemas defined
   - Versioning strategy mentioned

4. MIGRATION STRATEGY (1-5):
   - Concrete sequence of steps from flat schema
   - Data transformation logic explained
   - Handles existing data integrity
   - Rollback considerations
   - Performance impact assessed

5. NON-FUNCTIONAL CONCERNS (1-5):
   - Scalability discussed (e.g., partitioning strategy)
   - Performance considerations (e.g., indexing)
   - Consistency model (eventual vs strong)
   - Concurrency handling

IMPORTANT INSTRUCTIONS:
- Score ONLY based on rubric content, not writing quality or length
- A concise proposal that covers the rubric scores equally to a verbose one
- Provide reasoning for each score citing specific parts of the proposal
- Output ONLY valid JSON, no preamble or commentary

OUTPUT FORMAT (strict JSON):
{{
  "functional_completeness": {{"score": N, "reasoning": "..."}},
  "data_model_quality": {{"score": N, "reasoning": "..."}},
  "api_design": {{"score": N, "reasoning": "..."}},
  "migration_strategy": {{"score": N, "reasoning": "..."}},
  "non_functional": {{"score": N, "reasoning": "..."}},
  "total": N
}}

PROPOSAL TO EVALUATE:
{proposal_text}
"""
```

## Data aggregation a analýza

### `aggregate.py`

Vytvoří CSV s jedním řádkem per run:

```
run_id, task_id, model, effort, run_number,
input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,
thinking_tokens, total_tokens, total_cost_usd,
tool_call_count, subagent_count,
wall_clock_ms, exit_code,
verify_success, verify_score, judge_score
```

### `visualize.py`

Generuje grafy:

1. **Token consumption per effort level** (bar chart, jeden graf per task)
2. **Token vs quality scatter** (per task, identifikace Pareto frontier)
3. **Tool call count distribution** (boxplot per effort)
4. **Wall clock time** (per effort)
5. **Success rate** (binary tasks, per effort)
6. **Cost per successful run** (efficiency metric)

### `statistical_report.md`

Auto-generated markdown report s:
- Summary statistics per (task, effort)
- Standard deviations
- Pairwise comparisons mezi effort levely (s caveats o n=3)
- Identifikace anomálií (outliers, failed runs)
- Inter-rater agreement pro judge tasks

## Reprodukovatelnost a validita

### Co kontrolovat před spuštěním

1. **Verify scripts otestovány**: Pro každou úlohu spustit `validate_verifier.sh`, který:
   - Aplikuje `expected_solution/` na initial repo
   - Spustí `verify.sh`
   - Ověří, že produkuje `success: true`
   - Aplikuje záměrně chybné řešení
   - Ověří, že produkuje `success: false`

2. **Verze Claude Code zaznamenána**: V každém run_meta.json je `claude_version`.

3. **Model ID zaznamenán**: Použít full model ID (`claude-opus-4-7`), ne alias, pro pevné pinování.

4. **Network conditions**: Test ideálně běží během stejných hodin (nikoli noc + den smíšeně).

### Co se nesmí měnit během testu

- Verze Claude Code
- `~/.claude/settings.json`
- Hardware (stejný stroj)
- Prompt texty (žádné typo opravy během testu - pokud chyba, restart celé úlohy)

### Známé limity, které musí být v článku explicitně přiznané

1. **n=3 nedává statistickou signifikanci** - výsledky jsou observational, ne inferenční
2. **5-6 úloh není reprezentativní** pro všechnu coding práci
3. **Single judge model bias** - i s multi-judge protokolem existuje shared bias
4. **Anthropic-side variability** - prompt caching, rate limiting, model updates během testu
5. **`--bare` mode** - reálné používání Claude Code zahrnuje MCP, hooks, CLAUDE.md - náš test je purer ale méně realistický

## Plán implementace

### Sprint 1: Infrastruktura (4-6 hodin)

- [ ] Setup repository structure
- [ ] Implementovat `run_single.sh` s basic flow
- [ ] Implementovat `parse_session.py` pro extrahování metrik
- [ ] Implementovat verify framework (jeden referenční verify.sh)
- [ ] Test na jednoduchém dummy úkolu (např. "echo hello world")

### Sprint 2: První úloha end-to-end (3-4 hodiny)

- [ ] Připravit úlohu 01 (rename) kompletně
- [ ] Initial_repo.tar.gz s realistickým TypeScript kódem
- [ ] verify.sh s všemi checks
- [ ] expected_solution/ pro validaci verify.sh
- [ ] `validate_verifier.sh` projde
- [ ] Smoke test: 1 běh na low, 1 běh na xhigh
- [ ] Ověřit, že JSON parsing produkuje očekávané hodnoty

### Sprint 3: Zbytek úloh (8-12 hodin)

- [ ] Úlohy 02, 03, 05, 06 podle specifikace výše
- [ ] Úloha 04 (design) - verify pouze structure check
- [ ] Pro každou úlohu: prompt + repo + verify + expected_solution + validate

### Sprint 4: Matrix runner (2-3 hodiny)

- [ ] `run_matrix.sh` s randomizací a resumability
- [ ] `config/matrix.yaml` parser
- [ ] Progress tracking
- [ ] Error recovery (retry on transient failures)

### Sprint 5: Mini-experiment (3-4 hodiny)

- [ ] Spustit matici jen pro úlohu 01 (~12 běhů)
- [ ] Validovat, že data jsou kompletní a interpretovatelná
- [ ] Tweak parser pokud chybí metriky
- [ ] Tweak verify pokud false positives/negatives

### Sprint 6: Judge framework (4-5 hodin)

- [ ] OpenAI client pro GPT-5.5
- [ ] Google client pro Gemini 3.1 Pro
- [ ] Pairwise comparison s order randomization
- [ ] Single-output scoring s rubric
- [ ] Inter-rater agreement calculator

### Sprint 7: Plná matice běhů (8-10 hodin běhu + 1-2 hodiny supervize)

- [ ] Spustit kompletní matrix
- [ ] Monitorovat průběh, řešit transient errors
- [ ] Validovat completeness všech run dir

### Sprint 8: Analýza a vizualizace (4-6 hodin)

- [ ] `aggregate.py` produkuje finální CSV
- [ ] `visualize.py` generuje sadu grafů
- [ ] `statistical_report.md` auto-generated
- [ ] Manual review výsledků - hledat anomálie

### Sprint 9: Článek (8-12 hodin, mimo scope tohoto frameworku)

- [ ] Integrace dat do článku
- [ ] Diskuse výsledků
- [ ] Caveats a limitations
- [ ] Recommendations pro čtenáře

**Total estimate: 50-65 hodin práce, rozložené na 2-3 týdny.**

## Technické požadavky

### Závislosti

```
# Runtime
- bash 5.x
- Node.js 20+ (pro Claude Code)
- Claude Code v2.1.117+
- Python 3.11+
- yq (YAML parser pro bash)
- jq

# Python packages
- anthropic
- openai
- google-generativeai
- pandas
- matplotlib
- plotly
- scipy (pro statistické testy)
- pyyaml
```

### API klíče potřebné

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
```

### Subscription nebo billing

- Claude Code: Max plán nebo API credits (cca $100-200 odhad pro celou matici)
- OpenAI: $20-50 pro judge runs na GPT-5.5
- Google: $20-50 pro Gemini 3.1 Pro judge runs

**Celkový odhad nákladů: $140-300 v API kreditech.**

## Success criteria projektu

Framework je úspěšný, pokud:

1. **Reprodukovatelnost**: Druhé spuštění stejné matice produkuje výsledky v rámci 20% variance per cell
2. **Completeness**: 100% běhů má parsovatelný JSON output a verify výsledek
3. **Validity**: Verify scripts mají 0 false positives a 0 false negatives na expected_solution testech
4. **Judge reliability**: Inter-rater agreement (Cohen's kappa) > 0.5 pro úlohu 04
5. **Insight**: Aggregated CSV umožňuje formulovat alespoň 5 konkrétních claims s reálnými čísly

## Co tento framework nezvládne (out of scope)

- Testování modelů přes Bedrock/Vertex (jiné chování, custom test)
- Měření vlivu CLAUDE.md velikosti na effort behavior
- Testování MCP server overhead (`--bare` mode to záměrně vyřazuje)
- Long-running sessions s `/compact` (každý běh je fresh)
- Side-by-side comparison s GPT-5.5 nebo Gemini jako alternativami (jen jako judges)
- Cross-language testing (jen TypeScript projects)

## Otevřené otázky k vyjasnění před implementací

1. **Model verze**: Pin na `claude-opus-4-7` nebo testovat víc verzí (4.6, 4.7) souběžně?
2. **Sonnet zahrnout?**: Plná matice se Sonnet 4.6 zdvojnásobuje rozsah. Fázovat?
3. **Anonymizace pro judges**: Před judge evaluací odstranit jakékoli stopy effort levelu z výstupu? Markdown header, model self-references atd.
4. **Public release dat**: Po dokončení publikovat raw runs/ na GitHubu pro reprodukovatelnost?
5. **License**: Pro framework samotný - MIT? Pro datasets - CC-BY?

## Reference

- [Anthropic Effort parameter docs](https://platform.claude.com/docs/en/build-with-claude/effort)
- [Claude Code model configuration](https://code.claude.com/docs/en/model-config)
- [Claude Code headless mode](https://code.claude.com/docs/en/headless)
- [What's new in Claude Opus 4.7](https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-7)

---

**Verze dokumentu:** 1.0
**Datum:** 14. května 2026
**Status:** Specifikace připravená pro implementaci
