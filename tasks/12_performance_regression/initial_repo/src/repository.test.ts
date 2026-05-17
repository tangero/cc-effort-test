import { listInvoicesForTenant, seedData } from './repository';

test('lists invoice data with customer names', () => {
  seedData({
    customers: [{ id: 'c1', tenantId: 't1', name: 'Acme' }],
    invoices: [{ id: 'i1', tenantId: 't1', customerId: 'c1', total: 100 }],
  });

  expect(listInvoicesForTenant('t1')).toEqual([
    { id: 'i1', tenantId: 't1', customerId: 'c1', total: 100, customerName: 'Acme' },
  ]);
});
