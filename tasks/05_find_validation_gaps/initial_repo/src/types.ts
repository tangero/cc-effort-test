export interface ApiRequest<T = unknown> {
  body: T;
  params: Record<string, string>;
  query: Record<string, string>;
}

export interface ApiResponse<T = unknown> {
  status: number;
  body: T;
}

export interface User { id: string; email: string; username: string; }
export interface Product { id: string; name: string; price: number; categoryId: string; }
export interface Order { id: string; userId: string; items: OrderItem[]; status: string; }
export interface OrderItem { productId: string; quantity: number; }
export interface Category { id: string; name: string; slug: string; }
