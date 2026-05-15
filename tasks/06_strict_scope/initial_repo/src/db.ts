export interface User {
  id: string;
  email: string;
  username: string;
  createdAt: Date;
  updatedAt?: Date;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  createdAt: Date;
}

const uid = () => Math.random().toString(36).slice(2, 10);

export const db = {
  users: {
    insert: async (data: Omit<User, 'id'>): Promise<User> => ({ id: uid(), ...data }),
    update: async (id: string, data: Partial<Omit<User, 'id'>>): Promise<User> => ({
      id, email: '', username: '', createdAt: new Date(), ...data,
    }),
  },
  organizations: {
    insert: async (data: Omit<Organization, 'id'>): Promise<Organization> => ({ id: uid(), ...data }),
  },
};
