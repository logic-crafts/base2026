/**
 * Bounded, read-only public evidence pins. No source fetch, model, private
 * database, or semantic approval lives here. A matching quote/hash proves
 * identity and unchanged bytes, not entailment, independence or reuse rights.
 *
 * Keep this module runtime-import-free: the local packet tool loads only this
 * fixed module and editorial.ts, never code named by an input packet.
 */

export const EDITORIAL_EVIDENCE_LIMITS = Object.freeze({
  dependencies: 12,
  user_task: 400,
  quote: 320,
  document_id: 120,
  source_id: 300,
  document_body_bytes: 64 * 1024,
  snapshot_bytes: 1024 * 1024,
});

const VIDEO_ID = /^[0-9]{10,30}$/u;
const SOURCE_ID = /^tiktok:([A-Za-z0-9._-]{2,256}):([0-9]{10,30})$/u;
const CHUNK_ID = /^chunk-transcript(?:-polished)?-([0-9]{10,30})-([0-9]{4})$/u;
const CARD_DOCUMENT_ID = /^[a-f0-9]{40}$/u;
const SHA256 = /^[a-f0-9]{64}$/u;
const encoder = new TextEncoder();

export interface EditorialEvidenceDependency {
  citation_id: string;
  document_id: string;
  source_id: string;
  document_sha256: string;
  quote: string;
  relation: "direct" | "prerequisite";
}

export interface EditorialEvidence {
  user_task: string;
  dependencies: EditorialEvidenceDependency[];
}

/** Exactly the public SQL fields in a pin; extra DTO fields are not hashed. */
export interface PublicEvidenceDocument {
  id: string;
  source_id: string;
  source_url: string;
  creator_handle: string;
  title: string;
  body: string;
  full_transcript_public: boolean | 0 | 1;
  admission_state: string;
}

export type EditorialEvidenceErrorCode =
  | "EDITORIAL_EVIDENCE_DOCUMENT_INVALID"
  | "EDITORIAL_EVIDENCE_DOCUMENT_MISSING"
  | "EDITORIAL_EVIDENCE_SOURCE_MISMATCH"
  | "EDITORIAL_EVIDENCE_HASH_MISMATCH"
  | "EDITORIAL_EVIDENCE_QUOTE_MISMATCH"
  | "EDITORIAL_EVIDENCE_NOT_PUBLIC"
  | "EDITORIAL_EVIDENCE_PROJECTION_INVALID"
  | "EDITORIAL_EVIDENCE_PRIVACY_REJECTED"
  | "EDITORIAL_EVIDENCE_TOO_LARGE"
  | "EDITORIAL_EVIDENCE_SNAPSHOT_CHANGED"
  | "EDITORIAL_EVIDENCE_READ_FAILED";

export class EditorialEvidenceError extends Error {
  constructor(readonly code: EditorialEvidenceErrorCode, readonly field = "payload.evidence.dependencies") {
    // Never include a row, SQL detail, quote, URL or rejected input value.
    super(code);
    this.name = "EditorialEvidenceError";
  }
}

export function isPublicEvidenceDocumentId(value: string): boolean {
  return typeof value === "string" && value.length <= EDITORIAL_EVIDENCE_LIMITS.document_id
    && (CHUNK_ID.test(value) || CARD_DOCUMENT_ID.test(value));
}

export function isPublicEvidenceSourceId(value: string): boolean {
  return typeof value === "string" && value.length <= EDITORIAL_EVIDENCE_LIMITS.source_id && SOURCE_ID.test(value);
}

function fail(code: EditorialEvidenceErrorCode, field?: string): never {
  throw new EditorialEvidenceError(code, field);
}

function exactString(value: unknown, maxBytes: number): string {
  if (typeof value !== "string" || value.length > maxBytes
    || /[\ud800-\udfff]/u.test(value) || encoder.encode(value).byteLength > maxBytes) fail("EDITORIAL_EVIDENCE_DOCUMENT_INVALID");
  return value;
}

function hashFields(row: PublicEvidenceDocument): PublicEvidenceDocument & { full_transcript_public: boolean } {
  if (!row || typeof row !== "object" || Array.isArray(row)) fail("EDITORIAL_EVIDENCE_DOCUMENT_INVALID");
  const flag = row.full_transcript_public;
  if (flag !== false && flag !== true && flag !== 0 && flag !== 1) fail("EDITORIAL_EVIDENCE_DOCUMENT_INVALID");
  // Alphabetical keys, exact strings. Only the SQL integer/public DTO boolean
  // discriminator is normalized. Do not trim, case-fold or normalize Unicode.
  return {
    admission_state: exactString(row.admission_state, 32),
    body: exactString(row.body, EDITORIAL_EVIDENCE_LIMITS.document_body_bytes),
    creator_handle: exactString(row.creator_handle, 257),
    full_transcript_public: flag === true || flag === 1,
    id: exactString(row.id, EDITORIAL_EVIDENCE_LIMITS.document_id),
    source_id: exactString(row.source_id, EDITORIAL_EVIDENCE_LIMITS.source_id),
    source_url: exactString(row.source_url, 2_048),
    title: exactString(row.title, 4_800),
  };
}

