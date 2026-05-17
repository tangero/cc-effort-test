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
  const reasons: string[] = [];
  const total = items.reduce((sum, item) => sum + item.amountCents, 0);

  for (const item of items) {
    if (item.type === "MEAL" && item.amountCents >= 5000) reasons.push("meal-limit");
    if (!item.hasReceipt && item.amountCents >= 2500) reasons.push("missing-receipt");
    if (item.type === "LODGING" && item.amountCents >= 40000) reasons.push("lodging-limit");
  }

  if (total >= employee.monthlyLimitCents) reasons.unshift("monthly-limit");
  if (reasons.length > 0) return { status: "DENIED", approver: "MANAGER", reasons };
  if (total > 100000) return { status: "REVIEW", approver: "FINANCE", reasons };
  return { status: "APPROVED", approver: "NONE", reasons };
}
