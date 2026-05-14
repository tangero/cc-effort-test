export interface CartItem {
  name: string;
  quantity: number;
  unitPrice: number;
}

export interface Order {
  items: CartItem[];
  subtotal: number;
  shipping: number;
  discountPercent: number;
  total: number;
}
