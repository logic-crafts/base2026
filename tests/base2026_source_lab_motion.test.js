const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "..", "templates", "base2026-source-lab.js"), "utf8");

function element(name, { hidden = false, textContent = "", innerText = "" } = {}) {
  const listeners = {};
  const classes = new Set();
  const node = {
    name,
    hidden,
    textContent,
    innerText: innerText || textContent,
    attributes: {},
    open: false,
    tabIndex: 0,
    focused: 0,
    style: {
      removeProperty(property) { delete this[property]; }
    },
    classList: {
      add(...names) { names.forEach((value) => classes.add(value)); },
      remove(...names) { names.forEach((value) => classes.delete(value)); },
      contains(value) { return classes.has(value); }
    },
    getAttribute(key) { return Object.prototype.hasOwnProperty.call(this.attributes, key) ? this.attributes[key] : null; },
    setAttribute(key, value) { this.attributes[key] = String(value); },
    addEventListener(type, handler) { (listeners[type] ||= []).push(handler); },
    removeEventListener(type, handler) { listeners[type] = (listeners[type] || []).filter((item) => item !== handler); },
    dispatch(type, event = {}) { return (listeners[type] || []).slice().map((handler) => handler(event)); },
    querySelector() { return null; },
    querySelectorAll() { return []; },
    contains(target) { return target === this; },
    closest() { return null; },
    focus() { this.focused += 1; },
    getClientRects() { return [{ width: 100, height: 30 }]; }
  };
  return node;
}

function createMatchMedia({ reduceMotion = false, desktop = true } = {}) {
  const queries = {};
  function matchMedia(query) {
    const listeners = [];
    const media = {
      media: query,
      matches: query.includes("prefers-reduced-motion") ? reduceMotion : query.includes("min-width") ? desktop : false,
      addEventListener(type, handler) { if (type === "change") listeners.push(handler); },
      removeEventListener(type, handler) {
        if (type === "change") {
          const index = listeners.indexOf(handler);
          if (index >= 0) listeners.splice(index, 1);
        }
      },
      dispatchChange(matches) {
        this.matches = matches;
        listeners.slice().forEach((handler) => handler({ matches, media: query }));
      }
    };
    queries[query] = media;
    return media;
  }
  return { matchMedia, queries };
}

function createTimelineHarness() {
  const timelines = [];
  const transitions = [];

  function makeTimeline(options) {
    const stats = {
      calls: [],
      play: 0,
      pause: 0,
      resume: 0,
      killed: 0,
      complete: 0,
      playing: false,
      progress: 0,
      timeline: null
    };
    let duration = 0;
    const invoked = new Set();
    const timeline = {
      call(callback, args = [], at = 0) {
        const time = Number(at) || 0;
        duration = Math.max(duration, time);
        stats.calls.push({ callback, args, at: time });
        return timeline;
      },
      duration() { return duration; },
      play(value) {
        stats.play += 1;
        stats.playing = true;
        if (typeof value === "number") {
          stats.progress = duration ? Math.max(0, Math.min(1, value / duration)) : 0;
          timeline.runAt(value);
        }
        return timeline;
      },
      pause() { stats.pause += 1; stats.playing = false; return timeline; },
      resume() { stats.resume += 1; stats.playing = true; return timeline; },
      kill() { stats.killed += 1; stats.playing = false; return timeline; },
      complete() {
        stats.complete += 1;
        stats.progress = 1;
        stats.playing = false;
        if (options.onComplete) options.onComplete();
        return timeline;
      },
      runAt(time) {
        stats.progress = duration ? Math.max(0, Math.min(1, time / duration)) : 0;
        stats.calls
          .filter((entry) => entry.at <= time && !invoked.has(entry))
          .sort((left, right) => left.at - right.at)
          .forEach((entry) => { invoked.add(entry); entry.callback(...entry.args); });
        return timeline;
      },
      progress(value) {
        if (typeof value === "undefined") return stats.progress;
        stats.progress = Math.max(0, Math.min(1, Number(value) || 0));
        return timeline;
      }
    };
    stats.timeline = timeline;
    timelines.push(stats);
    return timeline;
  }

  return {
    timelines,
    transitions,
    gsap: {
      timeline: makeTimeline,
      fromTo(target, from, to) {
        const transition = { target, from, to, killed: 0, kill() { this.killed += 1; } };
        transitions.push(transition);
        return transition;
      }
    }
  };
}

