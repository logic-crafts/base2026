import {
  authRouteAllowed,
  appendMemberSignOutCookies,
  cleanupExpiredMemberVerification,
  consumeMemberRateLimit,
  createMemberAuth,
  getAuthoritativeSession,
  isMemberAuthPath,
  isTrustedMemberOrigin,
  isTrustedMemberRequestOrigin,
  memberAuthDisabledResponse,
  memberAuthIsConfigured,
  memberError,
  memberJson,
  readBoundedJson,
  type MemberAuthEnv,
  type MemberAuthSession,
  validateAuthBody,
} from "./member-auth";

export const MEMBER_RESEARCH_PATH_RE = /^\/api\/my-research(?:\/|$)/u;

const MAX_RESEARCH_BODY_BYTES = 16 * 1024;
const MAX_COLLECTIONS_PER_USER = 50;
const MAX_ITEMS_PER_USER = 500;
const MAX_NAME_LENGTH = 80;
const MAX_NOTE_LENGTH = 2_000;
const FRESH_SESSION_SECONDS = 10 * 60;
const VIDEO_REFERENCE_RE = /^\d{10,30}$/u;
const MEMBER_ID_RE = /^[A-Za-z0-9_-]{1,128}$/u;
const CONTROL_CHAR_RE = /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/u;

interface CollectionRow {
  id: string;
  userId: string;
  name: string;
  createdAt: number;
  updatedAt: number;
  itemCount?: number;
}

interface ItemRow {
  id: string;
  userId: string;
  collectionId: string;
  kind: "evidence";
  referenceId: string;
  title: string;
  url: string;
  note: string | null;
  createdAt: number;
  updatedAt: number;
}

interface PublicSourceRow {
  title: string | null;
}

interface SessionContext {
  auth: ReturnType<typeof createMemberAuth>;
  session: MemberAuthSession;
}

type RouteResult = Response | null;

function nowMs(): number {
  return Date.now();
}

function dateIso(value: unknown): string {
  const date = value instanceof Date
    ? value
    : typeof value === "number"
      ? new Date(value)
      : new Date(String(value));
  return Number.isFinite(date.getTime()) ? date.toISOString() : new Date(0).toISOString();
}

function collectionPayload(row: CollectionRow): {
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
  itemCount: number;
} {
  return {
    id: row.id,
    name: row.name,
    createdAt: dateIso(row.createdAt),
    updatedAt: dateIso(row.updatedAt),
    itemCount: Math.max(0, Number(row.itemCount ?? 0)),
  };
}

function itemPayload(row: ItemRow): {
  id: string;
  collectionId: string;
  kind: "evidence";
  referenceId: string;
  title: string;
  url: string;
  note: string | null;
  createdAt: string;
  updatedAt: string;
} {
  return {
    id: row.id,
    collectionId: row.collectionId,
    kind: "evidence",
    referenceId: row.referenceId,
    title: row.title,
    url: row.url,
    note: row.note ?? null,
    createdAt: dateIso(row.createdAt),
    updatedAt: dateIso(row.updatedAt),
  };
}

function isMutation(request: Request): boolean {
  return request.method !== "GET";
}

function mutationOriginAllowed(request: Request, env: MemberAuthEnv): boolean {
  return isTrustedMemberOrigin(request.headers.get("origin"), env);
}

function rateLimitResponse(retryAfter: number | null): Response {
  return memberJson(
    { error: { code: "RATE_LIMITED", message: "Too many requests. Try again later." } },
    {
      status: 429,
      headers: retryAfter === null ? undefined : { "Retry-After": String(Math.max(1, retryAfter)) },
    },
  );
}

async function enforceRateLimit(
  db: D1Database,
  secret: string,
  key: string,
  window: number,
  max: number,
): Promise<Response | null> {
  const result = await consumeMemberRateLimit(db, secret, key, { window, max });
  return result.allowed ? null : rateLimitResponse(result.retryAfter);
}

