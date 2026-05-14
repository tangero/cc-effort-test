# Task 02 — Implement IČO Validation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vytvořit benchmarkovací úlohu `02_implement_ico` — syntetický TypeScript projekt s existujícími validátory jako vzorem, do kterého model implementuje funkci `validateICO` dle specifikace.

**Architecture:** `initial_repo/` obsahuje funkční TypeScript projekt se dvěma hotovými validátory (email, phone) jako vzorem pro konvence. Model dostane prázdný `ico.ts` a musí implementovat validátor i testy. Verifikace probíhá přes skrytou testovací sadu (`hidden_tests/ico.hidden.test.ts`), která se při verifikaci dočasně zkopíruje do workdir, spustí Jest a smaže.

**Tech Stack:** TypeScript 5.4, Jest 29, ts-jest, bash, jq

---

## Struktura souborů

```
tasks/02_implement_ico/
  prompt.txt                                  ← zadání pro model
  meta.yaml                                   ← metadata úlohy
  README.md                                   ← lidsky čitelný popis
  verify.sh                                   ← verifikační skript
  hidden_tests/
    ico.hidden.test.ts                        ← skrytá testovací sada (9 cases)
  expected_solution/
    src/validators/ico.ts                     ← referenční implementace
    src/validators/ico.test.ts                ← referenční testy
  initial_repo/
    package.json
    tsconfig.json
    jest.config.js
    src/
      types.ts                                ← sdílený ValidationResult typ
      validators/
        email.ts                              ← existující validátor (vzor)
        email.test.ts
        phone.ts                              ← existující validátor (vzor)
        phone.test.ts
        index.ts                              ← barrel export (bez ico)
        ico.ts                                ← prázdný soubor pro model
```

---

## Task 1: Adresářová struktura a npm config

**Files:**
- Create: `tasks/02_implement_ico/initial_repo/package.json`
- Create: `tasks/02_implement_ico/initial_repo/tsconfig.json`
- Create: `tasks/02_implement_ico/initial_repo/jest.config.js`

- [ ] **Krok 1: Vytvořit adresáře**

```bash
mkdir -p tasks/02_implement_ico/initial_repo/src/validators
mkdir -p tasks/02_implement_ico/hidden_tests
mkdir -p tasks/02_implement_ico/expected_solution/src/validators
```

- [ ] **Krok 2: Vytvořit `package.json`**

```json
{
  "name": "validators",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "test": "jest",
    "build": "tsc --noEmit"
  },
  "devDependencies": {
    "@types/jest": "^29.5.0",
    "jest": "^29.7.0",
    "ts-jest": "^29.2.0",
    "typescript": "^5.4.0"
  }
}
```

Uložit do `tasks/02_implement_ico/initial_repo/package.json`.

- [ ] **Krok 3: Vytvořit `tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "strict": true,
    "esModuleInterop": true,
    "outDir": "dist",
    "rootDir": "src"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

Uložit do `tasks/02_implement_ico/initial_repo/tsconfig.json`.

- [ ] **Krok 4: Vytvořit `jest.config.js`**

```js
/** @type {import('jest').Config} */
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  testMatch: ['**/*.test.ts'],
};
```

Uložit do `tasks/02_implement_ico/initial_repo/jest.config.js`.

- [ ] **Krok 5: Commit**

```bash
git add tasks/02_implement_ico/initial_repo/package.json \
        tasks/02_implement_ico/initial_repo/tsconfig.json \
        tasks/02_implement_ico/initial_repo/jest.config.js
git commit -m "feat(02_ico): add npm project config"
```

---

## Task 2: Sdílené typy a existující validátory

**Files:**
- Create: `tasks/02_implement_ico/initial_repo/src/types.ts`
- Create: `tasks/02_implement_ico/initial_repo/src/validators/email.ts`
- Create: `tasks/02_implement_ico/initial_repo/src/validators/email.test.ts`
- Create: `tasks/02_implement_ico/initial_repo/src/validators/phone.ts`
- Create: `tasks/02_implement_ico/initial_repo/src/validators/phone.test.ts`
- Create: `tasks/02_implement_ico/initial_repo/src/validators/index.ts`

- [ ] **Krok 1: Vytvořit `src/types.ts`**

```typescript
export type ValidationResult =
  | { valid: true }
  | { valid: false; reason: string };
