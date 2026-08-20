-- Align the FTS external-content column names with search_documents.
-- This keeps rebuild/content-backed FTS operations valid on D1.

DROP TRIGGER IF EXISTS search_documents_ai;
DROP TRIGGER IF EXISTS search_documents_ad;
DROP TRIGGER IF EXISTS search_documents_au;
DROP TABLE IF EXISTS search_documents_fts;

CREATE VIRTUAL TABLE search_documents_fts USING fts5(
  body,
  title,
  topic_labels_json,
  handle,
  creator_id,
  platform,
  content='search_documents',
  content_rowid='rowid'
);

CREATE TRIGGER search_documents_ai
AFTER INSERT ON search_documents
BEGIN
  INSERT INTO search_documents_fts (rowid, body, title, topic_labels_json, handle, creator_id, platform)
  VALUES (new.rowid, new.body, new.title, new.topic_labels_json, new.handle, new.creator_id, new.platform);
END;

CREATE TRIGGER search_documents_ad
AFTER DELETE ON search_documents
BEGIN
  INSERT INTO search_documents_fts (search_documents_fts, rowid, body, title, topic_labels_json, handle, creator_id, platform)
  VALUES ('delete', old.rowid, old.body, old.title, old.topic_labels_json, old.handle, old.creator_id, old.platform);
END;

CREATE TRIGGER search_documents_au
AFTER UPDATE ON search_documents
BEGIN
  INSERT INTO search_documents_fts (search_documents_fts, rowid, body, title, topic_labels_json, handle, creator_id, platform)
  VALUES ('delete', old.rowid, old.body, old.title, old.topic_labels_json, old.handle, old.creator_id, old.platform);
  INSERT INTO search_documents_fts (rowid, body, title, topic_labels_json, handle, creator_id, platform)
  VALUES (new.rowid, new.body, new.title, new.topic_labels_json, new.handle, new.creator_id, new.platform);
END;

INSERT INTO search_documents_fts(search_documents_fts) VALUES('rebuild');