function normalizeRateAddress(value: string | null): string {
  if (!value) return "unknown";
  if (value.includes(",")) return "unknown";
  const candidate = value.trim().toLowerCase();
  const ipv4 = candidate.split(".");
  if (ipv4.length === 4 && ipv4.every((part) => /^(?:0|[1-9]\d{0,2})$/u.test(part) && Number(part) <= 255)) {
    // Keep only a /24 partition in the in-memory rate key. The key is HMACed
    // before persistence, so even this coarse network hint is not stored.
    return ipv4.slice(0, 3).join(".") + ".0/24";
  }
  if (!candidate.includes(":")) return "unknown";
  if (candidate.includes("%") || candidate.includes(".")) return "unknown";
  const halves = candidate.split("::");
  if (halves.length > 2) return "unknown";
  const left = halves[0] ? halves[0].split(":") : [];
  const right = halves.length === 2 && halves[1] ? halves[1].split(":") : [];
  const validGroup = (group: string): boolean => /^[0-9a-f]{1,4}$/u.test(group);
  if (!left.every(validGroup) || !right.every(validGroup)) return "unknown";
  const missing = halves.length === 2 ? 8 - left.length - right.length : 0;
  if (missing < 0 || (halves.length === 1 && left.length !== 8)) return "unknown";
  const groups = halves.length === 2
    ? [...left, ...Array.from({ length: missing }, () => "0"), ...right]
    : left;
  if (groups.length !== 8) return "unknown";
  return groups.slice(0, 4).map((group) => group.padStart(4, "0")).join(":") + "::/64";
}

function requestRateAddress(request: Request): string | null {
  // Cloudflare guarantees this header at the Worker edge. Do not accept
  // caller-controlled X-Forwarded-For for the durable privacy partition.
  return request.headers.get("cf-connecting-ip");
}

/** A coarse, HMAC-protected partition for unauthenticated session checks. */
export function memberSessionRateKey(request: Request): string | null {
  const address = normalizeRateAddress(requestRateAddress(request));
  if (address === "unknown") return null;
  return "member:session:" + address;
}

function researchRateCategory(method: string, segments: readonly string[]): string {
  if (segments.length === 1 && ["collections", "export", "revoke-sessions", "delete-account", "session"].includes(segments[0]!)) {
    return segments[0]!;
  }
  if (segments[0] === "collections" && segments.length === 3 && segments[2] === "items") return "collection-items";
  if (segments[0] === "collections" && segments.length === 2) return "collection";
  if (segments[0] === "items" && segments.length === 2) return "item";
  // Do not include arbitrary decoded path segments in a rate-limit key.
  return "unknown-" + method.toLowerCase();
}

export function memberResearchRateKey(method: string, segments: readonly string[], userId: string): string {
  return "member:research:" + method.toUpperCase() + ":" + researchRateCategory(method, segments) + ":" + userId;
}

async function readResearchBody(request: Request): Promise<Record<string, unknown> | null> {
  const contentType = request.headers.get("content-type")?.split(";", 1)[0].trim().toLowerCase();
  if (contentType !== "application/json") return null;
  return readBoundedJson(request, MAX_RESEARCH_BODY_BYTES);
}

function hasOnlyFields(body: Record<string, unknown>, allowed: readonly string[]): boolean {
  const allowedSet = new Set(allowed);
  return Object.keys(body).every((key) => allowedSet.has(key));
}

function parseCollectionName(body: Record<string, unknown>): string | null {
  if (!hasOnlyFields(body, ["name"]) || typeof body.name !== "string") return null;
  const name = body.name.trim();
  if (!name || name.length > MAX_NAME_LENGTH || CONTROL_CHAR_RE.test(name)) return null;
  return name;
}

