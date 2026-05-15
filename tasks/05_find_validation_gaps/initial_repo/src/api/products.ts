import type { ApiRequest, ApiResponse, Product } from '../types';
import { isUUID, isNonEmpty, isPositive } from '../validation';

export function listProducts(req: ApiRequest): ApiResponse {
  const limit = parseInt(req.query.limit ?? '20');
  if (isNaN(limit) || limit < 1 || limit > 100)
    return { status: 400, body: { error: 'limit must be 1–100' } };
  return { status: 200, body: [] };
}
// GET /api/products

export function getProduct(req: ApiRequest): ApiResponse {
  if (!isUUID(req.params.id)) return { status: 400, body: { error: 'Invalid product ID' } };
  return { status: 200, body: null };
}
// GET /api/products/:id

export function createProduct(req: ApiRequest<{ name: string; price: number; categoryId: string }>): ApiResponse {
  const product: Product = { id: 'new-id', name: req.body.name, price: req.body.price, categoryId: req.body.categoryId };
  return { status: 201, body: product };
}
// POST /api/products  ← NO VALIDATION

export function updateProduct(req: ApiRequest<{ name?: string; price?: number }>): ApiResponse {
  if (!isUUID(req.params.id)) return { status: 400, body: { error: 'Invalid ID' } };
  if (req.body.name !== undefined && !isNonEmpty(req.body.name))
    return { status: 400, body: { error: 'name cannot be empty' } };
  if (req.body.price !== undefined && !isPositive(req.body.price))
    return { status: 400, body: { error: 'price must be positive' } };
  return { status: 200, body: null };
}
// PUT /api/products/:id
