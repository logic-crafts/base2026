const configuredSearchHost = window.BASE2026_MEILI_URL || "http://127.0.0.1:7700";
const searchHost = configuredSearchHost.startsWith("/")
  ? `${window.location.origin}${configuredSearchHost}`
  : configuredSearchHost;
const searchKey = window.BASE2026_MEILI_KEY || "";
const searchIndex = window.BASE2026_MEILI_INDEX || "base2026_public_tiktok";
const scriptAssetVersion = (() => {
  try {
    const scriptSrc = document.currentScript?.getAttribute("src") || "";
    return scriptSrc ? new URL(scriptSrc, window.location.href).searchParams.get("v") || "" : "";
  } catch {
    return "";
  }
})();
const assetVersion = window.BASE2026_ASSET_VERSION || scriptAssetVersion;
const presetButtons = [...document.querySelectorAll("[data-query]")];
const selectedTerms = document.querySelector("#selected-terms");
const sourceDetailPanel = document.querySelector("#source-detail-panel");
const searchSignal = document.querySelector("#search-signal");
const analyticsStrip = document.querySelector("#analytics-strip");
const mobileFilterToggle = document.querySelector("#mobile-filter-toggle");
const mobileFilterClose = document.querySelector("#mobile-filter-close");
const mobileFilterBackdrop = document.querySelector("#mobile-filter-backdrop");
const mobileFilterCount = document.querySelector("#mobile-filter-count");
const documentCache = new Map();
const currentHitCache = new Map();
const relatedPassageCache = new Map();
const insightCache = new Map();
let analyticsState = null;
let selectedSourceId = "";
let applyingRouteState = false;

const { searchClient } = instantMeiliSearch(searchHost, searchKey, {
  primaryKey: "id",
  placeholderSearch: true,
});

function sourceLabel(type) {
  return type === "tiktok_video" ? "TikTok" : type === "local_file" ? "Local file" : type || "Source";
}

function creatorInitial(value) {
  return String(value || "B").replace("@", "").trim().slice(0, 1).toUpperCase() || "B";
}

