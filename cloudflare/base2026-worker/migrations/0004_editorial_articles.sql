-- Additive editorial storage only. No change to evidence/search corpus tables.
-- Payloads are validated public DTOs, never authoring/review prompts or transcripts.

CREATE TABLE editorial_articles (
  slug TEXT PRIMARY KEY NOT NULL
    CHECK (length(slug) BETWEEN 1 AND 120 AND slug NOT GLOB '*[^a-z0-9-]*'
      AND substr(slug, 1, 1) <> '-' AND substr(slug, -1) <> '-' AND instr(slug, '--') = 0),
  revision INTEGER NOT NULL CHECK (typeof(revision) = 'integer' AND revision BETWEEN 1 AND 9007199254740991),
  payload_sha256 TEXT NOT NULL CHECK (length(payload_sha256) = 64 AND payload_sha256 NOT GLOB '*[^a-f0-9]*'),
  payload_json TEXT NOT NULL CHECK (json_valid(payload_json) AND length(CAST(payload_json AS BLOB)) <= 131072),
  published_at TEXT NOT NULL CHECK (length(published_at) = 24 AND julianday(published_at) IS NOT NULL),
  updated_at TEXT NOT NULL CHECK (length(updated_at) = 24 AND julianday(updated_at) IS NOT NULL AND updated_at >= published_at),
  created_at TEXT NOT NULL CHECK (length(created_at) = 24 AND julianday(created_at) IS NOT NULL),
  stored_at TEXT NOT NULL CHECK (length(stored_at) = 24 AND julianday(stored_at) IS NOT NULL AND stored_at >= created_at),
  CHECK (json_type(payload_json, '$.schema_version') IS 'text' AND json_extract(payload_json, '$.schema_version') = 'base2026.editorial.v1'),
  CHECK (json_type(payload_json, '$.slug') IS 'text' AND json_extract(payload_json, '$.slug') = slug),
  CHECK (json_type(payload_json, '$.revision') IS 'integer' AND json_extract(payload_json, '$.revision') = revision),
  CHECK (json_type(payload_json, '$.published_at') IS 'text' AND json_extract(payload_json, '$.published_at') = published_at),
  CHECK (json_type(payload_json, '$.updated_at') IS 'text' AND json_extract(payload_json, '$.updated_at') = updated_at)
);

CREATE INDEX editorial_articles_publication_order ON editorial_articles (published_at DESC, slug ASC);

-- One receipt per applied revision. Replays/conflicts do not append receipts.
-- The application inserts this immediately after its conditional article
-- mutation in a D1 batch, guarded by SQLite changes() = 1.
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