```

Uložit do `tasks/02_implement_ico/initial_repo/src/types.ts`.

- [ ] **Krok 2: Vytvořit `src/validators/email.ts`**

```typescript
import { ValidationResult } from '../types';

export function validateEmail(input: string): ValidationResult {
  if (!input) {
    return { valid: false, reason: 'Email must not be empty' };
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input)) {
    return { valid: false, reason: 'Email format is invalid' };
  }
  return { valid: true };
}
```

Uložit do `tasks/02_implement_ico/initial_repo/src/validators/email.ts`.

- [ ] **Krok 3: Vytvořit `src/validators/email.test.ts`**

```typescript
import { validateEmail } from './email';

describe('validateEmail', () => {
  test('valid email passes', () => {
    expect(validateEmail('user@example.com')).toEqual({ valid: true });
  });
  test('empty string fails', () => {
    expect(validateEmail('')).toMatchObject({ valid: false });
  });
  test('missing @ fails', () => {
    expect(validateEmail('userexample.com')).toMatchObject({ valid: false });
  });
  test('missing domain fails', () => {
    expect(validateEmail('user@')).toMatchObject({ valid: false });
  });
});
```

Uložit do `tasks/02_implement_ico/initial_repo/src/validators/email.test.ts`.

- [ ] **Krok 4: Vytvořit `src/validators/phone.ts`**

```typescript
import { ValidationResult } from '../types';

export function validatePhone(input: string): ValidationResult {
  if (!input) {
    return { valid: false, reason: 'Phone number must not be empty' };
  }
  if (!/^\+?[0-9]{9,15}$/.test(input)) {
    return { valid: false, reason: 'Phone must contain 9–15 digits, optionally prefixed with +' };
  }
  return { valid: true };
}
```

Uložit do `tasks/02_implement_ico/initial_repo/src/validators/phone.ts`.

- [ ] **Krok 5: Vytvořit `src/validators/phone.test.ts`**

```typescript
import { validatePhone } from './phone';