function makeDetails(name) {
  const details = element(name);
  const summary = element(`${name}-summary`);
  const firstLink = element(`${name}-first-link`);
  details.querySelector = (selector) => selector === "summary" ? summary : selector === "a[href]" ? firstLink : null;
  details.contains = (target) => target === details || target === summary || target === firstLink;
  return { details, summary, firstLink };
}

function load({ navigation = false, example = true, gsapHarness = null, reduceMotion = false, desktop = true, clipboard = null, intersection = false } = {}) {
  const documentListeners = {};
  const windowListeners = {};
  const media = createMatchMedia({ reduceMotion, desktop });
  const body = element("body");
  const header = navigation ? element("header") : null;
  const research = navigation ? makeDetails("research") : null;
  const tools = navigation ? makeDetails("tools") : null;
  const opener = navigation ? element("mobile-opener", { hidden: true }) : null;
  const fallback = navigation ? element("mobile-fallback", { hidden: false }) : null;
  const closeButton = navigation ? element("mobile-close") : null;
  const sheet = navigation ? element("mobile-sheet") : null;
  const groups = navigation ? [research.details, tools.details] : [];
  let observerInstance = null;

  if (navigation) {
    sheet.querySelector = (selector) => selector === "[data-mobile-close]" ? closeButton : null;
    sheet.showModal = () => { sheet.open = true; };
    sheet.close = () => {
      if (!sheet.open) return;
      sheet.open = false;
      sheet.dispatch("close");
    };
    header.querySelector = (selector) => ({
      ".b26-mobile-sheet": sheet,
      "[data-mobile-open]": opener,
      "[data-mobile-fallback]": fallback
    })[selector] || null;
    header.querySelectorAll = (selector) => selector === ".b26-nav-group" ? groups : [];
    header.contains = (target) => [header, ...groups, research.summary, tools.summary, opener, fallback, sheet, closeButton].includes(target);
  }

  let exampleNode = null;
  let panels = [];
  let steps = [];
  let play = null;
  let status = null;
  let copy = null;
  let note = null;
  if (example) {
    exampleNode = element("worked-example");
    panels = [0, 1, 2].map((index) => element(`panel-${index}`));
    steps = ["Find", "Inspect", "Keep"].map((label, index) => element(`step-${index}`, { hidden: true, textContent: label }));
    play = element("play", { hidden: true, textContent: "Play walkthrough" });
    status = element("status", { textContent: "A real source, selected for this example." });
    copy = element("copy", { hidden: true, textContent: "Copy example note" });
    note = element("note", { innerText: "Finding: crawler activity is a signal.\nNext step: track citations separately." });
    exampleNode.querySelector = (selector) => ({
      "[data-example-play]": play,
      "[data-example-status]": status,
      "[data-example-copy]": copy,
      "[data-example-note]": note
    })[selector] || null;
    exampleNode.querySelectorAll = (selector) => selector === "[data-example-panel]" ? panels : selector === "[data-example-step]" ? steps : [];
  }

  const document = {
    hidden: false,
    body,
    querySelector(selector) {
      if (selector === ".b26-experience-header") return header;
      if (selector === "[data-worked-example]") return exampleNode;
      return null;
    },
    querySelectorAll(selector, root) {
      if (selector === ".b26-nav-group" && root === header) return groups;
      if (selector === "[data-example-panel]" && root === exampleNode) return panels;
      if (selector === "[data-example-step]" && root === exampleNode) return steps;
      return [];
    },
    addEventListener(type, handler) { (documentListeners[type] ||= []).push(handler); },
    removeEventListener(type, handler) { documentListeners[type] = (documentListeners[type] || []).filter((item) => item !== handler); },
    dispatch(type, event = {}) { return (documentListeners[type] || []).slice().map((handler) => handler(event)); }
  };
  const navigator = { clipboard: clipboard || null };
  const window = {
    document,
    navigator,
    __queryLog: [],
    matchMedia: media.matchMedia,
    addEventListener(type, handler) { (windowListeners[type] ||= []).push(handler); },
    removeEventListener(type, handler) { windowListeners[type] = (windowListeners[type] || []).filter((item) => item !== handler); },
    dispatch(type, event = {}) { return (windowListeners[type] || []).slice().map((handler) => handler(event)); },
    gsap: gsapHarness ? gsapHarness.gsap : undefined
  };
  if (intersection) {
    window.IntersectionObserver = class {
      constructor(callback) { this.callback = callback; observerInstance = this; }
      observe(target) { this.target = target; }
      disconnect() {}
    };
  }
  vm.runInNewContext(source, { window, document, navigator, console, isFinite, Promise });
  return {
    window,
    document,
    media: { reduced: media.queries["(prefers-reduced-motion: reduce)"], desktop: media.queries["(min-width: 1101px)"] },
    header,
    groups: { research, tools },
    mobile: { opener, fallback, sheet, closeButton },
    example: exampleNode,
    panels,
    steps,
    play,
    status,
    copy,
    note,
    observer: () => observerInstance,
    timelineHarness: gsapHarness
  };
}

