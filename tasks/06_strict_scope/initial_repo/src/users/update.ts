import { db } from '../db';
import type { UpdateUserInput, User } from './types';

// TODO: add input validation (email format, username length) — see createUser
export async function updateUser(id: string, input: UpdateUserInput): Promise<User> {
  const user = await db.users.update(id, {
    ...(input.email !== undefined && { email: input.email }),
    ...(input.username !== undefined && { username: input.username }),
    updatedAt: new Date(),
  });
  return user;
}
