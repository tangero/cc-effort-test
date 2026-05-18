# Task 03 — Debug Order — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vytvořit benchmarkovací úlohu `03_debug_order` — TypeScript e-commerce projekt se dvěma záměrnými bugy, kde model musí najít a opravit oba, aby prošel skrytou testovací sadou.

**Architecture:** `initial_repo/` obsahuje funkční TypeScript projekt s jedním padajícím testem (viditelný) a jednou skrytou business logic chybou. Bug A (červený sleď) způsobuje padající test — je snadno viditelný. Bug B (skutečná příčina) způsobuje chybný výpočet při objednávce se shipping — odhalí ho pouze skrytá testovací sada. Verify.sh kontroluje, zda model změnil OBA soubory a projde skrytou sadou.

**Tech Stack:** TypeScript 5.4, Jest 29, ts-jest

---

## Struktura souborů

```
tasks/03_debug_order/
  prompt.txt
  meta.yaml
  README.md
  verify.sh
  hidden_tests/
    order.hidden.test.ts          ← 3 hidden tests odhalující Bug B
  expected_solution/
    src/pricing/PriceCalculator.ts  ← Bug A opravený
    src/orders/OrderService.ts      ← Bug B opravený
  initial_repo/
    package.json
    tsconfig.json
    jest.config.js
    src/
      types.ts                      ← CartItem, Order typy
      pricing/
        PriceCalculator.ts          ← BUG A: + místo - v applyDiscount
      orders/
        OrderService.ts             ← BUG B: shipping zahrnut v discount base
      __tests__/
        order.test.ts               ← 1 padající test, 2 procházející
```

---

## Task 1: Adresářová struktura a npm config

**Files:**
- Create: `tasks/03_debug_order/initial_repo/package.json`
- Create: `tasks/03_debug_order/initial_repo/tsconfig.json`
- Create: `tasks/03_debug_order/initial_repo/jest.config.js`

- [ ] **Krok 1: Vytvořit adresáře**

```bash
mkdir -p tasks/03_debug_order/initial_repo/src/pricing
mkdir -p tasks/03_debug_order/initial_repo/src/orders
mkdir -p tasks/03_debug_order/initial_repo/src/__tests__
mkdir -p tasks/03_debug_order/hidden_tests
mkdir -p tasks/03_debug_order/expected_solution/src/pricing
mkdir -p tasks/03_debug_order/expected_solution/src/orders
```

- [ ] **Krok 2: Vytvořit `tasks/03_debug_order/initial_repo/package.json`**

```json
{
  "name": "order-service",
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

- [ ] **Krok 3: Vytvořit `tasks/03_debug_order/initial_repo/tsconfig.json`**

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

- [ ] **Krok 4: Vytvořit `tasks/03_debug_order/initial_repo/jest.config.js`**

```js
/** @type {import('jest').Config} */
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  testMatch: ['**/*.test.ts'],
};
```

- [ ] **Krok 5: Commit**

```bash
git add tasks/03_debug_order/initial_repo/package.json \
        tasks/03_debug_order/initial_repo/tsconfig.json \
        tasks/03_debug_order/initial_repo/jest.config.js
git commit -m "feat(03_order): add npm project config"
```

---

## Task 2: TypeScript zdrojové soubory s bugy

**Files:**
- Create: `tasks/03_debug_order/initial_repo/src/types.ts`
- Create: `tasks/03_debug_order/initial_repo/src/pricing/PriceCalculator.ts` ← Bug A
- Create: `tasks/03_debug_order/initial_repo/src/orders/OrderService.ts` ← Bug B

- [ ] **Krok 1: Vytvořit `src/types.ts`**

```typescript
export interface CartItem {
  name: string;
  quantity: number;
  unitPrice: number;
}

export interface Order {
  items: CartItem[];
  subtotal: number;
  shipping: number;
  discountPercent: number;
  total: number;
}
```

Uložit do `tasks/03_debug_order/initial_repo/src/types.ts`.

- [ ] **Krok 2: Vytvořit `src/pricing/PriceCalculator.ts` — BUG A**

```typescript
import type { CartItem } from '../types';

export class PriceCalculator {
  computeSubtotal(items: CartItem[]): number {
    return items.reduce((sum, item) => sum + item.quantity * item.unitPrice, 0);
  }

