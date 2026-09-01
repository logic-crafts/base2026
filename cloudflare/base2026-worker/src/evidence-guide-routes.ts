/** Maintained guides reuse the reviewed editorial store; every public route is read-only. */
import {
  EDITORIAL_EVIDENCE_GUIDE_SLUGS, EDITORIAL_ORIGIN, editorialArticlePath,
  getEditorialArticle, type StoredEditorialArticle,
} from "./editorial";
import { editorialEscape, editorialJson, renderEditorialArticle } from "./editorial-render";

type GuideEnv = Pick<Env, "DB" | "ASSETS">;
const MAX_SHELL_BYTES = 256 * 1024;
const MAX_GUIDES = 8;
const APPROVED_SLUGS = new Set<string>(EDITORIAL_EVIDENCE_GUIDE_SLUGS);
const GUIDE_HUB_ALIASES = new Set(["/guides", "/guides/"]);
const TOPIC_PATH = /^\/topics\/([a-z0-9]+(?:-[a-z0-9]+)*)(?:\/|\.html)?$/u;
const API_PATH = /^\/api\/guides\/([a-z0-9]+(?:-[a-z0-9]+)*)$/u;

function response(request: Request, body: string, type: string, status = 200, extras: HeadersInit = {}): Response {
  // Every request rechecks live dependencies. A cached positive response must
  // not outlive a source correction/removal and keep serving old advice.
  const headers = new Headers({ "Content-Type": type, "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" });
  if (status >= 400) headers.set("X-Robots-Tag", "noindex, follow");
  new Headers(extras).forEach((value, name) => headers.set(name, value));
  return new Response(request.method === "HEAD" ? null : body, { status, headers });
}

function json(request: Request, value: unknown, status = 200, extras: HeadersInit = {}): Response {
  const headers = new Headers(extras);
  headers.set("X-Robots-Tag", "noindex, follow");
  return response(request, editorialJson(value), "application/json; charset=utf-8", status, headers);
}

function failShell(): never { throw new Error("GUIDE_SHELL_INVALID"); }

function attribute(tag: string, name: string): string | null {
  const matches = [...tag.matchAll(new RegExp("\\s" + name + "\\s*=\\s*(?:\"([^\"]*)\"|'([^']*)'|([^\\s>]+))", "giu"))];
  if (matches.length > 1) failShell();
  return matches[0] ? (matches[0][1] ?? matches[0][2] ?? matches[0][3]) : null;
}

/** Verify the exact retained hub seam before using its shared header/footer.
 * Broader quote/case-aware counts reject duplicate metadata that an exact
 * replacement could otherwise miss. This is not an arbitrary HTML sanitizer.
 */
