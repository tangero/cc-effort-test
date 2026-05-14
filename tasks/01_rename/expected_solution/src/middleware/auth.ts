/**
 * Minimal JWT-like token decoder used by the auth middleware. Tokens are
 * base64-encoded JSON with a `accountId` claim.
 *
 * Note: this is not a real JWT implementation, just a fixture for the
 * benchmark project. Do not confuse the internal accountId claim with the
 * external `userIdentifier` field on the User record.
 */
export interface TokenPayload {
  accountId: string;
  issuedAt: number;
}

export function decodeToken(raw: string): TokenPayload | null {
  try {
    const decoded = Buffer.from(raw, 'base64').toString('utf-8');
    const parsed = JSON.parse(decoded);
    if (typeof parsed.accountId !== 'string' || typeof parsed.issuedAt !== 'number') {
      return null;
    }
    return { accountId: parsed.accountId, issuedAt: parsed.issuedAt };
  } catch {
    return null;
  }
}

/** Extract the accountId claim from a Bearer header value. Returns null if invalid. */
export function extractUserId(authorizationHeader: string | undefined): string | null {
  if (!authorizationHeader || !authorizationHeader.startsWith('Bearer ')) {
    return null;
  }
  const token = authorizationHeader.slice('Bearer '.length);
  const payload = decodeToken(token);
  return payload ? payload.accountId : null;
}
