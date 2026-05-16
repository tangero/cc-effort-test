// Data processing pipeline with intentional async bugs

export interface Record {
  id: number;
  value: number;
}

export interface ProcessedRecord {
  id: number;
  result: number;
  processedAt: number;
}

// Simulates an async fetch
async function fetchRecord(id: number): Promise<Record> {
  return new Promise(resolve => {
    setTimeout(() => resolve({ id, value: id * 10 }), 10);
  });
}

// Simulates async processing
async function processRecord(record: Record): Promise<ProcessedRecord> {
  return new Promise(resolve => {
    setTimeout(() => resolve({
      id: record.id,
      result: record.value * 2,
      processedAt: Date.now()
    }), 5);
  });
}

// BUG 1: Missing await — fetchRecord result is a Promise, not a Record
// processRecord receives a Promise object instead of a Record
export async function processSingle(id: number): Promise<ProcessedRecord> {
  const record = fetchRecord(id);  // BUG: missing await
  return processRecord(record as any);
}

// BUG 2: Sequential instead of parallel — should use Promise.all
// This processes 10 records one-by-one instead of in parallel, 10x slower
export async function processBatch(ids: number[]): Promise<ProcessedRecord[]> {
  const results: ProcessedRecord[] = [];
  for (const id of ids) {
    const record = await fetchRecord(id);
    const processed = await processRecord(record);
    results.push(processed);
  }
  return results;
}

// BUG 3: Error swallowed — catch block returns undefined silently
// Caller gets undefined instead of an error being propagated
export async function safeProcess(id: number): Promise<ProcessedRecord | undefined> {
  try {
    const record = await fetchRecord(id);
    if (record.value > 1000) {
      throw new Error(`Value too large: ${record.value}`);
    }
    return processRecord(record);
  } catch (err) {
    console.error('Processing failed:', err);
    // BUG: returns undefined instead of re-throwing or returning a meaningful error
  }
}

// BUG 4: Race condition — shared mutable state modified concurrently
// counter will have wrong value when called concurrently
let counter = 0;

export async function incrementAndGet(): Promise<number> {
  const current = counter;
  await new Promise(resolve => setTimeout(resolve, 1)); // simulate async work
  counter = current + 1;  // BUG: stale read — another call may have updated counter
  return counter;
}

// BUG 5: Promise created but never awaited, errors are silently lost
export function fireAndForget(ids: number[]): void {
  ids.forEach(id => {
    // BUG: Promise rejection is unhandled — if fetchRecord fails, error is lost
    fetchRecord(id).then(record => processRecord(record));
  });
}