/** Stable SHA-256 of the eight sorted public fields, shared by DTO/SQL authors. */
export async function hashPublicEvidenceDocument(row: PublicEvidenceDocument): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", encoder.encode(JSON.stringify(hashFields(row))));
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

type EvidenceDatabase = Pick<D1Database, "prepare">;
type EvidenceCitation = { id: string; url: string };
type PublicTextCheck = (value: string) => void;

interface EvidenceDocumentRow extends PublicEvidenceDocument {
  video_id: string;
  projection_id: string;
  chunk_id: string;
  chunk_index: number;
  public_eligible: number;
  projection_eligible: number;
}

/** Internal SQL parameters only. Never serialize this snapshot into a packet. */
export interface EditorialEvidenceSnapshot { readonly expected_json: string }

// These admission predicates deliberately are not added to the eight-field
// public hash. Recheck them on both the initial read and the atomic guard.
const PUBLIC_DOCUMENT_ELIGIBILITY = `d.full_transcript_public=0 AND d.admission_state='normal_public_card'
  AND d.platform='tiktok' AND d.source_type='tiktok_video'
  AND d.public_policy='search_passage' AND d.public_surface='main_search'`;

// Alias d always denotes one exact requested search document. The bounded
// child counts detect extras without counting an unbounded corrupted cohort.
// Every child must join and satisfy the tuple, not only the cited child.
// Keep AND groups shallow: local D1 enforces expression-tree depth 100, unlike
// default native SQLite. Real-D1 max-dependency tests cover the nested guards.
const PROJECTION_ELIGIBILITY = `(
  (d.projection_id='' AND NOT EXISTS (
    SELECT 1 FROM public_projection_cards orphan WHERE orphan.search_id=d.id
  ) AND NOT EXISTS (
    SELECT 1 FROM public_projection_receipts active
    WHERE active.source_id=d.source_id AND active.status='applied'
  ))
  OR (length(d.projection_id)=40 AND d.projection_id NOT GLOB '*[^0-9a-f]*' AND EXISTS (
    SELECT 1
    FROM public_projection_receipts r
    JOIN public_projection_cards c ON c.projection_id=r.projection_id AND c.source_id=r.source_id
    JOIN search_documents sibling
      ON sibling.id=c.search_id AND sibling.projection_id=r.projection_id AND sibling.source_id=r.source_id
    WHERE (r.projection_id=d.projection_id AND r.source_id=d.source_id
      AND r.status='applied' AND r.card_count BETWEEN 1 AND 3)
      AND (length(r.manifest_sha256)=64 AND r.manifest_sha256 NOT GLOB '*[^0-9a-f]*'
        AND length(r.content_sha256)=64 AND r.content_sha256 NOT GLOB '*[^0-9a-f]*')
      AND (length(r.private_import_receipt_sha256)=64 AND r.private_import_receipt_sha256 NOT GLOB '*[^0-9a-f]*'
        AND length(r.receipt_sha256)=64 AND r.receipt_sha256 NOT GLOB '*[^0-9a-f]*')
      AND (sibling.full_transcript_public=0 AND sibling.admission_state='normal_public_card'
        AND sibling.title=c.claim_text AND sibling.body=c.evidence_excerpt)
      AND (sibling.chunk_id=c.card_id AND sibling.chunk_index=c.ordinal
        AND sibling.video_id=d.video_id AND sibling.creator_handle=d.creator_handle)
      AND (sibling.source_url=d.source_url AND sibling.platform='tiktok' AND sibling.source_type='tiktok_video'
        AND sibling.public_policy='search_passage' AND sibling.public_surface='main_search')
      AND (length(c.card_id)=40 AND c.card_id NOT GLOB '*[^0-9a-f]*'
        AND length(c.search_id)=40 AND c.search_id NOT GLOB '*[^0-9a-f]*')
      AND (length(c.claim_text) BETWEEN 20 AND 360 AND length(c.evidence_excerpt) BETWEEN 20 AND 520
        AND length(c.suggested_action) BETWEEN 20 AND 360 AND length(c.topic_label) BETWEEN 2 AND 120)
      AND (c.evidence_start_seconds>=0 AND c.evidence_end_seconds>c.evidence_start_seconds
        AND c.ordinal BETWEEN 0 AND r.card_count-1)
      AND c.rowid IN (SELECT bounded.rowid FROM public_projection_cards bounded
        WHERE bounded.projection_id=r.projection_id ORDER BY bounded.ordinal LIMIT 4)
    GROUP BY r.projection_id, r.source_id, r.card_count
    HAVING COUNT(*)=r.card_count AND MIN(c.ordinal)=0 AND MAX(c.ordinal)=r.card_count-1
      AND (SELECT COUNT(*) FROM (SELECT 1 FROM public_projection_cards children
        WHERE children.projection_id=r.projection_id LIMIT 4))=r.card_count
      AND (SELECT COUNT(*) FROM (SELECT 1 FROM search_documents documents
        WHERE documents.projection_id=r.projection_id LIMIT 4))=r.card_count
      AND (SELECT COUNT(*) FROM (SELECT 1 FROM search_documents source_documents
        WHERE source_documents.source_id=r.source_id LIMIT 4))=r.card_count
      AND (SELECT COUNT(*) FROM (SELECT 1 FROM public_projection_cards source_cards
        WHERE source_cards.source_id=r.source_id LIMIT 4))=r.card_count
  ))
)`;

