# Task 05 — Find Validation Gaps — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement task-by-task.

**Goal:** Vytvořit benchmarkovací úlohu `05_find_validation_gaps` — TypeScript backend s ~20 API endpointy, z nichž 5 nemá vstupní validaci. Model musí identifikovat ty bez validace a vypsat je do `analysis.json`.

**Architecture:** `initial_repo/` obsahuje 20 TypeScript handler funkcí rozdělených do 5 souborů. 15 má validaci, 5 nemá. Ground truth je pevně daná v `verify.sh`. Scoring = precision/recall/F1 z porovnání s ground truth.

**Tech Stack:** TypeScript 5.4 (bez runtime frameworku — čisté handler funkce), Jest 29, ts-jest

---

## Ground Truth — 5 endpointů bez validace

| # | Method | Path | File | Co chybí |
|---|--------|------|------|----------|
| 1 | POST | /api/users | src/api/users.ts | email format, username length |
| 2 | PUT | /api/users/:id | src/api/users.ts | email format, username length |
| 3 | POST | /api/products | src/api/products.ts | name not empty, price > 0 |
| 4 | POST | /api/orders | src/api/orders.ts | items array not empty, quantities > 0 |
| 5 | PUT | /api/orders/:id | src/api/orders.ts | status enum validation |

Zbývajících 15 endpointů má explicitní validaci (if-checks, regex, guard clauses).

---

## Struktura souborů

```
tasks/05_find_validation_gaps/
  prompt.txt / meta.yaml / README.md / verify.sh
  initial_repo/
    package.json / tsconfig.json / jest.config.js
    src/
      types.ts                  ← sdílené typy
      validation.ts             ← helpers (isEmail, isUUID, isPositive...)
      api/
        users.ts                ← 4 endpoints (2 bez validace)
        products.ts             ← 4 endpoints (1 bez validace)
        orders.ts               ← 5 endpoints (2 bez validace)
        auth.ts                 ← 4 endpoints (vše validováno)
        categories.ts           ← 3 endpoints (vše validováno)
```

---

## Task 1: npm config + adresáře

- [ ] **Krok 1: Vytvořit adresáře**

```bash
mkdir -p tasks/05_find_validation_gaps/initial_repo/src/api
```

- [ ] **Krok 2: Konfigurační soubory** — identické s předchozími úlohami

`package.json` (name: "api-service"), `tsconfig.json` (stejný), `jest.config.js` (stejný).

```bash
git add tasks/05_find_validation_gaps/initial_repo/
git commit -m "feat(05_gaps): add npm project config"
```

---

## Task 2: Zdrojové soubory — typy a validační helpers

- [ ] **Krok 1: `src/types.ts`**

```typescript
export interface ApiRequest<T = unknown> {
  body: T;
  params: Record<string, string>;
  query: Record<string, string>;
}

export interface ApiResponse<T = unknown> {
  status: number;
  body: T;
}

export interface User { id: string; email: string; username: string; }
export interface Product { id: string; name: string; price: number; categoryId: string; }
export interface Order { id: string; userId: string; items: OrderItem[]; status: string; }
export interface OrderItem { productId: string; quantity: number; }
export interface Category { id: string; name: string; slug: string; }
```

Uložit do `tasks/05_find_validation_gaps/initial_repo/src/types.ts`.

- [ ] **Krok 2: `src/validation.ts`** — helpers používané v validovaných endpointech

```typescript
export const isEmail = (s: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s);
export const isUUID = (s: string) => /^[0-9a-f-]{36}$/.test(s);
export const isPositive = (n: number) => typeof n === 'number' && n > 0;
export const isNonEmpty = (s: string) => typeof s === 'string' && s.trim().length > 0;
export const ORDER_STATUSES = ['pending', 'processing', 'shipped', 'delivered', 'cancelled'] as const;
export type OrderStatus = typeof ORDER_STATUSES[number];
export const isOrderStatus = (s: string): s is OrderStatus =>
  ORDER_STATUSES.includes(s as OrderStatus);
```

