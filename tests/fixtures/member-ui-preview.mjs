// Local, synthetic browser-QA fixture. Not an auth implementation or a release
// artifact. It cannot contact Google, write D1 or listen outside loopback.
import { createServer } from "node:http";
import { readFile, realpath, stat } from "node:fs/promises";
import { extname, isAbsolute, resolve, sep } from "node:path";

const args = process.argv.slice(2);
const option = (name) => args[args.indexOf(name) + 1];
if (!args.includes("--assets")) throw new Error("Use --assets with a canonical builder output directory.");
const root = await realpath(resolve(option("--assets")));
const port = args.includes("--port") ? Number(option("--port")) : 8790;
if (!Number.isInteger(port) || port < 1024 || port > 65535) throw new Error("Invalid loopback port.");
const origin = `http://127.0.0.1:${port}`;
const user = { id: "synthetic-ui-user", name: "Local QA — synthetic account", email: "qa@example.invalid" };
const source = {
  id: "synthetic-ui-chunk", item_id: "tiktok-video-7999999999999999933", video_id: "7999999999999999933",
  source_id: "synthetic-ui-source", title: "Local UI test evidence — never published",
  body: "Synthetic evidence for checking Save controls. This is not a source claim.",
  creator_id: "synthetic-ui", creator_handle: "@synthetic_ui", handle: "@synthetic_ui",
  creator_display_name: "Synthetic UI fixture", platform: "tiktok", source_type: "tiktok_video",
  published_date: "2026-08-31", year: "2026", topics: ["ai-search"], topic_labels: ["AI search"],
  admission_state: "normal_public_card", public_surface: "main_search", full_transcript_public: false,
  source_url: "https://example.invalid/local-ui-fixture",
};
let collections = [];
let items = [];
let serial = 0;
const json = (response, status, data, extra = {}) => {
  response.writeHead(status, { "Content-Type": "application/json", "Cache-Control": "no-store", ...extra });
  response.end(JSON.stringify(data));
};
const readBody = async (request) => {
  let body = "";
  for await (const chunk of request) {
    body += chunk;
    if (Buffer.byteLength(body) > 8192) throw new Error("Fixture body too large.");
  }
  return body ? JSON.parse(body) : {};
};
const collectionDTO = (collection) => ({ ...collection, itemCount: items.filter((item) => item.collectionId === collection.id).length });
const mime = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png", ".jpeg": "image/jpeg", ".jpg": "image/jpeg", ".webp": "image/webp", ".woff2": "font/woff2" };

