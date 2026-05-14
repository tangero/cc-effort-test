/**
 * Minimal JWT-like token decoder used by the auth middleware. Tokens are
 * base64-encoded JSON with a `userId` claim.
 *
 * Note: this is not a real JWT implementation, just a fixture for the
 * benchmark project. Do not confuse the internal userId claim with the
 * external `userIdentifier` field on the User record.
 */
export interface TokenPayload {
  userId: string;
  issuedAt: number;
}

export function decodeToken(raw: string): TokenPayload | null {
  try {
    const decoded = Buffer.from(raw, 'base64').toString('utf-8');
    const parsed = JSON.parse(decoded);
    if (typeof parsed.userId !== 'string' || typeof parsed.issuedAt !== 'number') {
      return null;
    }
    return { userId: parsed.userId, issuedAt: parsed.issuedAt };
  } catch {
    return null;
  }
}

/** Extract the userId claim from a Bearer header value. Returns null if invalid. */
export function extractUserId(authorizationHeader: string | undefined): string | null {
  if (!authorizationHeader || !authorizationHeader.startsWith('Bearer ')) {
    return null;
  }
  const token = authorizationHeader.slice('Bearer '.length);
  const payload = decodeToken(token);
  return payload ? payload.userId : null;
}
