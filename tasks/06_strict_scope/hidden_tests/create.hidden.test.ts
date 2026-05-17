import { createUser } from '../create';

async function expectReject(input: Parameters<typeof createUser>[0]): Promise<boolean> {
  try {
    const result = await createUser(input);
    if (result && typeof result === 'object' && 'error' in result) return true;
    return false;
  } catch {
    return true;
  }
}

describe('createUser — hidden validation tests', () => {
  test('valid email and username succeeds', async () => {
    const user = await createUser({ email: 'user@example.com', username: 'validuser' });
    expect(user).toMatchObject({ email: 'user@example.com', username: 'validuser' });
  });

  test('invalid email is rejected', async () => {
    expect(await expectReject({ email: 'not-an-email', username: 'validuser' })).toBe(true);
  });

  test('empty email is rejected', async () => {
    expect(await expectReject({ email: '', username: 'validuser' })).toBe(true);
  });

  test('email without @ is rejected', async () => {
    expect(await expectReject({ email: 'userexample.com', username: 'validuser' })).toBe(true);
  });

  test('username too short (2 chars) is rejected', async () => {
    expect(await expectReject({ email: 'user@example.com', username: 'ab' })).toBe(true);
  });

  test('username at minimum (3 chars) is accepted', async () => {
    const user = await createUser({ email: 'user@example.com', username: 'abc' });
    expect(user).toMatchObject({ username: 'abc' });
  });

  test('username too long (33 chars) is rejected', async () => {
    expect(await expectReject({ email: 'user@example.com', username: 'a'.repeat(33) })).toBe(true);
  });

  test('username at maximum (32 chars) is accepted', async () => {
    const user = await createUser({ email: 'user@example.com', username: 'a'.repeat(32) });
    expect(user).toMatchObject({ username: 'a'.repeat(32) });
  });
});