function creatorAvatar(handle, avatarUrl) {
  const label = `${stripHandle(handle || "creator")} profile`;
  const safeUrl = compactText(avatarUrl);
  if (safeUrl && (/^https?:\/\//i.test(safeUrl) || safeUrl.startsWith("/") || safeUrl.startsWith("./"))) {
    return `<span class="avatar avatar--image"><img src="${escapeHtml(safeUrl)}" alt="${escapeHtml(label)}" loading="lazy" referrerpolicy="no-referrer" onerror="this.closest('.avatar').textContent='${escapeHtml(creatorInitial(handle))}'" /></span>`;
  }
  return `<span class="avatar" aria-hidden="true">${escapeHtml(creatorInitial(handle))}</span>`;
}

function tiktokLogoSvg() {
  return `
    <svg class="platform-logo platform-logo--tiktok" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/>
    </svg>
  `;
}

function platformBadge(type, sourceUrl = "") {
  const label = sourceLabel(type);
  const css = type === "tiktok_video" ? " platform-badge--tiktok" : "";
  const logo = type === "tiktok_video" ? tiktokLogoSvg() : "";
  if (type === "tiktok_video") {
    if (sourceUrl) {
      return `<a class="platform-badge${css} platform-badge--icon-only" href="${escapeHtml(sourceUrl)}" target="_blank" rel="noreferrer" title="Open TikTok source" aria-label="Open TikTok source">${logo}</a>`;
    }
    return `<span class="platform-badge${css} platform-badge--icon-only" title="${escapeHtml(label)} source" aria-label="${escapeHtml(label)} source">${logo}</span>`;
  }
  return `<span class="platform-badge${css}">${logo}${escapeHtml(label)}</span>`;
}

function platformInline(type) {
  if (type === "tiktok_video") {
    return `<span class="platform-inline" title="TikTok source" aria-label="TikTok source">${tiktokLogoSvg()}</span>`;
  }
  return `<span class="platform-inline">${escapeHtml(sourceLabel(type))}</span>`;
}

function platformValue(type, platform) {
  if (type === "tiktok_video" || String(platform || "").toLowerCase() === "tiktok") {
    return platformInline("tiktok_video");
  }
  return escapeHtml(platform || sourceLabel(type));
}

function publicPolicyLabel(value) {
  return compactText(value || "excerpt_only").replace(/_/g, " ");
}

function sourceIdentityMarkup(doc) {
  const handle = doc.handle || doc.author || "Unknown creator";
  const date = doc.published_date || "No date";
  return `
    <div class="source-identity source-identity--modal">
      ${creatorAvatar(handle, doc.avatar_url || doc.creator_avatar_url)}
      <div class="source-identity__body">
        <div class="source-identity__line">
          <a class="source-identity__handle" href="${escapeHtml(doc.creator_url || "#")}" target="_blank" rel="noreferrer">${escapeHtml(handle)}</a>
          <span class="source-identity__date">${escapeHtml(date)}</span>
        </div>
      </div>
    </div>
  `;
}

function infoHint(label, text, align = "") {
  const alignAttr = align ? ` data-tooltip-align="${escapeHtml(align)}"` : "";
  return `<span class="info-hint" tabindex="0" aria-label="${escapeHtml(`${label}: ${text}`)}" data-tooltip="${escapeHtml(text)}"${alignAttr}>i</span>`;
}

function stripHandle(value) {
  return String(value || "").replace(/^@/, "");
}

function compactText(value) {
  return decodeHtmlEntities(value).replace(/\s+/g, " ").trim();
}

function decodeHtmlEntities(value) {
  const text = String(value || "");
  if (!/[&][a-zA-Z#0-9]+;/.test(text)) return text;
  const namedEntities = {
    amp: "&",
    lt: "<",
    gt: ">",
    quot: '"',
    apos: "'",
    nbsp: " ",
  };
  return text.replace(/&(#x[0-9a-fA-F]+|#\d+|[a-zA-Z][a-zA-Z0-9]+);/g, (match, entity) => {
    if (entity[0] === "#") {
      const codePoint = entity[1]?.toLowerCase() === "x" ? Number.parseInt(entity.slice(2), 16) : Number.parseInt(entity.slice(1), 10);
      if (Number.isFinite(codePoint) && codePoint > 0 && codePoint <= 0x10ffff) {
        try {
          return String.fromCodePoint(codePoint);
        } catch (_err) {
          return match;
        }
      }
      return match;
    }
    return Object.prototype.hasOwnProperty.call(namedEntities, entity) ? namedEntities[entity] : match;
  });
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function limitFormattedWords(value, maxWords = 55) {
  const parts = String(value || "").split(/(\s+)/);
  let words = 0;
  let clipped = false;
  const out = [];
  for (const part of parts) {
    if (!part.trim()) {
      out.push(part);
      continue;
    }
    const visible = part.replace(/<[^>]*>/g, "");
    if (visible && !/^\W+$/.test(visible)) words += 1;
    if (words > maxWords) {
      clipped = true;
      break;
    }
    out.push(part);
  }
  return `${out.join("").trim()}${clipped ? "..." : ""}`;
}

function escapeRegExp(value) {
  return String(value || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function getHighlightTerms(query) {
  const stopTokens = new Set(["and", "or", "not"]);
  const terms = [];
  compactText(query)
    .split(",")
    .map((part) => compactText(part))
    .filter(Boolean)
    .forEach((part) => {
      terms.push(part);
      part
        .split(/\s+/)
        .map((token) => compactText(token.replace(/[^\w-]/g, "")))
        .filter((token) => token.length > 2 && !stopTokens.has(token.toLowerCase()))
        .forEach((token) => terms.push(token));
    });
  return [...new Set(terms.map((term) => term.toLowerCase()))]
    .sort((a, b) => b.length - a.length)
    .map((term) => terms.find((item) => item.toLowerCase() === term) || term);
}

function highlightPlainText(value, terms = []) {
  const text = String(value || "");
  const needles = terms.filter(Boolean);
  if (!text || !needles.length) return escapeHtml(text);
  const pattern = needles.map(escapeRegExp).join("|");
  if (!pattern) return escapeHtml(text);
  const regex = new RegExp(`(${pattern})`, "gi");
  let lastIndex = 0;
  let out = "";
  text.replace(regex, (match, _group, offset) => {
    out += escapeHtml(text.slice(lastIndex, offset));
    out += `<mark>${escapeHtml(match)}</mark>`;
    lastIndex = offset + match.length;
    return match;
  });
  out += escapeHtml(text.slice(lastIndex));
  return out;
}

function paragraphizeHtml(value) {
  const text = compactText(limitFormattedWords(value));
  if (!text) return "";
  const sentences = text.split(/(?<=[.!?])\s+(?=(?:<[^>]+>)*["'“‘(]?[A-Z0-9])/);
  return sentences.map((sentence) => `<p>${sentence}</p>`).join("");
}

function splitReadableText(value, options = {}) {
  const maxSentences = options.maxSentences || 3;
  const maxChars = options.maxChars || 520;
  const maxWords = options.maxWords || 74;
  const raw = decodeHtmlEntities(value || "").replace(/\r\n?/g, "\n").trim();
  if (!raw) return [];
  const sourceBlocks = raw
    .split(/\n{2,}/)
    .map((part) => part.replace(/[ \t]+/g, " ").trim())
    .filter(Boolean);
  const blocks = [];
  const pushWordChunks = (text) => {
    const words = compactText(text).split(/\s+/).filter(Boolean);
    for (let index = 0; index < words.length; index += maxWords) {
      const chunk = words.slice(index, index + maxWords).join(" ").trim();
      if (chunk) blocks.push(chunk);
    }
  };
  sourceBlocks.forEach((sourceBlock) => {
    const block = compactText(sourceBlock);
    if (!block) return;
    const sentences = block.match(/[^.!?…]+[.!?…]+(?=\s|$)|[^.!?…]+$/g) || [block];
    if (sentences.length <= 1 && block.length > maxChars) {
      pushWordChunks(block);
      return;
    }
    let current = "";
    let sentenceCount = 0;
    sentences.forEach((sentence) => {
      const clean = compactText(sentence);
      if (!clean) return;
      if (clean.length > maxChars) {
        if (current) blocks.push(current);
        current = "";
        sentenceCount = 0;
        pushWordChunks(clean);
        return;
      }
      const next = compactText(`${current} ${clean}`);
      if (current && (next.length > maxChars || sentenceCount >= maxSentences)) {
        blocks.push(current);
        current = clean;
        sentenceCount = 1;
        return;
      }
      current = next;
      sentenceCount += 1;
    });
    if (current) blocks.push(current);
  });
  return blocks.filter(Boolean);
}

function paragraphizePlainText(value, terms = []) {
  const blocks = splitReadableText(value);
  return blocks.map((part) => `<p>${highlightPlainText(part, terms)}</p>`).join("");
}

function pageSlug(value, fallback = "record") {
  const slug = String(value || "")
    .toLowerCase()
    .match(/[a-z0-9]+/g)
    ?.join("-");
  return (slug || fallback).slice(0, 120);
}

function sourcePageHref(hit) {
  return `./sources/${pageSlug(hit.item_id || hit.source_id)}.html`;
}

function workspaceRouteHref(patch = {}) {
  const params = routeSearchParams();
  const currentQuery = compactText(search?.helper?.state?.query || params.get("q") || "");
  if (currentQuery && !Object.prototype.hasOwnProperty.call(patch, "q")) params.set("q", currentQuery);
  Object.entries(patch).forEach(([key, value]) => {
    if (value === null || value === undefined || value === "") {
      params.delete(key);
    } else {
      params.set(key, String(value));
    }
  });
  const query = params.toString();
  return `./${query ? `#search?${query}` : ""}`;
}

function routeSearchParams() {
  const params = new URLSearchParams(window.location.search);
  const hash = window.location.hash || "";
  if (hash.startsWith("#search?")) {
    const hashParams = new URLSearchParams(hash.slice("#search?".length));
    hashParams.forEach((value, key) => {
      if (!params.has(key)) params.set(key, value);
    });
  }
  return params;
}

function getKnowledgeRouteState() {
  const params = routeSearchParams();
  return {
    q: params.get("q") || params.get(`${searchIndex}[query]`) || "",
    source: params.get("source") || "",
    creator: params.get("creator") || "",
    topic: params.get("topic") || "",
    compare: params.get("compare") || "",
    year: params.get("year") || "",
    source_type: params.get("source_type") || "",
  };
}

function setKnowledgeRouteState(patch = {}, options = {}) {
  const params = routeSearchParams();
  const currentQuery = compactText(search?.helper?.state?.query || "");
  if (currentQuery && !Object.prototype.hasOwnProperty.call(patch, "q")) params.set("q", currentQuery);
  Object.entries(patch).forEach(([key, value]) => {
    if (value === null || value === undefined || value === "") {
      params.delete(key);
    } else {
      params.set(key, String(value));
    }
  });
  const query = params.toString();
  const nextUrl = `${window.location.pathname}${query ? `#search?${query}` : ""}`;
  if (nextUrl === `${window.location.pathname}${window.location.hash}`) return;
  window.history[options.replace ? "replaceState" : "pushState"]({}, "", nextUrl);
}

function hasActiveRefinements() {
  const state = search?.helper?.state;
  if (!state) return false;
  const refinementGroups = [
    state.facetsRefinements,
    state.disjunctiveFacetsRefinements,
    state.hierarchicalFacetsRefinements,
    state.numericRefinements,
    state.tagRefinements,
  ];
  return refinementGroups.some((group) =>
    Object.values(group || {}).some((value) => {
      if (Array.isArray(value)) return value.length > 0;
      if (value && typeof value === "object") return Object.keys(value).length > 0;
      return Boolean(value);
    }),
  );
}

function syncWorkspaceActiveState(route = getKnowledgeRouteState()) {
  const hasRouteState = Boolean(route.source || route.creator || route.topic || route.compare || route.year || route.source_type);
  const hasQuery = Boolean(compactText(search?.helper?.state?.query || route.q || ""));
  document.body.classList.toggle("knowledge-workspace-active", hasRouteState || hasQuery || hasActiveRefinements());
}

function routeTopicLabel(topicId, label = "") {
  return compactText(label || String(topicId || "").replace(/-/g, " "));
}

function staticAssetHref(path) {
  return assetVersion ? `${path}?v=${encodeURIComponent(assetVersion)}` : path;
}

function publicDataHref(fileName) {
  const path = `./static/${fileName}`;
  return assetVersion ? `${path}?v=${encodeURIComponent(assetVersion)}` : path;
}

async function fetchPublicFile(primaryPath, fallbackPath) {
  const primary = await fetch(primaryPath, { cache: "no-cache" });
  if (primary.ok || !fallbackPath) return primary;
  return fetch(fallbackPath, { cache: "no-cache" });
}

function formatCount(value) {
  const number = Number(value || 0);
  return Number.isFinite(number) ? number.toLocaleString("en-US") : String(value || "0");
}

async function updateManifestCounters() {
  const counters = [...document.querySelectorAll("[data-manifest-count]")];
  if (!counters.length) return;
  try {
    const response = await fetchPublicFile(publicDataHref("manifest.json"), "../../public-data/tiktok/manifest.json");
    if (!response.ok) throw new Error(`manifest.json ${response.status}`);
    const manifest = await response.json();
    const values = {
      chunks: manifest.chunks ?? manifest.passages,
      creators: manifest.creators,
      documents: manifest.documents ?? manifest.source_records,
      insight_cards: manifest.insight_cards,
      public_insight_cards: manifest.public_insight_cards,
      topics: manifest.topics,
    };
    counters.forEach((node) => {
      const key = node.getAttribute("data-manifest-count") || "";
      if (Object.prototype.hasOwnProperty.call(values, key) && values[key] !== undefined) {
        node.textContent = formatCount(values[key]);
      }
    });
  } catch {
    document.body.classList.add("manifest-counts-fallback");
  }
}

function normalizeHandle(value) {
  const handle = stripHandle(value || "");
  return handle ? `@${handle}` : "";
}

async function loadAnalyticsData() {
  if (analyticsState) return analyticsState;
  const state = {
    loaded: false,
    totals: {},
    topTopics: [],
    topCreators: [],
    topicsById: new Map(),
    creatorsByHandle: new Map(),
  };
  analyticsState = state;
  try {
    const response = await fetchPublicFile(publicDataHref("analytics_summary.json"), "../../public-data/tiktok/analytics_summary.json");
    if (!response.ok) throw new Error(`analytics_summary.json ${response.status}`);
    const payload = await response.json();
    const strongTopics = new Set((payload.strong_topic_signals || []).map((row) => row.topic_id).filter(Boolean));
    state.loaded = true;
    state.totals = {
      source_records: payload.totals?.source_records ?? payload.totals?.documents,
      passages: payload.totals?.passages,
      public_topics: payload.totals?.public_topics ?? payload.totals?.topics,
      public_insight_cards: payload.totals?.public_insight_cards,
      signal_briefs: payload.totals?.strong_topic_signals ?? payload.totals?.signal_briefs,
    };
    state.topTopics = Array.isArray(payload.topics)
      ? payload.topics.map((row) => ({
          ...row,
          label: row.topic || row.label || row.topic_id,
          has_signal_brief: Boolean(row.has_signal_brief || strongTopics.has(row.topic_id)),
        }))
      : Array.isArray(payload.top_topics)
        ? payload.top_topics
        : [];
    state.topCreators = Array.isArray(payload.creators)
      ? payload.creators
      : Array.isArray(payload.top_creators)
        ? payload.top_creators
        : [];
    state.topTopics.forEach((row) => {
      if (row.topic_id) state.topicsById.set(row.topic_id, row);
    });
    state.topCreators.forEach((row) => {
      const handle = normalizeHandle(row.handle);
      if (handle) state.creatorsByHandle.set(handle, row);
    });
  } catch {
    try {
      const fallback = await fetchPublicFile(publicDataHref("base2026_analytics.json"), "../../public-data/tiktok/base2026_analytics.json");
      if (!fallback.ok) throw new Error(`base2026_analytics.json ${fallback.status}`);
      const payload = await fallback.json();
      state.loaded = true;
      state.totals = payload.totals || {};
      state.topTopics = Array.isArray(payload.top_topics) ? payload.top_topics : [];
      state.topCreators = Array.isArray(payload.top_creators) ? payload.top_creators : [];
      state.topTopics.forEach((row) => {
        if (row.topic_id) state.topicsById.set(row.topic_id, row);
      });
      state.topCreators.forEach((row) => {
        const handle = normalizeHandle(row.handle);
        if (handle) state.creatorsByHandle.set(handle, row);
      });
    } catch {
      state.loaded = false;
    }
  }
  return state;
}

function renderAnalyticsStrip(state) {
  if (!analyticsStrip || !state?.loaded) return;
  const totals = state.totals || {};
  const topTopic = state.topTopics?.[0];
  const topCreator = state.topCreators?.[0];
  analyticsStrip.hidden = false;
  analyticsStrip.innerHTML = `
    <a class="analytics-strip__item analytics-strip__item--link" href="./analytics.html">
      <span>Analytics</span>
      <strong>${formatCount(totals.source_records)} sources</strong>
    </a>
    <span class="analytics-strip__item">
      <span>Passages</span>
      <strong>${formatCount(totals.passages)}</strong>
    </span>
    <span class="analytics-strip__item">
      <span>Topics</span>
      <strong>${formatCount(totals.public_topics)}</strong>
    </span>
    ${topTopic ? `<a class="analytics-strip__item analytics-strip__item--link" href="${topicRouteHref(topTopic.topic_id, topTopic.label)}" data-workspace-route data-route-topic="${escapeHtml(topTopic.topic_id)}" data-route-label="${escapeHtml(topTopic.label)}"><span>Top signal</span><strong>${escapeHtml(topTopic.label)}</strong></a>` : ""}
    ${topCreator ? `<a class="analytics-strip__item analytics-strip__item--link" href="${workspaceRouteHref({ creator: stripHandle(topCreator.handle || "") })}" data-workspace-route data-route-creator="${escapeHtml(stripHandle(topCreator.handle || ""))}"><span>Top creator</span><strong>${escapeHtml(topCreator.handle || "")}</strong></a>` : ""}
  `;
}

function creatorPageHref(hit) {
  return `./creators/${pageSlug(hit.handle || hit.author || hit.creator_handle, "creator")}.html`;
}

function topicPageHref(topicId) {
  return `./topics/${pageSlug(topicId, "uncategorized")}.html`;
}

function creatorRouteHref(hit) {
  return workspaceRouteHref({ source: "", creator: stripHandle(hit.handle || hit.author || hit.creator_handle || "") });
}

function topicRouteHref(topicId, label = "") {
  return workspaceRouteHref({ source: "", topic: topicId, q: routeTopicLabel(topicId, label) });
}

function renderTopicLinks(hit) {
  const topicIds = Array.isArray(hit.topics) ? hit.topics : [];
  const labels = Array.isArray(hit.topic_labels) ? hit.topic_labels : [];
  const pairs = topicIds
    .slice(0, 4)
    .map((topicId, index) => ({
      topicId,
      label: labels[index] || String(topicId || "").replace(/-/g, " "),
    }))
    .filter((row) => row.topicId);
  if (!pairs.length) return "";
  return `
    <div class="result-topic-list" aria-label="Detected topics">
      ${pairs.map((row) => {
        const topic = analyticsState?.topicsById?.get(row.topicId);
        const signalClass = topic?.has_signal_brief ? " topic-tag--signal" : "";
        const count = topic?.source_count ? `<span>${formatCount(topic.source_count)}</span>` : "";
        return `<a class="topic-chip topic-tag${signalClass}" href="${topicRouteHref(row.topicId, row.label)}" data-workspace-route data-route-topic="${escapeHtml(row.topicId)}" data-route-label="${escapeHtml(row.label)}">${escapeHtml(row.label)}${count}</a>`;
      }).join("")}
    </div>
  `;
}

function renderRecordTopics(doc) {
  const topicIds = Array.isArray(doc.topics) ? doc.topics : [];
  const labels = Array.isArray(doc.topic_labels) ? doc.topic_labels : [];
  const pairs = topicIds
    .slice(0, 8)
    .map((topicId, index) => ({
      topicId,
      label: labels[index] || String(topicId || "").replace(/-/g, " "),
    }))
    .filter((row) => row.topicId);
  if (!pairs.length) return "";
  return `
    <div class="record-topics" aria-label="Detected topics">
      ${pairs.map((row) => `<a class="topic-chip topic-tag" href="${topicRouteHref(row.topicId, row.label)}" data-workspace-route data-route-topic="${escapeHtml(row.topicId)}" data-route-label="${escapeHtml(row.label)}">${escapeHtml(row.label)}</a>`).join("")}
    </div>
  `;
}

function renderResultAnalytics(hit) {
  const topicIds = Array.isArray(hit.topics) ? hit.topics : [];
  const primaryTopic = topicIds.map((topicId) => analyticsState?.topicsById?.get(topicId)).find(Boolean);
  const creator = analyticsState?.creatorsByHandle?.get(normalizeHandle(hit.handle || hit.author || hit.creator_handle));
  const items = [];
  if (primaryTopic) {
    items.push(`<span><strong>${formatCount(primaryTopic.source_count)}</strong> sources on ${escapeHtml(primaryTopic.label || "topic")}</span>`);
    if (primaryTopic.creator_count) items.push(`<span><strong>${formatCount(primaryTopic.creator_count)}</strong> creators</span>`);
  }
  if (creator) {
    items.push(`<span><strong>${formatCount(creator.source_count)}</strong> from ${escapeHtml(creator.handle || "creator")}</span>`);
  }
  if (!items.length) return "";
  return `<div class="result-intel" aria-label="Result analytics">${items.slice(0, 3).join("")}</div>`;
}

function sourceKey(row) {
  return row?.source_id || row?.item_id || "";
}

function shortSourceHeadline(value, fallback = "Source record") {
  const text = compactText(value || "");
  if (!text) return fallback;
  const sentence = text.match(/^(.{24,110}?[.!?])\s/)?.[1] || text;
  return sentence.length > 88 ? `${sentence.slice(0, 85).trim()}...` : sentence;
}

function sourceDisplayName(doc) {
  const title = compactText(doc.title || "");
  const truncated = compactText(doc.title_status).toLowerCase() === "truncated";
  if (title && !truncated) return title;
  return shortSourceHeadline(doc.source_summary_short || doc.public_source_text || doc.excerpt || doc.body, "Source record");
}

function sourceDetailLead(doc) {
  const title = compactText(doc.title || "");
  const truncated = compactText(doc.title_status).toLowerCase() === "truncated";
  if (title && !truncated) return title;
  return compactText(doc.source_summary_short || doc.excerpt || doc.body || sourceDisplayName(doc));
}

function stripEvidenceMarkup(value) {
  return compactText(String(value || "").replace(/<\/?mark>/g, " ").replace(/<[^>]+>/g, " "));
}

function evidenceFingerprint(value) {
  return stripEvidenceMarkup(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function sameEvidence(a, b) {
  const first = evidenceFingerprint(a);
  const second = evidenceFingerprint(b);
  if (!first || !second) return false;
  const short = first.length <= second.length ? first : second;
  const long = first.length > second.length ? first : second;
  if (short.length < 120) return first === second;
  return long.startsWith(short.slice(0, 240)) || short.startsWith(long.slice(0, 240));
}

function evidenceStartsWith(value, prefix) {
  const text = evidenceFingerprint(value);
  const lead = evidenceFingerprint(prefix);
  if (!text || !lead || lead.length < 40) return false;
  return text.startsWith(lead) || lead.startsWith(text);
}

function evidenceContainsFragment(fragmentValue, fullValue) {
  const fragment = evidenceFingerprint(fragmentValue);
  const full = evidenceFingerprint(fullValue);
  if (!fragment || !full) return false;
  if (fragment.length < 80) return fragment === full;
  return full.includes(fragment) || fragment.includes(full);
}

const INSIGHT_STOPWORDS = new Set([
  "about", "above", "after", "again", "against", "also", "because", "been",
  "being", "between", "could", "does", "doing", "from", "have", "having",
  "into", "more", "most", "need", "only", "other", "same", "should",
  "source", "that", "their", "them", "then", "there", "these", "they",
  "this", "those", "through", "when", "where", "which", "while", "with",
  "would", "your",
]);

const INSIGHT_ANCHOR_TOKENS = new Set([
  "access", "authority", "brand", "citation", "content", "creator",
  "ecommerce", "evidence", "freshness", "google", "government", "keyword",
  "link", "mention", "model", "page", "query", "recommendation", "retrieval",
  "risk", "search", "security", "seo", "signal", "source", "topic",
  "traffic", "visibility",
]);

function insightTokenSet(...values) {
  const text = evidenceFingerprint(values.join(" "));
  const tokens = new Set();
  text.split(/\s+/).forEach((rawToken) => {
    let token = rawToken;
    if (!token || INSIGHT_STOPWORDS.has(token)) return;
    if (token.length < 3 && token !== "ai") return;
    for (const suffix of ["ing", "ed", "es", "s"]) {
      if (token.length > suffix.length + 4 && token.endsWith(suffix)) {
        token = token.slice(0, -suffix.length);
        break;
      }
    }
    if (token && !INSIGHT_STOPWORDS.has(token)) tokens.add(token);
  });
  return tokens;
}

function insightSignature(row) {
  return insightTokenSet(
    row?.topic || "",
    row?.topic_id || "",
    row?.claim_text || "",
    row?.suggested_action || "",
    row?.evidence_excerpt || "",
  );
}

function insightRowsRelated(first, second) {
  const firstTopic = first?.topic_id || pageSlug(first?.topic || "", "");
  const secondTopic = second?.topic_id || pageSlug(second?.topic || "", "");
  if (firstTopic && firstTopic === secondTopic) return true;
  const firstTokens = insightSignature(first);
  const secondTokens = insightSignature(second);
  if (!firstTokens.size || !secondTokens.size) return false;
  const shared = [...firstTokens].filter((token) => secondTokens.has(token));
  const overlap = shared.length / Math.max(1, Math.min(firstTokens.size, secondTokens.size));
  if (shared.length >= 5 && overlap >= 0.18) return true;
  const sharedAnchors = shared.filter((token) => INSIGHT_ANCHOR_TOKENS.has(token));
  if (sharedAnchors.length >= 3 && shared.length >= 4) return true;
  const firstTopicTokens = insightTokenSet(first?.topic || firstTopic);
  const secondTopicTokens = insightTokenSet(second?.topic || secondTopic);
  const hasTopicOverlap = [...firstTopicTokens].some((token) => secondTopicTokens.has(token));
  return hasTopicOverlap && shared.length >= 4;
}

function groupInsightRows(rows = []) {
  const groups = [];
  rows.filter(Boolean).forEach((row) => {
    const group = groups.find((existingGroup) => existingGroup.some((existing) => insightRowsRelated(row, existing)));
    if (group) {
      group.push(row);
    } else {
      groups.push([row]);
    }
  });
  return groups;
}

function sentenceExcerpt(value, limit = 420, maxSentences = 3) {
  const text = stripEvidenceMarkup(value);
  if (!text) return "";
  const sentences = text.match(/[^.!?]+[.!?]+(?:\s|$)|[^.!?]+$/g) || [text];
  const picked = [];
  let length = 0;
  for (const sentence of sentences) {
    const clean = compactText(sentence);
    if (!clean) continue;
    if (picked.length >= maxSentences) break;
    if (length && length + clean.length > limit) break;
    picked.push(clean);
    length += clean.length + 1;
  }
  const excerpt = compactText(picked.join(" ")) || text;
  if (excerpt.length <= limit) return excerpt;
  const clipped = excerpt.slice(0, Math.max(0, limit - 3)).replace(/\s+\S*$/, "").trim();
  return `${clipped || excerpt.slice(0, limit - 3).trim()}...`;
}

function isClippedEvidence(value) {
  return /(?:\.{3}|\u2026)\s*$/.test(compactText(value));
}

function isFragmentaryEvidence(value) {
  const text = stripEvidenceMarkup(value);
  if (!text) return false;
  if (isClippedEvidence(text)) return true;
  const firstWord = text.replace(/^[^A-Za-z0-9]+/, "").split(/\s+/, 1)[0] || "";
  if (firstWord && /^[a-z]/.test(firstWord)) return true;
  return /^(and|or|but|so|then|because|when|while|that|this|it|they|you|we)\b/i.test(text);
}

function expandedInsightEvidence(row, relatedPassages = [], doc = null) {
  const evidence = stripEvidenceMarkup(row.evidence_excerpt || "");
  if (!evidence) return "";
  if (!isClippedEvidence(evidence)) return evidence;
  const fullMatch = relatedPassages.find((passage) => {
    const body = passage.body || passage.excerpt || "";
    return body && sameEvidence(evidence, body);
  });
  if (fullMatch) return stripEvidenceMarkup(fullMatch.body || fullMatch.excerpt || "");
  const sourceText = doc ? sourcePublicText(doc) : "";
  if (sourceText && sameEvidence(evidence, sourceText)) return stripEvidenceMarkup(sourceText);
  return evidence.replace(/(?:\.{3}|\u2026)\s*$/, ".").trim();
}

function sourceEvidenceText(doc, insights = [], relatedPassages = []) {
  const insight = insights.find((row) => row.evidence_excerpt);
  if (insight) return expandedInsightEvidence(insight, relatedPassages, doc);
  return doc.excerpt || doc.body || "";
}

function sourcePublicText(doc) {
  return doc.public_source_text || doc.excerpt || doc.body || "";
}

function sourceIntelligenceLead(doc, insights = [], loading = false) {
  if (insights.length) {
    return `Reviewed source-backed insight: ${compactText(insights[0].claim_text || insights[0].topic || "public claim")}`;
  }
  if (loading) return "Loading reviewed insights and public evidence for this source record.";
  return sourceDetailLead(doc) || "Attributed source record from the searchable Base2026 video knowledge base.";
}

function sourceIntelligenceHeading(doc, insights = []) {
  if (insights.length) return sentenceExcerpt(insights[0].claim_text || insights[0].topic || "Source-backed insight", 120, 1);
  if (doc.source_summary_short) return sentenceExcerpt(doc.source_summary_short, 140, 1);
  const handle = doc.handle || doc.author || doc.creator_handle || "creator";
  return `Source record from ${stripHandle(handle) ? `@${stripHandle(handle)}` : "creator"}`;
}

function detailSectionTitle(label, tooltip) {
  return `<div class="source-detail-section-title"><h3>${escapeHtml(label)}</h3>${infoHint(label, tooltip, "right")}</div>`;
}

const shareIconPaths = {
  share: "M18 15.6a3.3 3.3 0 0 0-2.6 1.3l-6.1-3.5c.1-.4.1-.8 0-1.2l6-3.4A3.4 3.4 0 1 0 14.4 7l-6 3.4a3.4 3.4 0 1 0 0 4.8l6.1 3.5a3.4 3.4 0 1 0 3.5-3.1z",
  link: "M9.2 14.8a1 1 0 0 1 0-1.4l4.2-4.2a1 1 0 0 1 1.4 1.4l-4.2 4.2a1 1 0 0 1-1.4 0z M8.4 18.4a4.2 4.2 0 0 1-3-7.2l2.1-2.1a1 1 0 0 1 1.4 1.4l-2.1 2.1a2.2 2.2 0 1 0 3.1 3.1l2.1-2.1a1 1 0 0 1 1.4 1.4l-2.1 2.1a4.2 4.2 0 0 1-2.9 1.3z M15.8 13.2a1 1 0 0 1-.7-1.7l2.1-2.1a2.2 2.2 0 0 0-3.1-3.1L12 8.4A1 1 0 0 1 10.6 7l2.1-2.1a4.2 4.2 0 0 1 5.9 5.9l-2.1 2.1a1 1 0 0 1-.7.3z",
  copy: "M8 7a3 3 0 0 1 3-3h6a3 3 0 0 1 3 3v6a3 3 0 0 1-3 3h-6a3 3 0 0 1-3-3V7zm3-1a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V7a1 1 0 0 0-1-1h-6z M4 11a3 3 0 0 1 3-3 1 1 0 1 1 0 2 1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1 1 1 0 1 1 2 0 3 3 0 0 1-3 3H7a3 3 0 0 1-3-3v-6z",
  print: "M7 3h10a2 2 0 0 1 2 2v3h1a3 3 0 0 1 3 3v5a2 2 0 0 1-2 2h-2v1a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-1H3a2 2 0 0 1-2-2v-5a3 3 0 0 1 3-3h1V5a2 2 0 0 1 2-2zm0 5h10V5H7v3zm0 8v3h10v-3H7zm12 0h2v-5a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1v5h2v-1a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v1z",
};

function shareIcon(pathKey) {
  return `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="${shareIconPaths[pathKey]}"/></svg>`;
}

function shareButton(action, label, iconKey) {
  return `<button type="button" class="source-share-action" data-share-action="${escapeHtml(action)}" aria-label="${escapeHtml(label)}" title="${escapeHtml(label)}">${shareIcon(iconKey)}</button>`;
}

function sourceShareActionBar(title, description) {
  return `
    <div class="source-share-actions source-detail-share-actions" data-share-root data-share-title="${escapeHtml(title)}" data-share-description="${escapeHtml(description)}" aria-label="Share source record">
      <span class="source-share-actions__label">Share</span>
      ${shareButton("share", "Share source record", "share")}
      ${shareButton("copy-link", "Copy source record link", "link")}
      ${shareButton("copy-citation", "Copy citation", "copy")}
      ${shareButton("print", "Save as PDF", "print")}
      <span class="share-actions__status source-share-actions__status" data-share-status aria-live="polite"></span>
    </div>
  `;
}

function sourceIntelligenceEmptyState(loading = false) {
  const text = loading
    ? "Loading reviewed Source Intelligence for this source."
    : "No reviewed Source Intelligence cards are published for this source yet. Base2026 only shows reviewed source-backed cards here; unreviewed candidates stay out of the public UI until evidence review.";
  return `<p class="empty-state source-intelligence-empty">${escapeHtml(text)}</p>`;
}

function shouldShowSummaryLong(summaryLong, summaryShort, publicText) {
  if (!summaryLong || summaryLong === summaryShort) return false;
  if (sameEvidence(summaryLong, publicText)) return false;
  if (summaryShort && (sameEvidence(summaryLong, summaryShort) || evidenceStartsWith(summaryLong, summaryShort))) return false;
  return true;
}

function shouldShowDetailCopy(value, title, publicText, previous = "") {
  const text = compactText(value);
  if (!text) return false;
  if (sameEvidence(text, title) || sameEvidence(text, previous)) return false;
  if (evidenceStartsWith(text, title) || evidenceStartsWith(text, previous)) return false;
  if (sameEvidence(text, publicText) || evidenceContainsFragment(text, publicText)) return false;
  return true;
}

function renderPassageCard(row, activeTerms = []) {
  const handle = row.handle || row.creator_handle || "Creator";
  const date = row.published_date || row.published_at || "No date";
  return `
    <article class="source-detail-passage">
      <div class="passage-card__meta">
        <span>${escapeHtml(handle)}</span>
        <span>${escapeHtml(date)}</span>
      </div>
      <div class="passage-card__body">${paragraphizePlainText(row.body || row.excerpt || "", activeTerms)}</div>
    </article>
  `;
}

function renderInsightCard(rowOrRows, relatedPassages = [], activeTerms = [], doc = null) {
  const rows = Array.isArray(rowOrRows) ? rowOrRows.filter(Boolean) : [rowOrRows].filter(Boolean);
  if (!rows.length) return "";
  const primary = rows[0];
  const sourceText = doc ? sourcePublicText(doc) : "";
  const topicLinks = [];
  const topicLabels = [];
  const seenTopics = new Set();
  rows.forEach((row) => {
    const topicId = row.topic_id || pageSlug(row.topic || "uncategorized", "uncategorized");
    if (!topicId || seenTopics.has(topicId)) return;
    seenTopics.add(topicId);
    const topicLabel = row.topic || row.topic_id || "Topic";
    topicLabels.push(topicLabel);
    topicLinks.push(`<a class="topic-chip topic-tag" href="${topicRouteHref(topicId, topicLabel)}" data-workspace-route data-route-topic="${escapeHtml(topicId)}" data-route-label="${escapeHtml(topicLabel)}">${escapeHtml(topicLabel)}</a>`);
  });

  const actions = [];
  const seenActions = [];
  const evidenceBlocks = [];
  const seenEvidence = [];
  let evidenceDuplicateCount = 0;
  rows.forEach((row) => {
    const claim = row.claim_text || row.topic || "Public insight";
    const action = compactText(row.suggested_action || "");
    if (action && !sameEvidence(action, claim) && !seenActions.some((existing) => sameEvidence(action, existing))) {
      seenActions.push(action);
      actions.push(`<li>${escapeHtml(action)}</li>`);
    }

    const evidence = stripEvidenceMarkup(row.evidence_excerpt || "");
    const expandedEvidence = expandedInsightEvidence(row, relatedPassages, doc);
    const evidenceBody = evidence || expandedEvidence;
    if (!evidenceBody) return;
    const evidenceIsSourceFragment = (
      evidenceContainsFragment(evidenceBody, sourceText) ||
      evidenceContainsFragment(evidenceBody, claim)
    );
    const evidenceIsDuplicate = sameEvidence(evidenceBody, sourceText) || sameEvidence(evidenceBody, claim) || evidenceIsSourceFragment;
    if (evidenceIsDuplicate || isFragmentaryEvidence(evidenceBody)) {
      evidenceDuplicateCount += 1;
      return;
    }
    if (seenEvidence.some((existing) => sameEvidence(evidenceBody, existing))) return;
    seenEvidence.push(evidenceBody);
    const evidencePreview = sentenceExcerpt(evidenceBody, 300, 2);
    evidenceBlocks.push(`<li>${paragraphizePlainText(evidencePreview || evidenceBody, activeTerms)}</li>`);
  });

  const meta = rows.length > 1
    ? `${rows.length} related signals · ${topicLabels.slice(0, 3).join(" / ")}`
    : `${topicLabels[0] || "Topic"} · ${primary.stance || "asserts"}`;
  const actionHtml = actions.length ? `<ul class="source-detail-insight__actions">${actions.join("")}</ul>` : "";
  const evidenceDetails = evidenceBlocks.length
    ? `
      <details class="source-detail-evidence">
        <summary>Show source evidence</summary>
        <div><ul class="source-detail-evidence-list">${evidenceBlocks.join("")}</ul></div>
      </details>
    `
    : "";
  const topicHtml = topicLinks.length
    ? `<div class="source-detail-topic-links" aria-label="Related topics">${topicLinks.join("")}</div>`
    : "";
  return `
    <article class="source-detail-insight">
      <h4>${escapeHtml(primary.claim_text || primary.topic || "Public insight")}</h4>
      <p class="meta">${escapeHtml(meta)}</p>
      ${actionHtml}
      ${evidenceDetails}
      ${topicHtml}
    </article>
  `;
}

async function streamJsonl(fileName, onRow) {
  const fallback = `../../public-data/tiktok/${fileName}`;
  const response = await fetchPublicFile(publicDataHref(fileName), fallback);
  if (!response.ok) throw new Error(`${fileName} ${response.status}`);

  async function inspectLine(line) {
    if (!line.trim()) return false;
    return Boolean(await onRow(JSON.parse(line)));
  }

  if (!response.body?.getReader) {
    const text = await response.text();
    for (const line of text.split(/\r?\n/)) {
      if (await inspectLine(line)) return;
    }
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const lines = buffer.split(/\r?\n/);
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (await inspectLine(line)) {
        reader.cancel().catch(() => {});
        return;
      }
    }
    if (done) break;
  }
  await inspectLine(buffer);
}

async function loadRelatedPassages(doc) {
  const key = sourceKey(doc);
  if (!key) return [];
  if (relatedPassageCache.has(key)) return relatedPassageCache.get(key);
  const rows = [];
  await streamJsonl("passages.jsonl", (row) => {
    if (row.source_id === doc.source_id || row.item_id === doc.item_id) rows.push(row);
    return false;
  });
  relatedPassageCache.set(key, rows);
  return rows;
}

async function loadPublicInsights(doc) {
  const key = sourceKey(doc);
  if (!key) return [];
  if (insightCache.has(key)) return insightCache.get(key);
  const rows = [];
  await streamJsonl("insight_cards.jsonl", (row) => {
    if ((row.source_id === doc.source_id || row.item_id === doc.item_id) && row.public) rows.push(row);
    return false;
  });
  insightCache.set(key, rows);
  return rows;
}

function renderSourceDetailShell(doc, matchedHit, relatedPassages = [], insights = [], loading = false) {
  const activeTerms = getHighlightTerms(search.helper?.state?.query || "");
  const publicText = sourcePublicText(doc);
  const evidenceText = sourceEvidenceText(doc, insights, relatedPassages);
  const summaryShort = compactText(doc.source_summary_short || sourceDetailLead(doc));
  const summaryLong = compactText(doc.source_summary_long || sourceIntelligenceLead(doc, insights, loading));
  const detailTitle = sourceIntelligenceHeading(doc, insights);
  const displayLead = shouldShowDetailCopy(summaryShort, detailTitle, publicText) ? summaryShort : "";
  const displaySummary = shouldShowSummaryLong(summaryLong, summaryShort, publicText) && shouldShowDetailCopy(summaryLong, detailTitle, publicText, displayLead)
    ? summaryLong
    : "";
  const handle = doc.handle || doc.author || doc.creator_handle || "";
  const matchedBody = matchedHit?._formatted?.body || matchedHit?._highlightResult?.body?.value || matchedHit?.body || "";
  const showMatchedPassage = Boolean(
    matchedBody &&
    !sameEvidence(matchedBody, publicText) &&
    !evidenceContainsFragment(matchedBody, publicText),
  );
  const matchedPassage = showMatchedPassage
    ? `<div class="source-detail-stack">${renderPassageCard({ ...doc, body: sentenceExcerpt(matchedBody, 420, 3) }, activeTerms)}</div>`
    : "";
  const relatedDistinct = relatedPassages.filter((row) => {
    const body = row.body || row.excerpt || "";
    return (
      body &&
      !sameEvidence(body, publicText) &&
      !sameEvidence(body, matchedBody) &&
      !evidenceContainsFragment(body, publicText) &&
      !evidenceContainsFragment(body, matchedBody)
    );
  });
  const relatedHtml = relatedDistinct.slice(0, 4).map((row) => renderPassageCard({ ...row, body: sentenceExcerpt(row.body || row.excerpt || "", 420, 3) }, activeTerms)).join("");
  const insightHtml = insights.length ? groupInsightRows(insights.slice(0, 6)).map((group) => renderInsightCard(group, relatedPassages, activeTerms, doc)).join("") : "";
  const matchedSection = showMatchedPassage
    ? `
      <section class="source-detail-section">
        ${detailSectionTitle("Search Match", "A distinct passage that matched the current query. Hidden when it duplicates the main evidence excerpt.")}
        ${matchedPassage}
      </section>
    `
    : "";
  const relatedSection = relatedDistinct.length
    ? `
      <section class="source-detail-section">
        ${detailSectionTitle("Supporting Passages", "Distinct public passages that add context beyond the Source Text.")}
        <div class="source-detail-stack">${relatedHtml}</div>
      </section>
    `
    : "";
  const insightBody = insights.length
    ? `<div class="source-detail-card-grid">${insightHtml}</div>`
    : sourceIntelligenceEmptyState(loading);
  const insightSection = `
      <section class="source-detail-section">
        <div class="source-detail-section-heading">
          ${detailSectionTitle("Source Intelligence", "Reviewed source-backed claims promoted from this evidence.")}
          ${insights.length ? sourceShareActionBar(`Source Intelligence: ${detailTitle}`, sourceIntelligenceLead(doc, insights, loading)) : ""}
        </div>
        ${insightBody}
      </section>
    `;
  return `
    <div class="source-detail-head">
      <div class="source-detail-nav-row">
        <button type="button" class="button-link source-detail-back" data-source-detail-back>Back to results</button>
        <p class="source-kicker">Public source</p>
      </div>
      <div class="source-detail-toolbar">
        ${sourceIdentityMarkup(doc)}
        <div class="source-detail-toolbar__tools">
          ${sourceShareActionBar(detailTitle, displayLead || summaryShort || detailTitle)}
          <div class="source-hero-meta source-detail-meta" aria-label="Source metadata">
            <span class="source-meta-chip source-meta-chip--platform">${platformValue(doc.source_type, doc.platform)}${infoHint("Platform", "Original platform where this public source was collected.", "left")}</span>
            <span class="source-meta-chip"><span>${escapeHtml(publicPolicyLabel(doc.public_policy))}</span>${infoHint("Public policy", "Base2026 publishes attributed excerpts, source links, passages, and reviewed annotations by default.", "left")}</span>
            <span class="source-meta-chip"><span>${escapeHtml(doc.language || "en")}</span>${infoHint("Language", "Detected or stored language for the public source text.", "left")}</span>
            ${insights.length ? `<span class="source-meta-chip"><span>${escapeHtml(String(insights.length))} insights</span>${infoHint("Insights", "Reviewed insight cards linked to this source.", "left")}</span>` : ""}
          </div>
        </div>
      </div>
      <h1>${escapeHtml(detailTitle)}</h1>
      ${displayLead ? `<p class="source-detail-lead">${escapeHtml(displayLead)}</p>` : ""}
      ${displaySummary ? `<p class="source-detail-summary">${escapeHtml(displaySummary)}</p>` : ""}
      <div class="source-detail-actions">
        <a class="button-link button-link--accent" href="${escapeHtml(doc.source_url || "#")}" target="_blank" rel="noreferrer">Open original</a>
        <a class="button-link" href="${creatorRouteHref(doc)}" data-workspace-route data-route-creator="${escapeHtml(stripHandle(handle))}">Creator</a>
      </div>
      ${renderRecordTopics(doc)}
    </div>
    <div class="source-detail-body">
      <section class="source-detail-section">
        ${detailSectionTitle("Source Text", "Reviewed polished transcript/source text normalized for reading and search. Raw captions and private QA stay local.")}
        <div class="source-excerpt-text source-full-text">${paragraphizePlainText(publicText || evidenceText || "No public source text is available for this source yet.", activeTerms)}</div>
      </section>
      ${insightSection}
      ${matchedSection}
      ${relatedSection}
    </div>
  `;
}

async function showSourceDetail(itemId, options = {}) {
  if (!sourceDetailPanel || !itemId) return;
  const { pushRoute = true, matchedHit = null, scroll = true } = options;
  selectedSourceId = itemId;
  const activeHit = matchedHit || currentHitCache.get(itemId) || {};
  sourceDetailPanel.classList.add("is-active");
  document.body.classList.add("source-detail-open");
  if (pushRoute && !applyingRouteState) setKnowledgeRouteState({ source: itemId });
  syncWorkspaceActiveState(getKnowledgeRouteState());
  sourceDetailPanel.innerHTML = `
    <div class="source-detail-empty">
      <p class="eyebrow">Source detail</p>
      <h2>Loading source...</h2>
      <p>Fetching the public source record and related evidence.</p>
    </div>
  `;
  if (scroll) sourceDetailPanel.scrollIntoView({ block: "start", behavior: "smooth" });
  try {
    const doc = (await loadDocumentById(itemId)) || activeHit;
    if (!doc?.item_id) throw new Error("Source record not found.");
    sourceDetailPanel.innerHTML = renderSourceDetailShell(doc, activeHit, [], [], true);
    const [relatedPassages, insights] = await Promise.all([
      loadRelatedPassages(doc).catch(() => []),
      loadPublicInsights(doc).catch(() => []),
    ]);
    if (selectedSourceId === itemId) {
      sourceDetailPanel.innerHTML = renderSourceDetailShell(doc, activeHit, relatedPassages, insights, false);
    }
  } catch (error) {
    sourceDetailPanel.innerHTML = `
      <div class="source-detail-empty">
        <button type="button" class="button-link source-detail-back" data-source-detail-back>Back to results</button>
        <p class="eyebrow">Source detail</p>
        <h2>Source not found in this public export</h2>
        <p>${escapeHtml(error.message || "The source may have been removed, unpublished, or not included in this release.")}</p>
      </div>
    `;
  }
}

function closeSourceDetail(options = {}) {
  const { pushRoute = true } = options;
  selectedSourceId = "";
  document.body.classList.remove("source-detail-open");
  sourceDetailPanel?.classList.remove("is-active");
  if (pushRoute && !applyingRouteState) setKnowledgeRouteState({ source: "" });
  syncWorkspaceActiveState(getKnowledgeRouteState());
}

function setMobileFiltersOpen(open) {
  document.documentElement.classList.toggle("filters-open", open);
  document.body.classList.toggle("filters-open", open);
  if (mobileFilterToggle) mobileFilterToggle.setAttribute("aria-expanded", open ? "true" : "false");
  if (mobileFilterBackdrop) mobileFilterBackdrop.hidden = !open;
}

function updateMobileFilterCount() {
  if (!mobileFilterCount) return;
  const count = document.querySelectorAll(".ais-CurrentRefinements-category").length;
  mobileFilterCount.textContent = count ? `${count} active` : "Choose filters";
}

function splitQueryTerms(query) {
  return compactText(query)
    .split(",")
    .map((term) => compactText(term))
    .filter(Boolean);
}

function mergeQueryTerm(query, term) {
  const target = compactText(term);
  const terms = splitQueryTerms(query);
  const exists = terms.some((item) => item.toLowerCase() === target.toLowerCase());
  const next = exists
    ? terms.filter((item) => item.toLowerCase() !== target.toLowerCase())
    : [...terms, target];
  return next.join(", ");
}

function syncPresetButtons(query) {
  const lowerQuery = compactText(query).toLowerCase();
  presetButtons.forEach((button) => {
    const term = compactText(button.getAttribute("data-query")).toLowerCase();
    const active = term && lowerQuery.includes(term);
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  });
}

function renderSelectedTerms(query) {
  if (!selectedTerms) return;
  const terms = splitQueryTerms(query);
  if (!terms.length) {
    selectedTerms.innerHTML = "";
    return;
  }
  selectedTerms.innerHTML = terms
    .map((term) => `<button type="button" class="selected-term" data-remove-term="${escapeHtml(term)}" aria-label="Remove ${escapeHtml(term)}">${escapeHtml(term)}<span>×</span></button>`)
    .join("");
}

function hitTemplate(hit) {
  if (hit.item_id) currentHitCache.set(hit.item_id, hit);
  const body = hit._formatted?.body || hit._highlightResult?.body?.value || hit.body || "";
  const activeTerms = getHighlightTerms(search.helper?.state?.query || "");
  const bodySnippet = sentenceExcerpt(body, 420, 3);
  const handle = hit._formatted?.handle || hit._highlightResult?.handle?.value || hit.handle || hit.author || "Base2026";
  const date = hit.published_date || "No date";
  const creatorProfileHref = creatorPageHref(hit);
  return `
    <article class="result">
      <div class="result-top">
        ${creatorAvatar(hit.handle || hit.author, hit.avatar_url || hit.creator_avatar_url)}
        <div>
          <div class="creator-line">
            <a class="creator-name" href="${creatorProfileHref}">${handle}</a>
            <span class="meta">${date}</span>
            ${platformBadge(hit.source_type, hit.source_url || hit.url || "")}
          </div>
          ${renderTopicLinks(hit)}
        </div>
      </div>
      <div class="snippet">${paragraphizePlainText(bodySnippet, activeTerms)}</div>
      ${renderResultAnalytics(hit)}
      <div class="result-actions">
        <button type="button" class="button-link button-link--accent view-source-detail" data-item-id="${escapeHtml(hit.item_id || "")}">Open source</button>
      </div>
    </article>
  `;
}

function renderSearchSignal(renderOptions) {
  if (!searchSignal) return;
  const hits = renderOptions.results?.hits || [];
  const sourceIds = new Set();
  const creators = new Set();
  hits.forEach((hit) => {
    const sourceId = hit.item_id || hit.source_id || hit.id || "";
    const creator = hit.handle || hit.creator_handle || hit.author || "";
    if (sourceId) sourceIds.add(sourceId);
    if (creator) creators.add(creator);
  });
  if (sourceIds.size < 5 || creators.size < 2) {
    searchSignal.innerHTML = "";
    searchSignal.hidden = true;
    return;
  }
  const route = getKnowledgeRouteState();
  const query = compactText(search.helper?.state?.query || route.q || "");
  if (!query && !route.topic && !route.creator) {
    searchSignal.innerHTML = "";
    searchSignal.hidden = true;
    return;
  }
  const actionHref = route.topic ? `./compare/${pageSlug(route.topic, "uncategorized")}.html` : "./topics/";
  const actionLabel = route.topic ? "Compare creators for this topic" : "Explore topic signals";
  const signalSubject = query ? "this query appears" : "visible results appear";
  searchSignal.hidden = false;
  searchSignal.innerHTML = `
    <div class="search-signal__row">
      <span>Current search signal: ${signalSubject} across <strong>${formatCount(creators.size)}</strong> creators and <strong>${formatCount(sourceIds.size)}</strong> source records.</span>
      <a class="button-link" href="${escapeHtml(actionHref)}">${escapeHtml(actionLabel)}</a>
    </div>
  `;
}

async function loadDocumentById(itemId) {
  if (documentCache.has(itemId)) return documentCache.get(itemId);
  const response = await fetchPublicFile(staticAssetHref("./static/documents.jsonl"), "../../public-data/tiktok/documents.jsonl");
  if (!response.ok) throw new Error(`documents.jsonl ${response.status}`);

  async function inspectLine(line) {
    if (!line.trim()) return null;
    const doc = JSON.parse(line);
    if (doc.item_id) documentCache.set(doc.item_id, doc);
    return doc.item_id === itemId ? doc : null;
  }

  if (!response.body?.getReader) {
    const text = await response.text();
    for (const line of text.split(/\r?\n/)) {
      const found = await inspectLine(line);
      if (found) return found;
    }
    return null;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const lines = buffer.split(/\r?\n/);
    buffer = lines.pop() || "";
    for (const line of lines) {
      const found = await inspectLine(line);
      if (found) {
        reader.cancel().catch(() => {});
        return found;
      }
    }
    if (done) break;
  }
  return inspectLine(buffer);
}

const search = instantsearch({
  indexName: searchIndex,
  searchClient,
});

search.addWidgets([
  instantsearch.widgets.configure({
    attributesToHighlight: ["body", "title", "handle"],
    attributesToCrop: ["body:45"],
    cropMarker: "...",
    highlightPreTag: "<mark>",
    highlightPostTag: "</mark>",
  }),
  instantsearch.widgets.searchBox({
    container: "#searchbox",
    placeholder: "Search TikTok, ChatGPT, schema, AI Overview...",
    autofocus: true,
    showReset: true,
    showSubmit: true,
  }),
  instantsearch.widgets.stats({
    container: "#stats",
    templates: {
      text(data) {
        return `${data.nbHits} passages · ${data.processingTimeMS}ms`;
      },
    },
  }),
  instantsearch.widgets.currentRefinements({
    container: "#current-refinements",
  }),
  instantsearch.widgets.refinementList({
    container: "#author-refinement",
    attribute: "handle",
    searchable: true,
    limit: 8,
  }),
  instantsearch.widgets.refinementList({
    container: "#source-refinement",
    attribute: "source_type",
    templates: {
      item(item) {
        return `
          <label class="ais-RefinementList-label">
            <input class="ais-RefinementList-checkbox" type="checkbox" value="${item.value}" ${item.isRefined ? "checked" : ""} />
            <span>${sourceLabel(item.label)}</span>
            <span class="ais-RefinementList-count">${item.count}</span>
          </label>
        `;
      },
    },
  }),
  instantsearch.widgets.refinementList({
    container: "#year-refinement",
    attribute: "year",
    sortBy: ["name:desc"],
  }),
  instantsearch.widgets.hits({
    container: "#hits",
    templates: {
      item: hitTemplate,
      empty: `<div class="empty"><strong>No results found.</strong><p>Try another phrase or remove a filter.</p></div>`,
    },
  }),
  {
    render: renderSearchSignal,
  },
  instantsearch.widgets.pagination({
    container: "#pagination",
  }),
]);

function applyFacetRoute(attribute, value) {
  if (!search.helper || !value) return false;
  const normalized = attribute === "handle" ? `@${stripHandle(value)}` : value;
  const disjunctive = search.helper.state.disjunctiveFacetsRefinements?.[attribute] || [];
  const conjunctive = search.helper.state.facetsRefinements?.[attribute] || [];
  const current = [...disjunctive, ...conjunctive];
  if (current.length === 1 && current[0] === normalized) return false;
  search.helper.clearRefinements(attribute);
  search.helper.toggleFacetRefinement(attribute, normalized);
  return true;
}

function applyKnowledgeRouteState(route = {}, options = {}) {
  if (!search.helper) return;
  applyingRouteState = true;
  let needsSearch = false;
  const nextQuery = compactText(route.q || (!route.q && route.topic ? routeTopicLabel(route.topic) : ""));
  if (nextQuery && search.helper.state.query !== nextQuery) {
    search.helper.setQuery(nextQuery);
    needsSearch = true;
  }
  if (route.creator && applyFacetRoute("handle", route.creator)) needsSearch = true;
  if (route.year && applyFacetRoute("year", route.year)) needsSearch = true;
  if (route.source_type && applyFacetRoute("source_type", route.source_type)) needsSearch = true;
  document.body.classList.toggle("has-route-creator", Boolean(route.creator));
  document.body.classList.toggle("has-route-topic", Boolean(route.topic));
  if (needsSearch) search.helper.search();
  if (route.source) {
    showSourceDetail(route.source, { pushRoute: false, scroll: !options.initial });
  } else {
    closeSourceDetail({ pushRoute: false });
  }
  syncWorkspaceActiveState(route);
  applyingRouteState = false;
}

search.start();

applyKnowledgeRouteState(getKnowledgeRouteState(), { initial: true });
updateManifestCounters();
loadAnalyticsData().then((state) => {
  renderAnalyticsStrip(state);
  search.refresh();
});

presetButtons.forEach((button) => {
  button.setAttribute("aria-pressed", "false");
  button.addEventListener("click", () => {
    const term = button.getAttribute("data-query") || "";
    const query = mergeQueryTerm(search.helper.state.query || "", term);
    search.helper.setQuery(query).search();
    setKnowledgeRouteState({ q: query, source: "" }, { replace: true });
    document.querySelector(".ais-SearchBox-input")?.focus();
  });
});

search.on("render", () => {
  const query = search.helper.state.query || "";
  syncPresetButtons(query);
  renderSelectedTerms(query);
  updateMobileFilterCount();
  if (!applyingRouteState) setKnowledgeRouteState({ q: query || "" }, { replace: true });
  syncWorkspaceActiveState(getKnowledgeRouteState());
});

selectedTerms?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-remove-term]");
  if (!button) return;
  const query = mergeQueryTerm(search.helper.state.query || "", button.getAttribute("data-remove-term") || "");
  search.helper.setQuery(query).search();
  setKnowledgeRouteState({ q: query, source: "" }, { replace: true });
});

document.addEventListener("click", (event) => {
  const backButton = event.target.closest("[data-source-detail-back]");
  if (backButton) {
    closeSourceDetail();
    return;
  }
  const routeLink = event.target.closest("[data-workspace-route]");
  if (routeLink) {
    event.preventDefault();
    const patch = { source: "" };
    if (routeLink.dataset.routeCreator) patch.creator = routeLink.dataset.routeCreator;
    if (routeLink.dataset.routeTopic) {
      patch.topic = routeLink.dataset.routeTopic;
      patch.q = routeTopicLabel(routeLink.dataset.routeTopic, routeLink.dataset.routeLabel || "");
    }
    setKnowledgeRouteState(patch);
    applyKnowledgeRouteState(getKnowledgeRouteState());
    return;
  }
  const button = event.target.closest(".view-source-detail");
  if (!button) return;
  showSourceDetail(button.getAttribute("data-item-id") || "", { pushRoute: true });
});

window.addEventListener("popstate", () => {
  applyKnowledgeRouteState(getKnowledgeRouteState());
});

mobileFilterToggle?.addEventListener("click", () => setMobileFiltersOpen(true));
mobileFilterClose?.addEventListener("click", () => setMobileFiltersOpen(false));
mobileFilterBackdrop?.addEventListener("click", () => setMobileFiltersOpen(false));
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && document.body.classList.contains("filters-open")) {
    setMobileFiltersOpen(false);
  }
});
