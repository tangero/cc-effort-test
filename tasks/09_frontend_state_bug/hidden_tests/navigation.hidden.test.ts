import { createNavigationAnalytics, MemoryRouter } from '../navigation';

describe('navigation analytics stale state', () => {
  test('subscription callback sees latest navigation type', () => {
    const router = new MemoryRouter({ path: '/', navigationType: 'POP' });
    const events: unknown[] = [];
    createNavigationAnalytics(router, event => events.push(event));

    router.navigate('/projects', 'PUSH');
    router.navigate('/projects/42', 'REPLACE');

    expect(events).toEqual([
      { path: '/projects', navigationType: 'PUSH' },
      { path: '/projects/42', navigationType: 'REPLACE' },
    ]);
  });

  test('manual flush reads the current snapshot after several transitions', () => {
    const router = new MemoryRouter({ path: '/', navigationType: 'POP' });
    const events: unknown[] = [];
    const analytics = createNavigationAnalytics(router, event => events.push(event));

    router.navigate('/a', 'PUSH');
    router.navigate('/b', 'PUSH');
    analytics.flush();

    expect(events.at(-1)).toEqual({ path: '/b', navigationType: 'PUSH' });
  });

  test('dispose removes the live subscription', () => {
    const router = new MemoryRouter({ path: '/', navigationType: 'POP' });
    const events: unknown[] = [];
    const analytics = createNavigationAnalytics(router, event => events.push(event));

    analytics.dispose();
    router.navigate('/after-dispose', 'PUSH');

    expect(events).toEqual([]);
  });
});
