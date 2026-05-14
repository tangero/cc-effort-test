import { UserRepository } from '../repositories/userRepository';
import { UserService } from '../services/userService';
import { extractUserId } from '../middleware/auth';
import type { User } from '../types';

function makeUser(userId: string, email = `${userId}@example.com`): User {
  return { userId, email, createdAt: new Date('2024-01-01T00:00:00Z') };
}

describe('UserService', () => {
  test('create succeeds with a valid record', () => {
    const svc = new UserService(new UserRepository());
    const result = svc.create(makeUser('alice'));
    expect(result.ok).toBe(true);
  });

  test('create rejects an empty userId', () => {
    const svc = new UserService(new UserRepository());
    const result = svc.create(makeUser(''));
    expect(result.ok).toBe(false);
  });

  test('create rejects a malformed email', () => {
    const svc = new UserService(new UserRepository());
    const result = svc.create(makeUser('bob', 'not-an-email'));
    expect(result.ok).toBe(false);
  });

  test('get returns ok=false when userId is unknown', () => {
    const svc = new UserService(new UserRepository());
    expect(svc.get('missing')).toEqual({ ok: false, error: 'not found: missing' });
  });

  test('remove returns true after a successful delete', () => {
    const svc = new UserService(new UserRepository());
    svc.create(makeUser('carol'));
    expect(svc.remove('carol')).toBe(true);
  });
});

describe('extractUserId', () => {
  test('decodes a base64 token carrying a userId claim', () => {
    const payload = JSON.stringify({ userId: 'dave', issuedAt: 123 });
    const token = Buffer.from(payload, 'utf-8').toString('base64');
    expect(extractUserId(`Bearer ${token}`)).toBe('dave');
  });

  test('returns null for a missing header', () => {
    expect(extractUserId(undefined)).toBeNull();
  });
});
