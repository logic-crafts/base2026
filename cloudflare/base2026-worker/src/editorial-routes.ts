/** Public editorial routes are strictly read-only. Publication is RPC-only. */
import {
  EditorialValidationError,
  EDITORIAL_EVIDENCE_GUIDE_SLUGS,
  EDITORIAL_SITEMAP_PAGE_SIZE,
  getEditorialArticle,
  listEditorialArticles,
  listEditorialSitemapEntries,
  type EditorialListCursor,
} from "./editorial";
import {
  LEGACY_EDITORIAL_CATALOG,
  articleSummary,
  editorialJson,
  renderEditorialArticle,
  renderEditorialFeed,
  renderEditorialHub,
  renderEditorialSitemap,
  renderEditorialSitemapIndex,
  sortEditorialSummaries,
} from "./editorial-render";

interface EditorialRouteEnv { DB: D1Database; ASSETS: Fetcher }
const MAX_SHELL_BYTES = 256 * 1024;
const ARTICLE_PATH = /^\/blog\/([a-z0-9]+(?:-[a-z0-9]+)*)\/?$/u;
const ARTICLE_API = /^\/api\/blog\/([a-z0-9]+(?:-[a-z0-9]+)*)\/?$/u;
const SITEMAP_PAGE = /^\/sitemaps\/blog-([1-9]\d{0,4})\.xml$/u;
const RECEIPTED_ARTICLES = "FROM editorial_articles a INNER JOIN editorial_publication_receipts r"
  + " ON r.slug=a.slug AND r.revision=a.revision AND r.payload_sha256=a.payload_sha256"
  + " AND r.published_at=a.published_at AND r.updated_at=a.updated_at"
  + " AND r.recorded_at=a.stored_at AND r.reviewer='sol-max'"
  + " WHERE COALESCE(json_extract(a.payload_json, '$.kind'),'')<>'evidence_guide'";

function response(request: Request, body: string, contentType: string, status = 200, extras: HeadersInit = {}): Response {
  const headers = new Headers({
    "Content-Type": contentType,
    "Cache-Control": status === 200 ? "public, max-age=60, s-maxage=120, must-revalidate" : "no-store",
    "X-Content-Type-Options": "nosniff",
  });
  new Headers(extras).forEach((value, name) => headers.set(name, value));
  return new Response(request.method === "HEAD" ? null : body, {
    status,
    headers,
  });
}

function json(request: Request, payload: unknown, status = 200, extras: HeadersInit = {}): Response {
  return response(request, editorialJson(payload), "application/json; charset=utf-8", status, extras);
}

async function assetShell(assets: Fetcher): Promise<string> {
  // The asset binding bypasses the public router; no network source fetch or
  // forwarded session/cookie/header. The current build owns the whole shell.
  const result = await assets.fetch(new Request("https://base2026.dev/blog", {
    headers: { Accept: "text/html" },
  }));
  if (result.status !== 200 || !result.headers.get("Content-Type")?.includes("text/html") || !result.body) {
    throw new Error("EDITORIAL_SHELL_UNAVAILABLE");
  }
  if (Number(result.headers.get("Content-Length")) > MAX_SHELL_BYTES) {
    await result.body.cancel();
    throw new Error("EDITORIAL_SHELL_TOO_LARGE");
  }
  const reader = result.body.getReader();
  const chunks: Uint8Array[] = [];
  let length = 0;
  try {
    while (true) {
      const chunk = await reader.read();
      if (chunk.done) break;
      length += chunk.value.byteLength;
      if (length > MAX_SHELL_BYTES) {
        await reader.cancel();
        throw new Error("EDITORIAL_SHELL_TOO_LARGE");
      }
      chunks.push(chunk.value);
    }
  } finally { reader.releaseLock(); }
  const bytes = new Uint8Array(length);
  let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
  return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
}

function cursorFrom(url: URL): EditorialListCursor | undefined {
  const values = url.searchParams.getAll("cursor");
  if (!values.length) return undefined;
  if (values.length !== 1 || values[0].length > 150) throw new EditorialValidationError("EDITORIAL_CURSOR_INVALID", "cursor");
  const match = /^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z)\|([a-z0-9]+(?:-[a-z0-9]+)*)$/u.exec(values[0]);
  if (!match) throw new EditorialValidationError("EDITORIAL_CURSOR_INVALID", "cursor");
  return { published_at: match[1], slug: match[2] };
}

function cursorLink(cursor: EditorialListCursor | null): string | null {
  return cursor ? "/blog?cursor=" + encodeURIComponent(cursor.published_at + "|" + cursor.slug) : null;
}

function canonicalRedirect(request: Request, url: URL, path: string): Response {
  url.pathname = path;
  return response(request, "", "text/plain; charset=utf-8", 308, { Location: url.toString() });
}

