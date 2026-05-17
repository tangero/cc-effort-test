import java.util.*;

class ExpenseReport {
  Decision decide(Employee employee, List<LineItem> items) {
    int total = 0;
    List<String> reasons = new ArrayList<>();
    for (LineItem item : items) {
      total += item.amountCents;
      int mealLimit = item.city.equals("NYC") || item.city.equals("SFO") ? 7500 : 5000;
      if (item.type.equals("MEAL") && item.amountCents > mealLimit) reasons.add("meal-limit");
      if (!item.hasReceipt && item.amountCents > 2500 && !employee.level.equals("EXEC")) reasons.add("missing-receipt");
      if (item.type.equals("LODGING") && item.amountCents > 40000) reasons.add("lodging-limit");
    }
    if (total > employee.monthlyLimitCents) reasons.add("monthly-limit");
    if (!reasons.isEmpty()) return new Decision("DENIED", "MANAGER", reasons);
    if (total >= 100000 || employee.level.equals("CONTRACTOR")) return new Decision("REVIEW", "FINANCE", reasons);
    return new Decision("APPROVED", "NONE", reasons);
  }
}
