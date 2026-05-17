export interface ChargeRequest {
  orderId: string;
  attempt: number;
  amountCents: number;
  currency: string;
  customerId: string;
  metadata: Record<string, string>;
}

export interface PaymentClient {
  charges: {
    create(params: Record<string, unknown>, options: { idempotencyKey: string }): Promise<{ id: string }>;
  };
}

export interface ChargeResult {
  ok: boolean;
  chargeId: string | null;
  recoverable: boolean;
}

export async function charge(client: PaymentClient, request: ChargeRequest): Promise<ChargeResult> {
  const params = {
    amount: request.amountCents,
    currency: request.currency.toLowerCase(),
    customer: request.customerId,
    metadata: { ...request.metadata, order_id: request.orderId },
  };
  const options = { idempotencyKey: `charge:${request.orderId}:${request.attempt}` };

  try {
    const created = await client.charges.create(params, options);
    return { ok: true, chargeId: created.id, recoverable: false };
  } catch (error) {
    const declineCode = typeof error === "object" && error !== null && "declineCode" in error
      ? (error as { declineCode?: unknown }).declineCode
      : undefined;
    return { ok: false, chargeId: null, recoverable: declineCode === "insufficient_funds" };
  }
}
