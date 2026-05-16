import request from 'supertest';
import express from 'express';
import { router } from './users';

const app = express();
app.use(express.json());
app.use('/users', router);

describe('Users API', () => {
  test('GET /users/search returns users', async () => {
    const res = await request(app).get('/users/search?username=alice');
    expect(res.status).toBe(200);
    expect(res.body).toBeInstanceOf(Array);
  });

  test('POST /users/login succeeds with correct credentials', async () => {
    const res = await request(app).post('/users/login').send({ username: 'alice', password: 'alice456' });
    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
  });

  test('POST /users/login fails with wrong credentials', async () => {
    const res = await request(app).post('/users/login').send({ username: 'alice', password: 'wrong' });
    expect(res.status).toBe(401);
  });
});
