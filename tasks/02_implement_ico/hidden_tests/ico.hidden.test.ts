import { validateICO } from './ico';

describe('validateICO — hidden test suite', () => {
  describe('valid IČOs', () => {
    test('25596641 is valid', () => {
      expect(validateICO('25596641')).toEqual({ valid: true });
    });
    test('27074358 is valid', () => {
      expect(validateICO('27074358')).toEqual({ valid: true });
    });
    test('45274649 is valid', () => {
      expect(validateICO('45274649')).toEqual({ valid: true });
    });
  });

  describe('invalid checksum', () => {
    test('25596642 has wrong checksum', () => {
      expect(validateICO('25596642')).toMatchObject({ valid: false });
    });
  });

  describe('wrong length', () => {
    test('123 is too short', () => {
      expect(validateICO('123')).toMatchObject({ valid: false });
    });
    test('123456789 is too long', () => {
      expect(validateICO('123456789')).toMatchObject({ valid: false });
    });
  });

  describe('non-digit characters', () => {
    test('abc12345 contains letters', () => {
      expect(validateICO('abc12345')).toMatchObject({ valid: false });
    });
    test('1234567a ends with letter', () => {
      expect(validateICO('1234567a')).toMatchObject({ valid: false });
    });
  });

  describe('empty string', () => {
    test('empty string is invalid', () => {
      expect(validateICO('')).toMatchObject({ valid: false });
    });
  });
});
