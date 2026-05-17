export type EmployeeLevel = "STAFF" | "MANAGER" | "EXEC" | "CONTRACTOR";
export type ExpenseType = "MEAL" | "LODGING" | "TRAVEL" | "SUPPLIES";

export interface Employee {
  level: EmployeeLevel;
  monthlyLimitCents: number;
}

export interface LineItem {
  type: ExpenseType;
  amountCents: number;
  city: string;
  hasReceipt: boolean;
}

export interface Decision {
  status: "APPROVED" | "REVIEW" | "DENIED";
  approver: "NONE" | "MANAGER" | "FINANCE";
  reasons: string[];
}

export function decide(employee: Employee, items: LineItem[]): Decision {
  let total = 0;
  const reasons: string[] = [];

  for (const item of items) {
    total += item.amountCents;
    const mealLimit = item.city === "NYC" || item.city === "SFO" ? 7500 : 5000;
    if (item.type === "MEAL" && item.amountCents > mealLimit) reasons.push("meal-limit");
    if (!item.hasReceipt && item.amountCents > 2500 && employee.level !== "EXEC") {
      reasons.push("missing-receipt");
    }
    if (item.type === "LODGING" && item.amountCents > 40000) reasons.push("lodging-limit");
  }

  if (total > employee.monthlyLimitCents) reasons.push("monthly-limit");
  if (reasons.length > 0) return { status: "DENIED", approver: "MANAGER", reasons };
  if (total >= 100000 || employee.level === "CONTRACTOR") {
    return { status: "REVIEW", approver: "FINANCE", reasons };
  }
  return { status: "APPROVED", approver: "NONE", reasons };
}
