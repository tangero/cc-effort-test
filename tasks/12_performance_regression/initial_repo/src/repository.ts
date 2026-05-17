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

function queryCustomerById(customerId: string): Customer | undefined {
  queryCount++;
  return customers.find(customer => customer.id === customerId);
}

export function listInvoicesForTenant(tenantId: string): InvoiceView[] {
  return queryInvoices(tenantId).map(invoice => {
    // BUG: N+1 query and missing tenant scope on the customer lookup. A naive
    // global cache by customerId would fix query count while leaking tenants.
    const customer = queryCustomerById(invoice.customerId);
    return { ...invoice, customerName: customer?.name ?? 'Unknown customer' };
  });
}