const server = createServer(async (request, response) => {
  try {
    const url = new URL(request.url, origin);
    const signedIn = /(?:^|;\s*)synthetic_ui_session=1(?:;|$)/u.test(request.headers.cookie || "");
    if (url.pathname === "/__qa/") {
      response.writeHead(200, { "Content-Type": "text/html", "Cache-Control": "no-store" });
      response.end('<!doctype html><html lang="en"><title>Local synthetic UI QA</title><h1>Local synthetic UI QA</h1><p>Only a display fixture. No Google, D1 or production data.</p><p><a href="/__qa/sign-in">Start synthetic signed-in preview</a></p><p><a href="/workspace/?q=local-ui-qa#results">Anonymous workspace</a></p><p><a href="/my-research/">My Research</a></p></html>');
      return;
    }
    if (url.pathname === "/__qa/sign-in") {
      response.writeHead(303, {
        Location: "/workspace/?q=local-ui-qa#results", "Cache-Control": "no-store",
        "Set-Cookie": "synthetic_ui_session=1; HttpOnly; SameSite=Lax; Path=/",
      });
      response.end();
      return;
    }
    if (url.pathname === "/api/search/multi-search" || url.pathname === "/knowledge-search/multi-search") {
      const input = await readBody(request);
      json(response, 200, { results: (input.queries || [{}]).map((query) => ({ indexUid: query.indexUid || "base2026_public_tiktok", query: query.q || "", hits: [source], estimatedTotalHits: 1, processingTimeMs: 1, limit: query.limit || 20, offset: 0, facetDistribution: {} })) });
      return;
    }
    if (url.pathname === "/api/my-research/session") {
      json(response, 200, { enabled: true, user: signedIn ? user : null, session: signedIn ? { expiresAt: "2099-01-01T00:00:00.000Z", fresh: false } : null });
      return;
    }
    if (url.pathname === "/api/auth/sign-in/social") {
      json(response, 503, { error: { code: "LOCAL_QA_ONLY", message: "Synthetic QA cannot start Google authorization." } });
      return;
    }
    if (url.pathname === "/api/auth/sign-out") {
      json(response, 200, { success: true }, { "Set-Cookie": "synthetic_ui_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0" });
      return;
    }
    if (url.pathname.startsWith("/api/my-research/")) {
      if (!signedIn) { json(response, 401, { error: { code: "UNAUTHENTICATED", message: "Synthetic preview is signed out." } }); return; }
      const input = request.method === "GET" ? {} : await readBody(request);
      const now = new Date().toISOString();
      if (url.pathname === "/api/my-research/collections") {
        if (request.method === "POST") {
          const collection = { id: `synthetic-collection-${++serial}`, name: String(input.name || "Local QA collection"), createdAt: now, updatedAt: now };
          collections.push(collection);
          json(response, 201, { collection: collectionDTO(collection) });
        } else json(response, 200, { collections: collections.map(collectionDTO) });
        return;
      }
      const match = /^\/api\/my-research\/collections\/([^/]+)(\/items)?$/u.exec(url.pathname);
      const collection = match && collections.find((entry) => entry.id === match[1]);
      if (collection) {
        if (match[2] && request.method === "POST") {
          const existing = items.find((item) => item.collectionId === collection.id && item.referenceId === input.referenceId);
          const item = existing || { id: `synthetic-item-${++serial}`, collectionId: collection.id, kind: "evidence", referenceId: String(input.referenceId), title: source.title, url: `/sources/tiktok-video-${input.referenceId}`, note: "", createdAt: now, updatedAt: now };
          if (!existing) items.push(item);
          json(response, existing ? 200 : 201, { item, created: !existing });
        } else json(response, 200, { collection: collectionDTO(collection), items: items.filter((item) => item.collectionId === collection.id) });
        return;
      }
      const itemMatch = /^\/api\/my-research\/items\/([^/]+)$/u.exec(url.pathname);
      const item = itemMatch && items.find((entry) => entry.id === itemMatch[1]);
      if (item && request.method === "PATCH") {
        item.note = String(input.note || ""); item.updatedAt = now;
        json(response, 200, { item }); return;
      }
      if (url.pathname === "/api/my-research/export") {
        json(response, 200, { fixture: "synthetic-ui-only", user, collections: collections.map(collectionDTO), items }); return;
      }
      json(response, 404, { error: { code: "FIXTURE_NOT_IMPLEMENTED", message: "This operation is covered by real D1 tests, not this display fixture." } });
      return;
    }
    if (url.pathname.startsWith("/api/")) { json(response, 404, { error: "Synthetic fixture route not found." }); return; }
    const pathname = decodeURIComponent(url.pathname);
    if (pathname.split("/").some((part) => part.startsWith("."))) throw new Error("Hidden fixture file denied.");
    let file = resolve(root, `.${pathname}`);
    if (!file.startsWith(`${root}${sep}`) && file !== root) throw new Error("Fixture path denied.");
    try { if ((await stat(file)).isDirectory()) file = resolve(file, "index.html"); } catch { if (!extname(file)) file += ".html"; }
    file = await realpath(file);
    if (!isAbsolute(file) || !file.startsWith(`${root}${sep}`)) throw new Error("Fixture file denied.");
    const privatePage = url.pathname.startsWith("/my-research/");
    response.writeHead(200, {
      "Content-Type": `${mime[extname(file)] || "application/octet-stream"}; charset=utf-8`,
      "Cache-Control": "no-store",
      ...(privatePage ? { "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'; object-src 'none'" } : {}),
    });
    response.end(request.method === "HEAD" ? undefined : await readFile(file));
  } catch {
    if (!response.headersSent) json(response, 404, { error: "Synthetic fixture resource unavailable." });
    else response.end();
  }
});
server.listen(port, "127.0.0.1", () => console.log(`Synthetic-only UI fixture: ${origin}/__qa/`));