Uložit do `tasks/05_find_validation_gaps/initial_repo/src/validation.ts`.

---

## Task 3: API soubory — auth.ts a categories.ts (vše validováno)

- [ ] **Krok 1: `src/api/auth.ts`** — 4 endpoints, všechny validovány

```typescript
import type { ApiRequest, ApiResponse } from '../types';
import { isEmail } from '../validation';

export function login(req: ApiRequest<{ email: string; password: string }>): ApiResponse {
  if (!isEmail(req.body.email)) return { status: 400, body: { error: 'Invalid email' } };
  if (!req.body.password || req.body.password.length < 8)
    return { status: 400, body: { error: 'Password too short' } };
  return { status: 200, body: { token: 'mock-token' } };
}
// POST /api/auth/login

export function register(req: ApiRequest<{ email: string; password: string; username: string }>): ApiResponse {
  if (!isEmail(req.body.email)) return { status: 400, body: { error: 'Invalid email' } };
  if (!req.body.password || req.body.password.length < 8)
    return { status: 400, body: { error: 'Password must be at least 8 characters' } };
  if (!req.body.username || req.body.username.length < 3)
    return { status: 400, body: { error: 'Username too short' } };
  return { status: 201, body: { message: 'Registered' } };
}
// POST /api/auth/register

export function refreshToken(req: ApiRequest<{ refreshToken: string }>): ApiResponse {
  if (!req.body.refreshToken)
    return { status: 400, body: { error: 'refreshToken required' } };
  return { status: 200, body: { token: 'new-token' } };
}
// POST /api/auth/refresh

export function logout(req: ApiRequest<{ token: string }>): ApiResponse {
  if (!req.body.token) return { status: 400, body: { error: 'token required' } };
  return { status: 200, body: { message: 'Logged out' } };
}
// POST /api/auth/logout
```

Uložit do `tasks/05_find_validation_gaps/initial_repo/src/api/auth.ts`.

- [ ] **Krok 2: `src/api/categories.ts`** — 3 endpoints, validovány

```typescript
import type { ApiRequest, ApiResponse, Category } from '../types';
import { isUUID } from '../validation';

export function listCategories(_req: ApiRequest): ApiResponse<Category[]> {
  return { status: 200, body: [] };
}
// GET /api/categories

export function getCategory(req: ApiRequest): ApiResponse {
  if (!isUUID(req.params.id)) return { status: 400, body: { error: 'Invalid category ID' } };
  return { status: 200, body: { id: req.params.id, name: 'Mock', slug: 'mock' } };
}
// GET /api/categories/:id

export function deleteCategory(req: ApiRequest): ApiResponse {
  if (!isUUID(req.params.id)) return { status: 400, body: { error: 'Invalid ID' } };
  return { status: 204, body: null };
}
// DELETE /api/categories/:id
```

Uložit do `tasks/05_find_validation_gaps/initial_repo/src/api/categories.ts`.

---

## Task 4: API soubory se smíšenou validací (users, products, orders)

- [ ] **Krok 1: `src/api/users.ts`** — 4 endpoints, **2 BEZ validace**

```typescript
import type { ApiRequest, ApiResponse, User } from '../types';
import { isEmail, isUUID } from '../validation';

export function listUsers(req: ApiRequest): ApiResponse<User[]> {
  const page = parseInt(req.query.page ?? '1');
  if (isNaN(page) || page < 1) return { status: 400, body: { error: 'Invalid page' } };
  return { status: 200, body: [] };
}
// GET /api/users

export function getUser(req: ApiRequest): ApiResponse {
  if (!isUUID(req.params.id)) return { status: 400, body: { error: 'Invalid user ID' } };
  return { status: 200, body: { id: req.params.id, email: '', username: '' } };
}
// GET /api/users/:id

export function createUser(req: ApiRequest<{ email: string; username: string }>): ApiResponse {
  const user: User = { id: 'new-id', email: req.body.email, username: req.body.username };
  return { status: 201, body: user };
}
// POST /api/users  ← NO VALIDATION

export function updateUser(req: ApiRequest<{ email?: string; username?: string }>): ApiResponse {
  return { status: 200, body: { id: req.params.id, ...req.body } };
}
// PUT /api/users/:id  ← NO VALIDATION
```