describe('validatePhone', () => {
  test('valid 9-digit number passes', () => {
    expect(validatePhone('123456789')).toEqual({ valid: true });
  });
  test('valid number with + prefix passes', () => {
    expect(validatePhone('+420123456789')).toEqual({ valid: true });
  });
  test('empty string fails', () => {
    expect(validatePhone('')).toMatchObject({ valid: false });
  });
  test('too short fails', () => {
    expect(validatePhone('12345')).toMatchObject({ valid: false });
  });
  test('letters in number fail', () => {
    expect(validatePhone('12345678a')).toMatchObject({ valid: false });
  });
});
```

Uložit do `tasks/02_implement_ico/initial_repo/src/validators/phone.test.ts`.

- [ ] **Krok 6: Vytvořit `src/validators/index.ts`** (barrel bez ico — model ho případně rozšíří)

```typescript
export { validateEmail } from './email';
export { validatePhone } from './phone';
```

Uložit do `tasks/02_implement_ico/initial_repo/src/validators/index.ts`.

- [ ] **Krok 7: Vytvořit prázdný `src/validators/ico.ts`**

Soubor je záměrně prázdný — model ho celý naplní.

```typescript
```

Uložit do `tasks/02_implement_ico/initial_repo/src/validators/ico.ts` jako prázdný soubor.

- [ ] **Krok 8: Commit**

```bash
git add tasks/02_implement_ico/initial_repo/src/
git commit -m "feat(02_ico): add initial_repo with email/phone validators"
```

---

## Task 3: Ověřit initial_repo

**Files:** žádné nové — jen validace

- [ ] **Krok 1: Nainstalovat závislosti v initial_repo**

```bash
cd tasks/02_implement_ico/initial_repo && npm install
```

Očekávaný výstup: instalace bez chyb.

- [ ] **Krok 2: Ověřit TypeScript kompilaci**

```bash
cd tasks/02_implement_ico/initial_repo && npx tsc --noEmit
```

Očekávaný výstup: žádné chyby, exit 0.

- [ ] **Krok 3: Ověřit že testy pro email a phone prochází**

```bash
cd tasks/02_implement_ico/initial_repo && npx jest --silent
```

Očekávaný výstup: `Tests: 9 passed`, exit 0.

- [ ] **Krok 4: Vrátit se do kořene repozitáře**

```bash
cd ../../..
```

---

## Task 4: Skrytá testovací sada

**Files:**
- Create: `tasks/02_implement_ico/hidden_tests/ico.hidden.test.ts`

Soubor se při verifikaci dočasně zkopíruje do `src/validators/ico.hidden.test.ts` uvnitř workdir, spustí se Jest a soubor se smaže. Import proto ukazuje na `./ico`.

- [ ] **Krok 1: Ověřit IČO algoritmus**

Algoritmus pro kontrolní součet dle specifikace:
- Váhy pro číslic 1–7: `[8, 7, 6, 5, 4, 3, 2]`
- `sum = d1*8 + d2*7 + ... + d7*2`
- `remainder = sum % 11`
- Pokud `remainder == 0` → checksum = 1
- Pokud `remainder == 1` → checksum = 0
- Jinak → checksum = 11 − remainder

Ověření testovacích IČO:
- `25596641`: sum=176, 176%11=0 → checksum=1 ✓
- `27074358`: sum=135, 135%11=3 → checksum=8 ✓
- `45274649`: sum=156, 156%11=2 → checksum=9 ✓
- `25596642`: checksum by měl být 1, ale je 2 → neplatné ✓

- [ ] **Krok 2: Vytvořit `hidden_tests/ico.hidden.test.ts`**

```typescript
import { validateICO } from './ico';

describe('validateICO — hidden test suite', () => {
  describe('valid IČOs', () => {
    test('25596641 is valid', () => {
      expect(validateICO('25596641')).toEqual({ valid: true });
    });
    test('27074358 is valid', () => {
      expect(validateICO('27074358')).toEqual({ valid: true });
    });
    test('45274649 is valid', () => {
      expect(validateICO('45274649')).toEqual({ valid: true });
    });
  });

  describe('invalid checksum', () => {
    test('25596642 has wrong checksum', () => {
      expect(validateICO('25596642')).toMatchObject({ valid: false });
    });
  });

  describe('wrong length', () => {
    test('123 is too short', () => {
      expect(validateICO('123')).toMatchObject({ valid: false });
    });
    test('123456789 is too long', () => {
      expect(validateICO('123456789')).toMatchObject({ valid: false });
    });
  });

  describe('non-digit characters', () => {
    test('abc12345 contains letters', () => {
      expect(validateICO('abc12345')).toMatchObject({ valid: false });
    });
    test('1234567a ends with letter', () => {
      expect(validateICO('1234567a')).toMatchObject({ valid: false });
    });
  });

  describe('empty string', () => {
    test('empty string is invalid', () => {
      expect(validateICO('')).toMatchObject({ valid: false });
    });
  });
});
```

Uložit do `tasks/02_implement_ico/hidden_tests/ico.hidden.test.ts`.

- [ ] **Krok 3: Commit**

```bash
git add tasks/02_implement_ico/hidden_tests/
git commit -m "feat(02_ico): add hidden test suite (9 cases)"
```

---

## Task 5: Referenční řešení (expected_solution)

**Files:**
- Create: `tasks/02_implement_ico/expected_solution/src/validators/ico.ts`
- Create: `tasks/02_implement_ico/expected_solution/src/validators/ico.test.ts`

Referenční řešení slouží pro validaci `verify.sh` — ověřuje, že verify.sh správně rozpozná korektní implementaci. **Neporovnává se s outputem modelu.**

- [ ] **Krok 1: Vytvořit `expected_solution/src/validators/ico.ts`**

```typescript
import { ValidationResult } from '../types';

