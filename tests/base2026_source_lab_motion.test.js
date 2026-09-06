const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "..", "templates", "base2026-source-lab.js"), "utf8");

function element(name) {
  const listeners = {};
  return {
    name,
    hidden: false,
    textContent: "",
    attributes: {},
    open: false,
    getAttribute(key) { return this.attributes[key] || ""; },
    setAttribute(key, value) { this.attributes[key] = String(value); },
    addEventListener(type, handler) { (listeners[type] ||= []).push(handler); },
    removeEventListener(type, handler) { listeners[type] = (listeners[type] || []).filter((item) => item !== handler); },
    dispatch(type, event = {}) { (listeners[type] || []).slice().forEach((handler) => handler(event)); },
    querySelector() { return null; },
    querySelectorAll() { return []; },
    contains(target) { return target === this; }
  };
}

function createGsapHarness(initialConditions, options = {}) {
  const timelines = [];
  const entries = [];
  let latestMedia = null;

  function timeline(optionsForTimeline) {
    let progress = 0;
    let total = 0;
    const stats = {
      play: 0,
      pause: 0,
      resume: 0,
      restart: 0,
      killed: 0,
      steps: [],
      timeline: null
    };
    const fake = {
      fromTo(target, from, to, at = 0) {
        const count = Array.isArray(target) ? target.length : 1;
        const duration = Number(to.duration) || 0;
        const stagger = Number(to.stagger) || 0;
        total = Math.max(total, Number(at) + duration + Math.max(0, count - 1) * stagger);
        stats.steps.push({ type: "fromTo", target, from, to, at: Number(at) });
        return fake;
      },
      to(target, vars, at = 0) {
        const count = Array.isArray(target) ? target.length : 1;
        const duration = Number(vars.duration) || 0;
        const stagger = Number(vars.stagger) || 0;
        total = Math.max(total, Number(at) + duration + Math.max(0, count - 1) * stagger);
        stats.steps.push({ type: "to", target, vars, at: Number(at) });
        return fake;
      },
      progress(value, suppressEvents) {
        if (typeof value === "undefined") return progress;
        progress = Math.max(0, Math.min(1, Number(value) || 0));
        if (!suppressEvents && optionsForTimeline.onUpdate) optionsForTimeline.onUpdate();
        return fake;
      },
      duration() { return total; },
      play(value) {
        stats.play += 1;
        if (typeof value === "number") progress = Math.max(0, Math.min(1, value / (total || 1)));
        if (optionsForTimeline.onStart) optionsForTimeline.onStart();
        return fake;
      },
      pause() {
        stats.pause += 1;
        if (optionsForTimeline.onPause) optionsForTimeline.onPause();
        return fake;
      },
      resume() {
        stats.resume += 1;
        return fake;
      },
      restart() {
        stats.restart += 1;
        progress = 0;
        if (optionsForTimeline.onStart) optionsForTimeline.onStart();
        return fake;
      },
      complete() {
        progress = 1;
        if (optionsForTimeline.onComplete) optionsForTimeline.onComplete();
      },
      kill() { stats.killed += 1; }
    };
    stats.timeline = fake;
    timelines.push(stats);
    return fake;
  }

  function mediaController() {
    let callback;
    let cleanup;
    const controller = {
      add(_query, next) {
        callback = next;
        cleanup = callback({ conditions: initialConditions });
      },
      rebuild(conditions) {
        // Real GSAP reverts its animations before calling custom cleanup.
        // An emptied timeline reports progress 1; callbacks are suppressed.
        if (options.revertBeforeCleanup && timelines.length) timelines.at(-1).timeline.progress(1, true);
        if (typeof cleanup === "function") cleanup();
        cleanup = callback({ conditions });
      },
      revert() {
        if (typeof cleanup === "function") cleanup();
        cleanup = null;
      }
    };
    latestMedia = controller;
    return controller;
  }

  const gsap = {
    registerPlugin() {},
    matchMedia: mediaController,
    timeline,
    set() {},
    saveStyles() {},
    fromTo(target, from, to) { entries.push({ target, from, to }); return { kill() {} }; },
    context(callback) { callback(); return { revert() {} }; }
  };
  return { gsap, timelines, entries, get media() { return latestMedia; }, options };
}

