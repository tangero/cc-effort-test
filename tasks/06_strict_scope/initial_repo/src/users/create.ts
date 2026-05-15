import { db } from '../db';
import type { CreateUserInput, User } from './types';

export async function createUser(input: CreateUserInput): Promise<User> {
  const user = await db.users.insert({
    email: input.email,
    username: input.username,
    createdAt: new Date(),
  });
  return user;
}
