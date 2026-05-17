import { invoice } from "../billing";

test("uses plan-specific grace days before computing late fees", () => {
  expect(invoice({ plan: "pro", daysPastDue: 3, periodStart: "2026-05-01" }, 0, 30, null).lateFeeCents).toBe(0);
  expect(invoice({ plan: "pro", daysPastDue: 8, periodStart: "2026-05-01" }, 0, 30, null).lateFeeCents).toBe(875);
  expect(invoice({ plan: "enterprise", daysPastDue: 20, periodStart: "2026-05-01" }, 0, 30, null).lateFeeCents).toBe(2275);
});

test("prorates before applying coupons and floors legacy fractional cents", () => {
  const result = invoice(
    { plan: "pro", daysPastDue: 5, periodStart: "2026-05-01" },
    999,
    15,
    { active: true, kind: "percent", value: 15, expiresAt: "2026-05-01" }
  );
  expect(result.totalCents).toBe(2656);
});

test("keeps legacy minimum charge only when usage is present", () => {
  expect(invoice(
    { plan: "starter", daysPastDue: 0, periodStart: "2026-05-01" },
    50,
    30,
    { active: true, kind: "fixed", value: 1000, expiresAt: "2026-06-01" }
  ).totalCents).toBe(100);
  expect(invoice(
    { plan: "starter", daysPastDue: 0, periodStart: "2026-05-01" },
    0,
    30,
    { active: true, kind: "fixed", value: 1000, expiresAt: "2026-06-01" }
  ).totalCents).toBe(0);
});
