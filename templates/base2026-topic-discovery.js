/* Progressive topic discovery for the generated /topics/ index. */
(function (host) {
  "use strict";

  var PAGE_SIZE = 24;
  var MAX_QUERY_LENGTH = 160;
  var DEFAULT_STATE = { query: "", coverage: "all", sort: "sources", page: 1 };
  var COVERAGES = ["all", "multiple", "single"];
  var SORTS = ["sources", "az"];
  var ROUTE_PATTERN = /^\/topics\/[a-z0-9]+(?:-[a-z0-9]+)*$/;

  function asText(value) {
    return String(value == null ? "" : value).trim();
  }

  function canonicalRoute(value) {
    var route = asText(value);
    return ROUTE_PATTERN.test(route) ? route : "";
  }

  function numberValue(value) {
    var number = Number.parseInt(value, 10);
    return Number.isFinite(number) && number >= 0 ? number : 0;
  }

  function normaliseRecord(record, order) {
    var title = asText(record && (record.title || record.displayTitle));
    var displayTitle = asText(record && (record.displayTitle || record.title));
    var route = canonicalRoute(record && record.route);
    if (!title || !displayTitle || !route) return null;
    var description = asText(record && record.description);
    var insights = numberValue(record && (record.insights == null ? record.insightCount : record.insights));
    var sources = numberValue(record && (record.sources == null ? record.sourceCount : record.sources));
    var countLabel = asText(record && (record.countLabel || record.counts));
    if (!countLabel) countLabel = insights + " public insights · " + sources + " sources";
    return {
      title: title,
      displayTitle: displayTitle,
      description: description,
      route: route,
      insights: insights,
      sources: sources,
      countLabel: countLabel,
      order: Number.isFinite(order) ? order : 0,
      searchText: (title + " " + displayTitle + " " + description + " " + route).toLocaleLowerCase()
    };
  }

  function normaliseRecords(records) {
    return (Array.isArray(records) ? records : []).map(normaliseRecord).filter(Boolean);
  }

  function normaliseState(input) {
    var state = input || {};
    var query = asText(state.query).slice(0, MAX_QUERY_LENGTH);
    var coverage = COVERAGES.indexOf(state.coverage) >= 0 ? state.coverage : DEFAULT_STATE.coverage;
    var sort = SORTS.indexOf(state.sort) >= 0 ? state.sort : DEFAULT_STATE.sort;
    var page = Number.parseInt(state.page, 10);
    if (!Number.isFinite(page) || page < 1) page = 1;
    return { query: query, coverage: coverage, sort: sort, page: page };
  }

  function filterRecords(records, state) {
    var active = normaliseState(state);
    var query = active.query.toLocaleLowerCase();
    return records.filter(function (record) {
      if (active.coverage === "multiple" && record.sources <= 1) return false;
      if (active.coverage === "single" && record.sources !== 1) return false;
      return !query || record.searchText.indexOf(query) >= 0;
    });
  }

  function sortRecords(records, sort) {
    var mode = SORTS.indexOf(sort) >= 0 ? sort : DEFAULT_STATE.sort;
    return records.slice().sort(function (left, right) {
      if (mode === "az") {
        var titleResult = left.displayTitle.localeCompare(right.displayTitle, undefined, { sensitivity: "base" });
        if (titleResult) return titleResult;
      } else {
        if (right.sources !== left.sources) return right.sources - left.sources;
        if (right.insights !== left.insights) return right.insights - left.insights;
      }
      if (left.order !== right.order) return left.order - right.order;
      return left.title.localeCompare(right.title, undefined, { sensitivity: "base" });
    });
  }

  function selectRecords(records, state) {
    return sortRecords(filterRecords(records, state), normaliseState(state).sort);
  }

  function paginateRecords(records, page, pageSize) {
    var size = Number.parseInt(pageSize, 10);
    if (!Number.isFinite(size) || size < 1) size = PAGE_SIZE;
    var total = records.length;
    var totalPages = Math.max(1, Math.ceil(total / size));
    var safePage = Number.parseInt(page, 10);
    if (!Number.isFinite(safePage) || safePage < 1) safePage = 1;
    safePage = Math.min(safePage, totalPages);
    var start = total ? (safePage - 1) * size : 0;
    var end = Math.min(start + size, total);
    return {
      page: safePage,
      pageSize: size,
      total: total,
      totalPages: totalPages,
      start: start,
      end: end,
      items: records.slice(start, end)
    };
  }

  function stateFromSearch(search) {
    var params = new URLSearchParams(search || "");
    return normaliseState({
      query: params.get("q") || "",
      coverage: params.get("coverage") || DEFAULT_STATE.coverage,
      sort: params.get("sort") || DEFAULT_STATE.sort,
      page: params.get("page") || DEFAULT_STATE.page
    });
  }

  function searchFromState(state) {
    var active = normaliseState(state);
    var params = new URLSearchParams();
    params.set("q", active.query);
    params.set("coverage", active.coverage);
    params.set("sort", active.sort);
    params.set("page", String(active.page));
    return "?" + params.toString();
  }

  function writeUrlState(location, history, state, mode) {
    if (!location || !history) return "";
    var method = mode === "replace" ? "replaceState" : "pushState";
    var path = String(location.pathname || "/") + searchFromState(state) + String(location.hash || "");
    if (typeof history[method] === "function") history[method]({}, "", path);
    return path;
  }

  function formatRange(page) {
    if (!page.total) return "No topics match these filters";
    return "Showing " + (page.start + 1) + "–" + page.end + " of " + page.total + " topics";
  }

  function recordsFromCards(cards) {
    return Array.prototype.map.call(cards || [], function (card, order) {
      var data = card && card.dataset ? card.dataset : {};
      return normaliseRecord({
        title: data.topicTitle,
        displayTitle: data.topicDisplayTitle,
        description: data.topicDescription,
        route: data.topicRoute,
        insights: data.topicInsights,
        sources: data.topicSources,
        countLabel: data.topicCountLabel
      }, order);
    }).filter(Boolean);
  }

  function createCard(documentRef, record) {
    var article = documentRef.createElement("article");
    article.className = "b26-topic-card";
    article.setAttribute("data-topic-card", "");
    var link = documentRef.createElement("a");
    link.className = "b26-topic-card__link";
    link.href = canonicalRoute(record.route);
    var kicker = documentRef.createElement("span");
    kicker.className = "b26-topic-card__kicker";
    kicker.textContent = "Topic";
    var title = documentRef.createElement("h3");
    title.className = "b26-topic-card__title";
    title.textContent = record.displayTitle;
    var meta = documentRef.createElement("p");
    meta.className = "b26-topic-card__meta";
    meta.textContent = record.countLabel;
    var description = documentRef.createElement("p");
    description.className = "b26-topic-card__description";
    description.textContent = record.description;
    var action = documentRef.createElement("span");
    action.className = "b26-topic-card__action";
    action.textContent = "Open topic ";
    var arrow = documentRef.createElement("span");
    arrow.setAttribute("aria-hidden", "true");
    arrow.textContent = "↗";
    action.appendChild(arrow);
    link.append(kicker, title, meta, description, action);
    article.appendChild(link);
    return article;
  }

  function renderRecords(documentRef, container, records, sort) {
    container.replaceChildren();
    if (sort !== "az") {
      records.forEach(function (record) { container.appendChild(createCard(documentRef, record)); });
      return;
    }
    var groups = new Map();
    records.forEach(function (record) {
      var initial = (record.displayTitle.charAt(0) || "#").toLocaleUpperCase();
      if (!/[A-Z]/.test(initial)) initial = "#";
      if (!groups.has(initial)) groups.set(initial, []);
      groups.get(initial).push(record);
    });
    groups.forEach(function (groupRecords, initial) {
      var group = documentRef.createElement("section");
      group.className = "b26-topic-group";
      group.setAttribute("data-topic-group", initial);
      var heading = documentRef.createElement("h3");
      heading.className = "b26-topic-group__title";
      heading.textContent = initial;
      group.appendChild(heading);
      var list = documentRef.createElement("div");
      list.className = "b26-topic-group__grid";
      groupRecords.forEach(function (record) { list.appendChild(createCard(documentRef, record)); });
      group.appendChild(list);
      container.appendChild(group);
    });
  }

  function init(root) {
    if (!root || !host.document) return null;
    var documentRef = host.document;
    var results = root.querySelector("[data-topic-results]");
    var controls = root.querySelector("[data-topic-controls]");
    var collections = root.querySelector(".b26-topic-discovery__collections");
    var search = root.querySelector("[data-topic-search]");
    var sort = root.querySelector("[data-topic-sort]");
    var coverage = root.querySelector("[data-topic-coverage]");
    var count = root.querySelector("[data-topic-count]");
    var empty = root.querySelector("[data-topic-empty]");
    var emptyCopy = root.querySelector("[data-topic-empty-copy]");
    var clear = root.querySelector("[data-topic-clear]");
    var emptyClear = root.querySelector("[data-topic-empty-clear]");
    var pagination = root.querySelector("[data-topic-pagination]");
    var previous = root.querySelector("[data-topic-previous]");
    var next = root.querySelector("[data-topic-next]");
    var pageLabel = root.querySelector("[data-topic-page-label]");
    var directoryHeading = root.querySelector("#b26-topic-directory-title");
    if (!results || !controls || !search || !sort || !coverage || !count || !empty || !pagination || !previous || !next || !pageLabel) return null;

    var records = recordsFromCards(results.querySelectorAll("[data-topic-card]"));
    var state = stateFromSearch(host.location && host.location.search);
    var timer = null;
    controls.hidden = false;

    function syncControls() {
      search.value = state.query;
      sort.value = state.sort;
      coverage.value = state.coverage;
      if (clear) clear.hidden = !state.query && state.coverage === "all";
    }

    function render() {
      var selected = selectRecords(records, state);
      var page = paginateRecords(selected, state.page, PAGE_SIZE);
      state.page = page.page;
      syncControls();
      if (collections) {
        collections.hidden = Boolean(state.query || state.coverage !== "all" || state.page > 1);
      }
      renderRecords(documentRef, results, page.items, state.sort);
      count.textContent = formatRange(page);
      empty.hidden = page.total !== 0;
      if (emptyCopy) emptyCopy.textContent = page.total ? "" : "No topics match these filters.";
      pagination.hidden = page.totalPages <= 1 || page.total === 0;
      previous.disabled = page.page <= 1;
      next.disabled = page.page >= page.totalPages;
      previous.setAttribute("aria-disabled", String(previous.disabled));
      next.setAttribute("aria-disabled", String(next.disabled));
      pageLabel.textContent = "Page " + page.page + " of " + page.totalPages;
    }

    function commit(nextState, historyMode) {
      cancelPendingSearch();
      state = normaliseState(nextState);
      render();
      writeUrlState(host.location, host.history, state, historyMode || "push");
    }

    function cancelPendingSearch() {
      if (timer) host.clearTimeout(timer);
      timer = null;
    }

    function focusDirectory() {
      if (!directoryHeading) return;
      if (typeof directoryHeading.focus === "function") {
        try {
          directoryHeading.focus({ preventScroll: true });
        } catch (_error) {
          directoryHeading.focus();
        }
      }
      if (typeof directoryHeading.scrollIntoView === "function") {
        var behavior = "smooth";
        if (typeof host.matchMedia === "function" && host.matchMedia("(prefers-reduced-motion: reduce)").matches) behavior = "auto";
        directoryHeading.scrollIntoView({ block: "start", behavior: behavior });
      }
    }

    function clearState() {
      commit(DEFAULT_STATE, "push");
      search.focus();
    }

    search.addEventListener("input", function () {
      if (timer) host.clearTimeout(timer);
      var value = search.value;
      timer = host.setTimeout(function () {
        timer = null;
        commit({ query: value, coverage: coverage.value, sort: sort.value, page: 1 }, "push");
      }, 220);
    });
    search.addEventListener("keydown", function (event) {
      if (event.key === "Enter") {
        if (timer) host.clearTimeout(timer);
        commit({ query: search.value, coverage: coverage.value, sort: sort.value, page: 1 }, "push");
      }
    });
    sort.addEventListener("change", function () {
      commit({ query: search.value, coverage: coverage.value, sort: sort.value, page: 1 }, "push");
    });
    coverage.addEventListener("change", function () {
      commit({ query: search.value, coverage: coverage.value, sort: sort.value, page: 1 }, "push");
    });
    if (clear) clear.addEventListener("click", clearState);
    if (emptyClear) emptyClear.addEventListener("click", clearState);
    previous.addEventListener("click", function () {
      if (!previous.disabled) {
        commit({ query: state.query, coverage: state.coverage, sort: state.sort, page: state.page - 1 }, "push");
        focusDirectory();
      }
    });
    next.addEventListener("click", function () {
      if (!next.disabled) {
        commit({ query: state.query, coverage: state.coverage, sort: state.sort, page: state.page + 1 }, "push");
        focusDirectory();
      }
    });
    host.addEventListener("popstate", function () {
      cancelPendingSearch();
      state = stateFromSearch(host.location && host.location.search);
      render();
    });
    render();
    return { records: records, getState: function () { return state; } };
  }

  var api = {
    PAGE_SIZE: PAGE_SIZE,
    MAX_QUERY_LENGTH: MAX_QUERY_LENGTH,
    DEFAULT_STATE: DEFAULT_STATE,
    canonicalRoute: canonicalRoute,
    normaliseState: normaliseState,
    filterRecords: function (records, state) { return filterRecords(normaliseRecords(records), state); },
    sortRecords: sortRecords,
    selectRecords: function (records, state) { return selectRecords(normaliseRecords(records), state); },
    paginateRecords: paginateRecords,
    stateFromSearch: stateFromSearch,
    searchFromState: searchFromState,
    writeUrlState: writeUrlState,
    formatRange: formatRange,
    init: init
  };

  host.Base2026TopicDiscovery = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (host.document) {
    var start = function () {
      var root = host.document.querySelector("[data-b26-topic-discovery]");
      if (root) init(root);
    };
    if (host.document.readyState === "loading") host.document.addEventListener("DOMContentLoaded", start);
    else start();
  }
})(typeof window !== "undefined" ? window : globalThis);
