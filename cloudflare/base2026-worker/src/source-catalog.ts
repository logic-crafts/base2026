/** Read-only source navigation. Receipt membership is not claim endorsement. */
const ORIGIN = "https://base2026.dev";
const PATH = "/sources/";
const PAGE_SIZE = 30;
const MAX_SHELL_BYTES = 256 * 1024;
const MAIN = '<main id="content" class="app-shell content-page">';
const LEGACY_SECTION = '<section class="content-section" aria-labelledby="source-records-list-heading">';
const LEGACY_HEADING = '<h2 id="source-records-list-heading">Available source records</h2>';
const VIDEO_ID = /^[0-9]{10,30}$/u;
const HANDLE = /^@?[A-Za-z0-9._-]{2,256}$/u;

type CatalogEnv = { DB: D1Database; ASSETS: Fetcher };
interface Cursor { date: string; video: string }
interface SourceRow {
  video_id: string;
  creator_handle: string;
  source_url: string;
  published_date: string;
  card_count: number;
  topic_label: string;
}

// Only aggregate public metadata leaves this query. Extra, missing, mismatched
// or non-public children invalidate the entire projection, not just one card.
// This checks navigation eligibility, not semantic truth or a new publication.
const SOURCE_QUERY = `SELECT d.video_id, MIN(d.creator_handle) AS creator_handle,
    MIN(d.source_url) AS source_url, MIN(d.published_date) AS published_date,
    COUNT(*) AS card_count, MIN(c.topic_label) AS topic_label
  FROM public_projection_receipts r
  JOIN public_projection_cards c ON c.projection_id=r.projection_id AND c.source_id=r.source_id
  JOIN search_documents d ON d.id=c.search_id AND d.projection_id=c.projection_id AND d.source_id=c.source_id
  WHERE r.status='applied' AND r.card_count BETWEEN 1 AND 3
    AND length(r.receipt_sha256)=64 AND r.receipt_sha256 NOT GLOB '*[^0-9a-f]*'
    AND d.admission_state='normal_public_card' AND d.full_transcript_public=0
    AND d.platform='tiktok' AND d.source_type='tiktok_video'
    AND d.public_policy='search_passage' AND d.public_surface='main_search'
    AND d.chunk_id=c.card_id AND d.chunk_index=c.ordinal
    AND length(d.video_id) BETWEEN 10 AND 30 AND d.video_id NOT GLOB '*[^0-9]*'
    AND length(ltrim(d.creator_handle,'@')) BETWEEN 2 AND 256
    AND ltrim(d.creator_handle,'@') NOT GLOB '*[^A-Za-z0-9._-]*'
    AND (d.creator_handle=ltrim(d.creator_handle,'@') OR d.creator_handle='@'||ltrim(d.creator_handle,'@'))
    AND r.source_id='tiktok:'||ltrim(d.creator_handle,'@')||':'||d.video_id
    AND (d.source_url='https://www.tiktok.com/@'||ltrim(d.creator_handle,'@')||'/video/'||d.video_id
      OR d.source_url='https://tiktok.com/@'||ltrim(d.creator_handle,'@')||'/video/'||d.video_id)
    AND NOT EXISTS (SELECT 1 FROM search_documents other
      WHERE other.source_id=r.source_id AND other.projection_id<>r.projection_id)
    /* KEYSET */
  GROUP BY r.projection_id, r.source_id, r.card_count
  HAVING COUNT(*)=r.card_count
    AND COUNT(DISTINCT d.video_id)=1 AND COUNT(DISTINCT d.creator_handle)=1
    AND COUNT(DISTINCT d.source_url)=1 AND COUNT(DISTINCT d.published_date)=1
    AND MIN(c.ordinal)=0 AND MAX(c.ordinal)=r.card_count-1
    AND (SELECT COUNT(*) FROM public_projection_cards children WHERE children.projection_id=r.projection_id)=r.card_count
    AND (SELECT COUNT(*) FROM search_documents documents WHERE documents.projection_id=r.projection_id)=r.card_count
  ORDER BY published_date DESC, d.video_id DESC LIMIT ?`;

function validDate(value: string): boolean {
  return value === "" || /^\d{4}-\d{2}-\d{2}$/u.test(value)
    && Number.isFinite(Date.parse(value + "T00:00:00.000Z"))
    && new Date(value + "T00:00:00.000Z").toISOString().slice(0, 10) === value;
}

