# Alex site template regression rollback — 2026-07-01

## Trigger

Alex reported that the AI Visibility funnel deployment used the wrong visual template. The issue was not the content meaning; the issue was layout/template choice.

## Root cause

The deployment used the wrong generator/template path:

- bad deployment: `scripts/generate-alex-base2026-native-site.py` as edited in-session produced `alex-native-intro` / generic card-heavy sections;
- correct accepted visual system from prior work: orange hero plus `alex-core-stitch-*` rhythm used on Home/About and later unified across Services, AI Visibility, and Pricing;
- prior accepted backup: `/root/alex-yarosh-file-backups/20260630-203858-unify-core-stitch-services-audit-pricing`;
- prior session evidence confirms: Home/About are source of truth; Services + AI Visibility + Pricing must stay in `alex-core-stitch-*`, not old/interim islands.

## Immediate live rollback performed

Rolled back the bad live deployment:

- current symlink restored to `/var/www/alex-yarosh-static/releases/alex-base2026-native-20260628`;
- overlay snippet restored from `/root/alex-yarosh-file-backups/20260701191627-ai-visibility-funnel-nginx/alex-base2026-native-overlay.conf`;
- WordPress `functions.php` restored from `/root/alex-yarosh-file-backups/20260701190631-ai-visibility-intent-handler/functions.php` to undo the in-session form handler touch;
- `php -l` passed;
- `nginx -t` passed;
- nginx reloaded.

Rollback backup created:

- `/root/alex-yarosh-file-backups/20260701200304-rollback-bad-ai-funnel`

## Verified after rollback

Live checked:

- `/` returns 200 and uses `alex-core-stitch-*` classes;
- `/services/` returns 200 and uses `alex-core-stitch-*` classes;
- `/ai-visibility-audit/` returns 200 and uses `alex-core-stitch-*` classes;
- `/pricing/` returns 200 and uses `alex-core-stitch-*` classes;
- `/sample-ai-visibility-snapshot/` is no longer served after rollback, because the new bad-release routes were removed from overlay.

Current live CSS markers:

- Home: `/alex-native/styles.css?v=funnel-align-20260630a`
- Services / AI Visibility / Pricing: `/alex-native/styles.css?v=core-stitch-unified-20260630a`

Class verification:

- Home: `alex-core-stitch` present, `alex-native-intro=0`.
- Services: `alex-core-stitch` present, `alex-native-intro=0`, `ay-roadmap-form-card=0`.
- AI Visibility: `alex-core-stitch` present, `alex-native-intro=0`.
- Pricing: `alex-core-stitch` present; pricing still has one `alex-pricing-stitch` marker in a page-specific class name, but it is inside the accepted core-stitch structure from the prior correction.

Visual screenshot evidence after rollback:

- Homepage: `/Users/alexyarosh/.hermes/cache/screenshots/browser_screenshot_edb8b231cad84b6c8c164cc97f48ff21.png`

## Correct template rule going forward

Do not use the generic `alex-native-intro` / card-heavy generator for Alex's main commercial pages.

Correct source-of-truth for the main site:

- orange `b26-about-hero` / `alex-native-hero` top section;
- `alex-core-stitch-intro` intro sections;
- `alex-core-stitch-main` and `alex-core-stitch-two-col` rhythm;
- `alex-core-stitch-note` side-note cards;
- `alex-core-stitch-entry` form sections;
- `alex-core-stitch-card-grid` / `alex-core-stitch-card` cards;
- native form cards such as `alex-services-form-card` only inside the core-stitch rhythm.

The returned ChatGPT Pro content remains useful, but must be mapped into this accepted template rather than replacing the template.

## Next safe action

Build a preview only, not live deploy:

1. Use `output/reference/alex-core-stitch-live-rollback-20260701/` as the local visual source-of-truth snapshot.
2. Map ChatGPT Pro content into the existing `alex-core-stitch-*` component shells.
3. Preserve Home/About/Services/AI Visibility/Pricing route shapes and forms.
4. Add sample/vertical pages only after a production-shaped preview confirms they use the same core-stitch visual language.
5. Show screenshots before any new live switch.
