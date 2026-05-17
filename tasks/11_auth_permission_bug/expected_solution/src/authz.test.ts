import { has, protect, Session } from './authz';

const admin: Session = {
  userId: 'u1',
  orgId: 'o1',
  roles: ['org:admin'],
  permissions: ['org:settings:update'],
  features: ['audit-log'],
  plan: 'enterprise',
  reverification: 'strict',
};

test('single permission checks work', () => {
  expect(has(admin, { permission: 'org:settings:update' })).toBe(true);
  expect(has(admin, { permission: 'org:billing:delete' })).toBe(false);
});

test('unauthenticated sessions redirect when configured', () => {
  expect(protect(null, { permission: 'org:settings:update', unauthenticatedUrl: '/login' })).toBe(
    'redirect'
  );
});