function cursorToken(cursor: Cursor): string {
  // These are public date/video values, not receipt IDs or an authorization token.
  return btoa(JSON.stringify([1, cursor.date, cursor.video])).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/u, "");
}

function readCursor(url: URL): Cursor | null {
  const keys = [...url.searchParams.keys()];
  if (!keys.length) {
    if (url.search) throw new Error("INVALID_CURSOR");
    return null;
  }
  if (keys.length !== 1 || keys[0] !== "after") throw new Error("INVALID_CURSOR");
  const token = url.searchParams.get("after") ?? "";
  if (!/^[A-Za-z0-9_-]{1,128}$/u.test(token)) throw new Error("INVALID_CURSOR");
  let value: unknown;
  try { value = JSON.parse(atob(token.replaceAll("-", "+").replaceAll("_", "/"))); }
  catch { throw new Error("INVALID_CURSOR"); }
  if (!Array.isArray(value) || value.length !== 3 || value[0] !== 1
    || typeof value[1] !== "string" || !validDate(value[1])
    || typeof value[2] !== "string" || !VIDEO_ID.test(value[2])) throw new Error("INVALID_CURSOR");
  const cursor = { date: value[1], video: value[2] };
  if (cursorToken(cursor) !== token) throw new Error("INVALID_CURSOR");
  return cursor;
}

function pagePath(cursor: Cursor | null): string {
  return PATH + (cursor ? "?after=" + cursorToken(cursor) : "");
}

function isSourceRow(value: unknown): value is SourceRow {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const row = value as Record<string, unknown>;
  if (typeof row.video_id !== "string" || !VIDEO_ID.test(row.video_id)
    || typeof row.creator_handle !== "string" || !HANDLE.test(row.creator_handle)
    || typeof row.published_date !== "string" || !validDate(row.published_date)
    || typeof row.topic_label !== "string" || row.topic_label.length < 2 || row.topic_label.length > 120
    || /[\u0000-\u001f\u007f-\u009f]/u.test(row.topic_label)
    || !Number.isInteger(row.card_count) || Number(row.card_count) < 1 || Number(row.card_count) > 3) return false;
  const sourcePath = `/@${row.creator_handle.replace(/^@/u, "")}/video/${row.video_id}`;
  return row.source_url === "https://www.tiktok.com" + sourcePath || row.source_url === "https://tiktok.com" + sourcePath;
}

async function querySources(db: D1Database, cursor: Cursor | null, anchor = false): Promise<SourceRow[]> {
  const predicate = cursor
    ? anchor ? "AND d.published_date=? AND d.video_id=?"
      : "AND (d.published_date<? OR (d.published_date=? AND d.video_id<?))"
    : "";
  const parameters = cursor
    ? anchor ? [cursor.date, cursor.video, 1] : [cursor.date, cursor.date, cursor.video, PAGE_SIZE + 1]
    : [PAGE_SIZE + 1];
  const result = await db.prepare(SOURCE_QUERY.replace("/* KEYSET */", predicate)).bind(...parameters).all<unknown>();
  if (!result.success || !Array.isArray(result.results) || result.results.length > (anchor ? 1 : PAGE_SIZE + 1)
    || !result.results.every(isSourceRow)
    || new Set(result.results.map((row) => row.video_id)).size !== result.results.length) throw new Error("SOURCE_CATALOG_DATA_UNAVAILABLE");
  return result.results;
}

function response(request: Request, body: string, status: number, headers: HeadersInit = {}): Response {
  const resultHeaders = new Headers({
    "Content-Type": "text/html; charset=utf-8",
    "Cache-Control": status === 200 ? "public, max-age=60, s-maxage=120, must-revalidate" : "no-store",
    "X-Content-Type-Options": "nosniff",
  });
  new Headers(headers).forEach((value, name) => resultHeaders.set(name, value));
  return new Response(request.method === "HEAD" ? null : body, {
    status,
    headers: resultHeaders,
  });
}

function failure(request: Request, status: number): Response {
  return response(request, '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="robots" content="noindex,follow"><title>Source catalog unavailable | Base2026</title></head><body><h1>Source catalog unavailable</h1><p>Please return to the <a href="/sources/">first source page</a> or try again later.</p></body></html>', status, {
    "X-Robots-Tag": "noindex, follow",
    ...(status === 503 ? { "Retry-After": "60" } : {}),
  });
}