export function validateICO(input: string): ValidationResult {
  if (!input) {
    return { valid: false, reason: 'IČO must not be empty' };
  }
  if (!/^\d+$/.test(input)) {
    return { valid: false, reason: 'IČO must contain digits only' };
  }
  if (input.length !== 8) {
    return { valid: false, reason: 'IČO must be exactly 8 digits' };
  }

  const digits = input.split('').map(Number);
  const weights = [8, 7, 6, 5, 4, 3, 2];
  const sum = digits
    .slice(0, 7)
    .reduce((acc, d, i) => acc + d * weights[i], 0);
  const remainder = sum % 11;

  let checksum: number;
  if (remainder === 0) {
    checksum = 1;
  } else if (remainder === 1) {
    checksum = 0;
  } else {
    checksum = 11 - remainder;
  }

  if (digits[7] !== checksum) {
    return { valid: false, reason: 'IČO checksum is invalid' };
  }

  return { valid: true };
}
```

Uložit do `tasks/02_implement_ico/expected_solution/src/validators/ico.ts`.

- [ ] **Krok 2: Vytvořit `expected_solution/src/validators/ico.test.ts`**

```typescript
import { validateICO } from './ico';

describe('validateICO', () => {
  test('25596641 is valid', () => {
    expect(validateICO('25596641')).toEqual({ valid: true });
  });
  test('27074358 is valid', () => {
    expect(validateICO('27074358')).toEqual({ valid: true });
  });
  test('invalid checksum fails', () => {
    expect(validateICO('25596642')).toMatchObject({ valid: false });
  });
  test('too short fails', () => {
    expect(validateICO('123')).toMatchObject({ valid: false });
  });
  test('too long fails', () => {
    expect(validateICO('123456789')).toMatchObject({ valid: false });
  });
  test('non-digits fail', () => {
    expect(validateICO('abc12345')).toMatchObject({ valid: false });
  });
  test('empty string fails', () => {
    expect(validateICO('')).toMatchObject({ valid: false });
  });
});
```

Uložit do `tasks/02_implement_ico/expected_solution/src/validators/ico.test.ts`.

- [ ] **Krok 3: Commit**

```bash
git add tasks/02_implement_ico/expected_solution/
git commit -m "feat(02_ico): add expected_solution reference implementation"
```

---

## Task 6: verify.sh

**Files:**
- Create: `tasks/02_implement_ico/verify.sh`

Skript se spouští z uvnitř workdir (runner provede `cd "$WORKDIR"` před invokem). Cesta k `hidden_tests/` se odvozuje z `BASH_SOURCE[0]`.

Pět checků (každý váha 1/5):
1. `src/validators/ico.ts` existuje
2. `src/validators/ico.test.ts` existuje
3. `tsc --noEmit` prochází
4. Model's own tests prochází
5. Skrytá testovací sada prochází

- [ ] **Krok 1: Vytvořit `verify.sh`**

```bash
#!/usr/bin/env bash
#
# Verify Task 02 (implement IČO validation).
#
# Run from inside the working copy of the task (runner cd's into the
# tempdir before invoking us). Emits a JSON document on stdout.
#
# Exit code: 0 if all checks pass, 1 otherwise.
#
set -uo pipefail

TASK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HIDDEN_TEST_SRC="$TASK_DIR/hidden_tests/ico.hidden.test.ts"
HIDDEN_TEST_DEST="src/validators/ico.hidden.test.ts"

# --- Check 1: ico.ts exists ------------------------------------------------
if [[ -f "src/validators/ico.ts" ]]; then
    CHECK_ICO_TS='{"passed": true, "details": "src/validators/ico.ts exists"}'
