import { ValidationResult } from '../types';

export function validateICO(input: string): ValidationResult {
  if (!input) {
    return { valid: false, reason: 'IČO must not be empty' };
  }
  if (!/^\d+$/.test(input)) {
    return { valid: false, reason: 'IČO must contain digits only' };
  }
  if (input.length !== 8) {
    return { valid: false, reason: 'IČO must be exactly 8 digits' };
  }

  const digits = input.split('').map(Number);
  const weights = [8, 7, 6, 5, 4, 3, 2];
  const sum = digits
    .slice(0, 7)
    .reduce((acc, d, i) => acc + d * weights[i], 0);
  const remainder = sum % 11;

  let checksum: number;
  if (remainder === 0) {
    checksum = 1;
  } else if (remainder === 1) {
    checksum = 0;
  } else {
    checksum = 11 - remainder;
  }

  if (digits[7] !== checksum) {
    return { valid: false, reason: 'IČO checksum is invalid' };
  }

  return { valid: true };
}