function assertShell(shell: string): void {
  for (const tag of ["html", "head", "body", "main", "h1", "title"]) {
    if ([...shell.matchAll(new RegExp("<" + tag + "\\b[^>]*>", "giu"))].length !== 1
      || [...shell.matchAll(new RegExp("</" + tag + "\\s*>", "giu"))].length !== 1) failShell();
  }
  if (/<base\b/iu.test(shell) || !/<body\b[^>]*data-b26-design-system="b26-independent-v1"[^>]*>/u.test(shell)) failShell();
  const main = '<main id="b26-blog-main" class="b26-blog" data-b26-blog-index>';
  const mainStart = shell.indexOf(main);
  const mainEnd = shell.indexOf("</main>");
  const headers = [...shell.matchAll(/<header\b[^>]*>/giu)].filter((match) => attribute(match[0], "class")?.split(/\s+/u).includes("b26-site-header"));
  const footers = [...shell.matchAll(/<footer\b[^>]*>/giu)].filter((match) => attribute(match[0], "class")?.split(/\s+/u).includes("b26-site-footer"));
  const headStart = shell.indexOf("<head>"); const headEnd = shell.indexOf("</head>");
  const bodyStart = shell.indexOf("<body "); const bodyEnd = shell.indexOf("</body>");
  if (headers.length !== 1 || footers.length !== 1 || mainStart < 0 || mainEnd <= mainStart
    || !(shell.indexOf("<html ") >= 0 && shell.indexOf("<html ") < headStart && headStart < headEnd && headEnd < bodyStart
      && bodyStart < headers[0].index && headers[0].index < mainStart && footers[0].index > mainEnd
      && footers[0].index < bodyEnd && bodyEnd < shell.indexOf("</html>"))) failShell();
  const headerEnd = shell.indexOf("</header>", headers[0].index);
  const footerEnd = shell.indexOf("</footer>", footers[0].index);
  if (headerEnd <= headers[0].index || headerEnd >= mainStart || footerEnd <= footers[0].index || footerEnd >= bodyEnd) failShell();
  for (const tag of ["header", "footer"]) {
    if ([...shell.matchAll(new RegExp("<" + tag + "\\b[^>]*>", "giu"))].length
      !== [...shell.matchAll(new RegExp("</" + tag + "\\s*>", "giu"))].length) failShell();
  }
  for (const name of ["FEATURED", "TOPIC_LINKS", "CARDS"]) {
    const start = "<!--B26_BLOG_" + name + "_START-->";
    const end = "<!--B26_BLOG_" + name + "_END-->";
    if (shell.split(start).length !== 2 || shell.split(end).length !== 2
      || shell.indexOf(start) <= mainStart || shell.indexOf(end) <= shell.indexOf(start)
      || shell.indexOf(end) >= mainEnd) failShell();
  }
  const links = [...shell.matchAll(/<link\b[^>]*>/giu)].map((match) => match[0]);
  const canonicals = links.filter((tag) => attribute(tag, "rel")?.toLowerCase().split(/\s+/u).includes("canonical"));
  if (canonicals.length !== 1 || attribute(canonicals[0], "href") !== EDITORIAL_ORIGIN + "/blog") failShell();
  for (const name of ["base2026-core.css", "base2026-blog.css"]) {
    if (links.filter((tag) => attribute(tag, "rel") === "stylesheet" && attribute(tag, "href")?.split("?")[0] === "/static/" + name).length !== 1) failShell();
  }
  const metas = [...shell.matchAll(/<meta\b[^>]*>/giu)].map((match) => match[0]);
  for (const [key, name] of [
    ["name", "robots"], ["name", "description"], ["property", "og:type"], ["property", "og:title"],
    ["property", "og:description"], ["property", "og:url"], ["property", "og:image"], ["property", "og:image:alt"],
    ["name", "twitter:title"], ["name", "twitter:description"], ["name", "twitter:image"], ["name", "twitter:image:alt"],
  ]) {
    const matches = metas.filter((tag) => attribute(tag, key)?.toLowerCase() === name);
    if (matches.length !== 1 || attribute(matches[0], "content") === null) failShell();
    if (name === "robots" && !/^<meta name="robots" content="[^"]*">$/u.test(matches[0])) failShell();
    if (name === "og:url" && attribute(matches[0], "content") !== EDITORIAL_ORIGIN + "/blog") failShell();
  }
  const schemas = [...shell.matchAll(/<script\b[^>]*>[\s\S]*?<\/script\s*>/giu)]
    .filter((match) => attribute(match[0].slice(0, match[0].indexOf(">") + 1), "type")?.toLowerCase() === "application/ld+json");
  if (schemas.length !== 1 || !schemas[0][0].startsWith('<script type="application/ld+json" data-b26-blog-schema>')) failShell();
  const parsed: unknown = JSON.parse(schemas[0][0].slice(schemas[0][0].indexOf(">") + 1, schemas[0][0].lastIndexOf("</script")));
  if (!parsed || typeof parsed !== "object" || !("@graph" in parsed) || !Array.isArray(parsed["@graph"])
    || !parsed["@graph"].some((node: unknown) => node && typeof node === "object" && "@type" in node && node["@type"] === "Blog")) failShell();
}

async function assetShell(assets: Fetcher): Promise<string> {
  const asset = await assets.fetch(new Request(EDITORIAL_ORIGIN + "/blog", { headers: { Accept: "text/html" } }));
  if (asset.status !== 200 || !/^text\/html(?:\s*;|$)/iu.test(asset.headers.get("Content-Type") ?? "") || !asset.body) {
    if (asset.body) await asset.body.cancel();
    throw new Error("GUIDE_SHELL_UNAVAILABLE");
  }
  const declared = asset.headers.get("Content-Length");
  if (declared !== null && (!/^\d+$/u.test(declared) || Number(declared) > MAX_SHELL_BYTES)) {
    await asset.body.cancel(); throw new Error("GUIDE_SHELL_SIZE_INVALID");
  }
  const reader = asset.body.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const chunk = await reader.read();
      if (chunk.done) break;
      size += chunk.value.byteLength;
      if (size > MAX_SHELL_BYTES) { await reader.cancel(); throw new Error("GUIDE_SHELL_TOO_LARGE"); }
      chunks.push(chunk.value);
    }
  } finally { reader.releaseLock(); }
  const bytes = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
  const shell = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  assertShell(shell);
  return shell;
}

function assertAllowlist(): void {
  if (APPROVED_SLUGS.size < 1 || APPROVED_SLUGS.size > MAX_GUIDES || APPROVED_SLUGS.size !== EDITORIAL_EVIDENCE_GUIDE_SLUGS.length
    || [...APPROVED_SLUGS].some((slug) => slug.length > 120 || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/u.test(slug))) throw new Error("GUIDE_ALLOWLIST_INVALID");
}

async function readGuide(db: D1Database, slug: string, now: string): Promise<StoredEditorialArticle | null> {
  const article = await getEditorialArticle(db, slug, now);
  if (article && (article.payload.kind !== "evidence_guide" || article.payload.slug !== slug
    || article.public_path !== editorialArticlePath(slug, "evidence_guide"))) throw new Error("GUIDE_KIND_OR_PATH_INVALID");
  return article;
}

