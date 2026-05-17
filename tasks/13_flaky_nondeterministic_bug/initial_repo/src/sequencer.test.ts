import { allocateBatch, resetSequence } from './sequencer';

test('allocates increasing values when called as a small batch', async () => {
  resetSequence();
  const result = await allocateBatch(['a']);
  expect(result).toEqual([{ label: 'a', sequence: 1 }]);
});

test('returns one result per label', async () => {
  resetSequence();
  await expect(allocateBatch(['a', 'b', 'c'])).resolves.toHaveLength(3);
});
