#!/usr/bin/env node

import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { basename, join, resolve } from "node:path";

const require = createRequire(import.meta.url);
const SOURCE_ID = "tiktok-video-7660551196687617287";
const SOLUTION_ID = "google-business-profile-visibility-audit";
const APPROVED_SOLUTION_IDS = new Set([
  "answer-ready-service-page-checklist",
  "content-refresh-prioritization",
  "google-business-profile-visibility-audit",
  "measure-ai-search-visibility",
  "search-console-high-impression-low-ctr",
]);
const VIEWPORTS = [
  { id: "mobile-390", width: 390, height: 844 },
  { id: "desktop-1440", width: 1440, height: 1000 },
];

function parseArgs(argv) {
  const options = { baseUrl: "", releaseRoot: "", out: "" };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--base-url") options.baseUrl = argv[++index];
    else if (arg === "--release-root") options.releaseRoot = argv[++index];
    else if (arg === "--out") options.out = argv[++index];
    else throw new Error(`Unknown option: ${arg}`);
  }
  if (!options.baseUrl || !options.releaseRoot || !options.out) throw new Error("--base-url, --release-root and --out are required");
  options.baseUrl = options.baseUrl.endsWith("/") ? options.baseUrl : `${options.baseUrl}/`;
  options.releaseRoot = resolve(options.releaseRoot);
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
        // Try the next known installation.
      }
    }
  }
  throw new Error("Playwright is not importable");
}

function sha256(buffer) {
  return createHash("sha256").update(buffer).digest("hex");
}

async function fixtureDocument(releaseRoot) {
  const lines = (await readFile(join(releaseRoot, "web/static/documents.jsonl"), "utf8")).split(/\r?\n/);
  for (const line of lines) {
    if (!line.trim()) continue;
    const row = JSON.parse(line);
    if (row.item_id === SOURCE_ID) return row;
  }
  throw new Error(`Fixture source ${SOURCE_ID} is missing`);
}

function searchResponse(hit, body) {
  let query = "";
  try {
    query = JSON.parse(body || "{}").queries?.[0]?.q || "";
  } catch {
    query = "";
  }
  return {
    results: [{
      indexUid: "base2026_public_tiktok",
      hits: [{ ...hit, _formatted: { ...hit }, _matchesPosition: {} }],
      query,
      processingTimeMs: 1,
      limit: 20,
      offset: 0,
      estimatedTotalHits: 1,
      totalHits: 1,
      totalPages: 1,
      totalResults: 1,
      facetDistribution: {
        handle: { [hit.handle]: 1 },
        source_type: { [hit.source_type]: 1 },
        year: { [hit.year]: 1 },
      },
      facetStats: {},
    }],
  };
}

async function prepareContext(browser, options, viewport, analytics, hit) {
  const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, deviceScaleFactor: 1 });
  const externalRequests = [];
  const serviceSubmissionRequests = [];
  await context.addInitScript(({ allowed }) => {
    localStorage.setItem("ay_cookie_preferences_v1", JSON.stringify({ necessary: true, analytics: allowed, marketing: false, updatedAt: "2026-07-17T00:00:00Z" }));
    const existing = JSON.parse(sessionStorage.getItem("base2026_p4_test_events") || "[]");
    window.addEventListener("base2026:product-truth-event", (event) => {
      existing.push(event.detail);
      sessionStorage.setItem("base2026_p4_test_events", JSON.stringify(existing));
    });
    document.addEventListener("submit", () => {
      if (!location.pathname.endsWith("/apply-research.html")) return;
      const count = Number(sessionStorage.getItem("base2026_p4_apply_form_submits") || "0");
      sessionStorage.setItem("base2026_p4_apply_form_submits", String(count + 1));
    }, true);
  }, { allowed: analytics });
  const origin = new URL(options.baseUrl).origin;
  await context.route("**/*", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.pathname === "/knowledge-search/multi-search") {
      await new Promise((resolveDelay) => setTimeout(resolveDelay, 220));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(searchResponse(hit, request.postData())),
      });
      return;
    }
    if (!["GET", "HEAD", "OPTIONS"].includes(request.method())) {
      serviceSubmissionRequests.push({ method: request.method(), path: url.pathname });
    }
    if (url.origin !== origin) {
      externalRequests.push({ host: url.hostname, resource_type: request.resourceType() });
      await route.abort("blockedbyclient");
      return;
    }
    if (url.pathname === "/knowledge" || url.pathname.startsWith("/knowledge/")) {
      const rewrittenPath = url.pathname.replace(/^\/knowledge/, "") || "/";
      const rewritten = new URL(`${rewrittenPath}${url.search}`, `${origin}/`);
      await route.continue({ url: rewritten.href });
      return;
    }
    await route.continue();
  });
  return { context, externalRequests, serviceSubmissionRequests };
}

