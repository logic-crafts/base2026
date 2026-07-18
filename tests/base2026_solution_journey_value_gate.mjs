import fs from "node:fs";
import vm from "node:vm";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const runtimePath = path.join(here, "..", "web", "static", "base2026-solution-journey.js");
const runtime = fs.readFileSync(runtimePath, "utf8");

const preferences = { analytics: true };
const localStorage = {
  getItem(key) {
    return key === "ay_cookie_preferences_v1" ? JSON.stringify(preferences) : null;
  },
};
const sessionValues = new Map();
const sessionStorage = {
  getItem: (key) => sessionValues.get(key) || null,
  setItem: (key, value) => sessionValues.set(key, String(value)),
  removeItem: (key) => sessionValues.delete(key),
};
const dispatched = [];
const window = {
  dataLayer: [],
  addEventListener() {},
  dispatchEvent(event) { dispatched.push(event.detail); },
};
const document = {
  currentScript: { src: "https://example.test/knowledge/static/base2026-solution-journey.js" },
  documentElement: { dataset: { cookieAnalytics: "allowed" } },
  head: { append() {} },
  addEventListener() {},
  querySelector() { return null; },
  createElement() { return { dataset: {} }; },
};
class CustomEvent {
  constructor(type, options = {}) { this.type = type; this.detail = options.detail; }
}

const context = {
  URL,
  CustomEvent,
  document,
  localStorage,
  location: { origin: "https://example.test", pathname: "/knowledge/" },
  sessionStorage,
  window,
};
vm.createContext(context);
vm.runInContext(runtime, context, { filename: runtimePath });
const emit = window.__BASE2026_PRODUCT_TRUTH__?.emit;
if (typeof emit !== "function") throw new Error("Product Truth emit() was not exposed");

const approvedSolution = "measure-ai-search-visibility";
const valid = [
  ["product_search_submitted", { query_length_bucket: "3_5_terms", result_count_bucket: "1_10", origin_surface: "search" }],
  ["source_opened", { public_source_id: "tiktok-video-7612827094069890317", origin_surface: "source_detail", admission_class: "normal_public_card" }],
  ["evidence_actioned", { action_type: "copy_citation", public_source_id: "tiktok-video-7612827094069890317", origin_surface: "search" }],
  ["solution_opened", { solution_id: approvedSolution, origin_surface: "solution" }],
  ["research_bridge_clicked", { bridge_id: "solution_to_apply_research", destination_id: "apply_research", origin_surface: "solution" }],
];

for (const [eventName, payload] of valid) {
  const before = window.dataLayer.length;
  if (emit(eventName, payload) !== true) throw new Error(`Valid ${eventName} failed closed`);
  if (window.dataLayer.length !== before + 1) throw new Error(`Valid ${eventName} was not emitted exactly once`);
}

const invalid = [
  ["product_search_submitted", { query_length_bucket: "google business profile", result_count_bucket: "1_10", origin_surface: "search" }],
  ["product_search_submitted", { query_length_bucket: "3_5_terms", result_count_bucket: "1_10", origin_surface: "solution" }],
  ["product_search_submitted", { query_length_bucket: "3_5_terms", result_count_bucket: "1_10", origin_surface: "search", raw_query: "private" }],
  ["source_opened", { public_source_id: "https://private.test/source", origin_surface: "source_detail", admission_class: "normal_public_card" }],
  ["source_opened", { public_source_id: "tiktok-video-7612827094069890317", origin_surface: "knowledge_home", admission_class: "normal_public_card" }],
  ["source_opened", { public_source_id: "tiktok-video-7612827094069890317", origin_surface: "source_detail", admission_class: "provenance_archive_noindex" }],
  ["evidence_actioned", { action_type: "download_private", public_source_id: "tiktok-video-7612827094069890317", origin_surface: "search" }],
  ["solution_opened", { solution_id: "unapproved-solution", origin_surface: "solution" }],
  ["solution_opened", { solution_id: approvedSolution, origin_surface: "knowledge_home" }],
  ["research_bridge_clicked", { bridge_id: "solution_to_apply_research", destination_id: "pricing", origin_surface: "solution" }],
  ["research_bridge_clicked", { bridge_id: "other", destination_id: "apply_research", origin_surface: "solution" }],
  ["research_bridge_clicked", { bridge_id: "solution_to_apply_research", destination_id: "apply_research", origin_surface: "search" }],
  ["solution_opened", { solution_id: approvedSolution }],
  ["solution_opened", { solution_id: approvedSolution, origin_surface: 42 }],
];

for (const [eventName, payload] of invalid) {
  const beforeLayer = window.dataLayer.length;
  const beforeDispatch = dispatched.length;
  if (emit(eventName, payload) !== false) throw new Error(`Invalid ${eventName} did not fail closed`);
  if (window.dataLayer.length !== beforeLayer || dispatched.length !== beforeDispatch) {
    throw new Error(`Invalid ${eventName} leaked into an analytics sink`);
  }
}

preferences.analytics = false;
const beforeConsent = window.dataLayer.length;
if (emit(valid[0][0], valid[0][1]) !== false || window.dataLayer.length !== beforeConsent) {
  throw new Error("Consent-denied event did not fail closed");
}

process.stdout.write(JSON.stringify({ valid: valid.length, rejected: invalid.length, consent_gate: true }) + "\n");
