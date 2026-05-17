import { charge, PaymentClient } from "./paymentGateway";

test("creates a basic charge", async () => {
  const client: PaymentClient = {
    charges: { create: jest.fn().mockResolvedValue({ id: "ch_1" }) },
  };
  await expect(charge(client, {
    orderId: "ord_1",
    attempt: 1,
    amountCents: 1200,
    currency: "EUR",
    customerId: "cus_1",
    metadata: {},
  })).resolves.toEqual({ ok: true, chargeId: "ch_1", recoverable: false });
});