Uložit do `tasks/05_find_validation_gaps/initial_repo/src/api/users.ts`.

- [ ] **Krok 2: `src/api/products.ts`** — 4 endpoints, **1 BEZ validace**

```typescript
import type { ApiRequest, ApiResponse, Product } from '../types';
import { isUUID, isNonEmpty, isPositive } from '../validation';

export function listProducts(req: ApiRequest): ApiResponse<Product[]> {
  const limit = parseInt(req.query.limit ?? '20');
  if (isNaN(limit) || limit < 1 || limit > 100)
    return { status: 400, body: { error: 'limit must be 1–100' } };
  return { status: 200, body: [] };
}
// GET /api/products

export function getProduct(req: ApiRequest): ApiResponse {
  if (!isUUID(req.params.id)) return { status: 400, body: { error: 'Invalid product ID' } };
  return { status: 200, body: null };
}
// GET /api/products/:id

export function createProduct(req: ApiRequest<{ name: string; price: number; categoryId: string }>): ApiResponse {
  const product: Product = { id: 'new-id', name: req.body.name, price: req.body.price, categoryId: req.body.categoryId };
  return { status: 201, body: product };
}
// POST /api/products  ← NO VALIDATION

export function updateProduct(req: ApiRequest<{ name?: string; price?: number }>): ApiResponse {
  if (!isUUID(req.params.id)) return { status: 400, body: { error: 'Invalid ID' } };
  if (req.body.name !== undefined && !isNonEmpty(req.body.name))
    return { status: 400, body: { error: 'name cannot be empty' } };
  if (req.body.price !== undefined && !isPositive(req.body.price))
    return { status: 400, body: { error: 'price must be positive' } };
  return { status: 200, body: null };
}
// PUT /api/products/:id
```

Uložit do `tasks/05_find_validation_gaps/initial_repo/src/api/products.ts`.

- [ ] **Krok 3: `src/api/orders.ts`** — 5 endpoints, **2 BEZ validace**

```typescript
import type { ApiRequest, ApiResponse, Order, OrderItem } from '../types';
import { isUUID, isOrderStatus } from '../validation';

export function listOrders(req: ApiRequest): ApiResponse<Order[]> {
  if (req.query.userId && !isUUID(req.query.userId))
    return { status: 400, body: { error: 'Invalid userId filter' } };
  return { status: 200, body: [] };
}
// GET /api/orders

export function getOrder(req: ApiRequest): ApiResponse {
  if (!isUUID(req.params.id)) return { status: 400, body: { error: 'Invalid order ID' } };
  return { status: 200, body: null };
}
// GET /api/orders/:id

export function createOrder(req: ApiRequest<{ userId: string; items: OrderItem[] }>): ApiResponse {
  const order: Order = { id: 'new-id', userId: req.body.userId, items: req.body.items, status: 'pending' };
  return { status: 201, body: order };
}
// POST /api/orders  ← NO VALIDATION (items could be empty, quantities not checked)

export function updateOrderStatus(req: ApiRequest<{ status: string }>): ApiResponse {
  const order = { id: req.params.id, status: req.body.status };
  return { status: 200, body: order };
}
// PUT /api/orders/:id  ← NO VALIDATION (status not checked against enum)

export function deleteOrder(req: ApiRequest): ApiResponse {
  if (!isUUID(req.params.id)) return { status: 400, body: { error: 'Invalid order ID' } };
  return { status: 204, body: null };
}
// DELETE /api/orders/:id
```

Uložit do `tasks/05_find_validation_gaps/initial_repo/src/api/orders.ts`.

- [ ] **Krok 4: Ověřit initial_repo**

```bash
cd tasks/05_find_validation_gaps/initial_repo
npm install --silent --no-audit --no-fund
npx tsc --noEmit   # must exit 0
cd ../../..
```

