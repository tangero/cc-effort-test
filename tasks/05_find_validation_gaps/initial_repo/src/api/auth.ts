import type { ApiRequest, ApiResponse } from '../types';
import { isEmail } from '../validation';

export function login(req: ApiRequest<{ email: string; password: string }>): ApiResponse {
  if (!isEmail(req.body.email)) return { status: 400, body: { error: 'Invalid email' } };
  if (!req.body.password || req.body.password.length < 8)
    return { status: 400, body: { error: 'Password too short' } };
  return { status: 200, body: { token: 'mock-token' } };
}
// POST /api/auth/login

export function register(req: ApiRequest<{ email: string; password: string; username: string }>): ApiResponse {
  if (!isEmail(req.body.email)) return { status: 400, body: { error: 'Invalid email' } };
  if (!req.body.password || req.body.password.length < 8)
    return { status: 400, body: { error: 'Password must be at least 8 characters' } };
  if (!req.body.username || req.body.username.length < 3)
    return { status: 400, body: { error: 'Username too short' } };
  return { status: 201, body: { message: 'Registered' } };
}
// POST /api/auth/register

export function refreshToken(req: ApiRequest<{ refreshToken: string }>): ApiResponse {
  if (!req.body.refreshToken)
    return { status: 400, body: { error: 'refreshToken required' } };
  return { status: 200, body: { token: 'new-token' } };
}
// POST /api/auth/refresh

export function logout(req: ApiRequest<{ token: string }>): ApiResponse {
  if (!req.body.token) return { status: 400, body: { error: 'token required' } };
  return { status: 200, body: { message: 'Logged out' } };
}
// POST /api/auth/logout
