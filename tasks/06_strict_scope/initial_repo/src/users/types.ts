export interface CreateUserInput {
  email: string;
  username: string;
}

export interface UpdateUserInput {
  email?: string;
  username?: string;
}

export type { User } from '../db';
