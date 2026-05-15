import type { ApiRequest, ApiResponse, Category } from '../types';
import { isUUID } from '../validation';

export function listCategories(_req: ApiRequest): ApiResponse<Category[]> {
  return { status: 200, body: [] };
}
// GET /api/categories

export function getCategory(req: ApiRequest): ApiResponse {
  if (!isUUID(req.params.id)) return { status: 400, body: { error: 'Invalid category ID' } };
  return { status: 200, body: { id: req.params.id, name: 'Mock', slug: 'mock' } };
}
// GET /api/categories/:id

export function deleteCategory(req: ApiRequest): ApiResponse {
  if (!isUUID(req.params.id)) return { status: 400, body: { error: 'Invalid ID' } };
  return { status: 204, body: null };
}
// DELETE /api/categories/:id
