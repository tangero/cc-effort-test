import { ValidationResult } from '../types';

export function validatePhone(input: string): ValidationResult {
  if (!input) {
    return { valid: false, reason: 'Phone number must not be empty' };
  }
  if (!/^\+?[0-9]{9,15}$/.test(input)) {
    return { valid: false, reason: 'Phone must contain 9–15 digits, optionally prefixed with +' };
  }
  return { valid: true };
}
