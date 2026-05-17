import { getQueryCount, listInvoicesForTenant, seedData } from '../repository';

describe('invoice listing performance and tenant isolation', () => {
  test('uses a bounded number of queries for many invoices', () => {
    seedData({
      customers: Array.from({ length: 10 }, (_, i) => ({
        id: `c${i}`,
        tenantId: 't1',
        name: `Customer ${i}`,
      })),
      invoices: Array.from({ length: 50 }, (_, i) => ({
        id: `i${i}`,
        tenantId: 't1',
        customerId: `c${i % 10}`,
        total: i,
      })),
    });

    const result = listInvoicesForTenant('t1');

    expect(result).toHaveLength(50);
    expect(getQueryCount()).toBeLessThanOrEqual(3);
  });

  test('does not leak customer names across tenants with the same customer id', () => {
    seedData({
      customers: [
        { id: 'shared', tenantId: 't1', name: 'Tenant One Customer' },
        { id: 'shared', tenantId: 't2', name: 'Tenant Two Customer' },
      ],
      invoices: [
        { id: 'i1', tenantId: 't1', customerId: 'shared', total: 100 },
        { id: 'i2', tenantId: 't2', customerId: 'shared', total: 200 },
      ],
    });

    expect(listInvoicesForTenant('t2')).toEqual([
      {
        id: 'i2',
        tenantId: 't2',
        customerId: 'shared',
        total: 200,
        customerName: 'Tenant Two Customer',
      },
    ]);
  });
});
