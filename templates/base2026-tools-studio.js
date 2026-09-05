(function () {
  "use strict";

  function initToolsStudio() {
    var root = document.querySelector("[data-tools-studio]");
    if (!root) return;

    var stationContent = {
      find: {
        index: "01 / FIND",
        title: "Find public evidence for one narrow question.",
        description: "Start with a question, topic or creator. Evidence Search returns a short list of public matches so you can open the Base2026 record and follow the original source where available.",
        input: "One narrow question, topic or creator.",
        output: "Attributed records with a source path and visible limits.",
        action: "Read at least one record before repeating its recommendation."
      },
      extract: {
        index: "02 / EXTRACT",
        title: "Extract the passage without losing its context.",
        description: "Use a selected public record to see the surrounding passage, record metadata and the limits of what that source actually says.",
        input: "One or more public record IDs.",
        output: "Bounded excerpts, record metadata and original-source links where available.",
        action: "Keep the excerpt and its source together in your working note."
      },
      attribute: {
        index: "03 / ATTRIBUTE",
        title: "Attribute every useful claim to its source.",
        description: "Compare the creator, exact record and normalized original-source relationships before calling repeated material independent evidence.",
        input: "Up to 12 public record or source IDs.",
        output: "Exact relationships, unresolved metadata and a source-diversity readout.",
        action: "Open the originals before treating a pattern as a consensus."
      },
      publish: {
        index: "04 / PUBLISH",
        title: "Publish a next step only after a human decision.",
        description: "Turn selected, attributed evidence into a local brief or a measured SEO experiment handoff. The public tools do not edit or publish a site for you.",
        input: "Selected public IDs, audience and one concrete work question.",
        output: "A portable brief or Experiment Card with measurement unknowns visible.",
        action: "Verify the source, choose the change and keep publication human-owned."
      }
    };

    var panel = root.querySelector("[data-station-panel]");
    var panelKicker = root.querySelector("[data-panel-kicker]");
    var panelTitle = root.querySelector("[data-panel-title]");
    var panelDescription = root.querySelector("[data-panel-description]");
    var panelInput = root.querySelector("[data-panel-input]");
    var panelOutput = root.querySelector("[data-panel-output]");
    var panelAction = root.querySelector("[data-panel-action]");
    var stationButtons = Array.prototype.slice.call(root.querySelectorAll("[data-station-button]"));
    var initialStationButton = stationButtons.find(function (button) {
      return button.getAttribute("aria-selected") === "true";
    }) || stationButtons[0];
    var initialStationKey = initialStationButton ? initialStationButton.getAttribute("data-station-button") : "find";

    // Apply roving tab stops only after JavaScript is available; no-JS keeps
    // every native button reachable in the normal document tab order.
    stationButtons.forEach(function (button) {
      button.setAttribute("tabindex", button === initialStationButton ? "0" : "-1");
    });

    function selectStation(key, moveFocus) {
      var content = stationContent[key];
      if (!content || !panel) return;

      stationButtons.forEach(function (button) {
        var selected = button.getAttribute("data-station-button") === key;
        button.setAttribute("aria-selected", selected ? "true" : "false");
        button.setAttribute("tabindex", selected ? "0" : "-1");
        if (selected && moveFocus) button.focus();
      });

      if (panelKicker) panelKicker.textContent = content.index;
      if (panelTitle) panelTitle.textContent = content.title;
      if (panelDescription) panelDescription.textContent = content.description;
      if (panelInput) panelInput.textContent = content.input;
      if (panelOutput) panelOutput.textContent = content.output;
      if (panelAction) panelAction.textContent = content.action;

      var selectedButton = root.querySelector('[data-station-button="' + key + '"]');
      if (selectedButton) panel.setAttribute("aria-labelledby", selectedButton.id);
    }

    selectStation(initialStationKey, false);

    stationButtons.forEach(function (button, index) {
      button.addEventListener("click", function () {
        selectStation(button.getAttribute("data-station-button"), false);
      });
      button.addEventListener("keydown", function (event) {
        var nextIndex = index;
        if (event.key === "ArrowRight" || event.key === "ArrowDown") nextIndex = (index + 1) % stationButtons.length;
        if (event.key === "ArrowLeft" || event.key === "ArrowUp") nextIndex = (index - 1 + stationButtons.length) % stationButtons.length;
        if (event.key === "Home") nextIndex = 0;
        if (event.key === "End") nextIndex = stationButtons.length - 1;
        if (nextIndex === index) return;
        event.preventDefault();
        selectStation(stationButtons[nextIndex].getAttribute("data-station-button"), true);
      });
    });

    var factory = root.querySelector("[data-factory]");
    var factoryToggle = root.querySelector("[data-factory-toggle]");
    var factorySignal = root.querySelector("[data-factory-signal]");
    var factoryPlaying = true;
    var factoryVisible = false;
    var factoryCompleted = false;
    var documentVisible = document.visibilityState !== "hidden";
    var motionQuery = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : null;

    function reducedMotion() {
      return Boolean(motionQuery && motionQuery.matches);
    }

    function restartFactorySignal() {
      if (!factorySignal) return;
      factoryCompleted = false;
      if (factory) factory.removeAttribute("data-factory-complete");
      factorySignal.classList.remove("is-running");
      void factorySignal.offsetWidth;
      factorySignal.classList.add("is-running");
    }

    function syncFactory() {
      if (!factory) return;
      factory.setAttribute("data-factory-playing", factoryPlaying ? "true" : "false");
      factory.setAttribute("data-factory-visible", factoryVisible ? "true" : "false");
      factory.setAttribute("data-factory-page-visible", documentVisible ? "true" : "false");
      if (factoryToggle) {
        factoryToggle.textContent = factoryPlaying ? "Pause illustration" : "Play illustration";
        factoryToggle.setAttribute("aria-pressed", factoryPlaying ? "false" : "true");
      }
      if (!factorySignal) return;
      if (reducedMotion() || factoryCompleted) {
        factorySignal.classList.remove("is-running");
      } else if (factoryVisible || factorySignal.classList.contains("is-running")) {
        // Keep the class while paused/offscreen so animation-play-state can
        // preserve elapsed progress instead of restarting the keyframes.
        factorySignal.classList.add("is-running");
      }
      factorySignal.style.animationPlayState = !reducedMotion() && factoryPlaying && factoryVisible && documentVisible && !factoryCompleted ? "running" : "paused";
    }

    if (factoryToggle) {
      factoryToggle.addEventListener("click", function () {
        factoryPlaying = !factoryPlaying;
        if (factoryPlaying && factoryCompleted) restartFactorySignal();
        syncFactory();
      });
    }
    if (factorySignal) {
      factorySignal.addEventListener("animationend", function (event) {
        if (event.animationName !== "b26-tools-factory-signal") return;
        factoryCompleted = true;
        factorySignal.classList.remove("is-running");
        if (factory) factory.setAttribute("data-factory-complete", "true");
      });
    }
    if (motionQuery && motionQuery.addEventListener) {
      motionQuery.addEventListener("change", function () {
        syncFactory();
      });
    }
    syncFactory();

    var liveStats = root.querySelector("[data-live-stats]");
    var liveStatus = root.querySelector("[data-live-stats-status]");
    var generatedNode = root.querySelector("[data-stat-generated]");
    var statNodes = {};
    ["documents_indexed", "distinct_sources", "public_evidence_routes", "projected_cards"].forEach(function (key) {
      statNodes[key] = root.querySelector('[data-stat-value="' + key + '"]');
    });
    var statsIntersecting = false;
    var statsVisible = false;
    var statsInterval = null;
    var statsRequest = null;
    var hasGoodRead = false;
    var lastServerLabel = "";
    var lastGoodValues = {};
    var metricKeys = Object.keys(statNodes);

    function setStatsState(state) {
      if (liveStats) liveStats.setAttribute("data-state", state);
      if (liveStatus) liveStatus.setAttribute("data-state", state);
      Object.keys(statNodes).forEach(function (key) {
        if (statNodes[key]) statNodes[key].closest(".b26-tools-stat").setAttribute("data-state", state);
      });
    }

    function setUnavailable() {
      metricKeys.forEach(function (key) {
        if (statNodes[key]) statNodes[key].textContent = "Unavailable";
      });
      if (generatedNode) generatedNode.textContent = "Unavailable";
    }

    function setStatus(state, message) {
      setStatsState(state);
      if (liveStatus) liveStatus.textContent = message;
    }

    function validMetric(value) {
      return Number.isSafeInteger(value) && value >= 0;
    }

    function validServerTime(value) {
      return typeof value === "string" && value.trim() !== "" && !Number.isNaN(Date.parse(value));
    }

    function applyStatsPayload(payload) {
      var dataset = payload && typeof payload === "object" ? payload.dataset : null;
      if (!dataset || typeof dataset !== "object") throw new Error("invalid public dataset");

      var missing = [];
      metricKeys.forEach(function (key) {
        if (!validMetric(dataset[key])) {
          missing.push(key);
          if (statNodes[key]) statNodes[key].textContent = "Unavailable";
          return;
        }
        if (statNodes[key]) statNodes[key].textContent = dataset[key].toLocaleString("en-US");
      });

      var serverTime = payload.generated_at;
      var hasTime = validServerTime(serverTime);
      if (generatedNode) generatedNode.textContent = hasTime ? serverTime : "Unavailable";

      if (missing.length === 0 && hasTime) {
        metricKeys.forEach(function (key) {
          lastGoodValues[key] = dataset[key];
        });
        hasGoodRead = true;
        lastServerLabel = serverTime;
        setStatus("ready", "Public counters · updated " + serverTime);
        return;
      }

      if (hasGoodRead) {
        metricKeys.forEach(function (key) {
          if (statNodes[key]) statNodes[key].textContent = lastGoodValues[key].toLocaleString("en-US");
        });
        if (generatedNode) generatedNode.textContent = lastServerLabel;
        setStatus("stale", "Public counters stale · last server read " + lastServerLabel);
        return;
      }

      var missingLabel = missing.length ? " · missing fields" : " · server time unavailable";
      setStatus("unavailable", "Public counters unavailable" + missingLabel + ".");
    }

    function markStatsError() {
      if (hasGoodRead) {
        setStatus("stale", "Public counters stale · last server read " + lastServerLabel);
        return;
      }
      setUnavailable();
      setStatus("unavailable", "Public counters unavailable · no zero inferred.");
    }

    function refreshStats() {
      if (!liveStats || !statsVisible || statsRequest) return;

      var controller = new AbortController();
      var request = { controller: controller };
      var timeoutId = window.setTimeout(function () { controller.abort(); }, 8000);
      statsRequest = request;

      fetch("/api/stats", {
        method: "GET",
        headers: { Accept: "application/json" },
        credentials: "same-origin",
        signal: controller.signal
      })
        .then(function (response) {
          if (!response.ok) throw new Error("public stats unavailable");
          return response.json();
        })
        .then(function (payload) {
          if (statsRequest !== request || !statsVisible) return;
          applyStatsPayload(payload);
        })
        .catch(function (error) {
          if (statsRequest !== request || (!statsVisible && error.name === "AbortError")) return;
          markStatsError();
        })
        .finally(function () {
          window.clearTimeout(timeoutId);
          if (statsRequest === request) statsRequest = null;
        });
    }

    function syncStatsVisibility() {
      var nextVisible = statsIntersecting && documentVisible;
      if (nextVisible === statsVisible) return;

      statsVisible = nextVisible;
      if (!statsVisible) {
        if (statsInterval) {
          window.clearInterval(statsInterval);
          statsInterval = null;
        }
        if (statsRequest) {
          statsRequest.controller.abort();
          statsRequest = null;
        }
        return;
      }

      if (!statsInterval) statsInterval = window.setInterval(refreshStats, 60000);
      refreshStats();
    }

    function startStats() {
      if (!liveStats) return;
      statsIntersecting = true;
      syncStatsVisibility();
    }

    function stopStats() {
      statsIntersecting = false;
      syncStatsVisibility();
    }

    document.addEventListener("visibilitychange", function () {
      documentVisible = document.visibilityState !== "hidden";
      syncFactory();
      syncStatsVisibility();
    });

    var revealTargets = Array.prototype.slice.call(root.querySelectorAll("[data-reveal]"));
    var supportsObserver = "IntersectionObserver" in window;
    var observer = null;
    if (supportsObserver) {
      observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.target === factory) {
            factoryVisible = entry.isIntersecting;
            syncFactory();
          }
          if (entry.target === liveStats) {
            if (entry.isIntersecting) startStats();
            else stopStats();
          }
          if (entry.target.hasAttribute("data-reveal") && entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.12 });

      if (!reducedMotion()) {
        root.classList.add("is-motion-ready");
        revealTargets.forEach(function (target) { observer.observe(target); });
      } else {
        revealTargets.forEach(function (target) { target.classList.add("is-visible"); });
      }
      if (factory) observer.observe(factory);
      if (liveStats) observer.observe(liveStats);
    } else {
      revealTargets.forEach(function (target) { target.classList.add("is-visible"); });
      factoryVisible = true;
      syncFactory();
      startStats();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initToolsStudio, { once: true });
  } else {
    initToolsStudio();
  }
})();
