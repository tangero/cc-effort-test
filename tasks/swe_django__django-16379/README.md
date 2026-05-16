# SWE-bench Task: django__django-16379

**Repo:** [django/django](https://github.com/django/django)
**Dataset:** princeton-nlp/SWE-bench_Lite
**Language:** python
**Base commit:** `1d0fa848e084`

## Problem Statement

FileBasedCache has_key is susceptible to race conditions
Description
	 
		(last modified by Marti Raudsepp)
	 
I received the exception from Django's cache framework:
FileNotFoundError: [Errno 2] No such file or directory: '/app/var/cache/d729e4cf4ba88cba5a0f48e0396ec48a.djcache'
[...]
 File "django/core/cache/backends/base.py", line 229, in get_or_set
	self.add(key, default, timeout=timeout, version=version)
 File "django/core/cache/backends/filebased.py", line 26, in add
	if self.has_key(key, version):
 File "django/core/cache/backends/filebased.py", line 94, in has_key
	with open(fname, "rb") as f:
The code is:
	def has_key(self, key, version=None):
		fname = self._key_to_file(key, version)
		if os.path.exists(fname):
			with open(fname, "rb") as f:
				return not self._is_expired(f)
		return False
Between the exists() check and open(), it's possible for the file to be deleted. In fact, the _is_expired() method itself deletes the file if it finds it to be expired. So if many threads race to read an expired cache at once, it's not that unlikely to hit this window.

## Failing Tests (must pass after fix)

- `test_has_key_race_handling (cache.tests.FileBasedCachePathLibTests)`
- `test_has_key_race_handling (cache.tests.FileBasedCacheTests)`

## Setup

```bash
# Generate initial_repo.tar.gz (once):
python3 scripts/swe_bench_import.py --instance django__django-16379 --force

# Run benchmark:
bash runner/run_single.sh tasks/swe_django__django-16379 low 1
```
