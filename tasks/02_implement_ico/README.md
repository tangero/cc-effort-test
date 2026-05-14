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
