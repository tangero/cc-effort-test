import { createNavigationAnalytics, MemoryRouter } from './navigation';

test('sends the initial navigation event', () => {
  const router = new MemoryRouter({ path: '/', navigationType: 'POP' });
  const events: unknown[] = [];
  const analytics = createNavigationAnalytics(router, event => events.push(event));

  analytics.flush();

  expect(events).toEqual([{ path: '/', navigationType: 'POP' }]);
});

test('uses the current path after navigation', () => {
  const router = new MemoryRouter({ path: '/', navigationType: 'POP' });
  const events: unknown[] = [];
  createNavigationAnalytics(router, event => events.push(event));

  router.navigate('/settings', 'REPLACE');

  expect(events).toEqual([{ path: '/settings', navigationType: 'POP' }]);
});