  applyDiscount(subtotal: number, discountPercent: number): number {
    return subtotal + (subtotal * discountPercent / 100);
  }
}
```

**POZOR:** Řádek `return subtotal + (...)` je záměrný Bug A — `+` má být `-`.

Uložit do `tasks/03_debug_order/initial_repo/src/pricing/PriceCalculator.ts`.

- [ ] **Krok 3: Vytvořit `src/orders/OrderService.ts` — BUG B**

```typescript
import type { CartItem, Order } from '../types';
import { PriceCalculator } from '../pricing/PriceCalculator';

export class OrderService {
  private calculator: PriceCalculator;

  constructor(calculator: PriceCalculator = new PriceCalculator()) {
    this.calculator = calculator;
  }

  createOrder(items: CartItem[], discountPercent: number, shippingCost: number): Order {
    const subtotal = this.calculator.computeSubtotal(items);
    const subtotalWithShipping = subtotal + shippingCost;
    const total = this.calculator.applyDiscount(subtotalWithShipping, discountPercent);
    return { items, subtotal, shipping: shippingCost, discountPercent, total };
  }
}
```

**POZOR:** `applyDiscount(subtotalWithShipping, ...)` je záměrný Bug B — shipping se do slevy zahrnovát nemá. Správně: `applyDiscount(subtotal, ...) + shippingCost`.

Uložit do `tasks/03_debug_order/initial_repo/src/orders/OrderService.ts`.

- [ ] **Krok 4: Commit**

```bash
git add tasks/03_debug_order/initial_repo/src/
git commit -m "feat(03_order): add source files with intentional bugs A and B"
```

---

## Task 3: Viditelné testy (1 padající)

**Files:**
- Create: `tasks/03_debug_order/initial_repo/src/__tests__/order.test.ts`

Testy jsou navrženy tak, aby Bug A způsoboval JEDEN padající test. Bug B nijak neovlivňuje viditelné testy (žádný z nich nepoužívá shipping > 0 s discount > 0 najednou).

- [ ] **Krok 1: Ověřit chování bugů ručně**

S Bug A: `applyDiscount(100, 10) = 100 + 10 = 110` (místo 90)
S Bug B při nulovém shipping: `applyDiscount(100 + 0, 10) = 90` — Bug B se neprojeví
S Bug B při shipping > 0: `applyDiscount(100 + 15, 10) = 103.5` (místo správných 105)

- [ ] **Krok 2: Vytvořit `src/__tests__/order.test.ts`**

```typescript
import { OrderService } from '../orders/OrderService';
import { PriceCalculator } from '../pricing/PriceCalculator';

describe('OrderService', () => {
  let orderService: OrderService;

  beforeEach(() => {
    orderService = new OrderService(new PriceCalculator());
  });

  test('order with no discount and no shipping', () => {
    const order = orderService.createOrder(
      [{ name: 'Widget', quantity: 2, unitPrice: 50 }],
      0,
      0
    );
    expect(order.subtotal).toBe(100);
    expect(order.total).toBe(100);
  });

  test('order with 10% discount and no shipping should cost $90', () => {
    const order = orderService.createOrder(
      [{ name: 'Widget', quantity: 1, unitPrice: 100 }],
      10,
      0
    );
    expect(order.total).toBe(90);
  });

  test('subtotal is computed correctly from multiple items', () => {
    const order = orderService.createOrder(
      [
        { name: 'Widget', quantity: 2, unitPrice: 30 },
        { name: 'Gadget', quantity: 1, unitPrice: 40 },
      ],
      0,
      0
    );
    expect(order.subtotal).toBe(100);
    expect(order.total).toBe(100);
  });
});
```

Uložit do `tasks/03_debug_order/initial_repo/src/__tests__/order.test.ts`.

- [ ] **Krok 3: Commit**

```bash
git add tasks/03_debug_order/initial_repo/src/__tests__/
git commit -m "feat(03_order): add visible tests (1 failing, 2 passing)"
```

---

## Task 4: Ověřit initial_repo

- [ ] **Krok 1: npm install**

```bash
cd tasks/03_debug_order/initial_repo && npm install --silent --no-audit --no-fund
```

Očekávaný výstup: instalace bez chyb.

- [ ] **Krok 2: TypeScript kompilace**

```bash
cd tasks/03_debug_order/initial_repo && npx tsc --noEmit
```

Očekávaný výstup: exit 0, žádné chyby (bugy jsou runtime, ne type errors).

- [ ] **Krok 3: Spustit testy — ověřit přesně 1 padající**

```bash
cd tasks/03_debug_order/initial_repo && npx jest 2>&1
```

Očekávaný výstup:
```
FAIL src/__tests__/order.test.ts
  ✓ order with no discount and no shipping
  ✗ order with 10% discount and no shipping should cost $90
  ✓ subtotal is computed correctly from multiple items

