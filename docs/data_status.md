# Data Status: Aktuální vs. Cílový stav

**Generováno:** 2026-05-17

## Legenda
- ✅ = kompletní (n=3+)
- ⚠️ = částečný (1–2 runy na buňku, nebo chybějící efforty)
- ❌ = chybí (0 runů celkem)
- **Cíl:** n=3 repetice pro každý (task, effort) u Opus 4.7
- **Sonnet 4.6:** Phase 2 — zatím žádné runy

## Syntetické úlohy

| Task | low | medium | high | max | Celkem | Cíl | Status |
|------|-----|--------|------|-----|--------|-----|--------|
| 01_rename | ✅ 4 | ✅ 4 | ✅ 4 | ✅ 3 | 15/12 | ✅ Kompletní |
| 02_implement_ico | ✅ 3 | ✅ 3 | ✅ 3 | ✅ 3 | 12/12 | ✅ Kompletní |
| 03_debug_order | ✅ 3 | ❌ 0 | ❌ 0 | ✅ 3 | 6/12 | ⚠️ Částečný |
| 05_find_validation_gaps | ✅ 6 | ✅ 6 | ✅ 6 | — | 24/9 | ✅ Kompletní |
| 06_strict_scope | ✅ 3 | ✅ 3 | ✅ 3 | ✅ 3 | 12/12 | ✅ Kompletní |
| 07_security_audit | ⚠️ 1 | ❌ 0 | ❌ 0 | ❌ 0 | 1/12 | ⚠️ Částečný |
| 08_async_bugs | ✅ 3 | ❌ 0 | ❌ 0 | ❌ 0 | 3/12 | ⚠️ Částečný |

## SWE-bench úlohy

| Task | low | medium | high | max | Celkem | Cíl | Status | Poznámka |
|------|-----|--------|------|-----|--------|-----|--------|----------|
| swe_astropy__astropy-12907 | ✅ 5 | ❌ 0 | ❌ 0 | ❌ 0 | 5/12 | ⚠️ Částečný | C extensions — všechny runy selhaly, nevhodné pro benchmark |
| swe_django__django-14016 | ⚠️ 1 | ❌ 0 | ❌ 0 | ❌ 0 | 1/12 | ⚠️ Částečný | Jen low, 1 run — nízká priorita |
| swe_django__django-16379 | ⚠️ 2 | ❌ 0 | ❌ 0 | ❌ 0 | 2/12 | ⚠️ Částečný | Jen low, 2 runy — doplnit medium+ |
| swe_django__django-16408 | ✅ 4 | ✅ 3 | ✅ 3 | ✅ 3 | 13/12 | ✅ Kompletní | Nejostřejší gradient, kompletní |
| swe_django__django-16820 | ✅ 4 | ⚠️ 2 | ✅ 3 | ✅ 3 | 12/12 | ⚠️ Částečný | Ostrý gradient, kompletní |
| swe_django__django-16910 | ✅ 3 | ✅ 4 | ✅ 4 | ✅ 3 | 14/12 | ✅ Kompletní | Silný gradient, kompletní |
| swe_django__django-17051 | ⚠️ 1 | ❌ 0 | ❌ 0 | ❌ 0 | 1/12 | ⚠️ Částečný | Jen low, 1 run — nízká priorita |
| swe_sympy__sympy-11400 | ⚠️ 2 | ❌ 0 | ❌ 0 | ❌ 0 | 2/12 | ⚠️ Částečný | Jen low, 2 runy |
| swe_sympy__sympy-21612 | ⚠️ 2 | ❌ 0 | ❌ 0 | ❌ 0 | 2/12 | ⚠️ Částečný | Jen low, 2 runy |
| swe_sympy__sympy-22840 | ✅ 4 | ✅ 3 | ✅ 3 | ✅ 5 | 15/12 | ✅ Kompletní | Nejcennější multi-aspect case, kompletní |
| swe_sympy__sympy-24909 | ⚠️ 2 | ⚠️ 1 | ⚠️ 1 | ⚠️ 1 | 5/12 | ⚠️ Částečný | Nedostatek dat na některých effortech |

## Souhrn

- **Celkem tasků:** 18
- **Celkem runů:** 145 / 213 cíl (68%)
- **Kompletní tasky:** 7 / 18
- **Částečné tasky:** 11 / 18
- **Tasky bez dat:** 0 / 18

## Priorita doplnění

1. **03_debug_order** — doplnit medium, high (máme jen low + max)
2. **07_security_audit** — doplnit na n=3 pro všechny efforty (jen 1 run)
3. **08_async_bugs** — doplnit na n=3 pro medium, high, max (jen 3 low runy)
4. **swe_sympy__sympy-24909** — doplnit na n=3 (některé efforty jen 1 run)
5. **swe_django__django-16820** — doplnit medium na n=3 (má 2 runy)
6. **swe_django__django-16379** — doplnit medium+ (jen 2 low runy)
7. **swe_django__django-14016, swe_django__django-17051** — jen 1 run each, nízká priorita
8. **swe_sympy__sympy-11400, swe_sympy__sympy-21612** — jen 2 low runy, nízká priorita
9. **swe_astropy__astropy-12907** — C extensions problém, všechny selhaly, odstranit z benchmarku
10. **Sonnet 4.6** — Phase 2, zatím žádné runy

## Poznámky

- Původní specifikace (PRD) počítala se 6 syntetickými úlohami (01–06).
- Rozšířili jsme o 07, 08 a 7 SWE-bench instancí pro reálnější data.
- xhigh effort byl odstraněn z testování (runner ho filtruje pro Opus 4.7).
- Náklady dosud: ~$115 za 145 runů.
- Odhad nákladů na doplnění chybějících buněk: ~$40–70.