const SNAPSHOT_STRING_FIELDS = [
  "id", "source_id", "source_url", "creator_handle", "title", "body", "admission_state",
  "video_id", "projection_id", "chunk_id",
] as const;

/**
 * Recheck the pre-hashed snapshot plus current whole-projection eligibility in
 * the same D1 transaction as the article mutation. The index is code-owned,
 * never packet SQL. SQLite JSON booleans compare to SQL integers here.
 */
export function editorialEvidenceSnapshotGuardSql(parameterIndex: number): string {
  if (!Number.isSafeInteger(parameterIndex) || parameterIndex < 1 || parameterIndex > 100) fail("EDITORIAL_EVIDENCE_DOCUMENT_INVALID");
  return `NOT EXISTS (
    SELECT 1 FROM json_each(?${parameterIndex}) expected
    WHERE NOT EXISTS (
      SELECT 1 FROM search_documents d
      WHERE ${SNAPSHOT_STRING_FIELDS.map((key) => `d.${key}=json_extract(expected.value,'$.${key}')`).join(" AND ")}
        AND d.full_transcript_public=json_extract(expected.value,'$.full_transcript_public')
        AND d.chunk_index=json_extract(expected.value,'$.chunk_index')
        AND ${PUBLIC_DOCUMENT_ELIGIBILITY}
        AND ${PROJECTION_ELIGIBILITY}
    )
  )`;
}

const BOUNDED_COLUMNS = [
  ["id", 120], ["source_id", 300], ["source_url", 2_048], ["creator_handle", 257],
  ["title", 4_800], ["body", EDITORIAL_EVIDENCE_LIMITS.document_body_bytes],
  ["admission_state", 32], ["video_id", 30], ["projection_id", 40], ["chunk_id", 120],
].map(([column, bytes]) => `CASE WHEN length(CAST(d.${column} AS BLOB))<=${bytes} THEN d.${column} ELSE NULL END AS ${column}`).join(", ");

/**
 * Called only with a parsed editorial payload. At most 12 exact-ID rows and
 * 64 KiB per body cross the binding; no corpus scan or title fallback.
 * The required callback reuses editorial.ts's existing privacy/markup gate.
 */
