import { UserRepository } from '../repositories/userRepository';
import type { User } from '../types';

function makeUser(accountId: string, overrides: Partial<User> = {}): User {
  return {
    accountId,
    email: `${accountId}@example.com`,
    createdAt: new Date('2024-01-01T00:00:00Z'),
    ...overrides,
  };
}

describe('UserRepository', () => {
  test('inserts and retrieves a user by accountId', () => {
    const repo = new UserRepository();
    repo.insert(makeUser('u-001'));
    const found = repo.findById('u-001');
    expect(found?.accountId).toBe('u-001');
  });

  test('rejects duplicate accountId on insert', () => {
    const repo = new UserRepository();
    repo.insert(makeUser('u-001'));
    expect(() => repo.insert(makeUser('u-001'))).toThrow(/duplicate accountId/);
  });

  test('delete returns true when the accountId exists', () => {
    const repo = new UserRepository();
    repo.insert(makeUser('u-002'));
    expect(repo.delete('u-002')).toBe(true);
    expect(repo.findById('u-002')).toBeUndefined();
  });

  test('delete returns false when the accountId is unknown', () => {
    const repo = new UserRepository();
    expect(repo.delete('missing')).toBe(false);
  });

  test('list returns copies, not references', () => {
    const repo = new UserRepository();
    repo.insert(makeUser('u-003'));
    const list = repo.list();
    list[0].email = 'mutated@example.com';
    expect(repo.findById('u-003')?.email).toBe('u-003@example.com');
  });
});
