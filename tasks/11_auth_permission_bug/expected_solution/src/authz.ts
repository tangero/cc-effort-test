export interface Session {
  userId: string;
  orgId: string;
  roles: string[];
  permissions: string[];
  features: string[];
  plan: 'free' | 'pro' | 'enterprise';
  reverification: 'none' | 'recent' | 'strict';
}

export type Requirement = {
  role?: string;
  permission?: string;
  feature?: string;
  plan?: Session['plan'];
  reverification?: Exclude<Session['reverification'], 'none'>;
  unauthenticatedUrl?: string;
  unauthorizedUrl?: string;
};

const planRank = { free: 0, pro: 1, enterprise: 2 };
const reverifyRank = { none: 0, recent: 1, strict: 2 };

export function has(session: Session | null, requirement: Requirement): boolean {
  if (!session) return false;
  const checks: boolean[] = [];
  if (requirement.role) checks.push(session.roles.includes(requirement.role));
  if (requirement.permission) checks.push(session.permissions.includes(requirement.permission));
  if (requirement.feature) checks.push(session.features.includes(requirement.feature));
  if (requirement.plan) checks.push(planRank[session.plan] >= planRank[requirement.plan]);
  if (requirement.reverification) {
    checks.push(reverifyRank[session.reverification] >= reverifyRank[requirement.reverification]);
  }
  return checks.length === 0 ? true : checks.every(Boolean);
}

export function protect(session: Session | null, requirement: Requirement): 'allow' | 'redirect' | 'deny' {
  if (!session) return requirement.unauthenticatedUrl ? 'redirect' : 'deny';
  return has(session, requirement) ? 'allow' : 'deny';
}
