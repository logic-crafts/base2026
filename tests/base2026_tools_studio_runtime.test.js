"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const SCRIPT = fs.readFileSync(
  path.join(__dirname, "..", "templates", "base2026-tools-studio.js"),
  "utf8",
);

class FakeClassList {
  constructor() {
    this.values = new Set();
  }

  add(...names) {
    names.forEach((name) => this.values.add(name));
  }

  remove(...names) {
    names.forEach((name) => this.values.delete(name));
  }

  contains(name) {
    return this.values.has(name);
  }

  toggle(name, force) {
    const next = force === undefined ? !this.values.has(name) : Boolean(force);
    if (next) this.values.add(name);
    else this.values.delete(name);
    return next;
  }
}

class FakeElement {
  constructor(attributes = {}) {
    this.attributes = { ...attributes };
    this.listeners = new Map();
    this.classList = new FakeClassList();
    this.style = {};
    this.textContent = "";
    this.id = attributes.id || "";
    this.focused = false;
    this.offsetWidth = 0;
    this.card = null;
  }

  getAttribute(name) {
    return Object.prototype.hasOwnProperty.call(this.attributes, name)
      ? this.attributes[name]
      : null;
  }

  setAttribute(name, value) {
    this.attributes[name] = String(value);
    if (name === "id") this.id = String(value);
  }

  removeAttribute(name) {
    delete this.attributes[name];
  }

  hasAttribute(name) {
    return Object.prototype.hasOwnProperty.call(this.attributes, name);
  }

  addEventListener(type, callback) {
    const callbacks = this.listeners.get(type) || [];
    callbacks.push(callback);
    this.listeners.set(type, callbacks);
  }

  dispatchEvent(event) {
    const callbacks = this.listeners.get(event.type) || [];
    callbacks.forEach((callback) => callback(event));
  }

  focus() {
    this.focused = true;
  }

  closest(selector) {
    return selector === ".b26-tools-stat" ? this.card : null;
  }
}

class FakeRoot extends FakeElement {
  constructor(elements) {
    super({ "data-tools-studio": "" });
    this.elements = elements;
  }

  querySelector(selector) {
    if (selector === "[data-tools-studio]") return this;
    if (selector === '[data-station-button="find"]') return this.elements.stations[0];
    if (selector === '[data-station-button="extract"]') return this.elements.stations[1];
    if (selector === '[data-station-button="attribute"]') return this.elements.stations[2];
    if (selector === '[data-station-button="publish"]') return this.elements.stations[3];
    if (selector === "[data-station-panel]") return this.elements.panel;
    if (selector === "[data-panel-kicker]") return this.elements.panelKicker;
    if (selector === "[data-panel-title]") return this.elements.panelTitle;
    if (selector === "[data-panel-description]") return this.elements.panelDescription;
    if (selector === "[data-panel-input]") return this.elements.panelInput;
    if (selector === "[data-panel-output]") return this.elements.panelOutput;
    if (selector === "[data-panel-action]") return this.elements.panelAction;
    if (selector === "[data-factory]") return this.elements.factory;
    if (selector === "[data-factory-toggle]") return this.elements.factoryToggle;
    if (selector === "[data-factory-signal]") return this.elements.factorySignal;
    if (selector === "[data-live-stats]") return this.elements.liveStats;
    if (selector === "[data-live-stats-status]") return this.elements.liveStatus;
    if (selector === "[data-stat-generated]") return this.elements.generated;
    if (selector.startsWith('[data-stat-value="')) {
      const key = selector.slice(18, -2);
      return this.elements.stats[key];
    }
    return null;
  }

  querySelectorAll(selector) {
    if (selector === "[data-station-button]") return this.elements.stations;
    if (selector === "[data-reveal]") return this.elements.reveals;
    return [];
  }
}

class FakeIntersectionObserver {
  constructor(callback) {
    this.callback = callback;
    this.observed = new Set();
    FakeIntersectionObserver.current = this;
  }

  observe(target) {
    this.observed.add(target);
  }

  unobserve(target) {
    this.observed.delete(target);
  }

  trigger(target, isIntersecting) {
    assert.equal(this.observed.has(target), true, "test target should be observed");
    this.callback([{ target, isIntersecting }]);
  }
}

class FakeAbortController {
  constructor() {
    this.signal = { aborted: false };
    FakeAbortController.instances.push(this);
  }

  abort() {
    this.signal.aborted = true;
    this.aborted = true;
  }
}

