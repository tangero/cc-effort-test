import { decide } from "./expenseReport";

test("approves a small staff report", () => {
  expect(decide({ level: "STAFF", monthlyLimitCents: 50000 }, [
    { type: "TRAVEL", amountCents: 12000, city: "PRG", hasReceipt: true },
  ])).toEqual({ status: "APPROVED", approver: "NONE", reasons: [] });
});

test("denies an obvious meal limit violation", () => {
  expect(decide({ level: "STAFF", monthlyLimitCents: 50000 }, [
    { type: "MEAL", amountCents: 9000, city: "PRG", hasReceipt: true },
  ]).reasons).toContain("meal-limit");
});
