import Database from 'better-sqlite3';

export const db = new Database(':memory:');

db.exec(`
  CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    email TEXT
  );
  INSERT INTO users (username, password, role, email)
    VALUES ('admin', 'secret123', 'admin', 'admin@example.com');
  INSERT INTO users (username, password, role, email)
    VALUES ('alice', 'alice456', 'user', 'alice@example.com');
`);