function load({ conditions = { desktop: true, mobile: false, reduceMotion: false }, intersection = false, gsapHarness } = {}) {
  const scene = element("scene");
  const sourceGroup = element("source-group");
  const sourceCards = [element("source-one"), element("source-two"), element("source-three")];
  const lens = element("lens");
  const excerpt = element("excerpt");
  const excerptHighlight = element("excerpt-highlight");
  const brief = element("brief");
  const briefHeading = element("brief-heading");
  const briefSource = element("brief-source");
  const briefNext = element("brief-next");
  const track = element("track");
  const toggle = element("toggle");
  const status = element("status");
  toggle.attributes["data-lab-motion"] = "toggle";
  const toolGroup = element("tool-group");
  const sequenceGroup = element("sequence-group");
  const toolEntries = [element("tool-one"), element("tool-two")];
  const sequenceEntries = [element("sequence-one"), element("sequence-two"), element("sequence-three")];
  const listeners = { window: {}, document: {} };
  let observerInstance = null;

  const groups = new Map([[toolGroup, toolEntries], [sequenceGroup, sequenceEntries]]);
  toolGroup.querySelectorAll = (selector) => selector === "[data-lab-entry]" ? toolEntries : [];
  sequenceGroup.querySelectorAll = (selector) => selector === "[data-lab-entry]" ? sequenceEntries : [];
  const document = {
    hidden: false,
    body: element("body"),
    querySelector(selector) {
      return ({
        "[data-lab-scene]": scene,
        "[data-lab-source]": sourceGroup,
        "[data-lab-lens]": lens,
        "[data-lab-excerpt]": excerpt,
        "[data-lab-excerpt-highlight]": excerptHighlight,
        "[data-lab-action]": brief,
        "[data-lab-brief-heading]": briefHeading,
        "[data-lab-brief-source]": briefSource,
        "[data-lab-brief-next]": briefNext,
        "[data-lab-motion-status]": status
      })[selector] || null;
    },
    querySelectorAll(selector, root) {
      if (selector === ".b26-nav-group" || selector === ".b26-mobile-nav") return [];
      if (selector === "[data-lab-entry-group]") return [toolGroup, sequenceGroup];
      if (selector === "[data-lab-source-card]") return sourceCards;
      if (selector === "[data-lab-line]") return [track];
      if (selector === "button[data-lab-motion='toggle']") return [toggle];
      if (selector === "[data-lab-entry]" && root) return groups.get(root) || [];
      return [];
    },
    addEventListener(type, handler) { (listeners.document[type] ||= []).push(handler); },
    removeEventListener(type, handler) { listeners.document[type] = (listeners.document[type] || []).filter((item) => item !== handler); },
    dispatch(type, event = {}) { (listeners.document[type] || []).slice().forEach((handler) => handler(event)); }
  };

  const window = {
    document,
    addEventListener(type, handler) { (listeners.window[type] ||= []).push(handler); },
    removeEventListener(type, handler) { listeners.window[type] = (listeners.window[type] || []).filter((item) => item !== handler); },
    dispatch(type, event = {}) { (listeners.window[type] || []).slice().forEach((handler) => handler(event)); },
    ScrollTrigger: {},
    gsap: gsapHarness ? gsapHarness.gsap : undefined
  };
  if (intersection) {
    window.IntersectionObserver = class {
      constructor(callback) { this.callback = callback; observerInstance = this; }
      observe() {}
      disconnect() {}
    };
  }
  vm.runInNewContext(source, { window, document, console, isFinite });
  return {
    window,
    document,
    scene,
    toggle,
    status,
    observer: () => observerInstance,
    controls: { toggle },
    sourceCards,
    groups: { toolGroup, sequenceGroup },
    entries: { toolEntries, sequenceEntries }
  };
}

test("does not initialize source motion when GSAP is unavailable", () => {
  const control = element("control");
  let motionQueried = false;
  const document = {
    querySelector() { motionQueried = true; return control; },
    querySelectorAll(selector) {
      if (selector !== ".b26-nav-group" && selector !== ".b26-mobile-nav") motionQueried = true;
      return [];
    }
  };
  const window = { document };
  vm.runInNewContext(source, { window, document, console, isFinite });
  assert.equal(motionQueried, false);
  assert.equal(control.hidden, false);
});

function navigationOnlyLoad() {
  const listeners = { document: {} };
  function menu(name) {
    const details = element(name);
    const summary = element(`${name}-summary`);
    details.open = false;
    summary.focused = 0;
    summary.focus = () => { summary.focused += 1; };
    details.querySelector = (selector) => selector === "summary" ? summary : null;
    details.contains = (target) => target === details || target === summary;
    return { details, summary };
  }

  const research = menu("research");
  const build = menu("build");
  const mobile = menu("mobile");
  const outside = element("outside");
  const document = {
    querySelectorAll(selector) {
      if (selector === ".b26-nav-group") return [research.details, build.details];
      if (selector === ".b26-mobile-nav") return [mobile.details];
      return [];
    },
    addEventListener(type, handler) { (listeners.document[type] ||= []).push(handler); },
    removeEventListener(type, handler) { listeners.document[type] = (listeners.document[type] || []).filter((item) => item !== handler); },
    dispatch(type, event = {}) { (listeners.document[type] || []).slice().forEach((handler) => handler(event)); }
  };
  const window = { document };
  vm.runInNewContext(source, { window, document, console, isFinite });
  return { document, research, build, mobile, outside };
}

