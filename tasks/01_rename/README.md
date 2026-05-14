# Task 01 — Rename `userId` → `accountId`

## Cíl

Mechanická rename úloha. Model dostane synthetic TypeScript projekt
(~57 výskytů identifikátoru `userId` napříč 8 source soubory + 3 config
soubory) a má provést konzistentní rename na `accountId`.

## Typ úlohy

`mechanical` — strict scope, žádné architektonické rozhodnutí.

## Prompt

Viz `prompt.txt` (bit-by-bit kopírovaný do každého běhu):

```
Rename the identifier `userId` to `accountId` throughout the codebase.
Update all related JSDoc comments to reflect the new naming.
Ensure that all tests still pass after the rename.
Do not modify any logic or behavior, only the identifier name.
```

## Initial state

`initial_repo/` obsahuje:

| Soubor | Účel | userId počty |
|--------|------|--------------|
| `src/types.ts` | doménové typy (User, Session, AuditEntry) | 5 |
| `src/repositories/userRepository.ts` | in-memory CRUD repo | 10 |
| `src/services/userService.ts` | business logic | 13 |
| `src/controllers/userController.ts` | HTTP adaptér | 6 |
| `src/middleware/auth.ts` | JWT-like token decoder | 7 |
| `src/utils/logger.ts` | structured logger | 1 |
| `src/__tests__/userRepository.test.ts` | jednotkové testy | 9 |
| `src/__tests__/userService.test.ts` | jednotkové testy | 6 |
| `package.json`, `tsconfig.json`, `jest.config.js` | config | 0 |

**Distraktory** (musí zůstat netknuté):

- `userIdentifier` — externí SSO claim, jiný koncept (3 výskyty)
- `useridx` — legacy Postgres column v komentáři (1 výskyt)
- `UserID` — uppercase historický LDAP název v komentáři (1 výskyt)

Initial repo má passing tests a clean `tsc --noEmit`.

## Verify checks

Viz `verify.sh`. Sedm hard checks:

1. `userId` count = 0
2. `accountId` count > 0
3. `userIdentifier` zachováno (≥ 3)
4. `useridx` zachováno (≥ 1)
5. `UserID` v komentáři zachováno (≥ 1)
6. `tsc --noEmit` → exit 0
7. `jest` → exit 0

Plus reported (informativně, mimo score):

- diff insertions count (sanity check pro over-engineering)

`success: true` jen pokud všech 7 checks passes.

## Expected solution

`expected_solution/` je reference rename pro validation verifier
(`scripts/validate_verifier.sh`). NEPOROVNÁVÁ se s outputem modelu —
slouží jen k tomu, aby ověřilo, že verify.sh správně rozpozná "perfect" rename.

## Hypotéza pro analýzu

Low effort dosahuje 100% success rate. Vyšší efforty produkují srovnatelný
výsledek za výrazně víc tokenů. Max může over-engineerovat (přidávat
refactor `findById` → `findByAccountId` na úrovní method names, lokalizaci,
linting fixes mimo scope, atd.).

## Efforts testované

`low, medium, xhigh, max` × 3 repetice = 12 běhů.
