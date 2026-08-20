CREATE TABLE IF NOT EXISTS project_inbox (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('support', 'partner')),
  submitted_at TEXT NOT NULL,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  organization TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT '',
  category TEXT NOT NULL,
  public_url TEXT NOT NULL DEFAULT '',
  proposal_json TEXT NOT NULL,
  attribution TEXT NOT NULL CHECK (attribution IN ('discuss', 'yes', 'no')),
  consent_version TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'active', 'closed', 'deleted'))
);

CREATE INDEX IF NOT EXISTS project_inbox_submitted_at_idx ON project_inbox(submitted_at);
CREATE INDEX IF NOT EXISTS project_inbox_kind_status_idx ON project_inbox(kind, status);
