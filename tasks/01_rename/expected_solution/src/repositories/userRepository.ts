import type { User } from '../types';

/**
 * In-memory user repository. Records are keyed by their accountId.
 *
 * Legacy note: pre-2024 storage layer used a Postgres column named `useridx`
 * with a different semantic (autoincrement index). The current accountId is an
 * opaque UUID-like string.
 */
export class UserRepository {
  private readonly store = new Map<string, User>();

  insert(user: User): void {
    if (this.store.has(user.accountId)) {
      throw new Error(`duplicate accountId: ${user.accountId}`);
    }
    this.store.set(user.accountId, { ...user });
  }

  /** Look up a record by its accountId. */
  findById(accountId: string): User | undefined {
    const record = this.store.get(accountId);
    return record ? { ...record } : undefined;
  }

  delete(accountId: string): boolean {
    return this.store.delete(accountId);
  }

  list(): User[] {
    return Array.from(this.store.values()).map((u) => ({ ...u }));
  }

  size(): number {
    return this.store.size;
  }
}
