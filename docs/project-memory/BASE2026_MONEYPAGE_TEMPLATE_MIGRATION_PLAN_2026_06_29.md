# Base2026 MoneyPage Template Migration Plan — Alex Site Style
Date: 2026-06-29

## Status
- Planning artifact only. No implementation, deploy, publish, GSC, Bing, or IndexNow action was performed.
- Purpose: prepare a safe template migration so Base2026 CTPH/MoneyPage pages stop looking technical/plain and inherit the Alex personal site visual language before further indexation/UGC amplification.

## Source references checked
- `home`: https://aggressorbulkit.online/ — HTTP 200; title: `Free AI Search Visibility Roadmap | SEO, GEO & AEO`
- `services`: https://aggressorbulkit.online/services/ — HTTP 200; title: `SEO, GEO & AEO Services for AI Search Visibility`
- `about`: https://aggressorbulkit.online/about/ — HTTP 200; title: `About Alex Yarosh | AI Search Visibility Consultant`
- `pricing`: https://aggressorbulkit.online/pricing/ — HTTP 200; title: `AI Search Visibility Pricing | SEO, GEO & AEO Packages`
- `roofing`: https://aggressorbulkit.online/knowledge/bing-seo-for-roofing-companies/ — HTTP 200; title: `Bing SEO for Roofing Companies | Base2026`
- `hvac`: https://aggressorbulkit.online/knowledge/bing-seo-for-hvac-companies/ — HTTP 200; title: `Bing SEO for HVAC Companies | Base2026`
- `audit`: https://aggressorbulkit.online/knowledge/ai-visibility-audit-for-local-service-businesses/ — HTTP 200; title: `AI Visibility Audit for Local Service Businesses | Base2026`

## Observed Alex-site direction to preserve
- Warm editorial consulting/product style: off-white background, paper cards, orange CTA, dark primary text, compact proof cards.
- Strong designed sections, not long SEO text walls.
- Services/pricing/about/home communicate as a coherent Alex Yarosh system; Base2026 pages should feel like part of the same funnel.
- Preserve existing orange Base2026 cards, aligned CTA cards/forms, and visual section rhythm.

## Current Base2026 issue
- Priority generated money pages are technically indexable but visually read as guide/technical pages.
- They need a reusable commercial template before more aggressive LinkedIn/UGC, GSC/Bing follow-up, or larger page expansion.

## Proposed master page skeleton
1. **Hero / commercial promise** — Niche-specific headline, short AI/Bing/Copilot visibility promise, primary CTA, secondary proof link. No generic SEO-wall intro.
2. **Trust/proof strip** — Small cards using Base2026 evidence/source intelligence language: crawlability, answer clarity, proof, internal links, conversion readiness.
3. **Problem / why this page exists** — Explain why the niche is under-visible in Bing/Copilot/AI answers; concise and commercial.
4. **Diagnostic checklist** — Designed cards/checklist, not a raw bullet dump: technical crawl, service proof, content quality, reviews, internal links, lead path.
5. **Source Intelligence / evidence cards** — Show reviewed public source/evidence where available; keep raw/private TikTok out. Human-readable summary first.
6. **Offer / CTA panel** — Bridge to Alex audit/roadmap/pricing. Use orange primary action and warm card/form treatment.
7. **Related priority crawl path** — Visible related links to 4–10 priority pages; keep sitemap/internal-link value without making it look like a footer dump.
8. **FAQ** — 4–6 short conversion/support questions, tailored by niche; avoid bloated SEO paragraphs.
9. **Final CTA** — Simple designed closing block: audit/roadmap/pricing route.

## Pilot pages
- `/knowledge/bing-seo-for-roofing-companies/`
- `/knowledge/bing-seo-for-hvac-companies/`
- `/knowledge/bing-seo-for-law-firms/`
- `/knowledge/ai-visibility-audit-for-local-service-businesses/`
- `/knowledge/service-area-pages-and-ai-visibility-for-local-businesses/`

## Acceptance checks before any deploy
- [ ] Preview generated locally for the 5 pilot pages
- [ ] Desktop and mobile visual QA screenshots taken
- [ ] HTTP/preview pages remain index,follow
- [ ] Canonical/self URL unchanged
- [ ] Exactly one primary H1
- [ ] CTA visible above fold and near page end
- [ ] Related priority links visible and useful
- [ ] Draft city/niche pages remain noindex,nofollow
- [ ] No private/source-review TikTok data leaked
- [ ] git diff scoped to template/generator/style/docs only

## Next quiet-work steps
1. Wait for or retrieve the Alex Personal Site template/spec from topic 107 if it arrives.
2. Map the exact generator/CSS files that create Base2026 AI visibility/money pages.
3. Draft a non-deployed local template candidate for the 5 pilot pages.
4. Run preview QA and report only when there is a concrete preview/evidence or blocker.

## Live heading/class evidence snapshot

### home
Headings:
- h1: Get your free AI search roadmap without agency theater.
- h2: Get the roadmap before spending on more SEO.
- h3: Check My Visibility
- h2: What happens after the request.
- h3: We check your market
- h3: We build your plan
- h3: We get to work
- h2: Built for local service businesses where visibility turns into leads.
- h3: Good fit
- h2: Search visibility for local service businesses
Relevant classes seen:
- site-header__cta, site-header__mobile-panel, site-header__mobile-cta, b26-about-hero, ay-about-contact-hero, alex-native-hero, b26-about-hero-copy, ay-about-contact-hero-copy, ay-founder-quote, alex-services-divider-heavy, alex-services-form-head, alex-core-stitch-card-grid, alex-core-stitch-card, ay-wrap, ay-footer-grid, ay-actions, ay-button, ay-button-secondary

