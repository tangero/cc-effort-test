let nextSequence = 0;

export function resetSequence(): void {
  nextSequence = 0;
}

export async function allocateSequence(label: string): Promise<{ label: string; sequence: number }> {
  const reserved = nextSequence;
  await new Promise(resolve => setTimeout(resolve, Math.floor(Math.random() * 3)));
  nextSequence = reserved + 1;
  return { label, sequence: nextSequence };
}

export async function allocateBatch(labels: string[]): Promise<Array<{ label: string; sequence: number }>> {
  return Promise.all(labels.map(label => allocateSequence(label)));
}
