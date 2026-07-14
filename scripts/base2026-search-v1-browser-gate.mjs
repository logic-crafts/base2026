#!/usr/bin/env node

import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { basename, join, resolve } from "node:path";

const require = createRequire(import.meta.url);

function parseArgs(argv) {
  const options = { baseUrl: "", out: "", searchUpstreamBase: "" };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--base-url") options.baseUrl = argv[++i];
    else if (arg === "--out") options.out = argv[++i];
    else if (arg === "--search-upstream-base") options.searchUpstreamBase = argv[++i];
    else throw new Error(`Unknown option: ${arg}`);
  }
  if (!options.baseUrl || !options.out) throw new Error("--base-url and --out are required");
  options.baseUrl = options.baseUrl.endsWith("/") ? options.baseUrl : `${options.baseUrl}/`;
  options.out = resolve(options.out);
  return options;
}

async function loadPlaywright() {
  try {
    return await import("playwright");
  } catch {
    for (const candidate of [
      process.env.PLAYWRIGHT_MODULE_PATH,
      "/opt/homebrew/lib/node_modules/playwright",
      "/usr/local/lib/node_modules/playwright",
    ].filter(Boolean)) {
      try {
        return require(candidate);
      } catch {
        // keep looking
      }
    }
  }
  throw new Error("Playwright is not importable; install it or set PLAYWRIGHT_MODULE_PATH.");
}

function sha256(buffer) {
  return createHash("sha256").update(buffer).digest("hex");
}

const VIEWPORTS = [
  { id: "mobile-390", width: 390, height: 844 },
  { id: "desktop-1440", width: 1440, height: 1000 },
];

async function installSearchUpstream(page, baseUrl, searchUpstreamBase) {
  if (!searchUpstreamBase) return;
  const localOrigin = new URL(baseUrl).origin;
  const upstream = searchUpstreamBase.endsWith("/") ? searchUpstreamBase : `${searchUpstreamBase}/`;
  await page.route(`${localOrigin}/knowledge-search/**`, async (route) => {
    const request = route.request();
    const localUrl = new URL(request.url());
    const relativePath = localUrl.pathname.replace(/^\/knowledge-search\/?/, "");
    const upstreamUrl = new URL(`${relativePath}${localUrl.search}`, upstream);
    const headers = { ...request.headers() };
    delete headers.host;
    delete headers.origin;
    delete headers.referer;
    try {
      const response = await route.fetch({
        url: upstreamUrl.href,
        method: request.method(),
        headers,
        postData: request.postData(),
        timeout: 30000,
      });
      await route.fulfill({ response });
    } catch (error) {
      const message = String(error?.message || error);
      if (/Route is already handled|Target page, context or browser has been closed/.test(message)) return;
      throw error;
    }
  });
}