function unavailable(request: Request, html: boolean): Response {
  if (!html) return json(request, { ok: false, code: "GUIDE_TEMPORARILY_UNAVAILABLE" }, 503, { "Retry-After": "60" });
  return response(request, '<!doctype html><html lang="en"><head><meta charset="utf-8">'
    + '<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,follow">'
    + '<title>Guide temporarily unavailable | Base2026</title></head><body><main><h1>Guide temporarily unavailable</h1>'
    + '<p>A source or publication check could not complete. Please try again later.</p>'
    + '<p><a href="/topics/">Browse topics</a></p></main></body></html>', "text/html; charset=utf-8", 503, { "Retry-After": "60" });
}

/** Null means an unrelated route, or an approved topic with no published guide. */
export async function handleEvidenceGuideRoute(
  request: Request, env: GuideEnv, now = new Date().toISOString(),
): Promise<Response | null> {
  const url = new URL(request.url);
  const topic = TOPIC_PATH.exec(url.pathname);
  const html = topic !== null && APPROVED_SLUGS.has(topic[1]);
  const hubAlias = GUIDE_HUB_ALIASES.has(url.pathname);
  const api = url.pathname === "/api/guides" || url.pathname.startsWith("/api/guides/");
  const sitemap = url.pathname === "/sitemap-guides.xml";
  if (!html && !hubAlias && !api && !sitemap) return null;
  if (request.method !== "GET" && request.method !== "HEAD") {
    return json(request, { ok: false, code: "METHOD_NOT_ALLOWED" }, 405, { Allow: "GET, HEAD" });
  }
  // Maintained evidence guides are canonical topic pages. Keep the intuitive
  // collection alias useful without introducing a second index or canonical.
  if (hubAlias) {
    return response(request, "", "text/plain; charset=utf-8", 308, {
      Location: EDITORIAL_ORIGIN + "/topics/" + url.search,
    });
  }
  const detail = api ? API_PATH.exec(url.pathname) : null;
  if (api && url.pathname !== "/api/guides" && (!detail || !APPROVED_SLUGS.has(detail[1]))) {
    return json(request, { ok: false, code: "NOT_FOUND" }, 404);
  }
  if ((api || sitemap) && url.search) return json(request, { ok: false, code: "QUERY_NOT_SUPPORTED" }, 400);
  try {
    assertAllowlist();
    if (!env.DB) throw new Error("GUIDE_DATABASE_UNAVAILABLE");
    if (html || detail) {
      const article = await readGuide(env.DB, (topic ?? detail)![1], now);
      if (!article) return html ? null : json(request, { ok: false, code: "NOT_FOUND" }, 404);
      const canonical = EDITORIAL_ORIGIN + article.public_path;
      if (detail) return json(request, { schema_version: "base2026.evidence-guide-public.v1", guide: article.payload,
        public_path: article.public_path, canonical_url: canonical, payload_sha256: article.payload_sha256 });
      if (url.pathname !== article.public_path) {
        return response(request, "", "text/plain; charset=utf-8", 308, { Location: canonical + url.search });
      }
      if (!env.ASSETS) throw new Error("GUIDE_ASSETS_UNAVAILABLE");
      let rendered = renderEditorialArticle(await assetShell(env.ASSETS), article);
      if (url.search) rendered = rendered.replace(/<meta name="robots" content="[^"]*">/u, '<meta name="robots" content="noindex,follow">');
      return response(request, rendered, "text/html; charset=utf-8", 200, url.search ? { "X-Robots-Tag": "noindex, follow" } : {});
    }
    const guides: StoredEditorialArticle[] = [];
    for (const slug of APPROVED_SLUGS) {
      const article = await readGuide(env.DB, slug, now);
      if (article) guides.push(article);
    }
    if (sitemap) return response(request, '<?xml version="1.0" encoding="UTF-8"?>\n'
      + '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
      + guides.map((article) => '<url><loc>' + EDITORIAL_ORIGIN + editorialEscape(article.public_path)
        + '</loc><lastmod>' + editorialEscape(article.payload.updated_at) + '</lastmod></url>').join("") + '</urlset>\n',
    "application/xml; charset=utf-8");
    return json(request, { schema_version: "base2026.evidence-guide-index.v1", registered_topics: [...APPROVED_SLUGS], guides: guides.map((article) => ({
      slug: article.payload.slug, title: article.payload.title, description: article.payload.description,
      category: article.payload.category, author: article.payload.author.name, revision: article.payload.revision,
      published_at: article.payload.published_at, updated_at: article.payload.updated_at,
      public_path: article.public_path, canonical_url: EDITORIAL_ORIGIN + article.public_path, payload_sha256: article.payload_sha256,
    })), note: "Maintained task guides; counts are separate from source records and blog articles." });
  } catch {
    console.error(JSON.stringify({ event: "base2026_evidence_guide_unavailable" }));
    return unavailable(request, html);
  }
}
