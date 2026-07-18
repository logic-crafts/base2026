(() => {
  const assetScript = document.currentScript;
  const assetBase = assetScript?.src ? new URL(".", assetScript.src) : new URL("./static/", document.baseURI);
  const contractVersion = "base2026-product-truth-events/v1";
  const approvedSolutionIds = new Set([
    "answer-ready-service-page-checklist",
    "content-refresh-prioritization",
    "google-business-profile-visibility-audit",
    "measure-ai-search-visibility",
    "search-console-high-impression-low-ctr",
  ]);
  const eventProperties = {
    product_search_submitted: new Set(["query_length_bucket", "result_count_bucket", "origin_surface"]),
    source_opened: new Set(["public_source_id", "origin_surface", "admission_class"]),
    evidence_actioned: new Set(["action_type", "public_source_id", "origin_surface"]),
    solution_opened: new Set(["solution_id", "origin_surface"]),
    research_bridge_clicked: new Set(["bridge_id", "destination_id", "origin_surface"]),
  };
  const queryLengthBuckets = new Set(["0_terms", "1_2_terms", "3_5_terms", "6_plus_terms"]);
  const resultCountBuckets = new Set(["0", "1_10", "11_50", "51_plus"]);
  const publicSourceIdPattern = /^[a-z0-9]+(?:-[a-z0-9]+)+$/;
  const eventValueValidators = {
    product_search_submitted: {
      query_length_bucket: (value) => queryLengthBuckets.has(value),
      result_count_bucket: (value) => resultCountBuckets.has(value),
      origin_surface: (value) => new Set(["knowledge_home", "search"]).has(value),
    },
    source_opened: {
      public_source_id: (value) => publicSourceIdPattern.test(value),
      origin_surface: (value) => new Set(["search", "solution", "source_detail"]).has(value),
      admission_class: (value) => value === "normal_public_card",
    },
    evidence_actioned: {
      action_type: (value) => new Set(["copy_citation", "copy_link"]).has(value),
      public_source_id: (value) => publicSourceIdPattern.test(value),
      origin_surface: (value) => new Set(["search", "source_detail"]).has(value),
    },
    solution_opened: {
      solution_id: (value) => approvedSolutionIds.has(value),
      origin_surface: (value) => new Set(["search", "solution", "source_detail"]).has(value),
    },
    research_bridge_clicked: {
      bridge_id: (value) => value === "solution_to_apply_research",
      destination_id: (value) => value === "apply_research",
      origin_surface: (value) => value === "solution",
    },
  };
  let registryPromise;
  let pendingSearchOrigin = "";
  let lastRenderedSource = "";

  function analyticsAllowed() {
    try {
      const prefs = JSON.parse(localStorage.getItem("ay_cookie_preferences_v1") || "null");
      const state = document.documentElement.dataset.cookieAnalytics;
      return Boolean(prefs?.analytics) && state !== "blocked";
    } catch (_) {
      return false;
    }
  }

  function whenConsentStateReady(callback) {
    const current = document.documentElement.dataset.cookieAnalytics;
    if (current === "allowed" || current === "blocked") {
      callback();
      return;
    }
    try {
      const stored = JSON.parse(localStorage.getItem("ay_cookie_preferences_v1") || "null");
      if (stored && typeof stored.analytics === "boolean") {
        callback();
        return;
      }
    } catch (_) {
      // Wait for the consent surface to publish an explicit state.
    }
    let completed = false;
    const run = () => {
      if (completed) return;
      const state = document.documentElement.dataset.cookieAnalytics;
      if (state !== "allowed" && state !== "blocked") return;
      completed = true;
      observer.disconnect();
      callback();
    };
    const observer = new MutationObserver(run);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-cookie-analytics"] });
    window.addEventListener("load", run, { once: true });
  }

  function emit(eventName, properties = {}) {
    const allowed = eventProperties[eventName];
    if (!allowed || !analyticsAllowed()) return false;
    if (!properties || typeof properties !== "object" || Array.isArray(properties)) return false;
    const keys = Object.keys(properties);
    if (keys.length !== allowed.size || keys.some((key) => !allowed.has(key))) return false;
    const validators = eventValueValidators[eventName];
    if (!validators) return false;
    for (const key of allowed) {
      const value = properties[key];
      if (typeof value !== "string" || !validators[key]?.(value)) return false;
    }
    const safe = { event: eventName, ...properties };
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push(safe);
    window.dispatchEvent(new CustomEvent("base2026:product-truth-event", { detail: safe }));
    return true;
  }

  function solutionIdFromPath() {
    const match = location.pathname.match(/\/knowledge\/solutions\/([a-z0-9-]+)\.html$/);
    return match && approvedSolutionIds.has(match[1]) ? match[1] : "";
  }

  function createText(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    node.textContent = text;
    return node;
  }

  function createBridge(mapping, runtime) {
    const section = document.createElement("section");
    section.id = "solutions";
    section.className = runtime
      ? "source-detail-section b26-source-solution-bridge"
      : "b26-source-section b26-source-solution-bridge";
    section.dataset.sourceSolutionCount = String(mapping.solutions.length);
    const heading = document.createElement("div");
    heading.className = runtime ? "source-detail-section-title b26-source-solution-bridge__heading" : "b26-section-heading b26-source-solution-bridge__heading";
    heading.append(createText("p", "", "Evidence → decision"));
    heading.append(createText(runtime ? "h3" : "h2", "", "Decision playbooks using this source"));
    section.append(heading);
    section.append(createText(
      "p",
      "b26-source-solution-bridge__boundary",
      "Shown only where this exact reviewed source signal contributes to an approved Base2026 Solution. Creator claims remain separate from Base2026 synthesis.",
    ));
    const list = document.createElement("div");
    list.className = "b26-source-solution-list";
    for (const solution of mapping.solutions) {
      if (!approvedSolutionIds.has(solution.id)) continue;
      const article = document.createElement("article");
      article.className = "b26-source-solution-card";
      article.dataset.solutionId = solution.id;
      article.append(createText("span", "b26-source-solution-card__role", "Evidence-bound Solution"));
      const title = document.createElement(runtime ? "h4" : "h3");
      const link = document.createElement("a");
      link.href = solution.href;
      link.dataset.journeyAction = "solution_opened";
      link.dataset.journeySurface = runtime ? "search_source_panel" : "source_detail";
      link.dataset.solutionId = solution.id;
      link.textContent = solution.title;
      title.append(link);
      article.append(title);
      article.append(createText("p", "", solution.why_relevant));
      list.append(article);
    }
    section.append(list);
    return section;
  }

  function registry() {
    if (!registryPromise) {
      registryPromise = fetch(new URL("base2026-solution-journey.json", assetBase), { credentials: "same-origin" })
        .then((response) => {
          if (!response.ok) throw new Error(`Solution journey registry ${response.status}`);
          return response.json();
        })
        .then((payload) => {
          if (payload?.schema !== "base2026.solution-journey-registry/v1") throw new Error("Unexpected Solution journey registry schema");
          const observed = [...(payload.approved_solution_ids || [])].sort();
          const expected = [...approvedSolutionIds].sort();
          if (JSON.stringify(observed) !== JSON.stringify(expected)) throw new Error("Solution journey approval mismatch");
          return payload;
        });
    }
    return registryPromise;
  }

  async function injectRuntimeBridge() {
    const panel = document.querySelector("#source-detail-panel");
    const sourceNode = panel?.querySelector("[data-source-item-id]");
    if (!panel || !sourceNode || panel.querySelector("#solutions")) return;
    const payload = await registry().catch(() => null);
    const mapping = payload?.source_mappings?.find((row) => row.item_id === sourceNode.dataset.sourceItemId);
    if (!mapping?.solutions?.length || panel.querySelector("#solutions")) return;
    const body = panel.querySelector(".source-detail-body");
    const intelligence = body?.querySelector(".source-detail-section:nth-child(2)");
    if (!body) return;
    const bridge = createBridge(mapping, true);
    if (intelligence) intelligence.insertAdjacentElement("afterend", bridge);
    else body.append(bridge);
  }

  function safeOrigin(value, fallback = "source_detail") {
    const allowed = new Set(["knowledge_home", "search", "solution", "source_detail"]);
    return allowed.has(value) ? value : fallback;
  }

  function sourceIdentity(node) {
    const publicSourceId = node?.dataset.sourceItemId || "";
    const admissionClass = node?.dataset.admissionClass || node?.dataset.admissionState || "";
    if (!publicSourceIdPattern.test(publicSourceId)) return null;
    if (admissionClass !== "normal_public_card") return null;
    return { publicSourceId, admissionClass };
  }

  function sourceOrigin(runtime) {
    if (runtime) return "search";
    try {
      const referrer = document.referrer ? new URL(document.referrer) : null;
      if (referrer?.origin !== location.origin) return "source_detail";
      if (referrer.pathname.startsWith("/knowledge/solutions/")) return "solution";
      if (referrer.pathname === "/knowledge/" || referrer.pathname === "/knowledge/index.html") return "search";
    } catch (_) {
      return "source_detail";
    }
    return "source_detail";
  }

  function emitSourceOpened(node, runtime) {
    const identity = sourceIdentity(node);
    if (!identity) {
      if (runtime) lastRenderedSource = "";
      return;
    }
    if (runtime && identity.publicSourceId === lastRenderedSource) return;
    if (runtime) lastRenderedSource = identity.publicSourceId;
    emit("source_opened", {
      public_source_id: identity.publicSourceId,
      origin_surface: sourceOrigin(runtime),
      admission_class: identity.admissionClass,
    });
  }

  function currentSourceIdentity() {
    return sourceIdentity(
      document.querySelector("#source-detail-panel [data-source-item-id]")
      || document.querySelector("main[data-source-item-id]"),
    );
  }

  function loadStyles() {
    const href = new URL("base2026-solution-journey.css", assetBase).href;
    if (document.querySelector('[data-base2026-solution-journey="styles"]')) return;
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    link.dataset.base2026SolutionJourney = "styles";
    document.head.append(link);
  }

  document.addEventListener("submit", (event) => {
    const form = event.target.closest?.(".ais-SearchBox-form");
    if (!form) return;
    pendingSearchOrigin = "search";
  });

  document.addEventListener("input", (event) => {
    if (!event.target.matches?.(".ais-SearchBox-input")) return;
    pendingSearchOrigin = "search";
  });

  document.addEventListener("base2026:search-results-available", (event) => {
    if (!pendingSearchOrigin) return;
    const detail = event.detail || {};
    emit("product_search_submitted", {
      query_length_bucket: detail.query_length_bucket,
      result_count_bucket: detail.result_count_bucket,
      origin_surface: safeOrigin(pendingSearchOrigin, "search"),
    });
    pendingSearchOrigin = "";
  });

  document.addEventListener("click", (event) => {
    const target = event.target.closest?.("a, button");
    if (!target) return;
    if (target.matches("[data-query]")) {
      pendingSearchOrigin = "knowledge_home";
    }
    if (target.matches('[data-journey-action="solution_opened"]')) {
      const solutionId = target.dataset.solutionId || "";
      if (approvedSolutionIds.has(solutionId)) {
        sessionStorage.setItem(
          "base2026_solution_origin_v1",
          target.dataset.journeySurface === "search_source_panel" ? "search" : "source_detail",
        );
      }
    }
    const evidenceAction = target.matches('[data-share-action="copy-citation"]')
      ? "copy_citation"
      : target.matches('[data-share-action="copy-link"], [data-copy-source]')
        ? "copy_link"
        : "";
    if (evidenceAction) {
      const identity = currentSourceIdentity();
      if (identity) {
        emit("evidence_actioned", {
          action_type: evidenceAction,
          public_source_id: identity.publicSourceId,
          origin_surface: document.querySelector("#source-detail-panel [data-source-item-id]") ? "search" : "source_detail",
        });
      }
    }
    if (target.matches('[data-research-bridge="solution_to_apply_research"]')) {
      if (approvedSolutionIds.has(target.dataset.originId || solutionIdFromPath())) {
        emit("research_bridge_clicked", {
          bridge_id: "solution_to_apply_research",
          destination_id: "apply_research",
          origin_surface: "solution",
        });
      }
    }
  });

  loadStyles();
  const panel = document.querySelector("#source-detail-panel");
  if (panel) {
    new MutationObserver(() => {
      const sourceNode = panel.querySelector("[data-source-item-id]");
      emitSourceOpened(sourceNode, true);
      injectRuntimeBridge();
    }).observe(panel, { childList: true, subtree: true });
    injectRuntimeBridge();
  }
  const staticSource = document.querySelector("main[data-source-item-id]");
  if (staticSource) whenConsentStateReady(() => emitSourceOpened(staticSource, false));
  const renderedSolutionId = solutionIdFromPath();
  if (renderedSolutionId && document.querySelector("main.solution-page")) {
    whenConsentStateReady(() => {
      const origin = safeOrigin(sessionStorage.getItem("base2026_solution_origin_v1") || "solution", "solution");
      sessionStorage.removeItem("base2026_solution_origin_v1");
      emit("solution_opened", { solution_id: renderedSolutionId, origin_surface: origin });
    });
  }
  window.__BASE2026_PRODUCT_TRUTH__ = Object.freeze({ contractVersion, analyticsAllowed, emit });
})();
