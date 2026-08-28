-- Controlled private-to-public projection receipts and card-level search rows.
-- The projection lane is intentionally separate from the private pipeline
-- database. Only excerpt/evidence card fields are admitted here.

ALTER TABLE search_documents
  ADD COLUMN admission_state TEXT NOT NULL DEFAULT 'normal_public_card';

ALTER TABLE search_documents
  ADD COLUMN projection_id TEXT NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_search_documents_projection_id
  ON search_documents (projection_id);

CREATE TABLE IF NOT EXISTS public_projection_receipts (
  projection_id TEXT PRIMARY KEY NOT NULL,
  source_id TEXT NOT NULL,
  manifest_sha256 TEXT NOT NULL,
  content_sha256 TEXT NOT NULL,
  private_import_receipt_sha256 TEXT NOT NULL,
  card_count INTEGER NOT NULL CHECK (card_count BETWEEN 1 AND 3),
  status TEXT NOT NULL DEFAULT 'applied' CHECK (status IN ('applied', 'rolled_back')),
  receipt_sha256 TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (source_id, manifest_sha256)
);

CREATE INDEX IF NOT EXISTS idx_public_projection_receipts_source
  ON public_projection_receipts (source_id);

CREATE INDEX IF NOT EXISTS idx_public_projection_receipts_manifest
  ON public_projection_receipts (manifest_sha256);

CREATE UNIQUE INDEX IF NOT EXISTS idx_public_projection_receipts_active_source
  ON public_projection_receipts (source_id)
  WHERE status = 'applied';

-- Keep the admitted card fields and timecodes in a separate public audit
-- ledger. Search documents intentionally contain only the excerpt/title
-- projection and never the private source text or source questions.
CREATE TABLE IF NOT EXISTS public_projection_cards (
  projection_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  ordinal INTEGER NOT NULL CHECK (ordinal BETWEEN 0 AND 2),
  card_id TEXT PRIMARY KEY NOT NULL,
  search_id TEXT NOT NULL UNIQUE,
  claim_text TEXT NOT NULL,
  suggested_action TEXT NOT NULL,
  topic_label TEXT NOT NULL,
  evidence_excerpt TEXT NOT NULL,
  evidence_start_seconds REAL NOT NULL CHECK (evidence_start_seconds >= 0),
  evidence_end_seconds REAL NOT NULL CHECK (evidence_end_seconds >= evidence_start_seconds),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (projection_id, ordinal),
  FOREIGN KEY (projection_id) REFERENCES public_projection_receipts (projection_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_public_projection_cards_projection
  ON public_projection_cards (projection_id, ordinal);

CREATE INDEX IF NOT EXISTS idx_public_projection_cards_source
  ON public_projection_cards (source_id);
