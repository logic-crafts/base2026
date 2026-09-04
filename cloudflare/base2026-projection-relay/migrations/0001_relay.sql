CREATE TABLE IF NOT EXISTS relay_nonces (
  nonce_sha256 TEXT PRIMARY KEY NOT NULL CHECK (length(nonce_sha256) = 64),
  operation TEXT NOT NULL CHECK (operation IN (
    'projection_apply', 'projection_rollback', 'projection_presence',
    'projection_verify', 'editorial_publish', 'editorial_inspect'
  )),
  idempotency_key TEXT NOT NULL CHECK (length(idempotency_key) = 40),
  created_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL CHECK (expires_at > created_at)
);

CREATE INDEX IF NOT EXISTS relay_nonces_expires_at_idx ON relay_nonces (expires_at);

CREATE TABLE IF NOT EXISTS relay_audit_receipts (
  receipt_id TEXT PRIMARY KEY NOT NULL CHECK (length(receipt_id) = 64),
  nonce_sha256 TEXT NOT NULL CHECK (length(nonce_sha256) = 64),
  operation TEXT NOT NULL CHECK (operation IN (
    'projection_apply', 'projection_rollback', 'projection_presence',
    'projection_verify', 'editorial_publish', 'editorial_inspect'
  )),
  idempotency_key TEXT NOT NULL CHECK (length(idempotency_key) = 40),
  request_sha256 TEXT NOT NULL CHECK (length(request_sha256) = 64),
  outcome TEXT NOT NULL CHECK (outcome IN (
    'accepted', 'replay_rejected', 'target_unconfirmed', 'target_rejected',
    'applied', 'rolled_back', 'presence', 'verified',
    'editorial_published', 'editorial_inspected'
  )),
  result_sha256 TEXT CHECK (result_sha256 IS NULL OR length(result_sha256) = 64),
  created_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS relay_audit_created_at_idx ON relay_audit_receipts (created_at);
