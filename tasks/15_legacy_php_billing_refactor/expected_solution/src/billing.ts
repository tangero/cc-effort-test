export type Plan = "starter" | "pro" | "enterprise";

export interface Account {
  plan: Plan;
  daysPastDue: number;
  periodStart: string;
}

export interface Coupon {
  active: boolean;
  kind: "percent" | "fixed";
  value: number;
  expiresAt: string;
}

export interface Invoice {
  totalCents: number;
  lateFeeCents: number;
}

export function invoice(
  account: Account,
  usageCents: number,
  periodDays: number,
  coupon?: Coupon | null
): Invoice {
  const base = account.plan === "enterprise" ? 12000 : account.plan === "pro" ? 4900 : 900;
  const grace = account.plan === "enterprise" ? 7 : 3;
  const lateFee = account.daysPastDue <= grace
    ? 0
    : Math.min(2500, (account.daysPastDue - grace) * 175);
  let subtotal = base + usageCents + lateFee;

  if (periodDays < 28) {
    subtotal = Math.floor(subtotal * periodDays / 30);
  }

  if (coupon?.active && coupon.expiresAt >= account.periodStart) {
    subtotal -= coupon.kind === "percent"
      ? Math.floor(subtotal * coupon.value / 100)
      : coupon.value;
  }

  if (subtotal < 100 && usageCents > 0) {
    subtotal = 100;
  }

  return { totalCents: Math.max(0, subtotal), lateFeeCents: lateFee };
}
