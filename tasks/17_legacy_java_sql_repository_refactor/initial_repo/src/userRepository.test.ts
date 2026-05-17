import { buildUserSearchQuery } from "./userRepository";

test("builds a basic limited query", () => {
  const plan = buildUserSearchQuery({ tenantId: "t1", limit: 20 });
  expect(plan.sql).toContain("limit ?");
  expect(plan.params.at(-1)).toBe(20);
});

test("adds an email filter", () => {
  const plan = buildUserSearchQuery({ tenantId: "t1", email: "A@Example.COM", limit: 10 });
  expect(plan.sql.toLowerCase()).toContain("lower(email)");
});
