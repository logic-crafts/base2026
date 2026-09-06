-- Index projected-source video lookups without changing admission predicates.
-- Allow migration after the same index has already been created operationally.
CREATE INDEX IF NOT EXISTS idx_search_documents_public_video_id
  ON search_documents (video_id)
  WHERE full_transcript_public = 0;
