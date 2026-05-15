import { createUser } from '../create';
import { updateUser } from '../update';

describe('createUser', () => {
  test('creates user with valid input', async () => {
    const user = await createUser({ email: 'test@example.com', username: 'testuser' });
    expect(user.email).toBe('test@example.com');
    expect(user.username).toBe('testuser');
    expect(user.id).toBeDefined();
  });
});

describe('updateUser', () => {
  test('updates user email', async () => {
    const user = await updateUser('user-1', { email: 'new@example.com' });
    expect(user.email).toBe('new@example.com');
  });
});
