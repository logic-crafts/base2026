# Base2026 Growth, Indexation, and Lead Pipeline Plan — 2026-06-23

## Objective

Use Base2026 as the public knowledge/acquisition engine and Alex's personal site/contact form as the conversion endpoint. Do not build a separate blog for the personal site. Do not expose Telegram as a public CTA from Base2026.

## Current status

- Live release deployed: `base2026-topic-link-fallback-ay56b-20260623`.
- Live full crawl gate: PASS.
- Sitemap URLs: 1,577.
- Full bounded crawl: 1,700 pages.
- Status counts: 1,700 × 200.
- Internal link 404/errors: 0.
- Bad link contract count: 0.
- Remaining non-blocking warning: one canonical mismatch for `https://aggressorbulkit.online/ai-visibility-audit/?plan=diagnostic`, canonicalizing to `/ai-visibility-audit/`.

## Strategic split

### Base2026

Role: public research/knowledge engine.

Goals:
- earn crawl/indexation from unique TikTok/source intelligence;
- build topical authority around TikTok, local business growth, AI visibility, SEO/GEO/AEO, creator intelligence;
- route qualified readers to Alex's site/contact form.

Rules:
- no Telegram CTA/buttons in public Base2026 UI;
- use contact form / personal site / email path only;
- avoid thin pages in priority indexation pushes;
- maintain public/private hygiene through release gates.

### Alex personal site

Role: conversion hub.

Goals:
- explain offer and credibility;
- receive contact-form leads;
- host audit request path;
- reference Base2026 as proof/research engine.

Do not use it as a daily blog. Base2026 is the content engine.

### Local business prospecting pipeline

Role: outbound/client acquisition engine.

Existing automation:
- cron: `Daily Local Business TikTok Lead Finder — 09:00 Minsk`;
- job id: `1aeac60d8da8`;
- output: Agency OS + `data/tiktok_local_business_leads.csv`;
- scope: USA local businesses with TikTok + website + address/location.

Rules:
- no outreach without approval;
- no comments/DM/email before audit + copy approval;
- first qualify, then audit, then approval-gated outreach.

## Work plan

### Phase 1 — crawl/indexation foundation

Done:
- fix topic links that pointed to unpublished topic pages;
- deploy live release;
- verify full crawl: 0 internal 404/errors.

Next:
1. Review the remaining canonical warning for `/ai-visibility-audit/?plan=diagnostic`.
2. Build a priority indexation list from strong pages only:
   - `/knowledge/`;
   - top topic pages;
   - top source pages with strong insights;
   - methodology/source-policy/support pages;
   - selected creator/topic cluster pages.
3. Create a GSC-ready request set and avoid pushing weak/thin URLs first.

### Phase 2 — Base2026 acquisition UX/CTA

1. Add a modest author/contact CTA to Base2026:
   - “Want to talk to the author?”
   - “Request an AI/local visibility audit”
   - destination: personal site contact/audit form, not Telegram.
2. Keep CTA secondary to content so pages remain research-first.
3. Ensure all CTA URLs are crawl-safe and canonical-clean.

### Phase 3 — topical authority / internal linking

1. Select 5–10 priority clusters:
   - local business TikTok growth;
   - med spa/dental/pilates local growth;
   - AI visibility/GEO/AEO;
   - TikTok-to-website conversion;
   - Google Business/local SEO;
   - creator intelligence and source methodology.
2. For each cluster:
   - identify best topic page;
   - identify 10–30 supporting source pages;
   - add stronger related links;
   - ensure answer block + clear title/H1/meta/schema.

### Phase 4 — local business lead pipeline automation

1. Audit existing CSV leads and rank priority candidates.
2. Create a worker chain:
   - finder;
   - qualifier;
   - website/TikTok auditor;
   - personalized audit drafter;
   - outreach copy drafter;
   - approval gate;
   - contacted/follow-up logger.
3. First production batch: choose 5–10 high-fit businesses, create evidence-backed mini-audits, do not send until approved.

### Phase 5 — monitoring

Daily:
- run Local Business Lead Finder;
- check Base2026 crawl/index gate if public release changes;
- short report only when something meaningful changed.

Weekly:
- GSC indexation samples;
- sitemap health;
- top pages/clusters;
- lead pipeline conversion/status.

## Definition of working

Base2026 is working when:
- live crawl has 0 internal errors;
- priority pages are indexable and submitted/ready for GSC;
- CTA routes to form/site only;
- new source intelligence can enter public knowledge safely;
- outbound pipeline produces qualified audited prospects, not just raw leads.