function parseNote(body: Record<string, unknown>, required: boolean): string | null | undefined {
  if (!Object.prototype.hasOwnProperty.call(body, "note")) return required ? undefined : null;
  if (body.note !== null && typeof body.note !== "string") return undefined;
  if (body.note === null) return null;
  const note = body.note;
  if (note.length > MAX_NOTE_LENGTH || CONTROL_CHAR_RE.test(note)) return undefined;
  return note;
}

function parseVideoReference(value: unknown): string | null {
  return typeof value === "string" && VIDEO_REFERENCE_RE.test(value) ? value : null;
}

function parseMemberId(value: string | undefined): string | null {
  if (!value) return null;
  try {
    const decoded = decodeURIComponent(value);
    return MEMBER_ID_RE.test(decoded) ? decoded : null;
  } catch {
    return null;
  }
}

function routeSegments(pathname: string): string[] | null {
  const normalized = pathname.replace(/\/$/u, "");
  const raw = normalized.split("/").filter(Boolean);
  if (raw.length < 2 || raw[0] !== "api" || raw[1] !== "my-research") return null;
  return raw.slice(2).map((segment) => {
    try {
      return decodeURIComponent(segment);
    } catch {
      return "";
    }
  });
}

function isFreshSession(session: MemberAuthSession): boolean {
  if (session.session.fresh === true) return true;
  const createdAt = session.session.createdAt;
  if (!(createdAt instanceof Date) || !Number.isFinite(createdAt.getTime())) return false;
  const age = nowMs() - createdAt.getTime();
  return age >= 0 && age < FRESH_SESSION_SECONDS * 1_000;
}

async function requireSession(request: Request, env: MemberAuthEnv): Promise<SessionContext | Response> {
  try {
    const auth = createMemberAuth(env);
    const session = await getAuthoritativeSession(auth, request);
    if (!session) return memberError(401, "AUTH_REQUIRED", "Sign-in is required.");
    return { auth, session };
  } catch {
    return memberError(503, "MEMBER_UNAVAILABLE", "Member service is temporarily unavailable.");
  }
}

async function findPublicSource(db: D1Database, referenceId: string): Promise<PublicSourceRow | null> {
  const row = await db.prepare(
    `SELECT title
       FROM search_documents
      WHERE video_id = ?
        AND admission_state = 'normal_public_card'
        AND public_surface = 'main_search'
        AND full_transcript_public = 0
      ORDER BY id ASC
      LIMIT 1`,
  ).bind(referenceId).first<PublicSourceRow>();
  return row ?? null;
}

function sourcePayload(referenceId: string, row: PublicSourceRow): { title: string; url: string } {
  const title = typeof row.title === "string" && row.title.trim()
    ? row.title.trim().slice(0, 320)
    : `Public evidence source ${referenceId}`;
  return { title, url: `/sources/tiktok-video-${referenceId}` };
}

async function listCollections(db: D1Database, userId: string): Promise<Response> {
  const rows = await db.prepare(
    `SELECT c.id, c.userId, c.name, c.createdAt, c.updatedAt,
            (SELECT COUNT(*) FROM research_items i WHERE i.collectionId = c.id AND i.userId = c.userId) AS itemCount
       FROM research_collections c
      WHERE c.userId = ?
      ORDER BY c.updatedAt DESC, c.id ASC`,
  ).bind(userId).all<CollectionRow>();
  return memberJson({ collections: rows.results.map(collectionPayload) });
}

async function getCollection(db: D1Database, userId: string, collectionId: string): Promise<Response> {
  const collection = await db.prepare(
    `SELECT c.id, c.userId, c.name, c.createdAt, c.updatedAt,
            (SELECT COUNT(*) FROM research_items i WHERE i.collectionId = c.id AND i.userId = c.userId) AS itemCount
       FROM research_collections c
      WHERE c.id = ? AND c.userId = ?`,
  ).bind(collectionId, userId).first<CollectionRow>();
  if (!collection) return memberError(404, "NOT_FOUND", "Not found.");
  const items = await db.prepare(
    `SELECT id, userId, collectionId, kind, referenceId, title, url, note, createdAt, updatedAt
       FROM research_items
      WHERE collectionId = ? AND userId = ?
      ORDER BY createdAt ASC, id ASC`,
  ).bind(collectionId, userId).all<ItemRow>();
  return memberJson({
    collection: collectionPayload(collection),
    items: items.results.map(itemPayload),
  });
}

