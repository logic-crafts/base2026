(function () {
  "use strict";

  const ENDPOINT = "/api/analytics/event";
  const MAX_EVENTS_PER_PAGE = 24;
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
    source_check_card_copied: new Set(["copy_format", "count_bucket", "position_bucket", "metadata_resolution"])
  });
  const VALUE_SETS = Object.freeze({
    completion_mode: new Set(["base2026_record_opened", "original_source_opened", "lookup_complete", "input_rejected"]),
    copy_format: new Set(["record_card", "markdown", "json"]),
    decision: new Set(["use", "investigate", "exclude", "inspect_originals", "find_independent_evidence", "keep_unknowns"]),
    error_class: new Set(["record_validation", "timeout", "http_error", "invalid_response", "network", "unknown"]),
    input_mode: new Set(["delimited_ids", "json_records"]),
    input_source: new Set(["typed", "example", "evidence_search_handoff", "direct"]),
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
    window.fetch(ENDPOINT, {
      method: "POST",
      mode: "same-origin",
      credentials: "omit",
      cache: "no-store",
      keepalive: true,
      referrerPolicy: "no-referrer",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ event: name, route: route, properties: properties })
    }).catch(function () {
      // Measurement is best effort and must never affect the tool UX.
    });
  }

  window.addEventListener("base2026:analytics", sendActivationEvent, false);
})();
