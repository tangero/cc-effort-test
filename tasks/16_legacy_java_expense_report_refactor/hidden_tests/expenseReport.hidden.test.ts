import { decide } from "../expenseReport";

test("preserves city-specific meal thresholds and strict greater-than boundaries", () => {
  expect(decide({ level: "STAFF", monthlyLimitCents: 60000 }, [
    { type: "MEAL", amountCents: 7500, city: "NYC", hasReceipt: true },
  ])).toEqual({ status: "APPROVED", approver: "NONE", reasons: [] });
  expect(decide({ level: "STAFF", monthlyLimitCents: 60000 }, [
    { type: "MEAL", amountCents: 7501, city: "SFO", hasReceipt: true },
  ]).reasons).toEqual(["meal-limit"]);
});

test("waives missing receipts for executives but not for other levels", () => {
  expect(decide({ level: "EXEC", monthlyLimitCents: 80000 }, [
    { type: "SUPPLIES", amountCents: 3000, city: "BRN", hasReceipt: false },
  ])).toEqual({ status: "APPROVED", approver: "NONE", reasons: [] });
  expect(decide({ level: "MANAGER", monthlyLimitCents: 80000 }, [
    { type: "SUPPLIES", amountCents: 2501, city: "BRN", hasReceipt: false },
  ]).reasons).toEqual(["missing-receipt"]);
});

test("keeps denial reason order and contractor finance review rule", () => {
  expect(decide({ level: "STAFF", monthlyLimitCents: 9000 }, [
    { type: "LODGING", amountCents: 45000, city: "PRG", hasReceipt: false },
  ]).reasons).toEqual(["missing-receipt", "lodging-limit", "monthly-limit"]);
  expect(decide({ level: "CONTRACTOR", monthlyLimitCents: 200000 }, [
    { type: "TRAVEL", amountCents: 1000, city: "PRG", hasReceipt: true },
  ])).toEqual({ status: "REVIEW", approver: "FINANCE", reasons: [] });
});
