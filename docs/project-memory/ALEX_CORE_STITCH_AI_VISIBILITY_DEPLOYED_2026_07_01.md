# Alex / Base2026 AI Visibility Funnel — Core-Stitch Deploy Report

Date: 2026-07-01
Release: `alex-core-stitch-ai-visibility-20260701a`
Live site: https://aggressorbulkit.online/

## What changed

Mapped the ChatGPT Pro AI Visibility content batch into the accepted `alex-core-stitch` visual layer instead of the rejected generic/card-heavy template.

Updated live pages:

- `/`
- `/services/`
- `/ai-visibility-audit/`
- `/pricing/`
- `/sample-ai-visibility-snapshot/`
- `/ai-visibility-audit-for-dentists/`
- `/ai-visibility-audit-for-roofing-companies/`
- `/ai-visibility-audit-for-hvac-companies/`
- `/ai-visibility-audit-for-plumbing-companies/`
- `/ai-visibility-audit-for-law-firms/`
- `/thank-you-ai-visibility-audit/`

## Guardrails respected

- Preserved accepted orange/core-stitch visual system.
- Did not use rejected `alex-native-intro` / generic card-heavy template classes.
- No live placeholder prices: no `$499`, no `[PRICE NEEDED]`.
- Removed stale public roadmap language from the funnel pages checked.
- Thank-you page is `noindex,follow` and excluded from sitemap.
- `www` redirects to apex.
- `/knowledge` redirects to `/knowledge/`.
- Did not submit a real test lead/email.

## Preview QA before deploy

Local preview server: `http://127.0.0.1:8131/` during QA only. Server was stopped after deployment.

Preview QA result:

- 16 Playwright checks across desktop/mobile: `0 failed`.
- Checked home, services, audit, pricing, sample report, dentists, law, thank-you.
- Verified exactly one H1 per page.
- Verified canonical tags.
- Verified no horizontal overflow at 1440px and 390px.
- Verified no missing resources / console warnings after asset route fix.
- Visual contact-sheet review confirmed orange/core-stitch preserved.

Preview QA artifacts:

- `/Users/alexyarosh/Projects/base2026-migration/DW/base2026/output/qa/alex-core-stitch-ai-visibility-20260701a/qa-summary.json`
- `/Users/alexyarosh/Projects/base2026-migration/DW/base2026/output/qa/alex-core-stitch-ai-visibility-20260701a/contact-sheet.png`

## Live deploy

Uploaded release to server:

- `/var/www/alex-yarosh-static/releases/alex-core-stitch-ai-visibility-20260701a`

Current live symlink verified:

- `/var/www/alex-yarosh-static/current -> /var/www/alex-yarosh-static/releases/alex-core-stitch-ai-visibility-20260701a`

Server-side checks:

- `php -l /var/www/alex-yarosh/wp-content/themes/alex-yarosh/functions.php` passed.
- `nginx -t` passed.
- nginx reloaded.

Backups created before server-side edits:

- `/root/alex-yarosh-file-backups/20260701211121-alex-core-stitch-ai-visibility-20260701a`
- `/root/alex-yarosh-file-backups/20260701212357-intent-handler-linefix`

## Live QA after deploy

Live URL checks returned HTTP 200 with expected metadata:

- `/` — title: `AI Visibility Consultant for Local Businesses`; one H1; canonical present; index/follow.
- `/services/` — title: `AI Search Visibility Services for Local Business`; one H1; canonical present; index/follow.
- `/ai-visibility-audit/` — title: `Free AI Visibility Audit for Local Businesses`; one H1; canonical present; index/follow.
- `/pricing/` — title: `AI Visibility Pricing and Packages`; one H1; canonical present; index/follow.
- `/sample-ai-visibility-snapshot/` — title: `AI Visibility Report Example for Local Business`; one H1; canonical present; index/follow.
- `/ai-visibility-audit-for-dentists/` — title: `AI Visibility Audit for Dentists`; one H1; canonical present; index/follow.
- `/ai-visibility-audit-for-law-firms/` — title: `AI Visibility Audit for Law Firms`; one H1; canonical present; index/follow.
- `/thank-you-ai-visibility-audit/` — title: `Thank You | AI Visibility Request`; one H1; canonical present; `noindex,follow`.

Live sitemap:

- `/sitemap.xml` returns 200.
- `thank-you-ai-visibility-audit` is not in sitemap.

Redirects verified:

- `http://www.aggressorbulkit.online/services/` -> 301 `https://aggressorbulkit.online/services/`
- `https://www.aggressorbulkit.online/services/` -> 301 `https://aggressorbulkit.online/services/`
- `https://aggressorbulkit.online/knowledge` -> 301 `https://aggressorbulkit.online/knowledge/`

Assets verified:

- `/alex-native/styles.css?v=alex-core-stitch-ai-visibility-20260701a` -> 200 text/css.
- `/knowledge/static/styles.css` -> 200 text/css.
- `/knowledge/static/assets/alex-yarosh-cutout-v115.png` -> 200 image/png.
- `/wp-content/themes/alex-yarosh/assets/alex-yarosh-avatar.png` -> 200 image/png.

Live Playwright QA:

- 22 desktop/mobile checks: `0 failed`.
- Checked home, services, audit, pricing, sample, dentists, roofing, HVAC, plumbing, law, thank-you.
- No horizontal overflow at 1440px or 390px.
- No 4xx resource loads.
- No console warnings/errors.
- No stale text markers (`[PRICE NEEDED]`, `$499`, `Get My Free Roadmap`, `AI search roadmap`, `Roadmap Audit`).
- No rejected old-template classes found.
- Forms present where expected.

Live QA artifacts:

- `/Users/alexyarosh/Projects/base2026-migration/DW/base2026/output/qa/live-alex-core-stitch-ai-visibility-20260701a/qa-summary.json`
- `/Users/alexyarosh/Projects/base2026-migration/DW/base2026/output/qa/live-alex-core-stitch-ai-visibility-20260701a/contact-sheet.png`

Visual review of live contact sheet confirmed:

- orange/core-stitch system preserved;
- no missing CSS;
- no obvious clipping;
- no raw/generic text-wall regression;
- only caution: mobile pages are long/content-dense, but structurally styled.

## Form / intent handling

Verified DOM for `/ai-visibility-audit/?intent=diagnostic`:

- `ay_intent = diagnostic`
- `ay_notes = Intent: diagnostic; Page: /ai-visibility-audit/; Free AI Visibility Snapshot request from audit page`
- form action: `/wp-admin/admin-post.php`
- method: `post`

WordPress handler patched narrowly:

- reads `ay_intent` with default `snapshot`;
- includes `Inquiry intent:` in the email body;
- email subject uses `New AI Visibility Snapshot Request` instead of old roadmap subject.

No real submission was performed.

## Remaining caution

The live pages are technically and visually deployed, but mobile pages are content-heavy. Next optimization pass can reduce mobile density and tighten sections without changing the accepted visual system.