Tests: 1 failed, 2 passed
```

- [ ] **Krok 4: Vrátit se do kořene**

```bash
cd ../../..
```

---

## Task 5: Skrytá testovací sada

**Files:**
- Create: `tasks/03_debug_order/hidden_tests/order.hidden.test.ts`

Tyto testy odhalují Bug B — všechny kombinují discount > 0 s shipping > 0.

- [ ] **Krok 1: Ověřit numericky každý hidden test**

Test 1: items=$100, discount=10%, shipping=$15
- Správně: `(100 * 0.9) + 15 = 90 + 15 = 105`
- Bug B: `(100 + 15) * 0.9 = 115 * 0.9 = 103.5`

Test 2: items=2×$50=$100, discount=20%, shipping=$25
- Správně: `(100 * 0.8) + 25 = 80 + 25 = 105`
- Bug B: `(100 + 25) * 0.8 = 125 * 0.8 = 100`

Test 3: items=$50, discount=0%, shipping=$10
- Správně: `50 + 10 = 60`
- Bug B: `(50 + 10) * 1.0 = 60` (Bug B se neprojeví při 0% slevě)

- [ ] **Krok 2: Vytvořit `hidden_tests/order.hidden.test.ts`**

```typescript
import { OrderService } from '../src/orders/OrderService';
import { PriceCalculator } from '../src/pricing/PriceCalculator';

describe('OrderService — hidden test suite', () => {
  let orderService: OrderService;

  beforeEach(() => {
    orderService = new OrderService(new PriceCalculator());
  });

  test('discount should not apply to shipping costs', () => {
    const order = orderService.createOrder(
      [{ name: 'Widget', quantity: 1, unitPrice: 100 }],
      10,
      15
    );
    expect(order.total).toBe(105);
  });

  test('large shipping should not reduce effective discount', () => {
    const order = orderService.createOrder(
      [{ name: 'Item', quantity: 2, unitPrice: 50 }],
      20,
      25
    );
    expect(order.total).toBe(105);
  });

  test('zero discount with shipping is unaffected by bug B', () => {
    const order = orderService.createOrder(
      [{ name: 'Item', quantity: 1, unitPrice: 50 }],
      0,
      10
    );
    expect(order.total).toBe(60);
  });
});
```

Uložit do `tasks/03_debug_order/hidden_tests/order.hidden.test.ts`.

- [ ] **Krok 3: Commit**

```bash
git add tasks/03_debug_order/hidden_tests/
git commit -m "feat(03_order): add hidden test suite (3 cases exposing Bug B)"
```

---

## Task 6: Expected solution

**Files:**
- Create: `tasks/03_debug_order/expected_solution/src/pricing/PriceCalculator.ts`
- Create: `tasks/03_debug_order/expected_solution/src/orders/OrderService.ts`

- [ ] **Krok 1: Vytvořit `expected_solution/src/pricing/PriceCalculator.ts`** (Bug A opravený)

```typescript
import type { CartItem } from '../types';

export class PriceCalculator {
  computeSubtotal(items: CartItem[]): number {
    return items.reduce((sum, item) => sum + item.quantity * item.unitPrice, 0);
  }

  applyDiscount(subtotal: number, discountPercent: number): number {
    return subtotal - (subtotal * discountPercent / 100);
  }
}
```

Uložit do `tasks/03_debug_order/expected_solution/src/pricing/PriceCalculator.ts`.

- [ ] **Krok 2: Vytvořit `expected_solution/src/orders/OrderService.ts`** (Bug B opravený)

```typescript
import type { CartItem, Order } from '../types';
import { PriceCalculator } from '../pricing/PriceCalculator';

export class OrderService {
  private calculator: PriceCalculator;

  constructor(calculator: PriceCalculator = new PriceCalculator()) {
    this.calculator = calculator;
  }

