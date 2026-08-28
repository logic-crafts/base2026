-- Base2026 Outreach public search schema (local/preview only).
--
-- This migration is deliberately separate from the TikTok/public-evidence
-- database in ``migrations/`` and from the private inbox in
-- ``migrations-inbox/``.  It contains only the reviewed Outreach finding
-- projection.  The importer writes topics_json/lanes_json as deterministic
-- search helpers while the link tables remain the facet/source of truth.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS outreach_findings (
  id TEXT PRIMARY KEY NOT NULL,
  collection TEXT NOT NULL CHECK (collection = 'outreach_findings'),
  record_type TEXT NOT NULL CHECK (record_type = 'finding'),
  source_record_id TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  tactic TEXT NOT NULL,
  evidence_summary TEXT NOT NULL,
  verdict TEXT NOT NULL,
  source_url TEXT NOT NULL UNIQUE,
  platform TEXT NOT NULL,
  author_name TEXT NOT NULL DEFAULT '',
  author_handle TEXT NOT NULL DEFAULT '',
  observed_at TEXT NOT NULL,
  score REAL NOT NULL CHECK (score >= 65),
  source_status TEXT NOT NULL CHECK (source_status IN ('Одобрено', 'Одобрено с ограничениями')),
  topics_json TEXT NOT NULL DEFAULT '[]',
  lanes_json TEXT NOT NULL DEFAULT '[]',
  cost TEXT NOT NULL DEFAULT '',
  complexity TEXT NOT NULL DEFAULT '',
  effect_speed TEXT NOT NULL DEFAULT '',
  public_policy TEXT NOT NULL CHECK (public_policy = 'reviewed_outreach_excerpt_v1'),
  reviewed_at TEXT NOT NULL,
  source_hash TEXT NOT NULL CHECK (length(source_hash) = 64),
  dedup_key TEXT NOT NULL CHECK (length(dedup_key) = 64),
  language TEXT NOT NULL CHECK (language = 'ru')
);

CREATE INDEX IF NOT EXISTS idx_outreach_findings_collection
  ON outreach_findings (collection);
CREATE INDEX IF NOT EXISTS idx_outreach_findings_source_record_id
  ON outreach_findings (source_record_id);
CREATE INDEX IF NOT EXISTS idx_outreach_findings_source_url
  ON outreach_findings (source_url);
CREATE INDEX IF NOT EXISTS idx_outreach_findings_platform
  ON outreach_findings (platform);
CREATE INDEX IF NOT EXISTS idx_outreach_findings_source_status
  ON outreach_findings (source_status);
CREATE INDEX IF NOT EXISTS idx_outreach_findings_score
  ON outreach_findings (score);
CREATE INDEX IF NOT EXISTS idx_outreach_findings_observed_at
  ON outreach_findings (observed_at);
CREATE INDEX IF NOT EXISTS idx_outreach_findings_reviewed_at
  ON outreach_findings (reviewed_at);
CREATE INDEX IF NOT EXISTS idx_outreach_findings_dedup_key
  ON outreach_findings (dedup_key);

CREATE TABLE IF NOT EXISTS outreach_topics (
  finding_id TEXT NOT NULL,
  topic TEXT NOT NULL,
  PRIMARY KEY (finding_id, topic),
  FOREIGN KEY (finding_id) REFERENCES outreach_findings (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_outreach_topics_topic
  ON outreach_topics (topic);
CREATE INDEX IF NOT EXISTS idx_outreach_topics_finding_id
  ON outreach_topics (finding_id);

CREATE TABLE IF NOT EXISTS outreach_lanes (
  finding_id TEXT NOT NULL,
  lane TEXT NOT NULL,
  PRIMARY KEY (finding_id, lane),
  FOREIGN KEY (finding_id) REFERENCES outreach_findings (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_outreach_lanes_lane
  ON outreach_lanes (lane);
CREATE INDEX IF NOT EXISTS idx_outreach_lanes_finding_id
  ON outreach_lanes (finding_id);

-- External-content FTS5 keeps the exact public row in one ordinary table.  The
-- JSON helper columns carry deterministic topic/lane terms into FTS while the
-- normalized link tables above provide precise facet joins.
CREATE VIRTUAL TABLE IF NOT EXISTS outreach_findings_fts USING fts5(
  title,
  summary,
  tactic,
  evidence_summary,
  verdict,
  source_url,
  platform,
  author_name,
  author_handle,
  topics_json,
  lanes_json,
  cost,
  complexity,
  effect_speed,
  content='outreach_findings',
  content_rowid='rowid'
);

CREATE TRIGGER IF NOT EXISTS outreach_findings_ai
AFTER INSERT ON outreach_findings
BEGIN
  INSERT INTO outreach_findings_fts (
    rowid, title, summary, tactic, evidence_summary, verdict, source_url,
    platform, author_name, author_handle, topics_json, lanes_json, cost,
    complexity, effect_speed
  )
  VALUES (
    new.rowid, new.title, new.summary, new.tactic, new.evidence_summary,
    new.verdict, new.source_url, new.platform, new.author_name,
    new.author_handle, new.topics_json, new.lanes_json, new.cost,
    new.complexity, new.effect_speed
  );
END;

CREATE TRIGGER IF NOT EXISTS outreach_findings_ad
AFTER DELETE ON outreach_findings
BEGIN
  INSERT INTO outreach_findings_fts (
    outreach_findings_fts, rowid, title, summary, tactic, evidence_summary,
    verdict, source_url, platform, author_name, author_handle, topics_json,
    lanes_json, cost, complexity, effect_speed
  )
  VALUES (
    'delete', old.rowid, old.title, old.summary, old.tactic,
    old.evidence_summary, old.verdict, old.source_url, old.platform,
    old.author_name, old.author_handle, old.topics_json, old.lanes_json,
    old.cost, old.complexity, old.effect_speed
  );
END;

CREATE TRIGGER IF NOT EXISTS outreach_findings_au
AFTER UPDATE ON outreach_findings
BEGIN
  INSERT INTO outreach_findings_fts (
    outreach_findings_fts, rowid, title, summary, tactic, evidence_summary,
    verdict, source_url, platform, author_name, author_handle, topics_json,
    lanes_json, cost, complexity, effect_speed
  )
  VALUES (
    'delete', old.rowid, old.title, old.summary, old.tactic,
    old.evidence_summary, old.verdict, old.source_url, old.platform,
    old.author_name, old.author_handle, old.topics_json, old.lanes_json,
    old.cost, old.complexity, old.effect_speed
  );
  INSERT INTO outreach_findings_fts (
    rowid, title, summary, tactic, evidence_summary, verdict, source_url,
    platform, author_name, author_handle, topics_json, lanes_json, cost,
    complexity, effect_speed
  )
  VALUES (
    new.rowid, new.title, new.summary, new.tactic, new.evidence_summary,
    new.verdict, new.source_url, new.platform, new.author_name,
    new.author_handle, new.topics_json, new.lanes_json, new.cost,
    new.complexity, new.effect_speed
  );
END;
