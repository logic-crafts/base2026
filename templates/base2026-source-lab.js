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
        // Close the previous group before native <details> toggles this one.
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

  // Motion is deliberately inert when the local GSAP assets are absent.
  // Native details navigation above remains usable without the enhancement.
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

  function unique(elements) {
    return elements.filter(function (element, index) {
      return element && elements.indexOf(element) === index;
    });
  }

  function actionFor(button) {
    var action = (button.getAttribute("data-lab-motion") || "").toLowerCase();
    return action === "pause" || action === "resume" || action === "replay" ? action : "toggle";
  }

  function setControl(button, visible, state) {
    if (!button) return;
    button.hidden = !visible;
    button.setAttribute("aria-hidden", visible ? "false" : "true");
    if (state) button.setAttribute("data-lab-motion-state", state);
    var action = actionFor(button);
    if (action === "pause") button.setAttribute("aria-label", "Pause source motion");
    if (action === "resume") button.setAttribute("aria-label", "Resume source motion");
    if (action === "replay") button.setAttribute("aria-label", "Replay source motion once");
    if (action === "toggle") {
      var toggleLabel = state === "complete" ? "Replay illustration" : state === "paused" ? "Resume illustration" : "Pause illustration";
      button.textContent = toggleLabel;
      button.setAttribute("aria-label", state === "complete" ? "Replay illustration once" : toggleLabel);
    }
  }

  function setup() {
    cleanup();

    var scene = document.querySelector("[data-lab-scene]");
    var progressSections = queryAll("[data-lab-progress]");
    var sourceTargets = queryAll("[data-lab-source]");
    var excerptTargets = queryAll("[data-lab-excerpt]");
    var actionTargets = queryAll("[data-lab-action]");
    var lineTargets = queryAll("[data-lab-line]");
    var imageTargets = queryAll("image.b26-lab-scene__image, .b26-lab-scene__image");
    var controls = queryAll("button[data-lab-motion]");

    if (!scene && !progressSections.length) return;

    var state = {
      timeline: null,
      started: false,
      complete: false,
      manualPaused: userPaused,
      environmentPaused: false,
      hidden: Boolean(document.hidden),
      offscreen: false,
      reduced: false
    };
    var listeners = [];
    var observer = null;
    var media = null;
    var disposed = false;

    controls.forEach(function (button) {
      setControl(button, false, "disabled");
        var action = actionFor(button);
        addListener(button, "click", function () {
          var timeline = state.timeline;
        if (!timeline || state.reduced) {
          return;
        }
        if (action === "toggle") {
          if (state.complete) {
            userPaused = false;
            state.manualPaused = false;
            state.environmentPaused = false;
            state.started = true;
            state.complete = false;
            timeline.restart();
          } else if (state.manualPaused || state.environmentPaused) {
            userPaused = false;
            state.manualPaused = false;
            if (!state.hidden && !state.offscreen) {
              state.environmentPaused = false;
              if (state.started) timeline.resume();
              else timeline.play(0);
            }
          } else if (state.started) {
            userPaused = true;
            state.manualPaused = true;
            state.environmentPaused = false;
            timeline.pause();
          } else {
            maybeResume();
          }
          syncControls();
          return;
        }
        if (state.complete) {
          if (action === "replay" && state.complete && timeline) {
            state.complete = false;
          } else {
            return;
          }
        }

        if (action === "pause") {
          userPaused = true;
          state.manualPaused = true;
          state.environmentPaused = false;
          timeline.pause();
        } else if (action === "resume") {
          userPaused = false;
          state.manualPaused = false;
          if (!state.hidden && !state.offscreen) {
            state.environmentPaused = false;
            if (state.started) timeline.resume();
            else timeline.play(0);
          }
        } else if (action === "replay") {
          userPaused = false;
          state.manualPaused = false;
          state.environmentPaused = false;
          state.started = true;
          state.complete = false;
          timeline.restart();
        }
        syncControls();
      }, listeners);
    });

    function syncControls() {
      var timeline = state.timeline;
      var stateName = state.reduced ? "disabled" : state.complete ? "complete" : state.manualPaused || state.environmentPaused ? "paused" : state.started ? "running" : "ready";
      controls.forEach(function (button) {
        var action = actionFor(button);
        var visible = false;
        if (timeline && !state.reduced) {
          if (action === "toggle") visible = true;
          if (action === "pause") visible = state.started && !state.complete && !state.manualPaused && !state.environmentPaused;
          if (action === "resume") visible = state.started && !state.complete && (state.manualPaused || state.environmentPaused);
          if (action === "replay") visible = state.complete;
        }
        setControl(button, visible, stateName);
      });
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
        timeline.play(0);
      } else if (state.environmentPaused) {
        state.environmentPaused = false;
        timeline.resume();
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
          timeline.pause();
        }
      } else if (state.environmentPaused && !state.manualPaused) {
        maybeResume();
        return;
      }
      syncControls();
    }

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
        state.started = false;
        state.complete = false;
        state.manualPaused = userPaused;
        state.environmentPaused = false;
        syncControls();

        if (reduced) {
          return function () {
            state.timeline = null;
            state.reduced = true;
            syncControls();
          };
        }

        var offset = conditions.desktop ? 30 : 12;
        var localContext = null;
        var timeline = null;
        var progressTargets = [];
        progressSections.forEach(function (section) {
          if (!section || typeof section.querySelector !== "function") return;
          var progressLine = section.querySelector("[data-lab-progress-line]");
          var progressImage = section.querySelector("image.b26-lab-scene__image, .b26-lab-scene__image");
          if (progressLine) progressTargets.push(progressLine);
          else if (progressImage) progressTargets.push(progressImage);
        });
        var saveTargets = unique(sourceTargets.concat(excerptTargets, actionTargets, lineTargets, imageTargets, progressTargets));
        if (typeof gsap.saveStyles === "function" && saveTargets.length) gsap.saveStyles(saveTargets);

        function buildAnimations() {
          if (lineTargets.length) gsap.set(lineTargets, { transformOrigin: "left center" });
          if (sourceTargets.length || lineTargets.length || excerptTargets.length || actionTargets.length) {
            timeline = gsap.timeline({
              paused: true,
              defaults: { ease: "power3.out" },
              onStart: function () {
                state.started = true;
                state.complete = false;
                syncControls();
              },
              onPause: function () {
                syncControls();
              },
              onComplete: function () {
                state.complete = true;
                state.environmentPaused = false;
                syncControls();
              }
            });

            if (sourceTargets.length) timeline.fromTo(sourceTargets, {
              x: offset,
              rotation: conditions.desktop ? -1.5 : -0.75
            }, {
              x: 0,
              rotation: 0,
              duration: 0.9,
              ease: "power3.out"
            }, 0);
            if (lineTargets.length) {
              timeline.fromTo(lineTargets, { scaleX: 0 }, {
                scaleX: 1,
                duration: 0.65,
                ease: "power3.out"
              }, 0.12);
            }
            if (excerptTargets.length) timeline.fromTo(excerptTargets, { y: offset }, {
              y: 0,
              duration: 0.75,
              ease: "power3.out"
            }, 0.42);
            if (actionTargets.length) timeline.fromTo(actionTargets, { y: Math.round(offset * 0.7) }, {
              y: 0,
              duration: 0.65,
              ease: "power3.out"
            }, 1.05);
            state.timeline = timeline;
          }

          progressSections.forEach(function (section) {
            if (!section || (scene && (section === scene || (typeof section.contains === "function" && section.contains(scene))))) return;
            var progressLine = section.querySelector("[data-lab-progress-line]");
            var progressImage = section.querySelector("image.b26-lab-scene__image, .b26-lab-scene__image");
            if (progressLine) {
              gsap.set(progressLine, { transformOrigin: "left center" });
              gsap.fromTo(progressLine, { scaleX: 0 }, {
                scaleX: 1,
                ease: "none",
                scrollTrigger: {
                  trigger: section,
                  start: "top 85%",
                  end: "bottom 25%",
                  scrub: true
                }
              });
            } else if (progressImage) {
              gsap.fromTo(progressImage, { y: 18 }, {
                y: 0,
                ease: "none",
                scrollTrigger: {
                  trigger: section,
                  start: "top 85%",
                  end: "bottom 25%",
                  scrub: true
                }
              });
            }
          });
        }

        if (typeof gsap.context === "function") {
          localContext = gsap.context(buildAnimations, scene || document.body);
        } else {
          buildAnimations();
        }
        syncControls();
        maybeResume();

        return function () {
          if (localContext && typeof localContext.revert === "function") localContext.revert();
          else if (timeline && typeof timeline.kill === "function") timeline.kill();
          if (state.timeline === timeline) state.timeline = null;
          state.started = false;
          state.complete = false;
          state.environmentPaused = false;
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
        disposed = true;
        if (observer) observer.disconnect();
        if (media && typeof media.revert === "function") media.revert();
        listeners.splice(0).forEach(function (remove) { remove(); });
        controls.forEach(function (button) { setControl(button, false, "disabled"); });
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