async function readShell(assets: Fetcher): Promise<string> {
  // ASSETS bypasses the router. Never self-fetch the public URL or forward
  // cookies, authorization, query strings or conditional request headers.
  const asset = await assets.fetch(new Request(ORIGIN + PATH, { headers: { Accept: "text/html" } }));
  if (asset.status !== 200 || !/^text\/html(?:\s*;|$)/iu.test(asset.headers.get("Content-Type") ?? "") || !asset.body) {
    await asset.body?.cancel();
    throw new Error("SOURCE_CATALOG_SHELL_UNAVAILABLE");
  }
  const lengthHeader = asset.headers.get("Content-Length");
  if (lengthHeader !== null && (!/^\d+$/u.test(lengthHeader) || Number(lengthHeader) > MAX_SHELL_BYTES)) {
    await asset.body.cancel();
    throw new Error("SOURCE_CATALOG_SHELL_TOO_LARGE");
  }
  const reader = asset.body.getReader();
  const chunks: Uint8Array[] = [];
  let length = 0;
  try {
    while (true) {
      const chunk = await reader.read();
      if (chunk.done) break;
      length += chunk.value.byteLength;
      if (length > MAX_SHELL_BYTES) {
        await reader.cancel();
        throw new Error("SOURCE_CATALOG_SHELL_TOO_LARGE");
      }
      chunks.push(chunk.value);
    }
  } finally { reader.releaseLock(); }
  const bytes = new Uint8Array(length);
  let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
  return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
}

function one(html: string, pattern: RegExp): RegExpMatchArray {
  const matches = [...html.matchAll(pattern)];
  if (matches.length !== 1) throw new Error("SOURCE_CATALOG_SHELL_INVALID");
  return matches[0];
}

function escapeHtml(value: string): string {
  return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}

function sourcePath(row: SourceRow): string { return "/sources/tiktok-video-" + row.video_id; }
function creator(row: SourceRow): string { return "@" + row.creator_handle.replace(/^@/u, ""); }

const CATALOG_STYLE = `<style data-b26-source-catalog>
.b26-source-catalog{min-width:0;scroll-margin-top:6rem}
.b26-source-catalog .intelligence-card{min-width:0}
.b26-source-catalog h3{font-size:clamp(18px,2vw,23px);overflow-wrap:anywhere}
.b26-source-catalog p,.b26-source-catalog a{overflow-wrap:anywhere}
.b26-source-catalog .b26-source-catalog__id{font-family:"Geist Mono",ui-monospace,monospace;font-size:.75rem;color:var(--b26-muted);overflow-wrap:anywhere}
.b26-source-catalog .b26-source-catalog__links,.b26-source-catalog .b26-source-catalog__pagination{display:flex;flex-wrap:wrap;align-items:center;gap:14px}
.b26-source-catalog .b26-source-catalog__pagination{margin-top:24px}
.b26-source-catalog .b26-source-catalog__pagination a{min-height:44px;display:inline-flex;align-items:center}
@media print{.b26-source-catalog .b26-source-catalog__pagination{display:none}}
</style>`;

function catalogSection(rows: SourceRow[], cursor: Cursor | null, next: Cursor | null): string {
  const cards = rows.map((row) => `<article class="intelligence-card">
    <h3><a href="${sourcePath(row)}">Source from ${escapeHtml(creator(row))}</a></h3>
    <p class="meta">${row.published_date ? `<time datetime="${row.published_date}">Published ${row.published_date}</time>` : "Publication date not supplied"} · ${row.card_count} extracted ${row.card_count === 1 ? "note" : "notes"}</p>
    <p class="meta">Extracted topic: ${escapeHtml(row.topic_label)}</p>
    <p class="b26-source-catalog__id">TikTok video ${row.video_id}</p>
    <div class="b26-source-catalog__links"><a class="button-link" href="${sourcePath(row)}">Read source record</a><a class="button-link" href="${escapeHtml(row.source_url)}" rel="noopener noreferrer">Original TikTok</a></div>
  </article>`).join("\n");
  return `<section id="b26-source-catalog" class="content-section b26-source-catalog" aria-labelledby="b26-source-catalog-heading">
    <p class="eyebrow">Live public catalog</p><h2 id="b26-source-catalog-heading">Cloud-added source records</h2>
    <p class="section-helper">These records contain extracted notes with creator attribution. Listing a source is not an endorsement or proof that its claims are correct. Check the original source and context.</p>
    <p class="meta">${rows.length} cloud-added source ${rows.length === 1 ? "record" : "records"} on this page. The legacy selection is listed separately below.</p>
    ${rows.length ? `<div class="card-grid">${cards}</div>` : '<p>No cloud-added source records are currently available.</p>'}
    ${cursor || next ? `<nav class="b26-source-catalog__pagination" aria-label="Cloud-added source pages">${cursor ? '<a class="button-link" href="/sources/#b26-source-catalog">First cloud-added source page</a>' : ""}${next ? `<a class="button-link" rel="next" href="${pagePath(next)}#b26-source-catalog">More cloud-added source records</a>` : ""}</nav>` : ""}
  </section>\n`;
}

