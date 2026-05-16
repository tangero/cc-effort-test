import { processSingle, processBatch, safeProcess, incrementAndGet } from './pipeline';

describe('Async correctness', () => {
  test('processSingle returns correct result (Bug 1: missing await)', async () => {
    const result = await processSingle(5);
    // id=5, value=50, result=100
    expect(result.id).toBe(5);
    expect(result.result).toBe(100);
  });

  test('processBatch runs in parallel (Bug 2: sequential)', async () => {
    const ids = [1, 2, 3, 4, 5];
    const start = Date.now();
    await processBatch(ids);
    const elapsed = Date.now() - start;
    // Sequential would take ~75ms (5 * 15ms), parallel should take ~15ms
    expect(elapsed).toBeLessThan(50);
  });

  test('safeProcess propagates errors (Bug 3: swallowed error)', async () => {
    // id=200, value=2000 > 1000 — should throw
    // With bug fix, should either throw or return a rejected promise
    await expect(safeProcess(200)).rejects.toThrow();
  });

  test('incrementAndGet is race-condition free (Bug 4)', async () => {
    // Reset counter by running sequentially first
    // Then run 5 concurrent calls — final counter should be 5 more than start
    const start = 0;
    // @ts-ignore — access internal counter for test
    (global as any).__counter_reset = true;

    const promises = Array.from({ length: 5 }, () => incrementAndGet());
    const results = await Promise.all(promises);
    // All results should be unique (no two calls returned same value)
    const unique = new Set(results);
    expect(unique.size).toBe(5);
  });

  test('processBatch results have correct values (Bug 1+2 combined)', async () => {
    const results = await processBatch([1, 2, 3]);
    // id=1: value=10, result=20; id=2: value=20, result=40; id=3: value=30, result=60
    const sorted = results.sort((a: {id: number}, b: {id: number}) => a.id - b.id);
    expect(sorted[0].result).toBe(20);
    expect(sorted[1].result).toBe(40);
    expect(sorted[2].result).toBe(60);
  });
});
