const PUBLIC_ORIGIN = "https://base2026.dev";
const MAX_BODY_BYTES = 4 * 1024;
const MAX_VALUE_LENGTH = 32;
const MAX_PROPERTIES = 8;
const RATE_LIMIT_KEY_PREFIX = "base2026:activation:v1:";
const RATE_LIMIT_RETRY_AFTER_SECONDS = 60;
const ANALYTICS_INDEX = "base2026:activation:v1";

const SECURITY_HEADERS = Object.freeze({
  "Cache-Control": "no-store",
  "Cross-Origin-Resource-Policy": "same-origin",
  "Permissions-Policy": "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()",
  "Referrer-Policy": "no-referrer",
  "Vary": "Origin",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
});

const COUNT_BUCKETS = new Set([
  "0_1",
  "1",
  "2_5",
  "6_10",
  "11_plus",
  "11_25",
  "26_100",
  "101_plus",
]);

const VALUE_SETS: Readonly<Record<string, ReadonlySet<string>>> = Object.freeze({
  completion_mode: new Set([
    "base2026_record_opened",
    "original_source_opened",
    "lookup_complete",
    "input_rejected",
  ]),
  copy_format: new Set(["record_card", "markdown", "json"]),
  decision: new Set([
    "use",
    "investigate",
    "exclude",
    "inspect_originals",
    "find_independent_evidence",
    "keep_unknowns",
  ]),
  error_class: new Set([
    "record_validation",
    "timeout",
    "http_error",
    "invalid_response",
    "network",
    "unknown",
  ]),
  input_mode: new Set(["delimited_ids", "json_records"]),
  input_source: new Set(["typed", "example", "evidence_search_handoff", "direct"]),
  latency_bucket_ms: new Set(["under_500", "500_1499", "1500_2999", "3000_plus"]),
  metadata_resolution: new Set(["complete", "partial", "unresolved"]),
  position_bucket: new Set(["1_3", "4_10", "11_plus"]),
  render_mode: new Set(["enhanced"]),
  response_class: new Set(["complete", "partial", "no_resolved_records", "invalid_input"]),
  scope: new Set(["record", "record_set"]),
  viewport_class: new Set(["small", "medium", "large"]),
  count_bucket: COUNT_BUCKETS,
  submitted_count_bucket: COUNT_BUCKETS,
  invalid_input_bucket: COUNT_BUCKETS,
  duplicate_input_bucket: COUNT_BUCKETS,
  record_id_bucket: COUNT_BUCKETS,
  source_id_bucket: COUNT_BUCKETS,
  loaded_count_bucket: COUNT_BUCKETS,
  failed_count_bucket: new Set(["1", "2_5", "6_plus"]),
  query_length_bucket: new Set(["1_20", "21_50", "51_100", "101_plus"]),
  query_token_bucket: new Set(["1", "2_3", "4_7", "8_plus"]),
});

const EVENT_PROPERTIES: Readonly<Record<string, ReadonlySet<string>>> = Object.freeze({
  evidence_search_viewed: new Set(["render_mode", "viewport_class"]),
  evidence_search_submitted: new Set(["input_source", "query_length_bucket", "query_token_bucket", "render_mode"]),
  evidence_search_results_returned: new Set(["count_bucket", "latency_bucket_ms", "response_class"]),
  evidence_source_record_opened: new Set(["position_bucket"]),
  evidence_original_source_clicked: new Set(["position_bucket"]),
  evidence_search_completed: new Set(["completion_mode", "count_bucket", "render_mode"]),
  evidence_search_empty: new Set(["query_length_bucket", "query_token_bucket", "render_mode"]),
  evidence_search_partial: new Set(["loaded_count_bucket", "failed_count_bucket", "error_class"]),
  evidence_search_error: new Set(["error_class", "render_mode"]),
  source_check_run: new Set([
    "input_source",
    "input_mode",
    "submitted_count_bucket",
    "invalid_input_bucket",
    "duplicate_input_bucket",
    "record_id_bucket",
    "source_id_bucket",
    "viewport_class",
  ]),
  source_check_completed: new Set(["completion_mode", "count_bucket", "response_class", "viewport_class"]),
  source_check_decision_recorded: new Set(["decision", "scope", "count_bucket", "position_bucket", "metadata_resolution", "viewport_class"]),
  source_check_card_copied: new Set(["copy_format", "count_bucket", "position_bucket", "metadata_resolution"]),
});

const ROUTE_EVENTS: Readonly<Record<string, ReadonlySet<string>>> = Object.freeze({
  "/tools/evidence-search/": new Set([
    "evidence_search_viewed",
    "evidence_search_submitted",
    "evidence_search_results_returned",
    "evidence_source_record_opened",
    "evidence_original_source_clicked",
    "evidence_search_completed",
    "evidence_search_empty",
    "evidence_search_partial",
    "evidence_search_error",
  ]),
  "/tools/source-diversity-check/": new Set([
    "source_check_run",
    "source_check_completed",
    "source_check_decision_recorded",
    "source_check_card_copied",
  ]),
});

interface RateLimitBinding {
  limit(options: { key: string }): Promise<{ success: boolean }>;
}

export interface ActivationAnalyticsEnv {
  ANALYTICS?: AnalyticsEngineDataset;
  MCP_RATE_LIMIT?: RateLimitBinding;
}

class MeasurementError extends Error {
  constructor(readonly status: number) {
    super();
  }
}

function response(status: number, extra: HeadersInit = {}): Response {
  const headers = new Headers(SECURITY_HEADERS);
  new Headers(extra).forEach((value, name) => headers.set(name, value));
  return new Response(null, { status, headers });
}