test("keeps exactly one desktop disclosure open, restores Escape focus, and closes on outside interaction", () => {
  const loaded = load({ navigation: true, example: false });
  const { research, tools } = loaded.groups;
  research.details.open = true;
  research.details.dispatch("toggle");
  assert.equal(research.details.open, true);
  assert.equal(research.summary.attributes["aria-expanded"], "true");

  tools.details.open = true;
  tools.details.dispatch("toggle");
  assert.equal(research.details.open, false);
  assert.equal(tools.details.open, true);

  let prevented = false;
  tools.details.dispatch("keydown", { key: "Escape", preventDefault() { prevented = true; } });
  assert.equal(prevented, true);
  assert.equal(tools.details.open, false);
  assert.equal(tools.summary.focused, 1);
  assert.equal(tools.summary.attributes["aria-expanded"], "false");

  research.details.open = true;
  research.details.dispatch("toggle");
  loaded.document.dispatch("pointerdown", { target: element("outside-pointer") });
  assert.equal(research.details.open, false);

  tools.details.open = true;
  tools.details.dispatch("toggle");
  loaded.document.dispatch("focusin", { target: element("outside-focus") });
  assert.equal(tools.details.open, false);
});

test("opens and closes the native mobile dialog, clears scroll lock, restores opener focus, and closes on desktop resize", () => {
  const loaded = load({ navigation: true, example: false, desktop: false });
  const { opener, fallback, sheet, closeButton } = loaded.mobile;
  assert.equal(opener.hidden, false);
  assert.equal(fallback.hidden, true);

  opener.dispatch("click");
  assert.equal(sheet.open, true);
  assert.equal(loaded.document.body.classList.contains("b26-navigation-open"), true);
  assert.equal(opener.attributes["aria-expanded"], "true");

  closeButton.dispatch("click");
  assert.equal(sheet.open, false);
  assert.equal(loaded.document.body.classList.contains("b26-navigation-open"), false);
  assert.equal(opener.attributes["aria-expanded"], "false");
  assert.equal(opener.focused, 1);

  opener.dispatch("click");
  loaded.mobile.sheet.dispatch("click", { target: loaded.mobile.sheet });
  assert.equal(sheet.open, false);
  assert.equal(loaded.document.body.classList.contains("b26-navigation-open"), false);

  opener.dispatch("click");
  loaded.media.desktop.dispatchChange(true);
  assert.equal(sheet.open, false);
  assert.equal(loaded.document.body.classList.contains("b26-navigation-open"), false);
  assert.equal(opener.focused, 3);
});

