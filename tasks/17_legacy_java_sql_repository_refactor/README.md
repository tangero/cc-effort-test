# 17 Legacy Java SQL Repository Refactor

Legacy Java repository migration task. The model must preserve query semantics while replacing unsafe string interpolation with parameterized TypeScript query planning.

The hidden checks cover tenant isolation, SQL injection resistance, optional filter precedence, empty-result filters and stable parameter order.
