-- Restore the legacy Sol-only receipt contract after a pre-Astra rollback.
-- Apply all three statements in one atomic D1 batch; do not split them.
ALTER TABLE editorial_publication_receipts
  RENAME TO editorial_publication_receipts_astra_rollback_0007;

CREATE TABLE editorial_publication_receipts (
  slug TEXT NOT NULL,
  revision INTEGER NOT NULL CHECK (typeof(revision) = 'integer' AND revision BETWEEN 1 AND 9007199254740991),
  payload_sha256 TEXT NOT NULL CHECK (length(payload_sha256) = 64 AND payload_sha256 NOT GLOB '*[^a-f0-9]*'),
  published_at TEXT NOT NULL CHECK (length(published_at) = 24 AND julianday(published_at) IS NOT NULL),
  updated_at TEXT NOT NULL CHECK (length(updated_at) = 24 AND julianday(updated_at) IS NOT NULL AND updated_at >= published_at),
  reviewer TEXT NOT NULL CHECK (reviewer = 'sol-max'),
  reviewed_at TEXT NOT NULL CHECK (length(reviewed_at) = 24 AND julianday(reviewed_at) IS NOT NULL AND reviewed_at >= published_at),
  recorded_at TEXT NOT NULL CHECK (length(recorded_at) = 24 AND julianday(recorded_at) IS NOT NULL AND recorded_at >= reviewed_at),
  PRIMARY KEY (slug, revision),
  FOREIGN KEY (slug) REFERENCES editorial_articles (slug)
);

INSERT INTO editorial_publication_receipts
  (slug, revision, payload_sha256, published_at, updated_at, reviewer, reviewed_at, recorded_at)
SELECT slug, revision, payload_sha256, published_at, updated_at, reviewer, reviewed_at, recorded_at
  FROM editorial_publication_receipts_astra_rollback_0007;
