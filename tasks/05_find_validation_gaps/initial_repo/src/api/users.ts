import type { ApiRequest, ApiResponse, User } from '../types';
import { isUUID } from '../validation';

export function listUsers(req: ApiRequest): ApiResponse {
  const page = parseInt(req.query.page ?? '1');
  if (isNaN(page) || page < 1) return { status: 400, body: { error: 'Invalid page' } };
  return { status: 200, body: [] };
}
// GET /api/users

export function getUser(req: ApiRequest): ApiResponse {
  if (!isUUID(req.params.id)) return { status: 400, body: { error: 'Invalid user ID' } };
  return { status: 200, body: { id: req.params.id, email: '', username: '' } };
}
// GET /api/users/:id

export function createUser(req: ApiRequest<{ email: string; username: string }>): ApiResponse {
  const user: User = { id: 'new-id', email: req.body.email, username: req.body.username };
  return { status: 201, body: user };
}
// POST /api/users

export function updateUser(req: ApiRequest<{ email?: string; username?: string }>): ApiResponse {
  return { status: 200, body: { id: req.params.id, ...req.body } };
}
// PUT /api/users/:id
