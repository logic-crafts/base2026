#!/usr/bin/env node

import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { basename, join, resolve } from "node:path";

const require = createRequire(import.meta.url);

function parseArgs(argv) {
  const options = { baseUrl: "", manifest: "", out: "", fullPage: true };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--base-url") options.baseUrl = argv[++index];
    else if (arg === "--manifest") options.manifest = argv[++index];
    else if (arg === "--out") options.out = argv[++index];
    else if (arg === "--viewport-only") options.fullPage = false;
    else throw new Error(`Unknown option: ${arg}`);
  }
  for (const key of ["baseUrl", "manifest", "out"]) {
    if (!options[key]) throw new Error(`--${key.replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`)} is required`);
  }
  options.baseUrl = options.baseUrl.endsWith("/") ? options.baseUrl : `${options.baseUrl}/`;
  options.manifest = resolve(options.manifest);
  options.out = resolve(options.out);
  return options;
}

async function loadPlaywright() {
  try {
    return await import("playwright");
  } catch {
    const candidates = [
      process.env.PLAYWRIGHT_MODULE_PATH,
      "/opt/homebrew/lib/node_modules/playwright",
      "/usr/local/lib/node_modules/playwright",
    ].filter(Boolean);
    for (const candidate of candidates) {
      try {
        return require(candidate);
      } catch {
        // Try the next known install location.
      }
    }
  }
  throw new Error("Playwright is not importable; install it or set PLAYWRIGHT_MODULE_PATH.");
}

function sha256(buffer) {
  return createHash("sha256").update(buffer).digest("hex");
}

function safeName(value) {
  return value.replace(/[^A-Za-z0-9._-]+/g, "-").slice(-96);
}

function selectSamples(manifest) {
  const normal = manifest.rendered.find((item) => item.admission_state === "normal_public_card");
  const archive = manifest.rendered.find((item) => item.admission_state === "provenance_archive_noindex");
  if (!normal || !archive) throw new Error("Manifest must contain normal and archive source routes.");
  return [normal, archive];
}

const VIEWPORTS = [
  { id: "mobile-320", width: 320, height: 568 },
  { id: "mobile-390", width: 390, height: 844 },
  { id: "desktop-1280", width: 1280, height: 900 },
  { id: "desktop-1440", width: 1440, height: 1000 },
];

const REQUIRED_SOURCE_BODY_CLASSES = [
  "ayds-root",
  "ayds-mode-product",
  "b26-family-source",
  "b26-source-v2",
];

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const manifest = JSON.parse(await readFile(options.manifest, "utf8"));
  const samples = selectSamples(manifest);
  const { chromium } = await loadPlaywright();
  await mkdir(options.out, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const report = {
    schema: "base2026.source-detail-v2-browser-gate/v1",
    generated_at: new Date().toISOString(),
    base_url: options.baseUrl,
    manifest: options.manifest,
    viewports: VIEWPORTS,
    samples: samples.map(({ route, admission_state }) => ({ route, admission_state })),
    results: [],
    failures: [],
  };

  try {
    for (const viewport of VIEWPORTS) {
      const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, deviceScaleFactor: 1 });
      for (const sample of samples) {
        const page = await context.newPage();
        const consoleErrors = [];
        const pageErrors = [];
        const requestFailures = [];
        const badResponses = [];
        const targetUrl = new URL(sample.route, options.baseUrl).toString();
        const targetOrigin = new URL(targetUrl).origin;

        page.on("console", (message) => {
          if (message.type() === "error" && !/favicon/i.test(message.text())) {
            consoleErrors.push(message.text());
          }
        });
        page.on("pageerror", (error) => pageErrors.push(error.message));
        page.on("requestfailed", (request) => {
          if (new URL(request.url()).origin === targetOrigin) {
            requestFailures.push({ url: request.url(), error: request.failure()?.errorText || "requestfailed" });
          }
        });
        page.on("response", (response) => {
          if (new URL(response.url()).origin === targetOrigin && response.status() >= 400) {
            badResponses.push({ url: response.url(), status: response.status() });
          }
        });

        const failures = [];
        let status = null;
        let diagnostics = null;
        let screenshot = "";
        let screenshotSha256 = "";
        try {
          const response = await page.goto(targetUrl, { waitUntil: "domcontentloaded", timeout: 30000 });
          status = response?.status() ?? null;
          await page.waitForLoadState("networkidle", { timeout: 10000 }).catch(() => {});
          await page.waitForTimeout(400);
          diagnostics = await page.evaluate(() => {
            const header = document.querySelector(".ay-v2-header-shell");
            const main = document.querySelector("main.b26-source-shell[data-admission-state]");
            const footer = document.querySelector("footer.ay-site-footer");
            const robots = document.querySelector('meta[name="robots"]')?.getAttribute("content") || "";
            const h1 = document.querySelector("main h1")?.textContent?.trim() || "";
            const headerRect = header?.getBoundingClientRect();
            const mainRect = main?.getBoundingClientRect();
            return {
              title: document.title,
              h1,
              robots,
              admission_state: main?.getAttribute("data-admission-state") || "",
              body_classes: document.body.className,
              header_present: Boolean(header),
              footer_present: Boolean(footer),
              footer_sections: document.querySelectorAll(".ay-footer-grid > section, .ay-footer-grid > nav").length,
              scroll_width: document.documentElement.scrollWidth,
              client_width: document.documentElement.clientWidth,
              overflow_x: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
              header_width: headerRect?.width ?? null,
              main_width: mainRect?.width ?? null,
              main_within_header: Boolean(headerRect && mainRect && mainRect.width <= headerRect.width + 1),
            };
          });

          if (status !== 200) failures.push(`document status ${status}, expected 200`);
          if (!diagnostics.header_present) failures.push("canonical .ay-v2-header-shell missing");
          if (!diagnostics.footer_present) failures.push("canonical .ay-site-footer missing");
          if (!diagnostics.h1) failures.push("source H1 missing");
          const bodyClasses = new Set(diagnostics.body_classes.split(/\s+/).filter(Boolean));
          for (const className of REQUIRED_SOURCE_BODY_CLASSES) {
            if (!bodyClasses.has(className)) failures.push(`${className} body class missing`);
          }
          if (diagnostics.admission_state !== sample.admission_state) failures.push(`admission state ${diagnostics.admission_state}, expected ${sample.admission_state}`);
          if (sample.admission_state === "provenance_archive_noindex" && !/noindex/i.test(diagnostics.robots)) failures.push("archive route lacks noindex");
          if (sample.admission_state === "normal_public_card" && /noindex/i.test(diagnostics.robots)) failures.push("normal route unexpectedly has noindex");
          if (diagnostics.overflow_x) failures.push(`horizontal overflow ${diagnostics.scroll_width}>${diagnostics.client_width}`);
          if (!diagnostics.main_within_header) failures.push(`main width ${diagnostics.main_width} exceeds header ${diagnostics.header_width}`);

          screenshot = `${safeName(sample.route)}--${viewport.id}.png`;
          const screenshotPath = join(options.out, screenshot);
          await page.screenshot({ path: screenshotPath, fullPage: options.fullPage });
          screenshotSha256 = sha256(await readFile(screenshotPath));
        } catch (error) {
          failures.push(`navigation/browser check failed: ${error.message}`);
        }

        if (consoleErrors.length) failures.push(`${consoleErrors.length} console error(s)`);
        if (pageErrors.length) failures.push(`${pageErrors.length} page error(s)`);
        if (requestFailures.length) failures.push(`${requestFailures.length} same-origin request failure(s)`);
        if (badResponses.length) failures.push(`${badResponses.length} same-origin HTTP >=400 response(s)`);

        const result = {
          route: sample.route,
          admission_state: sample.admission_state,
          viewport,
          target_url: targetUrl,
          status,
          diagnostics,
          console_errors: consoleErrors,
          page_errors: pageErrors,
          request_failures: requestFailures,
          bad_responses: badResponses,
          screenshot,
          screenshot_sha256: screenshotSha256,
          failures,
        };
        report.results.push(result);
        if (failures.length) report.failures.push({ route: sample.route, viewport: viewport.id, failures });
        await page.close();
      }
      await context.close();
    }
  } finally {
    await browser.close();
  }

  report.passed = report.failures.length === 0;
  const reportPath = join(options.out, "report.json");
  await writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
  const manualReview = [
    "# Source Detail v2 browser evidence",
    "",
    `- Generated: ${report.generated_at}`,
    `- Base URL: ${report.base_url}`,
    `- Result: ${report.passed ? "PASS" : "FAIL"}`,
    `- Browser checks: ${report.results.length}`,
    `- Failures: ${report.failures.length}`,
    "- Coverage: normal + archive source states at 320, 390, 1280, and 1440 px; canonical shell; noindex contract; overflow; main/header width; console; page errors; same-origin request/HTTP failures; screenshots.",
    "",
  ].join("\n");
  await writeFile(join(options.out, "MANUAL_REVIEW.md"), `${manualReview}\n`, "utf8");

  const files = ["MANUAL_REVIEW.md", "report.json", ...report.results.map((item) => item.screenshot).filter(Boolean)].sort();
  const hashes = [];
  for (const file of files) {
    const data = await readFile(join(options.out, file));
    hashes.push({ path: basename(file), sha256: sha256(data), bytes: data.length });
  }
  await writeFile(join(options.out, "SHA256SUMS.json"), `${JSON.stringify({ schema: "base2026.source-detail-v2-browser-evidence-sha256/v1", files: hashes }, null, 2)}\n`, "utf8");

  console.log(`report=${reportPath}`);
  console.log(`passed=${report.passed}`);
  console.log(`checks=${report.results.length}`);
  console.log(`failures=${report.failures.length}`);
  if (!report.passed) process.exitCode = 1;
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});