- [ ] **Krok 5: Commit**

```bash
git add tasks/05_find_validation_gaps/initial_repo/src/
git commit -m "feat(05_gaps): add initial_repo with 20 API endpoints (5 without validation)"
```

---

## Task 5: verify.sh s precision/recall scoring

Ground truth JSON (5 endpointů):
```
POST /api/users        src/api/users.ts
PUT  /api/users/:id    src/api/users.ts
POST /api/products     src/api/products.ts
POST /api/orders       src/api/orders.ts
PUT  /api/orders/:id   src/api/orders.ts
```

Pět checků:
1. `analysis.json` existuje
2. Validní JSON se správným schématem (pole `endpoints_without_validation`)
3. Recall ≥ 0.6 (nalezeno alespoň 3/5)
4. Precision ≥ 0.5 (ne příliš mnoho false positives)
5. F1 ≥ 0.65

- [ ] **Krok 1: Vytvořit `tasks/05_find_validation_gaps/verify.sh`**

```bash
#!/usr/bin/env bash
#
# Verify Task 05 (find validation gaps).
# Run from workdir. Emits JSON on stdout.
#
set -uo pipefail

# Ground truth: method:path pairs without validation
GROUND_TRUTH='["POST:/api/users","PUT:/api/users/:id","POST:/api/products","POST:/api/orders","PUT:/api/orders/:id"]'

# --- Check 1: analysis.json exists ----------------------------------------
if [[ ! -f "analysis.json" ]]; then
  cat <<'EOF'
{"success": false, "score": 0.0000, "checks": {
  "file_exists":     {"passed": false, "details": "analysis.json not found"},
  "schema_valid":    {"passed": false, "details": "file missing"},
  "recall_pass":     {"passed": false, "details": "file missing"},
  "precision_pass":  {"passed": false, "details": "file missing"},
  "f1_pass":         {"passed": false, "details": "file missing"}
}}
EOF
  exit 1
fi
CHECK_FILE='{"passed": true, "details": "analysis.json exists"}'

# --- Check 2: valid JSON with correct schema --------------------------------
SCHEMA_ERR=$(python3 -c "
import json, sys
try:
    d = json.load(open('analysis.json'))
    eps = d.get('endpoints_without_validation')
    if not isinstance(eps, list):
        print('endpoints_without_validation must be an array')
        sys.exit(1)
    for i, ep in enumerate(eps):
        for key in ['path','method','file','missing_validation']:
            if key not in ep:
                print(f'item {i} missing key: {key}')
                sys.exit(1)
    print('ok')
except json.JSONDecodeError as e:
    print(f'JSON parse error: {e}')
    sys.exit(1)
except Exception as e:
    print(str(e))
    sys.exit(1)
" 2>&1)

if [[ "$SCHEMA_ERR" == "ok" ]]; then
  CHECK_SCHEMA='{"passed": true, "details": "schema valid"}'
else
  ESC=$(printf '%s' "$SCHEMA_ERR" | jq -Rs '.')
  CHECK_SCHEMA=$(printf '{"passed": false, "details": %s}' "$ESC")
fi

# --- Compute precision/recall/F1 ------------------------------------------
METRICS=$(python3 -c "
import json, sys

ground_truth = set([
    'POST:/api/users',
    'PUT:/api/users/:id',
    'POST:/api/products',
    'POST:/api/orders',
    'PUT:/api/orders/:id',
])

try:
    d = json.load(open('analysis.json'))
    reported = set()
    for ep in d.get('endpoints_without_validation', []):
        key = f\"{ep.get('method','').upper()}:{ep.get('path','')}\"
        reported.add(key)

    tp = len(ground_truth & reported)
    fp = len(reported - ground_truth)
    fn = len(ground_truth - reported)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    print(f'{precision:.4f} {recall:.4f} {f1:.4f} {tp} {fp} {fn}')
except Exception as e:
    print(f'0.0000 0.0000 0.0000 0 0 5')
" 2>/dev/null)

read -r PRECISION RECALL F1 TP FP FN <<< "$METRICS"

# --- Check 3: Recall >= 0.6 -----------------------------------------------
if python3 -c "import sys; sys.exit(0 if float('$RECALL') >= 0.6 else 1)" 2>/dev/null; then
  CHECK_RECALL=$(printf '{"passed": true, "details": "recall=%.4f (TP=%s FN=%s)"}' "$RECALL" "$TP" "$FN")
else
  CHECK_RECALL=$(printf '{"passed": false, "details": "recall=%.4f < 0.6 (TP=%s FN=%s)"}' "$RECALL" "$TP" "$FN")
fi

# --- Check 4: Precision >= 0.5 --------------------------------------------
if python3 -c "import sys; sys.exit(0 if float('$PRECISION') >= 0.5 else 1)" 2>/dev/null; then
  CHECK_PREC=$(printf '{"passed": true, "details": "precision=%.4f (TP=%s FP=%s)"}' "$PRECISION" "$TP" "$FP")
else
  CHECK_PREC=$(printf '{"passed": false, "details": "precision=%.4f < 0.5 (TP=%s FP=%s)"}' "$PRECISION" "$TP" "$FP")
fi

# --- Check 5: F1 >= 0.65 --------------------------------------------------
if python3 -c "import sys; sys.exit(0 if float('$F1') >= 0.65 else 1)" 2>/dev/null; then
  CHECK_F1=$(printf '{"passed": true, "details": "F1=%.4f"}' "$F1")
else
  CHECK_F1=$(printf '{"passed": false, "details": "F1=%.4f < 0.65"}' "$F1")
fi

# --- Score ----------------------------------------------------------------
PASSED=0; TOTAL=5
for c in "$CHECK_FILE" "$CHECK_SCHEMA" "$CHECK_RECALL" "$CHECK_PREC" "$CHECK_F1"; do
  echo "$c" | jq -e '.passed == true' >/dev/null 2>&1 && PASSED=$((PASSED+1))
done

SCORE=$(awk -v p="$PASSED" -v t="$TOTAL" 'BEGIN{printf "%.4f", p/t}')
[[ "$PASSED" -eq "$TOTAL" ]] && SUCCESS="true" || SUCCESS="false"

cat <<EOF
{
  "success": $SUCCESS,
  "score": $SCORE,
  "metrics": {"precision": $PRECISION, "recall": $RECALL, "f1": $F1, "tp": $TP, "fp": $FP, "fn": $FN},
  "checks": {
    "file_exists":    $CHECK_FILE,
    "schema_valid":   $CHECK_SCHEMA,
    "recall_pass":    $CHECK_RECALL,
    "precision_pass": $CHECK_PREC,
    "f1_pass":        $CHECK_F1
  }
}
EOF
[[ "$SUCCESS" == "true" ]] && exit 0 || exit 1
```