async function createCollection(db: D1Database, userId: string, name: string): Promise<Response> {
  const id = crypto.randomUUID();
  const timestamp = nowMs();
  await db.prepare(
    `INSERT OR IGNORE INTO research_collections (id, userId, name, createdAt, updatedAt)
     SELECT ?, id, ?, ?, ?
       FROM user
      WHERE id = ?
        AND (SELECT COUNT(*) FROM research_collections WHERE userId = ?) < ?`,
  ).bind(id, name, timestamp, timestamp, userId, userId, MAX_COLLECTIONS_PER_USER).run();
  const created = await db.prepare(
    "SELECT id, userId, name, createdAt, updatedAt FROM research_collections WHERE id = ? AND userId = ?",
  ).bind(id, userId).first<CollectionRow>();
  if (created) return memberJson({ collection: collectionPayload(created) }, { status: 201 });
  const count = await db.prepare("SELECT COUNT(*) AS count FROM research_collections WHERE userId = ?").bind(userId).first<{ count: number }>();
  return Number(count?.count ?? 0) >= MAX_COLLECTIONS_PER_USER
    ? memberError(409, "COLLECTION_LIMIT_REACHED", "Collection limit reached.")
    : memberError(503, "MEMBER_UNAVAILABLE", "Member service is temporarily unavailable.");
}

async function updateCollection(db: D1Database, userId: string, collectionId: string, name: string): Promise<Response> {
  await db.prepare(
    "UPDATE research_collections SET name = ?, updatedAt = ? WHERE id = ? AND userId = ?",
  ).bind(name, nowMs(), collectionId, userId).run();
  const row = await db.prepare(
    "SELECT id, userId, name, createdAt, updatedAt, (SELECT COUNT(*) FROM research_items WHERE collectionId = ? AND userId = ?) AS itemCount FROM research_collections WHERE id = ? AND userId = ?",
  ).bind(collectionId, userId, collectionId, userId).first<CollectionRow>();
  return row ? memberJson({ collection: collectionPayload(row) }) : memberError(404, "NOT_FOUND", "Not found.");
}

async function deleteCollection(db: D1Database, userId: string, collectionId: string): Promise<Response> {
  const result = await db.prepare("DELETE FROM research_collections WHERE id = ? AND userId = ?").bind(collectionId, userId).run();
  return Number(result.meta?.changes ?? 0) > 0
    ? memberJson({ deleted: true })
    : memberError(404, "NOT_FOUND", "Not found.");
}

