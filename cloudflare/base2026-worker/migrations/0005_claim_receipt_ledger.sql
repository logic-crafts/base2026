-- Additive public claim-receipt ledger for the bounded internal-linking
-- canary.  Only public projection identities, attribution and bounded
-- evidence are stored here; private import receipts and source vault fields
-- have no columns in this table.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS public_claim_receipts (
  receipt_id TEXT PRIMARY KEY NOT NULL
    CHECK (length(receipt_id) = 64 AND receipt_id NOT GLOB '*[^a-f0-9]*'),
  canary_id TEXT NOT NULL
    CHECK (length(canary_id) BETWEEN 1 AND 160),
  selection_rank INTEGER NOT NULL
    CHECK (typeof(selection_rank) = 'integer' AND selection_rank BETWEEN 1 AND 10),
  source_id TEXT NOT NULL,
  projection_id TEXT NOT NULL
    CHECK (length(projection_id) = 40 AND projection_id NOT GLOB '*[^a-f0-9]*'),
  card_id TEXT NOT NULL
    CHECK (length(card_id) = 40 AND card_id NOT GLOB '*[^a-f0-9]*'),
  search_id TEXT NOT NULL
    CHECK (length(search_id) = 40 AND search_id NOT GLOB '*[^a-f0-9]*'),
  card_ordinal INTEGER NOT NULL
    CHECK (typeof(card_ordinal) = 'integer' AND card_ordinal BETWEEN 0 AND 2),
  creator_handle TEXT NOT NULL,
  creator_display_name TEXT NOT NULL DEFAULT '',
  creator_url TEXT NOT NULL,
  original_url TEXT NOT NULL,
  video_id TEXT NOT NULL,
  base2026_url TEXT NOT NULL,
  published_at TEXT NOT NULL,
  published_date TEXT NOT NULL,
  claim_text TEXT NOT NULL,
  suggested_action TEXT NOT NULL,
  topic_label TEXT NOT NULL,
  evidence_excerpt TEXT NOT NULL,
  evidence_start_seconds REAL NOT NULL CHECK (evidence_start_seconds >= 0),
  evidence_end_seconds REAL NOT NULL CHECK (evidence_end_seconds >= evidence_start_seconds),
  public_projection_receipt_sha256 TEXT NOT NULL
    CHECK (length(public_projection_receipt_sha256) = 64
      AND public_projection_receipt_sha256 NOT GLOB '*[^a-f0-9]*'),
  policy_version TEXT NOT NULL,
  ledger_sha256 TEXT NOT NULL
    CHECK (length(ledger_sha256) = 64 AND ledger_sha256 NOT GLOB '*[^a-f0-9]*'),
  state TEXT NOT NULL DEFAULT 'active'
    CHECK (state IN ('active', 'superseded', 'removed', 'rolled_back')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (canary_id, selection_rank),
  UNIQUE (canary_id, card_id),
  UNIQUE (canary_id, source_id)
);

CREATE INDEX IF NOT EXISTS idx_public_claim_receipts_canary_state
  ON public_claim_receipts (canary_id, state, selection_rank);

CREATE INDEX IF NOT EXISTS idx_public_claim_receipts_source
  ON public_claim_receipts (source_id, state);

CREATE INDEX IF NOT EXISTS idx_public_claim_receipts_creator
  ON public_claim_receipts (creator_handle, state);
