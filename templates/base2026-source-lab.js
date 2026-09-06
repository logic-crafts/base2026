(function (window, document) {
  "use strict";

  function queryAll(selector, root) {
    var scope = root || document;
    if (!scope || typeof scope.querySelectorAll !== "function") return [];
    return Array.prototype.slice.call(scope.querySelectorAll(selector));
  }

  function addListener(target, type, handler, listeners) {
    if (!target || typeof target.addEventListener !== "function") return;
    target.addEventListener(type, handler);
    listeners.push(function () {
      target.removeEventListener(type, handler);
    });
  }

  function setupNavigation() {
    var groups = queryAll(".b26-nav-group");
    var mobileMenus = queryAll(".b26-mobile-nav");
    var menus = groups.concat(mobileMenus);
    if (!menus.length) return;

    var firstOpenGroup = null;
    groups.forEach(function (group) {
      if (!group || !group.open) return;
      if (firstOpenGroup) group.open = false;
      else firstOpenGroup = group;
    });

    var listeners = [];

    function summaryFor(menu) {
      return menu && typeof menu.querySelector === "function" ? menu.querySelector("summary") : null;
    }

    function close(menu, restoreFocus) {
      if (!menu || !menu.open) return;
      menu.open = false;
      if (restoreFocus) {
        var summary = summaryFor(menu);
        if (summary && typeof summary.focus === "function") summary.focus();
      }
    }

    function closeOtherGroups(openGroup) {
      groups.forEach(function (group) {
        if (group !== openGroup) close(group, false);
      });
    }

    groups.forEach(function (group) {
      var summary = summaryFor(group);
      if (summary) {
        addListener(summary, "click", function () {
          closeOtherGroups(group);
        }, listeners);
      }
      addListener(group, "toggle", function () {
        if (group.open) closeOtherGroups(group);
      }, listeners);
      addListener(group, "keydown", function (event) {
        if (!event || (event.key !== "Escape" && event.keyCode !== 27)) return;
        if (typeof event.preventDefault === "function") event.preventDefault();
        close(group, true);
      }, listeners);
    });

    mobileMenus.forEach(function (menu) {
      addListener(menu, "keydown", function (event) {
        if (!event || (event.key !== "Escape" && event.keyCode !== 27)) return;
        if (typeof event.preventDefault === "function") event.preventDefault();
        close(menu, true);
      }, listeners);
    });

    addListener(document, "click", function (event) {
      var target = event && event.target;
      menus.forEach(function (menu) {
        if (!menu || !menu.open) return;
        var inside = target && typeof menu.contains === "function" && menu.contains(target);
        if (!inside) close(menu, false);
      });
    }, listeners);

    return {
      cleanup: function () {
        listeners.splice(0).forEach(function (remove) { remove(); });
      }
    };
  }

  setupNavigation();

  // The source engine is progressive enhancement. Navigation and the static
  // source-to-brief composition remain useful when the local GSAP assets are
  // unavailable.
  if (!window || !document || !window.gsap || !window.ScrollTrigger) return;

  var gsap = window.gsap;
  var ScrollTrigger = window.ScrollTrigger;
  if (typeof gsap.matchMedia !== "function" || typeof gsap.timeline !== "function" || typeof gsap.registerPlugin !== "function") return;

  try {
    gsap.registerPlugin(ScrollTrigger);
  } catch (_error) {
    return;
  }

  var runtime = null;
  var lifecycleBound = false;
  var userPaused = false;
  var resumeSnapshot = {
    progress: 0,
    started: false,
    complete: false,
    manualPaused: false
  };

  function clampProgress(value) {
    var numeric = Number(value);
    if (!isFinite(numeric)) return 0;
    return Math.max(0, Math.min(1, numeric));
  }

  function unique(elements) {
    return elements.filter(function (element, index) {
      return element && elements.indexOf(element) === index;
    });
  }

  function setStatus(element, value) {
    if (element) element.textContent = value;
  }

  function readTimelineProgress(timeline, fallback) {
    if (timeline && typeof timeline.progress === "function") {
      try {
        var current = timeline.progress();
        if (typeof current === "number") return clampProgress(current);
      } catch (_error) {
        // A reduced test double may expose a setter only.
      }
    }
    return clampProgress(fallback);
  }

  function writeTimelineProgress(timeline, value) {
    if (!timeline) return;
    var progress = clampProgress(value);
    if (typeof timeline.progress === "function") {
      try {
        timeline.progress(progress, true);
        return;
      } catch (_error) {
        // Fall through to seek for minimal GSAP-compatible test doubles.
      }
    }
    if (progress > 0 && typeof timeline.seek === "function" && typeof timeline.duration === "function") {
      timeline.seek(timeline.duration() * progress, true);
    }
  }

  function motionStateText(state) {
    if (state.reduced) return "Reduced motion: static composition.";
    if (state.complete) return "Illustration complete.";
    if (state.manualPaused) return "Paused. Resume when ready.";
    if (state.hidden) return "Paused while the tab is hidden.";
    if (state.offscreen) return "Paused while the illustration is off screen.";
    if (!state.started) return "Illustration ready.";
    return "Playing illustrative workflow once.";
  }

  function setup() {
    cleanup();

    var scene = document.querySelector("[data-lab-scene]");
    var entryGroups = queryAll("[data-lab-entry-group]");
    var sourceCards = queryAll("[data-lab-source-card]");
    var sourceGroup = document.querySelector("[data-lab-source]");
    var lens = document.querySelector("[data-lab-lens]");
    var excerpt = document.querySelector("[data-lab-excerpt]");
    var excerptHighlight = document.querySelector("[data-lab-excerpt-highlight]");
    var brief = document.querySelector("[data-lab-action]");
    var briefHeading = document.querySelector("[data-lab-brief-heading]");
    var briefSource = document.querySelector("[data-lab-brief-source]");
    var briefNext = document.querySelector("[data-lab-brief-next]");
    var track = queryAll("[data-lab-line]");
    var controls = queryAll("button[data-lab-motion='toggle']");
    var status = document.querySelector("[data-lab-motion-status]");

    if (!scene && !entryGroups.length) return;

    var state = {
      timeline: null,
      started: Boolean(resumeSnapshot.started || resumeSnapshot.progress > 0),
      complete: Boolean(resumeSnapshot.complete || resumeSnapshot.progress >= 0.999),
      progress: clampProgress(resumeSnapshot.progress),
      manualPaused: Boolean(userPaused || resumeSnapshot.manualPaused),
      environmentPaused: false,
      hidden: Boolean(document.hidden),
      offscreen: false,
      reduced: false
    };
    var listeners = [];
    var observer = null;
    var media = null;
    var disposed = false;

    function captureState(afterMediaRevert) {
      // matchMedia runs custom cleanup AFTER reverting its animations. That
      // emptied timeline can report progress() === 1 even if it was paused
      // halfway through. Keep the last live onUpdate value during cleanup.
      var progress = afterMediaRevert ? clampProgress(state.progress) : readTimelineProgress(state.timeline, state.progress);
      state.progress = progress;
      resumeSnapshot = {
        progress: progress,
        started: Boolean(state.started || progress > 0),
        complete: progress >= 0.999,
        manualPaused: Boolean(state.manualPaused || userPaused)
      };
    }

    function syncControls() {
      var visible = Boolean(state.timeline && !state.reduced && controls.length);
      var paused = state.manualPaused || state.environmentPaused || state.hidden || state.offscreen;
      var label = state.complete ? "Replay illustration" : paused ? "Resume illustration" : "Pause illustration";
      controls.forEach(function (button) {
        button.hidden = !visible;
        button.setAttribute("aria-hidden", visible ? "false" : "true");
        button.setAttribute("data-lab-motion-state", state.reduced ? "disabled" : state.complete ? "complete" : paused ? "paused" : state.started ? "running" : "ready");
        button.textContent = label;
        button.setAttribute("aria-label", label + " once");
      });
      setStatus(status, motionStateText(state));
    }

    function maybeResume() {
      var timeline = state.timeline;
      if (!timeline || state.reduced || state.manualPaused || state.hidden || state.offscreen || state.complete) {
        syncControls();
        return;
      }
      if (!state.started) {
        state.started = true;
        state.environmentPaused = false;
        if (typeof timeline.play === "function") timeline.play(0);
      } else if (state.environmentPaused) {
        state.environmentPaused = false;
        if (typeof timeline.resume === "function") timeline.resume();
        else if (typeof timeline.play === "function") timeline.play();
      } else if (typeof timeline.play === "function") {
        timeline.play();
      }
      syncControls();
    }

    function pauseForEnvironment() {
      var timeline = state.timeline;
      if (!timeline || state.reduced || state.complete) {
        syncControls();
        return;
      }
      if (state.hidden || state.offscreen) {
        if (state.started && !state.manualPaused) {
          state.environmentPaused = true;
          captureState();
          if (typeof timeline.pause === "function") timeline.pause();
        }
      } else if (state.environmentPaused && !state.manualPaused) {
        maybeResume();
        return;
      }
      syncControls();
    }

    controls.forEach(function (button) {
      button.hidden = true;
      button.setAttribute("aria-hidden", "true");
      addListener(button, "click", function () {
        var timeline = state.timeline;
        if (!timeline || state.reduced) return;

        if (state.complete) {
          userPaused = false;
          state.manualPaused = false;
          state.environmentPaused = false;
          state.started = true;
          state.complete = false;
          state.progress = 0;
          if (typeof timeline.restart === "function") timeline.restart();
          else if (typeof timeline.play === "function") timeline.play(0);
        } else if (state.manualPaused || state.environmentPaused || state.hidden || state.offscreen) {
          userPaused = false;
          state.manualPaused = false;
          if (!state.hidden && !state.offscreen) {
            state.environmentPaused = false;
            if (state.started && typeof timeline.resume === "function") timeline.resume();
            else if (typeof timeline.play === "function") timeline.play(state.progress > 0 ? undefined : 0);
          }
        } else if (state.started) {
          userPaused = true;
          state.manualPaused = true;
          state.environmentPaused = false;
          captureState();
          if (typeof timeline.pause === "function") timeline.pause();
        } else {
          maybeResume();
        }
        syncControls();
      }, listeners);
    });

    addListener(document, "visibilitychange", function () {
      state.hidden = Boolean(document.hidden);
      pauseForEnvironment();
    }, listeners);

    if (scene && typeof window.IntersectionObserver === "function") {
      state.offscreen = true;
      observer = new window.IntersectionObserver(function (entries) {
        if (!entries || !entries.length) return;
        var entry = entries[0];
        state.offscreen = !(entry.isIntersecting || entry.intersectionRatio > 0);
        if (state.offscreen) pauseForEnvironment();
        else maybeResume();
      }, { threshold: 0.05 });
      observer.observe(scene);
    }

    media = gsap.matchMedia();
    try {
      media.add({
        desktop: "(min-width: 721px)",
        mobile: "(max-width: 720px)",
        reduceMotion: "(prefers-reduced-motion: reduce)"
      }, function (context) {
        var conditions = context.conditions || {};
        var reduced = Boolean(conditions.reduceMotion);
        state.reduced = reduced;
        state.timeline = null;
        state.environmentPaused = false;
        syncControls();

        if (reduced) {
          return function () {
            captureState(true);
            state.timeline = null;
            state.reduced = true;
            syncControls();
          };
        }

        var travelX = conditions.desktop ? 190 : 82;
        var saveTargets = unique(sourceCards.concat([sourceGroup, lens, excerpt, excerptHighlight, brief, briefHeading, briefSource, briefNext], track));
        if (typeof gsap.saveStyles === "function" && saveTargets.length) gsap.saveStyles(saveTargets);

        function buildAnimations() {
          if (sourceCards.length || lens || excerpt || brief) {
            var timeline = gsap.timeline({
              paused: true,
              defaults: { ease: "power3.out" },
              onStart: function () {
                state.started = true;
                state.complete = false;
                syncControls();
              },
              onUpdate: function () {
                state.progress = readTimelineProgress(timeline, state.progress);
              },
              onPause: function () {
                state.progress = readTimelineProgress(timeline, state.progress);
                syncControls();
              },
              onComplete: function () {
                state.progress = 1;
                state.complete = true;
                state.environmentPaused = false;
                syncControls();
              }
            });

            if (sourceCards.length) {
              timeline.fromTo(sourceCards, {
                x: function (index) { return -10 - index * 4; },
                y: function (index) { return 14 - index * 5; },
                rotation: function (index) { return -14 + index * 8; },
                z: function (index) { return 28 - index * 18; }
              }, {
                x: 0,
                y: 0,
                rotation: function (index) { return index === 1 ? 5 : index === 2 ? -2 : -8; },
                z: function (index) { return 24 - index * 20; },
                duration: 0.94,
                stagger: 0.08,
                ease: "power3.out"
              }, 0);
              timeline.to(sourceCards, {
                x: function (index) { return travelX + index * 10; },
                y: function (index) { return -8 + index * 14; },
                rotation: function (index) { return -7 + index * 7; },
                z: function (index) { return 50 - index * 24; },
                duration: 1.9,
                stagger: 0.09,
                ease: "power2.inOut"
              }, 1.1);
            }

            if (track.length) {
              timeline.fromTo(track, { opacity: 0.2, scaleX: 0.45, transformOrigin: "left center" }, {
                opacity: 1,
                scaleX: 1,
                transformOrigin: "left center",
                duration: 1.7,
                ease: "power2.inOut"
              }, 1.15);
            }

            if (lens) {
              timeline.to(lens, {
                scale: 1.12,
                rotation: 7,
                duration: 0.82,
                ease: "power2.inOut"
              }, 3.2);
              timeline.to(lens, {
                scale: 1,
                rotation: 0,
                duration: 1.0,
                ease: "power2.out"
              }, 4.02);
            }

            if (excerpt) {
              timeline.fromTo(excerpt, {
                x: -118,
                y: 62,
                rotation: -4,
                clipPath: "inset(0 100% 0 0 round 9px)"
              }, {
                x: 0,
                y: 0,
                rotation: 0,
                clipPath: "inset(0 0% 0 0 round 9px)",
                duration: 1.45,
                ease: "power3.out"
              }, 3.35);
            }
            if (excerptHighlight) {
              timeline.fromTo(excerptHighlight, { x: -82, opacity: 0.35 }, {
                x: 0,
                opacity: 1,
                duration: 1.05,
                ease: "power2.out"
              }, 3.75);
            }

            if (brief) {
              timeline.fromTo(brief, { x: 54, y: 30, rotation: 3, scale: 0.94 }, {
                x: 0,
                y: 0,
                rotation: 0,
                scale: 1,
                duration: 2.7,
                ease: "power3.out"
              }, 5.1);
            }
            if (briefHeading) {
              timeline.fromTo(briefHeading, { x: 24, y: 10, opacity: 0.45 }, {
                x: 0,
                y: 0,
                opacity: 1,
                duration: 0.72,
                ease: "power2.out"
              }, 5.32);
            }
            if (briefSource) {
              timeline.fromTo(briefSource, { x: 28, opacity: 0.45 }, {
                x: 0,
                opacity: 1,
                duration: 0.72,
                ease: "power2.out"
              }, 5.62);
            }
            if (briefNext) {
              timeline.fromTo(briefNext, { x: 32, opacity: 0.45 }, {
                x: 0,
                opacity: 1,
                duration: 0.72,
                ease: "power2.out"
              }, 6.14);
            }

            state.timeline = timeline;
            writeTimelineProgress(timeline, state.progress);
          }

          if (typeof gsap.fromTo === "function") {
            entryGroups.forEach(function (group) {
              var entries = queryAll("[data-lab-entry]", group);
              if (!entries.length) return;
              gsap.fromTo(entries, { y: 18 }, {
                y: 0,
                duration: 0.48,
                stagger: 0.07,
                ease: "power2.out",
                scrollTrigger: {
                  trigger: group,
                  start: "top 84%",
                  once: true
                }
              });
            });
          }
        }

        // matchMedia already owns a context; a nested context would revert the
        // same timeline twice and make its lifecycle harder to preserve.
        buildAnimations();
        syncControls();
        if (state.progress >= 0.999) {
          state.complete = true;
          syncControls();
        } else if (!state.manualPaused) {
          maybeResume();
        }

        return function () {
          captureState(true);
          state.timeline = null;
          syncControls();
        };
      });
    } catch (_error) {
      if (media && typeof media.revert === "function") media.revert();
      state.reduced = true;
      syncControls();
    }

    runtime = {
      cleanup: function () {
        if (disposed) return;
        captureState();
        disposed = true;
        if (observer && typeof observer.disconnect === "function") observer.disconnect();
        if (media && typeof media.revert === "function") media.revert();
        listeners.splice(0).forEach(function (remove) { remove(); });
        controls.forEach(function (button) {
          button.hidden = true;
          button.setAttribute("aria-hidden", "true");
        });
        state.timeline = null;
      }
    };
    syncControls();
  }

  function cleanup() {
    if (runtime && typeof runtime.cleanup === "function") runtime.cleanup();
    runtime = null;
  }

  function bindLifecycle() {
    if (lifecycleBound || typeof window.addEventListener !== "function") return;
    lifecycleBound = true;
    window.addEventListener("pagehide", cleanup);
    window.addEventListener("pageshow", function (event) {
      if (event && event.persisted) setup();
      else if (!runtime) setup();
    });
  }

  bindLifecycle();
  setup();
})(window, document);
