#!/usr/bin/env node

import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { basename, join, resolve } from "node:path";

const require = createRequire(import.meta.url);

function parseArgs(argv) {
  const options = { baseUrl: "", out: "" };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--base-url") options.baseUrl = argv[++index];
    else if (arg === "--out") options.out = argv[++index];
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
        // Try the next known installation.
      }
    }
  }
  throw new Error("Playwright is not importable; install it or set PLAYWRIGHT_MODULE_PATH.");
}

function sha256(buffer) {
  return createHash("sha256").update(buffer).digest("hex");
}

function safeName(value) {
  return value.replace(/[^A-Za-z0-9._-]+/g, "-").slice(-110);
}

const VIEWPORTS = [
  { id: "mobile-320", width: 320, height: 568 },
  { id: "mobile-390", width: 390, height: 844 },
  { id: "desktop-1280", width: 1280, height: 900 },
  { id: "desktop-1440", width: 1440, height: 1000 },
];

const SAMPLES = [
  { family: "topic", route: "topics/wordpress-and-website-seo-settings.html", required: ".topic-page-hero,.page-hero", minDisclosures: 4, maxVisibleRepeated: 4 },
  { family: "compare", route: "compare/wordpress-and-website-seo-settings.html", required: ".comparison-grid", minDisclosures: 3, maxVisibleRepeated: 2 },
  { family: "compare-index", route: "compare/index.html", required: ".b26-k-directory-grid", minDisclosures: 1, maxVisibleRepeated: 12 },
  { family: "creator", route: "creators/webhivedigital.html", required: ".creator-page-hero,.page-hero", minDisclosures: 1, maxVisibleRepeated: 4 },
  { family: "topic-index", route: "topics/index.html", required: ".b26-k-directory-grid", minDisclosures: 1, maxVisibleRepeated: 12 },
  { family: "creator-index", route: "creators/index.html", required: ".b26-k-directory-grid", minDisclosures: 1, maxVisibleRepeated: 12 },
  { family: "source-index", route: "sources/index.html", required: ".b26-k-directory-grid", minDisclosures: 1, maxVisibleRepeated: 12 },
  { family: "document", route: "methodology.html", required: ".b26-k-document-body", documentContext: true, noDocumentRail: true },
  { family: "ai-visibility", route: "ai-visibility-pages/index.html", required: ".b26-k-reading-page", minDisclosures: 2, maxVisibleRepeated: 12 },
  { family: "ai-visibility", route: "ai-visibility-audit-for-local-service-businesses/index.html", required: ".b26-money-hero" },
  { family: "article", route: "roadmap-dataviz-test.html", required: "main.b26-k-article" },
];

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const { chromium } = await loadPlaywright();
  await mkdir(options.out, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const report = {
    schema: "base2026.whole-corpus-stitch-v1-browser-gate/v1",
    generated_at: new Date().toISOString(),
    base_url: options.baseUrl,
    viewports: VIEWPORTS,
    samples: SAMPLES,
    results: [],
    failures: [],
  };

  try {
    for (const viewport of VIEWPORTS) {
      const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, deviceScaleFactor: 1 });
      for (const sample of SAMPLES) {
        const page = await context.newPage();
        const targetUrl = new URL(sample.route, options.baseUrl).toString();
        const targetOrigin = new URL(targetUrl).origin;
        const consoleErrors = [];
        const pageErrors = [];
        const requestFailures = [];
        const badResponses = [];
        const failures = [];
        let status = null;
        let diagnostics = null;
        let screenshot = "";
        let screenshotSha256 = "";

        page.on("console", (message) => {
          if (message.type() === "error" && !/favicon/i.test(message.text())) consoleErrors.push(message.text());
        });
        page.on("pageerror", (error) => pageErrors.push(error.message));
        page.on("requestfailed", (request) => {
          if (new URL(request.url()).origin === targetOrigin) requestFailures.push({ url: request.url(), error: request.failure()?.errorText || "requestfailed" });
        });
        page.on("response", (response) => {
          if (new URL(response.url()).origin === targetOrigin && response.status() >= 400) badResponses.push({ url: response.url(), status: response.status() });
        });

        try {
          const response = await page.goto(targetUrl, { waitUntil: "domcontentloaded", timeout: 30000 });
          status = response?.status() ?? null;
          await page.waitForLoadState("networkidle", { timeout: 10000 }).catch(() => {});
          await page.waitForTimeout(350);

          diagnostics = await page.evaluate(({ family, required, documentContext, noDocumentRail, width, height }) => {
            const header = document.querySelector("header.ay-v2-header");
            const headerShell = document.querySelector(".ay-v2-header-shell");
            const main = document.querySelector("main.b26-k-main");
            const footer = document.querySelector("footer.ay-site-footer");
            const h1 = main?.querySelector("h1");
            const requiredNode = document.querySelector(required);
            const mainRect = main?.getBoundingClientRect();
            const headerRect = headerShell?.getBoundingClientRect();
            const banner = document.querySelector("[data-cookie-banner]");
            const bannerRect = banner?.getBoundingClientRect();
            const bannerStyle = banner ? getComputedStyle(banner) : null;
            const titleStyle = banner?.querySelector("h2") ? getComputedStyle(banner.querySelector("h2")) : null;
            const isVisible = (node) => {
              if (node.closest("details:not([open])") && !node.closest("summary")) return false;
              const rect = node.getBoundingClientRect();
              const style = getComputedStyle(node);
              return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
            };
            const cards = [...document.querySelectorAll(".b26-k-directory-grid:not(.b26-k-disclosure-grid) > .intelligence-card")].filter(isVisible);
            const cardTops = cards.map((card) => Math.round(card.getBoundingClientRect().top));
            const disclosures = [...document.querySelectorAll("details.b26-k-disclosure")];
            const visibleRepeated = [...document.querySelectorAll(".ai-pages-card,.b26-k-ledger-row,.comparison-group")].filter(isVisible);
            const localNavItems = [...document.querySelectorAll(".b26-k-local-nav > *")];
            const localNav = document.querySelector(".b26-k-local-nav");
            const localNavRects = localNavItems.map((item) => item.getBoundingClientRect());
            const localNavOverlap = localNavRects.some((rect, index) => {
              const next = localNavRects[index + 1];
              const sharesRow = Boolean(next && rect.bottom > next.top + 0.5 && next.bottom > rect.top + 0.5);
              return Boolean(next && sharesRow && rect.right > next.left + 0.5);
            });
            return {
              family,
              title: document.title,
              h1: h1?.textContent?.trim() || "",
              body_classes: document.body.className,
              main_classes: main?.className || "",
              canonical_shell: Boolean(header && headerShell && footer),
              required_component: Boolean(requiredNode),
              document_context: !documentContext || Boolean(document.querySelector(".page-hero .hero-actions .b26-k-document-context[role='note']")),
              document_rail_absent: !noDocumentRail || !document.querySelector(".b26-k-document-rail,.ayds-document-rail,.b26-k-document-layout,.ayds-document-layout"),
              legacy_shell_count: document.querySelectorAll("header.site-header,footer.site-footer").length,
              knowledge_css: [...document.styleSheets].some((sheet) => sheet.href?.includes("base2026-knowledge-stitch-v1.css")),
              client_width: document.documentElement.clientWidth,
              scroll_width: document.documentElement.scrollWidth,
              overflow_x: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
              main_width: mainRect?.width ?? null,
              header_width: headerRect?.width ?? null,
              main_within_header: Boolean(mainRect && headerRect && mainRect.width <= headerRect.width + 1),
              footer_sections: document.querySelectorAll(".ay-footer-grid > section,.ay-footer-grid > nav").length,
              directory_card_count: cards.length,
              directory_distinct_rows: new Set(cardTops).size,
              disclosure_count: disclosures.length,
              disclosure_open_count: disclosures.filter((node) => node.open).length,
              visible_repeated_count: visibleRepeated.length,
              local_nav_overlap: localNavOverlap,
              local_nav_clipped: Boolean(localNav && localNav.scrollWidth > localNav.clientWidth + 1),
              cookie_banner_present: Boolean(banner),
              cookie_banner_visible: Boolean(banner && !banner.hidden && bannerRect && bannerRect.width > 0 && bannerRect.height > 0),
              cookie_banner_inside_viewport: Boolean(!bannerRect || (bannerRect.left >= -1 && bannerRect.right <= width + 1 && bannerRect.top >= -1 && bannerRect.bottom <= height + 1)),
              cookie_background: bannerStyle?.backgroundColor || "",
              cookie_title_color: titleStyle?.color || "",
            };
          }, { family: sample.family, required: sample.required, documentContext: Boolean(sample.documentContext), noDocumentRail: Boolean(sample.noDocumentRail), width: viewport.width, height: viewport.height });

          if (status !== 200) failures.push(`document status ${status}, expected 200`);
          if (!diagnostics.canonical_shell) failures.push("canonical header/footer shell missing");
          if (!diagnostics.h1) failures.push("H1 missing");
          if (!diagnostics.body_classes.includes(`b26-family-${sample.family}`)) failures.push(`family class b26-family-${sample.family} missing`);
          if (!diagnostics.main_classes.includes("b26-k-main")) failures.push("b26-k-main class missing");
          if (!diagnostics.required_component) failures.push(`required component ${sample.required} missing`);
          if (!diagnostics.document_context) failures.push("document context is not placed in hero actions");
          if (!diagnostics.document_rail_absent) failures.push("legacy document rail/layout remains");
          if (diagnostics.legacy_shell_count) failures.push(`${diagnostics.legacy_shell_count} legacy shell node(s) remain`);
          if (!diagnostics.knowledge_css) failures.push("whole-corpus Stitch stylesheet not loaded");
          if (diagnostics.overflow_x) failures.push(`horizontal overflow ${diagnostics.scroll_width}>${diagnostics.client_width}`);
          if (!diagnostics.main_within_header) failures.push(`main width ${diagnostics.main_width} exceeds header ${diagnostics.header_width}`);
          if (diagnostics.footer_sections < 3) failures.push(`footer section count ${diagnostics.footer_sections}`);
          if (diagnostics.local_nav_overlap) failures.push("local navigation items overlap");
          if (viewport.width >= 1280 && diagnostics.local_nav_clipped) failures.push("desktop local navigation is clipped or horizontally scrollable");
          if (sample.family.endsWith("index") && diagnostics.directory_card_count > 1 && diagnostics.directory_distinct_rows >= diagnostics.directory_card_count && viewport.width >= 1280) failures.push("desktop directory collapsed to one card per row");
          if (sample.minDisclosures && diagnostics.disclosure_count < sample.minDisclosures) failures.push(`disclosure count ${diagnostics.disclosure_count}, expected at least ${sample.minDisclosures}`);
          if (sample.maxVisibleRepeated != null && diagnostics.visible_repeated_count > sample.maxVisibleRepeated) failures.push(`visible repeated items ${diagnostics.visible_repeated_count}, maximum ${sample.maxVisibleRepeated}`);
          if (diagnostics.disclosure_open_count) failures.push("disclosures must be closed on initial load");
          if (diagnostics.cookie_banner_visible && !diagnostics.cookie_banner_inside_viewport) failures.push("cookie banner leaves viewport");
          if (diagnostics.cookie_banner_visible && /rgba?\(0, 0, 0, 0\)/.test(diagnostics.cookie_background)) failures.push("cookie banner background is transparent");

          if (viewport.width <= 390) {
            const toggle = page.locator(".ay-v2-menu-toggle");
            if ((await toggle.count()) === 1) {
              await toggle.click();
              const expanded = await toggle.getAttribute("aria-expanded");
              const panelVisible = await page.locator("#ay-v2-mobile-panel").isVisible().catch(() => false);
              if (expanded !== "true" || !panelVisible) failures.push("mobile menu did not open");
              await toggle.click().catch(() => {});
            } else {
              failures.push("mobile menu toggle missing");
            }
          }

          if (diagnostics.disclosure_count) {
            const firstDisclosure = page.locator("details.b26-k-disclosure").first();
            const firstSummary = firstDisclosure.locator(":scope > summary");
            await firstSummary.click();
            if (!(await firstDisclosure.evaluate((node) => node.open))) failures.push("disclosure did not open");
            await firstSummary.click();
            if (await firstDisclosure.evaluate((node) => node.open)) failures.push("disclosure did not close");
          }

          if (sample.family === "topic" && [390, 1440].includes(viewport.width)) {
            const manage = page.locator("[data-cookie-manage]");
            if ((await manage.count()) === 1 && (await manage.isVisible())) {
              await manage.click();
              const dialog = page.locator("[data-cookie-dialog]");
              if (!(await dialog.isVisible())) failures.push("cookie preferences dialog did not open");
              const dialogInside = await dialog.evaluate((node) => {
                const rect = node.getBoundingClientRect();
                return rect.left >= -1 && rect.right <= innerWidth + 1 && rect.top >= -1 && rect.bottom <= innerHeight + 1;
              }).catch(() => false);
              if (!dialogInside) failures.push("cookie preferences dialog leaves viewport");
              await page.locator("[data-cookie-close]").click().catch(() => {});
            }
          }
          const reject = page.locator("[data-cookie-reject]");
          if ((await reject.count()) === 1 && (await reject.isVisible())) await reject.click();

          await page.evaluate(() => window.scrollTo(0, Math.min(900, document.documentElement.scrollHeight / 3)));
          await page.waitForTimeout(120);
          const scrolledHeaderVisible = await page.locator("header.ay-v2-header").isVisible().catch(() => false);
          if (!scrolledHeaderVisible) failures.push("canonical header not visible after scroll");
          await page.evaluate(() => window.scrollTo(0, 0));

          screenshot = `${safeName(sample.family)}--${safeName(sample.route)}--${viewport.id}.png`;
          const screenshotPath = join(options.out, screenshot);
          await page.screenshot({ path: screenshotPath, fullPage: true });
          screenshotSha256 = sha256(await readFile(screenshotPath));
        } catch (error) {
          failures.push(`navigation/browser check failed: ${error.message}`);
        }

        if (consoleErrors.length) failures.push(`${consoleErrors.length} console error(s)`);
        if (pageErrors.length) failures.push(`${pageErrors.length} page error(s)`);
        if (requestFailures.length) failures.push(`${requestFailures.length} same-origin request failure(s)`);
        if (badResponses.length) failures.push(`${badResponses.length} same-origin HTTP >=400 response(s)`);

        const result = {
          family: sample.family,
          route: sample.route,
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
        if (failures.length) report.failures.push({ family: sample.family, route: sample.route, viewport: viewport.id, failures });
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
  const files = ["report.json", ...report.results.map((item) => item.screenshot).filter(Boolean)].sort();
  const hashes = [];
  for (const file of files) {
    const data = await readFile(join(options.out, file));
    hashes.push({ path: basename(file), bytes: data.length, sha256: sha256(data) });
  }
  await writeFile(join(options.out, "SHA256SUMS.json"), `${JSON.stringify({ schema: "base2026.whole-corpus-stitch-v1-browser-evidence-sha256/v1", files: hashes }, null, 2)}\n`, "utf8");
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
