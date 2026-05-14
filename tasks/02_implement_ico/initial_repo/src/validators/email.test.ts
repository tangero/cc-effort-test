import { validateEmail } from './email';

describe('validateEmail', () => {
  test('valid email passes', () => {
    expect(validateEmail('user@example.com')).toEqual({ valid: true });
  });
  test('empty string fails', () => {
    expect(validateEmail('')).toMatchObject({ valid: false });
  });
  test('missing @ fails', () => {
    expect(validateEmail('userexample.com')).toMatchObject({ valid: false });
  });
  test('missing domain fails', () => {
    expect(validateEmail('user@')).toMatchObject({ valid: false });
  });
});