export async function resolveEditorialEvidence(
  db: EvidenceDatabase,
  evidence: EditorialEvidence,
  sources: readonly EvidenceCitation[],
  checkPublicText: PublicTextCheck,
): Promise<EditorialEvidenceSnapshot> {
  const dependencies = evidence.dependencies;
  if (!Array.isArray(dependencies) || dependencies.length < 1 || dependencies.length > EDITORIAL_EVIDENCE_LIMITS.dependencies
    || dependencies.some((item) => !isPublicEvidenceDocumentId(item.document_id))
    || new Set(dependencies.map((item) => item.document_id)).size !== dependencies.length) fail("EDITORIAL_EVIDENCE_DOCUMENT_INVALID");
  let rows: EvidenceDocumentRow[];
  try {
    const result = await db.prepare(`SELECT ${BOUNDED_COLUMNS}, d.full_transcript_public,
        CASE WHEN typeof(d.chunk_index)='integer' AND d.chunk_index BETWEEN 0 AND 9007199254740991
          THEN d.chunk_index ELSE NULL END AS chunk_index,
        CASE WHEN ${PUBLIC_DOCUMENT_ELIGIBILITY} THEN 1 ELSE 0 END AS public_eligible,
        CASE WHEN ${PROJECTION_ELIGIBILITY} THEN 1 ELSE 0 END AS projection_eligible
      FROM search_documents d
      WHERE d.id IN (SELECT value FROM json_each(?1))
      ORDER BY d.id LIMIT ${EDITORIAL_EVIDENCE_LIMITS.dependencies}`)
      .bind(JSON.stringify(dependencies.map((item) => item.document_id))).all<EvidenceDocumentRow>();
    if (!result.success || !Array.isArray(result.results) || result.results.length > dependencies.length) throw new Error("read");
    rows = result.results;
  } catch { fail("EDITORIAL_EVIDENCE_READ_FAILED"); }
  if (rows.some((row) => !row || typeof row !== "object" || Array.isArray(row)
    || !isPublicEvidenceDocumentId(row.id))) fail("EDITORIAL_EVIDENCE_DOCUMENT_INVALID");
  const byId = new Map(rows.map((row) => [row.id, row]));
  if (byId.size !== rows.length) fail("EDITORIAL_EVIDENCE_DOCUMENT_INVALID");
  const expected = [];
  for (const [index, dependency] of dependencies.entries()) {
    const field = `payload.evidence.dependencies[${index}]`;
    const row = byId.get(dependency.document_id);
    if (!row) fail("EDITORIAL_EVIDENCE_DOCUMENT_MISSING", field);
    const fields = hashFields(row);
    if (fields.full_transcript_public || fields.admission_state !== "normal_public_card"
      || row.public_eligible !== 1) fail("EDITORIAL_EVIDENCE_NOT_PUBLIC", field);
    const identity = SOURCE_ID.exec(fields.source_id);
    const chunk = CHUNK_ID.exec(fields.id);
    if (!identity || !VIDEO_ID.test(row.video_id) || identity[2] !== row.video_id
      || fields.creator_handle.replace(/^@/u, "") !== identity[1]
      || ![identity[1], "@" + identity[1]].includes(fields.creator_handle)
      || fields.source_id !== dependency.source_id
      || (chunk && chunk[1] !== row.video_id)) fail("EDITORIAL_EVIDENCE_SOURCE_MISMATCH", field);
    const sourcePath = `/@${identity[1]}/video/${row.video_id}`;
    if (fields.source_url !== "https://www.tiktok.com" + sourcePath
      && fields.source_url !== "https://tiktok.com" + sourcePath) fail("EDITORIAL_EVIDENCE_SOURCE_MISMATCH", field);
    const citation = sources.find((item) => item.id === dependency.citation_id);
    if (!citation || (citation.url !== `https://base2026.dev/sources/tiktok-video-${row.video_id}`
      && citation.url !== fields.source_url)) fail("EDITORIAL_EVIDENCE_SOURCE_MISMATCH", field);
    if (typeof row.projection_id !== "string" || row.projection_eligible !== 1
      || (row.projection_id === "" ? !chunk : !CARD_DOCUMENT_ID.test(fields.id))
      || typeof row.chunk_id !== "string" || !Number.isSafeInteger(row.chunk_index) || row.chunk_index < 0) {
      fail("EDITORIAL_EVIDENCE_PROJECTION_INVALID", field);
    }
    if (chunk && (row.chunk_id !== fields.id || Number(chunk[2]) !== row.chunk_index)) fail("EDITORIAL_EVIDENCE_DOCUMENT_INVALID", field);
    try {
      for (const value of [fields.body, fields.title, fields.creator_handle]) checkPublicText(value);
    } catch { fail("EDITORIAL_EVIDENCE_PRIVACY_REJECTED", field); }
    if (!SHA256.test(dependency.document_sha256) || await hashPublicEvidenceDocument(fields) !== dependency.document_sha256) fail("EDITORIAL_EVIDENCE_HASH_MISMATCH", field);
    if (!dependency.quote || dependency.quote.length > EDITORIAL_EVIDENCE_LIMITS.quote
      || !fields.body.includes(dependency.quote)) fail("EDITORIAL_EVIDENCE_QUOTE_MISMATCH", field);
    expected.push({ ...fields, video_id: row.video_id, projection_id: row.projection_id,
      chunk_id: row.chunk_id, chunk_index: row.chunk_index });
  }
  const expectedJson = JSON.stringify(expected);
  if (encoder.encode(expectedJson).byteLength > EDITORIAL_EVIDENCE_LIMITS.snapshot_bytes) fail("EDITORIAL_EVIDENCE_TOO_LARGE");
  return { expected_json: expectedJson };
}
