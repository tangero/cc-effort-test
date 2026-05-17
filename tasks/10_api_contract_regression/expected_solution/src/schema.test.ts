import { toOpenApi30Schema } from './schema';

test('removes unsupported const keyword', () => {
  expect(toOpenApi30Schema({ type: 'string', const: 'x' })).toEqual({ type: 'string' });
});

test('rewrites real JSON references', () => {
  expect(toOpenApi30Schema({ $ref: '#/$defs/User' })).toEqual({
    $ref: '#/components/schemas/User',
  });
});
