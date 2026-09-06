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
    attributes: {},
    getAttribute(key) { return this.attributes[key] || ""; },
    setAttribute(key, value) { this.attributes[key] = String(value); },
    addEventListener(type, handler) { (listeners[type] ||= []).push(handler); },
    removeEventListener(type, handler) { listeners[type] = (listeners[type] || []).filter((item) => item !== handler); },
    dispatch(type, event = {}) { (listeners[type] || []).slice().forEach((handler) => handler(event)); },
    querySelector() { return null; },
    contains() { return false; }
  };
}

function load({ gsap, conditions = { desktop: true, mobile: false, reduceMotion: false } } = {}) {
  const scene = element("scene");
  const sourceTarget = element("source");
  const excerpt = element("excerpt");
  const action = element("action");
  const line = element("line");
  const image = element("image");
  const toggle = element("toggle");
  const pause = element("pause");
  const resume = element("resume");
  const replay = element("replay");
  toggle.attributes["data-lab-motion"] = "toggle";
  pause.attributes["data-lab-motion"] = "pause";
  resume.attributes["data-lab-motion"] = "resume";
  replay.attributes["data-lab-motion"] = "replay";

  const listeners = { window: {}, document: {} };
  const document = {
    hidden: false,
    body: element("body"),
    querySelector(selector) { return selector === "[data-lab-scene]" ? scene : null; },
    querySelectorAll(selector) {
      if (selector === "[data-lab-progress]") return [];
      if (selector === "[data-lab-source]") return [sourceTarget];
      if (selector === "[data-lab-excerpt]") return [excerpt];
      if (selector === "[data-lab-action]") return [action];
      if (selector === "[data-lab-line]") return [line];
      if (selector.includes("b26-lab-scene__image")) return [image];
      if (selector === "button[data-lab-motion]") return [toggle, pause, resume, replay];
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
    gsap
  };
  vm.runInNewContext(source, { window, document, console });
  return { window, document, controls: { toggle, pause, resume, replay }, scene, sourceTarget };
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
  vm.runInNewContext(source, { window, document, console });
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
  vm.runInNewContext(source, { window, document, console });
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

test("preserves an explicit toggle pause across rebuilds and lets resume/replay clear it", () => {
  let latestMedia = null;
  const timelines = [];
  function mediaController() {
    let callback;
    let cleanup;
    return {
      add(_query, next) {
        callback = next;
        cleanup = callback({ conditions: { desktop: true, mobile: false, reduceMotion: false } });
      },
      rebuild(conditions) {
        if (typeof cleanup === "function") cleanup();
        cleanup = callback({ conditions });
      },
      revert() {
        if (typeof cleanup === "function") cleanup();
        cleanup = null;
      }
    };
  }
  const gsap = {
    registerPlugin() {},
    matchMedia() {
      latestMedia = mediaController();
      return latestMedia;
    },
    timeline(options) {
      const stats = { play: 0, pause: 0, resume: 0, restart: 0 };
      const timeline = {
        fromTo() { return timeline; },
        play() { stats.play += 1; if (options.onStart) options.onStart(); return timeline; },
        pause() { stats.pause += 1; if (options.onPause) options.onPause(); return timeline; },
        resume() { stats.resume += 1; return timeline; },
        restart() { stats.restart += 1; if (options.onStart) options.onStart(); return timeline; },
        complete() { if (options.onComplete) options.onComplete(); },
        kill() {}
      };
      stats.timeline = timeline;
      timelines.push(stats);
      return timeline;
    },
    set() {},
    saveStyles() {},
    context(callback) { callback(); return { revert() {} }; }
  };

  const loaded = load({ gsap });
  assert.equal(timelines.length, 1);
  assert.equal(timelines[0].play, 1);

  loaded.controls.toggle.dispatch("click");
  assert.equal(timelines[0].pause, 1);
  assert.equal(loaded.controls.toggle.textContent, "Resume illustration");

  loaded.window.dispatch("pagehide");
  loaded.window.dispatch("pageshow", { persisted: true });
  assert.equal(timelines.length, 2);
  assert.equal(timelines[1].play, 0);
  assert.equal(loaded.controls.toggle.textContent, "Resume illustration");

  latestMedia.rebuild({ desktop: false, mobile: true, reduceMotion: false });
  assert.equal(timelines.length, 3);
  assert.equal(timelines[2].play, 0);

  loaded.document.hidden = true;
  loaded.document.dispatch("visibilitychange");
  loaded.document.hidden = false;
  loaded.document.dispatch("visibilitychange");
  assert.equal(timelines[2].play, 0);
  assert.equal(timelines[2].resume, 0);

  loaded.controls.toggle.dispatch("click");
  assert.equal(timelines[2].play, 1);
  assert.equal(loaded.controls.toggle.textContent, "Pause illustration");

  timelines[2].timeline.complete();
  assert.equal(loaded.controls.toggle.textContent, "Replay illustration");
  loaded.controls.toggle.dispatch("click");
  assert.equal(timelines[2].restart, 1);

  latestMedia.rebuild({ desktop: true, mobile: false, reduceMotion: false });
  assert.equal(timelines.length, 4);
  assert.equal(timelines[3].play, 1);
});

test("reduced motion hides controls and does not create an autoplay timeline", () => {
  let timelineCreated = 0;
  const gsap = {
    registerPlugin() {},
    matchMedia() { return { add(_query, callback) { callback({ conditions: { desktop: true, mobile: false, reduceMotion: true } }); }, revert() {} }; },
    timeline() { timelineCreated += 1; throw new Error("timeline must not be created for reduced motion"); },
    saveStyles() {},
    context(callback) { callback(); return { revert() {} }; }
  };
  const { controls } = load({ gsap });
  assert.equal(timelineCreated, 0);
  assert.equal(controls.pause.hidden, true);
  assert.equal(controls.resume.hidden, true);
  assert.equal(controls.replay.hidden, true);
  assert.equal(controls.pause.attributes["data-lab-motion-state"], "disabled");
});

test("pagehide cleans the finite timeline and pageshow creates a fresh setup", () => {
  let timelineCreated = 0;
  const gsap = {
    registerPlugin() {},
    matchMedia() {
      let cleanup;
      return {
        add(_query, callback) { cleanup = callback({ conditions: { desktop: true, mobile: false, reduceMotion: false } }); },
        revert() { if (typeof cleanup === "function") cleanup(); }
      };
    },
    timeline(options) {
      timelineCreated += 1;
      const timeline = {
        fromTo() { return timeline; },
        play() { if (options.onStart) options.onStart(); return timeline; },
        pause() { if (options.onPause) options.onPause(); return timeline; },
        resume() { return timeline; },
        restart() { if (options.onStart) options.onStart(); return timeline; },
        kill() {}
      };
      return timeline;
    },
    set() {},
    saveStyles() {},
    context(callback) { callback(); return { revert() {} }; }
  };
  const loaded = load({ gsap });
  assert.equal(timelineCreated, 1);
  assert.equal(loaded.controls.pause.hidden, false);
  loaded.window.dispatch("pagehide");
  assert.equal(loaded.controls.pause.hidden, true);
  loaded.window.dispatch("pageshow", { persisted: true });
  assert.equal(timelineCreated, 2);
  assert.equal(loaded.controls.pause.hidden, false);
});
