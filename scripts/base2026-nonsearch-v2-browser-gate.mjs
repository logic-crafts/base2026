#!/usr/bin/env node
import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { join } from "node:path";


const require = createRequire(import.meta.url);


const ROUTES = [
  { id: "topic-detail", route: "topics/content-repurposing.html", required: ["B26-07", "B26-09"], forbiddenHero: "B26-05" },
  { id: "topics-hub", route: "topics/index.html", required: ["B26-05"] },
  { id: "creator", route: "creators/neilpatel.html", required: ["B26-07"], forbiddenHero: "B26-06" },
  { id: "source", route: "sources/tiktok-video-7388244947352210734.html", required: ["B26-04", "B26-08"] },
  { id: "compare", route: "compare/content-repurposing.html", required: ["B26-06"], forbiddenHero: "B26-06" },
];

const VIEWPORTS = [
  { id: "desktop-1440", width: 1440, height: 1000, h1Max: 48, footerMax: 420 },
  { id: "mobile-390", width: 390, height: 844, h1Max: 36.1, footerMax: 720 },
  { id: "mobile-320", width: 320, height: 720, h1Max: 36.1, footerMax: 720 },
];


function parseArgs(argv) {
  const options = { baseUrl: "", out: "" };
  for (let index = 2; index < argv.length; index += 1) {
    if (argv[index] === "--base-url") options.baseUrl = argv[++index] || "";
    else if (argv[index] === "--out") options.out = argv[++index] || "";
    else throw new Error(`Unknown argument: ${argv[index]}`);
  }
  if (!options.baseUrl || !options.out) throw new Error("Usage: --base-url URL --out DIR");
  return options;
}


async function loadPlaywright() {
  try {
    const loaded = await import("playwright");
    return loaded.chromium ? loaded : loaded.default;
  } catch {
    for (const candidate of [
      process.env.PLAYWRIGHT_MODULE_PATH,
      "/opt/homebrew/lib/node_modules/playwright",
      "/usr/local/lib/node_modules/playwright",
    ].filter(Boolean)) {
      try {
        return require(candidate);
      } catch {
        // Try the next deterministic global installation.
      }
    }
  }
  throw new Error("Playwright is not importable");
}


function sha256(buffer) {
  return createHash("sha256").update(buffer).digest("hex");
}


