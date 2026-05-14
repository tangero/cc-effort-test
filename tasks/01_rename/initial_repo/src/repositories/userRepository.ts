import type { User } from '../types';

/**
 * In-memory user repository. Records are keyed by their userId.
 *
 * Legacy note: pre-2024 storage layer used a Postgres column named `useridx`
 * with a different semantic (autoincrement index). The current userId is an
 * opaque UUID-like string.
 */
export class UserRepository {
  private readonly store = new Map<string, User>();

  insert(user: User): void {
    if (this.store.has(user.userId)) {
      throw new Error(`duplicate userId: ${user.userId}`);
    }
    this.store.set(user.userId, { ...user });
  }

  /** Look up a record by its userId. */
  findById(userId: string): User | undefined {
    const record = this.store.get(userId);
    return record ? { ...record } : undefined;
  }

  delete(userId: string): boolean {
    return this.store.delete(userId);
  }

  list(): User[] {
    return Array.from(this.store.values()).map((u) => ({ ...u }));
  }

  size(): number {
    return this.store.size;
  }
}
