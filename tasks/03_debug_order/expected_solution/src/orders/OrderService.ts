import type { CartItem, Order } from '../types';
import { PriceCalculator } from '../pricing/PriceCalculator';

export class OrderService {
  private calculator: PriceCalculator;

  constructor(calculator: PriceCalculator = new PriceCalculator()) {
    this.calculator = calculator;
  }

  createOrder(items: CartItem[], discountPercent: number, shippingCost: number): Order {
    const subtotal = this.calculator.computeSubtotal(items);
    const discountedSubtotal = this.calculator.applyDiscount(subtotal, discountPercent);
    const total = discountedSubtotal + shippingCost;
    return { items, subtotal, shipping: shippingCost, discountPercent, total };
  }
}
