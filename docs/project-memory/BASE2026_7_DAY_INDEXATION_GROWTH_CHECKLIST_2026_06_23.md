# Base2026 — 7-day indexation/growth execution checklist

Date: 2026-06-23
Live baseline: `base2026-topic-link-fallback-ay56b-20260623`
Latest verified full crawl: `output/seo-crawl-gate/ay56b-full-20260623/summary.json`

## Baseline from the overnight check

- Full live crawl gate passed: 1,700 crawled pages, 1,577 sitemap URLs, all crawled pages `200`, bad link-contract count `0`, crawled error pages `0`.
- Only remaining warning: `https://aggressorbulkit.online/ai-visibility-audit/?plan=diagnostic` canonicalizes to `https://aggressorbulkit.online/ai-visibility-audit/`.
- This warning is from the WordPress/personal-site conversion page, not the Base2026 static `/knowledge/` app. Do not redeploy Base2026 for it.
- Public CTA boundary remains: no Telegram CTAs/buttons; route public visitors to Alex site/contact/audit form/email only.

## Day 1 — freeze clean baseline + GSC request set

1. Use `docs/project-memory/BASE2026_PRIORITY_INDEXATION_URLS_2026_06_23.csv` as the first GSC-ready set.
2. Submit only strong self-canonical pages first:
   - `https://aggressorbulkit.online/knowledge/`
   - `https://aggressorbulkit.online/knowledge/methodology.html`
   - `https://aggressorbulkit.online/knowledge/api.html`
   - `https://aggressorbulkit.online/knowledge/analytics.html`
   - `https://aggressorbulkit.online/knowledge/topics/`
   - `https://aggressorbulkit.online/knowledge/creators/`
   - `https://aggressorbulkit.online/knowledge/source-policy.html`
   - top topic/source/creator URLs from the CSV, not the full 1,577-page sitemap.
3. Do not submit noindex singleton/thin topic pages manually.
4. Before any new GSC/Ahrefs comparison, preserve the current passing crawl artifact path in notes so later regressions can be diffed against ay56b.

Acceptance check:

- Manual queue contains only URLs with `200`, canonical equal to URL, title/meta/H1 present, and no `noindex`.

## Day 2 — source archive/internal-link lift

1. Inspect `/knowledge/sources/`, `/knowledge/topics/`, `/knowledge/creators/`, and `/knowledge/analytics.html` as crawl hubs.
2. Add or plan only source-hub links that point to existing generated source pages; do not recreate the ay56 topic fallback issue.
3. Prioritize 20–40 high-value source pages with strong Source Intelligence and business-relevant topics:
   - local SEO / Google Business Profile;
   - AI visibility / AI citations;
   - content freshness / internal linking;
   - dental/medspa/local-service applicable sources.
4. If code changes are needed, regenerate static output locally and run the live/static link-contract gate before deploy.

Acceptance check:

- New/changed hub links resolve to `200`; no generated link points at unpublished topic/source pages.

## Day 3 — Base2026 → Alex conversion CTA audit

1. Review current Base2026 public CTAs on `/knowledge/`, info pages, topic/source/creator pages.
2. Ensure every conversion CTA goes to one of:
   - `/ai-visibility-audit/`
   - `/contact/` only if the live route exists and is intentionally public;
   - `mailto:offflinerpsy@gmail.com` where static mailto is already used.
3. Do not add Telegram links, Telegram usernames, Telegram buttons, or Telegram topic references to public UI.
4. Keep CTA secondary: Base2026 pages should remain research/source-first, with a modest author/audit path.

Acceptance check:

- Crawl query for public Base2026 HTML contains no Telegram CTA; all CTA routes return `200` and are canonical-clean or intentionally canonicalized by WordPress.

## Day 4 — cluster map for local business acquisition

Create a small operational cluster map from existing public pages:

| Cluster | Seed URL type | Supporting page types | Outcome |
| --- | --- | --- | --- |
| Local SEO / GBP | top topic pages | source pages + creator pages | GSC request set + internal links |
| AI visibility / AI citations | topic pages | source pages + `/knowledge/api.html` | proof pages for audit offer |
| TikTok-to-website conversion | source pages | creator/source intelligence | lead-audit evidence library |
| Medspa/dental local growth | source pages + external audit queue | Base2026 supporting evidence | audit talking points, no outreach yet |
| Methodology/trust | methodology/source-policy/API | story/support | credibility for source database |

Acceptance check:

- Each cluster has 1 index page, 5–15 support pages, and a clear next internal-link/action item.

## Day 5 — GSC/Ahrefs delta check, no blind fixes

1. Compare GSC indexed/not-indexed sample against the priority URL CSV.
2. Separate issues into:
   - Base2026 static app;
   - WordPress/personal-site;
   - external crawler cache/history;
   - not actionable yet.
3. Do not change sitemap/robots/canonical logic unless the issue is reproduced live with current HTML.
4. If Ahrefs still reports stale 404s after ay56b, use the ay56b full crawl as counter-evidence and wait for recrawl rather than changing working links.

Acceptance check:

- Every proposed fix names a live reproducible URL and layer owner.

## Day 6 — local-business audit queue integration

1. Use the latest Agency OS queue artifact: `04_Audits/2026-06-23-top-priority-audit-queue.md`.
2. For each top candidate, map one Base2026 supporting angle:
   - local SEO / GBP;
   - AI visibility;
   - service-page schema;
   - TikTok-to-booking path;
   - trust/review proof.
3. Produce audits only; do not send DMs/comments/emails.
4. Keep business contact paths private to the Agency OS lane; public Base2026 should not expose prospecting targets.

Acceptance check:

- 3 audit drafts ready for review, each with public evidence, no contact action, and an explicit approval gate.

## Day 7 — weekly gate + next release decision

1. Rerun a bounded live crawl only if public pages changed; otherwise reference ay56b full crawl.
2. If Base2026 code/docs changed, run:
   - `git diff --check`
   - `python3 scripts/audit-publication-boundary.py`
   - relevant static generation/link-contract checks
   - live crawl gate after deploy only if deploy was required.
3. Decide one of:
   - no release needed: continue GSC/manual indexation and audits;
   - docs-only commit candidate;
   - Base2026 static release candidate;
   - WordPress/personal-site task for canonical/CTA work.

Acceptance check:

- NEXT_ACTION.md points to one concrete next task, not a broad SEO bucket.
