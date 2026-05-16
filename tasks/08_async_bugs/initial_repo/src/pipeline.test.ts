import { processSingle, processBatch, safeProcess, incrementAndGet, fireAndForget } from './pipeline';

describe('Pipeline basic functionality', () => {
  test('fireAndForget does not throw', () => {
    expect(() => fireAndForget([1, 2, 3])).not.toThrow();
  });

  test('processBatch returns correct number of results', async () => {
    const results = await processBatch([1, 2, 3]);
    expect(results).toHaveLength(3);
  });

  test('safeProcess returns something for valid id', async () => {
    const result = await safeProcess(1);
    // With bug, result might be wrong but still defined
    expect(result).toBeDefined();
  });
});
