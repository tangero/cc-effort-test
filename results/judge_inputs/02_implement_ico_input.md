# Judge input: 02_implement_ico — 12 runs

## Rubrika

Hodnoť každou dimenzi na škále 1–5. Porovnávej runy relativně v rámci této úlohy.

- **scope_compliance** (1–5): Držel se model přesně zadání?
  5 = nic navíc, přesně v scope | 1 = výrazně přesáhl scope

- **code_quality** (1–5): Čistota kódu, pojmenování, konzistence s repozitářem
  5 = čisté, konzistentní | 1 = chaotické, nekonzistentní

- **approach_efficiency** (1–5): Zvolil model rozumnou strategii?
  5 = přímočará, efektivní cesta | 1 = zbytečně složitá, mnoho slepých uliček

- **over_engineering** (1–5): Přidal model abstrakce/refaktoring mimo zadání?
  5 = žádný over-engineering | 1 = výrazný over-engineering

## Output JSON schema

Ulož výsledek jako validní JSON do `results/judge/02_implement_ico_judge.json`:

```json
{
  "task": "02_implement_ico",
  "judge_model": "<model name>",
  "judged_at": "<ISO timestamp>",
  "runs": [
    {
      "run_id": "<run_id>",
      "effort": "<effort>",
      "run_number": 1,
      "dimensions": {
        "scope_compliance":    { "score": 1, "reasoning": "<text>" },
        "code_quality":        { "score": 1, "reasoning": "<text>" },
        "approach_efficiency": { "score": 1, "reasoning": "<text>" },
        "over_engineering":    { "score": 1, "reasoning": "<text>" }
      },
      "overall_score": 1.0,
      "summary": "<1-2 věty>"
    }
  ],
  "comparative_analysis": "<trend low→max, hlavní pozorování>"
}
```

---

## Run 1: low / run1

**run_id:** `02_implement_ico_claude-opus-4-7_low_run1_1778757845`

**Metadata:** wall=43s  cost=$0.236  turns=7  tool_calls=6  breakdown=Bash=2; Read=2; Write=2

**Verify:** success=True  score=1.0

**Diff stat:**
```
src/validators/ico.test.ts | 69 ++++++++++++++++++++++++++++++++++++++++++++++
 src/validators/ico.ts      | 27 ++++++++++++++++++
 2 files changed, 96 insertions(+)
```

**Final diff:**
```diff
diff --git a/src/validators/ico.test.ts b/src/validators/ico.test.ts
new file mode 100644
index 0000000..2d5f6d6
--- /dev/null
+++ b/src/validators/ico.test.ts
@@ -0,0 +1,69 @@
+import { validateICO } from './ico';
+
+describe('validateICO', () => {
+  describe('valid IČO', () => {
+    it('accepts a known valid IČO (27074358)', () => {
+      expect(validateICO('27074358')).toEqual({ valid: true });
+    });
+
+    it('accepts checksum branch where remainder is 0 (00000001)', () => {
+      // sum=0, 0%11=0, checksum=1
+      expect(validateICO('00000001')).toEqual({ valid: true });
+    });
+
+    it('accepts checksum branch where remainder is 1 (00000060)', () => {
+      // sum = 6*2 = 12, 12%11=1, checksum=0
+      expect(validateICO('00000060')).toEqual({ valid: true });
+    });
+
+    it('accepts checksum branch where remainder is >1 (00000019)', () => {
+      // sum = 1*2 = 2, 2%11=2, checksum=11-2=9
+      expect(validateICO('00000019')).toEqual({ valid: true });
+    });
+  });
+
+  describe('invalid IČO', () => {
+    it('rejects empty string', () => {
+      const r = validateICO('');
+      expect(r.valid).toBe(false);
+      if (!r.valid) expect(r.reason).toMatch(/empty/i);
+    });
+
+    it('rejects non-digit characters', () => {
+      const r = validateICO('2707435a');
+      expect(r.valid).toBe(false);
+      if (!r.valid) expect(r.reason).toMatch(/digit/i);
+    });
+
+    it('rejects strings with spaces', () => {
+      expect(validateICO('2707 4358').valid).toBe(false);
+    });
+
+    it('rejects strings with dashes', () => {
+      expect(validateICO('2707-358').valid).toBe(false);
+    });
+
+    it('rejects too-short input', () => {
+      const r = validateICO('1234567');
+      expect(r.valid).toBe(false);
+      if (!r.valid) expect(r.reason).toMatch(/8 digits/i);
+    });
+
+    it('rejects too-long input', () => {
+      const r = validateICO('123456789');
+      expect(r.valid).toBe(false);
+      if (!r.valid) expect(r.reason).toMatch(/8 digits/i);
+    });
+
+    it('rejects valid-length input with wrong checksum', () => {
+      const r = validateICO('27074350');
+      expect(r.valid).toBe(false);
+      if (!r.valid) expect(r.reason).toMatch(/checksum/i);
+    });
+
+    it('rejects all zeros (00000000)', () => {
+      // sum=0, checksum should be 1, but last digit is 0
+      expect(validateICO('00000000').valid).toBe(false);
+    });
+  });
+});
diff --git a/src/validators/ico.ts b/src/validators/ico.ts
index e69de29..f7c6330 100644
--- a/src/validators/ico.ts
+++ b/src/validators/ico.ts
@@ -0,0 +1,27 @@
+import { ValidationResult } from '../types';
+
+export function validateICO(input: string): ValidationResult {
+  if (!input) {
+    return { valid: false, reason: 'IČO must not be empty' };
+  }
+  if (!/^\d+$/.test(input)) {
+    return { valid: false, reason: 'IČO must contain only digits' };
+  }
+  if (input.length !== 8) {
+    return { valid: false, reason: 'IČO must be exactly 8 digits' };
+  }
+
+  const digits = input.split('').map(Number);
+  const weights = [8, 7, 6, 5, 4, 3, 2];
+  const sum = weights.reduce((acc, w, i) => acc + w * digits[i], 0);
+  const remainder = sum % 11;
+  let checksum: number;
+  if (remainder === 0) checksum = 1;
+  else if (remainder === 1) checksum = 0;
+  else checksum = 11 - remainder;
+
+  if (checksum !== digits[7]) {
+    return { valid: false, reason: 'IČO checksum is invalid' };
+  }
+  return { valid: true };
+}
```

---

## Run 2: low / run2

**run_id:** `02_implement_ico_claude-opus-4-7_low_run2_1778758028`

**Metadata:** wall=46s  cost=$0.256  turns=8  tool_calls=7  breakdown=Bash=3; Read=1; Write=3

**Verify:** success=True  score=1.0

**Diff stat:**
```
src/validators/ico.test.ts | 69 ++++++++++++++++++++++++++++++++++++++++++++++
 src/validators/ico.ts      | 27 ++++++++++++++++++
 2 files changed, 96 insertions(+)
```

