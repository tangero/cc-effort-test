export type Invoice = { id: string; tenantId: string; customerId: string; total: number };
export type Customer = { id: string; tenantId: string; name: string };
export type InvoiceView = Invoice & { customerName: string };

const invoices: Invoice[] = [];
const customers: Customer[] = [];
let queryCount = 0;

export function seedData(input: { invoices: Invoice[]; customers: Customer[] }): void {
  invoices.splice(0, invoices.length, ...input.invoices);
  customers.splice(0, customers.length, ...input.customers);
  queryCount = 0;
}

export function getQueryCount(): number {
  return queryCount;
}

function queryInvoices(tenantId: string): Invoice[] {
  queryCount++;
  return invoices.filter(invoice => invoice.tenantId === tenantId);
}

function queryCustomersByTenant(tenantId: string): Customer[] {
  queryCount++;
  return customers.filter(customer => customer.tenantId === tenantId);
}

export function listInvoicesForTenant(tenantId: string): InvoiceView[] {
  const tenantInvoices = queryInvoices(tenantId);
  const customersById = new Map(
    queryCustomersByTenant(tenantId).map(customer => [customer.id, customer.name])
  );
  return tenantInvoices.map(invoice => ({
    ...invoice,
    customerName: customersById.get(invoice.customerId) ?? 'Unknown customer',
  }));
}
