import type { Result, User } from '../types';
import { UserRepository } from '../repositories/userRepository';
import { logEvent } from '../utils/logger';

/**
 * Business logic for managing users. Wraps the repository with validation
 * and audit logging. The userId in the input record is treated as authoritative.
 */
export class UserService {
  constructor(private readonly repo: UserRepository) {}

  /**
   * Create a new user.
   *
   * @param user - full user record including a unique userId
   * @returns Result indicating success or a validation error
   */
  create(user: User): Result<User> {
    if (!user.userId || user.userId.trim() === '') {
      return { ok: false, error: 'userId is required' };
    }
    if (!user.email.includes('@')) {
      return { ok: false, error: 'invalid email' };
    }
    if (this.repo.findById(user.userId)) {
      return { ok: false, error: `user already exists: ${user.userId}` };
    }
    this.repo.insert(user);
    logEvent('user.created', { userId: user.userId });
    return { ok: true, value: user };
  }

  get(userId: string): Result<User> {
    const found = this.repo.findById(userId);
    if (!found) {
      return { ok: false, error: `not found: ${userId}` };
    }
    return { ok: true, value: found };
  }

  remove(userId: string): boolean {
    const removed = this.repo.delete(userId);
    if (removed) {
      logEvent('user.removed', { userId });
    }
    return removed;
  }
}