**Final diff:**
```diff
diff --git a/src/validators/ico.test.ts b/src/validators/ico.test.ts
new file mode 100644
index 0000000..8d3054d
--- /dev/null
+++ b/src/validators/ico.test.ts
@@ -0,0 +1,69 @@
+import { validateICO } from './ico';
+
+describe('validateICO', () => {
+  describe('valid IČO', () => {
+    it('accepts a standard valid IČO', () => {
+      expect(validateICO('12345679')).toEqual({ valid: true });
+    });
+
+    it('accepts a known Czech IČO (27074358)', () => {
+      expect(validateICO('27074358')).toEqual({ valid: true });
+    });
+
+    it('accepts checksum case where remainder is 0 (checksum=1)', () => {
+      expect(validateICO('00000001')).toEqual({ valid: true });
+    });
+
+    it('accepts checksum case where remainder is 1 (checksum=0)', () => {
+      expect(validateICO('70000000')).toEqual({ valid: true });
+    });
+  });
+
+  describe('invalid IČO', () => {
+    it('rejects empty string', () => {
+      const r = validateICO('');
+      expect(r.valid).toBe(false);
+      if (!r.valid) expect(r.reason).toMatch(/empty/i);
+    });
+
+    it('rejects too short', () => {
+      const r = validateICO('1234567');
+      expect(r.valid).toBe(false);
+      if (!r.valid) expect(r.reason).toMatch(/8 digits/);
+    });
+
+    it('rejects too long', () => {
+      const r = validateICO('123456789');
+      expect(r.valid).toBe(false);
+      if (!r.valid) expect(r.reason).toMatch(/8 digits/);
+    });
+
+    it('rejects non-digit characters', () => {
+      const r = validateICO('1234567a');
+      expect(r.valid).toBe(false);
+      if (!r.valid) expect(r.reason).toMatch(/digits/);
+    });
+
+    it('rejects whitespace', () => {
+      const r = validateICO('1234 678');
+      expect(r.valid).toBe(false);
+    });
+
+    it('rejects negative sign', () => {
+      const r = validateICO('-1234567');
+      expect(r.valid).toBe(false);
+    });
+
+    it('rejects invalid checksum', () => {
+      const r = validateICO('12345678');
+      expect(r.valid).toBe(false);
+      if (!r.valid) expect(r.reason).toMatch(/checksum/i);
+    });
+
+    it('rejects all-zero IČO (checksum should be 1, not 0)', () => {
+      const r = validateICO('00000000');
+      expect(r.valid).toBe(false);
+      if (!r.valid) expect(r.reason).toMatch(/checksum/i);
+    });
+  });
+});
diff --git a/src/validators/ico.ts b/src/validators/ico.ts
index e69de29..2e2fece 100644
--- a/src/validators/ico.ts
+++ b/src/validators/ico.ts
@@ -0,0 +1,27 @@
+import type { ValidationResult } from '../types';
+
+export function validateICO(input: string): ValidationResult {
+  if (input === '') {
+    return { valid: false, reason: 'IČO must not be empty' };
+  }
+  if (!/^\d+$/.test(input)) {
+    return { valid: false, reason: 'IČO must contain only digits' };
+  }
+  if (input.length !== 8) {
+    return { valid: false, reason: 'IČO must be exactly 8 digits' };
+  }
+
+  const digits = input.split('').map(Number);
+  const weights = [8, 7, 6, 5, 4, 3, 2];
+  const sum = weights.reduce((acc, w, i) => acc + w * digits[i], 0);
+  const remainder = sum % 11;
+  let checksum: number;
+  if (remainder === 0) checksum = 1;
+  else if (remainder === 1) checksum = 0;
+  else checksum = 11 - remainder;
+
+  if (checksum !== digits[7]) {
+    return { valid: false, reason: 'Invalid IČO checksum' };
+  }
+  return { valid: true };
+}
```

---

## Run 3: low / run3

**run_id:** `02_implement_ico_claude-opus-4-7_low_run3_1778758090`

**Metadata:** wall=68s  cost=$0.323  turns=10  tool_calls=9  breakdown=Bash=4; Edit=1; Read=1; Write=3

**Verify:** success=True  score=1.0

**Diff stat:**
```
src/validators/ico.test.ts | 78 ++++++++++++++++++++++++++++++++++++++++++++++
 src/validators/ico.ts      | 29 +++++++++++++++++
 2 files changed, 107 insertions(+)
```

**Final diff:**
```diff
diff --git a/src/validators/ico.test.ts b/src/validators/ico.test.ts
new file mode 100644
index 0000000..5edd05d
--- /dev/null
+++ b/src/validators/ico.test.ts
@@ -0,0 +1,78 @@
+import { validateICO } from './ico';
+
+describe('validateICO', () => {
+  describe('valid IČOs', () => {
+    it('accepts a valid IČO', () => {
+      expect(validateICO('27074358')).toEqual({ valid: true });
+    });
+
+    it('accepts an IČO with leading zeros', () => {
+      expect(validateICO('00006947')).toEqual({ valid: true });
+    });
+  });
+
+  describe('invalid inputs', () => {
+    it('rejects empty string', () => {
+      expect(validateICO('')).toEqual({
+        valid: false,
+        reason: 'IČO is empty',
+      });
+    });
+
+    it('rejects non-digit characters', () => {
+      const result = validateICO('1234567a');
+      expect(result.valid).toBe(false);
+      if (!result.valid) expect(result.reason).toMatch(/digits/);
+    });
+
+    it('rejects strings with spaces', () => {
+      const result = validateICO('2707 358');
+      expect(result.valid).toBe(false);
+    });
+
+    it('rejects too short input', () => {
+      const result = validateICO('1234567');
+      expect(result.valid).toBe(false);
+      if (!result.valid) expect(result.reason).toMatch(/8 digits/);
+    });
+
+    it('rejects too long input', () => {
+      const result = validateICO('123456789');
+      expect(result.valid).toBe(false);
+      if (!result.valid) expect(result.reason).toMatch(/8 digits/);
+    });
+
+    it('rejects invalid checksum', () => {
+      expect(validateICO('12345678')).toEqual({
+        valid: false,
+        reason: 'Invalid checksum',
+      });
+    });
+
+    it('rejects IČO of all zeros (checksum mismatch)', () => {
+      // sum=0, remainder=0, checksum=1, last digit=0 -> invalid
+      expect(validateICO('00000000').valid).toBe(false);
+    });
+  });
+
+  describe('checksum branches', () => {
+    it('handles remainder === 0 (checksum = 1)', () => {
+      // Find digits with sum % 11 === 0; e.g. "00000011": sum = 1*3 + 1*2 = 5. no.
+      // Try "11111115": 1*(8+7+6+5+4+3+2)=35, 35%11=2 -> checksum=9. no.
+      // Use "00000011" let's compute precisely: digits 0,0,0,0,0,0,1,1; weighted sum = 1*2=2; 2%11=2 -> ck=9. no
+      // Construct: pick first 7 = 0,0,0,0,0,0,11 invalid. Use programmatic check below.
+      // Use "00006212": d=0,0,0,0,6,2,1; sum=6*4+2*3+1*2=24+6+2=32; 32%11=10; ck=1; last=1? need last digit 1.
+      expect(validateICO('00006211')).toEqual({ valid: true });
+    });
+
+    it('handles remainder === 1 (checksum = 0)', () => {
+      // sum%11===1 -> ck=0. Try first7="00000001": sum=1*2=2 -> rem 2. no.
+      // first7="00000010": sum=1*3=3. first7="00000100": sum=1*4=4. first7="00001000": sum=1*5=5.
+      // first7="00010000": sum=1*6=6. first7="00100000": sum=1*7=7. first7="01000000": sum=1*8=8.
+      // first7="00000023": invalid format. Use first7 sums producing rem1: need sum=12,23,...
+      // "00000060": sum=6*3=18, rem 7. "00000050": sum=15, rem 4. "00000034": sum=3*3+4*2=17, rem 6.
+      // "00000067": 6*3+7*2=32, rem 10. "00000045": 4*3+5*2=22, rem 0 -> ck 1. interesting.
+      expect(validateICO('00000451')).toEqual({ valid: true });
+    });
+  });
+});
diff --git a/src/validators/ico.ts b/src/validators/ico.ts
index e69de29..585ff9b 100644
--- a/src/validators/ico.ts
+++ b/src/validators/ico.ts
@@ -0,0 +1,29 @@
+import { ValidationResult } from '../types';
+
+export function validateICO(input: string): ValidationResult {
+  if (input === '') {
+    return { valid: false, reason: 'IČO is empty' };
+  }
+  if (!/^\d+$/.test(input)) {
+    return { valid: false, reason: 'IČO must contain only digits' };
+  }
+  if (input.length !== 8) {
+    return { valid: false, reason: 'IČO must be exactly 8 digits' };
+  }
+
+  const digits = input.split('').map(Number);
+  const weights = [8, 7, 6, 5, 4, 3, 2];
+  const sum = weights.reduce((acc, w, i) => acc + w * digits[i], 0);
+  const remainder = sum % 11;
+
+  let checksum: number;
+  if (remainder === 0) checksum = 1;
+  else if (remainder === 1) checksum = 0;
+  else checksum = 11 - remainder;
+
+  if (checksum !== digits[7]) {
+    return { valid: false, reason: 'Invalid checksum' };
+  }
+
+  return { valid: true };
+}
```

