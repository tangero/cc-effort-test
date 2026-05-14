import { ValidationResult } from '../types';

export function validateEmail(input: string): ValidationResult {
  if (!input) {
    return { valid: false, reason: 'Email must not be empty' };
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input)) {
    return { valid: false, reason: 'Email format is invalid' };
  }
  return { valid: true };
}
