import { toOpenApi30Schema } from '../schema';

describe('OpenAPI contract conversion edge cases', () => {
  test('preserves a user property literally named $ref', () => {
    const converted = toOpenApi30Schema({
      type: 'object',
      required: ['$ref'],
      properties: {
        $ref: { type: 'string', examples: ['external-id'] },
      },
    });

    expect(converted).toEqual({
      type: 'object',
      required: ['$ref'],
      properties: {
        $ref: { type: 'string', examples: ['external-id'] },
      },
    });
  });

  test('preserves a root schema object whose key is literally $ref', () => {
    expect(toOpenApi30Schema({ $ref: { type: 'string', examples: ['literal'] } })).toEqual({
      $ref: { type: 'string', examples: ['literal'] },
    });
  });

  test('recursively removes const while preserving nullable and examples', () => {
    expect(
      toOpenApi30Schema({
        type: 'object',
        properties: {
          status: { type: 'string', const: 'active', examples: ['active'] },
          deletedAt: { type: 'string', nullable: true },
        },
      })
    ).toEqual({
      type: 'object',
      properties: {
        status: { type: 'string', examples: ['active'] },
        deletedAt: { type: 'string', nullable: true },
      },
    });
  });

  test('rewrites nested real refs without confusing sibling properties', () => {
    expect(
      toOpenApi30Schema({
        type: 'object',
        properties: {
          owner: { $ref: '#/$defs/User' },
          metadata: {
            type: 'object',
            properties: { $ref: { type: 'string' } },
          },
        },
      })
    ).toEqual({
      type: 'object',
      properties: {
        owner: { $ref: '#/components/schemas/User' },
        metadata: {
          type: 'object',
          properties: { $ref: { type: 'string' } },
        },
      },
    });
  });
});