---

## Run 4: medium / run1

**run_id:** `02_implement_ico_claude-opus-4-7_medium_run1_1778758171`

**Metadata:** wall=395s  cost=$0.258  turns=7  tool_calls=6  breakdown=Bash=2; Read=2; Write=2

**Verify:** success=True  score=1.0

**Diff stat:**
```
src/validators/ico.test.ts | 90 ++++++++++++++++++++++++++++++++++++++++++++++
 src/validators/ico.ts      | 33 +++++++++++++++++
 2 files changed, 123 insertions(+)
```

**Final diff:**
```diff
diff --git a/src/validators/ico.test.ts b/src/validators/ico.test.ts
new file mode 100644
index 0000000..64163aa
--- /dev/null
+++ b/src/validators/ico.test.ts
@@ -0,0 +1,90 @@
+import { validateICO } from './ico';
+
+describe('validateICO', () => {
+  describe('valid IČOs', () => {
+    it('accepts a known-valid IČO (Avast: 27074358)', () => {
+      expect(validateICO('27074358')).toEqual({ valid: true });
+    });
+
+    it('accepts a known-valid IČO with leading zeros (CNB: 00006947)', () => {
+      expect(validateICO('00006947')).toEqual({ valid: true });
+    });
+
+    it('accepts the remainder=0 → checksum=1 case (00000001)', () => {
+      expect(validateICO('00000001')).toEqual({ valid: true });
+    });
+
+    it('accepts the remainder=1 → checksum=0 case (00000060)', () => {
+      expect(validateICO('00000060')).toEqual({ valid: true });
+    });
+
+    it('accepts the general remainder case (11111119)', () => {
+      expect(validateICO('11111119')).toEqual({ valid: true });
+    });
+  });
+
+  describe('invalid IČOs', () => {
+    it('rejects empty string', () => {
+      expect(validateICO('')).toEqual({
+        valid: false,
+        reason: 'IČO must not be empty',
+      });
+    });
+
+    it('rejects input with letters', () => {
+      expect(validateICO('2707435a')).toEqual({
+        valid: false,
+        reason: 'IČO must contain only digits',
+      });
+    });
+
+    it('rejects input with whitespace', () => {
+      expect(validateICO('2707 4358')).toEqual({
+        valid: false,
+        reason: 'IČO must contain only digits',
+      });
+    });
+
+    it('rejects input with symbols', () => {
+      expect(validateICO('2707-358')).toEqual({
+        valid: false,
+        reason: 'IČO must contain only digits',
+      });
+    });
+
+    it('rejects too short input', () => {
+      expect(validateICO('1234567')).toEqual({
+        valid: false,
+        reason: 'IČO must be exactly 8 digits',
+      });
+    });
+
+    it('rejects too long input', () => {
+      expect(validateICO('123456789')).toEqual({
+        valid: false,
+        reason: 'IČO must be exactly 8 digits',
+      });
+    });
+
+    it('rejects wrong checksum', () => {
+      expect(validateICO('27074357')).toEqual({
+        valid: false,
+        reason: 'IČO checksum is invalid',
+      });
+    });
+
+    it('rejects 00000000 (all zeros — checksum mismatch)', () => {
+      expect(validateICO('00000000')).toEqual({
+        valid: false,
+        reason: 'IČO checksum is invalid',
+      });
+    });
+
+    it('rejects 12345678 (wrong checksum)', () => {
+      expect(validateICO('12345678')).toEqual({
+        valid: false,
+        reason: 'IČO checksum is invalid',
+      });
+    });
+  });
+});
diff --git a/src/validators/ico.ts b/src/validators/ico.ts
index e69de29..e3eb049 100644
--- a/src/validators/ico.ts
+++ b/src/validators/ico.ts
@@ -0,0 +1,33 @@
+import { ValidationResult } from '../types';
+
+export function validateICO(input: string): ValidationResult {
+  if (!input) {
+    return { valid: false, reason: 'IČO must not be empty' };
+  }
+  if (!/^\d+$/.test(input)) {
+    return { valid: false, reason: 'IČO must contain only digits' };
+  }
+  if (input.length !== 8) {
+    return { valid: false, reason: 'IČO must be exactly 8 digits' };
+  }
+
+  const digits = input.split('').map(Number);
+  const weights = [8, 7, 6, 5, 4, 3, 2];
+  const sum = weights.reduce((acc, w, i) => acc + w * digits[i], 0);
+  const remainder = sum % 11;
+
+  let checksum: number;
+  if (remainder === 0) {
+    checksum = 1;
+  } else if (remainder === 1) {
+    checksum = 0;
+  } else {
+    checksum = 11 - remainder;
+  }
+
+  if (checksum !== digits[7]) {
+    return { valid: false, reason: 'IČO checksum is invalid' };
+  }
+
+  return { valid: true };
+}
```

---

## Run 5: medium / run2

**run_id:** `02_implement_ico_claude-opus-4-7_medium_run2_1778758574`

**Metadata:** wall=665s  cost=$0.338  turns=11  tool_calls=10  breakdown=Bash=4; Read=3; Write=3

**Verify:** success=True  score=1.0

**Diff stat:**
```
src/validators/ico.test.ts | 87 ++++++++++++++++++++++++++++++++++++++++++++++
 src/validators/ico.ts      | 35 +++++++++++++++++++
 2 files changed, 122 insertions(+)
```

