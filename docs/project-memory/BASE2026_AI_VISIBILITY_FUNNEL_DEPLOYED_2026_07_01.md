# Alex/Base2026 AI Visibility Funnel deployed — 2026-07-01

## Scope

Mapped the ChatGPT Pro content batch into the live Alex Yarosh static overlay and closed the technical SEO/conversion leaks identified in the zero-traffic audit.

## Content inputs

- ChatGPT Pro content task: `docs/project-memory/BASE2026_CHATGPT_PRO_CONTENT_TASK_2026_07_01.md`
- Returned content batch saved as: `docs/project-memory/BASE2026_CHATGPT_PRO_CONTENT_BATCH_2026_07_01.md`

## Release

- Release name: `alex-ai-visibility-funnel-20260701`
- Live symlink: `/var/www/alex-yarosh-static/current -> /var/www/alex-yarosh-static/releases/alex-ai-visibility-funnel-20260701`
- Generator updated: `scripts/generate-alex-base2026-native-site.py`
- Overlay snippet updated: `/etc/nginx/snippets/alex-base2026-native-overlay.conf`
- WordPress form handler patched with live backups before changes.

## Pages live

Main pages updated:

- `/`
- `/ai-visibility-audit/`
- `/pricing/`
- `/services/`
- `/sample-ai-visibility-snapshot/`

Vertical pages added:

- `/ai-visibility-audit-for-dentists/`
- `/ai-visibility-audit-for-roofing-companies/`
- `/ai-visibility-audit-for-hvac-companies/`
- `/ai-visibility-audit-for-plumbing-companies/`
- `/ai-visibility-audit-for-law-firms/`

Existing support/service pages regenerated in the same visual system:

- `/ai-visibility-diagnostic-audit/`
- `/technical-seo-geo-foundation/`
- `/answer-ready-service-pages/`
- `/entity-trust-source-intelligence/`
- `/ai-visibility-source-footprint/`
- `/what-is-ai-search-visibility/`
- `/why-chatgpt-does-not-recommend-your-business/`
- `/when-to-rebuild-website-for-seo/`
- `/about/`
- `/privacy-policy/`
- `/thank-you-ai-visibility-audit/`

## Technical fixes closed

- `https://www.aggressorbulkit.online/` now 301 redirects to `https://aggressorbulkit.online/`.
- `http://www.aggressorbulkit.online/services/` now 301 redirects directly to `https://aggressorbulkit.online/services/`.
- `https://aggressorbulkit.online/knowledge` now 301 redirects to `https://aggressorbulkit.online/knowledge/`.
- `/thank-you-ai-visibility-audit/` is now `noindex,follow`.
- `/thank-you-ai-visibility-audit/` is removed from the main sitemap.
- Main sitemap now contains 20 indexable canonical URLs.
- `/sample-ai-visibility-snapshot/` is in sitemap.
- 5 vertical pages are in sitemap.
- Pricing page no longer exposes `$499`, `[PRICE NEEDED]`, or placeholder price ranges.
- Remaining public `roadmap` wording removed from generated Alex overlay pages.

## Form / intent capture

Static forms now include:

- `ay_intent`
- `ay_website`
- `ay_business_name`
- `ay_industry`
- `ay_market`
- `ay_services`
- `ay_competitors_freeform`
- `ay_name`
- `ay_email`
- `ay_extra_notes`

URL intents are captured from:

- `?intent=snapshot`
- `?intent=diagnostic`
- `?intent=sprint`
- `?intent=growth`
- legacy `?plan=...` fallback

WordPress handler now records in lead/email body:

- inquiry intent
- competitors/freeform
- extra notes

Verification example:

- Live `/ai-visibility-audit/?intent=diagnostic` produced hidden `ay_intent=diagnostic` and `ay_notes=Intent: diagnostic; Free AI Visibility Snapshot request from audit page`.

## Live SEO verification

Checked live pages:

- `/`
- `/services/`
- `/ai-visibility-audit/`
- `/pricing/`
- `/sample-ai-visibility-snapshot/`
- all 5 vertical pages
- `/thank-you-ai-visibility-audit/`

Results:

- All checked pages returned HTTP 200.
- All indexable pages have self-canonical URLs.
- All checked indexable pages have `index,follow,max-image-preview:large`.
- Thank-you page has `noindex,follow`.
- All checked pages have exactly one H1.
- Form pages include `ay_intent` field.
- No checked page contained `$499`, `Get My Free Roadmap`, `AI search roadmap`, or `PRICE NEEDED`.

## Visual QA evidence

Browser screenshot evidence:

- Homepage: `/Users/alexyarosh/.hermes/cache/screenshots/browser_screenshot_b036af06d15642369f73e3becf42907f.png`
- `/ai-visibility-audit/`: `/Users/alexyarosh/.hermes/cache/screenshots/browser_screenshot_c9ef38e2c650448f949f41072f393095.png`
- `/pricing/`: `/Users/alexyarosh/.hermes/cache/screenshots/browser_screenshot_f46e336dff0c4d82ba7f0e16df9ebb87.png`

Visual result:

- Orange Alex/Base2026 visual system preserved.
- Pages use hero/card/form/FAQ sections, not plain text walls.
- Pricing cards remain visual and contain no public dollar price placeholders.
- Snapshot form is visible and styled.
- Browser console geometry check on Pricing: no horizontal overflow and one H1.

## Server backups

Relevant live backups created under `/root/alex-yarosh-file-backups/`, including:

- `20260701190631-ai-visibility-intent-handler`
- `20260701190908-ai-visibility-intent-handler-2`
- `20260701191153-ai-visibility-intent-handler-3`
- `20260701192111-ai-visibility-funnel-final`

## Remaining follow-up

1. Run a real form test only if Alex approves creating a test lead/email.
2. Open GSC/Bing after crawl delay and inspect the 20 main sitemap URLs plus Base2026 priority URLs.
3. Decide later whether to add med spa/restoration/contractor vertical pages.
4. If exact prices are approved later, update `/pricing/` with visible price/range schema. Until then it is intentionally package-based.
