# Alex Home unified rebuild deployed — 2026-07-05

Scope: `https://aggressorbulkit.online/` Home/static overlay release.

## Release

- Release: `alex-home-unified-system-20260705a`
- Generator updated: `scripts/generate-alex-base2026-native-site.py`
- Local backup before edit: `.planning/backups/generate-alex-base2026-native-site.before-home-unified-20260705-050813.py`
- Remote previous current symlink: `/var/www/alex-yarosh-static/releases/alex-core-stitch-ai-visibility-20260701a`
- Remote current symlink after deploy: `/var/www/alex-yarosh-static/releases/alex-home-unified-system-20260705a`

## Design correction

This rebuild treats the previous Home as an anti-reference, not a source-of-truth template. The new Home uses a single reusable visual grammar:

1. unified hero + integrated snapshot form;
2. one-system explanatory tiles;
3. clickable service cards with explicit `Open service →` affordance;
4. Base2026 evidence/product band with real links;
5. compact FAQ accordion;
6. consistent orange primary CTA and short header CTA.

Removed/avoided:

- old `alex-home-snapshot-bridge` first-screen pattern;
- disconnected text-section stack;
- duplicate equal-weight CTAs in the hero;
- generic repeated FAQ/card treatment;
- visible `Business name`, `Best contact`, and `FORM 01-B` fields on Home.

## Local QA

Production-shaped local preview server: `http://127.0.0.1:8127/`

Local HTTP checks:

- `/` -> `200 text/html`, 16288 bytes
- `/alex-native/styles.css` -> `200 text/css`, 42564 bytes
- `/knowledge/static/styles.css` -> `200 text/css`, 129155 bytes
- `/knowledge/static/assets/alex-yarosh-cutout-v115.png` -> `200 image/png`, 1799173 bytes

Local DOM/browser checks:

- one H1: pass
- no horizontal overflow at desktop 1280×577: pass
- visible Home fields: Website URL, Your name, Email
- removed fields absent: pass
- form action preserved: `/wp-admin/admin-post.php`
- service links: 4
- Base2026 evidence links: 3
- FAQ details: 3

Local screenshots/contact sheet:

- desktop: `/Users/alexyarosh/.hermes/cache/screenshots/alex_home_unified_local_desktop_1280x577_cdp.png`
- mobile: `/Users/alexyarosh/.hermes/cache/screenshots/alex_home_unified_local_mobile_390x844_cdp.png`
- contact sheet: `/Users/alexyarosh/.hermes/cache/screenshots/alex_home_unified_local_contact_sheet.png`

Vision QA:

- desktop local: PASS
- mobile local CDP 390×844: PASS

## Live deploy + QA

Deploy method:

- zipped `output/releases/alex-home-unified-system-20260705a/web`
- uploaded to `geo:/tmp/alex-home-unified-system-20260705a.zip`
- unpacked to `/var/www/alex-yarosh-static/releases/alex-home-unified-system-20260705a`
- atomically repointed `/var/www/alex-yarosh-static/current`
- ran `nginx -t`
- reloaded nginx

Remote verification:

- current symlink: `/var/www/alex-yarosh-static/releases/alex-home-unified-system-20260705a`
- `nginx -t`: pass
- `systemctl is-active nginx`: active

Live HTTP checks:

- `https://aggressorbulkit.online/?qa=live-alex-home-unified-v1` -> `200 text/html`, 16288 bytes
- `https://aggressorbulkit.online/alex-native/styles.css?v=alex-home-unified-system-20260705a` -> `200 text/css`, 44297 bytes
- `https://aggressorbulkit.online/knowledge/static/styles.css?v=base2026-ai-pages-cardfix-20260628` -> `200 text/css`, 129155 bytes
- `https://aggressorbulkit.online/knowledge/ai-visibility-pages/?qa=after-alex-home-deploy` -> `200 text/html`, 50260 bytes

Live browser DOM checks:

- release CSS loaded: `/alex-native/styles.css?v=alex-home-unified-system-20260705a`
- `alex-home-unified`: present
- one H1: pass
- no desktop horizontal overflow: pass
- old bridge: absent
- removed fields absent: pass
- visible Home fields: Website URL, Your name, Email
- form action preserved: `/wp-admin/admin-post.php`
- service links: 4
- Base2026 evidence links: 3
- FAQ details: 3

Live screenshots/contact sheet:

- desktop: `/Users/alexyarosh/.hermes/cache/screenshots/browser_screenshot_64bcf2840f1945b087501236d782c17f.png`
- mobile: `/Users/alexyarosh/.hermes/cache/screenshots/alex_home_unified_live_mobile_390x844_cdp.png`
- contact sheet: `/Users/alexyarosh/.hermes/cache/screenshots/alex_home_unified_live_contact_sheet.png`

Vision QA:

- live desktop browser QA: PASS
- live mobile CDP 390×844 QA: PASS

## Notes

- No Base2026 `/knowledge/` release or Meilisearch reindex was performed.
- No Git commit/push was performed.
- The local repo was already heavily dirty before this task; stage only intentional files if committing later.
