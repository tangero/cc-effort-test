import { db } from '../db';
import type { CreateUserInput, User } from './types';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export async function createUser(input: CreateUserInput): Promise<User> {
  if (!input.email || !EMAIL_RE.test(input.email)) {
    throw new Error('Invalid email format');
  }
  if (!input.username || input.username.length < 3 || input.username.length > 32) {
    throw new Error('Username must be between 3 and 32 characters');
  }
  return db.users.insert({ email: input.email, username: input.username, createdAt: new Date() });
}
