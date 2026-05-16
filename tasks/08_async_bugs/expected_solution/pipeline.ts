// Data processing pipeline — fixed version

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

// FIX 1: Added missing await
export async function processSingle(id: number): Promise<ProcessedRecord> {
  const record = await fetchRecord(id);  // FIX: added await
  return processRecord(record);
}

// FIX 2: Use Promise.all for parallel processing
export async function processBatch(ids: number[]): Promise<ProcessedRecord[]> {
  return Promise.all(
    ids.map(async id => {
      const record = await fetchRecord(id);
      return processRecord(record);
    })
  );
}

// FIX 3: Re-throw error instead of swallowing it
export async function safeProcess(id: number): Promise<ProcessedRecord | undefined> {
  try {
    const record = await fetchRecord(id);
    if (record.value > 1000) {
      throw new Error(`Value too large: ${record.value}`);
    }
    return processRecord(record);
  } catch (err) {
    console.error('Processing failed:', err);
    throw err;  // FIX: re-throw instead of returning undefined
  }
}

// FIX 4: Use a queue/mutex pattern to avoid race condition
let counter = 0;
let lock: Promise<void> = Promise.resolve();

export async function incrementAndGet(): Promise<number> {
  lock = lock.then(async () => {
    await new Promise(resolve => setTimeout(resolve, 1));
    counter = counter + 1;
  });
  await lock;
  return counter;
}

// FIX 5: Return promise array so callers can handle errors
export function fireAndForget(ids: number[]): void {
  ids.forEach(id => {
    fetchRecord(id)
      .then(record => processRecord(record))
      .catch(err => console.error(`Failed to process id ${id}:`, err));  // FIX: handle rejection
  });
}