async function inspectCanonical(page, baseUrl, viewport, out, searchUpstreamBase) {
  await installSearchUpstream(page, baseUrl, searchUpstreamBase);
  const sameOriginErrors = [];
  const consoleErrors = [];
  const pageErrors = [];
  const baseOrigin = new URL(baseUrl).origin;
  page.on("console", (message) => {
    if (message.type() === "error" && !/favicon/i.test(message.text())) consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("response", (response) => {
    if (new URL(response.url()).origin === baseOrigin && response.status() >= 400) {
      sameOriginErrors.push({ url: response.url(), status: response.status() });
    }
  });

  const target = `${baseUrl}?q=automation`;
  const response = await page.goto(target, { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForSelector('.ais-SearchBox-input[aria-label="Search"]', { timeout: 15000 });
  await page.waitForFunction(
    () => document.querySelector('.ais-SearchBox-input[aria-label="Search"]')?.value === "automation",
    null,
    { timeout: 15000 },
  );
  await page.waitForTimeout(1800);

  const diagnostics = await page.evaluate(() => {
    const header = document.querySelector(".ay-v2-header-shell");
    const main = document.querySelector("main");
    const footer = document.querySelector("footer.ay-site-footer");
    const resultItems = document.querySelectorAll(".ais-Hits-item").length;
    const styles = [...document.querySelectorAll('link[rel="stylesheet"]')].map((node) => node.href);
    const scripts = [...document.querySelectorAll("script[src]")].map((node) => node.src);
    const headerRect = header?.getBoundingClientRect();
    const mainRect = main?.getBoundingClientRect();
    return {
      url: location.href,
      body_classes: document.body.className,
      h1: document.querySelector("main h1")?.textContent?.trim() || "",
      query: document.querySelector(".ais-SearchBox-input")?.value || "",
      result_items: resultItems,
      header_present: Boolean(header),
      footer_present: Boolean(footer),
      search_command_present: Boolean(document.querySelector(".search-command__heading")),
      research_context_present: Boolean(document.querySelector(".research-context")),
      styles,
      scripts,
      client_width: document.documentElement.clientWidth,
      scroll_width: document.documentElement.scrollWidth,
      overflow_x: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
      header_width: headerRect?.width ?? null,
      main_width: mainRect?.width ?? null,
    };
  });

  const failures = [];
  if (response?.status() !== 200) failures.push(`canonical status ${response?.status()}`);
  if (!diagnostics.body_classes.includes("ay-alex-v4-static")) failures.push("ay-alex-v4-static body class missing");
  if (!diagnostics.body_classes.includes("base2026-search-v1")) failures.push("base2026-search-v1 body class missing");
  if (!diagnostics.header_present || !diagnostics.footer_present) failures.push("canonical shell missing");
  if (!diagnostics.search_command_present || !diagnostics.research_context_present) failures.push("Search V1 component hierarchy missing");
  if (!diagnostics.styles.some((value) => value.includes("alex-v4-static-shell.css"))) failures.push("shell CSS missing");
  if (!diagnostics.styles.some((value) => value.includes("base2026-search-v1.css"))) failures.push("Search V1 CSS missing");
  if (!diagnostics.scripts.some((value) => value.includes("base2026-search-v3.js"))) failures.push("Search V3 JS missing");
  if (diagnostics.query !== "automation") failures.push(`query=${diagnostics.query}`);
  if (diagnostics.result_items < 1) failures.push("no search results rendered");
  if (diagnostics.overflow_x) failures.push(`horizontal overflow ${diagnostics.scroll_width}>${diagnostics.client_width}`);
  if (sameOriginErrors.length) failures.push(`${sameOriginErrors.length} same-origin HTTP error(s)`);
  if (pageErrors.length) failures.push(`${pageErrors.length} page error(s)`);

  const screenshot = `search-v1--${viewport.id}.png`;
  await page.screenshot({ path: join(out, screenshot), fullPage: true });
  const result = { viewport, status: response?.status() ?? null, diagnostics, same_origin_errors: sameOriginErrors, console_errors: consoleErrors, page_errors: pageErrors, screenshot, failures };
  await page.unrouteAll({ behavior: "ignoreErrors" });
  await page.close();
  return result;
}

async function inspectAlias(page, baseUrl, aliasPath, searchUpstreamBase) {
  await installSearchUpstream(page, baseUrl, searchUpstreamBase);
  const target = `${baseUrl}${aliasPath}?q=automation#alias-proof`;
  const response = await page.goto(target, { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForURL(
    (url) =>
      url.pathname === new URL(baseUrl).pathname &&
      url.searchParams.get("q") === "automation" &&
      url.hash === "#alias-proof",
    { timeout: 10000 },
  );
  await page.waitForSelector(".ais-SearchBox-input", { timeout: 15000 });
  const finalUrl = page.url();
  const bodyClass = await page.locator("body").getAttribute("class");
  const failures = [];
  if (!bodyClass?.includes("base2026-search-v1")) failures.push("alias did not land on Search V1");
  const result = { alias_path: aliasPath, entry_url: target, entry_status: response?.status() ?? null, final_url: finalUrl, body_class: bodyClass, failures };
  await page.unrouteAll({ behavior: "ignoreErrors" });
  await page.close();
  return result;
}

async function inspectLegacyHash(page, baseUrl, searchUpstreamBase) {
  await installSearchUpstream(page, baseUrl, searchUpstreamBase);
  const target = `${baseUrl}#search?q=automation&creator=iamdandavies`;
  const response = await page.goto(target, { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForURL(
    (url) =>
      url.pathname === new URL(baseUrl).pathname &&
      url.searchParams.get("q") === "automation" &&
      url.searchParams.get("creator") === "iamdandavies" &&
      url.hash === "",
    { timeout: 10000 },
  );
  await page.waitForSelector(".ais-SearchBox-input", { timeout: 15000 });
  await page.waitForFunction(
    () => document.querySelector(".ais-SearchBox-input")?.value === "automation",
    null,
    { timeout: 15000 },
  );
  const query = await page.locator(".ais-SearchBox-input").inputValue();
  const finalUrl = page.url();
  const bodyClass = await page.locator("body").getAttribute("class");
  const failures = [];
  if (response?.status() !== 200) failures.push(`legacy hash status ${response?.status()}`);
  if (!bodyClass?.includes("base2026-search-v1")) failures.push("legacy hash did not land on Search V1");
  if (query !== "automation") failures.push(`legacy hash query=${query}`);
  const result = { entry_url: target, entry_status: response?.status() ?? null, final_url: finalUrl, query, body_class: bodyClass, failures };
  await page.unrouteAll({ behavior: "ignoreErrors" });
  await page.close();
  return result;
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const { chromium } = await loadPlaywright();
  await mkdir(options.out, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const report = {
    schema: "base2026.search-v1-browser-gate/v1",
    generated_at: new Date().toISOString(),
    base_url: options.baseUrl,
    search_upstream_base: options.searchUpstreamBase || null,
    results: [],
    aliases: [],
    legacy_hashes: [],
    failures: [],
  };
  try {
    for (const viewport of VIEWPORTS) {
      const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, deviceScaleFactor: 1 });
      const page = await context.newPage();
      const result = await inspectCanonical(page, options.baseUrl, viewport, options.out, options.searchUpstreamBase);
      report.results.push(result);
      if (result.failures.length) report.failures.push({ viewport: viewport.id, failures: result.failures });
      for (const aliasPath of ["search/", "search.html"]) {
        const aliasPage = await context.newPage();
        const alias = await inspectAlias(aliasPage, options.baseUrl, aliasPath, options.searchUpstreamBase);
        report.aliases.push({ viewport: viewport.id, ...alias });
        if (alias.failures.length) {
          report.failures.push({ viewport: viewport.id, alias_path: aliasPath, alias_failures: alias.failures });
        }
      }
      const legacyHashPage = await context.newPage();
      const legacyHash = await inspectLegacyHash(legacyHashPage, options.baseUrl, options.searchUpstreamBase);
      report.legacy_hashes.push({ viewport: viewport.id, ...legacyHash });
      if (legacyHash.failures.length) {
        report.failures.push({ viewport: viewport.id, legacy_hash_failures: legacyHash.failures });
      }
      await context.close();
    }
  } finally {
    await browser.close();
  }
  report.passed = report.failures.length === 0;
  const reportPath = join(options.out, "report.json");
  await writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
  const files = ["report.json", ...report.results.map((item) => item.screenshot)];
  const hashes = [];
  for (const file of files) {
    const data = await readFile(join(options.out, file));
    hashes.push({ path: basename(file), bytes: data.length, sha256: sha256(data) });
  }
  await writeFile(join(options.out, "SHA256SUMS.json"), `${JSON.stringify({ schema: "base2026.search-v1-browser-evidence-sha256/v1", files: hashes }, null, 2)}\n`, "utf8");
  console.log(`report=${reportPath}`);
  console.log(`passed=${report.passed}`);
  console.log(`failures=${report.failures.length}`);
  if (!report.passed) process.exitCode = 1;
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});