FakeAbortController.instances = [];

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

function responseFor(payload) {
  return {
    ok: true,
    json: () => Promise.resolve(payload),
  };
}

function completePayload(values = {}, generatedAt = "2026-09-05T12:00:00Z") {
  return {
    dataset: {
      documents_indexed: values.documents_indexed ?? 10,
      distinct_sources: values.distinct_sources ?? 8,
      public_evidence_routes: values.public_evidence_routes ?? 4,
      projected_cards: values.projected_cards ?? 3,
    },
    generated_at: generatedAt,
  };
}

function makeHarness({ visibilityState = "visible", reducedMotion = false, responses = [] } = {}) {
  const panel = new FakeElement({ id: "station-panel" });
  const stations = ["find", "extract", "attribute", "publish"].map((key, index) => new FakeElement({
    id: `station-tab-${key}`,
    "data-station-button": key,
    "aria-selected": index === 0 ? "true" : "false",
    disabled: "",
  }));
  const factory = new FakeElement({ "data-factory": "", "data-factory-playing": "true", "data-factory-visible": "false" });
  const factoryToggle = new FakeElement({ "data-factory-toggle": "", hidden: "", "aria-pressed": "false" });
  const factorySignal = new FakeElement({ "data-factory-signal": "" });
  const liveStats = new FakeElement({ "data-live-stats": "" });
  const liveStatus = new FakeElement({ "data-live-stats-status": "" });
  const generated = new FakeElement({ "data-stat-generated": "" });
  const reveals = Array.from({ length: 6 }, (_, index) => new FakeElement({ "data-reveal": "", id: `reveal-${index}` }));
  const stats = {};
  ["documents_indexed", "distinct_sources", "public_evidence_routes", "projected_cards"].forEach((key) => {
    stats[key] = new FakeElement({ "data-stat-value": key });
    stats[key].card = new FakeElement();
  });
  const elements = {
    panel,
    panelKicker: new FakeElement(),
    panelTitle: new FakeElement(),
    panelDescription: new FakeElement(),
    panelInput: new FakeElement(),
    panelOutput: new FakeElement(),
    panelAction: new FakeElement(),
    stations,
    factory,
    factoryToggle,
    factorySignal,
    liveStats,
    liveStatus,
    generated,
    reveals,
    reveal: reveals[0],
    stats,
  };
  const root = new FakeRoot(elements);
  const documentListeners = new Map();
  const document = {
    readyState: "complete",
    visibilityState,
    querySelector: (selector) => (selector === "[data-tools-studio]" ? root : null),
    addEventListener(type, callback) {
      const callbacks = documentListeners.get(type) || [];
      callbacks.push(callback);
      documentListeners.set(type, callbacks);
    },
    dispatch(type) {
      (documentListeners.get(type) || []).forEach((callback) => callback());
    },
  };
  const timers = { timeouts: [], intervals: [] };
  const fetchCalls = [];
  const queue = responses.slice();
  const motionListeners = [];
  const motionQuery = {
    matches: reducedMotion,
    addEventListener(type, callback) {
      if (type === "change") motionListeners.push(callback);
    },
    setMatches(nextMatches) {
      this.matches = Boolean(nextMatches);
      motionListeners.forEach((callback) => callback({ matches: this.matches }));
    },
  };
  function fetchStub(url, options) {
    fetchCalls.push({ url, options });
    const next = queue.shift();
    if (next === undefined) return Promise.reject(new Error("unexpected fetch"));
    if (next && next.type === "pending") return next.promise;
    if (next && next.type === "error") return Promise.reject(next.error || new Error("fetch failed"));
    if (next && next.type === "response") return next.promise || Promise.resolve(next.value);
    return Promise.resolve(responseFor(next));
  }
  const context = {
    console,
    document,
    fetch: fetchStub,
    AbortController: FakeAbortController,
    IntersectionObserver: FakeIntersectionObserver,
    setTimeout,
    clearTimeout,
    Promise,
    Date,
    Number,
    String,
  };
  context.window = context;
  context.matchMedia = () => motionQuery;
  context.setTimeout = (callback, delay) => {
    const timer = { callback, delay, cleared: false };
    timers.timeouts.push(timer);
    return timer;
  };
  context.clearTimeout = (timer) => {
    if (timer) timer.cleared = true;
  };
  context.setInterval = (callback, delay) => {
    const timer = { callback, delay, cleared: false };
    timers.intervals.push(timer);
    return timer;
  };
  context.clearInterval = (timer) => {
    if (timer) timer.cleared = true;
  };
  vm.runInNewContext(SCRIPT, context, { filename: "base2026-tools-studio.js" });

  return {
    ...elements,
    document,
    fetchCalls,
    timers,
    observer: FakeIntersectionObserver.current,
    setReducedMotion(nextState) {
      motionQuery.setMatches(nextState);
    },
    triggerVisibility(nextState) {
      document.visibilityState = nextState;
      document.dispatch("visibilitychange");
    },
    runIntervals() {
      timers.intervals.filter((timer) => !timer.cleared).forEach((timer) => timer.callback());
    },
  };
}

