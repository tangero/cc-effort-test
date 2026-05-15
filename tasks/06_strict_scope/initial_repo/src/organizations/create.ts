import { db } from '../db';
import type { CreateOrgInput, Organization } from './types';

// TODO: add input validation (name not empty, slug format)
export async function createOrganization(input: CreateOrgInput): Promise<Organization> {
  const org = await db.organizations.insert({
    name: input.name,
    slug: input.slug,
    createdAt: new Date(),
  });
  return org;
}