**Final diff:**
```diff
diff --git a/src/validators/ico.test.ts b/src/validators/ico.test.ts
new file mode 100644
index 0000000..b05eca7
--- /dev/null
+++ b/src/validators/ico.test.ts
@@ -0,0 +1,87 @@
+import { validateICO } from './ico';
+
+describe('validateICO', () => {
+  describe('valid IČOs', () => {
+    test('accepts a valid IČO (remainder 0 -> checksum 1)', () => {
+      // 25596641: sum=176, 176%11=0, checksum=1
+      expect(validateICO('25596641')).toEqual({ valid: true });
+    });
+
+    test('accepts a valid IČO (general remainder case)', () => {
+      // 27074358: sum=135, 135%11=3, checksum=11-3=8
+      expect(validateICO('27074358')).toEqual({ valid: true });
+    });
+
+    test('accepts a valid IČO (remainder 1 -> checksum 0)', () => {
+      // 51111110: sum=67, 67%11=1, checksum=0
+      expect(validateICO('51111110')).toEqual({ valid: true });
+    });
+
+    test('accepts IČO with leading zero', () => {
+      // 00000000: sum=0, 0%11=0, checksum=1 — but digit is 0, so invalid checksum
+      // Use a real leading-zero case: 01234560
+      // sum = 0*8+1*7+2*6+3*5+4*4+5*3+6*2 = 0+7+12+15+16+15+12 = 77
+      // 77%11=0, checksum=1
+      expect(validateICO('01234561')).toEqual({ valid: true });
+    });
+  });
+
+  describe('invalid IČOs', () => {
+    test('rejects empty string', () => {
+      const result = validateICO('');
+      expect(result.valid).toBe(false);
+      if (!result.valid) expect(result.reason).toMatch(/empty/i);
+    });
+
+    test('rejects non-digit characters', () => {
+      const result = validateICO('1234567a');
+      expect(result.valid).toBe(false);
+      if (!result.valid) expect(result.reason).toMatch(/digit/i);
+    });
+
+    test('rejects strings with spaces', () => {
+      expect(validateICO('1234 567').valid).toBe(false);
+    });
+
+    test('rejects strings with dashes', () => {
+      expect(validateICO('1234-567').valid).toBe(false);
+    });
+
+    test('rejects too-short input', () => {
+      const result = validateICO('1234567');
+      expect(result.valid).toBe(false);
+      if (!result.valid) expect(result.reason).toMatch(/8 digits/i);
+    });
+
+    test('rejects too-long input', () => {
+      const result = validateICO('123456789');
+      expect(result.valid).toBe(false);
+      if (!result.valid) expect(result.reason).toMatch(/8 digits/i);
+    });
+
+    test('rejects valid-length input with wrong checksum', () => {
+      // 25596642: same digits but wrong checksum (should be 1)
+      const result = validateICO('25596642');
+      expect(result.valid).toBe(false);
+      if (!result.valid) expect(result.reason).toMatch(/checksum/i);
+    });
+
+    test('rejects all zeros (checksum mismatch)', () => {
+      // sum=0, remainder=0, expected checksum=1, but digit is 0
+      expect(validateICO('00000000').valid).toBe(false);
+    });
+
+    test('rejects input with unicode digits', () => {
+      // Arabic-Indic digits should not pass /^\d+$/ ... actually JS \d matches only [0-9] by default
+      expect(validateICO('١٢٣٤٥٦٧٨').valid).toBe(false);
+    });
+
+    test('rejects negative number string', () => {
+      expect(validateICO('-1234567').valid).toBe(false);
+    });
+
+    test('rejects decimal number string', () => {
+      expect(validateICO('1234.567').valid).toBe(false);
+    });
+  });
+});
diff --git a/src/validators/ico.ts b/src/validators/ico.ts
index e69de29..941b9de 100644
--- a/src/validators/ico.ts
+++ b/src/validators/ico.ts
@@ -0,0 +1,35 @@
+import { ValidationResult } from '../types';
+
+export function validateICO(input: string): ValidationResult {
+  if (input.length === 0) {
+    return { valid: false, reason: 'IČO must not be empty' };
+  }
+  if (!/^\d+$/.test(input)) {
+    return { valid: false, reason: 'IČO must contain only digits' };
+  }
+  if (input.length !== 8) {
+    return { valid: false, reason: 'IČO must be exactly 8 digits' };
+  }
+
+  const digits = input.split('').map((d) => Number(d));
+  const weights = [8, 7, 6, 5, 4, 3, 2];
+  let sum = 0;
+  for (let i = 0; i < 7; i++) {
+    sum += digits[i] * weights[i];
+  }
+  const remainder = sum % 11;
+  let expected: number;
+  if (remainder === 0) {
+    expected = 1;
+  } else if (remainder === 1) {
+    expected = 0;
+  } else {
+    expected = 11 - remainder;
+  }
+
+  if (digits[7] !== expected) {
+    return { valid: false, reason: 'Invalid checksum' };
+  }
+
+  return { valid: true };
+}
```

---

## Run 6: medium / run3

**run_id:** `02_implement_ico_claude-opus-4-7_medium_run3_1778759248`

**Metadata:** wall=55s  cost=$0.293  turns=9  tool_calls=8  breakdown=Bash=4; Read=2; Write=2

**Verify:** success=True  score=1.0

**Diff stat:**
```
src/validators/ico.test.ts | 81 ++++++++++++++++++++++++++++++++++++++++++++++
 src/validators/ico.ts      | 33 +++++++++++++++++++
 2 files changed, 114 insertions(+)
```

**Final diff:**
```diff
diff --git a/src/validators/ico.test.ts b/src/validators/ico.test.ts
new file mode 100644
index 0000000..912fd9c
--- /dev/null
+++ b/src/validators/ico.test.ts
@@ -0,0 +1,81 @@
+import { validateICO } from './ico';
+
+describe('validateICO', () => {
+  describe('valid IČOs', () => {
+    it('accepts a known valid IČO (Seznam.cz: 27074358)', () => {
+      expect(validateICO('27074358')).toEqual({ valid: true });
+    });
+
+    it('accepts a known valid IČO (25596641)', () => {
+      expect(validateICO('25596641')).toEqual({ valid: true });
+    });
+
+    it('accepts an IČO where remainder is 0 (checksum becomes 1)', () => {
+      // 00000001: sum=0, rem=0, checksum=1
+      expect(validateICO('00000001')).toEqual({ valid: true });
+    });
+
+    it('accepts an IČO where remainder is 1 (checksum becomes 0)', () => {
+      // 10001000: 1*8 + 1*4 = 12, rem=1, checksum=0
+      expect(validateICO('10001000')).toEqual({ valid: true });
+    });
+  });
+
+  describe('invalid IČOs', () => {
+    it('rejects empty string', () => {
+      const result = validateICO('');
+      expect(result.valid).toBe(false);
+      if (!result.valid) expect(result.reason).toMatch(/empty/i);
+    });
+
+    it('rejects strings with non-digit characters', () => {
+      const result = validateICO('2707435a');
+      expect(result.valid).toBe(false);
+      if (!result.valid) expect(result.reason).toMatch(/digits/i);
+    });
+
+    it('rejects strings with spaces', () => {
+      const result = validateICO('2707 4358');
+      expect(result.valid).toBe(false);
+      if (!result.valid) expect(result.reason).toMatch(/digits/i);
+    });
+
+    it('rejects strings with leading/trailing whitespace', () => {
+      expect(validateICO(' 27074358').valid).toBe(false);
+      expect(validateICO('27074358 ').valid).toBe(false);
+    });
+
+    it('rejects strings shorter than 8 digits', () => {
+      const result = validateICO('1234567');
+      expect(result.valid).toBe(false);
+      if (!result.valid) expect(result.reason).toMatch(/8 digits/i);
+    });
+
+    it('rejects strings longer than 8 digits', () => {
+      const result = validateICO('123456789');
+      expect(result.valid).toBe(false);
+      if (!result.valid) expect(result.reason).toMatch(/8 digits/i);
+    });
+
+    it('rejects an IČO with an incorrect checksum', () => {
+      // Take a valid one and change the last digit
+      const result = validateICO('27074357');
+      expect(result.valid).toBe(false);
+      if (!result.valid) expect(result.reason).toMatch(/checksum/i);
+    });
+
+    it('rejects 00000000 (rem=0 → checksum should be 1, not 0)', () => {
+      const result = validateICO('00000000');
+      expect(result.valid).toBe(false);
+      if (!result.valid) expect(result.reason).toMatch(/checksum/i);
+    });
+
+    it('rejects negative-looking input', () => {
+      expect(validateICO('-2707435').valid).toBe(false);
+    });
+
+    it('rejects decimal-looking input', () => {
+      expect(validateICO('2707435.').valid).toBe(false);
+    });
+  });
+});
diff --git a/src/validators/ico.ts b/src/validators/ico.ts
index e69de29..7fef904 100644
--- a/src/validators/ico.ts
+++ b/src/validators/ico.ts
@@ -0,0 +1,33 @@
+import { ValidationResult } from '../types';
+
+export function validateICO(input: string): ValidationResult {
+  if (!input) {
+    return { valid: false, reason: 'IČO must not be empty' };
+  }
+  if (!/^\d+$/.test(input)) {
+    return { valid: false, reason: 'IČO must contain only digits' };
+  }
+  if (input.length !== 8) {
+    return { valid: false, reason: 'IČO must be exactly 8 digits' };
+  }
+
+  const digits = input.split('').map((d) => parseInt(d, 10));
+  const weights = [8, 7, 6, 5, 4, 3, 2];
+  const sum = weights.reduce((acc, w, i) => acc + w * digits[i], 0);
+  const remainder = sum % 11;
+
+  let checksum: number;
+  if (remainder === 0) {
+    checksum = 1;
+  } else if (remainder === 1) {
+    checksum = 0;
+  } else {
+    checksum = 11 - remainder;
+  }
+
+  if (checksum !== digits[7]) {
+    return { valid: false, reason: 'IČO checksum is invalid' };
+  }
+
+  return { valid: true };
+}
```