test("keeps desktop and mobile details navigation usable without GSAP", () => {
  const loaded = navigationOnlyLoad();
  loaded.research.details.open = true;
  loaded.research.details.dispatch("toggle");
  loaded.build.details.open = true;
  loaded.build.details.dispatch("toggle");
  assert.equal(loaded.research.details.open, false);
  assert.equal(loaded.build.details.open, true);

  let prevented = false;
  loaded.build.details.dispatch("keydown", {
    key: "Escape",
    preventDefault() { prevented = true; }
  });
  assert.equal(prevented, true);
  assert.equal(loaded.build.details.open, false);
  assert.equal(loaded.build.summary.focused, 1);

  loaded.mobile.details.open = true;
  loaded.mobile.details.dispatch("keydown", {
    keyCode: 27,
    preventDefault() {}
  });
  assert.equal(loaded.mobile.details.open, false);
  assert.equal(loaded.mobile.summary.focused, 1);

  loaded.research.details.open = true;
  loaded.mobile.details.open = true;
  loaded.document.dispatch("click", { target: loaded.outside });
  assert.equal(loaded.research.details.open, false);
  assert.equal(loaded.mobile.details.open, false);
});

test("builds one finite 7.8 second source-to-brief storyboard with physical objects", () => {
  const harness = createGsapHarness({ desktop: true, mobile: false, reduceMotion: false });
  const loaded = load({ gsapHarness: harness });
  assert.equal(harness.timelines.length, 1);
  const timeline = harness.timelines[0];
  assert.equal(timeline.timeline.duration(), 7.8);
  assert.equal(loaded.toggle.hidden, false);
  assert.equal(loaded.toggle.textContent, "Pause illustration");
  assert.ok(timeline.steps.some((step) => step.type === "to" && Array.isArray(step.target) && step.target.length === 3 && step.at === 1.1));
  assert.ok(timeline.steps.some((step) => step.target && step.target.name === "excerpt" && step.at >= 3.2 && step.at < 3.5));
  assert.ok(timeline.steps.some((step) => step.target && step.target.name === "brief" && step.at === 5.1));
  assert.ok(harness.entries.length >= 2, "lower groups receive bounded one-time entry motion");
  assert.match(loaded.status.textContent, /Playing illustrative workflow/);
});

test("preserves progress and explicit pause across responsive rebuilds, with replay", () => {
  const harness = createGsapHarness({ desktop: true, mobile: false, reduceMotion: false }, { revertBeforeCleanup: true });
  const loaded = load({ gsapHarness: harness });
  const first = harness.timelines[0];
  first.timeline.progress(0.42);
  loaded.toggle.dispatch("click");
  assert.equal(first.pause, 1);
  assert.equal(loaded.toggle.textContent, "Resume illustration");
  harness.media.rebuild({ desktop: false, mobile: true, reduceMotion: false });
  assert.equal(harness.timelines.length, 2);
  assert.equal(harness.timelines[1].timeline.progress(), 0.42);
  assert.equal(harness.timelines[1].play, 0);
  loaded.toggle.dispatch("click");
  assert.equal(harness.timelines[1].resume, 1);
  assert.equal(loaded.toggle.textContent, "Pause illustration");
  harness.timelines[1].timeline.complete();
  assert.equal(loaded.toggle.textContent, "Replay illustration");
  loaded.toggle.dispatch("click");
  assert.equal(harness.timelines[1].restart, 1);
});

test("pauses offscreen and hidden-tab playback without taking over scroll", () => {
  const harness = createGsapHarness({ desktop: true, mobile: false, reduceMotion: false });
  const loaded = load({ gsapHarness: harness, intersection: true });
  const timeline = harness.timelines[0];
  assert.equal(timeline.play, 0, "offscreen setup waits for intersection");
  loaded.observer().callback([{ isIntersecting: true, intersectionRatio: 1 }]);
  assert.equal(timeline.play, 1);
  loaded.document.hidden = true;
  loaded.document.dispatch("visibilitychange");
  assert.equal(timeline.pause, 1);
  loaded.document.hidden = false;
  loaded.document.dispatch("visibilitychange");
  assert.equal(timeline.resume, 1);
});

test("reduced motion hides the replay control and keeps a static status", () => {
  const harness = createGsapHarness({ desktop: true, mobile: false, reduceMotion: true });
  const loaded = load({ gsapHarness: harness });
  assert.equal(harness.timelines.length, 0);
  assert.equal(loaded.toggle.hidden, true);
  assert.equal(loaded.toggle.attributes["data-lab-motion-state"], "disabled");
  assert.match(loaded.status.textContent, /Reduced motion/);
});

test("pagehide cleans the finite timeline and pageshow restores a fresh setup", () => {
  const harness = createGsapHarness({ desktop: true, mobile: false, reduceMotion: false });
  const loaded = load({ gsapHarness: harness });
  harness.timelines[0].timeline.progress(0.35);
  loaded.window.dispatch("pagehide");
  assert.equal(loaded.toggle.hidden, true);
  loaded.window.dispatch("pageshow", { persisted: true });
  assert.equal(harness.timelines.length, 2);
  assert.equal(harness.timelines[1].timeline.progress(), 0.35);
  assert.equal(loaded.toggle.hidden, false);
});
