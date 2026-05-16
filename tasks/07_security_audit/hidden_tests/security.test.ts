import request from 'supertest';
import express from 'express';
import { router } from './users';

const app = express();
app.use(express.json());
app.use('/users', router);

describe('Security checks', () => {
  test('SQL injection in search is blocked', async () => {
    // If the vulnerability is fixed, this returns an empty array (not all users)
    const res = await request(app).get("/users/search?username=' OR '1'='1");
    expect(res.status).toBe(200);
    // Prepared statements return an empty array (no user has such a username)
    expect(res.body).toHaveLength(0);
  });

  test('SQL injection in login is blocked', async () => {
    // Classic bypass: ' OR '1'='1
    const res = await request(app).post('/users/login').send({
      username: "' OR '1'='1",
      password: "' OR '1'='1"
    });
    expect(res.status).toBe(401);
  });

  test('GET /users/:id does not return password', async () => {
    const res = await request(app).get('/users/1');
    expect(res.status).toBe(200);
    expect(res.body).not.toHaveProperty('password');
  });

  test('POST /users/register does not reflect XSS', async () => {
    const res = await request(app).post('/users/register').send({
      username: 'x',  // too short -> triggers error response
      email: 'test@test.com'
    });
    // Response must not be HTML with unescaped input
    expect(res.headers['content-type']).not.toMatch(/html/);
  });

  test('PUT /users/:id ignores role field', async () => {
    await request(app).put('/users/2').send({ username: 'alice', email: 'alice@example.com', role: 'admin' });
    // After update alice should still be 'user', not 'admin'
    const loginRes = await request(app).post('/users/login').send({ username: 'alice', password: 'alice456' });
    expect(loginRes.body.user?.role).toBe('user');
  });
});
