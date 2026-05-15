export const isEmail = (s: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s);
export const isUUID = (s: string) => /^[0-9a-f-]{36}$/.test(s);
export const isPositive = (n: number) => typeof n === 'number' && n > 0;
export const isNonEmpty = (s: string) => typeof s === 'string' && s.trim().length > 0;
export const ORDER_STATUSES = ['pending', 'processing', 'shipped', 'delivered', 'cancelled'] as const;
export type OrderStatus = typeof ORDER_STATUSES[number];
export const isOrderStatus = (s: string): s is OrderStatus =>
  ORDER_STATUSES.includes(s as OrderStatus);
