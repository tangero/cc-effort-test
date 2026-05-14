import type { CartItem } from '../types';

export class PriceCalculator {
  computeSubtotal(items: CartItem[]): number {
    return items.reduce((sum, item) => sum + item.quantity * item.unitPrice, 0);
  }

  applyDiscount(subtotal: number, discountPercent: number): number {
    return subtotal + (subtotal * discountPercent / 100);
  }
}
