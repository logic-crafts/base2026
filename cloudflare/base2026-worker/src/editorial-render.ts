/** Text-only DTOs become public HTML here, never arbitrary author HTML. */
import catalog from "./editorial-catalog.json";
import {
  EDITORIAL_ORIGIN,
  editorialArticlePath,
  type EditorialHero,
  type EditorialPayload,
  type StoredEditorialArticle,
} from "./editorial";

export interface EditorialSummary {
  id: string;
  path: string;
  title: string;
  description: string;
  category: string;
  published_at: string;
  updated_at: string;
  author: string;
  hero?: EditorialHero;
}

export const LEGACY_EDITORIAL_CATALOG: readonly EditorialSummary[] = catalog;
const DEFAULT_IMAGE = "/static/assets/base2026-ai-visibility-card.png";
const XML_HEADER = '<?xml version="1.0" encoding="UTF-8"?>\n';
const DATE_FORMAT = new Intl.DateTimeFormat("en-US", {
  year: "numeric", month: "long", day: "numeric", timeZone: "UTC",
});

export function editorialEscape(value: string): string {
  return value.replace(/[&<>"']/gu, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]!);
}

function truncateEditorialTitle(value: string, limit: number): string {
  const compact = value.replace(/\s+/gu, " ").trim();
  if (compact.length <= limit) return compact;
  return compact.slice(0, Math.max(0, limit - 1)).trimEnd() + "…";
}

export function editorialJson(value: unknown): string {
  return JSON.stringify(value).replace(/</gu, "\\u003c").replace(/>/gu, "\\u003e")
    .replace(/&/gu, "\\u0026").replace(/\u2028/gu, "\\u2028").replace(/\u2029/gu, "\\u2029");
}

export function editorialDate(value: string): string {
  return DATE_FORMAT.format(new Date(value));
}

export function articleSummary(article: StoredEditorialArticle): EditorialSummary {
  const payload = article.payload;
  return {
    id: payload.slug, path: article.public_path, title: payload.title,
    description: payload.description, category: payload.category,
    published_at: payload.published_at, updated_at: payload.updated_at,
    author: payload.author.name, ...(payload.hero ? { hero: payload.hero } : {}),
  };
}

export function sortEditorialSummaries(articles: readonly EditorialSummary[]): EditorialSummary[] {
  const seen = new Set<string>();
  return [...articles].sort((a, b) =>
    Date.parse(b.published_at) - Date.parse(a.published_at) || a.id.localeCompare(b.id),
  ).filter((article) => {
    if (seen.has(article.path)) return false;
    seen.add(article.path);
    return true;
  });
}

function imageMarkup(hero: EditorialHero, className: string): string {
  // Dimensions are measured from reviewed assets, never guessed from a URL.
  // Add each new illustration here as part of its explicit asset release.
  const dimensions: Record<string, readonly [number, number]> = {
    "/static/assets/base2026-source-diversity.png": [1254, 1254],
    "/static/assets/base2026-ai-visibility-measurement.png": [1536, 1024],
  };
  const size = dimensions[hero.path];
  return '<figure class="' + className + '"><img src="' + editorialEscape(hero.path)
    + '" alt="' + editorialEscape(hero.alt) + '"'
    + (size ? ' width="' + size[0] + '" height="' + size[1] + '"' : "")
    + ' loading="eager" fetchpriority="high">'
    + "<figcaption>" + editorialEscape(hero.credit)
    + (hero.ai_generated && !/AI[- ]generated/iu.test(hero.credit)
      ? " AI-generated editorial illustration." : "") + "</figcaption></figure>";
}

export function renderEditorialCard(article: EditorialSummary, featured = false): string {
  const family = article.path.startsWith("/journal/") ? "journal-" : "article-";
  const headingId = "blog-" + (featured ? "feature-" : "card-") + family + article.id;
  const heading = featured ? "h2" : "h3";
  const meta = '<p class="b26-blog-card__meta"><span class="b26-blog-card__category">'
    + editorialEscape(article.category) + '</span><time datetime="'
    + editorialEscape(article.published_at) + '">' + editorialDate(article.published_at) + "</time></p>";
  const copy = meta + "<" + heading + ' class="b26-blog-card__title" id="' + editorialEscape(headingId)
    + '">' + editorialEscape(article.title) + "</" + heading + '><p class="b26-blog-card__excerpt">'
    + editorialEscape(article.description) + '</p><div class="b26-blog-card__footer">'
    + '<span class="b26-blog-card__byline">' + editorialEscape(article.author) + "</span>"
    + '<span class="b26-blog-card__read">Read article <span aria-hidden="true">→</span></span></div>';
  const className = featured
    ? "b26-blog-feature" + (article.hero ? "" : " b26-blog-feature--text-only")
    : "b26-blog-card";
  return '<article class="' + className + '"><a class="b26-blog-card__link" href="'
    + editorialEscape(article.path) + '" aria-labelledby="' + editorialEscape(headingId) + '">'
    + (featured ? '<div class="b26-blog-feature__body">' + copy + "</div>" : copy)
    + (featured && article.hero ? imageMarkup(article.hero, "b26-blog-feature__media") : "")
    + "</a></article>";
}

export function blogSchema(articles: readonly EditorialSummary[]): unknown {
  return {
    "@context": "https://schema.org",
    "@graph": [{
      "@type": "CollectionPage", "@id": EDITORIAL_ORIGIN + "/blog#page",
      url: EDITORIAL_ORIGIN + "/blog", name: "Base2026 Blog",
      mainEntity: { "@id": EDITORIAL_ORIGIN + "/blog#blog" },
    }, {
      "@type": "Blog", "@id": EDITORIAL_ORIGIN + "/blog#blog",
      name: "Base2026 Blog", url: EDITORIAL_ORIGIN + "/blog",
      blogPost: articles.map((article) => ({
        "@type": "BlogPosting", headline: article.title, url: EDITORIAL_ORIGIN + article.path,
        datePublished: article.published_at, dateModified: article.updated_at,
        author: { "@type": "Person", name: article.author, url: EDITORIAL_ORIGIN + "/founder" },
      })),
    }],
  };
}

function replaceOne(source: string, pattern: RegExp, replacement: string): string {
  const matches = [...source.matchAll(new RegExp(pattern.source, pattern.flags.includes("g") ? pattern.flags : pattern.flags + "g"))];
  if (matches.length !== 1) throw new Error("EDITORIAL_SHELL_INVALID");
  return source.replace(pattern, () => replacement);
}

function replaceRegion(shell: string, name: string, value: string): string {
  const start = "<!--B26_BLOG_" + name + "_START-->";
  const end = "<!--B26_BLOG_" + name + "_END-->";
  if (shell.split(start).length !== 2 || shell.split(end).length !== 2) {
    throw new Error("EDITORIAL_SHELL_INVALID");
  }
  return replaceOne(shell, new RegExp(start + "[\\s\\S]*?" + end, "u"), start + value + end);
}

export function renderEditorialHub(
  shell: string, articles: readonly EditorialSummary[], nextHref: string | null = null,
): string {
  const feature = articles[0];
  let result = replaceRegion(shell, "FEATURED", feature ? renderEditorialCard(feature, true) : "");
  const more = articles.slice(1).map((article) => renderEditorialCard(article)).join("");
  result = replaceRegion(result, "CARDS", more
    + (nextHref ? '<nav aria-label="Blog pagination"><a class="b26-blog-text-link" rel="next" href="'
      + editorialEscape(nextHref) + '">Older articles →</a></nav>' : ""));
  result = replaceRegion(result, "TOPIC_LINKS",
    '<a href="/topics/">Browse source topics</a><a href="/methodology">Research methodology</a>');
  return replaceOne(result, /<script type="application\/ld\+json" data-b26-blog-schema>[\s\S]*?<\/script>/u,
    '<script type="application/ld+json" data-b26-blog-schema>' + editorialJson(blogSchema(articles)) + "</script>");
}

function citations(ids: readonly string[], payload: EditorialPayload): string {
  return ids.map((id) => {
    const index = payload.sources.findIndex((source) => source.id === id);
    if (index < 0) throw new Error("EDITORIAL_CITATION_INVALID");
    return '<a class="b26-article-citation" href="#source-' + editorialEscape(id)
      + '" aria-label="Source ' + (index + 1) + '">' + (index + 1) + "</a>";
  }).join(" ");
}

function relatedLabel(path: string): string {
  const exact = LEGACY_EDITORIAL_CATALOG.find((article) => article.path === path);
  if (exact) return exact.title;
  const known: Record<string, string> = {
    "/blog": "More research notes", "/methodology": "How Base2026 prepares evidence",
    "/dataset": "Explore the public dataset", "/api": "Use the public API",
    "/about": "About Base2026", "/roadmap": "What works and what is next",
    "/opt-out": "Creator corrections and removal", "/topics/": "Browse research topics",
    "/creators/": "Explore source creators", "/sources/": "Browse source records",
  };
  if (known[path]) return known[path];
  return path.split("/").filter(Boolean).at(-1)!.replace(/-/gu, " ");
}

function renderGuideDecisionRecord(payload: EditorialPayload): string {
  if (!payload.evidence) throw new Error("GUIDE_EVIDENCE_REQUIRED");
  const canonical = EDITORIAL_ORIGIN + editorialArticlePath(payload.slug, payload.kind);
  return '<section id="guide-decision-record" class="b26-guide-record" data-b26-guide-decision'
    + ' data-guide-url="' + editorialEscape(canonical) + '" data-guide-revision="' + payload.revision
    + '" data-guide-updated="' + editorialEscape(payload.updated_at) + '" aria-labelledby="guide-record-title">'
    + '<p class="b26-blog-eyebrow">One target. One decision.</p><h2 id="guide-record-title">Make a decision record</h2>'
    + '<p class="b26-guide-task">' + editorialEscape(payload.evidence.user_task) + '</p>'
    + '<p id="guide-record-privacy" class="b26-guide-record-note">Your entries stay in this tab. Nothing is sent or saved by this tool. '
    + 'URLs are not fetched or crawled. Copy or download your record before leaving.</p>'
    + '<fieldset class="b26-guide-record-fields" aria-describedby="guide-record-privacy"><legend>Record your own assessment</legend>'
    + '<div class="b26-guide-field"><label for="b26-guide-target">Target URL</label><p id="guide-target-help">The page that could receive the link.</p>'
    + '<input id="b26-guide-target" type="url" inputmode="url" autocomplete="off" spellcheck="false" maxlength="2048" aria-describedby="guide-target-help" required></div>'
    + '<div class="b26-guide-field"><label for="b26-guide-source">Proposed source URL</label><p id="guide-source-help">The page that could link to the target.</p>'
    + '<input id="b26-guide-source" type="url" inputmode="url" autocomplete="off" spellcheck="false" maxlength="2048" aria-describedby="guide-source-help" required></div>'
    + '<div class="b26-guide-field"><label for="b26-guide-decision">Decision</label><select id="b26-guide-decision" required>'
    + '<option value="">Choose a decision</option><option value="add">Add a link</option>'
    + '<option value="context">Improve its context</option><option value="repair">Repair an existing link</option>'
    + '<option value="no-change">Make no change</option></select></div>'
    + '<div class="b26-guide-field"><label for="b26-guide-rationale">Rationale</label><p id="guide-rationale-help">What reader need supports this decision? Record uncertainty too.</p>'
    + '<textarea id="b26-guide-rationale" rows="4" maxlength="1600" autocomplete="off" aria-describedby="guide-rationale-help" required></textarea></div>'
    + '<div class="b26-guide-field"><label for="b26-guide-verification">Verification</label><p id="guide-verification-help">What did you check, or what still needs checking?</p>'
    + '<textarea id="b26-guide-verification" rows="4" maxlength="1600" autocomplete="off" aria-describedby="guide-verification-help" required></textarea></div></fieldset>'
    + '<div class="b26-guide-record-actions"><button type="button" class="b26-button--primary" data-guide-copy hidden>Copy record</button>'
    + '<button type="button" class="b26-button--secondary" data-guide-download hidden>Download CSV</button></div>'
    + '<p class="b26-guide-record-status" data-guide-status role="status" aria-live="polite" aria-atomic="true"></p>'
    + '<noscript><p>Copy and download need JavaScript. You can still use these fields, copy the text manually, or print a blank record.</p></noscript>'
    + '<dl class="b26-guide-record-preview" data-guide-print hidden><dt>Target URL</dt><dd data-print-target>Not entered</dd>'
    + '<dt>Proposed source URL</dt><dd data-print-source>Not entered</dd><dt>Decision</dt><dd data-print-decision>Not selected</dd>'
    + '<dt>Rationale</dt><dd data-print-rationale>Not entered</dd><dt>Verification</dt><dd data-print-verification>Not entered</dd></dl></section>';
}

function renderGuideEvidence(payload: EditorialPayload): string {
  if (!payload.evidence) throw new Error("GUIDE_EVIDENCE_REQUIRED");
  return '<section id="guide-evidence" class="b26-guide-evidence" aria-labelledby="guide-evidence-title">'
    + '<h2 id="guide-evidence-title">Evidence for this task</h2>'
    + '<p>Selected short excerpts, with their role in this guide. A prerequisite is an adjacent check, not direct support for the decision. '
    + 'Read the linked source for context; source counts are not proof votes.</p><ol>'
    + payload.evidence.dependencies.map((dependency) => '<li class="b26-guide-evidence-item">'
      + '<p class="b26-guide-evidence-relation">' + (dependency.relation === "direct" ? "Direct support" : "Adjacent prerequisite")
      + " " + citations([dependency.citation_id], payload) + '</p><blockquote><p>' + editorialEscape(dependency.quote)
      + '</p></blockquote><details><summary>Public document ID</summary><code>' + editorialEscape(dependency.document_id)
      + '</code></details></li>').join("") + '</ol></section>';
}

export function renderEditorialArticleBody(article: StoredEditorialArticle): string {
  const payload = article.payload;
  const guide = payload.kind === "evidence_guide";
  const linkDecision = guide && payload.slug === "internal-linking";
  const contents = payload.sections.map((section) => '<li><a href="#section-' + editorialEscape(section.id)
    + '">' + editorialEscape(section.heading) + "</a></li>").join("");
  const sections = payload.sections.map((section) =>
    '<section id="section-' + editorialEscape(section.id) + '"><h2>'
    + editorialEscape(section.heading) + "</h2>"
    + section.blocks.map((block) => block.type === "paragraph"
      ? "<p>" + editorialEscape(block.text) + (block.citation_ids.length ? " " + citations(block.citation_ids, payload) : "") + "</p>"
      : "<ul>" + block.items.map((item) => "<li>" + editorialEscape(item.text)
        + (item.citation_ids.length ? " " + citations(item.citation_ids, payload) : "") + "</li>").join("") + "</ul>",
    ).join("") + "</section>",
  ).join("");
  const sourceList = payload.sources.map((source) => '<li id="source-' + editorialEscape(source.id)
    + '"><a href="' + editorialEscape(source.url) + '" rel="noopener noreferrer">'
    + editorialEscape(source.title) + '</a><p class="b26-article-source-meta">'
    + (source.creator ? editorialEscape(source.creator) + ". " : "")
    + (source.published_at ? "Published " + editorialDate(source.published_at) + ". " : "")
    + 'Checked <time datetime="' + editorialEscape(source.checked_at) + '">'
    + editorialDate(source.checked_at) + "</time>.</p></li>").join("");
  return '<article><nav class="b26-article-breadcrumb" aria-label="Breadcrumb">'
    + (guide ? '<a href="/topics/">Topics</a>' : '<a href="/blog">Blog</a>')
    + '<span aria-hidden="true"> / </span><span>' + editorialEscape(payload.category) + "</span></nav>"
    + '<header class="b26-article-header"><p class="b26-blog-eyebrow">' + editorialEscape(payload.category) + "</p>"
    + "<h1>" + editorialEscape(payload.title) + '</h1><p class="b26-article-lede">' + editorialEscape(payload.lede)
    + '</p><p class="b26-article-meta"><a href="/founder">' + editorialEscape(payload.author.name)
    + '</a><span>Published <time datetime="' + editorialEscape(payload.published_at) + '">'
    + editorialDate(payload.published_at) + "</time></span>"
    + (guide || payload.updated_at !== payload.published_at ? '<span>Updated <time datetime="'
      + editorialEscape(payload.updated_at) + '">' + editorialDate(payload.updated_at) + "</time></span>" : "")
    + "</p></header>" + (payload.hero ? imageMarkup(payload.hero, "b26-article-hero") : "")
    + '<div class="b26-article-layout"><aside class="b26-article-toc" aria-label="In this ' + (guide ? "guide" : "article") + '">'
    + "<h2>In this " + (guide ? "guide" : "article") + "</h2><ol>"
    + (linkDecision ? '<li><a href="#guide-decision-record">Make a decision record</a></li>' : "") + contents
    + (guide ? '<li><a href="#guide-evidence">Evidence for this task</a></li>' : "")
    + '<li><a href="#article-sources">Sources</a></li></ol></aside>'
    + '<div class="b26-article-body">' + (linkDecision ? renderGuideDecisionRecord(payload) : "") + sections
    + (guide ? renderGuideEvidence(payload) : "")
    + '<section id="article-sources" class="b26-article-sources"><h2>Sources and checks</h2>'
    + "<p>Links support the statements cited above. Different URLs do not automatically mean independent evidence.</p>"
    + "<ol>" + sourceList + "</ol></section>"
    + '<aside class="b26-article-disclosure" aria-labelledby="article-disclosure-title"><h2 id="article-disclosure-title">How this '
    + (guide ? "guide" : "note") + ' was prepared</h2>'
    + "<p>" + editorialEscape(payload.ai_assistance_disclosure) + "</p>"
    + (payload.first_party_context ? "<p>" + editorialEscape(payload.first_party_context) + "</p>" : "") + "</aside>"
    + (payload.related_paths.length ? '<nav class="b26-article-related" aria-labelledby="article-related-title">'
      + '<h2 id="article-related-title">Continue the research</h2><ul>' + payload.related_paths.map((path) =>
        '<li><a href="' + editorialEscape(path) + '">' + editorialEscape(relatedLabel(path)) + "</a></li>",
      ).join("") + "</ul></nav>" : "") + "</div></div></article>"
    + '<aside class="b26-blog-bridge" aria-labelledby="blog-bridge-title"><div>'
    + '<p class="b26-blog-eyebrow">Read, then investigate</p>'
    + '<h2 id="blog-bridge-title">Keep the source in view.</h2>'
    + "<p>Search the public evidence library, follow the original material, and see how each record is prepared.</p>"
    + '</div><div class="b26-blog-bridge__actions"><a class="b26-button--primary" href="/workspace/">'
    + 'Try evidence search <span aria-hidden="true">→</span></a>'
    + '<a class="b26-blog-text-link" href="/methodology">Read the methodology <span aria-hidden="true">→</span></a>'
    + "</div></aside>";
}

export function renderEditorialArticle(shell: string, article: StoredEditorialArticle): string {
  const payload = article.payload;
  const guide = payload.kind === "evidence_guide";
  const canonical = EDITORIAL_ORIGIN + editorialArticlePath(payload.slug, payload.kind);
  let result = replaceOne(shell, /<main id="b26-blog-main"[^>]*>[\s\S]*?<\/main>/u,
    '<main id="b26-blog-main" class="b26-blog-article' + (guide ? " b26-evidence-guide" : "") + '">'
    + renderEditorialArticleBody(article) + "</main>");
  // Article pages reuse the index shell, but only the index needs corpus
  // discovery. Keep article reading free of the unrelated index enhancement.
  result = result.replace(/<script src="\/static\/base2026-blog-discovery\.js(?:\?[^"<>]*)?" defer><\/script>\s*/gu, "");
  const browserTitle = truncateEditorialTitle(payload.title + " | Base2026", 65);
  result = replaceOne(result, /<title>[\s\S]*?<\/title>/u, "<title>" + editorialEscape(browserTitle) + "</title>");
  result = replaceOne(result, /<link rel="canonical" href="[^"]*">/u, '<link rel="canonical" href="' + canonical + '">');
  for (const [attribute, name, value] of [
    ["name", "description", payload.description],
    ["property", "og:type", "article"], ["property", "og:title", payload.title],
    ["property", "og:description", payload.description], ["property", "og:url", canonical],
    ["property", "og:image", EDITORIAL_ORIGIN + (payload.hero?.path ?? DEFAULT_IMAGE)],
    ["property", "og:image:alt", payload.hero?.alt ?? "Base2026 public-source intelligence"],
    ["name", "twitter:title", payload.title], ["name", "twitter:description", payload.description],
    ["name", "twitter:image", EDITORIAL_ORIGIN + (payload.hero?.path ?? DEFAULT_IMAGE)],
    ["name", "twitter:image:alt", payload.hero?.alt ?? "Base2026 public-source intelligence"],
  ]) {
    result = replaceOne(result, new RegExp('<meta ' + attribute + '="' + name + '" content="[^"]*">', "u"),
      "<meta " + attribute + '="' + name + '" content="' + editorialEscape(value) + '">');
  }
  // Inherited default-card dimensions must never describe a different illustration.
  result = result.replace(/<meta property="og:image:(?:width|height)" content="[^"]*">\s*/gu, "");
  const schema = {
    "@context": "https://schema.org", "@graph": [{
      "@type": guide ? "TechArticle" : "BlogPosting", "@id": canonical + (guide ? "#guide" : "#article"), url: canonical, mainEntityOfPage: canonical,
      headline: payload.title, description: payload.description, datePublished: payload.published_at,
      dateModified: payload.updated_at, inLanguage: "en", isAccessibleForFree: true,
      author: { "@type": "Person", name: payload.author.name, url: EDITORIAL_ORIGIN + "/founder" },
      publisher: { "@type": "Organization", name: "Base2026", url: EDITORIAL_ORIGIN + "/" },
      image: EDITORIAL_ORIGIN + (payload.hero?.path ?? DEFAULT_IMAGE),
      citation: payload.sources.map((source) => source.url),
    }, {
      "@type": "BreadcrumbList", itemListElement: [
        { "@type": "ListItem", position: 1, name: guide ? "Base2026 topics" : "Base2026 Blog", item: EDITORIAL_ORIGIN + (guide ? "/topics/" : "/blog") },
        { "@type": "ListItem", position: 2, name: payload.title, item: canonical },
      ],
    }],
  };
  result = replaceOne(result, /<script type="application\/ld\+json" data-b26-blog-schema>[\s\S]*?<\/script>/u,
    '<script type="application/ld+json" data-b26-blog-schema>' + editorialJson(schema) + "</script>");
  if (guide) {
    result = result.replace('href="#b26-blog-main">Skip to blog</a>', 'href="#b26-blog-main">Skip to guide</a>')
      .replace(/<link rel="alternate" type="application\/rss\+xml" title="Base2026 Blog" href="\/blog\/feed\.xml">\s*/u, "");
  }
  return result.replace("</head>",
    '<link rel="stylesheet" href="/static/base2026-blog-article.css?v=20260830-blog-v1">'
    + (guide ? '<link rel="stylesheet" href="/static/base2026-evidence-guide.css?v=20260830-guide-v1">'
      + '<script src="/static/base2026-evidence-guide.js?v=20260830-guide-v1" defer></script>' : "")
    + '<meta property="article:published_time" content="' + editorialEscape(payload.published_at) + '">'
    + '<meta property="article:modified_time" content="' + editorialEscape(payload.updated_at) + '"></head>');
}

export function renderEditorialFeed(articles: readonly EditorialSummary[]): string {
  return XML_HEADER + '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>'
    + "<title>Base2026 Blog</title><link>" + EDITORIAL_ORIGIN + "/blog</link>"
    + "<description>Research methods and engineering notes. Sources included.</description>"
    + '<language>en</language><atom:link href="' + EDITORIAL_ORIGIN + '/blog/feed.xml" rel="self" type="application/rss+xml"/>'
    + articles.map((article) => "<item><title>" + editorialEscape(article.title) + "</title>"
      + "<link>" + EDITORIAL_ORIGIN + editorialEscape(article.path) + "</link>"
      + '<guid isPermaLink="true">' + EDITORIAL_ORIGIN + editorialEscape(article.path) + "</guid>"
      + "<description>" + editorialEscape(article.description) + "</description>"
      + "<pubDate>" + new Date(article.published_at).toUTCString() + "</pubDate></item>").join("")
    + "</channel></rss>\n";
}

export function renderEditorialSitemapIndex(pageCount: number): string {
  return XML_HEADER + '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    + Array.from({ length: pageCount }, (_, index) => "<sitemap><loc>" + EDITORIAL_ORIGIN
      + "/sitemaps/blog-" + (index + 1) + ".xml</loc></sitemap>").join("") + "</sitemapindex>\n";
}

export function renderEditorialSitemap(rows: readonly { slug: string; updated_at: string }[]): string {
  return XML_HEADER + '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    + rows.map((row) => "<url><loc>" + EDITORIAL_ORIGIN + editorialArticlePath(row.slug)
      + "</loc><lastmod>" + editorialEscape(row.updated_at) + "</lastmod></url>").join("") + "</urlset>\n";
}