else
    CHECK_ICO_TS='{"passed": false, "details": "src/validators/ico.ts not found"}'
fi

# --- Check 2: ico.test.ts exists -------------------------------------------
if [[ -f "src/validators/ico.test.ts" ]]; then
    CHECK_ICO_TEST='{"passed": true, "details": "src/validators/ico.test.ts exists"}'
else
    CHECK_ICO_TEST='{"passed": false, "details": "src/validators/ico.test.ts not found"}'
fi

# --- Check 3: TypeScript compiles ------------------------------------------
TSC_OUTPUT="$(npx --no-install tsc --noEmit 2>&1)"
TSC_EXIT=$?
if [[ $TSC_EXIT -eq 0 ]]; then
    CHECK_TSC='{"passed": true, "details": "tsc --noEmit exit 0"}'
else
    TSC_ESC=$(printf '%s' "$TSC_OUTPUT" | head -20 | jq -Rs '.')
    CHECK_TSC=$(printf '{"passed": false, "details": %s}' "$TSC_ESC")
fi

# --- Check 4: Model's own tests pass ---------------------------------------
if [[ -f "src/validators/ico.test.ts" ]]; then
    JEST_OWN_OUTPUT="$(npx --no-install jest src/validators/ico.test.ts --silent 2>&1)"
    JEST_OWN_EXIT=$?
else
    JEST_OWN_OUTPUT="ico.test.ts not found"
    JEST_OWN_EXIT=1
fi
if [[ $JEST_OWN_EXIT -eq 0 ]]; then
    CHECK_OWN='{"passed": true, "details": "model own tests pass"}'
else
    OWN_ESC=$(printf '%s' "$JEST_OWN_OUTPUT" | tail -20 | jq -Rs '.')
    CHECK_OWN=$(printf '{"passed": false, "details": %s}' "$OWN_ESC")
fi

# --- Check 5: Hidden test suite passes -------------------------------------
cp "$HIDDEN_TEST_SRC" "$HIDDEN_TEST_DEST"
JEST_HIDDEN_OUTPUT="$(npx --no-install jest "$HIDDEN_TEST_DEST" --silent 2>&1)"
JEST_HIDDEN_EXIT=$?
rm -f "$HIDDEN_TEST_DEST"
if [[ $JEST_HIDDEN_EXIT -eq 0 ]]; then
    CHECK_HIDDEN='{"passed": true, "details": "all 9 hidden test cases pass"}'
else
    HIDDEN_ESC=$(printf '%s' "$JEST_HIDDEN_OUTPUT" | tail -30 | jq -Rs '.')
    CHECK_HIDDEN=$(printf '{"passed": false, "details": %s}' "$HIDDEN_ESC")
fi

# --- Score -----------------------------------------------------------------
PASSED=0
TOTAL=5
for c in "$CHECK_ICO_TS" "$CHECK_ICO_TEST" "$CHECK_TSC" "$CHECK_OWN" "$CHECK_HIDDEN"; do
    if echo "$c" | jq -e '.passed == true' >/dev/null 2>&1; then
        PASSED=$((PASSED + 1))
    fi
done

SCORE=$(awk -v p="$PASSED" -v t="$TOTAL" 'BEGIN { printf "%.4f", p / t }')
if [[ "$PASSED" -eq "$TOTAL" ]]; then
    SUCCESS="true"
else
    SUCCESS="false"
fi

cat <<EOF
{
  "success": $SUCCESS,
  "score": $SCORE,
  "checks": {
    "ico_ts_exists":      $CHECK_ICO_TS,
    "ico_test_ts_exists": $CHECK_ICO_TEST,
    "tsc_compiles":       $CHECK_TSC,
    "own_tests_pass":     $CHECK_OWN,
    "hidden_tests_pass":  $CHECK_HIDDEN
  }
}
EOF