```bash
chmod +x tasks/05_find_validation_gaps/verify.sh
git add tasks/05_find_validation_gaps/verify.sh
git commit -m "feat(05_gaps): add verify.sh with precision/recall/F1 scoring"
```

---

## Task 6: Metadata + end-to-end validace

- [ ] **Krok 1: `prompt.txt`**

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

- [ ] **Krok 2: `meta.yaml`**

```yaml
id: 05_find_validation_gaps
type: information_retrieval
description: Najít 5 API endpointů bez vstupní validace z 20 celkem. Scoring přes precision/recall/F1.

allowed_tools:
  - Read
  - Edit
  - Write
  - Glob
  - Grep
  - Bash

expected_duration_seconds: 300
success_criteria:
  - analysis.json existuje s validním schématem
  - recall >= 0.6 (nalezeno alespoň 3/5 endpointů)
  - precision >= 0.5
  - F1 >= 0.65

hypothesis: |
  Low effort zachytí jen zjevné případy (recall ~0.4-0.6, nalezne 2-3).
  High/max přečte pečlivě všechny soubory a identifikuje všech 5 (recall 1.0).
  High může over-report (lower precision). Medium jako sweet spot.
```

- [ ] **Krok 3: `README.md`**

```markdown
# Task 05 — Find Validation Gaps

## Cíl

Information retrieval úloha. Backend s 20 TypeScript API handlery.
15 má validaci, 5 nemá. Model musí najít ty bez validace a zapsat
je do `analysis.json`.

## Ground truth (5 endpointů bez validace)

| Method | Path | Soubor |
|--------|------|--------|
| POST | /api/users | src/api/users.ts |
| PUT | /api/users/:id | src/api/users.ts |
| POST | /api/products | src/api/products.ts |
| POST | /api/orders | src/api/orders.ts |
| PUT | /api/orders/:id | src/api/orders.ts |

## Scoring

verify.sh počítá precision/recall/F1 z porovnání s ground truth.
Pět verify checks: existence, schema, recall≥0.6, precision≥0.5, F1≥0.65.

## Hypotéza

Low: nalezne 2-3 (recall ~0.4-0.6). High/max: nalezne všech 5 (recall 1.0).
Tato úloha jako první může ukázat skutečný kvalitativní rozdíl effort levelů.

## Efforts testované

`low, medium, high, max` × 3 repetice = 12 běhů.
```

