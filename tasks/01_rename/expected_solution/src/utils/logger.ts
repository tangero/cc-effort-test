/**
 * Tiny structured logger used by the service layer. Emits one JSON line
 * per event onto a configurable stream (defaults to stderr).
 */
type LogContext = Record<string, unknown>;

let stream: NodeJS.WriteStream = process.stderr;

export function setLogStream(s: NodeJS.WriteStream): void {
  stream = s;
}

/**
 * Log an event with arbitrary structured context. Commonly the context
 * carries a accountId field so log lines can be filtered per user.
 */
export function logEvent(event: string, context: LogContext = {}): void {
  if (process.env.NODE_ENV === 'test') {
    return;
  }
  const payload = { event, timestamp: new Date().toISOString(), ...context };
  stream.write(JSON.stringify(payload) + '\n');
}