  createOrder(items: CartItem[], discountPercent: number, shippingCost: number): Order {
    const subtotal = this.calculator.computeSubtotal(items);
    const discountedSubtotal = this.calculator.applyDiscount(subtotal, discountPercent);
    const total = discountedSubtotal + shippingCost;
    return { items, subtotal, shipping: shippingCost, discountPercent, total };
  }
}
```

Uložit do `tasks/03_debug_order/expected_solution/src/orders/OrderService.ts`.

- [ ] **Krok 3: Commit**

```bash
git add tasks/03_debug_order/expected_solution/
git commit -m "feat(03_order): add expected_solution with both bugs fixed"
```

---

## Task 7: verify.sh

**Files:**
- Create: `tasks/03_debug_order/verify.sh`

Pět checků:
1. `tsc --noEmit` prochází
2. Model's own tests prochází (všechny 3 visible)
3. `PriceCalculator.ts` byl změněn (Bug A opraven) — `git diff HEAD`
4. `OrderService.ts` byl změněn (Bug B opraven) — `git diff HEAD`
5. Skrytá testovací sada prochází

- [ ] **Krok 1: Vytvořit `verify.sh`**

```bash
#!/usr/bin/env bash
#
# Verify Task 03 (debug order — two bugs).
#
# Run from inside the working copy of the task (runner cd's into workdir).
# Emits JSON on stdout. Exit 0 if all checks pass, 1 otherwise.
#
set -uo pipefail

TASK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HIDDEN_TEST_SRC="$TASK_DIR/hidden_tests/order.hidden.test.ts"
HIDDEN_TEST_DEST="src/__tests__/order.hidden.test.ts"

# --- Check 1: TypeScript compiles -----------------------------------------
TSC_OUTPUT="$(npx --no-install tsc --noEmit 2>&1)"
TSC_EXIT=$?
if [[ $TSC_EXIT -eq 0 ]]; then
    CHECK_TSC='{"passed": true, "details": "tsc --noEmit exit 0"}'
else
    TSC_ESC=$(printf '%s' "$TSC_OUTPUT" | head -20 | jq -Rs '.')
    CHECK_TSC=$(printf '{"passed": false, "details": %s}' "$TSC_ESC")
fi

# --- Check 2: Model's own tests pass --------------------------------------
JEST_OWN="$(npx --no-install jest src/__tests__/order.test.ts --silent 2>&1)"
JEST_OWN_EXIT=$?
if [[ $JEST_OWN_EXIT -eq 0 ]]; then
    CHECK_OWN='{"passed": true, "details": "all 3 visible tests pass"}'
else
    OWN_ESC=$(printf '%s' "$JEST_OWN" | tail -20 | jq -Rs '.')
    CHECK_OWN=$(printf '{"passed": false, "details": %s}' "$OWN_ESC")
fi

# --- Check 3: PriceCalculator.ts was modified (Bug A fixed) ---------------
CALC_DIFF="$(git diff HEAD -- src/pricing/PriceCalculator.ts 2>/dev/null | wc -l | tr -d ' ')"
if [[ "${CALC_DIFF:-0}" -gt 0 ]]; then
    CHECK_CALC=$(printf '{"passed": true, "details": "%s diff lines in PriceCalculator.ts"}' "$CALC_DIFF")
else
    CHECK_CALC='{"passed": false, "details": "PriceCalculator.ts was not modified — Bug A likely not fixed"}'
fi

# --- Check 4: OrderService.ts was modified (Bug B fixed) ------------------
ORDER_DIFF="$(git diff HEAD -- src/orders/OrderService.ts 2>/dev/null | wc -l | tr -d ' ')"
if [[ "${ORDER_DIFF:-0}" -gt 0 ]]; then
    CHECK_ORDER=$(printf '{"passed": true, "details": "%s diff lines in OrderService.ts"}' "$ORDER_DIFF")
else
    CHECK_ORDER='{"passed": false, "details": "OrderService.ts was not modified — Bug B likely not fixed"}'
fi

# --- Check 5: Hidden tests pass -------------------------------------------
cp "$HIDDEN_TEST_SRC" "$HIDDEN_TEST_DEST"
JEST_HIDDEN="$(npx --no-install jest "$HIDDEN_TEST_DEST" --silent 2>&1)"
JEST_HIDDEN_EXIT=$?
rm -f "$HIDDEN_TEST_DEST"
if [[ $JEST_HIDDEN_EXIT -eq 0 ]]; then
    CHECK_HIDDEN='{"passed": true, "details": "all 3 hidden test cases pass"}'
else
    HIDDEN_ESC=$(printf '%s' "$JEST_HIDDEN" | tail -30 | jq -Rs '.')
    CHECK_HIDDEN=$(printf '{"passed": false, "details": %s}' "$HIDDEN_ESC")
fi

# --- Score ----------------------------------------------------------------
PASSED=0
TOTAL=5
for c in "$CHECK_TSC" "$CHECK_OWN" "$CHECK_CALC" "$CHECK_ORDER" "$CHECK_HIDDEN"; do
    if echo "$c" | jq -e '.passed == true' >/dev/null 2>&1; then
        PASSED=$((PASSED + 1))
    fi