async function eventLog(page) {
  return page.evaluate(() => JSON.parse(sessionStorage.getItem("base2026_p4_test_events") || "[]"));
}

function count(events, name) {
  return events.filter((event) => event.event === name).length;
}

function validatePayloads(events) {
  const allowed = {
    product_search_submitted: ["event", "query_length_bucket", "result_count_bucket", "origin_surface"],
    source_opened: ["event", "public_source_id", "origin_surface", "admission_class"],
    evidence_actioned: ["event", "action_type", "public_source_id", "origin_surface"],
    solution_opened: ["event", "solution_id", "origin_surface"],
    research_bridge_clicked: ["event", "bridge_id", "destination_id", "origin_surface"],
  };
  const forbiddenKeys = new Set([
    "raw_query", "query_text", "search_term", "raw_filter_text", "email", "name", "phone",
    "website", "notes", "message", "page_referrer", "page_location", "full_url", "private_source_id",
  ]);
  const queryBuckets = new Set(["0_terms", "1_2_terms", "3_5_terms", "6_plus_terms"]);
  const resultBuckets = new Set(["0", "1_10", "11_50", "51_plus"]);
  const sourceId = /^[a-z0-9]+(?:-[a-z0-9]+)+$/;
  const failures = [];
  for (const [index, event] of events.entries()) {
    if (!allowed[event.event]) {
      failures.push(`event ${index} has unknown id ${event.event}`);
      continue;
    }
    const extra = Object.keys(event).filter((key) => !allowed[event.event].includes(key));
    if (extra.length) failures.push(`event ${index} has undeclared properties ${extra.join(",")}`);
    const forbidden = Object.keys(event).filter((key) => forbiddenKeys.has(key));
    if (forbidden.length) failures.push(`event ${index} contains forbidden properties ${forbidden.join(",")}`);
    if (event.query_length_bucket && !queryBuckets.has(event.query_length_bucket)) failures.push(`event ${index} has invalid query bucket`);
    if (event.result_count_bucket && !resultBuckets.has(event.result_count_bucket)) failures.push(`event ${index} has invalid result bucket`);
    if (event.event === "product_search_submitted" && !new Set(["knowledge_home", "search"]).has(event.origin_surface)) failures.push(`event ${index} has invalid search origin`);
    if (event.event === "source_opened" && (!sourceId.test(event.public_source_id || "") || event.admission_class !== "normal_public_card" || !new Set(["search", "solution", "source_detail"]).has(event.origin_surface))) failures.push(`event ${index} has invalid public source domain`);
    if (event.event === "evidence_actioned" && (!new Set(["copy_citation", "copy_link"]).has(event.action_type) || !sourceId.test(event.public_source_id || "") || !new Set(["search", "source_detail"]).has(event.origin_surface))) failures.push(`event ${index} has invalid evidence domain`);
    if (event.event === "solution_opened" && (!APPROVED_SOLUTION_IDS.has(event.solution_id) || !new Set(["search", "solution", "source_detail"]).has(event.origin_surface))) failures.push(`event ${index} has invalid Solution domain`);
    if (event.event === "research_bridge_clicked" && (event.bridge_id !== "solution_to_apply_research" || event.destination_id !== "apply_research" || event.origin_surface !== "solution")) failures.push(`event ${index} has invalid bridge domain`);
    const serialized = JSON.stringify(event).toLowerCase();
    if (serialized.includes("google business profile") || serialized.includes("http://") || serialized.includes("https://") || serialized.includes("@example")) {
      failures.push(`event ${index} contains fixture query, URL or email-like value`);
    }
  }
  return failures;
}

