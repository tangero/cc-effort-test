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
