import { OrderService } from '../orders/OrderService';
import { PriceCalculator } from '../pricing/PriceCalculator';

describe('OrderService', () => {
  let orderService: OrderService;

  beforeEach(() => {
    orderService = new OrderService(new PriceCalculator());
  });

  test('order with no discount and no shipping', () => {
    const order = orderService.createOrder(
      [{ name: 'Widget', quantity: 2, unitPrice: 50 }],
      0,
      0
    );
    expect(order.subtotal).toBe(100);
    expect(order.total).toBe(100);
  });

  test('order with 10% discount and no shipping should cost $90', () => {
    const order = orderService.createOrder(
      [{ name: 'Widget', quantity: 1, unitPrice: 100 }],
      10,
      0
    );
    expect(order.total).toBe(90);
  });

  test('subtotal is computed correctly from multiple items', () => {
    const order = orderService.createOrder(
      [
        { name: 'Widget', quantity: 2, unitPrice: 30 },
        { name: 'Gadget', quantity: 1, unitPrice: 40 },
      ],
      0,
      0
    );
    expect(order.subtotal).toBe(100);
    expect(order.total).toBe(100);
  });
});
