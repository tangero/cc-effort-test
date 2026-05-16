# SWE-bench Task: sympy__sympy-24909

**Repo:** [sympy/sympy](https://github.com/sympy/sympy)
**Dataset:** princeton-nlp/SWE-bench_Lite
**Language:** python
**Base commit:** `d3b4158dea27`

## Problem Statement

Bug with milli prefix
What happened:
```
In [1]: from sympy.physics.units import milli, W
In [2]: milli*W == 1
Out[2]: True
In [3]: W*milli
Out[3]: watt*Prefix(milli, m, -3, 10)
```
What I expected to happen: milli*W should evaluate to milli watts / mW

`milli*W` or more generally `milli` times some unit evaluates to the number 1. I have tried this with Watts and Volts, I'm not sure what other cases this happens. I'm using sympy version 1.11.1-1 on Arch Linux with Python 3.10.9. If you cannot reproduce I would be happy to be of any assitance.

## Failing Tests (must pass after fix)

- `test_prefix_operations`

## Setup

```bash
# Generate initial_repo.tar.gz (once):
python3 scripts/swe_bench_import.py --instance sympy__sympy-24909 --force

# Run benchmark:
bash runner/run_single.sh tasks/swe_sympy__sympy-24909 low 1
```
