(function () {
  "use strict";

  const root = document.querySelector("[data-evidence-search]");
  if (!root) return;

  const form = root.querySelector("[data-search-form]");
  const input = root.querySelector("[data-search-input]");
  const submit = root.querySelector("[data-search-submit]");
  const retry = root.querySelector("[data-search-retry]");
  const status = root.querySelector("[data-search-status]");
  const boundary = root.querySelector("[data-count-boundary]");
  const results = root.querySelector("[data-search-results]");
  const resultsSection = root.querySelector("[data-results-section]");
  const endpoint = root.dataset.searchEndpoint;

  if (!form || !input || !submit || !retry || !status || !boundary || !results || !resultsSection || !endpoint) return;

  const INDEX_UID = "base2026_public_tiktok";
  const RESULT_LIMIT = 24;
  const DISPLAY_LIMIT = 10;
  const MAX_EXCERPT_CHARS = 360;
  const REQUEST_TIMEOUT_MS = 12000;
  const RESULT_BOUNDARY = "This result shows what an attributed source says in the admitted Base2026 record. It does not prove that the recommendation is correct or effective.";
  const ALLOWED_ANALYTICS_EVENTS = new Set([
    "evidence_search_viewed",
    "evidence_search_submitted",
    "evidence_search_results_returned",
    "evidence_source_record_opened",
    "evidence_original_source_clicked",
    "evidence_search_completed",
    "evidence_search_empty",
    "evidence_search_partial",
    "evidence_search_error"
  ]);

  let activeController = null;
  let lastQuery = "";
  let pendingInputSource = "typed";
  let completedForResultSet = false;
  let renderedCount = 0;

  document.documentElement.classList.add("evidence-search-enhanced");

  function cleanText(value, maxLength) {
    if (typeof value !== "string") return "";
    const compact = value.replace(/\s+/g, " ").trim();
    if (!compact) return "";
    return compact.slice(0, maxLength);
  }

  function boundedExcerpt(value) {
    const compact = cleanText(value, MAX_EXCERPT_CHARS + 80);
    if (compact.length <= MAX_EXCERPT_CHARS) return compact;
    const shortened = compact.slice(0, MAX_EXCERPT_CHARS + 1);
    const lastBoundary = Math.max(shortened.lastIndexOf(". "), shortened.lastIndexOf("; "), shortened.lastIndexOf(" "));
    const cutoff = lastBoundary >= 240 ? lastBoundary + (shortened.slice(lastBoundary, lastBoundary + 2) === ". " ? 1 : 0) : MAX_EXCERPT_CHARS;
    return compact.slice(0, cutoff).trimEnd() + "…";
  }

  function element(tagName, className, textValue) {
    const node = document.createElement(tagName);
    if (className) node.className = className;
    if (typeof textValue === "string") node.textContent = textValue;
    return node;
  }

  function safePublicRecord(hit) {
    const itemId = cleanText(hit && hit.item_id, 80);
    if (/^tiktok-video-\d{10,30}$/.test(itemId)) {
      return { id: itemId, url: "/sources/" + itemId };
    }
    const videoId = cleanText(hit && hit.video_id, 40);
    if (/^\d{10,30}$/.test(videoId)) {
      return { id: "tiktok-video-" + videoId, url: "/sources/tiktok-video-" + videoId };
    }
    return null;
  }

  function safeOriginalUrl(value) {
    const raw = cleanText(value, 500);
    if (!raw) return "";
    try {
      const parsed = new URL(raw);
      if (parsed.protocol !== "https:") return "";
      if (parsed.hostname !== "tiktok.com" && parsed.hostname !== "www.tiktok.com") return "";
      return parsed.href;
    } catch (_error) {
      return "";
    }
  }

  function sourceType(hit) {
    return cleanText(hit && (hit.source_type || hit.platform), 48).replace(/[^a-zA-Z0-9_-]/g, "");
  }

  function sourceDate(hit) {
    const value = cleanText(hit && hit.published_date, 32);
    return /^\d{4}-\d{2}-\d{2}$/.test(value) ? value : "";
  }

  function topicsFor(hit) {
    const slugs = Array.isArray(hit && hit.topics) ? hit.topics : [];
    const labels = Array.isArray(hit && hit.topic_labels) ? hit.topic_labels : [];
    const output = [];
    slugs.slice(0, 3).forEach(function (rawSlug, index) {
      const slug = cleanText(rawSlug, 120).toLowerCase();
      if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) return;
      const label = cleanText(labels[index], 80) || slug.replace(/-/g, " ");
      output.push({ label: label });
    });
    return output;
  }

  function referrerClass() {
    if (!document.referrer) return "direct";
    try {
      const host = new URL(document.referrer).hostname.toLowerCase();
      if (host === window.location.hostname) return "internal";
      if (/google|bing|duckduckgo|yahoo|yandex|baidu/.test(host)) return "search";
      if (/tiktok|linkedin|facebook|instagram|x\.com|twitter|youtube/.test(host)) return "social";
      return "other";
    } catch (_error) {
      return "other";
    }
  }

  function viewportClass() {
    if (window.innerWidth < 640) return "small";
    if (window.innerWidth < 1024) return "medium";
    return "large";
  }

  function queryLengthBucket(query) {
    if (query.length <= 20) return "1_20";
    if (query.length <= 50) return "21_50";
    if (query.length <= 100) return "51_100";
    return "101_plus";
  }

  function queryTokenBucket(query) {
    const count = query.split(/\s+/).filter(Boolean).length;
    if (count <= 1) return "1";
    if (count <= 3) return "2_3";
    if (count <= 7) return "4_7";
    return "8_plus";
  }

  function countBucket(count, extended) {
    if (count <= 1) return "1";
    if (count <= 5) return "2_5";
    if (count <= 10) return "6_10";
    if (!extended) return "11_plus";
    if (count <= 25) return "11_25";
    if (count <= 100) return "26_100";
    return "101_plus";
  }

  function failedCountBucket(count) {
    if (count <= 1) return "1";
    if (count <= 5) return "2_5";
    return "6_plus";
  }

  function latencyBucket(milliseconds) {
    if (milliseconds < 500) return "under_500";
    if (milliseconds < 1500) return "500_1499";
    if (milliseconds < 3000) return "1500_2999";
    return "3000_plus";
  }

  function positionBucket(position) {
    if (position <= 3) return "1_3";
    if (position <= 10) return "4_10";
    return "11_plus";
  }

  function emitAnalytics(name, properties) {
    if (!ALLOWED_ANALYTICS_EVENTS.has(name)) return;
    const detail = { name: name, properties: Object.assign({}, properties) };
    window.dispatchEvent(new CustomEvent("base2026:analytics", { detail: detail }));
    if (Array.isArray(window.dataLayer)) {
      window.dataLayer.push(Object.assign({ event: name }, properties));
    }
  }

  function setStatus(state, message) {
    status.dataset.state = state;
    status.textContent = message;
  }

  function setLoading(loading) {
    submit.disabled = loading;
    submit.textContent = loading ? "Searching…" : "Search the evidence";
    input.setAttribute("aria-busy", loading ? "true" : "false");
  }

  function clearResults() {
    results.replaceChildren();
    boundary.hidden = true;
    retry.hidden = true;
    renderedCount = 0;
  }

  function queryFromHash() {
    const raw = window.location.hash.replace(/^#/, "");
    if (!raw.startsWith("search?")) return "";
    return cleanText(new URLSearchParams(raw.slice(7)).get("q"), 200);
  }

  function hashForQuery(query) {
    const parameters = new URLSearchParams();
    parameters.set("q", query);
    return "#search?" + parameters.toString();
  }

  function publicRequest(query) {
    return {
      queries: [{
        indexUid: INDEX_UID,
        q: query,
        limit: RESULT_LIMIT,
        attributesToRetrieve: [
          "id", "item_id", "source_id", "video_id", "title",
          "creator_display_name", "creator_handle", "handle", "source_url", "published_date",
          "source_type", "platform", "topics", "topic_labels"
        ],
        attributesToHighlight: []
      }]
    };
  }

  function normalizeResponse(payload) {
    if (!payload || !Array.isArray(payload.results) || !payload.results[0]) {
      throw new Error("invalid_response");
    }
    const response = payload.results[0];
    if (!Array.isArray(response.hits)) throw new Error("invalid_response");

    const seen = new Set();
    const valid = [];
    let failed = 0;
    response.hits.forEach(function (hit) {
      if (!hit || typeof hit !== "object") {
        failed += 1;
        return;
      }
      const record = safePublicRecord(hit);
      if (!record) {
        failed += 1;
        return;
      }
      if (seen.has(record.id)) return;
      seen.add(record.id);
      valid.push({ hit: hit, record: record });
    });

    const estimated = Number.isFinite(response.estimatedTotalHits) ? Math.max(0, Math.floor(response.estimatedTotalHits)) : valid.length;
    return {
      rows: valid.slice(0, DISPLAY_LIMIT),
      estimated: estimated,
      failed: failed,
      processingTime: Number.isFinite(response.processingTimeMs) ? Math.max(0, response.processingTimeMs) : 0
    };
  }

  function addLabeledText(card, label, value) {
    card.appendChild(element("h4", "", label));
    card.appendChild(element("p", "", value));
  }

  function renderResult(recordRow, position) {
    const hit = recordRow.hit;
    const record = recordRow.record;
    const creator = cleanText(hit.creator_handle || hit.handle || hit.creator_display_name, 100) || "Creator attribution unavailable in this record";
    const excerpt = boundedExcerpt(hit.title) || "No bounded public source summary is available in this record.";
    const originalUrl = safeOriginalUrl(hit.source_url);
    const type = sourceType(hit);
    const date = sourceDate(hit);
    const card = element("article", "b26-evidence-search__result-card");

    card.appendChild(element("p", "b26-evidence-search__result-index", "Result " + position));
    card.appendChild(element("p", "b26-evidence-search__result-index", "Creator"));
    card.appendChild(element("h3", "", creator));
    addLabeledText(card, "What the source says", excerpt);

    const metaHeading = element("h4", "", "Source details");
    const meta = element("div", "b26-evidence-search__result-meta");
    if (type) meta.appendChild(element("span", "", "Type: " + type.replace(/_/g, " ")));
    if (date) meta.appendChild(element("span", "", "Published: " + date));
    meta.appendChild(element("span", "", "Record: " + record.id));
    card.appendChild(metaHeading);
    card.appendChild(meta);

    const topics = topicsFor(hit);
    const topicList = element("div", "b26-evidence-search__topics");
    if (topics.length) {
      topics.forEach(function (topic) {
        topicList.appendChild(element("span", "", topic.label));
      });
    }
    const topicIndexLink = element("a", "", "Browse topics");
    topicIndexLink.href = "/topics/";
    topicList.appendChild(topicIndexLink);
    card.appendChild(topicList);

    const resultBoundary = element("p", "b26-evidence-search__result-boundary", RESULT_BOUNDARY);
    card.appendChild(resultBoundary);

    const actions = element("div", "b26-evidence-search__actions");
    const baseLink = element("a", "", "Open Base2026 record");
    baseLink.href = record.url;
    baseLink.addEventListener("click", function () {
      recordInspection("evidence_source_record_opened", "base2026_record_opened", record.id, type, position);
    });
    actions.appendChild(baseLink);

    if (originalUrl) {
      const originalLink = element("a", "", "Open original source ↗");
      originalLink.href = originalUrl;
      originalLink.target = "_blank";
      originalLink.rel = "noopener noreferrer";
      originalLink.addEventListener("click", function () {
        recordInspection("evidence_original_source_clicked", "original_source_opened", record.id, type, position);
      });
      actions.appendChild(originalLink);
    } else {
      actions.appendChild(element("span", "b26-evidence-search__original-unavailable", "Original source unavailable in this record"));
    }
    card.appendChild(actions);
    return card;
  }

  function recordInspection(eventName, completionMode, recordId, type, position) {
    emitAnalytics(eventName, {
      public_record_id: recordId,
      result_position_bucket: positionBucket(position),
      source_type: type || "unavailable"
    });
    if (!completedForResultSet) {
      completedForResultSet = true;
      emitAnalytics("evidence_search_completed", {
        completion_mode: completionMode,
        result_count_bucket: countBucket(renderedCount, true),
        render_mode: "enhanced"
      });
    }
  }

  function sourceDiversityHandoff(rows) {
    const ids = rows.map(function (row) {
      return row && row.record ? row.record.id : "";
    }).filter(function (id) {
      return /^tiktok-video-\d{10,30}$/.test(id);
    }).slice(0, 10);
    if (!ids.length) return null;

    const handoff = element("div", "b26-evidence-search__handoff");
    handoff.appendChild(element("p", "", "Want to compare this bounded public set? Keep the record IDs attached, then inspect creator and original-source relationships separately."));
    const link = element("a", "b26-button--primary", "Run the source diversity check");
    link.href = "/tools/source-diversity-check/?ids=" + encodeURIComponent(ids.join(","));
    handoff.appendChild(link);
    return handoff;
  }

  function renderMatches(normalized, query, wallTime) {
    const nodes = normalized.rows.map(function (row, index) {
      return renderResult(row, index + 1);
    });
    results.replaceChildren.apply(results, nodes);
    renderedCount = nodes.length;
    boundary.hidden = false;

    const partial = normalized.failed > 0;
    if (partial) {
      setStatus("partial", "Some matching records could not be loaded. The results below are incomplete; inspect the available records or retry the search before drawing a conclusion.");
      retry.hidden = false;
      emitAnalytics("evidence_search_partial", {
        loaded_count_bucket: countBucket(nodes.length, false),
        failed_count_bucket: failedCountBucket(normalized.failed),
        error_class: "record_validation"
      });
    } else {
      setStatus("result", "Showing admitted Base2026 matches for “" + query + "”. Inspect the creator, source record and original link before using a recommendation.");
    }

    const shown = Math.min(nodes.length, normalized.estimated || nodes.length);
    const countNote = element("p", "b26-evidence-search__result-count", "Showing " + shown + " of an estimated " + normalized.estimated + " admitted matches. Results are deduplicated by public source record.");
    results.prepend(countNote);
    const handoff = sourceDiversityHandoff(normalized.rows);
    if (handoff) results.appendChild(handoff);

    emitAnalytics("evidence_search_results_returned", {
      result_count_bucket: countBucket(normalized.estimated, true),
      latency_bucket_ms: latencyBucket(Math.max(wallTime, normalized.processingTime)),
      response_class: partial ? "partial" : "complete"
    });
  }

  function errorDetails(error, responseStatus) {
    if (error && error.name === "AbortError") return { errorClass: "timeout", statusBucket: "timeout" };
    if (responseStatus >= 500) return { errorClass: "http_error", statusBucket: "5xx" };
    if (responseStatus >= 400) return { errorClass: "http_error", statusBucket: "4xx" };
    if (error && error.message === "invalid_response") return { errorClass: "invalid_response", statusBucket: "unknown" };
    if (error instanceof TypeError) return { errorClass: "network", statusBucket: "network" };
    return { errorClass: "unknown", statusBucket: "unknown" };
  }

  async function runSearch(query, inputSource) {
    const normalizedQuery = cleanText(query, 200);
    if (normalizedQuery.length < 2) {
      input.value = normalizedQuery;
      setStatus("error", "Enter at least two characters to search the admitted Base2026 corpus.");
      input.focus();
      return;
    }

    if (activeController) activeController.abort();
    activeController = new AbortController();
    const requestController = activeController;
    const timeoutId = window.setTimeout(function () { requestController.abort(); }, REQUEST_TIMEOUT_MS);
    const startedAt = performance.now();
    let responseStatus = 0;

    lastQuery = normalizedQuery;
    input.value = normalizedQuery;
    completedForResultSet = false;
    clearResults();
    setLoading(true);
    setStatus("loading", "Searching the admitted Base2026 evidence…");

    emitAnalytics("evidence_search_submitted", {
      input_source: inputSource === "example" ? "example" : "typed",
      query_length_bucket: queryLengthBucket(normalizedQuery),
      query_token_bucket: queryTokenBucket(normalizedQuery),
      render_mode: "enhanced"
    });

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        mode: "cors",
        credentials: "omit",
        cache: "no-store",
        referrerPolicy: "strict-origin-when-cross-origin",
        headers: { "content-type": "application/json", "accept": "application/json" },
        body: JSON.stringify(publicRequest(normalizedQuery)),
        signal: requestController.signal
      });
      responseStatus = response.status;
      if (!response.ok) throw new Error("http_error");
      const payload = await response.json();
      const normalized = normalizeResponse(payload);

      if (!normalized.rows.length) {
        boundary.hidden = false;
        setStatus("empty", "No admitted Base2026 records matched “" + normalizedQuery + "”. This does not mean the topic has not been discussed elsewhere. Try a shorter phrase or a closely related term.");
        emitAnalytics("evidence_search_empty", {
          query_length_bucket: queryLengthBucket(normalizedQuery),
          query_token_bucket: queryTokenBucket(normalizedQuery),
          render_mode: "enhanced"
        });
      } else {
        renderMatches(normalized, normalizedQuery, performance.now() - startedAt);
      }
    } catch (error) {
      if (requestController !== activeController) return;
      const details = errorDetails(error, responseStatus);
      setStatus("error", "The public evidence search could not complete. Your query has been kept. Retry the search or browse the available topic pages.");
      retry.hidden = false;
      emitAnalytics("evidence_search_error", {
        error_class: details.errorClass,
        http_status_bucket: details.statusBucket,
        render_mode: "enhanced"
      });
    } finally {
      window.clearTimeout(timeoutId);
      if (requestController === activeController) {
        setLoading(false);
        activeController = null;
      }
    }
  }

  function updateHashAndSearch(query, inputSource) {
    const nextHash = hashForQuery(query);
    pendingInputSource = inputSource;
    if (window.location.hash === nextHash) {
      runSearch(query, pendingInputSource);
      pendingInputSource = "typed";
      return;
    }
    window.location.hash = nextHash;
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    if (!form.reportValidity()) return;
    updateHashAndSearch(input.value, "typed");
  });

  root.querySelectorAll("[data-example-query]").forEach(function (link) {
    link.addEventListener("click", function (event) {
      event.preventDefault();
      const query = cleanText(link.dataset.exampleQuery, 200);
      input.value = query;
      updateHashAndSearch(query, "example");
    });
  });

  retry.addEventListener("click", function () {
    if (lastQuery) runSearch(lastQuery, "typed");
  });

  window.addEventListener("hashchange", function () {
    const query = queryFromHash();
    if (!query) return;
    const source = pendingInputSource;
    pendingInputSource = "typed";
    runSearch(query, source);
  });

  emitAnalytics("evidence_search_viewed", {
    render_mode: "enhanced",
    referrer_class: referrerClass(),
    viewport_class: viewportClass()
  });

  const initialQuery = queryFromHash();
  if (initialQuery) {
    input.value = initialQuery;
    runSearch(initialQuery, "typed");
  }
})();
