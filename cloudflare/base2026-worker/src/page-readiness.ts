/** Source-only safety fallback: this module must never fetch a caller's URL. */
export const PAGE_LIMITS = Object.freeze({ bodyBytes: 320 * 1024, htmlBytes: 256 * 1024, milliseconds: 5000, elements: 8000, values: 40, text: 512, redirects: 0, targetRequests: 0 });
type Check = { id: string; state: "observed" | "review" | "unknown"; observation: string; why: string; action: string; recheck: string };
type SourceFacts = {
  titles: string[]; h1: string[]; canonical: string[]; robots: { agent: string; content: string }[];
  links: number; nofollowLinks: number; unresolvedLinks: number;
  jsonLd: { total: number; parseable: number; invalid: number; nonObject: number };
  otherStructuredMarkup: boolean; textClipped: boolean;
};
class CheckError extends Error {
  constructor(readonly code: string, message: string, readonly status = 400) { super(message); }
}
const unsupported = "Live URL retrieval is unavailable in this version. Open the public page, choose View Page Source, and paste its HTML below. Only the supplied source will be checked.";
const unknownNetwork = { state: "unknown", httpStatus: null, redirects: null, xRobotsTag: null, robotsTxt: null, crawlEligibility: null, indexing: null } as const;

/** Syntactic input policy, NOT DNS validation. No network request follows it. */
export function pageSourceUrl(value: unknown): URL {
  if (typeof value !== "string" || value.length > 2048 || /[\s\\\u0000-\u001f\u007f]/u.test(value)) throw new CheckError("INVALID_URL", "Use a complete public HTTPS URL without spaces.");
  let url: URL;
  try { url = new URL(value); } catch { throw new CheckError("INVALID_URL", "Use a complete public HTTPS URL."); }
  const host = url.hostname.toLowerCase();
  if (url.protocol !== "https:" || url.username || url.password || url.port || url.search || url.hash) throw new CheckError("UNSUPPORTED_URL", "Use HTTPS on the standard port, without credentials, query strings or a fragment.");
  if (!host.includes(".") || host.endsWith(".") || host.includes(":") || /(?:^|\.)\d+$/u.test(host) || /(?:^|\.)(?:localhost|local|internal|intranet|lan|home|test|invalid|onion|arpa)$/u.test(host)) throw new CheckError("UNSUPPORTED_HOST", "Private, local, reserved and IP-literal targets are unsupported.");
  return url;
}

async function boundedBody(request: Request, signal: AbortSignal): Promise<string> {
  if (Number(request.headers.get("Content-Length")) > PAGE_LIMITS.bodyBytes) throw new CheckError("OVERSIZE", "Request exceeds 320 KiB.", 413);
  if (!request.body) throw new CheckError("INVALID_INPUT", "Provide a JSON object with a URL and optional public HTML.");
  const reader = request.body.getReader();
  const decoder = new TextDecoder("utf-8", { fatal: true });
  let bytes = 0, text = "";
  const cancel = () => { void reader.cancel().catch(() => {}); };
  signal.addEventListener("abort", cancel, { once: true });
  try {
    while (true) {
      if (signal.aborted) throw new CheckError("TIMEOUT", "The check timed out. Try again with a smaller public source file.", 408);
      const chunk = await reader.read();
      if (signal.aborted) throw new CheckError("TIMEOUT", "The check timed out. Try again with a smaller public source file.", 408);
      if (chunk.done) break;
      bytes += chunk.value.byteLength;
      if (bytes > PAGE_LIMITS.bodyBytes) throw new CheckError("OVERSIZE", "Request exceeds 320 KiB.", 413);
      text += decoder.decode(chunk.value, { stream: true });
    }
    return text + decoder.decode();
  } finally {
    signal.removeEventListener("abort", cancel);
    void reader.cancel().catch(() => {});
  }
}

