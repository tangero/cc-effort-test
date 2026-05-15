import type { ApiRequest, ApiResponse, Order, OrderItem } from '../types';
import { isUUID, isOrderStatus } from '../validation';

export function listOrders(req: ApiRequest): ApiResponse {
  if (req.query.userId && !isUUID(req.query.userId))
    return { status: 400, body: { error: 'Invalid userId filter' } };
  return { status: 200, body: [] };
}
// GET /api/orders

export function getOrder(req: ApiRequest): ApiResponse {
  if (!isUUID(req.params.id)) return { status: 400, body: { error: 'Invalid order ID' } };
  return { status: 200, body: null };
}
// GET /api/orders/:id

export function createOrder(req: ApiRequest<{ userId: string; items: OrderItem[] }>): ApiResponse {
  const order: Order = { id: 'new-id', userId: req.body.userId, items: req.body.items, status: 'pending' };
  return { status: 201, body: order };
}
// POST /api/orders  ← NO VALIDATION (items could be empty, quantities not checked)

export function updateOrderStatus(req: ApiRequest<{ status: string }>): ApiResponse {
  const order = { id: req.params.id, status: req.body.status };
  return { status: 200, body: order };
}
// PUT /api/orders/:id  ← NO VALIDATION (status not validated against enum)

export function deleteOrder(req: ApiRequest): ApiResponse {
  if (!isUUID(req.params.id)) return { status: 400, body: { error: 'Invalid order ID' } };
  return { status: 204, body: null };
}
// DELETE /api/orders/:id
