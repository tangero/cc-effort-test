import { charge, PaymentClient } from "../paymentGateway";

test("uses legacy idempotency key and lower-case currency", async () => {
  const create = jest.fn().mockResolvedValue({ id: "ch_123" });
  const client: PaymentClient = { charges: { create } };
  await charge(client, {
    orderId: "ord_42",
    attempt: 3,
    amountCents: 9900,
    currency: "CZK",
    customerId: "cus_9",
    metadata: { source: "checkout" },
  });
  expect(create).toHaveBeenCalledWith({
    amount: 9900,
    currency: "czk",
    customer: "cus_9",
    metadata: { source: "checkout", order_id: "ord_42" },
  }, { idempotencyKey: "charge:ord_42:3" });
});

test("does not mutate caller metadata", async () => {
  const create = jest.fn().mockResolvedValue({ id: "ch_123" });
  const metadata = { source: "retry" };
  await charge({ charges: { create } }, {
    orderId: "ord_7",
    attempt: 2,
    amountCents: 500,
    currency: "USD",
    customerId: "cus_7",
    metadata,
  });
  expect(metadata).toEqual({ source: "retry" });
});

test("maps insufficient funds declines as recoverable only", async () => {
  const insufficient = Object.assign(new Error("declined"), { declineCode: "insufficient_funds" });
  const stolen = Object.assign(new Error("declined"), { declineCode: "stolen_card" });
  await expect(charge({ charges: { create: jest.fn().mockRejectedValue(insufficient) } }, {
    orderId: "a", attempt: 1, amountCents: 1, currency: "USD", customerId: "c", metadata: {},
  })).resolves.toEqual({ ok: false, chargeId: null, recoverable: true });
  await expect(charge({ charges: { create: jest.fn().mockRejectedValue(stolen) } }, {
    orderId: "b", attempt: 1, amountCents: 1, currency: "USD", customerId: "c", metadata: {},
  })).resolves.toEqual({ ok: false, chargeId: null, recoverable: false });
});