test("keyboard entry reaches the first menu destination and moving focus to another header control dismisses it", () => {
  const loaded = load({ navigation: true, example: false });
  const { research } = loaded.groups;
  let prevented = false;
  research.details.dispatch("keydown", { key: "ArrowDown", target: research.summary, preventDefault() { prevented = true; } });
  assert.equal(prevented, true);
  assert.equal(research.details.open, true);
  assert.equal(research.firstLink.focused, 1);
  loaded.document.dispatch("focusin", { target: research.firstLink });
  assert.equal(research.details.open, true);
  loaded.document.dispatch("focusin", { target: loaded.mobile.opener });
  assert.equal(research.details.open, false);
  assert.equal(research.summary.attributes["aria-expanded"], "false");
});

test("desktop disclosures close when the layout changes or the document leaves", () => {
  const loaded = load({ navigation: true, example: false });
  const { research } = loaded.groups;
  research.details.open = true;
  loaded.media.desktop.dispatchChange(false);
  assert.equal(research.details.open, false);
  research.details.open = true;
  loaded.window.dispatch("pagehide");
  assert.equal(research.details.open, false);
});

test("native cancel and page navigation release the mobile scroll lock and allow a clean reopen", () => {
  const loaded = load({ navigation: true, example: false, desktop: false });
  const { opener, sheet } = loaded.mobile;
  opener.dispatch("click");
  let prevented = false;
  sheet.dispatch("cancel", { preventDefault() { prevented = true; } });
  assert.equal(prevented, true);
  assert.equal(sheet.open, false);
  assert.equal(loaded.document.body.classList.contains("b26-navigation-open"), false);
  opener.dispatch("click");
  assert.equal(sheet.open, true);
  loaded.window.dispatch("pagehide");
  assert.equal(sheet.open, false);
  assert.equal(loaded.document.body.classList.contains("b26-navigation-open"), false);
});

test("keeps the worked example manual-first when GSAP is unavailable", () => {
  const loaded = load({ gsapHarness: null });
  assert.equal(loaded.play.hidden, true);
  assert.equal(loaded.steps.every((step) => step.hidden === false), true);
  loaded.steps[1].dispatch("click");
  assert.equal(loaded.panels[0].hidden, true);
  assert.equal(loaded.panels[1].hidden, false);
  assert.match(loaded.status.textContent, /^Inspect:/);
});

test("manual example steps cancel autoplay and retain the selected panel", () => {
  const harness = createTimelineHarness();
  const loaded = load({ gsapHarness: harness });
  loaded.play.dispatch("click");
  assert.equal(harness.timelines.length, 1);
  assert.equal(harness.timelines[0].playing, true);
  assert.equal(loaded.play.textContent, "Pause walkthrough");

  loaded.steps[1].dispatch("click");
  assert.equal(harness.timelines[0].killed, 1);
  assert.equal(loaded.panels[0].hidden, true);
  assert.equal(loaded.panels[1].hidden, false);
  assert.match(loaded.status.textContent, /^Inspect:/);
  assert.equal(loaded.play.textContent, "Play walkthrough");
});

test("plays a finite walkthrough, supports pause/resume, and creates a fresh replay", () => {
  const harness = createTimelineHarness();
  const loaded = load({ gsapHarness: harness });
  loaded.play.dispatch("click");
  const first = harness.timelines[0];
  assert.equal(first.timeline.duration(), 9.6);
  assert.equal(first.play, 1);
  first.timeline.runAt(3.2);
  assert.match(loaded.status.textContent, /^Inspect:/);
  loaded.play.dispatch("click");
  assert.equal(first.pause, 1);
  assert.equal(loaded.play.textContent, "Resume walkthrough");
  loaded.play.dispatch("click");
  assert.equal(first.resume, 1);
  assert.equal(loaded.play.textContent, "Pause walkthrough");
  first.timeline.complete();
  assert.equal(loaded.play.textContent, "Replay walkthrough");
  loaded.play.dispatch("click");
  assert.equal(harness.timelines.length, 2);
  assert.equal(harness.timelines[1].play, 1);
  assert.equal(loaded.play.textContent, "Pause walkthrough");
});

