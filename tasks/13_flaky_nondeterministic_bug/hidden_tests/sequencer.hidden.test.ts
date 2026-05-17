import { allocateBatch, resetSequence } from '../sequencer';

describe('deterministic sequence allocation under concurrency', () => {
  test('concurrent allocations produce unique contiguous sequences repeatedly', async () => {
    for (let run = 0; run < 40; run++) {
      resetSequence();
      const labels = Array.from({ length: 25 }, (_, i) => `job-${i}`);
      const result = await allocateBatch(labels);
      const sequences = result.map(item => item.sequence).sort((a, b) => a - b);

      expect(sequences).toEqual(Array.from({ length: 25 }, (_, i) => i + 1));
    }
  });

  test('result order remains tied to input labels', async () => {
    resetSequence();
    const result = await allocateBatch(['first', 'second', 'third']);
    expect(result.map(item => item.label)).toEqual(['first', 'second', 'third']);
  });
});
