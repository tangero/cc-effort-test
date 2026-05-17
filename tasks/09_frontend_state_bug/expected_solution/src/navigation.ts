export type NavigationType = 'POP' | 'PUSH' | 'REPLACE';

export interface RouterSnapshot {
  path: string;
  navigationType: NavigationType;
}

export interface Router {
  getSnapshot(): RouterSnapshot;
  subscribe(listener: () => void): () => void;
  navigate(path: string, navigationType: NavigationType): void;
}

export class MemoryRouter implements Router {
  private snapshot: RouterSnapshot;
  private listeners = new Set<() => void>();

  constructor(initial: RouterSnapshot = { path: '/', navigationType: 'POP' }) {
    this.snapshot = initial;
  }

  getSnapshot(): RouterSnapshot {
    return this.snapshot;
  }

  subscribe(listener: () => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  navigate(path: string, navigationType: NavigationType): void {
    this.snapshot = { path, navigationType };
    for (const listener of this.listeners) listener();
  }
}

export type AnalyticsEvent = { path: string; navigationType: NavigationType };

export function createNavigationAnalytics(
  router: Router,
  send: (event: AnalyticsEvent) => void
): { flush(): void; dispose(): void } {
  const flush = () => {
    const snapshot = router.getSnapshot();
    send({ path: snapshot.path, navigationType: snapshot.navigationType });
  };

  const unsubscribe = router.subscribe(flush);
  return { flush, dispose: unsubscribe };
}