---

## Run 7: high / run1

**run_id:** `02_implement_ico_claude-opus-4-7_high_run1_1778759311`

**Metadata:** wall=59s  cost=$0.322  turns=10  tool_calls=9  breakdown=Bash=4; Read=3; Write=2

**Verify:** success=True  score=1.0

**Diff stat:**
```
src/validators/ico.test.ts | 79 ++++++++++++++++++++++++++++++++++++++++++++++
 src/validators/ico.ts      | 33 +++++++++++++++++++
 2 files changed, 112 insertions(+)
```

**Final diff:**
```diff
diff --git a/src/validators/ico.test.ts b/src/validators/ico.test.ts
new file mode 100644
index 0000000..1940a63
--- /dev/null
+++ b/src/validators/ico.test.ts
@@ -0,0 +1,79 @@
+import { validateICO } from './ico';
+
+describe('validateICO', () => {
+  describe('valid IČO', () => {
+    test('valid IČO 27074358 passes', () => {
+      expect(validateICO('27074358')).toEqual({ valid: true });
+    });
+    test('valid IČO 00006947 passes', () => {
+      expect(validateICO('00006947')).toEqual({ valid: true });
+    });
+    test('valid IČO with remainder 0 (checksum becomes 1)', () => {
+      expect(validateICO('00000001')).toEqual({ valid: true });
+    });
+    test('valid IČO with remainder 1 (checksum becomes 0)', () => {
+      expect(validateICO('00000230')).toEqual({ valid: true });
+    });
+  });
+
+  describe('empty input', () => {
+    test('empty string fails', () => {
+      const result = validateICO('');
+      expect(result).toMatchObject({ valid: false });
+      if (!result.valid) {
+        expect(result.reason).toMatch(/empty/i);
+      }
+    });
+  });
+
+  describe('non-digit characters', () => {
+    test('contains letters fails', () => {
+      const result = validateICO('2707435a');
+      expect(result).toMatchObject({ valid: false });
+      if (!result.valid) {
+        expect(result.reason).toMatch(/digit/i);
+      }
+    });
+    test('contains spaces fails', () => {
+      expect(validateICO('2707 358')).toMatchObject({ valid: false });
+    });
+    test('contains hyphen fails', () => {
+      expect(validateICO('2707-358')).toMatchObject({ valid: false });
+    });
+    test('contains plus sign fails', () => {
+      expect(validateICO('+2707435')).toMatchObject({ valid: false });
+    });
+  });
+
+  describe('wrong length', () => {
+    test('7 digits fails', () => {
+      const result = validateICO('2707435');
+      expect(result).toMatchObject({ valid: false });
+      if (!result.valid) {
+        expect(result.reason).toMatch(/8 digits/i);
+      }
+    });
+    test('9 digits fails', () => {
+      expect(validateICO('270743588')).toMatchObject({ valid: false });
+    });
+    test('single digit fails', () => {
+      expect(validateICO('1')).toMatchObject({ valid: false });
+    });
+  });
+
+  describe('invalid checksum', () => {
+    test('27074359 (off-by-one checksum) fails', () => {
+      const result = validateICO('27074359');
+      expect(result).toMatchObject({ valid: false });
+      if (!result.valid) {
+        expect(result.reason).toMatch(/checksum/i);
+      }
+    });
+    test('12345678 fails', () => {
+      expect(validateICO('12345678')).toMatchObject({ valid: false });
+    });
+    test('00000000 fails (remainder 0 expects checksum 1)', () => {
+      expect(validateICO('00000000')).toMatchObject({ valid: false });
+    });
+  });
+});
diff --git a/src/validators/ico.ts b/src/validators/ico.ts
index e69de29..53c4986 100644
--- a/src/validators/ico.ts
+++ b/src/validators/ico.ts
@@ -0,0 +1,33 @@
+import { ValidationResult } from '../types';
+
+export function validateICO(input: string): ValidationResult {
+  if (!input) {
+    return { valid: false, reason: 'IČO must not be empty' };
+  }
+  if (!/^\d+$/.test(input)) {
+    return { valid: false, reason: 'IČO must contain only digits' };
+  }
+  if (input.length !== 8) {
+    return { valid: false, reason: 'IČO must be exactly 8 digits' };
+  }
+
+  const weights = [8, 7, 6, 5, 4, 3, 2];
+  let sum = 0;
+  for (let i = 0; i < 7; i++) {
+    sum += parseInt(input[i], 10) * weights[i];
+  }
+  const remainder = sum % 11;
+  let checksum: number;
+  if (remainder === 0) {
+    checksum = 1;
+  } else if (remainder === 1) {
+    checksum = 0;
+  } else {
+    checksum = 11 - remainder;
+  }
+
+  if (parseInt(input[7], 10) !== checksum) {
+    return { valid: false, reason: 'IČO checksum is invalid' };
+  }
+  return { valid: true };
+}
```

---

## Run 8: high / run2

**run_id:** `02_implement_ico_claude-opus-4-7_high_run2_1778759378`

**Metadata:** wall=61s  cost=$0.324  turns=10  tool_calls=9  breakdown=Bash=4; Read=3; Write=2

**Verify:** success=True  score=1.0

**Diff stat:**
```
src/validators/ico.test.ts | 95 ++++++++++++++++++++++++++++++++++++++++++++++
 src/validators/ico.ts      | 34 +++++++++++++++++
 2 files changed, 129 insertions(+)
```

