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
  let sql = "select id,email,status from users where 1=1";
  const params: unknown[] = [];

  if (search.email) {
    sql += ` and lower(email) like '%${search.email.toLowerCase()}%'`;
  }
  if (search.statuses?.length) {
    sql += " and status in (" + search.statuses.map((s) => `'${s}'`).join(",") + ")";
  }
  if (search.includeDeleted !== true) {
    sql += " or deleted_at is null";
  }

  sql += " order by created_at desc limit ?";
  params.push(search.limit);
  return { sql, params };
}
