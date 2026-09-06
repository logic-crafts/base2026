(function (window, document) {
  "use strict";
  if (!window || !document) return;
  var all = function (selector, root) { return Array.from((root || document).querySelectorAll(selector)); };
  var reduced = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };
  var header = document.querySelector(".b26-experience-header");
  if (header) {
    var groups = all(".b26-nav-group", header);
    var desktop = window.matchMedia ? window.matchMedia("(min-width: 1101px)") : null;
    if (window.location) {
      var currentPath = window.location.pathname.replace(/\/$/, "") || "/";
      all("a[href]", header).forEach(function (link) {
        var href = link.getAttribute("href");
        if (href && href.indexOf("#") === -1 && (href.replace(/\/$/, "") || "/") === currentPath) {
          link.setAttribute("aria-current", "page");
        }
      });
    }
    function closeGroup(group, restore) {
      if (!group.open) return;
      group.open = false;
      var trigger = group.querySelector("summary");
      trigger.setAttribute("aria-expanded", "false");
      if (restore) trigger.focus();
    }
    groups.forEach(function (group) {
      var trigger = group.querySelector("summary");
      trigger.setAttribute("aria-expanded", String(group.open));
      trigger.addEventListener("click", function () {
        groups.forEach(function (other) { if (other !== group) closeGroup(other, false); });
      });
      group.addEventListener("toggle", function () {
        trigger.setAttribute("aria-expanded", String(group.open));
        if (group.open) groups.forEach(function (other) { if (other !== group) closeGroup(other, false); });
      });
      group.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && group.open) { event.preventDefault(); closeGroup(group, true); }
        if (event.key === "ArrowDown" && event.target === trigger) {
          event.preventDefault();
          groups.forEach(function (other) { if (other !== group) closeGroup(other, false); });
          group.open = true;
          trigger.setAttribute("aria-expanded", "true");
          var firstLink = group.querySelector("a[href]");
          if (firstLink) firstLink.focus();
        }
      });
      group.addEventListener("click", function (event) {
        if (event.target.closest("a")) closeGroup(group, false);
      });
    });
    document.addEventListener("pointerdown", function (event) {
      groups.forEach(function (group) { if (!group.contains(event.target)) closeGroup(group, false); });
    });
    document.addEventListener("focusin", function (event) {
      groups.forEach(function (group) { if (!group.contains(event.target)) closeGroup(group, false); });
    });
    if (desktop && desktop.addEventListener) desktop.addEventListener("change", function () {
      groups.forEach(function (group) { closeGroup(group, false); });
    });
    window.addEventListener("pagehide", function () { groups.forEach(function (group) { closeGroup(group, false); }); });
    var sheet = header.querySelector(".b26-mobile-sheet");
    var opener = header.querySelector("[data-mobile-open]");
    var fallback = header.querySelector("[data-mobile-fallback]");
    if (sheet && opener && typeof sheet.showModal === "function") {
      opener.hidden = false;
      if (fallback) fallback.hidden = true;
      function closeSheet() { if (sheet.open) sheet.close(); }
      opener.addEventListener("click", function () {
        if (sheet.open) return;
        groups.forEach(function (group) { closeGroup(group, false); });
        sheet.showModal();
        document.body.classList.add("b26-navigation-open");
        opener.setAttribute("aria-expanded", "true");
      });
      sheet.querySelector("[data-mobile-close]").addEventListener("click", closeSheet);
      sheet.addEventListener("cancel", function (event) { event.preventDefault(); closeSheet(); });
      sheet.addEventListener("close", function () {
        document.body.classList.remove("b26-navigation-open");
        opener.setAttribute("aria-expanded", "false");
        if (opener.getClientRects().length) opener.focus();
      });
      sheet.addEventListener("click", function (event) {
        if (event.target.closest("a") || event.target === sheet) closeSheet();
      });
      if (desktop && desktop.addEventListener) desktop.addEventListener("change", function (event) { if (event.matches) closeSheet(); });
      window.addEventListener("pagehide", closeSheet);
    }
  }

  var example = document.querySelector("[data-worked-example]");
  if (!example) return;
  var panels = all("[data-example-panel]", example);
  var steps = all("[data-example-step]", example);
  var play = example.querySelector("[data-example-play]");
  var status = example.querySelector("[data-example-status]");
  var active = 0;
  var timeline = null;
  var playing = false;
  var complete = false;
  var environmentalPause = false;
  var offscreen = false;
  var transition = null;
  var gsap = window.gsap;

  function showStep(index, animate) {
    active = Math.max(0, Math.min(panels.length - 1, index));
    if (transition) { transition.kill(); transition = null; }
    panels.forEach(function (panel, i) {
      panel.hidden = i !== active;
      panel.style.removeProperty("opacity");
      panel.style.removeProperty("transform");
    });
    steps.forEach(function (step, i) { step.setAttribute("aria-pressed", String(i === active)); });
    if (animate && !reduced.matches && gsap && typeof gsap.fromTo === "function") {
      transition = gsap.fromTo(panels[active], { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.36, ease: "power2.out", clearProps: "opacity,transform" });
    }
    status.textContent = ["Find: a real source, chosen for this example.", "Inspect: separate the creator’s suggestion from the context.", "Keep: copy the example note or continue in the workspace."][active];
  }
  function buttonState() {
    if (!play) return;
    play.textContent = playing ? "Pause walkthrough" : complete ? "Replay walkthrough" : timeline ? "Resume walkthrough" : "Play walkthrough";
    play.setAttribute("aria-pressed", String(playing));
  }
  function pause(manual) {
    if (timeline) timeline.pause();
    if (manual) environmentalPause = false;
    playing = false;
    buttonState();
  }
  function stop() {
    if (timeline) timeline.kill();
    timeline = null;
    playing = false;
    complete = false;
    environmentalPause = false;
    buttonState();
  }
  steps.forEach(function (step, i) {
    step.hidden = false;
    step.addEventListener("click", function () { stop(); showStep(i, true); });
  });
  showStep(0, false);
  if (play && gsap && typeof gsap.timeline === "function") {
    play.hidden = reduced.matches;
    play.addEventListener("click", function () {
      if (playing) { pause(true); return; }
      environmentalPause = false;
      if (!timeline || complete) {
        if (timeline) timeline.kill();
        complete = false;
        timeline = gsap.timeline({ paused: true, onComplete: function () {
          playing = false; complete = true; buttonState();
          status.textContent = "Walkthrough complete. Explore the source or try your own question.";
        } });
        timeline.call(function () { showStep(0, true); }, [], 0);
        timeline.call(function () { showStep(1, true); }, [], 3.2);
        timeline.call(function () { showStep(2, true); }, [], 6.4);
        timeline.call(function () {}, [], 9.6);
        timeline.play(0);
      } else timeline.resume();
      playing = true;
      buttonState();
    });
  }
  function checkEnvironment() {
    var shouldPause = document.hidden || offscreen;
    if (shouldPause && playing) { environmentalPause = true; pause(false); }
    else if (!shouldPause && environmentalPause && timeline && !complete && !reduced.matches) {
      environmentalPause = false; playing = true; timeline.resume(); buttonState();
    }
  }
  document.addEventListener("visibilitychange", checkEnvironment);
  if (typeof window.IntersectionObserver === "function") {
    new window.IntersectionObserver(function (entries) {
      offscreen = !entries[0].isIntersecting; checkEnvironment();
    }, { threshold: 0.1 }).observe(example);
  }
  if (reduced.addEventListener) reduced.addEventListener("change", function () {
    if (reduced.matches) { stop(); if (transition) transition.kill(); showStep(active, false); }
    if (play && gsap) play.hidden = reduced.matches;
  });
  window.addEventListener("pagehide", function () { pause(true); });
  var copy = example.querySelector("[data-example-copy]");
  var note = example.querySelector("[data-example-note]");
  if (copy && note) {
    copy.hidden = false;
    copy.addEventListener("click", async function () {
      try {
        if (!window.navigator.clipboard || !window.navigator.clipboard.writeText) throw new Error("Clipboard unavailable");
        await window.navigator.clipboard.writeText(note.innerText.trim());
        status.textContent = "Example note copied. It has not been saved to an account.";
        copy.textContent = "Copied";
      } catch (_) {
        status.textContent = "Copy is unavailable here. Select and copy the note below.";
        note.tabIndex = -1; note.focus();
      }
    });
  }
})(window, document);
