export interface UserSearch {
  tenantId: string;
  email?: string;
  statuses?: string[];
  includeDeleted?: boolean;
  limit: number;
}

export interface QueryPlan {
  sql: string;
  params: unknown[];
}

export function buildUserSearchQuery(search: UserSearch): QueryPlan {
  let sql = "select id,email,status from users where tenant_id = ?";
  const params: unknown[] = [search.tenantId];

  const email = search.email?.trim();
  if (email) {
    sql += " and lower(email) like ?";
    params.push(`%${email.toLowerCase()}%`);
  }
  if (search.statuses?.length) {
    sql += ` and status in (${search.statuses.map(() => "?").join(",")})`;
    params.push(...search.statuses);
  }
  if (!search.includeDeleted) {
    sql += " and deleted_at is null";
  }

  sql += " order by created_at desc limit ?";
  params.push(search.limit);
  return { sql, params };
}