done

SCORE=$(awk -v p="$PASSED" -v t="$TOTAL" 'BEGIN { printf "%.4f", p / t }')
if [[ "$PASSED" -eq "$TOTAL" ]]; then SUCCESS="true"; else SUCCESS="false"; fi

cat <<EOF
{
  "success": $SUCCESS,
  "score": $SCORE,
  "checks": {
    "tsc_compiles":          $CHECK_TSC,
    "own_tests_pass":        $CHECK_OWN,
    "price_calculator_fixed": $CHECK_CALC,
    "order_service_fixed":   $CHECK_ORDER,
    "hidden_tests_pass":     $CHECK_HIDDEN
  }
}
EOF

if [[ "$SUCCESS" == "true" ]]; then exit 0; else exit 1; fi
```

Uložit do `tasks/03_debug_order/verify.sh` a nastavit executable:

```bash
chmod +x tasks/03_debug_order/verify.sh
```

- [ ] **Krok 2: Commit**

```bash
git add tasks/03_debug_order/verify.sh
git commit -m "feat(03_order): add verify.sh with 5 checks"
```

---

## Task 8: Metadata a prompt

**Files:**
- Create: `tasks/03_debug_order/prompt.txt`
- Create: `tasks/03_debug_order/meta.yaml`
- Create: `tasks/03_debug_order/README.md`

- [ ] **Krok 1: Vytvořit `prompt.txt`**

```
The test suite in `src/__tests__/order.test.ts` has a failing test.
Find the root cause and fix it.

Do not modify any test files.

After your fix, ensure that all tests in the test suite still pass.
```

Uložit do `tasks/03_debug_order/prompt.txt`.

- [ ] **Krok 2: Vytvořit `meta.yaml`**

```yaml
id: 03_debug_order
type: bounded_debugging
description: Opravit dva záměrné bugy v TypeScript e-commerce systému. Bug A způsobuje padající test. Bug B je skrytý — odhalí ho pouze hidden test suite.

allowed_tools:
  - Read
  - Edit
  - Write
  - Glob
  - Grep
  - Bash

expected_duration_seconds: 300
diff_size_max_lines: 20
success_criteria:
  - tsc kompiluje bez chyb
  - Všechny visible testy prochází
  - PriceCalculator.ts byl změněn (Bug A opraven)
  - OrderService.ts byl změněn (Bug B opraven)
  - Skrytá testovací sada (3 cases) prochází

hypothesis: |
  Low effort opraví Bug A (padající test), ale přehlédne Bug B (žádný
  failing test ho neindikuje). Score low effortu: ~0.6 (3/5 checks).
  High a max effort přečtou celý kód, pochopí business logiku a opraví
  oba bugy. Tato úloha přímo měří schopnost prohledat systém i bez
  explicitního signálu selhání.
```

Uložit do `tasks/03_debug_order/meta.yaml`.

- [ ] **Krok 3: Vytvořit `README.md`**

```markdown
# Task 03 — Debug Order Service

## Cíl

Úloha ohraničeného debuggingu se dvěma záměrnými bugy. Jeden bug
způsobuje padající test (viditelný signál). Druhý bug je skrytá business
logic chyba, kterou žádný visible test neodhalí — model ji musí najít
vlastním prozkoumáním kódu.

## Typ úlohy

`bounded_debugging` — scoped systém, dva bugy, jeden viditelný a jeden skrytý.

## Prompt

Viz `prompt.txt`:

> The test suite in `src/__tests__/order.test.ts` has a failing test.
> Find the root cause and fix it.
> Do not modify any test files.
> After your fix, ensure that all tests in the test suite still pass.

## Bugy

### Bug A — Červený sleď (viditelný)

**Soubor:** `src/pricing/PriceCalculator.ts`

```typescript
// BUG: + místo -
return subtotal + (subtotal * discountPercent / 100);
```

Přímo způsobuje padající visible test. Model ho snadno najde.

### Bug B — Skutečná příčina (skrytý)

**Soubor:** `src/orders/OrderService.ts`

```typescript
// BUG: shipping je zahrnut v discount base
const subtotalWithShipping = subtotal + shippingCost;
const total = this.calculator.applyDiscount(subtotalWithShipping, discountPercent);
```

Business logic chyba: doprava se nesmí slevovat. Model ji musí najít
čtením kódu, bez failing testu.