- [ ] **Krok 4: End-to-end validace — perfektní výstup (score 1.0)**

```bash
TMPDIR=$(mktemp -d)
cp -a tasks/05_find_validation_gaps/initial_repo/. "$TMPDIR/"
cd "$TMPDIR"
cat > analysis.json <<'EOF'
{
  "endpoints_without_validation": [
    {"path": "/api/users", "method": "POST", "file": "src/api/users.ts", "missing_validation": "email format, username length"},
    {"path": "/api/users/:id", "method": "PUT", "file": "src/api/users.ts", "missing_validation": "email format, username length"},
    {"path": "/api/products", "method": "POST", "file": "src/api/products.ts", "missing_validation": "name not empty, price > 0"},
    {"path": "/api/orders", "method": "POST", "file": "src/api/orders.ts", "missing_validation": "items not empty, quantities > 0"},
    {"path": "/api/orders/:id", "method": "PUT", "file": "src/api/orders.ts", "missing_validation": "status must be valid enum value"}
  ]
}
EOF
bash /Users/patrickzandl/GitHub/cc-effort-test/tasks/05_find_validation_gaps/verify.sh
cd /Users/patrickzandl/GitHub/cc-effort-test && rm -rf "$TMPDIR"
```

Očekávaný výstup: `"success": true`, `"score": 1.0000`, F1=1.0

- [ ] **Krok 5: End-to-end validace — partial výstup (score 0.6)**

```bash
TMPDIR=$(mktemp -d)
cp -a tasks/05_find_validation_gaps/initial_repo/. "$TMPDIR/"
cd "$TMPDIR"
cat > analysis.json <<'EOF'
{
  "endpoints_without_validation": [
    {"path": "/api/users", "method": "POST", "file": "src/api/users.ts", "missing_validation": "email format"},
    {"path": "/api/products", "method": "POST", "file": "src/api/products.ts", "missing_validation": "name not empty"},
    {"path": "/api/orders", "method": "POST", "file": "src/api/orders.ts", "missing_validation": "items not empty"}
  ]
}
EOF
bash /Users/patrickzandl/GitHub/cc-effort-test/tasks/05_find_validation_gaps/verify.sh
cd /Users/patrickzandl/GitHub/cc-effort-test && rm -rf "$TMPDIR"
```

Očekávaný výstup: `"success": false`, recall=0.6, precision=1.0, F1≈0.75 — check 3 projde, check 5 projde, ale ... actually F1=0.75 projde. Hmm — model našel 3/5 (recall=0.6) s precision=1.0, F1=0.75 → projde checks 3,4,5. Score=4/5=0.8.

- [ ] **Krok 6: Final commit**

```bash
git add tasks/05_find_validation_gaps/
git commit -m "feat(05_gaps): complete task 05 — validation gaps benchmark"
```