test("pauses hidden or offscreen playback and resumes only environmental pauses", () => {
  const harness = createTimelineHarness();
  const loaded = load({ gsapHarness: harness, intersection: true });
  loaded.play.dispatch("click");
  const timeline = harness.timelines[0];

  loaded.document.hidden = true;
  loaded.document.dispatch("visibilitychange");
  assert.equal(timeline.pause, 1);
  assert.equal(loaded.play.textContent, "Resume walkthrough");
  loaded.document.hidden = false;
  loaded.document.dispatch("visibilitychange");
  assert.equal(timeline.resume, 1);
  assert.equal(loaded.play.textContent, "Pause walkthrough");

  loaded.observer().callback([{ isIntersecting: false }]);
  assert.equal(timeline.pause, 2);
  loaded.observer().callback([{ isIntersecting: true }]);
  assert.equal(timeline.resume, 2);
});

test("does not auto-resume an explicit manual pause after visibility changes", () => {
  const harness = createTimelineHarness();
  const loaded = load({ gsapHarness: harness });
  loaded.play.dispatch("click");
  const timeline = harness.timelines[0];
  loaded.play.dispatch("click");
  assert.equal(timeline.pause, 1);
  loaded.document.hidden = true;
  loaded.document.dispatch("visibilitychange");
  loaded.document.hidden = false;
  loaded.document.dispatch("visibilitychange");
  assert.equal(timeline.resume, 0);
  assert.equal(loaded.play.textContent, "Resume walkthrough");
});

test("reduced motion disables autoplay while manual steps remain usable", () => {
  const harness = createTimelineHarness();
  const loaded = load({ gsapHarness: harness, reduceMotion: true });
  assert.equal(harness.timelines.length, 0);
  assert.equal(loaded.play.hidden, true);
  loaded.steps[2].dispatch("click");
  assert.equal(loaded.panels[2].hidden, false);
  assert.equal(loaded.panels[0].hidden, true);
  assert.match(loaded.status.textContent, /^Keep:/);
  loaded.media.reduced.dispatchChange(false);
  assert.equal(loaded.play.hidden, false);
});

test("reports clipboard success only after the write resolves and does not log a query", async () => {
  let resolveWrite;
  const writes = [];
  const clipboard = {
    writeText(value) {
      writes.push(value);
      return new Promise((resolve) => { resolveWrite = resolve; });
    }
  };
  const harness = createTimelineHarness();
  const loaded = load({ gsapHarness: harness, clipboard });
  const [pending] = loaded.copy.dispatch("click");
  assert.equal(loaded.status.textContent, "Find: a real source, chosen for this example.");
  assert.equal(loaded.copy.textContent, "Copy example note");
  assert.deepEqual(loaded.window.__queryLog, []);
  assert.equal(writes.length, 1);
  assert.equal(writes[0], loaded.note.innerText.trim());

  resolveWrite();
  await pending;
  assert.equal(loaded.status.textContent, "Example note copied. It has not been saved to an account.");
  assert.equal(loaded.copy.textContent, "Copied");
  assert.deepEqual(loaded.window.__queryLog, []);
});

test("reports clipboard fallback after a rejected write", async () => {
  const loaded = load({
    clipboard: { writeText() { return Promise.reject(new Error("denied")); } }
  });
  const [pending] = loaded.copy.dispatch("click");
  await pending;
  assert.equal(loaded.status.textContent, "Copy is unavailable here. Select and copy the note below.");
  assert.equal(loaded.note.tabIndex, -1);
  assert.equal(loaded.note.focused, 1);
});
