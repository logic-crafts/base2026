(function () {
  "use strict";

  const ENDPOINT = "/api/analytics/event";
  const MAX_EVENTS_PER_PAGE = 24;
  const CAMPAIGN_PARAM = "b26_campaign";
  const QA_PARAM = "b26_qa";
  const CAMPAIGNS = new Set(["none", "evidence_pulse", "worked_example", "agent_workflow"]);
  const ROUTE_EVENTS = Object.freeze({
    "/tools/evidence-search/": new Set([
      "evidence_search_viewed",
      "evidence_search_submitted",
      "evidence_search_results_returned",
      "evidence_source_record_opened",
      "evidence_original_source_clicked",
      "evidence_search_completed",
      "evidence_search_empty",
      "evidence_search_partial",
      "evidence_search_error"
    ]),
    "/tools/source-diversity-check/": new Set([
      "source_check_run",
      "source_check_completed",
      "source_check_decision_recorded",
      "source_check_card_copied"
    ]),
    "/tools/source-backed-brief/": new Set([
      "brief_required_fields_completed",
      "brief_preview_created",
      "brief_exported",
      "brief_completed"
    ])
  });
  const EVENT_PROPERTIES = Object.freeze({
    evidence_search_viewed: new Set(["render_mode", "viewport_class"]),
    evidence_search_submitted: new Set(["input_source", "query_length_bucket", "query_token_bucket", "render_mode"]),
    evidence_search_results_returned: new Set(["count_bucket", "latency_bucket_ms", "response_class"]),
    evidence_source_record_opened: new Set(["position_bucket"]),
    evidence_original_source_clicked: new Set(["position_bucket"]),
    evidence_search_completed: new Set(["completion_mode", "count_bucket", "render_mode"]),
    evidence_search_empty: new Set(["query_length_bucket", "query_token_bucket", "render_mode"]),
    evidence_search_partial: new Set(["loaded_count_bucket", "failed_count_bucket", "error_class"]),
    evidence_search_error: new Set(["error_class", "render_mode"]),
    source_check_run: new Set([
      "input_source",
      "input_mode",
      "submitted_count_bucket",
      "invalid_input_bucket",
      "duplicate_input_bucket",
      "record_id_bucket",
      "source_id_bucket",
      "viewport_class"
    ]),
    source_check_completed: new Set(["completion_mode", "count_bucket", "response_class", "viewport_class"]),
    source_check_decision_recorded: new Set(["decision", "scope", "count_bucket", "position_bucket", "metadata_resolution", "viewport_class"]),
    source_check_card_copied: new Set(["copy_format", "count_bucket", "position_bucket", "metadata_resolution"]),
    brief_required_fields_completed: new Set(["deliverable", "selected_count_bucket", "input_source", "viewport_class"]),
    brief_preview_created: new Set(["deliverable", "response_class", "selected_count_bucket", "resolved_count_bucket", "viewport_class"]),
    brief_exported: new Set(["export_format", "export_action", "selected_count_bucket", "resolved_count_bucket", "viewport_class"]),
    brief_completed: new Set(["response_class", "deliverable", "selected_count_bucket", "invalid_field_bucket", "input_source", "viewport_class"])
  });
  const VALUE_SETS = Object.freeze({
    completion_mode: new Set(["base2026_record_opened", "original_source_opened", "lookup_complete", "input_rejected"]),
    copy_format: new Set(["record_card", "markdown", "json"]),
    deliverable: new Set(["brief", "memo", "outline"]),
    decision: new Set(["use", "investigate", "exclude", "inspect_originals", "find_independent_evidence", "keep_unknowns"]),
    error_class: new Set(["record_validation", "timeout", "http_error", "invalid_response", "network", "unknown"]),
    input_mode: new Set(["delimited_ids", "json_records"]),
    input_source: new Set(["typed", "example", "evidence_search_handoff", "direct"]),
    export_action: new Set(["copy", "download"]),
    export_format: new Set(["markdown", "json"]),
    latency_bucket_ms: new Set(["under_500", "500_1499", "1500_2999", "3000_plus"]),
    metadata_resolution: new Set(["complete", "partial", "unresolved"]),
    position_bucket: new Set(["1_3", "4_10", "11_plus"]),
    render_mode: new Set(["enhanced"]),
    response_class: new Set(["complete", "partial", "no_resolved_records", "invalid_input"]),
    scope: new Set(["record", "record_set"]),
    viewport_class: new Set(["small", "medium", "large"]),
    count_bucket: new Set(["0_1", "1", "2_5", "6_10", "11_plus", "11_25", "26_100", "101_plus"]),
    submitted_count_bucket: new Set(["0_1", "1", "2_5", "6_10", "11_plus"]),
    invalid_input_bucket: new Set(["0_1", "1", "2_5", "6_10", "11_plus"]),
    duplicate_input_bucket: new Set(["0_1", "1", "2_5", "6_10", "11_plus"]),
    record_id_bucket: new Set(["0_1", "1", "2_5", "6_10", "11_plus"]),
    source_id_bucket: new Set(["0_1", "1", "2_5", "6_10", "11_plus"]),
    selected_count_bucket: new Set(["0_1", "1", "2_5", "6_10", "11_plus"]),
    resolved_count_bucket: new Set(["0_1", "1", "2_5", "6_10", "11_plus"]),
    invalid_field_bucket: new Set(["0_1", "1", "2_5", "6_10", "11_plus"]),
    loaded_count_bucket: new Set(["1", "2_5", "6_10", "11_plus"]),
    failed_count_bucket: new Set(["1", "2_5", "6_plus"]),
    query_length_bucket: new Set(["1_20", "21_50", "51_100", "101_plus"]),
    query_token_bucket: new Set(["1", "2_3", "4_7", "8_plus"])
  });
  const PROPERTY_ALIASES = Object.freeze({
    record_count_bucket: "count_bucket",
    result_count_bucket: "count_bucket",
    record_position_bucket: "position_bucket",
    result_position_bucket: "position_bucket"
  });

  let sentEvents = 0;

  function safeValue(value, property) {
    return typeof value === "string"
      && value.length > 0
      && value.length <= 32
      && !/[\u0000-\u001f\u007f-\u009f]/u.test(value)
      && VALUE_SETS[property]
      && VALUE_SETS[property].has(value);
  }

  function routeForCurrentPath() {
    const pathname = window.location.pathname;
    return ROUTE_EVENTS[pathname] ? pathname : "";
  }

  function contextFromCurrentUrl() {
    const fallback = {
      cohort: "unattributed",
      campaign: "none",
      explicitCampaign: false,
      explicitQa: false
    };
    if (!window.location || typeof URLSearchParams !== "function") return fallback;

    let parameters;
    try {
      // Read only the two fixed tags. The complete URL is never placed in an
      // event body, and an absent/invalid/duplicate value cannot claim its
      // corresponding context dimension.
      parameters = new URLSearchParams(window.location.search || "");
    } catch (_error) {
      return fallback;
    }
    const campaignValues = parameters.getAll(CAMPAIGN_PARAM);
    const qaValues = parameters.getAll(QA_PARAM);
    const explicitCampaign = campaignValues.length === 1 && CAMPAIGNS.has(campaignValues[0]);
    const explicitQa = qaValues.length === 1 && qaValues[0] === "1";
    const campaign = explicitCampaign ? campaignValues[0] : "none";
    const cohort = explicitQa
      ? "operator_qa"
      : explicitCampaign && campaign !== "none"
        ? "experiment"
        : "unattributed";
    return { cohort, campaign, explicitCampaign, explicitQa };
  }

  function eventContext() {
    const context = contextFromCurrentUrl();
    if (!context.explicitCampaign && !context.explicitQa) return null;
    return { cohort: context.cohort, campaign: context.campaign };
  }

  function anchorFromClick(event) {
    let target = event && event.target;
    if (!target) return null;
    if (typeof target.closest === "function") return target.closest("a[href]");
    while (target && target !== window) {
      if (String(target.tagName || "").toLowerCase() === "a" && typeof target.href === "string") return target;
      target = target.parentElement;
    }
    return null;
  }

  function propagateTaggedContext(event) {
    const context = contextFromCurrentUrl();
    if (!context.explicitCampaign && !context.explicitQa) return;
    const link = anchorFromClick(event);
    if (!link || typeof link.href !== "string" || typeof URL !== "function") return;

    let destination;
    try {
      destination = new URL(link.href, window.location.origin);
    } catch (_error) {
      return;
    }
    if (destination.origin !== window.location.origin || !ROUTE_EVENTS[destination.pathname]) return;

    // A tagged source owns both fixed context dimensions. Clear destination
    // copies first so a one-tag source cannot inherit a stale opposing tag.
    destination.searchParams.delete(CAMPAIGN_PARAM);
    destination.searchParams.delete(QA_PARAM);
    if (context.explicitCampaign) {
      destination.searchParams.append(CAMPAIGN_PARAM, context.campaign);
    }
    if (context.explicitQa) {
      destination.searchParams.append(QA_PARAM, "1");
    }
    const nextHref = destination.pathname + destination.search + destination.hash;
    if (typeof link.setAttribute === "function") link.setAttribute("href", nextHref);
    else link.href = nextHref;
  }

  function boundedProperties(name, rawProperties) {
    if (!rawProperties || typeof rawProperties !== "object" || Array.isArray(rawProperties)) return null;
    const allowed = EVENT_PROPERTIES[name];
    if (!Object.prototype.hasOwnProperty.call(EVENT_PROPERTIES, name) || !allowed) return null;
    const output = {};
    Object.keys(rawProperties).sort().forEach(function (property) {
      const canonical = PROPERTY_ALIASES[property] || property;
      if (!allowed.has(canonical) || Object.prototype.hasOwnProperty.call(output, canonical)) return;
      if (!safeValue(rawProperties[property], canonical)) return;
      output[canonical] = rawProperties[property];
    });
    return output;
  }

  function sendActivationEvent(domEvent) {
    if (sentEvents >= MAX_EVENTS_PER_PAGE) return;
    const detail = domEvent && domEvent.detail;
    if (!detail || typeof detail !== "object") return;
    const name = detail.name;
    const route = routeForCurrentPath();
    if (!route || !ROUTE_EVENTS[route].has(name)) return;
    const properties = boundedProperties(name, detail.properties);
    if (!properties || typeof window.fetch !== "function") return;
    sentEvents += 1;
    const context = eventContext();
    const payload = { event: name, route: route, properties: properties };
    if (context) payload.context = context;
    window.fetch(ENDPOINT, {
      method: "POST",
      mode: "same-origin",
      credentials: "omit",
      cache: "no-store",
      keepalive: true,
      referrerPolicy: "no-referrer",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload)
    }).catch(function () {
      // Measurement is best effort and must never affect the tool UX.
    });
  }

  window.addEventListener("click", propagateTaggedContext, true);
  window.addEventListener("base2026:analytics", sendActivationEvent, false);
})();
