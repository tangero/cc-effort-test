import type { Result, User } from '../types';
import { UserRepository } from '../repositories/userRepository';
import { logEvent } from '../utils/logger';

/**
 * Business logic for managing users. Wraps the repository with validation
 * and audit logging. The accountId in the input record is treated as authoritative.
 */
export class UserService {
  constructor(private readonly repo: UserRepository) {}

  /**
   * Create a new user.
   *
   * @param user - full user record including a unique accountId
   * @returns Result indicating success or a validation error
   */
  create(user: User): Result<User> {
    if (!user.accountId || user.accountId.trim() === '') {
      return { ok: false, error: 'accountId is required' };
    }
    if (!user.email.includes('@')) {
      return { ok: false, error: 'invalid email' };
    }
    if (this.repo.findById(user.accountId)) {
      return { ok: false, error: `user already exists: ${user.accountId}` };
    }
    this.repo.insert(user);
    logEvent('user.created', { accountId: user.accountId });
    return { ok: true, value: user };
  }

  get(accountId: string): Result<User> {
    const found = this.repo.findById(accountId);
    if (!found) {
      return { ok: false, error: `not found: ${accountId}` };
    }
    return { ok: true, value: found };
  }

  remove(accountId: string): boolean {
    const removed = this.repo.delete(accountId);
    if (removed) {
      logEvent('user.removed', { accountId });
    }
    return removed;
  }
}