async function main() {
  const options = parseArgs(process.argv);
  await mkdir(options.out, { recursive: false });
  const { chromium } = await loadPlaywright();
  const browser = await chromium.launch({ headless: true });
  const results = [];
  try {
    for (const route of ROUTES) {
      for (const viewport of VIEWPORTS) {
        const page = await browser.newPage({ viewport: { width: viewport.width, height: viewport.height } });
        await page.addInitScript(() => {
          localStorage.setItem(
            "ay_cookie_preferences_v1",
            JSON.stringify({ necessary: true, analytics: false, marketing: false, updatedAt: "fixture" }),
          );
        });
        const consoleErrors = [];
        const pageErrors = [];
        const sameOriginFailures = [];
        page.on("console", (message) => {
          if (message.type() === "error") consoleErrors.push(message.text());
        });
        page.on("pageerror", (error) => pageErrors.push(String(error)));
        page.on("requestfailed", (request) => {
          try {
            if (new URL(request.url()).origin === new URL(options.baseUrl).origin) {
              sameOriginFailures.push(`${request.method()} ${request.url()} ${request.failure()?.errorText || "failed"}`);
            }
          } catch {
            sameOriginFailures.push(request.url());
          }
        });
        const url = new URL(route.route, `${options.baseUrl.replace(/\/$/, "")}/`).href;
        const response = await page.goto(url, { waitUntil: "networkidle", timeout: 30000 });
        const diagnostics = await page.evaluate(({ required, forbiddenHero }) => {
          const root = document.body;
          const h1 = document.querySelector("main h1");
          const header = document.querySelector("header.b26-product-header");
          const footer = document.querySelector("footer.b26-product-footer");
          const components = [...document.querySelectorAll("[data-b26-component]")].map((node) => node.getAttribute("data-b26-component"));
          const rootStyle = root ? getComputedStyle(root) : null;
          const h1Style = h1 ? getComputedStyle(h1) : null;
          const visible = (node) => {
            const rect = node.getBoundingClientRect();
            const style = getComputedStyle(node);
            return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
          };
          const metrics = (selector) => [...document.querySelectorAll(selector)].filter(visible).map((node) => {
            const rect = node.getBoundingClientRect();
            const style = getComputedStyle(node);
            return {
              width: rect.width,
              height: rect.height,
              top: rect.top,
              borderWidth: Number.parseFloat(style.borderTopWidth || "0"),
            };
          });
          const touchTargets = metrics(
            ".ay-v2-menu-toggle, .source-share-action, .info-hint, main .ayds-btn, main .b26-action, footer nav a, footer nav button",
          );
          const iconChrome = metrics(".source-share-action, .platform-icon-only, .info-hint");
          const shareControls = metrics(".source-share-action");
          const iconGlyphs = metrics(".source-share-action svg, .platform-icon-only .platform-logo");
          const spread = (values) => values.length ? Math.max(...values) - Math.min(...values) : 0;
          return {
            visualRoot: root?.getAttribute("data-b26-visual-root") || "",
            background: rootStyle?.backgroundColor || "",
            h1Text: h1?.textContent?.trim() || "",
            h1FontSize: Number.parseFloat(h1Style?.fontSize || "0"),
            h1LineHeight: h1Style?.lineHeight || "",
            viewportWidth: window.innerWidth,
            scrollWidth: document.documentElement.scrollWidth,
            headerHeight: header?.getBoundingClientRect().height || 0,
            footerHeight: footer?.getBoundingClientRect().height || 0,
            productHeader: Boolean(header),
            productFooter: Boolean(footer),
            components,
            missingComponents: required.filter((id) => !components.includes(id)),
            bridgeCount: document.querySelectorAll('[data-b26-component="B26-09"]').length,
            touchTargetCount: touchTargets.length,
            touchTargetMinWidth: touchTargets.length ? Math.min(...touchTargets.map((item) => item.width)) : 0,
            touchTargetMinHeight: touchTargets.length ? Math.min(...touchTargets.map((item) => item.height)) : 0,
            iconChromeCount: iconChrome.length,
            iconChromeMaxBox: iconChrome.length ? Math.max(...iconChrome.flatMap((item) => [item.width, item.height])) : 0,
            iconChromeBorderWidths: [...new Set(iconChrome.map((item) => item.borderWidth))],
            shareControlBoxSpread: spread(shareControls.flatMap((item) => [item.width, item.height])),
            shareControlBaselineSpread: spread(shareControls.map((item) => item.top)),
            iconGlyphBoxSpread: spread(iconGlyphs.flatMap((item) => [item.width, item.height])),
            iconGlyphMinBox: iconGlyphs.length ? Math.min(...iconGlyphs.flatMap((item) => [item.width, item.height])) : 0,
            iconGlyphMaxBox: iconGlyphs.length ? Math.max(...iconGlyphs.flatMap((item) => [item.width, item.height])) : 0,
            forbiddenHeroMatch: forbiddenHero
              ? Boolean(document.querySelector(`.page-hero[data-b26-component="${forbiddenHero}"], .topic-page-hero[data-b26-component="${forbiddenHero}"], .creator-page-hero[data-b26-component="${forbiddenHero}"]`))
              : false,
          };
        }, { required: route.required, forbiddenHero: route.forbiddenHero || "" });
        diagnostics.mobileMenuOpened = null;
        diagnostics.mobileMenuClosed = null;
        if (viewport.width <= 768) {
          const menuButton = page.locator(".ay-v2-menu-toggle");
          const menuPanel = page.locator("#ay-v2-mobile-panel");
          await menuButton.click();
          diagnostics.mobileMenuOpened =
            (await menuButton.getAttribute("aria-expanded")) === "true" && !(await menuPanel.getAttribute("hidden"));
          await page.keyboard.press("Escape");
          diagnostics.mobileMenuClosed =
            (await menuButton.getAttribute("aria-expanded")) === "false" && (await menuPanel.getAttribute("hidden")) !== null;
        }
        const preferencesButton = page.locator("footer [data-cookie-preferences]");
        const preferencesDialog = page.locator("[data-cookie-dialog]");
        await preferencesButton.click();
        diagnostics.cookiePreferencesOpened = (await preferencesDialog.getAttribute("open")) !== null;
        await page.locator("[data-cookie-close]").click();
        const failures = [];
        if (response?.status() !== 200) failures.push(`status=${response?.status() ?? "none"}`);
        if (diagnostics.visualRoot !== "v2") failures.push("missing visual root opt-in");
        if (!diagnostics.productHeader || !diagnostics.productFooter) failures.push("missing compact product shell");
        if (!diagnostics.h1Text) failures.push("missing h1");
        if (diagnostics.h1FontSize > viewport.h1Max + 0.01) failures.push(`h1=${diagnostics.h1FontSize}px > ${viewport.h1Max}px`);
        if (diagnostics.scrollWidth > diagnostics.viewportWidth + 1) failures.push(`overflow=${diagnostics.scrollWidth - diagnostics.viewportWidth}px`);
        if (diagnostics.headerHeight > 84) failures.push(`header=${diagnostics.headerHeight}px`);
        if (diagnostics.footerHeight > viewport.footerMax) failures.push(`footer=${diagnostics.footerHeight}px > ${viewport.footerMax}px`);
        if (diagnostics.missingComponents.length) failures.push(`missing=${diagnostics.missingComponents.join(",")}`);
        if (diagnostics.bridgeCount > 1) failures.push(`bridges=${diagnostics.bridgeCount}`);
        if (diagnostics.forbiddenHeroMatch) failures.push("card component ID assigned to hero");
        if (viewport.width <= 768 && (!diagnostics.mobileMenuOpened || !diagnostics.mobileMenuClosed)) failures.push("mobile menu interaction failed");
        if (viewport.width <= 768 && diagnostics.touchTargetMinWidth < 43.5) failures.push(`touch target width=${diagnostics.touchTargetMinWidth}px`);
        if (viewport.width <= 768 && diagnostics.touchTargetMinHeight < 43.5) failures.push(`touch target height=${diagnostics.touchTargetMinHeight}px`);
        if (viewport.width <= 768 && diagnostics.iconChromeMaxBox > 44.5) failures.push(`oversized icon chrome=${diagnostics.iconChromeMaxBox}px`);
        if (viewport.width <= 768 && diagnostics.iconChromeBorderWidths.some((value) => Math.abs(value - 1) > 0.01)) failures.push(`icon border weights=${diagnostics.iconChromeBorderWidths.join(",")}`);
        if (viewport.width <= 768 && diagnostics.shareControlBoxSpread > 0.5) failures.push(`share box spread=${diagnostics.shareControlBoxSpread}px`);
        if (viewport.width <= 768 && diagnostics.shareControlBaselineSpread > 1) failures.push(`share baseline spread=${diagnostics.shareControlBaselineSpread}px`);
        if (viewport.width <= 768 && diagnostics.iconGlyphBoxSpread > 0.5) failures.push(`icon glyph spread=${diagnostics.iconGlyphBoxSpread}px`);
        if (viewport.width <= 768 && diagnostics.iconGlyphMaxBox && (diagnostics.iconGlyphMinBox < 17.5 || diagnostics.iconGlyphMaxBox > 18.5)) failures.push(`icon glyph box=${diagnostics.iconGlyphMinBox}-${diagnostics.iconGlyphMaxBox}px`);
        if (!diagnostics.cookiePreferencesOpened) failures.push("cookie preferences interaction failed");
        failures.push(...consoleErrors.map((value) => `console:${value}`));
        failures.push(...pageErrors.map((value) => `page:${value}`));
        failures.push(...sameOriginFailures.map((value) => `request:${value}`));
        const screenshot = `${route.id}--${viewport.id}.png`;
        await page.screenshot({ path: join(options.out, screenshot), fullPage: true });
        results.push({
          route: route.route,
          viewport,
          status: response?.status() ?? null,
          diagnostics,
          screenshot,
          failures,
        });
        await page.close();
      }
    }
  } finally {
    await browser.close();
  }
  const report = {
    schema: "base2026.nonsearch-v2-browser-gate/v1",
    base_url_label: "local-representative-candidate",
    routes: ROUTES.map(({ id, route }) => ({ id, route })),
    viewports: VIEWPORTS,
    ok: results.every((row) => row.failures.length === 0),
    results,
  };
  const reportPath = join(options.out, "report.json");
  await writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
  const files = ["report.json", ...results.map((row) => row.screenshot)].sort();
  const hashes = {};
  for (const file of files) hashes[file] = sha256(await readFile(join(options.out, file)));
  await writeFile(
    join(options.out, "SHA256SUMS.json"),
    `${JSON.stringify({ schema: "base2026.nonsearch-v2-browser-evidence-sha256/v1", files: hashes }, null, 2)}\n`,
    "utf8",
  );
  process.stdout.write(`${JSON.stringify({ ok: report.ok, checks: results.length })}\n`);
  if (!report.ok) process.exitCode = 1;
}


main().catch((error) => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exitCode = 1;
});