async function flushPromises() {
  for (let index = 0; index < 6; index += 1) await Promise.resolve();
}

test("hidden document never starts stats work and aborts active work until visible", async () => {
  const pending = deferred();
  const harness = makeHarness({
    visibilityState: "hidden",
    responses: [
      { type: "pending", promise: pending.promise },
      completePayload({ documents_indexed: 1 }),
    ],
  });

  harness.observer.trigger(harness.liveStats, true);
  await flushPromises();
  assert.equal(harness.fetchCalls.length, 0);

  harness.triggerVisibility("visible");
  assert.equal(harness.fetchCalls.length, 1);
  harness.triggerVisibility("hidden");
  assert.equal(FakeAbortController.instances.at(-1).aborted, true);
  harness.runIntervals();
  assert.equal(harness.fetchCalls.length, 1, "hidden interval must not fetch");

  pending.reject(Object.assign(new Error("hidden"), { name: "AbortError" }));
  await flushPromises();
  harness.triggerVisibility("visible");
  await flushPromises();
  assert.equal(harness.fetchCalls.length, 2);
  assert.match(harness.liveStatus.textContent, /updated/);
});

test("a failed refresh is stale and retains the last complete public read", async () => {
  const harness = makeHarness({
    responses: [
      completePayload({ documents_indexed: 17, distinct_sources: 11, public_evidence_routes: 5, projected_cards: 4 }),
      { type: "error", error: new Error("temporary outage") },
    ],
  });
  harness.observer.trigger(harness.liveStats, true);
  await flushPromises();
  assert.equal(harness.stats.documents_indexed.textContent, "17");
  assert.equal(harness.stats.distinct_sources.textContent, "11");
  assert.equal(harness.stats.public_evidence_routes.textContent, "5");
  assert.equal(harness.stats.projected_cards.textContent, "4");
  assert.equal(harness.generated.textContent, "2026-09-05T12:00:00Z");

  harness.runIntervals();
  await flushPromises();
  assert.deepEqual(
    Object.fromEntries(Object.entries(harness.stats).map(([key, node]) => [key, node.textContent])),
    {
      documents_indexed: "17",
      distinct_sources: "11",
      public_evidence_routes: "5",
      projected_cards: "4",
    },
    "a failed refresh must preserve every last-good metric",
  );
  assert.equal(harness.generated.textContent, "2026-09-05T12:00:00Z");
  assert.equal(harness.liveStatus.getAttribute("data-state"), "stale");
  assert.match(harness.liveStatus.textContent, /last server read/);
});

test("missing fields remain unavailable and never become fabricated zeros", async () => {
  const harness = makeHarness({ responses: [{ dataset: {}, generated_at: "2026-09-05T12:00:00Z" }] });
  harness.observer.trigger(harness.liveStats, true);
  await flushPromises();
  Object.values(harness.stats).forEach((node) => assert.equal(node.textContent, "Unavailable"));
  assert.equal(harness.generated.textContent, "2026-09-05T12:00:00Z");
  assert.equal(harness.liveStatus.getAttribute("data-state"), "unavailable");
  assert.doesNotMatch(harness.liveStatus.textContent, /0/);
});