**Správná implementace:**
```typescript
const discountedSubtotal = this.calculator.applyDiscount(subtotal, discountPercent);
const total = discountedSubtotal + shippingCost;
```

## Verify checks (5 celkem)

1. `tsc --noEmit` → exit 0
2. Visible tests → exit 0
3. `PriceCalculator.ts` byl změněn
4. `OrderService.ts` byl změněn
5. Skrytá sada (3 testy se shipping) → exit 0

## Hypotéza

Low effort: opraví Bug A, visible testy projdou, hotovo. Score = 3/5 (0.6000).
High/max effort: přečte celý systém, opraví oba bugy. Score = 5/5 (1.0000).

## Efforts testované

`low, medium, high, max` × 3 repetice = 12 běhů.
```

Uložit do `tasks/03_debug_order/README.md`.

- [ ] **Krok 4: Commit**

```bash
git add tasks/03_debug_order/prompt.txt \
        tasks/03_debug_order/meta.yaml \
        tasks/03_debug_order/README.md
git commit -m "feat(03_order): add prompt, meta, README"
```

---

## Task 9: End-to-end validace

- [ ] **Krok 1: Ověřit strukturu**

```bash
find tasks/03_debug_order -type f | sort
```

Očekávaný výstup obsahuje minimálně:
```
tasks/03_debug_order/README.md
tasks/03_debug_order/expected_solution/src/orders/OrderService.ts
tasks/03_debug_order/expected_solution/src/pricing/PriceCalculator.ts
tasks/03_debug_order/hidden_tests/order.hidden.test.ts
tasks/03_debug_order/initial_repo/jest.config.js
tasks/03_debug_order/initial_repo/package.json
tasks/03_debug_order/initial_repo/src/__tests__/order.test.ts
tasks/03_debug_order/initial_repo/src/orders/OrderService.ts
tasks/03_debug_order/initial_repo/src/pricing/PriceCalculator.ts
tasks/03_debug_order/initial_repo/src/types.ts
tasks/03_debug_order/initial_repo/tsconfig.json
tasks/03_debug_order/meta.yaml
tasks/03_debug_order/prompt.txt
tasks/03_debug_order/verify.sh
```

- [ ] **Krok 2: Ověřit verify.sh s expected_solution (success: true)**

```bash
TMPDIR=$(mktemp -d)
cp -a tasks/03_debug_order/initial_repo/. "$TMPDIR/"
cd "$TMPDIR"
npm install --silent --no-audit --no-fund --prefer-offline
cp /Users/patrickzandl/GitHub/cc-effort-test/tasks/03_debug_order/expected_solution/src/pricing/PriceCalculator.ts src/pricing/PriceCalculator.ts
cp /Users/patrickzandl/GitHub/cc-effort-test/tasks/03_debug_order/expected_solution/src/orders/OrderService.ts src/orders/OrderService.ts
git add -A
bash /Users/patrickzandl/GitHub/cc-effort-test/tasks/03_debug_order/verify.sh
cd /Users/patrickzandl/GitHub/cc-effort-test
rm -rf "$TMPDIR"
```

Očekávaný výstup: `"success": true`, `"score": 1.0000`

- [ ] **Krok 3: Ověřit verify.sh s opravou pouze Bug A (success: false, score 0.6)**

```bash
TMPDIR=$(mktemp -d)
cp -a tasks/03_debug_order/initial_repo/. "$TMPDIR/"
cd "$TMPDIR"
npm install --silent --no-audit --no-fund --prefer-offline
# Opravit pouze Bug A (+ na -)
sed -i '' 's/return subtotal + (subtotal \* discountPercent/return subtotal - (subtotal * discountPercent/' src/pricing/PriceCalculator.ts
git add -A
bash /Users/patrickzandl/GitHub/cc-effort-test/tasks/03_debug_order/verify.sh
cd /Users/patrickzandl/GitHub/cc-effort-test
rm -rf "$TMPDIR"
```

Očekávaný výstup: `"success": false`, `"score": 0.6000` — checks 1,2,3 pass, check 4 a 5 fail.

- [ ] **Krok 4: Smoke test přes runner**

```bash
bash runner/run_single.sh tasks/03_debug_order low 1
```

```bash
cat results/runs/03_debug_order_*/verify_result.json
```

Sleduj, zda low effort opraví jen Bug A nebo oba bugy.

- [ ] **Krok 5: Commit**

```bash
git add tasks/03_debug_order/
git commit -m "feat(03_order): complete task 03 — debugging benchmark with two intentional bugs"
```