function renderShell(html: string, rows: SourceRow[], cursor: Cursor | null, next: Cursor | null): string {
  // The retained builder owns this exact seam. Unexpected/duplicated markup
  // must not produce a fragment or a second page/header inside the document.
  const main = one(html, /<main\b[^>]*>/giu);
  const endMain = one(html, /<\/main\s*>/giu);
  const head = one(html, /<head\b[^>]*>/giu);
  const endHead = one(html, /<\/head\s*>/giu);
  const header = one(html, /<header\b[^>]*>/giu);
  const endHeader = one(html, /<\/header\s*>/giu);
  const footer = one(html, /<footer\b[^>]*>/giu);
  const endFooter = one(html, /<\/footer\s*>/giu);
  const body = one(html, /<body\b[^>]*>/giu);
  const endBody = one(html, /<\/body\s*>/giu);
  const heading = one(html, /<h1\b[^>]*>[\s\S]*?<\/h1\s*>/giu);
  const legacy = one(html, /<section class="content-section" aria-labelledby="source-records-list-heading">/gu);
  one(html, /<h2 id="source-records-list-heading">Available source records<\/h2>/gu);
  one(html, /<html\b[^>]*>/giu); one(html, /<\/html\s*>/giu);
  if (main[0] !== MAIN || heading[0] !== "<h1>Source Records</h1>"
    || !header[0].includes('class="b26-site-header"') || !footer[0].includes('class="b26-site-footer"')
    || html.includes("b26-source-catalog") || /<base\b/iu.test(html)
    || !(head.index! < endHead.index! && endHead.index! < body.index! && body.index! < header.index!
      && header.index! < endHeader.index! && endHeader.index! < main.index! && main.index! < heading.index!
      && heading.index! < legacy.index! && legacy.index! < endMain.index! && endMain.index! < footer.index!
      && footer.index! < endFooter.index! && endFooter.index! < endBody.index!)) {
    throw new Error("SOURCE_CATALOG_SHELL_INVALID");
  }
  const legacyHtml = html.slice(legacy.index, endMain.index);
  if ((legacyHtml.match(/<section\b/giu) ?? []).length !== 1
    || (legacyHtml.match(/<\/section\s*>/giu) ?? []).length !== 1) throw new Error("SOURCE_CATALOG_SHELL_INVALID");
  const legacyCards = [...legacyHtml.matchAll(/<article class="intelligence-card">/gu)].length;
  // The release builder canonicalizes internal `.html` aliases. Accept both
  // the retained pre-build shell and its extensionless production form.
  const legacyLinks = [...legacyHtml.matchAll(/href="tiktok-video-([0-9]{10,30})(?:\.html)?"/gu)].map((match) => match[1]);
  if (legacyCards < 1 || legacyCards > 200 || legacyLinks.length !== legacyCards || new Set(legacyLinks).size !== legacyCards
    || (legacyHtml.match(/<\/article\s*>/giu) ?? []).length !== legacyCards) throw new Error("SOURCE_CATALOG_SHELL_INVALID");

  const canonical = one(html, /<link\b(?=[^>]*\srel\s*=\s*(?:"canonical"|'canonical'|canonical(?=[\s/>])))[^>]*>/giu);
  const robots = one(html, /<meta\b(?=[^>]*\sname\s*=\s*(?:"robots"|'robots'|robots(?=[\s/>])))[^>]*>/giu);
  const ogUrl = one(html, /<meta\b(?=[^>]*\sproperty\s*=\s*(?:"og:url"|'og:url'|og:url(?=[\s/>])))[^>]*>/giu);
  const schemaTag = one(html, /<script\b(?=[^>]*\stype\s*=\s*(?:"application\/ld\+json"|'application\/ld\+json'|application\/ld\+json(?=[\s>])))[^>]*>([\s\S]*?)<\/script\s*>/giu);
  if (![canonical, robots, ogUrl, schemaTag].every((match) => match.index! > head.index! && match.index! < endHead.index!)
    || !canonical[0].includes(`href="${ORIGIN + PATH}"`) || !ogUrl[0].includes(`content="${ORIGIN + PATH}"`)) throw new Error("SOURCE_CATALOG_SHELL_INVALID");
  const oldSchema: unknown = JSON.parse(schemaTag[1]);
  if (!oldSchema || typeof oldSchema !== "object" || Array.isArray(oldSchema)) throw new Error("SOURCE_CATALOG_SHELL_INVALID");
  const schema = oldSchema as Record<string, unknown>;
  if (schema["@context"] !== "https://schema.org" || schema["@type"] !== "WebPage" || schema.url !== ORIGIN + PATH) throw new Error("SOURCE_CATALOG_SHELL_INVALID");
  const pageUrl = ORIGIN + pagePath(cursor);
  const updatedSchema = { ...schema, "@type": "CollectionPage", url: pageUrl,
    mainEntity: { "@type": "ItemList", name: "Cloud-added source records on this page", numberOfItems: rows.length,
      itemListElement: rows.map((row, index) => ({ "@type": "ListItem", position: index + 1,
        item: { "@type": "CreativeWork", name: "Source from " + creator(row), url: ORIGIN + sourcePath(row),
          creator: { "@type": "Person", name: creator(row) }, isBasedOn: row.source_url,
          ...(row.published_date ? { datePublished: row.published_date } : {}) } })) } };
  const schemaJson = JSON.stringify(updatedSchema).replaceAll("<", "\\u003c").replaceAll(">", "\\u003e").replaceAll("&", "\\u0026");
  return html
    .replace(canonical[0], `<link rel="canonical" href="${escapeHtml(pageUrl)}" />`)
    .replace(robots[0], `<meta name="robots" content="${cursor ? "noindex,follow" : "index,follow"}" />`)
    .replace(ogUrl[0], `<meta property="og:url" content="${escapeHtml(pageUrl)}" />`)
    .replace(schemaTag[0], () => `<script type="application/ld+json">${schemaJson}</script>`)
    .replace(endHead[0], CATALOG_STYLE + endHead[0])
    .replace(LEGACY_SECTION, catalogSection(rows, cursor, next) + LEGACY_SECTION)
    .replace(LEGACY_HEADING, `<h2 id="source-records-list-heading">Legacy source selection</h2><p class="section-helper">${legacyCards} source records from the retained static selection. Cloud-added records are listed separately above.</p>`);
}