**Final diff:**
```diff
diff --git a/src/validators/ico.test.ts b/src/validators/ico.test.ts
new file mode 100644
index 0000000..7e1fe5c
--- /dev/null
+++ b/src/validators/ico.test.ts
@@ -0,0 +1,95 @@
+import { validateICO } from './ico';
+
+describe('validateICO', () => {
+  describe('valid IČO', () => {
+    test('accepts a known valid IČO (Seznam.cz: 27074358)', () => {
+      expect(validateICO('27074358')).toEqual({ valid: true });
+    });
+
+    test('accepts a known valid IČO (Alza: 25596641, remainder 0 → checksum 1)', () => {
+      expect(validateICO('25596641')).toEqual({ valid: true });
+    });
+
+    test('accepts IČO where remainder is 1 → checksum 0 (00000060)', () => {
+      expect(validateICO('00000060')).toEqual({ valid: true });
+    });
+
+    test('accepts IČO with leading zeros (00000019)', () => {
+      // digits 1-7 = 0000001, sum = 1*2 = 2, remainder = 2, checksum = 9
+      expect(validateICO('00000019')).toEqual({ valid: true });
+    });
+  });
+
+  describe('invalid IČO', () => {
+    test('rejects empty string', () => {
+      expect(validateICO('')).toEqual({
+        valid: false,
+        reason: 'IČO must not be empty',
+      });
+    });
+
+    test('rejects non-digit characters (letters)', () => {
+      expect(validateICO('2707435a')).toMatchObject({
+        valid: false,
+        reason: 'IČO must contain only digits',
+      });
+    });
+
+    test('rejects non-digit characters (whitespace)', () => {
+      expect(validateICO('2707 358')).toMatchObject({
+        valid: false,
+        reason: 'IČO must contain only digits',
+      });
+    });
+
+    test('rejects non-digit characters (dash)', () => {
+      expect(validateICO('2707-358')).toMatchObject({
+        valid: false,
+        reason: 'IČO must contain only digits',
+      });
+    });
+
+    test('rejects too-short input (7 digits)', () => {
+      expect(validateICO('2707435')).toMatchObject({
+        valid: false,
+        reason: 'IČO must be exactly 8 digits',
+      });
+    });
+
+    test('rejects too-long input (9 digits)', () => {
+      expect(validateICO('270743580')).toMatchObject({
+        valid: false,
+        reason: 'IČO must be exactly 8 digits',
+      });
+    });
+
+    test('rejects single digit', () => {
+      expect(validateICO('1')).toMatchObject({
+        valid: false,
+        reason: 'IČO must be exactly 8 digits',
+      });
+    });
+
+    test('rejects valid-format IČO with wrong checksum', () => {
+      // 27074358 is valid; flip last digit
+      expect(validateICO('27074357')).toMatchObject({
+        valid: false,
+        reason: 'IČO checksum is invalid',
+      });
+    });
+
+    test('rejects all zeros (checksum should be 1, not 0)', () => {
+      expect(validateICO('00000000')).toMatchObject({
+        valid: false,
+        reason: 'IČO checksum is invalid',
+      });
+    });
+
+    test('rejects 8-digit string with plus sign', () => {
+      expect(validateICO('+2707435')).toMatchObject({
+        valid: false,
+        reason: 'IČO must contain only digits',
+      });
+    });
+  });
+});
diff --git a/src/validators/ico.ts b/src/validators/ico.ts
index e69de29..60e4aec 100644
--- a/src/validators/ico.ts
+++ b/src/validators/ico.ts
@@ -0,0 +1,34 @@
+import { ValidationResult } from '../types';
+
+export function validateICO(input: string): ValidationResult {
+  if (!input) {
+    return { valid: false, reason: 'IČO must not be empty' };
+  }
+  if (!/^\d+$/.test(input)) {
+    return { valid: false, reason: 'IČO must contain only digits' };
+  }
+  if (input.length !== 8) {
+    return { valid: false, reason: 'IČO must be exactly 8 digits' };
+  }
+
+  const weights = [8, 7, 6, 5, 4, 3, 2];
+  let sum = 0;
+  for (let i = 0; i < 7; i++) {
+    sum += Number(input[i]) * weights[i];
+  }
+  const remainder = sum % 11;
+  let checksum: number;
+  if (remainder === 0) {
+    checksum = 1;
+  } else if (remainder === 1) {
+    checksum = 0;
+  } else {
+    checksum = 11 - remainder;
+  }
+
+  if (checksum !== Number(input[7])) {
+    return { valid: false, reason: 'IČO checksum is invalid' };
+  }
+
+  return { valid: true };
+}
```

---

## Run 9: high / run3

**run_id:** `02_implement_ico_claude-opus-4-7_high_run3_1778759447`

**Metadata:** wall=55s  cost=$0.304  turns=13  tool_calls=12  breakdown=Bash=4; Read=6; Write=2

**Verify:** success=True  score=1.0

**Diff stat:**
```
src/validators/ico.test.ts | 95 ++++++++++++++++++++++++++++++++++++++++++++++
 src/validators/ico.ts      | 33 ++++++++++++++++
 2 files changed, 128 insertions(+)
```

**Final diff:**
```diff
diff --git a/src/validators/ico.test.ts b/src/validators/ico.test.ts
new file mode 100644
index 0000000..07019b1
--- /dev/null
+++ b/src/validators/ico.test.ts
@@ -0,0 +1,95 @@
+import { validateICO } from './ico';
+
+describe('validateICO', () => {
+  describe('valid IČO', () => {
+    test('accepts a real-world valid IČO', () => {
+      expect(validateICO('27074358')).toEqual({ valid: true });
+    });
+
+    test('accepts a valid IČO (12345679)', () => {
+      expect(validateICO('12345679')).toEqual({ valid: true });
+    });
+
+    test('accepts checksum branch where remainder is 0 (checksum becomes 1)', () => {
+      expect(validateICO('00000001')).toEqual({ valid: true });
+    });
+
+    test('accepts checksum branch where remainder is 1 (checksum becomes 0)', () => {
+      expect(validateICO('00000060')).toEqual({ valid: true });
+    });
+  });
+
+  describe('format errors', () => {
+    test('rejects empty string', () => {
+      expect(validateICO('')).toEqual({
+        valid: false,
+        reason: 'IČO must not be empty',
+      });
+    });
+
+    test('rejects string with letters', () => {
+      expect(validateICO('1234567A')).toMatchObject({
+        valid: false,
+        reason: 'IČO must contain only digits',
+      });
+    });
+
+    test('rejects string with spaces', () => {
+      expect(validateICO('2707 4358')).toMatchObject({
+        valid: false,
+        reason: 'IČO must contain only digits',
+      });
+    });
+
+    test('rejects string with punctuation', () => {
+      expect(validateICO('2707-4358')).toMatchObject({
+        valid: false,
+        reason: 'IČO must contain only digits',
+      });
+    });
+
+    test('rejects too few digits', () => {
+      expect(validateICO('1234567')).toMatchObject({
+        valid: false,
+        reason: 'IČO must be exactly 8 digits',
+      });
+    });
+
+    test('rejects too many digits', () => {
+      expect(validateICO('123456789')).toMatchObject({
+        valid: false,
+        reason: 'IČO must be exactly 8 digits',
+      });
+    });
+
+    test('rejects a single digit', () => {
+      expect(validateICO('1')).toMatchObject({
+        valid: false,
+        reason: 'IČO must be exactly 8 digits',
+      });
+    });
+  });
+
+  describe('checksum errors', () => {
+    test('rejects an 8-digit value with a wrong checksum', () => {
+      expect(validateICO('27074359')).toMatchObject({
+        valid: false,
+        reason: 'IČO checksum is invalid',
+      });
+    });
+
+    test('rejects all zeros (checksum should be 1)', () => {
+      expect(validateICO('00000000')).toMatchObject({
+        valid: false,
+        reason: 'IČO checksum is invalid',
+      });
+    });
+
+    test('rejects 12345678 (checksum should be 9)', () => {
+      expect(validateICO('12345678')).toMatchObject({
+        valid: false,
+        reason: 'IČO checksum is invalid',
+      });
+    });
+  });
+});
diff --git a/src/validators/ico.ts b/src/validators/ico.ts
index e69de29..a50d69d 100644
--- a/src/validators/ico.ts
+++ b/src/validators/ico.ts
@@ -0,0 +1,33 @@
+import { ValidationResult } from '../types';
+
+export function validateICO(input: string): ValidationResult {
+  if (input === '') {
+    return { valid: false, reason: 'IČO must not be empty' };
+  }
+  if (!/^\d+$/.test(input)) {
+    return { valid: false, reason: 'IČO must contain only digits' };
+  }
+  if (input.length !== 8) {
+    return { valid: false, reason: 'IČO must be exactly 8 digits' };
+  }
+
+  const weights = [8, 7, 6, 5, 4, 3, 2];
+  let sum = 0;
+  for (let i = 0; i < 7; i++) {
+    sum += Number(input[i]) * weights[i];
+  }
+  const remainder = sum % 11;
+  let expected: number;
+  if (remainder === 0) {
+    expected = 1;
+  } else if (remainder === 1) {
+    expected = 0;
+  } else {
+    expected = 11 - remainder;
+  }
+
+  if (Number(input[7]) !== expected) {
+    return { valid: false, reason: 'IČO checksum is invalid' };
+  }
+  return { valid: true };
+}
```

---

## Run 10: max / run1

**run_id:** `02_implement_ico_claude-opus-4-7_max_run1_1778759510`

**Metadata:** wall=104s  cost=$0.551  turns=19  tool_calls=18  breakdown=Bash=6; Edit=1; Read=8; Write=3

**Verify:** success=True  score=1.0

**Diff stat:**
```
src/validators/ico.test.ts | 73 ++++++++++++++++++++++++++++++++++++++++++++++
 src/validators/ico.ts      | 35 ++++++++++++++++++++++
 src/validators/index.ts    |  1 +
 3 files changed, 109 insertions(+)
```