/** Return null only for a route outside this editorial namespace. */
export async function handleEditorialRoute(
  request: Request, env: EditorialRouteEnv, now = new Date().toISOString(),
): Promise<Response | null> {
  const url = new URL(request.url);
  const path = url.pathname;
  const inScope = path === "/blog" || path === "/blog.html" || path.startsWith("/blog/")
    || path === "/api/blog" || path.startsWith("/api/blog/")
    || path === "/sitemap-blog.xml" || SITEMAP_PAGE.test(path);
  if (!inScope) return null;
  if (request.method !== "GET" && request.method !== "HEAD") {
    return json(request, { ok: false, code: "METHOD_NOT_ALLOWED" }, 405, { Allow: "GET, HEAD" });
  }
  if (path === "/blog/" || path === "/blog.html" || path === "/blog/index.html") {
    return canonicalRedirect(request, url, "/blog");
  }
  if (path === "/api/blog/") return canonicalRedirect(request, url, "/api/blog");
  try {
    if (!env.DB || !env.ASSETS) throw new Error("EDITORIAL_BINDINGS_UNAVAILABLE");
    const pageMatch = SITEMAP_PAGE.exec(path);
    if (path === "/sitemap-blog.xml" || pageMatch) {
      if (pageMatch) {
        const page = Number(pageMatch[1]);
        if (page > 50_000) return json(request, { ok: false, code: "NOT_FOUND" }, 404);
        const rows = await listEditorialSitemapEntries(env.DB, page, now);
        if (!rows.length && page !== 1) return json(request, { ok: false, code: "NOT_FOUND" }, 404);
        return response(request, renderEditorialSitemap(rows), "application/xml; charset=utf-8");
      }
      const count = await env.DB.prepare("SELECT COUNT(*) AS total " + RECEIPTED_ARTICLES).first<{ total: number }>();
      if (!count || !Number.isSafeInteger(count.total) || count.total < 0) throw new Error("EDITORIAL_SITEMAP_INVALID");
      const pages = Math.max(1, Math.ceil(count.total / EDITORIAL_SITEMAP_PAGE_SIZE));
      if (pages > 50_000) throw new Error("EDITORIAL_SITEMAP_CAPACITY");
      return response(request, renderEditorialSitemapIndex(pages), "application/xml; charset=utf-8");
    }

    if (path === "/blog" || path === "/api/blog" || path === "/blog/feed.xml") {
      const cursor = path === "/blog/feed.xml" ? undefined : cursorFrom(url);
      const page = await listEditorialArticles(env.DB, { now, limit: 25, ...(cursor ? { cursor } : {}) });
      const summaries = sortEditorialSummaries([
        ...page.articles.map(articleSummary), ...(cursor ? [] : LEGACY_EDITORIAL_CATALOG),
      ]);
      if (path === "/api/blog") {
        return json(request, {
          schema_version: "base2026.editorial-index.v1", articles: summaries,
          next_cursor: page.next_cursor, next_url: cursorLink(page.next_cursor),
          note: "Original editorial articles; counts are separate from source and evidence records.",
        });
      }
      if (path === "/blog/feed.xml") {
        return response(request, renderEditorialFeed(summaries.slice(0, 25)), "application/rss+xml; charset=utf-8");
      }
      const rendered = renderEditorialHub(await assetShell(env.ASSETS), summaries, cursorLink(page.next_cursor));
      // Cursor navigation is useful for discovery, not another indexed copy of
      // the hub. Every article keeps its own canonical and sitemap entry.
      return response(request, rendered, "text/html; charset=utf-8", 200,
        cursor ? { "X-Robots-Tag": "noindex, follow" } : {});
    }

    const articleMatch = ARTICLE_PATH.exec(path);
    const apiMatch = ARTICLE_API.exec(path);
    if (articleMatch || apiMatch) {
      const slug = (articleMatch ?? apiMatch)![1];
      if (slug.length > 120 || EDITORIAL_EVIDENCE_GUIDE_SLUGS.includes(slug)) return json(request, { ok: false, code: "NOT_FOUND" }, 404);
      const article = await getEditorialArticle(env.DB, slug, now);
      // A guide has one existing topic canonical, never a second blog copy.
      if (!article || article.payload.kind === "evidence_guide") return json(request, { ok: false, code: "NOT_FOUND" }, 404);
      if (apiMatch) return json(request, {
        schema_version: "base2026.editorial-public-article.v1",
        article: article.payload, public_path: article.public_path, payload_sha256: article.payload_sha256,
      });
      if (!path.endsWith("/")) return canonicalRedirect(request, url, article.public_path);
      const rendered = renderEditorialArticle(await assetShell(env.ASSETS), article);
      return response(request, rendered, "text/html; charset=utf-8");
    }
    return json(request, { ok: false, code: "NOT_FOUND" }, 404);
  } catch (error) {
    if (error instanceof EditorialValidationError) {
      return json(request, { ok: false, code: error.code, field: error.field }, 400);
    }
    // Never log a rejected payload, source URL, cursor, D1 row or request header.
    console.error(JSON.stringify({ event: "base2026_editorial_unavailable" }));
    return json(request, { ok: false, code: "EDITORIAL_TEMPORARILY_UNAVAILABLE" }, 503, { "Retry-After": "60" });
  }
}