async function journey(page, options, viewport, analytics, externalRequests, serviceSubmissionRequests) {
  const failures = [];
  const consoleErrors = [];
  const pageErrors = [];
  page.on("console", (message) => {
    if (message.type() === "error" && !/favicon|ERR_BLOCKED_BY_CLIENT|Failed to load resource/i.test(message.text())) consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await page.goto(options.baseUrl, { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForSelector(".ais-SearchBox-input", { timeout: 15000 });
  await page.locator(".ais-SearchBox-input").fill("google business profile");
  await page.locator(".ais-SearchBox-input").press("Enter");
  await page.waitForTimeout(60);
  const beforeResults = await eventLog(page);
  if (count(beforeResults, "product_search_submitted") !== 0) failures.push("search event fired before results response/render");
  await page.waitForSelector(".view-source-detail", { timeout: 15000 });
  if (analytics) {
    await page.waitForFunction(() => (JSON.parse(sessionStorage.getItem("base2026_p4_test_events") || "[]")).some((row) => row.event === "product_search_submitted"));
  }
  const buttonItemId = await page.locator(".view-source-detail").first().getAttribute("data-item-id");
  if (buttonItemId !== SOURCE_ID) throw new Error(`Search fixture item mismatch: ${buttonItemId || "missing"}`);
  await page.locator(".view-source-detail").click();
  try {
    await page.locator(`#source-detail-panel [data-source-item-id="${SOURCE_ID}"]`).waitFor({ state: "attached", timeout: 15000 });
  } catch (error) {
    const diagnostic = await page.evaluate(() => ({
      body_source_open: document.body.classList.contains("source-detail-open"),
      panel_active: document.querySelector("#source-detail-panel")?.classList.contains("is-active") || false,
      panel_heading: document.querySelector("#source-detail-panel h2")?.textContent?.trim() || "",
    }));
    throw new Error(`Source panel did not render: ${JSON.stringify(diagnostic)}; ${error.message}`);
  }
  await page.locator('#source-detail-panel #solutions [data-journey-action="solution_opened"]').waitFor({ state: "attached", timeout: 15000 });
  if (analytics) {
    await page.waitForFunction(() => (JSON.parse(sessionStorage.getItem("base2026_p4_test_events") || "[]")).some((row) => row.event === "source_opened"));
  }
  await page.waitForTimeout(250);
  const sourceEvents = await eventLog(page);
  if (analytics && count(sourceEvents, "source_opened") !== 1) failures.push(`source_opened count ${count(sourceEvents, "source_opened")}, expected 1`);
  if (!analytics && sourceEvents.length) failures.push(`no-consent journey emitted ${sourceEvents.length} event(s)`);
  const sourceShot = `source-bridge--${viewport.id}--${analytics ? "consent" : "no-consent"}.png`;
  await page.screenshot({ path: join(options.out, sourceShot), fullPage: true });

  await page.locator('#source-detail-panel [data-share-action="copy-link"]').first().click();
  if (analytics) await page.waitForFunction(() => (JSON.parse(sessionStorage.getItem("base2026_p4_test_events") || "[]")).some((row) => row.event === "evidence_actioned"));
  await page.locator('#source-detail-panel [data-journey-action="solution_opened"]').first().click();
  await page.waitForURL(`**/knowledge/solutions/${SOLUTION_ID}.html`, { timeout: 15000 });
  await page.waitForSelector('main.solution-page [data-research-bridge="solution_to_apply_research"]', { timeout: 15000 });
  if (analytics) await page.waitForFunction(() => (JSON.parse(sessionStorage.getItem("base2026_p4_test_events") || "[]")).some((row) => row.event === "solution_opened"));
  if (analytics) {
    const invalidGate = await page.evaluate(() => {
      const truth = window.__BASE2026_PRODUCT_TRUTH__;
      const before = JSON.parse(sessionStorage.getItem("base2026_p4_test_events") || "[]").length;
      const invalidValue = truth?.emit("solution_opened", { solution_id: "unapproved-solution", origin_surface: "solution" });
      const invalidProperty = truth?.emit("solution_opened", { solution_id: "google-business-profile-visibility-audit", origin_surface: "solution", raw_query: "private" });
      const after = JSON.parse(sessionStorage.getItem("base2026_p4_test_events") || "[]").length;
      return { runtime: Boolean(truth), invalidValue, invalidProperty, before, after };
    });
    if (!invalidGate.runtime || invalidGate.invalidValue !== false || invalidGate.invalidProperty !== false || invalidGate.after !== invalidGate.before) {
      failures.push(`runtime value-domain gate failed: ${JSON.stringify(invalidGate)}`);
    }
  }
  const solutionDiagnostics = await page.evaluate(() => ({
    client_width: document.documentElement.clientWidth,
    scroll_width: document.documentElement.scrollWidth,
  }));
  if (solutionDiagnostics.scroll_width > solutionDiagnostics.client_width + 1) {
    failures.push(`Solution horizontal overflow ${solutionDiagnostics.scroll_width}>${solutionDiagnostics.client_width}`);
  }
  const solutionShot = `solution--${viewport.id}--${analytics ? "consent" : "no-consent"}.png`;
  await page.screenshot({ path: join(options.out, solutionShot), fullPage: true });
  await page.locator('[data-research-bridge="solution_to_apply_research"]').click();
  await page.waitForURL("**/knowledge/apply-research.html", { timeout: 15000 });
  await page.waitForSelector("main#content h1", { timeout: 15000 });
  await page.waitForTimeout(100);
  const events = await eventLog(page);
  if (analytics) {
    const expected = {
      product_search_submitted: 1,
      source_opened: 1,
      evidence_actioned: 1,
      solution_opened: 1,
      research_bridge_clicked: 1,
    };
    for (const [name, expectedCount] of Object.entries(expected)) {
      if (count(events, name) !== expectedCount) failures.push(`${name} count ${count(events, name)}, expected ${expectedCount}`);
    }
    const searchEvent = events.find((row) => row.event === "product_search_submitted");
    if (searchEvent?.query_length_bucket !== "3_5_terms" || searchEvent?.result_count_bucket !== "1_10") {
      failures.push("search event buckets do not match the one-result fixture");
    }
    failures.push(...validatePayloads(events));
  } else if (events.length) {
    failures.push(`no-consent completed journey emitted ${events.length} event(s)`);
  }
  const applyFormSubmitCount = await page.evaluate(() => Number(sessionStorage.getItem("base2026_p4_apply_form_submits") || "0"));
  if (applyFormSubmitCount !== 0) failures.push(`Apply Research form submit count ${applyFormSubmitCount}, expected 0`);
  if (serviceSubmissionRequests.length) failures.push(`${serviceSubmissionRequests.length} service submission request(s)`);
  const applyShot = `apply-research--${viewport.id}--${analytics ? "consent" : "no-consent"}.png`;
  await page.screenshot({ path: join(options.out, applyShot), fullPage: true });
  const diagnostics = await page.evaluate(() => ({
    current_path: location.pathname,
    apply_research_rendered: Boolean(document.querySelector("main#content h1")),
    apply_research_heading: document.querySelector("main#content h1")?.textContent?.trim() || "",
    client_width: document.documentElement.clientWidth,
    scroll_width: document.documentElement.scrollWidth,
  }));
  if (!diagnostics.apply_research_rendered) failures.push("Apply Research destination did not render");
  if (diagnostics.scroll_width > diagnostics.client_width + 1) failures.push(`horizontal overflow ${diagnostics.scroll_width}>${diagnostics.client_width}`);
  if (consoleErrors.length) failures.push(`${consoleErrors.length} console error(s)`);
  if (pageErrors.length) failures.push(`${pageErrors.length} page error(s)`);
  if (externalRequests.length) failures.push(`${externalRequests.length} external browser request(s)`);
  return {
    viewport,
    analytics_consent: analytics,
    events,
    diagnostics,
    solution_diagnostics: solutionDiagnostics,
    apply_research_form_submit_count: applyFormSubmitCount,
    service_submission_request_count: serviceSubmissionRequests.length,
    external_request_count: externalRequests.length,
    external_request_hosts: [...new Set(externalRequests.map((row) => row.host))].sort(),
    console_errors: consoleErrors,
    page_errors: pageErrors,
    screenshots: [sourceShot, solutionShot, applyShot],
    failures,
  };
}

async function staticSource(page, options, viewport, externalRequests, serviceSubmissionRequests) {
  const failures = [];
  const url = new URL(`sources/${SOURCE_ID}.html`, options.baseUrl).href;
  const response = await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForSelector('main[data-admission-state="normal_public_card"]#content #solutions', { timeout: 15000 });
  await page.waitForFunction(() => (JSON.parse(sessionStorage.getItem("base2026_p4_test_events") || "[]")).some((row) => row.event === "source_opened"));
  await page.waitForTimeout(150);
  const events = await eventLog(page);
  if (response?.status() !== 200) failures.push(`static source status ${response?.status()}`);
  if (count(events, "source_opened") !== 1) failures.push(`static source_opened count ${count(events, "source_opened")}`);
  if (await page.locator('#solutions a[data-journey-action="solution_opened"][data-solution-id="google-business-profile-visibility-audit"]').count() !== 1) {
    failures.push("static evidence-bound Solution anchor missing or duplicated");
  }
  if (externalRequests.length) failures.push(`${externalRequests.length} external browser request(s)`);
  if (serviceSubmissionRequests.length) failures.push(`${serviceSubmissionRequests.length} service submission request(s)`);
  const screenshot = `static-source--${viewport.id}.png`;
  await page.screenshot({ path: join(options.out, screenshot), fullPage: true });
  return {
    viewport,
    events,
    service_submission_request_count: serviceSubmissionRequests.length,
    external_request_count: externalRequests.length,
    external_request_hosts: [...new Set(externalRequests.map((row) => row.host))].sort(),
    screenshot,
    failures,
  };
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const hit = await fixtureDocument(options.releaseRoot);
  const { chromium } = await loadPlaywright();
  await mkdir(options.out, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const report = {
    schema: "base2026.phase1-base-p4-browser-gate/v1",
    release_name: basename(options.releaseRoot),
    fixture_source_id: SOURCE_ID,
    fixture_solution_id: SOLUTION_ID,
    results: [],
    static_results: [],
    failures: [],
  };
  try {
    for (const viewport of VIEWPORTS) {
      for (const analytics of [false, true]) {
        const { context, externalRequests, serviceSubmissionRequests } = await prepareContext(browser, options, viewport, analytics, hit);
        const page = await context.newPage();
        const result = await journey(page, options, viewport, analytics, externalRequests, serviceSubmissionRequests);
        report.results.push(result);
        if (result.failures.length) report.failures.push({ viewport: viewport.id, analytics, failures: result.failures });
        await context.close();
      }
      const { context, externalRequests, serviceSubmissionRequests } = await prepareContext(browser, options, viewport, true, hit);
      const page = await context.newPage();
      const result = await staticSource(page, options, viewport, externalRequests, serviceSubmissionRequests);
      report.static_results.push(result);
      if (result.failures.length) report.failures.push({ viewport: viewport.id, static_source: true, failures: result.failures });
      await context.close();
    }
  } finally {
    await browser.close();
  }
  const allResults = [...report.results, ...report.static_results];
  report.external_request_count = allResults.reduce((sum, row) => sum + row.external_request_count, 0);
  report.external_request_hosts = [...new Set(allResults.flatMap((row) => row.external_request_hosts))].sort();
  report.service_submission_request_count = allResults.reduce((sum, row) => sum + row.service_submission_request_count, 0);
  const measurementEvents = report.results
    .filter((row) => row.analytics_consent)
    .flatMap((row) => row.events);
  report.measurement_event_fixture = "measurement-events.json";
  report.measurement_event_count = measurementEvents.length;
  report.passed = report.failures.length === 0;
  const reportPath = join(options.out, "report.json");
  await writeFile(join(options.out, "measurement-events.json"), `${JSON.stringify(measurementEvents, null, 2)}\n`, "utf8");
  await writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
  const files = [
    "measurement-events.json",
    "report.json",
    ...report.results.flatMap((row) => row.screenshots),
    ...report.static_results.map((row) => row.screenshot),
  ].sort();
  const hashes = [];
  for (const file of files) {
    const data = await readFile(join(options.out, file));
    hashes.push({ path: file, sha256: sha256(data), bytes: data.length });
  }
  await writeFile(join(options.out, "SHA256SUMS.json"), `${JSON.stringify({ schema: "base2026.phase1-base-p4-browser-evidence/v1", files: hashes }, null, 2)}\n`, "utf8");
  console.log(`report=${reportPath}`);
  console.log(`passed=${report.passed}`);
  console.log(`journeys=${report.results.length}`);
  console.log(`static_checks=${report.static_results.length}`);
  console.log(`failures=${report.failures.length}`);
  if (!report.passed) process.exitCode = 1;
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});
