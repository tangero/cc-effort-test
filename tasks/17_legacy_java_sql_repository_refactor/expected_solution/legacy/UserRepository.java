class UserRepository {
  String search(Search s) {
    String sql = "select id,email,status from users where tenant_id = ?";
    if (s.email != null && !s.email.isBlank()) sql += " and lower(email) like ?";
    if (s.statuses != null && !s.statuses.isEmpty()) sql += " and status in (?)";
    if (!s.includeDeleted) sql += " and deleted_at is null";
    sql += " order by created_at desc limit ?";
    return sql;
  }
}