async function createItem(
  db: D1Database,
  publicDb: D1Database | undefined,
  userId: string,
  collectionId: string,
  body: Record<string, unknown>,
): Promise<Response> {
  if (!publicDb) return memberError(503, "MEMBER_UNAVAILABLE", "Member service is temporarily unavailable.");
  if (!hasOnlyFields(body, ["kind", "referenceId", "note"]) || body.kind !== "evidence") {
    return memberError(400, "INVALID_ITEM", "Evidence item fields are invalid.");
  }
  const referenceId = parseVideoReference(body.referenceId);
  if (!referenceId) return memberError(400, "INVALID_REFERENCE", "Evidence reference is invalid.");
  const note = parseNote(body, false);
  if (note === undefined) return memberError(400, "INVALID_NOTE", "Note is invalid.");
  // This owner-scoped read keeps foreign collection IDs indistinguishable
  // before public-source validation. The INSERT below repeats the owner
  // predicate atomically, so this is defense-in-depth rather than an
  // authorization precheck.
  const ownedCollection = await db.prepare(
    "SELECT id FROM research_collections WHERE id = ? AND userId = ?",
  ).bind(collectionId, userId).first<{ id: string }>();
  if (!ownedCollection) return memberError(404, "NOT_FOUND", "Not found.");
  const source = await findPublicSource(publicDb, referenceId);
  if (!source) return memberError(404, "SOURCE_NOT_FOUND", "Public source not found.");
  const canonical = sourcePayload(referenceId, source);
  const id = crypto.randomUUID();
  const timestamp = nowMs();

  // The owner check and item quota are part of the INSERT SELECT itself. A
  // preflight collection lookup would leave a concurrent cross-owner write
  // window, so it is intentionally not used here.
  await db.prepare(
    `INSERT OR IGNORE INTO research_items
      (id, userId, collectionId, kind, referenceId, title, url, note, createdAt, updatedAt)
     SELECT ?, c.userId, c.id, 'evidence', ?, ?, ?, ?, ?, ?
       FROM research_collections c
       JOIN user u ON u.id = c.userId
      WHERE c.id = ?
        AND c.userId = ?
        AND u.id = ?
        AND (SELECT COUNT(*) FROM research_items WHERE userId = ?) < ?`,
  ).bind(
    id,
    referenceId,
    canonical.title,
    canonical.url,
    note,
    timestamp,
    timestamp,
    collectionId,
    userId,
    userId,
    userId,
    MAX_ITEMS_PER_USER,
  ).run();

  const created = await db.prepare(
    `SELECT id, userId, collectionId, kind, referenceId, title, url, note, createdAt, updatedAt
       FROM research_items WHERE id = ? AND userId = ?`,
  ).bind(id, userId).first<ItemRow>();
  if (created) return memberJson({ item: itemPayload(created), created: true }, { status: 201 });

  // A unique conflict is the idempotent duplicate-save path. It reads only
  // the authenticated owner's row and never overwrites its existing note.
  const duplicate = await db.prepare(
    `SELECT id, userId, collectionId, kind, referenceId, title, url, note, createdAt, updatedAt
       FROM research_items
      WHERE collectionId = ? AND userId = ? AND kind = 'evidence' AND referenceId = ?`,
  ).bind(collectionId, userId, referenceId).first<ItemRow>();
  if (duplicate) return memberJson({ item: itemPayload(duplicate), created: false });
  const collection = await db.prepare(
    "SELECT id FROM research_collections WHERE id = ? AND userId = ?",
  ).bind(collectionId, userId).first<{ id: string }>();
  if (!collection) return memberError(404, "NOT_FOUND", "Not found.");
  const count = await db.prepare("SELECT COUNT(*) AS count FROM research_items WHERE userId = ?").bind(userId).first<{ count: number }>();
  return Number(count?.count ?? 0) >= MAX_ITEMS_PER_USER
    ? memberError(409, "ITEM_LIMIT_REACHED", "Item limit reached.")
    : memberError(503, "MEMBER_UNAVAILABLE", "Member service is temporarily unavailable.");
}

async function updateItem(db: D1Database, userId: string, itemId: string, note: string | null): Promise<Response> {
  await db.prepare(
    "UPDATE research_items SET note = ?, updatedAt = ? WHERE id = ? AND userId = ?",
  ).bind(note, nowMs(), itemId, userId).run();
  const row = await db.prepare(
    `SELECT id, userId, collectionId, kind, referenceId, title, url, note, createdAt, updatedAt
       FROM research_items WHERE id = ? AND userId = ?`,
  ).bind(itemId, userId).first<ItemRow>();
  return row ? memberJson({ item: itemPayload(row) }) : memberError(404, "NOT_FOUND", "Not found.");
}

async function deleteItem(db: D1Database, userId: string, itemId: string): Promise<Response> {
  const result = await db.prepare("DELETE FROM research_items WHERE id = ? AND userId = ?").bind(itemId, userId).run();
  return Number(result.meta?.changes ?? 0) > 0
    ? memberJson({ deleted: true })
    : memberError(404, "NOT_FOUND", "Not found.");
}

