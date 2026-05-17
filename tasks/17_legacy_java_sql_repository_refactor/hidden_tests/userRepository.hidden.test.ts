import { buildUserSearchQuery } from "../userRepository";

test("always scopes by tenant as the first parameter", () => {
  const plan = buildUserSearchQuery({ tenantId: "tenant-a", limit: 25 });
  expect(plan.sql).toMatch(/where tenant_id = \?/);
  expect(plan.params).toEqual(["tenant-a", 25]);
});

test("parameterizes email and statuses without interpolating attacker text", () => {
  const plan = buildUserSearchQuery({
    tenantId: "t1",
    email: "x%' OR 1=1 --",
    statuses: ["active", "locked'); drop table users; --"],
    limit: 5,
  });
  expect(plan.sql).toBe("select id,email,status from users where tenant_id = ? and lower(email) like ? and status in (?,?) and deleted_at is null order by created_at desc limit ?");
  expect(plan.sql).not.toContain("drop table");
  expect(plan.params).toEqual(["t1", "%x%' or 1=1 --%", "active", "locked'); drop table users; --", 5]);
});

test("does not turn deleted filter into a broad OR condition", () => {
  const plan = buildUserSearchQuery({ tenantId: "t1", statuses: ["active"], includeDeleted: false, limit: 50 });
  expect(plan.sql).toContain("status in (?) and deleted_at is null");
  expect(plan.sql).not.toContain(" or deleted_at");
});
