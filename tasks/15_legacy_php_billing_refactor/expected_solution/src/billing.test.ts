import { invoice } from "./billing";

test("calculates a normal pro invoice", () => {
  expect(invoice({ plan: "pro", daysPastDue: 0, periodStart: "2026-05-01" }, 1300, 30, null)).toEqual({
    totalCents: 6200,
    lateFeeCents: 0,
  });
});

test("applies a simple fixed coupon", () => {
  expect(invoice(
    { plan: "starter", daysPastDue: 0, periodStart: "2026-05-01" },
    600,
    30,
    { active: true, kind: "fixed", value: 500, expiresAt: "2026-05-31" }
  ).totalCents).toBe(1000);
});