export async function inspectPageSource(html: string, url: URL | null, signal?: AbortSignal): Promise<{ facts: SourceFacts; checks: Check[] }> {
  if (new TextEncoder().encode(html).length > PAGE_LIMITS.htmlBytes) throw new CheckError("OVERSIZE", "HTML exceeds 256 KiB. Partial source would give an incomplete result.", 413);
  const facts: SourceFacts = { titles: [], h1: [], canonical: [], robots: [], links: 0, nofollowLinks: 0, unresolvedLinks: 0, jsonLd: { total: 0, parseable: 0, invalid: 0, nonObject: 0 }, otherStructuredMarkup: false, textClipped: false };
  let elements = 0, documentTags = 0, titleIndex = -1, h1Index = -1;
  let overflow: CheckError | null = null;
  let base: string | undefined;
  const links: { href: string; nofollow: boolean }[] = [];
  const json: string[] = [];
  let jsonIndex = -1;
  const add = (list: string[], value: string) => {
    if (overflow) return -1;
    if (list.length >= PAGE_LIMITS.values) { overflow = new CheckError("COMPLEX_SOURCE", "Too many repeated metadata elements to check completely.", 422); return -1; }
    list.push(clip(value));
    return list.length - 1;
  };
  const clip = (value: string) => {
    if (value.length > PAGE_LIMITS.text) facts.textClipped = true;
    return value.slice(0, PAGE_LIMITS.text);
  };
  const attribute = (value: string) => {
    if (value.length > PAGE_LIMITS.text) overflow = new CheckError("COMPLEX_SOURCE", "Metadata attributes exceed the supported length; partial directives would be misleading.", 422);
    return value.slice(0, PAGE_LIMITS.text);
  };
  const rewriter = new HTMLRewriter()
    .on("*", { element(element) {
      if (++elements > PAGE_LIMITS.elements) { overflow = new CheckError("COMPLEX_SOURCE", "This source has too many elements to check completely.", 422); return; }
      if (["html", "head", "body"].includes(element.tagName)) documentTags++;
      if (element.hasAttribute("itemscope") || element.hasAttribute("typeof")) facts.otherStructuredMarkup = true;
    } })
    .on("head > title", {
      element(element) { titleIndex = add(facts.titles, ""); element.onEndTag(() => { titleIndex = -1; }); },
      text(chunk) { if (titleIndex >= 0) facts.titles[titleIndex] = clip(facts.titles[titleIndex] + chunk.text); },
    })
    .on("h1", {
      element(element) { h1Index = add(facts.h1, ""); element.onEndTag(() => { h1Index = -1; }); },
      text(chunk) { if (h1Index >= 0) facts.h1[h1Index] = clip(facts.h1[h1Index] + chunk.text); },
    })
    .on("head > base[href]", { element(element) { if (base === undefined) base = element.getAttribute("href") ?? ""; } })
    .on("head > link", { element(element) {
      if ((element.getAttribute("rel") ?? "").toLowerCase().split(/\s+/u).includes("canonical")) add(facts.canonical, attribute(element.getAttribute("href") ?? ""));
    } })
    .on("head > meta", { element(element) {
      const agent = (element.getAttribute("name") ?? "").toLowerCase();
      if (["robots", "googlebot", "googlebot-news", "googlebot-image", "bingbot", "slurp", "duckduckbot", "baiduspider", "yandexbot", "gptbot", "oai-searchbot", "chatgpt-user"].includes(agent) || agent.endsWith("bot")) {
        if (overflow) return;
        if (facts.robots.length >= PAGE_LIMITS.values) { overflow = new CheckError("COMPLEX_SOURCE", "Too many robots directives to check completely.", 422); return; }
        facts.robots.push({ agent: attribute(agent), content: attribute(element.getAttribute("content") ?? "") });
      }
    } })
    .on("a[href]", { element(element) {
      if (overflow) return;
      links.push({ href: element.getAttribute("href") ?? "", nofollow: (element.getAttribute("rel") ?? "").toLowerCase().split(/\s+/u).includes("nofollow") });
    } })
    .on("script", {
      element(element) {
        jsonIndex = -1;
        if ((element.getAttribute("type") ?? "").trim().toLowerCase() === "application/ld+json") {
          if (overflow) return;
          if (json.length >= PAGE_LIMITS.values) { overflow = new CheckError("COMPLEX_SOURCE", "Too many JSON-LD blocks to check completely.", 422); return; }
          jsonIndex = json.push("") - 1;
        }
        element.onEndTag(() => { jsonIndex = -1; });
      },
      text(chunk) { if (jsonIndex >= 0) json[jsonIndex] += chunk.text; },
    });
  // HTMLRewriter parses inert source. Never return transformed HTML, load resources,
  // execute scripts, resolve JSON-LD contexts or interpret page text as instructions.
  const parsed = rewriter.transform(new Response(html, { headers: { "Content-Type": "text/html; charset=utf-8" } }));
  const reader = parsed.body!.getReader();
  const cancel = () => { void reader.cancel().catch(() => {}); };
  signal?.addEventListener("abort", cancel, { once: true });
  try {
    while (!(await reader.read()).done) {
      if (signal?.aborted) break;
    }
  } finally { signal?.removeEventListener("abort", cancel); cancel(); }
  if (signal?.aborted) throw new CheckError("TIMEOUT", "The source check timed out.", 408);
  if (overflow) throw overflow;
  if (!documentTags) throw new CheckError("NON_HTML", "Paste a complete HTML page source, including its html, head or body element.", 422);
  facts.titles = facts.titles.map((value) => value.trim());
  facts.h1 = facts.h1.map((value) => value.trim());
  let effectiveBase: URL | null = url;
  if (base !== undefined) { try { effectiveBase = new URL(base, url ?? undefined); } catch { effectiveBase = null; } }
  for (const link of links) {
    if (!link.href.trim() || link.href.trim().startsWith("#")) continue;
    try {
      const target = new URL(link.href, effectiveBase ?? undefined);
      if (!["http:", "https:"].includes(target.protocol) || target.username || target.password) continue;
      if (link.nofollow) facts.nofollowLinks++; else facts.links++;
    } catch { facts.unresolvedLinks++; }
  }
  for (const value of json) {
    facts.jsonLd.total++;
    try {
      const parsed: unknown = JSON.parse(value);
      if (parsed !== null && typeof parsed === "object") facts.jsonLd.parseable++;
      else facts.jsonLd.nonObject++;
    } catch { facts.jsonLd.invalid++; }
  }
  const check = (id: string, state: Check["state"], observation: string, why: string, action: string, recheck: string): Check => ({ id, state, observation, why, action, recheck });
  const titleOk = facts.titles.length === 1 && !!facts.titles[0];
  const h1Ok = facts.h1.length === 1 && !!facts.h1[0];
  let canonicalValid = false;
  let canonicalUnresolved = false;
  try {
    const canonical = facts.canonical.length === 1 && facts.canonical[0] ? new URL(facts.canonical[0], effectiveBase ?? undefined) : null;
    canonicalValid = !!canonical && ["https:", "http:"].includes(canonical.protocol) && !canonical.username && !canonical.password;
  } catch { canonicalUnresolved = !effectiveBase; }
  const restricted = facts.robots.some(({ content }) => /(?:^|[\s,])(?:noindex|none)(?:$|[\s,])/iu.test(content));
  const checks: Check[] = [
    check("title", facts.textClipped ? "unknown" : titleOk ? "observed" : "review", `${facts.titles.length} title element(s) in the supplied head${facts.titles[0] ? `: ${facts.titles[0]}` : "."}`, "The title names the page in browser tabs and can inform search result titles.", titleOk ? "Read the title and confirm it describes this page accurately." : "In the page head, keep one descriptive, non-empty <title> element.", "Paste fresh source and confirm one non-empty title."),
    check("h1", facts.textClipped ? "unknown" : h1Ok ? "observed" : "review", `${facts.h1.length} H1 element(s) in the supplied source${facts.h1[0] ? `: ${facts.h1[0]}` : "."}`, "A clear main heading helps readers identify the page topic. Multiple H1s are not a ranking penalty by themselves.", h1Ok ? "Confirm the main heading is visible and accurately names the page." : "Review the page outline. Give the main content a clear H1; use H2 for subordinate sections where appropriate.", "Paste fresh source and compare its H1s; check visibility in your browser."),
    check("robots", restricted ? "review" : "observed", `${facts.robots.length} robots meta declaration(s). ${restricted ? "A noindex or none token was detected." : "No noindex/none token detected in these declarations."}`, "Directives can apply to specific crawlers. Source alone cannot establish crawl or indexing eligibility.", restricted ? "If this page is intended for search, review the named crawler directives and remove an unintended noindex/none in your CMS. Preserve deliberate exclusions." : "Check HTTP X-Robots-Tag and robots.txt separately before drawing an eligibility conclusion.", "Paste fresh source and compare the named directives; separately verify response headers."),
    check("canonical", canonicalValid ? "observed" : canonicalUnresolved ? "unknown" : "review", `${facts.canonical.length} canonical declaration(s); ${canonicalValid ? "one resolves to an HTTP(S) URL." : "a single HTTP(S) canonical could not be resolved."}`, "A canonical declaration suggests the preferred URL; search engines may choose a different one.", canonicalUnresolved ? "Add the public page URL as context to resolve the relative canonical. Its validity is currently unknown." : canonicalValid ? "Confirm the declared URL is the intended preferred page and is reachable." : "If this page needs a canonical, set one link rel=canonical in the head to its intended preferred HTTPS URL.", "Paste fresh source and confirm one resolvable intended canonical. Reachability is a separate check."),
    check("links", facts.links ? "observed" : facts.unresolvedLinks ? "unknown" : "review", `${facts.links} HTTP(S) anchor(s) without rel=nofollow; ${facts.nofollowLinks} with nofollow; ${facts.unresolvedLinks} unresolved.`, "Ordinary anchors expose destinations in HTML. This count does not prove that any destination is crawlable or indexed.", facts.unresolvedLinks && !facts.links ? "Add the public page URL as context to resolve relative links. Check any invalid base element in the source." : facts.links ? "Inspect a relevant anchor and confirm its destination helps the reader." : "Where useful, add an ordinary <a href=\"/related-page\">descriptive link</a> to a relevant public page.", "Paste fresh source and compare HTTP(S) anchors; open the intended destination yourself."),
    check("jsonld", facts.jsonLd.invalid || facts.jsonLd.nonObject ? "review" : "observed", `${facts.jsonLd.total} JSON-LD block(s): ${facts.jsonLd.parseable} parseable object/array, ${facts.jsonLd.invalid} invalid JSON, ${facts.jsonLd.nonObject} non-object JSON. Other structured-markup attributes ${facts.otherStructuredMarkup ? "detected" : "not detected"}.`, "JSON syntax is only one prerequisite. This does not validate schema types, facts, rich results or other markup formats.", facts.jsonLd.invalid || facts.jsonLd.nonObject ? "Fix JSON syntax in application/ld+json blocks and use an object or array describing the actual page." : "Use structured data only where it fits real page content; validate applicable markup separately.", "Paste fresh source to recheck JSON syntax. Use a schema validator for meaning and eligibility."),
    check("network", "unknown", "HTTP status, redirects, X-Robots-Tag, robots.txt, crawl eligibility and indexing were not checked.", "No target URL is fetched, and a supplied source file cannot establish live server behavior.", "Verify the public response and crawler controls separately. Keep these facts unknown until observed.", "This source check cannot verify live HTTP or indexing changes."),
  ];
  return { facts, checks };
}

