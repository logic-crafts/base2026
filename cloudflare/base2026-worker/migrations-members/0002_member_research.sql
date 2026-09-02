-- Private AUTH_DB member data. Every row carries its owner for defense in
-- depth; request handlers still scope every read/write by the authenticated id.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS research_collections (
  id TEXT PRIMARY KEY NOT NULL,
  userId TEXT NOT NULL,
  name TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 80),
  createdAt INTEGER NOT NULL,
  updatedAt INTEGER NOT NULL,
  FOREIGN KEY (userId) REFERENCES user (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS research_collections_userId_idx
  ON research_collections (userId, updatedAt DESC);

CREATE TABLE IF NOT EXISTS research_items (
  id TEXT PRIMARY KEY NOT NULL,
  userId TEXT NOT NULL,
  collectionId TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind = 'evidence'),
  referenceId TEXT NOT NULL,
  title TEXT NOT NULL,
  url TEXT NOT NULL,
  note TEXT CHECK (note IS NULL OR length(note) <= 2000),
  createdAt INTEGER NOT NULL,
  updatedAt INTEGER NOT NULL,
  FOREIGN KEY (userId) REFERENCES user (id) ON DELETE CASCADE,
  FOREIGN KEY (collectionId) REFERENCES research_collections (id) ON DELETE CASCADE,
  UNIQUE (collectionId, kind, referenceId)
);

CREATE INDEX IF NOT EXISTS research_items_userId_idx
  ON research_items (userId, updatedAt DESC);

CREATE INDEX IF NOT EXISTS research_items_collectionId_idx
  ON research_items (collectionId, createdAt ASC);