### services
Headings:
- h1: Start with the layer that blocks visibility.
- h2: Check my visibility before choosing a package.
- h3: Check My Visibility
- h2: Five repair layers.One visibility system.
- h2: Each service connects to proof.
- h3: Good fit
- h2: Search visibility for local service businesses
- h3: Services
- h3: Start Here
- h3: Base2026 Pilot Project
Relevant classes seen:
- site-header__cta, site-header__mobile-panel, site-header__mobile-cta, b26-about-hero, ay-about-contact-hero, alex-native-hero, alex-services-hero-cover, b26-about-hero-copy, ay-about-contact-hero-copy, ay-founder-quote, alex-services-stitch-intro, alex-services-stitch-main, alex-services-divider-heavy, alex-services-stitch-two-col, alex-services-request-block, alex-services-stitch-entry, alex-services-request-copy, alex-services-form-card

### about
Headings:
- h1: AI visibility repair for local service businesses.
- h2: No fake hacks. No random posts. No mystery dashboards.
- h3: Clarity first
- h3: Proof before spend
- h3: Measured repair
- h2: Visibility systems that buyers and AI systems can understand.
- h3: Focus
- h2: Send the website and the visibility problem.
- h3: Contact Alex
- h2: Search visibility for local service businesses
Relevant classes seen:
- site-header__cta, site-header__mobile-panel, site-header__mobile-cta, b26-about-hero, ay-about-contact-hero, alex-native-hero, b26-about-hero-copy, ay-about-contact-hero-copy, ay-founder-quote, alex-services-divider-heavy, alex-core-stitch-card-grid, alex-core-stitch-card, alex-services-form-head, ay-wrap, ay-footer-grid, ay-actions, ay-button, ay-button-secondary

### pricing
Headings:
- h1: AI Search Visibility pricing without guesswork.
- h2: Pick the level of help you need now.
- h3: AI Visibility Snapshot
- h3: AI Visibility Diagnostic Audit
- h3: 90-Day AI Search Visibility Sprint
- h3: Monthly Growth Support
- h2: Send the site and I’ll point you to the right package.
- h3: Ask about the right option
- h2: Search visibility for local service businesses
- h3: Services
Relevant classes seen:
- site-header__cta, site-header__mobile-panel, site-header__mobile-cta, b26-about-hero, ay-about-contact-hero, alex-native-hero, b26-about-hero-copy, ay-about-contact-hero-copy, ay-founder-quote, alex-pricing-stitch-intro, alex-services-divider-heavy, alex-pricing-stitch-packages, alex-pricing-stitch-grid, alex-pricing-stitch-card, alex-pricing-stitch-actions, ay-button, alex-pricing-contact-block, alex-services-form-head

### roofing
Headings:
- h1: Bing SEO for Roofing Companies
- h2: Search intent
- h2: Bing and Copilot checks
- h2: Business page pattern
- h2: Internal linking plan
- h2: Practical review questions
- h2: How this maps to business work
- h2: Recommended workflow
- h3: 1. Check what search and AI can understand
- h3: 2. Identify the weak layer
Relevant classes seen:
- site-header__cta, site-header__mobile-panel, site-header__mobile-cta, b26-about-hero, ay-about-contact-hero, b26-about-hero-copy, ay-about-contact-hero-copy, ay-founder-quote, ay-contact-layout, ay-contact-layout-compact, b26-card, b26-contact-form-card, ay-card, ay-contact-form-card, b26-calendar-booking-card, ay-calendar-booking-card, ay-button, ay-button-small

### hvac
Headings:
- h1: Bing SEO for HVAC Companies
- h2: Search intent
- h2: Bing and Copilot checks
- h2: Business page pattern
- h2: Internal linking plan
- h2: Practical review questions
- h2: How this maps to business work
- h2: Recommended workflow
- h3: 1. Check what search and AI can understand
- h3: 2. Identify the weak layer
Relevant classes seen:
- site-header__cta, site-header__mobile-panel, site-header__mobile-cta, b26-about-hero, ay-about-contact-hero, b26-about-hero-copy, ay-about-contact-hero-copy, ay-founder-quote, ay-contact-layout, ay-contact-layout-compact, b26-card, b26-contact-form-card, ay-card, ay-contact-form-card, b26-calendar-booking-card, ay-calendar-booking-card, ay-button, ay-button-small

### audit
Headings:
- h1: AI Visibility Audit for Local Service Businesses
- h2: The problem
- h2: What the audit looks at
- h2: What most generic pages miss
- h2: How Base2026 makes this useful
- h2: Fast self-check
- h2: Suggested next step
- h2: How this maps to business work
- h2: Recommended workflow
- h3: 1. Check what search and AI can understand
Relevant classes seen:
- site-header__cta, site-header__mobile-panel, site-header__mobile-cta, b26-about-hero, ay-about-contact-hero, b26-about-hero-copy, ay-about-contact-hero-copy, ay-founder-quote, ay-contact-layout, ay-contact-layout-compact, b26-card, b26-contact-form-card, ay-card, ay-contact-form-card, b26-calendar-booking-card, ay-calendar-booking-card, ay-button, ay-button-small
