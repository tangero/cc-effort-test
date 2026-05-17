import { has, protect, Session } from '../authz';

const base: Session = {
  userId: 'u1',
  orgId: 'o1',
  roles: ['org:member'],
  permissions: ['org:reports:read'],
  features: ['reports'],
  plan: 'pro',
  reverification: 'recent',
};

describe('combined authorization requirements', () => {
  test('permission and plan must both pass', () => {
    expect(has(base, { permission: 'org:reports:read', plan: 'pro' })).toBe(true);
    expect(has(base, { permission: 'org:settings:delete', plan: 'pro' })).toBe(false);
    expect(has(base, { permission: 'org:reports:read', plan: 'enterprise' })).toBe(false);
  });

  test('reverification is an additional requirement, not an alternative', () => {
    expect(has(base, { permission: 'org:reports:read', reverification: 'recent' })).toBe(true);
    expect(has(base, { permission: 'org:reports:read', reverification: 'strict' })).toBe(false);
  });

  test('protect keeps authorization requirements when redirect URLs are present', () => {
    expect(
      protect(base, {
        permission: 'org:settings:delete',
        unauthorizedUrl: '/forbidden',
      })
    ).toBe('deny');
  });
});