if [[ "$SUCCESS" == "true" ]]; then exit 0; else exit 1; fi
```

Uložit do `tasks/02_implement_ico/verify.sh` a nastavit executable:

```bash
chmod +x tasks/02_implement_ico/verify.sh
```

- [ ] **Krok 2: Commit**

```bash
git add tasks/02_implement_ico/verify.sh
git commit -m "feat(02_ico): add verify.sh with 5 checks + hidden test suite"
```

---

## Task 7: Metadata a prompt

**Files:**
- Create: `tasks/02_implement_ico/prompt.txt`
- Create: `tasks/02_implement_ico/meta.yaml`
- Create: `tasks/02_implement_ico/README.md`

- [ ] **Krok 1: Vytvořit `prompt.txt`**

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

The `ValidationResult` type is already defined in `src/types.ts`:
  type ValidationResult =
    | { valid: true }
    | { valid: false; reason: string };

Handle edge cases: empty string, non-digit characters, wrong length.

Write comprehensive unit tests in `src/validators/ico.test.ts` using the existing
test framework (Jest is already configured).
```

Uložit do `tasks/02_implement_ico/prompt.txt`.

- [ ] **Krok 2: Vytvořit `meta.yaml`**

```yaml
id: 02_implement_ico
type: specified_implementation
description: Implementovat TypeScript funkci validateICO dle přesné specifikace algoritmu.

allowed_tools:
  - Read
  - Edit
  - Write
  - Glob
  - Grep
  - Bash

expected_duration_seconds: 240
diff_size_max_lines: 150
success_criteria:
  - src/validators/ico.ts existuje a exportuje validateICO
  - src/validators/ico.test.ts existuje
  - TypeScript kompiluje bez chyb
  - Model's own tests prochází
  - Skrytá testovací sada (9 cases) prochází

hypothesis: |
  Medium produkuje srovnatelný výsledek s high na této úloze.
  Low může selhat na edge cases (checksum remainder=0 nebo remainder=1).
  Max over-engineeruje: přidává Czech-specific logic, lokalizaci error
  messages, helper funkce, nebo mění nesouvisející soubory.
```

Uložit do `tasks/02_implement_ico/meta.yaml`.

- [ ] **Krok 3: Vytvořit `README.md`**

```markdown
# Task 02 — Implement `validateICO`

## Cíl

Úloha specifikované implementace. Model dostane TypeScript projekt
s existujícími validátory (email, phone) jako vzorem pro konvence
a prázdný `src/validators/ico.ts`. Musí implementovat funkci dle
přesného algoritmu ze zadání a napsat vlastní testy.

## Typ úlohy

`specified_implementation` — přesná specifikace algoritmu, žádná
architektonická volnost.

## Prompt

Viz `prompt.txt`. Klíčové body:
- Implementovat `validateICO(input: string): ValidationResult`
- Soubor: `src/validators/ico.ts`
- `ValidationResult` typ je již definován v `src/types.ts`
- Napsat unit testy v `src/validators/ico.test.ts`

## Initial state

`initial_repo/` obsahuje:

| Soubor | Obsah |
|--------|-------|
| `src/types.ts` | `ValidationResult` typ |
| `src/validators/email.ts` | hotový validátor (vzor) |
| `src/validators/email.test.ts` | testy emailu |
| `src/validators/phone.ts` | hotový validátor (vzor) |
| `src/validators/phone.test.ts` | testy telefonu |
| `src/validators/index.ts` | barrel export (bez ico) |
| `src/validators/ico.ts` | **prázdný soubor** |

Initial repo kompiluje a má 9 passing testů pro email + phone.

## Verify checks

1. `src/validators/ico.ts` existuje
2. `src/validators/ico.test.ts` existuje
3. `tsc --noEmit` → exit 0
4. Model's own tests → exit 0
5. Skrytá testovací sada (9 cases) → exit 0

`success: true` jen pokud všech 5 checks passes.

## Skrytá testovací sada

Model nevidí `hidden_tests/ico.hidden.test.ts`. Verify.sh ho dočasně
zkopíruje do workdir, spustí Jest a smaže. Testuje:
- 3 platná IČO: 25596641, 27074358, 45274649
- 1 neplatný checksum: 25596642
- 2 špatné délky: 123, 123456789
- 2 non-digit vstupy: abc12345, 1234567a
- prázdný string

## Efforts testované

`low, medium, high, max` × 3 repetice = 12 běhů.
```

