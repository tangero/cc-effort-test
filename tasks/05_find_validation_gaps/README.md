# Task 05 — Find Validation Gaps

## Cíl

Information retrieval úloha. Backend s 20 TypeScript API handlery
(5 souborů). 15 má validaci, 5 nemá. Model musí najít ty bez validace
a zapsat je do `analysis.json`.

## Ground truth (5 endpointů bez validace)

| Method | Path | Soubor |
|--------|------|--------|
| POST | /api/users | src/api/users.ts |
| PUT | /api/users/:id | src/api/users.ts |
| POST | /api/products | src/api/products.ts |
| POST | /api/orders | src/api/orders.ts |
| PUT | /api/orders/:id | src/api/orders.ts |

## Scoring

verify.sh počítá precision/recall/F1 z porovnání modelu s ground truth.

## Verify checks (5)

1. `analysis.json` existuje
2. Validní JSON se správným schématem
3. Recall ≥ 0.6 (nalezeno alespoň 3/5)
4. Precision ≥ 0.5
5. F1 ≥ 0.65

## Hypotéza

Low: nalezne 2-3 (recall ~0.4-0.6). High/max: nalezne všech 5 (recall 1.0).
Tato úloha může jako první ukázat skutečný kvalitativní rozdíl effort levelů.

## Efforts testované

`low, medium, high, max` × 3 repetice = 12 běhů.
