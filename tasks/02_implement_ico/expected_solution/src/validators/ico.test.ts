import { validateICO } from './ico';

describe('validateICO', () => {
  test('25596641 is valid', () => {
    expect(validateICO('25596641')).toEqual({ valid: true });
  });
  test('27074358 is valid', () => {
    expect(validateICO('27074358')).toEqual({ valid: true });
  });
  test('invalid checksum fails', () => {
    expect(validateICO('25596642')).toMatchObject({ valid: false });
  });
  test('too short fails', () => {
    expect(validateICO('123')).toMatchObject({ valid: false });
  });
  test('too long fails', () => {
    expect(validateICO('123456789')).toMatchObject({ valid: false });
  });
  test('non-digits fail', () => {
    expect(validateICO('abc12345')).toMatchObject({ valid: false });
  });
  test('empty string fails', () => {
    expect(validateICO('')).toMatchObject({ valid: false });
  });
});
