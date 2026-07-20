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
  { id: "roadmap", route: "roadmap.html", required: [], footerMax: 1180 },
];

const VIEWPORTS = [
  { id: "desktop-1440", width: 1440, height: 1000, h1Max: 48, footerMax: 500 },
  { id: "mobile-390", width: 390, height: 844, h1Max: 36.1, footerMax: 980 },
  { id: "mobile-320", width: 320, height: 720, h1Max: 36.1, footerMax: 980 },
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
        await page.evaluate(async () => {
          await document.fonts.ready;
          await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        });
        const screenshot = `${route.id}--${viewport.id}--top.png`;
        const fullScreenshot = `${route.id}--${viewport.id}--full.png`;
        // The top-of-page evidence is intentionally captured before menu, dialog,
        // focus, or scroll interaction. Headless Chromium intermittently drops text
        // from the fixed composited layer, so flatten only that layer while capturing;
        // runtime stickiness is tested later against the unmodified page.
        const topPaintStabilizer = await page.addStyleTag({ content: `
          header[data-ay-v2-header] {
            position: absolute !important;
            inset: 0 0 auto !important;
            transform: none !important;
            contain: none !important;
          }
          header[data-ay-v2-header], header[data-ay-v2-header] * {
            transition: none !important;
            animation: none !important;
            will-change: auto !important;
          }
          header[data-ay-v2-header] :is(.ay-v2-brand, .b26-product-header__wordmark, .ay-v2-menu-toggle) {
            max-width: none !important;
            overflow: visible !important;
            visibility: visible !important;
            opacity: 1 !important;
          }
        ` });
        await page.evaluate(async () => {
          await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
          await new Promise((resolve) => setTimeout(resolve, 150));
        });
        await page.screenshot({ path: join(options.out, screenshot), fullPage: false, animations: "disabled" });
        await topPaintStabilizer.evaluate((node) => node.remove());
        await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(resolve)));
        const diagnostics = await page.evaluate(({ required, forbiddenHero }) => {
          const root = document.body;
          const h1 = document.querySelector("main h1");
          const header = document.querySelector("header.b26-product-header");
          const footer = document.querySelector("footer.b26-product-footer");
          const components = [...document.querySelectorAll("[data-b26-component]")].map((node) => node.getAttribute("data-b26-component"));
          const rootStyle = root ? getComputedStyle(root) : null;
          const h1Style = h1 ? getComputedStyle(h1) : null;
          const visible = (node) => {
            const closedDisclosure = node.closest("details:not([open])");
            if (closedDisclosure && !node.closest("summary")) return false;
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
          const heights = (selector) => metrics(selector).map((item) => item.height);
          const median = (values) => {
            if (!values.length) return 0;
            const ordered = [...values].sort((left, right) => left - right);
            const middle = Math.floor(ordered.length / 2);
            return ordered.length % 2 ? ordered[middle] : (ordered[middle - 1] + ordered[middle]) / 2;
          };
          const topicCardHeights = heights('.b26-k-family-topic-index .intelligence-card[data-b26-variant="topic-card"]');
          const creatorCardHeights = heights('.b26-family-creators .card-grid > .intelligence-card');
          const infoGlyphs = [...document.querySelectorAll(".info-hint")].filter(visible).map((node) => {
            const style = getComputedStyle(node, "::before");
            return {
              width: Number.parseFloat(style.width || "0"),
              height: Number.parseFloat(style.height || "0"),
            };
          });
          const infoControls = [...document.querySelectorAll(".info-hint")].filter(visible).map((node) => {
            const style = getComputedStyle(node);
            return {
              background: style.backgroundColor,
              padding: [style.paddingTop, style.paddingRight, style.paddingBottom, style.paddingLeft]
                .map((value) => Number.parseFloat(value || "0")),
              radius: style.borderRadius,
            };
          });
          const sourceHandle = document.querySelector(".b26-creator-copy h1");
          const sourceActions = document.querySelector(".b26-source-actions");
          const sourceText = document.querySelector("#source-text");
          const sourceActionsRect = sourceActions?.getBoundingClientRect();
          const sourceTextRect = sourceText?.getBoundingClientRect();
          const footerStyle = footer ? getComputedStyle(footer) : null;
          const phaseTabs = [...document.querySelectorAll(".roadmap-page .phase-tab")].filter(visible);
          const sequenceSteps = [...document.querySelectorAll(".roadmap-page .sequence-step")].filter(visible);
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
            footerBackground: footerStyle?.backgroundColor || "",
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
            infoGlyphMinBox: infoGlyphs.length ? Math.min(...infoGlyphs.flatMap((item) => [item.width, item.height])) : 0,
            infoGlyphMaxBox: infoGlyphs.length ? Math.max(...infoGlyphs.flatMap((item) => [item.width, item.height])) : 0,
            infoControlBackgrounds: [...new Set(infoControls.map((item) => item.background))],
            infoControlMaxPadding: infoControls.length ? Math.max(...infoControls.flatMap((item) => item.padding)) : 0,
            infoControlRadii: [...new Set(infoControls.map((item) => item.radius))],
            topicCardCount: topicCardHeights.length,
            topicCardMedianHeight: median(topicCardHeights),
            topicCardMaxHeight: topicCardHeights.length ? Math.max(...topicCardHeights) : 0,
            creatorCardCount: creatorCardHeights.length,
            creatorCardMedianHeight: median(creatorCardHeights),
            creatorCardMaxHeight: creatorCardHeights.length ? Math.max(...creatorCardHeights) : 0,
            sourceHandleFontSize: sourceHandle ? Number.parseFloat(getComputedStyle(sourceHandle).fontSize || "0") : 0,
            sourceHandleLines: sourceHandle ? Math.round(sourceHandle.getBoundingClientRect().height / Number.parseFloat(getComputedStyle(sourceHandle).lineHeight || "1")) : 0,
            sourceActionsToTextGap: sourceActionsRect && sourceTextRect ? sourceTextRect.top - sourceActionsRect.bottom : 0,
            forbiddenHeroMatch: forbiddenHero
              ? Boolean(document.querySelector(`.page-hero[data-b26-component="${forbiddenHero}"], .topic-page-hero[data-b26-component="${forbiddenHero}"], .creator-page-hero[data-b26-component="${forbiddenHero}"]`))
              : false,
            documentRail: Boolean(document.querySelector(".roadmap-page .b26-k-document-rail, .roadmap-page .ayds-document-rail")),
            documentContext: Boolean(document.querySelector(".roadmap-page .b26-k-document-context[role='note']")),
            phaseTabCount: phaseTabs.length,
            phaseTabMinWidth: phaseTabs.length ? Math.min(...phaseTabs.map((node) => node.getBoundingClientRect().width)) : 0,
            sequenceStepCount: sequenceSteps.length,
          };
        }, { required: route.required, forbiddenHero: route.forbiddenHero || "" });
        diagnostics.mobileMenuOpened = null;
        diagnostics.mobileMenuClosed = null;
        diagnostics.topScreenshotPhase = "fresh-networkidle-fonts-ready-before-scroll-or-interaction";
        diagnostics.topScreenshotPaintMode = "fixed-layer-flattened; runtime-sticky-tested-separately";
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
        diagnostics.stickyHeader = await page.evaluate(async () => {
          const header = document.querySelector("header.b26-product-header");
          if (!header) return { position: "", top: 0, visible: false };
          document.documentElement.style.scrollBehavior = "auto";
          document.body.style.scrollBehavior = "auto";
          window.scrollTo(0, Math.min(700, Math.max(1, document.documentElement.scrollHeight - window.innerHeight)));
          await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
          const rect = header.getBoundingClientRect();
          const result = {
            position: getComputedStyle(header).position,
            top: rect.top,
            visible: rect.bottom > 0 && rect.top < window.innerHeight,
          };
          window.scrollTo(0, 0);
          await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
          return result;
        });
        const failures = [];
        if (response?.status() !== 200) failures.push(`status=${response?.status() ?? "none"}`);
        if (diagnostics.visualRoot !== "v2") failures.push("missing visual root opt-in");
        if (!diagnostics.productHeader || !diagnostics.productFooter) failures.push("missing compact product shell");
        if (!diagnostics.h1Text) failures.push("missing h1");
        if (diagnostics.h1FontSize > viewport.h1Max + 0.01) failures.push(`h1=${diagnostics.h1FontSize}px > ${viewport.h1Max}px`);
        if (diagnostics.scrollWidth > diagnostics.viewportWidth + 1) failures.push(`overflow=${diagnostics.scrollWidth - diagnostics.viewportWidth}px`);
        if (diagnostics.headerHeight > 84) failures.push(`header=${diagnostics.headerHeight}px`);
        const footerMax = route.footerMax || viewport.footerMax;
        if (diagnostics.footerHeight > footerMax) failures.push(`footer=${diagnostics.footerHeight}px > ${footerMax}px`);
        if (diagnostics.footerBackground !== "rgb(255, 255, 255)") failures.push(`footer background=${diagnostics.footerBackground}`);
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
        if (viewport.width <= 768 && diagnostics.infoGlyphMaxBox && (diagnostics.infoGlyphMinBox < 17.5 || diagnostics.infoGlyphMaxBox > 20.5)) failures.push(`info glyph box=${diagnostics.infoGlyphMinBox}-${diagnostics.infoGlyphMaxBox}px`);
        if (viewport.width <= 768 && diagnostics.infoControlBackgrounds.some((value) => !["rgba(0, 0, 0, 0)", "transparent"].includes(value))) failures.push(`info backgrounds=${diagnostics.infoControlBackgrounds.join(",")}`);
        if (viewport.width <= 768 && diagnostics.infoControlMaxPadding > 0.01) failures.push(`info padding=${diagnostics.infoControlMaxPadding}px`);
        if (viewport.width <= 768 && diagnostics.infoControlRadii.some((value) => !value.includes("50%"))) failures.push(`info radii=${diagnostics.infoControlRadii.join(",")}`);
        if (viewport.width <= 768 && route.id === "topics-hub" && (diagnostics.topicCardMedianHeight < 160 || diagnostics.topicCardMedianHeight > 230 || diagnostics.topicCardMaxHeight > 250)) failures.push(`topic card heights median=${diagnostics.topicCardMedianHeight}px max=${diagnostics.topicCardMaxHeight}px`);
        if (viewport.width <= 768 && route.id === "creator" && (diagnostics.creatorCardMedianHeight < 230 || diagnostics.creatorCardMedianHeight > 320 || diagnostics.creatorCardMaxHeight > 330)) failures.push(`creator card heights median=${diagnostics.creatorCardMedianHeight}px max=${diagnostics.creatorCardMaxHeight}px`);
        if (viewport.width <= 768 && route.id === "source" && (diagnostics.sourceHandleFontSize < 20.5 || diagnostics.sourceHandleFontSize > 24.5 || diagnostics.sourceHandleLines > 1)) failures.push(`source handle font=${diagnostics.sourceHandleFontSize}px lines=${diagnostics.sourceHandleLines}`);
        if (viewport.width <= 768 && route.id === "source" && (diagnostics.sourceActionsToTextGap < 0 || diagnostics.sourceActionsToTextGap > 50)) failures.push(`source actions-to-text gap=${diagnostics.sourceActionsToTextGap}px`);
        if (route.id === "roadmap" && diagnostics.documentRail) failures.push("roadmap document rail present");
        if (route.id === "roadmap" && !diagnostics.documentContext) failures.push("roadmap document context missing");
        if (route.id === "roadmap" && viewport.width > 768 && diagnostics.phaseTabCount !== 6) failures.push(`roadmap phase tabs=${diagnostics.phaseTabCount}`);
        if (route.id === "roadmap" && viewport.width > 768 && diagnostics.phaseTabMinWidth < 120) failures.push(`roadmap phase tab width=${diagnostics.phaseTabMinWidth}px`);
        if (route.id === "roadmap" && diagnostics.sequenceStepCount !== 6) failures.push(`roadmap sequence steps=${diagnostics.sequenceStepCount}`);
        if (!diagnostics.stickyHeader.visible || !["fixed", "sticky"].includes(diagnostics.stickyHeader.position) || Math.abs(diagnostics.stickyHeader.top) > 16) failures.push(`sticky header=${JSON.stringify(diagnostics.stickyHeader)}`);
        if (!diagnostics.cookiePreferencesOpened) failures.push("cookie preferences interaction failed");
        failures.push(...consoleErrors.map((value) => `console:${value}`));
        failures.push(...pageErrors.map((value) => `page:${value}`));
        failures.push(...sameOriginFailures.map((value) => `request:${value}`));
        await page.evaluate(async () => {
          document.querySelectorAll("dialog[open]").forEach((dialog) => dialog.close());
          const menu = document.querySelector("#ay-v2-mobile-panel");
          if (menu) menu.setAttribute("hidden", "");
          const menuButton = document.querySelector(".ay-v2-menu-toggle");
          if (menuButton) menuButton.setAttribute("aria-expanded", "false");
          if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
          document.documentElement.style.scrollBehavior = "auto";
          document.body.style.scrollBehavior = "auto";
          window.scrollTo(0, 0);
          window.dispatchEvent(new Event("scroll"));
          await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
          await new Promise((resolve) => setTimeout(resolve, 50));
        });
        diagnostics.screenshotScrollY = await page.evaluate(() => window.scrollY);
        diagnostics.cleanHeader = await page.evaluate(() => {
          const metric = (selector) => {
            const node = document.querySelector(selector);
            if (!node) return { present: false, visible: false, opacity: 0, text: "" };
            const rect = node.getBoundingClientRect();
            const style = getComputedStyle(node);
            return {
              present: true,
              visible: rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden",
              opacity: Number.parseFloat(style.opacity || "0"),
              text: node.textContent?.trim() || "",
            };
          };
          return {
            brand: metric(".b26-product-header .ay-v2-brand"),
            wordmark: metric(".b26-product-header__wordmark"),
            menu: metric(".b26-product-header .ay-v2-menu-toggle"),
          };
        });
        if (diagnostics.screenshotScrollY > 1) failures.push(`screenshot scrollY=${diagnostics.screenshotScrollY}px`);
        if (!diagnostics.cleanHeader.brand.visible || diagnostics.cleanHeader.brand.opacity < 0.99 || diagnostics.cleanHeader.brand.text !== "Alex Yarosh") failures.push(`clean header brand=${JSON.stringify(diagnostics.cleanHeader.brand)}`);
        if (!diagnostics.cleanHeader.wordmark.visible || diagnostics.cleanHeader.wordmark.opacity < 0.99 || diagnostics.cleanHeader.wordmark.text !== "Base2026") failures.push(`clean header wordmark=${JSON.stringify(diagnostics.cleanHeader.wordmark)}`);
        if (viewport.width <= 768 && (!diagnostics.cleanHeader.menu.visible || diagnostics.cleanHeader.menu.opacity < 0.99 || diagnostics.cleanHeader.menu.text.toLowerCase() !== "menu")) failures.push(`clean header menu=${JSON.stringify(diagnostics.cleanHeader.menu)}`);
        await page.addStyleTag({ content: `
          header[data-ay-v2-header] { position: absolute !important; top: 0 !important; }
          .skip-link { display: none !important; }
          #ay-v2-mobile-panel, dialog { display: none !important; }
        ` });
        await page.screenshot({ path: join(options.out, fullScreenshot), fullPage: true });
        results.push({
          route: route.route,
          viewport,
          status: response?.status() ?? null,
          diagnostics,
          screenshot,
          fullScreenshot,
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
  const files = ["report.json", ...results.flatMap((row) => [row.screenshot, row.fullScreenshot])].sort();
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