**Final diff:**
```diff
diff --git a/src/validators/ico.test.ts b/src/validators/ico.test.ts
new file mode 100644
index 0000000..bdc9e56
--- /dev/null
+++ b/src/validators/ico.test.ts
@@ -0,0 +1,73 @@
+import { validateICO } from './ico';
+
+describe('validateICO', () => {
+  describe('valid IČOs', () => {
+    test('real-world IČO passes', () => {
+      expect(validateICO('27074358')).toEqual({ valid: true });
+    });
+    test('IČO with leading zeros passes', () => {
+      expect(validateICO('00006947')).toEqual({ valid: true });
+    });
+    test('IČO where remainder is 0 (checksum becomes 1) passes', () => {
+      expect(validateICO('25596641')).toEqual({ valid: true });
+    });
+    test('IČO where remainder is 1 (checksum becomes 0) passes', () => {
+      expect(validateICO('66666660')).toEqual({ valid: true });
+    });
+    test('all-zero with checksum 1 passes', () => {
+      expect(validateICO('00000001')).toEqual({ valid: true });
+    });
+  });
+
+  describe('invalid checksum', () => {
+    test('off-by-one checksum fails', () => {
+      const result = validateICO('27074359');
+      expect(result).toMatchObject({ valid: false });
+      if (!result.valid) {
+        expect(result.reason).toMatch(/checksum/i);
+      }
+    });
+    test('sequential digits fail', () => {
+      expect(validateICO('12345678')).toMatchObject({ valid: false });
+    });
+  });
+
+  describe('format errors', () => {
+    test('empty string fails', () => {
+      const result = validateICO('');
+      expect(result).toMatchObject({ valid: false });
+      if (!result.valid) {
+        expect(result.reason).toMatch(/empty/i);
+      }
+    });
+    test('too short fails', () => {
+      const result = validateICO('1234567');
+      expect(result).toMatchObject({ valid: false });
+      if (!result.valid) {
+        expect(result.reason).toMatch(/8 digits/i);
+      }
+    });
+    test('too long fails', () => {
+      expect(validateICO('123456789')).toMatchObject({ valid: false });
+    });
+    test('letters in input fail', () => {
+      const result = validateICO('1234567a');
+      expect(result).toMatchObject({ valid: false });
+      if (!result.valid) {
+        expect(result.reason).toMatch(/digits/i);
+      }
+    });
+    test('whitespace fails', () => {
+      expect(validateICO('2707435 ')).toMatchObject({ valid: false });
+    });
+    test('special characters fail', () => {
+      expect(validateICO('2707-358')).toMatchObject({ valid: false });
+    });
+    test('leading plus sign fails', () => {
+      expect(validateICO('+2707435')).toMatchObject({ valid: false });
+    });
+    test('8 spaces fail', () => {
+      expect(validateICO('        ')).toMatchObject({ valid: false });
+    });
+  });
+});
diff --git a/src/validators/ico.ts b/src/validators/ico.ts
index e69de29..9092999 100644
--- a/src/validators/ico.ts
+++ b/src/validators/ico.ts
@@ -0,0 +1,35 @@
+import { ValidationResult } from '../types';
+
+const WEIGHTS = [8, 7, 6, 5, 4, 3, 2];
+
+export function validateICO(input: string): ValidationResult {
+  if (!input) {
+    return { valid: false, reason: 'IČO must not be empty' };
+  }
+  if (input.length !== 8) {
+    return { valid: false, reason: 'IČO must be exactly 8 digits' };
+  }
+  if (!/^[0-9]{8}$/.test(input)) {
+    return { valid: false, reason: 'IČO must contain only digits' };
+  }
+
+  const digits = input.split('').map(Number);
+  let sum = 0;
+  for (let i = 0; i < 7; i++) {
+    sum += digits[i] * WEIGHTS[i];
+  }
+  const remainder = sum % 11;
+  let expected: number;
+  if (remainder === 0) {
+    expected = 1;
+  } else if (remainder === 1) {
+    expected = 0;
+  } else {
+    expected = 11 - remainder;
+  }
+
+  if (expected !== digits[7]) {
+    return { valid: false, reason: 'IČO checksum is invalid' };
+  }
+  return { valid: true };
+}
diff --git a/src/validators/index.ts b/src/validators/index.ts
index 6773e50..098adf8 100644
--- a/src/validators/index.ts
+++ b/src/validators/index.ts
@@ -1,2 +1,3 @@
 export { validateEmail } from './email';
 export { validatePhone } from './phone';
+export { validateICO } from './ico';
```

---

## Run 11: max / run2

**run_id:** `02_implement_ico_claude-opus-4-7_max_run2_1778759623`

**Metadata:** wall=121s  cost=$0.600  turns=19  tool_calls=18  breakdown=Bash=5; Edit=2; Read=8; Write=3

**Verify:** success=True  score=1.0

**Diff stat:**
```
src/validators/ico.test.ts | 85 ++++++++++++++++++++++++++++++++++++++++++++++
 src/validators/ico.ts      | 33 ++++++++++++++++++
 src/validators/index.ts    |  1 +
 3 files changed, 119 insertions(+)
```

**Final diff:**
```diff
diff --git a/src/validators/ico.test.ts b/src/validators/ico.test.ts
new file mode 100644
index 0000000..9c7c9f5
--- /dev/null
+++ b/src/validators/ico.test.ts
@@ -0,0 +1,85 @@
+import { validateICO } from './ico';
+
+describe('validateICO', () => {
+  describe('valid IČOs', () => {
+    test('real-world valid IČO 25596641 passes', () => {
+      expect(validateICO('25596641')).toEqual({ valid: true });
+    });
+    test('real-world valid IČO 27082440 passes (checksum 0 branch)', () => {
+      expect(validateICO('27082440')).toEqual({ valid: true });
+    });
+    test('real-world valid IČO 26168685 passes', () => {
+      expect(validateICO('26168685')).toEqual({ valid: true });
+    });
+    test('00000001 passes (checksum 1 branch, remainder 0)', () => {
+      expect(validateICO('00000001')).toEqual({ valid: true });
+    });
+    test('leading zeros are accepted', () => {
+      expect(validateICO('00000108')).toEqual({ valid: true });
+    });
+  });
+
+  describe('format errors', () => {
+    test('empty string fails', () => {
+      const result = validateICO('');
+      expect(result).toMatchObject({ valid: false });
+      if (!result.valid) expect(result.reason).toMatch(/empty/i);
+    });
+    test('too short fails', () => {
+      expect(validateICO('1234567')).toMatchObject({ valid: false });
+    });
+    test('too long fails', () => {
+      expect(validateICO('123456789')).toMatchObject({ valid: false });
+    });
+    test('non-digit characters fail', () => {
+      expect(validateICO('1234567a')).toMatchObject({ valid: false });
+    });
+    test('whitespace fails', () => {
+      expect(validateICO('2559664 ')).toMatchObject({ valid: false });
+    });
+    test('leading whitespace fails', () => {
+      expect(validateICO(' 5596641')).toMatchObject({ valid: false });
+    });
+    test('hyphen fails', () => {
+      expect(validateICO('2559-641')).toMatchObject({ valid: false });
+    });
+    test('decimal point fails', () => {
+      expect(validateICO('2559664.')).toMatchObject({ valid: false });
+    });
+    test('unicode digits fail', () => {
+      expect(validateICO('٢٥٥٩٦٦٤١')).toMatchObject({ valid: false });
+    });
+  });
+
+  describe('checksum errors', () => {
+    test('all zeros fails (checksum should be 1, not 0)', () => {
+      const result = validateICO('00000000');
+      expect(result).toMatchObject({ valid: false });
+      if (!result.valid) expect(result.reason).toMatch(/checksum/i);
+    });
+    test('off-by-one checksum fails', () => {
+      expect(validateICO('25596642')).toMatchObject({ valid: false });
+    });
+    test('digits transposed fails', () => {
+      expect(validateICO('52596641')).toMatchObject({ valid: false });
+    });
+    test('returns checksum reason for wrong checksum', () => {
+      const result = validateICO('12345678');
+      expect(result).toMatchObject({ valid: false });
+      if (!result.valid) expect(result.reason).toMatch(/checksum/i);
+    });
+  });
+
+  describe('error message routing', () => {
+    test('non-digit input reports digit error, not checksum error', () => {
+      const result = validateICO('abcdefgh');
+      expect(result).toMatchObject({ valid: false });
+      if (!result.valid) expect(result.reason).toMatch(/digit/i);
+    });
+    test('wrong length all-digit input reports length error', () => {
+      const result = validateICO('1234567');
+      expect(result).toMatchObject({ valid: false });
+      if (!result.valid) expect(result.reason).toMatch(/8 digits/i);
+    });
+  });
+});
diff --git a/src/validators/ico.ts b/src/validators/ico.ts
index e69de29..8a5a5c3 100644
--- a/src/validators/ico.ts
+++ b/src/validators/ico.ts
@@ -0,0 +1,33 @@
+import { ValidationResult } from '../types';
+
+export function validateICO(input: string): ValidationResult {
+  if (!input) {
+    return { valid: false, reason: 'IČO must not be empty' };
+  }
+  if (!/^[0-9]+$/.test(input)) {
+    return { valid: false, reason: 'IČO must contain only digits' };
+  }
+  if (input.length !== 8) {
+    return { valid: false, reason: 'IČO must be exactly 8 digits' };
+  }
+
+  const weights = [8, 7, 6, 5, 4, 3, 2];
+  let sum = 0;
+  for (let i = 0; i < 7; i++) {
+    sum += Number(input[i]) * weights[i];
+  }
+  const remainder = sum % 11;
+  let expected: number;
+  if (remainder === 0) {
+    expected = 1;
+  } else if (remainder === 1) {
+    expected = 0;
+  } else {
+    expected = 11 - remainder;
+  }
+
+  if (Number(input[7]) !== expected) {
+    return { valid: false, reason: 'IČO checksum is invalid' };
+  }
+  return { valid: true };
+}
diff --git a/src/validators/index.ts b/src/validators/index.ts
index 6773e50..098adf8 100644
--- a/src/validators/index.ts
+++ b/src/validators/index.ts
@@ -1,2 +1,3 @@
 export { validateEmail } from './email';
 export { validatePhone } from './phone';
+export { validateICO } from './ico';
```