test("factory pause, hidden-tab and offscreen gates preserve the animation class", () => {
  const harness = makeHarness();
  harness.observer.trigger(harness.factory, true);
  assert.equal(harness.factorySignal.classList.contains("is-running"), true);
  assert.equal(harness.factorySignal.style.animationPlayState, "running");

  harness.factoryToggle.dispatchEvent({ type: "click" });
  assert.equal(harness.factorySignal.classList.contains("is-running"), true);
  assert.equal(harness.factorySignal.style.animationPlayState, "paused");
  harness.factoryToggle.dispatchEvent({ type: "click" });
  assert.equal(harness.factorySignal.classList.contains("is-running"), true);
  assert.equal(harness.factorySignal.style.animationPlayState, "running");

  harness.observer.trigger(harness.factory, false);
  assert.equal(harness.factorySignal.classList.contains("is-running"), true);
  assert.equal(harness.factorySignal.style.animationPlayState, "paused");
  harness.observer.trigger(harness.factory, true);
  assert.equal(harness.factorySignal.style.animationPlayState, "running");

  harness.triggerVisibility("hidden");
  assert.equal(harness.factorySignal.classList.contains("is-running"), true);
  assert.equal(harness.factorySignal.style.animationPlayState, "paused");
  harness.triggerVisibility("visible");
  assert.equal(harness.factorySignal.style.animationPlayState, "running");

  harness.factorySignal.dispatchEvent({ type: "animationend", animationName: "b26-tools-factory-signal" });
  assert.equal(harness.factorySignal.classList.contains("is-running"), false);
  assert.equal(harness.factoryToggle.textContent, "Replay illustration");
  harness.observer.trigger(harness.factory, false);
  harness.observer.trigger(harness.factory, true);
  assert.equal(harness.factorySignal.classList.contains("is-running"), false, "completed illustration must not auto-replay");
  harness.factoryToggle.dispatchEvent({ type: "click" });
  assert.equal(harness.factorySignal.classList.contains("is-running"), true, "one explicit replay click must restart completion");
  assert.equal(harness.factory.hasAttribute("data-factory-complete"), false);
  assert.equal(harness.factoryToggle.textContent, "Pause illustration");
  assert.equal(harness.factorySignal.style.animationPlayState, "running");
});

test("station tabs use progressive roving tab stops and keyboard selection", () => {
  const harness = makeHarness();
  assert.deepEqual(harness.stations.map((station) => station.hasAttribute("disabled")), [false, false, false, false]);
  assert.equal(harness.factoryToggle.hasAttribute("hidden"), false);
  assert.deepEqual(harness.stations.map((station) => station.getAttribute("tabindex")), ["0", "-1", "-1", "-1"]);
  const event = {
    type: "keydown",
    key: "ArrowRight",
    preventDefault() { this.prevented = true; },
  };
  harness.stations[0].dispatchEvent(event);
  assert.equal(event.prevented, true);
  assert.equal(harness.stations[1].getAttribute("aria-selected"), "true");
  assert.equal(harness.stations[1].getAttribute("tabindex"), "0");
  assert.equal(harness.stations[1].focused, true);
  assert.match(harness.panelTitle.textContent, /Extract/);

  harness.stations[3].dispatchEvent({ type: "click" });
  assert.equal(harness.panelKicker.textContent, "Use");
  assert.equal(harness.panelTitle.textContent, "Build a brief. Choose the next move.");
});

test("every observed progressive reveal target becomes visible", () => {
  const harness = makeHarness();
  assert.equal(harness.reveals.length, 6, "the workbench has six product cards");
  harness.reveals.forEach((target) => harness.observer.trigger(target, true));
  harness.reveals.forEach((target) => assert.equal(target.classList.contains("is-visible"), true));
});

test("reduced motion keeps the factory static and disables its toggle", () => {
  const harness = makeHarness({ reducedMotion: true });
  harness.observer.trigger(harness.factory, true);
  assert.equal(harness.factorySignal.classList.contains("is-running"), false);
  assert.equal(harness.factorySignal.style.animationPlayState, "paused");
  assert.equal(harness.factoryToggle.hasAttribute("disabled"), true);
  assert.equal(harness.factoryToggle.textContent, "Motion reduced");
});

test("a reduced-motion preference change updates the illustration at runtime", () => {
  const harness = makeHarness();
  harness.observer.trigger(harness.factory, true);
  assert.equal(harness.factorySignal.classList.contains("is-running"), true);

  harness.setReducedMotion(true);
  assert.equal(harness.factoryToggle.hasAttribute("disabled"), true);
  assert.equal(harness.factoryToggle.textContent, "Motion reduced");
  assert.equal(harness.factorySignal.classList.contains("is-running"), false);
  assert.equal(harness.factorySignal.style.animationPlayState, "paused");

  harness.setReducedMotion(false);
  assert.equal(harness.factoryToggle.hasAttribute("disabled"), false);
  assert.equal(harness.factoryToggle.textContent, "Pause illustration");
  assert.equal(harness.factorySignal.classList.contains("is-running"), true);
  assert.equal(harness.factorySignal.style.animationPlayState, "running");
});