function response(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), { status, headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer", "X-Robots-Tag": "noindex", ...(status === 429 ? { "Retry-After": "60" } : {}), ...(status === 405 ? { Allow: "POST" } : {}) } });
}

export async function handlePageReadiness(request: Request, env: Pick<Env, "MCP_RATE_LIMIT">): Promise<Response> {
  const controller = new AbortController();
  let timer: ReturnType<typeof setTimeout> | undefined;
  const timeout = new Promise<never>((_, reject) => { timer = setTimeout(() => { controller.abort(); reject(new CheckError("TIMEOUT", "The check timed out. Try again with a smaller public source file.", 408)); }, PAGE_LIMITS.milliseconds); });
  try {
    return await Promise.race([timeout, (async () => {
      const endpoint = new URL(request.url);
      if (endpoint.protocol !== "https:" || endpoint.search) throw new CheckError("INVALID_ENDPOINT", "Use the HTTPS endpoint with a POST body and no query string.");
      if (request.method !== "POST") throw new CheckError("METHOD_NOT_ALLOWED", "Use POST with a JSON body.", 405);
      const origin = request.headers.get("Origin");
      if (origin && origin !== endpoint.origin) throw new CheckError("ORIGIN_NOT_ALLOWED", "Use this tool from the same site.", 403);
      if (request.headers.get("Content-Type")?.split(";")[0].trim().toLowerCase() !== "application/json") throw new CheckError("CONTENT_TYPE", "Use application/json.", 415);
      if (!env.MCP_RATE_LIMIT) throw new CheckError("UNAVAILABLE", "Abuse protection is unavailable. Please try again later.", 503);
      const rawIdentity = request.headers.get("CF-Connecting-IP") ?? "";
      const identity = rawIdentity.length <= 128 && /^[a-fA-F0-9.:]+$/u.test(rawIdentity) ? rawIdentity : "anonymous";
      let allowed: { success: boolean };
      try { allowed = await env.MCP_RATE_LIMIT.limit({ key: `base2026:page-readiness:v1:${identity}` }); }
      catch { throw new CheckError("UNAVAILABLE", "Abuse protection is unavailable. Please try again later.", 503); }
      if (controller.signal.aborted) throw new CheckError("TIMEOUT", "The check timed out.", 408);
      if (!allowed.success) throw new CheckError("RATE_LIMITED", "Too many checks. Wait a minute and try again.", 429);
      let input: unknown;
      try { input = JSON.parse(await boundedBody(request, controller.signal)); }
      catch (error) { if (error instanceof CheckError) throw error; throw new CheckError("INVALID_INPUT", "Provide valid UTF-8 JSON with a URL and optional public HTML."); }
      if (!input || typeof input !== "object" || Array.isArray(input)) throw new CheckError("INVALID_INPUT", "Provide an object with url and optional html.");
      const body = input as Record<string, unknown>;
      if (Object.keys(body).some((key) => !["url", "html"].includes(key))) throw new CheckError("INVALID_INPUT", "Only url and html fields are supported.");
      const url = body.url === undefined || body.url === "" ? null : pageSourceUrl(body.url);
      if (!url && (body.html === undefined || body.html === "")) throw new CheckError("INVALID_INPUT", "Paste or choose a complete public HTML page source.");
      if (body.html === undefined || body.html === "") return response({ version: "base2026.page-readiness.v1", state: "unknown", code: "LIVE_FETCH_UNSUPPORTED", message: unsupported, network: unknownNetwork, limits: PAGE_LIMITS }, 422);
      if (typeof body.html !== "string") throw new CheckError("INVALID_INPUT", "HTML must be a string.");
      const result = await inspectPageSource(body.html, url, controller.signal);
      return response({ version: "base2026.page-readiness.v1", state: "observed", mode: "supplied_source", checkedAt: new Date().toISOString(), url: url?.href ?? null, provenance: "User-supplied HTML. Not retrieved from or verified against the URL. Scripts are not rendered.", ...result, network: unknownNetwork, limits: PAGE_LIMITS });
    })()]);
  } catch (error) {
    const failure = error instanceof CheckError ? error : new CheckError("CHECK_UNAVAILABLE", "This source could not be checked. No page failure is inferred.", 422);
    return response({ version: "base2026.page-readiness.v1", state: "unknown", code: failure.code, message: failure.message, network: unknownNetwork }, failure.status);
  } finally { clearTimeout(timer); }
}