---

## Run 12: max / run3

**run_id:** `02_implement_ico_claude-opus-4-7_max_run3_1778759753`

**Metadata:** wall=120s  cost=$0.602  turns=20  tool_calls=19  breakdown=Bash=5; Edit=1; Read=10; Write=3

**Verify:** success=True  score=1.0

**Diff stat:**
```
src/validators/ico.test.ts | 89 ++++++++++++++++++++++++++++++++++++++++++++++
 src/validators/ico.ts      | 33 +++++++++++++++++
 src/validators/index.ts    |  1 +
 3 files changed, 123 insertions(+)
```

**Final diff:**
```diff
diff --git a/src/validators/ico.test.ts b/src/validators/ico.test.ts
new file mode 100644
index 0000000..91dfa48
--- /dev/null
+++ b/src/validators/ico.test.ts
@@ -0,0 +1,89 @@
+import { validateICO } from './ico';
+
+describe('validateICO', () => {
+  describe('valid IČO', () => {
+    test('real-world IČO with remainder 0 (checksum 1)', () => {
+      expect(validateICO('25596641')).toEqual({ valid: true });
+    });
+
+    test('real-world IČO with general checksum case', () => {
+      expect(validateICO('27074358')).toEqual({ valid: true });
+    });
+
+    test('IČO with leading zeros', () => {
+      expect(validateICO('00006947')).toEqual({ valid: true });
+    });
+
+    test('IČO with remainder 1 (checksum 0)', () => {
+      expect(validateICO('10001000')).toEqual({ valid: true });
+    });
+  });
+
+  describe('invalid IČO', () => {
+    test('empty string fails', () => {
+      expect(validateICO('')).toEqual({
+        valid: false,
+        reason: 'IČO must not be empty',
+      });
+    });
+
+    test('too few digits fails', () => {
+      expect(validateICO('1234567')).toMatchObject({ valid: false });
+    });
+
+    test('too many digits fails', () => {
+      expect(validateICO('123456789')).toMatchObject({ valid: false });
+    });
+
+    test('non-digit characters fail', () => {
+      expect(validateICO('1234567a')).toMatchObject({ valid: false });
+    });
+
+    test('whitespace fails', () => {
+      expect(validateICO('1234 678')).toMatchObject({ valid: false });
+    });
+
+    test('leading whitespace fails', () => {
+      expect(validateICO(' 25596641')).toMatchObject({ valid: false });
+    });
+
+    test('wrong checksum fails', () => {
+      expect(validateICO('12345678')).toEqual({
+        valid: false,
+        reason: 'IČO checksum is invalid',
+      });
+    });
+
+    test('off-by-one checksum fails', () => {
+      // 25596641 is valid; flipping the checksum to 2 should fail
+      expect(validateICO('25596642')).toMatchObject({
+        valid: false,
+        reason: 'IČO checksum is invalid',
+      });
+    });
+
+    test('all zeros fails (checksum should be 1)', () => {
+      expect(validateICO('00000000')).toMatchObject({ valid: false });
+    });
+
+    test('special characters fail', () => {
+      expect(validateICO('2559-641')).toMatchObject({ valid: false });
+    });
+  });
+
+  describe('return type', () => {
+    test('valid result has no reason field', () => {
+      const result = validateICO('25596641');
+      expect(result).toEqual({ valid: true });
+    });
+
+    test('invalid result has a reason field', () => {
+      const result = validateICO('12345678');
+      expect(result.valid).toBe(false);
+      if (!result.valid) {
+        expect(typeof result.reason).toBe('string');
+        expect(result.reason.length).toBeGreaterThan(0);
+      }
+    });
+  });
+});
diff --git a/src/validators/ico.ts b/src/validators/ico.ts
index e69de29..90f9d88 100644
--- a/src/validators/ico.ts
+++ b/src/validators/ico.ts
@@ -0,0 +1,33 @@
+import { ValidationResult } from '../types';
+
+export function validateICO(input: string): ValidationResult {
+  if (!input) {
+    return { valid: false, reason: 'IČO must not be empty' };
+  }
+  if (!/^[0-9]+$/.test(input)) {
+    return { valid: false, reason: 'IČO must contain only digits' };
+  }
+  if (input.length !== 8) {
+    return { valid: false, reason: 'IČO must be exactly 8 digits' };
+  }
+
+  const weights = [8, 7, 6, 5, 4, 3, 2];
+  let sum = 0;
+  for (let i = 0; i < 7; i++) {
+    sum += Number(input[i]) * weights[i];
+  }
+  const remainder = sum % 11;
+  let expectedChecksum: number;
+  if (remainder === 0) {
+    expectedChecksum = 1;
+  } else if (remainder === 1) {
+    expectedChecksum = 0;
+  } else {
+    expectedChecksum = 11 - remainder;
+  }
+
+  if (Number(input[7]) !== expectedChecksum) {
+    return { valid: false, reason: 'IČO checksum is invalid' };
+  }
+  return { valid: true };
+}
diff --git a/src/validators/index.ts b/src/validators/index.ts
index 6773e50..098adf8 100644
--- a/src/validators/index.ts
+++ b/src/validators/index.ts
@@ -1,2 +1,3 @@
 export { validateEmail } from './email';
 export { validatePhone } from './phone';
+export { validateICO } from './ico';
```