function rateLimitIdentity(request: Request): string {
  // CF-Connecting-IP is read only for the ephemeral edge rate-limit key. It is
  // never included in the Analytics Engine data point or an application log.
  const candidate = request.headers.get("CF-Connecting-IP")?.trim() ?? "";
  if (!candidate || candidate.length > 128 || /[\u0000-\u001f\u007f-\u009f]/u.test(candidate)) {
    return "anonymous";
  }
  return candidate;
}

async function enforceRateLimit(request: Request, env: ActivationAnalyticsEnv): Promise<Response | null> {
  if (!env.MCP_RATE_LIMIT) return response(503);
  try {
    const outcome = await env.MCP_RATE_LIMIT.limit({
      key: `${RATE_LIMIT_KEY_PREFIX}${rateLimitIdentity(request)}`,
    });
    if (!outcome.success) return response(429, { "Retry-After": String(RATE_LIMIT_RETRY_AFTER_SECONDS) });
    return null;
  } catch {
    return response(503);
  }
}

async function readBoundedBody(request: Request): Promise<string> {
  const contentLength = request.headers.get("content-length");
  if (contentLength && /^\d+$/u.test(contentLength) && Number(contentLength) > MAX_BODY_BYTES) {
    throw new MeasurementError(413);
  }
  if (!request.body) throw new MeasurementError(400);
  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const result = await reader.read();
      if (result.done) break;
      if (!result.value) continue;
      size += result.value.byteLength;
      if (size > MAX_BODY_BYTES) {
        await reader.cancel("body too large");
        throw new MeasurementError(413);
      }
      chunks.push(result.value);
    }
  } finally {
    reader.releaseLock();
  }
  const body = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return new TextDecoder().decode(body);
}

function parseBody(body: string): Record<string, unknown> {
  if (!body.trim()) throw new MeasurementError(400);
  let parsed: unknown;
  try {
    parsed = JSON.parse(body);
  } catch {
    throw new MeasurementError(400);
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new MeasurementError(400);
  return parsed as Record<string, unknown>;
}

function safeString(value: unknown): value is string {
  return typeof value === "string"
    && value.length > 0
    && value.length <= MAX_VALUE_LENGTH
    && !/[\u0000-\u001f\u007f-\u009f]/u.test(value);
}

function normalizedProperties(event: string, value: unknown): string {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new MeasurementError(400);
  const properties = value as Record<string, unknown>;
  const allowed = EVENT_PROPERTIES[event];
  if (!Object.prototype.hasOwnProperty.call(EVENT_PROPERTIES, event) || !allowed) throw new MeasurementError(400);
  const keys = Object.keys(properties);
  if (keys.length > MAX_PROPERTIES) throw new MeasurementError(400);
  const normalized: Record<string, string> = {};
  for (const key of keys) {
    if (!allowed.has(key) || !safeString(properties[key]) || !VALUE_SETS[key]?.has(properties[key] as string)) {
      throw new MeasurementError(400);
    }
    normalized[key] = properties[key] as string;
  }
  return JSON.stringify(normalized, Object.keys(normalized).sort());
}

function timestampBucket(now: Date): string {
  const safeNow = Number.isNaN(now.getTime()) ? new Date(0) : now;
  return `${safeNow.toISOString().slice(0, 13)}:00:00Z`;
}

function validateEvent(body: Record<string, unknown>, now: Date): AnalyticsEngineDataPoint {
  const keys = Object.keys(body);
  if (keys.some((key) => key !== "event" && key !== "route" && key !== "properties")) throw new MeasurementError(400);
  if (!safeString(body.event) || !Object.prototype.hasOwnProperty.call(EVENT_PROPERTIES, body.event)) throw new MeasurementError(400);
  if (!safeString(body.route) || !Object.prototype.hasOwnProperty.call(ROUTE_EVENTS, body.route)) throw new MeasurementError(400);
  const event = body.event;
  if (!ROUTE_EVENTS[body.route]?.has(event)) throw new MeasurementError(400);
  const properties = normalizedProperties(event, body.properties);
  return {
    blobs: [event, body.route, timestampBucket(now), properties],
    doubles: [1],
    indexes: [ANALYTICS_INDEX],
  };
}

/**
 * Collect one bounded, first-party activation event for the two public tools.
 *
 * The endpoint intentionally has no read API, cookie/session state, client
 * timestamp, request logging, or fallback storage. A failed write returns 204
 * so instrumentation can never block the product UI.
 */
export async function handleAnalyticsEvent(
  request: Request,
  env: ActivationAnalyticsEnv,
  now = new Date(),
): Promise<Response> {
  if (request.headers.get("Origin") !== PUBLIC_ORIGIN) return response(403);
  if (request.method !== "POST") return response(405, { Allow: "POST" });
  const contentType = request.headers.get("content-type")?.split(";", 1)[0]?.trim().toLowerCase();
  if (contentType !== "application/json") return response(415);

  const rateLimitResponse = await enforceRateLimit(request, env);
  if (rateLimitResponse) return rateLimitResponse;

  let point: AnalyticsEngineDataPoint;
  try {
    point = validateEvent(parseBody(await readBoundedBody(request)), now);
  } catch (error) {
    return response(error instanceof MeasurementError ? error.status : 400);
  }
  if (!env.ANALYTICS) return response(503);

  try {
    // Analytics Engine writes are non-blocking. Do not await or expose a write
    // failure to the browser; measurement is strictly best effort.
    env.ANALYTICS.writeDataPoint(point);
  } catch {
    // Keep the event path fail-open for the public tool UX.
  }
  return response(204);
}
