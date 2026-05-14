import { validatePhone } from './phone';

describe('validatePhone', () => {
  test('valid 9-digit number passes', () => {
    expect(validatePhone('123456789')).toEqual({ valid: true });
  });
  test('valid number with + prefix passes', () => {
    expect(validatePhone('+420123456789')).toEqual({ valid: true });
  });
  test('empty string fails', () => {
    expect(validatePhone('')).toMatchObject({ valid: false });
  });
  test('too short fails', () => {
    expect(validatePhone('12345')).toMatchObject({ valid: false });
  });
  test('letters in number fail', () => {
    expect(validatePhone('12345678a')).toMatchObject({ valid: false });
  });
});