/** Exact catalog routes only; root keeps all other routing and response policy. */
export async function handleSourceCatalog(request: Request, env: CatalogEnv, url: URL): Promise<Response | null> {
  if (url.pathname !== "/sources" && url.pathname !== PATH) return null;
  if (request.method !== "GET" && request.method !== "HEAD") {
    return response(request, "Method not allowed", 405, { Allow: "GET, HEAD", "X-Robots-Tag": "noindex, follow" });
  }
  let cursor: Cursor | null;
  try { cursor = readCursor(url); } catch { return failure(request, 400); }
  if (url.pathname === "/sources") return response(request, "", 308, { Location: ORIGIN + pagePath(cursor) });
  try {
    if (!env.DB || !env.ASSETS) throw new Error("SOURCE_CATALOG_BINDINGS_UNAVAILABLE");
    // Anchor validation avoids arbitrary, invented cursor ranges. If its source
    // was rolled back, the visible first-page link provides a safe restart.
    if (cursor && (await querySources(env.DB, cursor, true)).length !== 1) return failure(request, 400);
    const candidates = await querySources(env.DB, cursor);
    if (cursor && !candidates.length) return failure(request, 404);
    const rows = candidates.slice(0, PAGE_SIZE);
    const last = rows.at(-1);
    const next = candidates.length > PAGE_SIZE && last ? { date: last.published_date, video: last.video_id } : null;
    const html = renderShell(await readShell(env.ASSETS), rows, cursor, next);
    return response(request, html, 200, { "X-Robots-Tag": cursor ? "noindex, follow" : "index, follow" });
  } catch { return failure(request, 503); }
}