async function exportResearch(db: D1Database, userId: string): Promise<Response> {
  const user = await db.prepare("SELECT id, name, email FROM user WHERE id = ?").bind(userId).first<{ id: string; name: string; email: string }>();
  if (!user) return memberError(401, "AUTH_REQUIRED", "Sign-in is required.");
  const collections = await db.prepare(
    `SELECT id, userId, name, createdAt, updatedAt,
            (SELECT COUNT(*) FROM research_items i WHERE i.collectionId = c.id AND i.userId = c.userId) AS itemCount
       FROM research_collections c WHERE c.userId = ? ORDER BY c.createdAt ASC, c.id ASC LIMIT ${MAX_COLLECTIONS_PER_USER}`,
  ).bind(userId).all<CollectionRow>();
  const items = await db.prepare(
    `SELECT id, userId, collectionId, kind, referenceId, title, url, note, createdAt, updatedAt
       FROM research_items WHERE userId = ? ORDER BY createdAt ASC, id ASC LIMIT ${MAX_ITEMS_PER_USER}`,
  ).bind(userId).all<ItemRow>();
  const itemsByCollection = new Map<string, ItemRow[]>();
  for (const item of items.results) {
    const list = itemsByCollection.get(item.collectionId) ?? [];
    list.push(item);
    itemsByCollection.set(item.collectionId, list);
  }
  const payload = {
    version: 1,
    exportedAt: new Date(nowMs()).toISOString(),
    user: { id: user.id, name: user.name, email: user.email },
    collections: collections.results.map((collection) => ({
      ...collectionPayload(collection),
      items: (itemsByCollection.get(collection.id) ?? []).map(itemPayload),
    })),
  };
  return memberJson(payload, {
    headers: {
      "Content-Disposition": 'attachment; filename="base2026-research-export.json"',
    },
  });
}

async function revokeSessions(
  db: D1Database,
  userId: string,
  auth: SessionContext["auth"],
  request: Request,
): Promise<Response> {
  await db.prepare("DELETE FROM session WHERE userId = ?").bind(userId).run();
  return appendMemberSignOutCookies(memberJson({ revoked: true }), auth, request);
}

async function deleteAccount(
  db: D1Database,
  userId: string,
  auth: SessionContext["auth"],
  request: Request,
): Promise<Response> {
  // Expired OAuth state has no owner column. Clean only expired rows, in a
  // bounded best-effort pass, before the account batch; valid/in-flight state
  // for every other member remains untouched and a maintenance failure never
  // turns a committed account deletion into a misleading error.
  try {
    await cleanupExpiredMemberVerification(db, Date.now(), true);
  } catch {
    // The auth/member deletion below is authoritative; state cleanup is not.
  }
  // D1 does not expose interactive transactions in Workers. A single batch is
  // atomic and explicitly deletes all owned rows before the Better Auth user.
  await db.batch([
    db.prepare("DELETE FROM research_items WHERE userId = ?").bind(userId),
    db.prepare("DELETE FROM research_collections WHERE userId = ?").bind(userId),
    db.prepare("DELETE FROM account WHERE userId = ?").bind(userId),
    db.prepare("DELETE FROM session WHERE userId = ?").bind(userId),
    db.prepare("DELETE FROM user WHERE id = ?").bind(userId),
  ]);
  return appendMemberSignOutCookies(memberJson({ deleted: true }), auth, request);
}

