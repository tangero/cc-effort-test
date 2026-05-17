# Benchmark Reliability And Codex Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the benchmark into a reproducible provider-neutral matrix for comparing model and effort suitability by task type.

**Architecture:** Keep task definitions and verifiers shared. Add provider-specific runners and parsers that emit one common artifact schema consumed by aggregation and report generation.

**Tech Stack:** Bash runners, Python 3.11 stdlib scripts, JSON/CSV artifacts, existing task-level TypeScript/Python verifiers.

---

### Task 1: Data Contract And Tests

**Files:**
- Create: `tests/test_aggregate.py`
- Create: `tests/test_codex_parser.py`
- Create: `tests/test_manifest.py`

- [ ] Add tests proving aggregation marks incomplete runs, exports score fields, and preserves check JSON.
- [ ] Add tests proving Codex JSONL is parsed into the common metrics shape.
- [ ] Add tests proving matrix cells are reproducibly shuffled by seed.

### Task 2: Shared Aggregation Improvements

**Files:**
- Modify: `scripts/aggregate.py`

- [ ] Add `score`, `functional_score`, `scope_score`, `checks_json`, `run_valid`, and `incomplete_reason` columns.
- [ ] Keep compatibility with existing columns.
- [ ] Treat missing `run_meta.json`, `metrics.json`, or `verify_result.json` as an invalid row instead of silently losing diagnostic value.

### Task 3: Reproducible Matrix Manifest

**Files:**
- Create: `scripts/build_matrix_manifest.py`
- Modify: `scripts/run_matrix.sh`

- [ ] Generate `results/matrix_<ts>_manifest.json` before running cells.
- [ ] Add `--seed` and `--provider claude|codex`.
- [ ] Shuffle planned cells with Python `random.Random(seed)`.
- [ ] Dispatch provider-specific single-run adapters.

### Task 4: Codex Adapter

**Files:**
- Create: `runner/lib/parse_codex_session.py`
- Create: `runner/run_single_codex.sh`

- [ ] Invoke `codex exec --json --ephemeral --ignore-user-config --ignore-rules`.
- [ ] Map benchmark effort to `model_reasoning_effort`.
- [ ] Emit the same result artifact files as the Claude runner.
- [ ] Record provider, model, effort, CLI version, seed, environment versions, and ignored config state.

### Task 5: Verifier And Metadata Hardening

**Files:**
- Modify: `tasks/01_rename/verify.sh`
- Modify: `tasks/03_debug_order/verify.sh`
- Modify: `tasks/*/meta.yaml`

- [ ] Keep functional score focused on behavioral checks.
- [ ] Move changed-file and diff-size checks into `diagnostics` or `scope_score`.
- [ ] Add `bug_type` and `difficulty_axes` metadata for reporting by task category.

### Task 6: Report Updates

**Files:**
- Modify: `scripts/generate_report.py`

- [ ] Load complete and incomplete run counts.
- [ ] Group by provider/model/task/effort.
- [ ] Surface partial cells and warn when `n < 3`.
- [ ] Include task taxonomy from `meta.yaml` when present.

### Task 7: Verification

**Files:**
- Run only.

- [ ] Run Python unit tests.
- [ ] Run aggregation over existing results.
- [ ] Run report generation.
- [ ] Run verifier validation on changed synthetic tasks where local dependencies permit it.
