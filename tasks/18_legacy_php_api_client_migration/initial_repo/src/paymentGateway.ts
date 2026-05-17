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
  request.metadata.order_id = request.orderId;
  try {
    const created = await client.charges.create({
      amount: request.amountCents,
      currency: request.currency,
      customer: request.customerId,
      metadata: request.metadata,
    }, { idempotencyKey: request.orderId });
    return { ok: true, chargeId: created.id, recoverable: false };
  } catch {
    return { ok: false, chargeId: null, recoverable: false };
  }
}
