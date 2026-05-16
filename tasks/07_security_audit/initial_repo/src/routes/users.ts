import { Router, Request, Response } from 'express';
import { db } from '../db';

export const router = Router();

// BUG 1 (obvious): SQL injection — username from query parameter directly into SQL
router.get('/search', (req: Request, res: Response) => {
  const username = req.query.username as string;
  const users = db.prepare(`SELECT id, username, email FROM users WHERE username LIKE '%${username}%'`).all();
  res.json(users);
});

// BUG 2 (obvious): SQL injection in login — password directly into SQL
router.post('/login', (req: Request, res: Response) => {
  const { username, password } = req.body;
  const user = db.prepare(`SELECT * FROM users WHERE username = '${username}' AND password = '${password}'`).get();
  if (user) {
    res.json({ success: true, user });
  } else {
    res.status(401).json({ success: false });
  }
});

// BUG 3 (medium): Missing authorization — any user can see another user including password
router.get('/:id', (req: Request, res: Response) => {
  const user = db.prepare('SELECT * FROM users WHERE id = ?').get(req.params.id);
  if (!user) return res.status(404).json({ error: 'Not found' });
  res.json(user);  // returns password too!
});

// BUG 4 (medium): Reflected XSS — error message contains unescaped user input
router.post('/register', (req: Request, res: Response) => {
  const { username, email } = req.body;
  if (!username || username.length < 3) {
    // Returns raw user input in HTML error message
    return res.status(400).send(`<p>Invalid username: ${username}</p>`);
  }
  try {
    db.prepare('INSERT INTO users (username, password, role, email) VALUES (?, ?, ?, ?)').run(username, 'changeme', 'user', email);
    res.status(201).json({ success: true });
  } catch {
    res.status(409).json({ error: 'Username taken' });
  }
});

// BUG 5 (hidden): Mass assignment — role can be set via body even for normal registration
router.put('/:id', (req: Request, res: Response) => {
  const { username, email, role } = req.body;  // role should not be accepted from request!
  db.prepare('UPDATE users SET username = ?, email = ?, role = ? WHERE id = ?').run(username, email, role, req.params.id);
  res.json({ success: true });
});