async function sessionSummary(request: Request, env: MemberAuthEnv): Promise<Response> {
  const rateKey = memberSessionRateKey(request);
  if (!rateKey && env.MEMBER_AUTH_LOCAL_DEV !== "true") {
    // The production Worker must receive Cloudflare's trusted client IP before
    // serving this unauthenticated endpoint; otherwise one shared bucket
    // could be used to deny every visitor. The local prototype is explicitly
    // allowed to omit the edge header.
    return memberError(503, "MEMBER_UNAVAILABLE", "Member service is temporarily unavailable.");
  }
  if (rateKey) {
    const rateLimit = await enforceRateLimit(env.AUTH_DB!, env.BETTER_AUTH_SECRET!, rateKey, 60, 120);
    if (rateLimit) return rateLimit;
  }
  const result = await requireSession(request, env);
  if (result instanceof Response) {
    if (result.status === 401) {
      return memberJson({ enabled: true, user: null, session: null });
    }
    return result;
  }
  return memberJson({
    enabled: true,
    user: {
      id: result.session.user.id,
      name: result.session.user.name,
      email: result.session.user.email,
    },
    session: {
      expiresAt: dateIso(result.session.session.expiresAt),
      fresh: isFreshSession(result.session),
    },
  });
}

export async function handleMemberRequest(request: Request, env: MemberAuthEnv): Promise<RouteResult> {
  const url = new URL(request.url);

  if (isMemberAuthPath(url.pathname)) {
    if (!memberAuthIsConfigured(env)) return memberAuthDisabledResponse();
    if (!authRouteAllowed(request, env)) return memberError(403, "AUTH_ROUTE_FORBIDDEN", "Authentication request is not allowed.");
    const path = url.pathname.replace(/\/$/u, "");
    if (request.method === "POST") {
      const body = await readBoundedJson(request.clone());
      if (!body) return memberError(400, "INVALID_BODY", "Request body is invalid.");
      const validationError = validateAuthBody(path, body);
      if (validationError) return memberError(400, validationError, "Authentication request is not allowed.");
    }
    try {
      await cleanupExpiredMemberVerification(env.AUTH_DB!);
      const response = await createMemberAuth(env).handler(request);
      const headers = new Headers(response.headers);
      headers.set("Cache-Control", "private, no-store");
      headers.set("X-Robots-Tag", "noindex, nofollow");
      headers.set("X-Content-Type-Options", "nosniff");
      return new Response(response.body, { status: response.status, statusText: response.statusText, headers });
    } catch {
      return memberError(503, "AUTH_UNAVAILABLE", "Authentication is temporarily unavailable.");
    }
  }

  if (!MEMBER_RESEARCH_PATH_RE.test(url.pathname)) return null;
  if (!memberAuthIsConfigured(env)) return memberAuthDisabledResponse();
  if (!env.AUTH_DB || !isTrustedMemberRequestOrigin(request, env)) {
    return memberError(403, "REQUEST_ORIGIN_FORBIDDEN", "Request origin is not allowed.");
  }

  const segments = routeSegments(url.pathname);
  if (!segments) return memberError(404, "NOT_FOUND", "Not found.");
  if (segments.length === 1 && segments[0] === "session") {
    if (request.method !== "GET") return memberError(405, "METHOD_NOT_ALLOWED", "Method is not allowed.");
    try {
      return await sessionSummary(request, env);
    } catch {
      return memberError(503, "MEMBER_UNAVAILABLE", "Member service is temporarily unavailable.");
    }
  }

  if (isMutation(request) && !mutationOriginAllowed(request, env)) {
    return memberError(403, "ORIGIN_FORBIDDEN", "Request origin is not allowed.");
  }

  let sessionResult: SessionContext | Response;
  try {
    sessionResult = await requireSession(request, env);
  } catch {
    return memberError(503, "MEMBER_UNAVAILABLE", "Member service is temporarily unavailable.");
  }
  if (sessionResult instanceof Response) return sessionResult;
  const { auth, session } = sessionResult;
  const rateLimit = await enforceRateLimit(
    env.AUTH_DB,
    env.BETTER_AUTH_SECRET!,
    memberResearchRateKey(request.method, segments, session.user.id),
    60,
    120,
  );
  if (rateLimit) return rateLimit;

  try {
    if (segments.length === 1 && segments[0] === "collections") {
      if (request.method === "GET") return await listCollections(env.AUTH_DB, session.user.id);
      if (request.method === "POST") {
        const body = await readResearchBody(request);
        const name = body && parseCollectionName(body);
        return name ? await createCollection(env.AUTH_DB, session.user.id, name) : memberError(400, "INVALID_NAME", "Collection name is invalid.");
      }
      return memberError(405, "METHOD_NOT_ALLOWED", "Method is not allowed.");
    }

    if (segments[0] === "collections" && segments[1]) {
      const collectionId = parseMemberId(segments[1]);
      if (!collectionId) return memberError(404, "NOT_FOUND", "Not found.");
      if (segments.length === 2) {
        if (request.method === "GET") return await getCollection(env.AUTH_DB, session.user.id, collectionId);
        if (request.method === "PATCH") {
          const body = await readResearchBody(request);
          const name = body && parseCollectionName(body);
          return name ? await updateCollection(env.AUTH_DB, session.user.id, collectionId, name) : memberError(400, "INVALID_NAME", "Collection name is invalid.");
        }
        if (request.method === "DELETE") return await deleteCollection(env.AUTH_DB, session.user.id, collectionId);
        return memberError(405, "METHOD_NOT_ALLOWED", "Method is not allowed.");
      }
      if (segments.length === 3 && segments[2] === "items") {
        if (request.method !== "POST") return memberError(405, "METHOD_NOT_ALLOWED", "Method is not allowed.");
        const body = await readResearchBody(request);
        return body ? await createItem(env.AUTH_DB, env.DB, session.user.id, collectionId, body) : memberError(400, "INVALID_BODY", "Request body is invalid.");
      }
    }

    if (segments[0] === "items" && segments[1]) {
      const itemId = parseMemberId(segments[1]);
      if (!itemId || segments.length !== 2) return memberError(404, "NOT_FOUND", "Not found.");
      if (request.method === "PATCH") {
        const body = await readResearchBody(request);
        const note = body && hasOnlyFields(body, ["note"]) ? parseNote(body, true) : undefined;
        return body && note !== undefined ? await updateItem(env.AUTH_DB, session.user.id, itemId, note) : memberError(400, "INVALID_NOTE", "Note is invalid.");
      }
      if (request.method === "DELETE") return await deleteItem(env.AUTH_DB, session.user.id, itemId);
      return memberError(405, "METHOD_NOT_ALLOWED", "Method is not allowed.");
    }

    if (segments.length === 1 && segments[0] === "export") {
      return request.method === "GET"
        ? await exportResearch(env.AUTH_DB, session.user.id)
        : memberError(405, "METHOD_NOT_ALLOWED", "Method is not allowed.");
    }

    if (segments.length === 1 && segments[0] === "revoke-sessions") {
      return request.method === "POST"
        ? await revokeSessions(env.AUTH_DB, session.user.id, auth, request)
        : memberError(405, "METHOD_NOT_ALLOWED", "Method is not allowed.");
    }

    if (segments.length === 1 && segments[0] === "delete-account") {
      if (request.method !== "POST") return memberError(405, "METHOD_NOT_ALLOWED", "Method is not allowed.");
      const body = await readResearchBody(request);
      if (!body || !hasOnlyFields(body, ["confirmation"]) || body.confirmation !== "DELETE") {
        return memberError(400, "CONFIRMATION_REQUIRED", "Type DELETE to confirm account deletion.");
      }
      if (!isFreshSession(session)) return memberError(403, "REAUTH_REQUIRED", "A fresh sign-in is required.");
      return await deleteAccount(env.AUTH_DB, session.user.id, auth, request);
    }

    return memberError(404, "NOT_FOUND", "Not found.");
  } catch {
    return memberError(503, "MEMBER_UNAVAILABLE", "Member service is temporarily unavailable.");
  }
}
