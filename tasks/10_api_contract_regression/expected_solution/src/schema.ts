export type JsonSchema = {
  type?: string;
  properties?: Record<string, JsonSchema>;
  required?: string[];
  const?: unknown;
  examples?: unknown[];
  nullable?: boolean;
  $ref?: string | JsonSchema;
  [key: string]: unknown;
};

const UNSUPPORTED_OPENAPI_30_KEYS = new Set(['const']);

export function toOpenApi30Schema(schema: JsonSchema): JsonSchema {
  if (typeof schema.$ref === 'string') {
    return { $ref: rewriteRef(schema.$ref) };
  }

  const out: JsonSchema = {};
  for (const [key, value] of Object.entries(schema)) {
    if (UNSUPPORTED_OPENAPI_30_KEYS.has(key)) continue;
    if (key === 'properties' && value && typeof value === 'object' && !Array.isArray(value)) {
      out.properties = {};
      for (const [propName, propSchema] of Object.entries(value as Record<string, JsonSchema>)) {
        out.properties[propName] = toOpenApi30Schema(propSchema);
      }
      continue;
    }
    if (key === '$ref' && value && typeof value === 'object' && !Array.isArray(value)) {
      out.$ref = toOpenApi30Schema(value as JsonSchema);
      continue;
    }
    (out as Record<string, unknown>)[key] = value;
  }
  return out;
}

export function rewriteRef(ref: string): string {
  return ref.replace('#/$defs/', '#/components/schemas/');
}
