import { OrderService } from '../orders/OrderService';
import { PriceCalculator } from '../pricing/PriceCalculator';

describe('OrderService — hidden test suite', () => {
  let orderService: OrderService;

  beforeEach(() => {
    orderService = new OrderService(new PriceCalculator());
  });

  test('discount should not apply to shipping costs', () => {
    const order = orderService.createOrder(
      [{ name: 'Widget', quantity: 1, unitPrice: 100 }],
      10,
      15
    );
    expect(order.total).toBe(105);
  });

  test('large shipping should not reduce effective discount', () => {
    const order = orderService.createOrder(
      [{ name: 'Item', quantity: 2, unitPrice: 50 }],
      20,
      25
    );
    expect(order.total).toBe(105);
  });

  test('zero discount with shipping is unaffected by bug B', () => {
    const order = orderService.createOrder(
      [{ name: 'Item', quantity: 1, unitPrice: 50 }],
      0,
      10
    );
    expect(order.total).toBe(60);
  });
});
