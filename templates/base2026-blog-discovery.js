/* The public editorial API is the sole live index. Filters become available
   only after every cursor page has arrived; the server-rendered articles and
   continuation link remain usable if that read cannot finish. */
(function (root, factory) {
  "use strict";
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root && root.document) api.mount(root.document, root);
})(typeof window !== "undefined" ? window : null, function () {
  "use strict";
  var ORIGIN = "https://base2026.dev";
  var PAGE_SIZE = 9;
  var MAX_PAGES = 100;
  var MAX_ARTICLES = 2500;

  function compact(value, limit) {
    return String(value || "").replace(/\s+/g, " ").trim().slice(0, limit);
  }

  function readState(href) {
    var params = new URL(href, ORIGIN).searchParams;
    var page = Number(params.get("page") || "1");
    return {
      q: compact(params.get("q"), 160),
      category: compact(params.get("category"), 100),
      page: Number.isSafeInteger(page) && page > 0 && page <= 9999 ? page : 1
    };
  }

  function stateUrl(state, href) {
    var url = new URL(href, ORIGIN);
    url.searchParams.delete("cursor");
    ["q", "category", "page"].forEach(function (name) { url.searchParams.delete(name); });
    if (state.q) url.searchParams.set("q", compact(state.q, 160));
    if (state.category) url.searchParams.set("category", compact(state.category, 100));
    if (state.page > 1) url.searchParams.set("page", String(state.page));
    return url.pathname + url.search + url.hash;
  }

  function requiredText(value, max) {
    if (typeof value !== "string" || !value.trim() || value.length > max) throw new Error("ARTICLE_INDEX_INVALID");
    return value;
  }

  function normalizeArticle(input) {
    if (!input || typeof input !== "object") throw new Error("ARTICLE_INDEX_INVALID");
    var item = {};
    [["id", 120], ["path", 180], ["title", 500], ["description", 2000], ["category", 100],
      ["author", 200], ["published_at", 40], ["updated_at", 40]].forEach(function (field) {
      item[field[0]] = requiredText(input[field[0]], field[1]);
    });
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(item.id)
      || !/^\/(?:blog|journal)\/[a-z0-9]+(?:-[a-z0-9]+)*\/$/.test(item.path)
      || !/^\d{4}-\d{2}-\d{2}(?:T.*Z)?$/.test(item.published_at)
      || !Number.isFinite(Date.parse(item.published_at)) || !Number.isFinite(Date.parse(item.updated_at))) {
      throw new Error("ARTICLE_INDEX_INVALID");
    }
    if (input.hero) {
      if (typeof input.hero !== "object"
        || typeof input.hero.path !== "string"
        || !/^\/static\/assets\/[a-zA-Z0-9/_-]+\.(?:png|webp|jpe?g)$/.test(input.hero.path)
        || input.hero.path.includes("..")) throw new Error("ARTICLE_IMAGE_INVALID");
      item.hero = {
        path: input.hero.path, alt: requiredText(input.hero.alt, 700),
        credit: requiredText(input.hero.credit, 700), ai_generated: input.hero.ai_generated === true
      };
    }
    return item;
  }

  function nextApiPath(nextUrl, cursor) {
    if (nextUrl === null && cursor === null) return null;
    if (typeof nextUrl !== "string" || nextUrl.length > 320 || !cursor || typeof cursor !== "object") {
      throw new Error("ARTICLE_CURSOR_INVALID");
    }
    var next = new URL(nextUrl, ORIGIN);
    var keys = Array.from(next.searchParams.keys());
    var value = next.searchParams.get("cursor");
    if (next.origin !== ORIGIN || next.pathname !== "/blog" || next.hash || keys.length !== 1 || keys[0] !== "cursor"
      || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\|[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value || "")
      || value !== cursor.published_at + "|" + cursor.slug) throw new Error("ARTICLE_CURSOR_INVALID");
    return "/api/blog" + next.search;
  }

  async function loadAllArticles(fetcher, options) {
    options = options || {};
    var current = "/api/blog";
    var seenPages = new Set();
    var articles = new Map();
    while (current) {
      if (seenPages.has(current) || seenPages.size >= MAX_PAGES) throw new Error("ARTICLE_INDEX_INCOMPLETE");
      seenPages.add(current);
      var result = await fetcher(current, {
        method: "GET", credentials: "omit", headers: { Accept: "application/json" }, signal: options.signal
      });
      if (!result.ok) throw new Error("ARTICLE_INDEX_UNAVAILABLE");
      var page = await result.json();
      if (!page || page.schema_version !== "base2026.editorial-index.v1" || !Array.isArray(page.articles)
        || page.articles.length > 50) throw new Error("ARTICLE_INDEX_INVALID");
      page.articles.map(normalizeArticle).forEach(function (item) {
        if (!articles.has(item.path)) articles.set(item.path, item);
      });
      if (articles.size > MAX_ARTICLES) throw new Error("ARTICLE_INDEX_INCOMPLETE");
      current = nextApiPath(page.next_url, page.next_cursor);
      if (options.onProgress) options.onProgress(articles.size, current === null);
    }
    return Array.from(articles.values()).sort(function (a, b) {
      return Date.parse(b.published_at) - Date.parse(a.published_at) || a.id.localeCompare(b.id);
    });
  }

  function selectArticles(articles, state) {
    var terms = compact(state.q, 160).toLocaleLowerCase().split(" ").filter(Boolean);
    var matches = articles.filter(function (article) {
      if (state.category && article.category !== state.category) return false;
      var text = [article.title, article.description, article.category, article.author].join(" ").toLocaleLowerCase();
      return terms.every(function (term) { return text.includes(term); });
    });
    var pages = Math.max(1, Math.ceil(matches.length / PAGE_SIZE));
    var page = Math.min(Math.max(state.page, 1), pages);
    return { matches: matches, page: page, pages: pages, total: matches.length, items: matches.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE) };
  }

  function categoriesFor(articles) {
    var counts = new Map();
    articles.forEach(function (article) { counts.set(article.category, (counts.get(article.category) || 0) + 1); });
    return Array.from(counts.entries()).sort(function (a, b) { return a[0].localeCompare(b[0]); });
  }

  function element(document, tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function articleCard(document, item, featured) {
    var article = element(document, "article", featured ? "b26-blog-feature" + (item.hero ? "" : " b26-blog-feature--text-only") : "b26-blog-card");
    var link = element(document, "a", "b26-blog-card__link");
    link.href = item.path;
    var content = featured ? element(document, "div", "b26-blog-feature__body") : link;
    var meta = element(document, "p", "b26-blog-card__meta");
    meta.append(element(document, "span", "b26-blog-card__category", item.category));
    var time = element(document, "time", "", new Intl.DateTimeFormat("en-US", {
      month: "long", day: "numeric", year: "numeric", timeZone: "UTC"
    }).format(new Date(item.published_at)));
    time.dateTime = item.published_at;
    meta.append(time);
    var title = element(document, featured ? "h2" : "h3", "b26-blog-card__title", item.title);
    title.id = "blog-" + (featured ? "feature-" : "card-") + (item.path.startsWith("/journal/") ? "journal-" : "article-") + item.id;
    link.setAttribute("aria-labelledby", title.id);
    var foot = element(document, "div", "b26-blog-card__footer");
    foot.append(element(document, "span", "b26-blog-card__byline", item.author), element(document, "span", "b26-blog-card__read", "Read article →"));
    content.append(meta, title, element(document, "p", "b26-blog-card__excerpt", item.description), foot);
    if (featured) link.append(content);
    if (featured && item.hero) {
      var figure = element(document, "figure", "b26-blog-feature__media");
      var image = element(document, "img");
      image.src = item.hero.path;
      image.alt = item.hero.alt;
      image.loading = "eager";
      image.decoding = "async";
      var credit = item.hero.credit;
      if (item.hero.ai_generated && !/AI[- ]generated/i.test(credit)) credit += " AI-generated editorial illustration.";
      figure.append(image, element(document, "figcaption", "", credit));
      link.append(figure);
    }
    article.append(link);
    return article;
  }

  function mount(document, window) {
    var host = document.querySelector("[data-blog-discovery]");
    if (!host || host.dataset.blogMounted) return null;
    var selectors = {
      controls: "[data-blog-controls]", form: "[data-blog-search]", query: "#blog-query", categories: "[data-blog-categories]",
      featured: "[data-blog-featured]", results: "[data-blog-results]", empty: "[data-blog-empty]", count: "[data-blog-count]",
      title: "[data-blog-results-title]", pagination: "[data-blog-pagination]", previous: "[data-blog-previous]",
      next: "[data-blog-next]", pageLabel: "[data-blog-page-label]", status: "[data-blog-load-status]", retry: "[data-blog-retry]"
    };
    var nodes = {};
    if (!Object.keys(selectors).every(function (key) { nodes[key] = host.querySelector(selectors[key]); return !!nodes[key]; })) return null;
    host.dataset.blogMounted = "true";
    var state = readState(window.location.href);
    var articles = null;
    var controller;
    var timer;
    var listeners = [];

    function listen(target, event, handler) {
      target.addEventListener(event, handler);
      listeners.push(function () { target.removeEventListener(event, handler); });
    }

    function render() {
      if (!articles) return;
      var selection = selectArticles(articles, state);
      state.page = selection.page;
      nodes.query.value = state.q;
      Array.from(nodes.categories.querySelectorAll("button")).forEach(function (button) {
        button.setAttribute("aria-pressed", String(button.dataset.category === state.category));
      });
      var featured = !state.q && !state.category && state.page === 1 && selection.items.length > 0;
      nodes.featured.hidden = !featured;
      if (featured) nodes.featured.replaceChildren(articleCard(document, selection.items[0], true));
      nodes.results.replaceChildren.apply(nodes.results, selection.items.slice(featured ? 1 : 0).map(function (item) { return articleCard(document, item, false); }));
      nodes.empty.hidden = selection.total !== 0;
      nodes.count.hidden = false;
      nodes.title.textContent = state.q || state.category ? "Matching articles" : "Latest articles";
      nodes.count.textContent = selection.total === 0 ? "No articles found" : "Showing " + ((state.page - 1) * PAGE_SIZE + 1) + "–" + Math.min(state.page * PAGE_SIZE, selection.total) + " of " + selection.total + " articles";
      if (state.q) nodes.count.textContent += ' for “' + state.q + '”';
      if (state.category) nodes.count.textContent += " · " + state.category;
      nodes.pagination.hidden = selection.pages === 1;
      nodes.previous.disabled = state.page === 1;
      nodes.next.disabled = state.page === selection.pages;
      nodes.pageLabel.textContent = "Page " + state.page + " of " + selection.pages;
      Array.from(host.querySelectorAll("[data-blog-reset]")).forEach(function (button) { button.hidden = !state.q && !state.category && state.page === 1; });
    }

    function commit(next, focusResults) {
      state = next;
      render();
      var url = stateUrl(state, window.location.href);
      if (url !== window.location.pathname + window.location.search + window.location.hash) window.history.pushState(null, "", url);
      if (focusResults) {
        nodes.title.focus({ preventScroll: true });
        nodes.title.scrollIntoView({ block: "start", behavior: "auto" });
      }
    }

    function reset() { commit({ q: "", category: "", page: 1 }, false); }
    listen(nodes.form, "submit", function (event) { event.preventDefault(); commit({ q: compact(nodes.query.value, 160), category: state.category, page: 1 }, false); });
    listen(nodes.query, "search", function () { if (!nodes.query.value) commit({ q: "", category: state.category, page: 1 }, false); });
    Array.from(host.querySelectorAll("[data-blog-reset]")).forEach(function (button) { listen(button, "click", reset); });
    listen(nodes.categories, "click", function (event) {
      var button = event.target.closest("button[data-category]");
      if (button && nodes.categories.contains(button)) commit({ q: compact(nodes.query.value, 160), category: button.dataset.category, page: 1 }, false);
    });
    listen(nodes.previous, "click", function () { commit({ q: state.q, category: state.category, page: Math.max(1, state.page - 1) }, true); });
    listen(nodes.next, "click", function () { commit({ q: state.q, category: state.category, page: state.page + 1 }, true); });
    listen(window, "popstate", function () { state = readState(window.location.href); render(); });

    async function load() {
      if (controller) controller.abort();
      window.clearTimeout(timer);
      controller = new AbortController();
      var requestController = controller;
      timer = window.setTimeout(function () { requestController.abort(); }, 20000);
      nodes.status.textContent = "Loading the searchable article index…";
      nodes.retry.hidden = true;
      try {
        var complete = await loadAllArticles(window.fetch.bind(window), { signal: requestController.signal });
        if (requestController.signal.aborted || controller !== requestController) return;
        articles = complete;
        var all = element(document, "button", "", "All articles");
        all.type = "button"; all.dataset.category = "";
        nodes.categories.replaceChildren(all);
        categoriesFor(articles).forEach(function (entry) {
          var button = element(document, "button", "", entry[0]);
          button.type = "button"; button.dataset.category = entry[0];
          button.append(element(document, "span", "b26-blog-filter-count", String(entry[1])));
          nodes.categories.append(button);
        });
        nodes.controls.hidden = false;
        nodes.status.textContent = "Search all " + articles.length + " published articles by title, topic or method.";
        render();
      } catch (_) {
        if (controller !== requestController) return;
        nodes.status.textContent = "The full article index could not load. Browse the articles below and use Older articles when available.";
        nodes.retry.hidden = false;
      } finally { if (controller === requestController) window.clearTimeout(timer); }
    }

    listen(nodes.retry, "click", load);
    listen(window, "pagehide", function () { if (controller) controller.abort(); window.clearTimeout(timer); });
    listen(window, "pageshow", function (event) { if (event.persisted && !articles) load(); });
    load();
    return { destroy: function () {
      if (controller) controller.abort(); window.clearTimeout(timer);
      listeners.forEach(function (remove) { remove(); }); delete host.dataset.blogMounted;
    } };
  }

  return { readState: readState, stateUrl: stateUrl, normalizeArticle: normalizeArticle, nextApiPath: nextApiPath,
    loadAllArticles: loadAllArticles, selectArticles: selectArticles, categoriesFor: categoriesFor, mount: mount };
});
