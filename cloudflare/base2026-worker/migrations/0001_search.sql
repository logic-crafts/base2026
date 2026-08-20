-- Base2026 public search schema.
-- Only reviewed public chunks are admitted. Raw captions, ASR, media and
-- private pipeline fields have no columns in this schema.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS search_documents (
  id TEXT PRIMARY KEY NOT NULL,
  item_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  chunk_id TEXT NOT NULL,
  chunk_index INTEGER NOT NULL DEFAULT 0,
  body TEXT NOT NULL,
  captured_at TEXT NOT NULL DEFAULT '',
  creator_display_name TEXT NOT NULL DEFAULT '',
  creator_handle TEXT NOT NULL DEFAULT '',
  creator_id TEXT NOT NULL DEFAULT '',
  creator_url TEXT NOT NULL DEFAULT '',
  full_transcript_public INTEGER NOT NULL DEFAULT 0 CHECK (full_transcript_public IN (0, 1)),
  handle TEXT NOT NULL DEFAULT '',
  platform TEXT NOT NULL DEFAULT '',
  post_id TEXT NOT NULL DEFAULT '',
  public_policy TEXT NOT NULL DEFAULT '',
  public_surface TEXT NOT NULL DEFAULT '',
  published_at TEXT NOT NULL DEFAULT '',
  published_date TEXT NOT NULL DEFAULT '',
  source_type TEXT NOT NULL DEFAULT '',
  source_url TEXT NOT NULL DEFAULT '',
  title TEXT NOT NULL DEFAULT '',
  title_source TEXT NOT NULL DEFAULT '',
  title_status TEXT NOT NULL DEFAULT '',
  video_id TEXT NOT NULL DEFAULT '',
  year TEXT NOT NULL DEFAULT '',
  avatar_url TEXT NOT NULL DEFAULT '',
  topics_json TEXT NOT NULL DEFAULT '[]',
  topic_labels_json TEXT NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_search_documents_item_id
  ON search_documents (item_id);
CREATE INDEX IF NOT EXISTS idx_search_documents_source_id
  ON search_documents (source_id);
CREATE INDEX IF NOT EXISTS idx_search_documents_platform
  ON search_documents (platform);
CREATE INDEX IF NOT EXISTS idx_search_documents_source_type
  ON search_documents (source_type);
CREATE INDEX IF NOT EXISTS idx_search_documents_creator_id
  ON search_documents (creator_id);
CREATE INDEX IF NOT EXISTS idx_search_documents_handle
  ON search_documents (handle);
CREATE INDEX IF NOT EXISTS idx_search_documents_year
  ON search_documents (year);
CREATE INDEX IF NOT EXISTS idx_search_documents_published_date
  ON search_documents (published_date);

CREATE TABLE IF NOT EXISTS search_topics (
  document_id TEXT NOT NULL,
  topic_id TEXT NOT NULL,
  topic_label TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (document_id, topic_id),
  FOREIGN KEY (document_id) REFERENCES search_documents (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_search_topics_topic_id
  ON search_topics (topic_id);
CREATE INDEX IF NOT EXISTS idx_search_topics_document_id
  ON search_topics (document_id);

-- External-content FTS5 keeps the public row shape in one ordinary table while
-- indexing exactly the fields configured by the existing Meilisearch export.
CREATE VIRTUAL TABLE IF NOT EXISTS search_documents_fts USING fts5(
  body,
  title,
  topic_labels_json,
  handle,
  creator_id,
  platform,
  content='search_documents',
  content_rowid='rowid'
);

CREATE TRIGGER IF NOT EXISTS search_documents_ai
AFTER INSERT ON search_documents
BEGIN
  INSERT INTO search_documents_fts (rowid, body, title, topic_labels_json, handle, creator_id, platform)
  VALUES (new.rowid, new.body, new.title, new.topic_labels_json, new.handle, new.creator_id, new.platform);
END;

CREATE TRIGGER IF NOT EXISTS search_documents_ad
AFTER DELETE ON search_documents
BEGIN
  INSERT INTO search_documents_fts (search_documents_fts, rowid, body, title, topic_labels_json, handle, creator_id, platform)
  VALUES ('delete', old.rowid, old.body, old.title, old.topic_labels_json, old.handle, old.creator_id, old.platform);
END;

CREATE TRIGGER IF NOT EXISTS search_documents_au
AFTER UPDATE ON search_documents
BEGIN
  INSERT INTO search_documents_fts (search_documents_fts, rowid, body, title, topic_labels_json, handle, creator_id, platform)
  VALUES ('delete', old.rowid, old.body, old.title, old.topic_labels_json, old.handle, old.creator_id, old.platform);
  INSERT INTO search_documents_fts (rowid, body, title, topic_labels_json, handle, creator_id, platform)
  VALUES (new.rowid, new.body, new.title, new.topic_labels_json, new.handle, new.creator_id, new.platform);
END;
