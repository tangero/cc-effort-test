/**
 * Domain types for the user service.
 *
 * Historical note: the legacy LDAP system referenced these records by their
 * `UserID` column (all uppercase). Do not confuse `accountId` with
 * `userIdentifier`, which is the external SSO subject claim from the
 * identity provider.
 */
export interface User {
  accountId: string;
  email: string;
  /** External SSO identifier (e.g. from Auth0, Okta). Not the same as accountId. */
  userIdentifier?: string;
  createdAt: Date;
}

export interface Session {
  sessionId: string;
  accountId: string;
  expiresAt: Date;
}

export interface AuditEntry {
  accountId: string;
  action: string;
  timestamp: Date;
}

export type Result<T> =
  | { ok: true; value: T }
  | { ok: false; error: string };
