let nextSequence = 0;
let queue: Promise<void> = Promise.resolve();

export function resetSequence(): void {
  nextSequence = 0;
  queue = Promise.resolve();
}

export async function allocateSequence(label: string): Promise<{ label: string; sequence: number }> {
  let allocated = 0;
  const current = queue.then(async () => {
    await new Promise(resolve => setTimeout(resolve, Math.floor(Math.random() * 3)));
    nextSequence += 1;
    allocated = nextSequence;
  });
  queue = current.catch(() => undefined);
  await current;
  return { label, sequence: allocated };
}

export async function allocateBatch(labels: string[]): Promise<Array<{ label: string; sequence: number }>> {
  return Promise.all(labels.map(label => allocateSequence(label)));
}
