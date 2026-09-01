-- Better Auth 1.7.2 SQLite/D1 schema for the private member database.
-- This database is intentionally separate from public DB/INBOX_DB/OUTREACH_DB.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS user (
  id TEXT PRIMARY KEY NOT NULL,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  emailVerified INTEGER NOT NULL DEFAULT 0,
  image TEXT,
  createdAt INTEGER NOT NULL,
  updatedAt INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS session (
  id TEXT PRIMARY KEY NOT NULL,
  expiresAt INTEGER NOT NULL,
  token TEXT NOT NULL UNIQUE,
  createdAt INTEGER NOT NULL,
  updatedAt INTEGER NOT NULL,
  ipAddress TEXT,
  userAgent TEXT,
  userId TEXT NOT NULL,
  FOREIGN KEY (userId) REFERENCES user (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS session_userId_idx ON session (userId);

CREATE TABLE IF NOT EXISTS account (
  id TEXT PRIMARY KEY NOT NULL,
  issuer TEXT NOT NULL,
  accountId TEXT NOT NULL,
  providerId TEXT NOT NULL,
  userId TEXT NOT NULL,
  accessToken TEXT,
  refreshToken TEXT,
  idToken TEXT,
  accessTokenExpiresAt INTEGER,
  refreshTokenExpiresAt INTEGER,
  scope TEXT,
  password TEXT,
  createdAt INTEGER NOT NULL,
  updatedAt INTEGER NOT NULL,
  FOREIGN KEY (userId) REFERENCES user (id) ON DELETE CASCADE,
  UNIQUE (issuer, accountId)
);

CREATE INDEX IF NOT EXISTS account_userId_idx ON account (userId);

CREATE TABLE IF NOT EXISTS verification (
  id TEXT PRIMARY KEY NOT NULL,
  identifier TEXT NOT NULL,
  value TEXT NOT NULL,
  expiresAt INTEGER NOT NULL,
  createdAt INTEGER NOT NULL,
  updatedAt INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS verification_identifier_idx ON verification (identifier);

-- Atomic Better Auth/member rate-limit counters. Key values are HMAC-SHA-256 digests;
-- no request IP or user-agent is persisted in this table.
CREATE TABLE IF NOT EXISTS member_rate_limits (
  key TEXT PRIMARY KEY NOT NULL,
  windowStarted INTEGER NOT NULL,
  count INTEGER NOT NULL CHECK (count >= 0),
  updatedAt INTEGER NOT NULL
);