Uložit do `tasks/02_implement_ico/README.md`.

- [ ] **Krok 4: Commit**

```bash
git add tasks/02_implement_ico/prompt.txt \
        tasks/02_implement_ico/meta.yaml \
        tasks/02_implement_ico/README.md
git commit -m "feat(02_ico): add prompt, meta, README"
```

---

## Task 8: End-to-end validace

- [ ] **Krok 1: Ověřit strukturu úlohy**

```bash
find tasks/02_implement_ico -type f | sort
```

Očekávaný výstup (minimálně):
```
tasks/02_implement_ico/README.md
tasks/02_implement_ico/expected_solution/src/validators/ico.test.ts
tasks/02_implement_ico/expected_solution/src/validators/ico.ts
tasks/02_implement_ico/hidden_tests/ico.hidden.test.ts
tasks/02_implement_ico/initial_repo/jest.config.js
tasks/02_implement_ico/initial_repo/package.json
tasks/02_implement_ico/initial_repo/src/types.ts
tasks/02_implement_ico/initial_repo/src/validators/email.test.ts
tasks/02_implement_ico/initial_repo/src/validators/email.ts
tasks/02_implement_ico/initial_repo/src/validators/ico.ts
tasks/02_implement_ico/initial_repo/src/validators/index.ts
tasks/02_implement_ico/initial_repo/src/validators/phone.test.ts
tasks/02_implement_ico/initial_repo/src/validators/phone.ts
tasks/02_implement_ico/meta.yaml
tasks/02_implement_ico/prompt.txt
tasks/02_implement_ico/verify.sh
```

- [ ] **Krok 2: Ověřit verify.sh proti expected_solution**

Simulace verify.sh s referenčním řešením — ověří, že verify.sh vrátí `success: true` pro korektní implementaci:

```bash
# Setup dočasného workdir
TMPDIR=$(mktemp -d)
cp -a tasks/02_implement_ico/initial_repo/. "$TMPDIR/"
cd "$TMPDIR"
npm install --silent --no-audit --no-fund --prefer-offline

# Aplikovat expected_solution
cp tasks/02_implement_ico/expected_solution/src/validators/ico.ts src/validators/ico.ts
cp tasks/02_implement_ico/expected_solution/src/validators/ico.test.ts src/validators/ico.test.ts

# Spustit verify.sh
bash tasks/02_implement_ico/verify.sh
```

Očekávaný výstup: `"success": true`, `"score": 1.0000`, všech 5 checks `"passed": true`.

```bash
# Úklid
cd -
rm -rf "$TMPDIR"
```

- [ ] **Krok 3: Ověřit verify.sh s prázdným ico.ts (baseline)**

```bash
TMPDIR=$(mktemp -d)
cp -a tasks/02_implement_ico/initial_repo/. "$TMPDIR/"
cd "$TMPDIR"
npm install --silent --no-audit --no-fund --prefer-offline
bash tasks/02_implement_ico/verify.sh
```

Očekávaný výstup: `"success": false` — checks 3, 4, 5 selžou (prázdný soubor nekompiluje, testy neexistují).

```bash
cd -
rm -rf "$TMPDIR"
```

- [ ] **Krok 4: Smoke test přes runner**

```bash
bash runner/run_single.sh tasks/02_implement_ico low 1
```

Zkontrolovat výsledky:
```bash
cat results/runs/02_implement_ico_*/verify_result.json
```

Očekávaný výstup: `"success": true`, `"score": 1.0000`.

- [ ] **Krok 5: Závěrečný commit**

```bash
git add tasks/02_implement_ico/
git commit -m "feat(02_ico): complete task 02 — IČO validator benchmark task"
```
