# Base2026 Design Authority and Legacy Quarantine

Date: 2026-08-28
Status: active release rule

## Why this exists

Past release scripts could reapply the founder's warm WordPress/Alex V4 shell
to Base2026 after the product UI had already been corrected. The files were not
the problem by themselves; multiple active design authorities were.

## One production authority

The only supported public release chain is:

1. reviewed public data and `docs/public-pages/`;
2. the current public generators;
3. the retained `web/static/` search components;
4. `templates/base2026-core.css` plus the `base2026-startup-*` templates;
5. `scripts/build-base2026-cloudflare-release.py`;
6. an immutable candidate, automated tests, desktop/mobile screenshots and a
   release receipt;
7. Cloudflare Workers Static Assets.

The visual contract is `b26-independent-v1`: cool-blue canvas, white surfaces,
navy text, blue evidence accent, Manrope/Geist Mono, one Base2026 header and
one Base2026 footer.

## Quarantined historical sources

The following families are history or migration compatibility, not production
design inputs:

- `scripts/alex_v4_static_shell.py`;
- `templates/shared/alex-home-v4-*`;
- `scripts/normalize-wordpress-v4-shell-release.py`;
- `scripts/restore-wordpress-v4-footer-release.py`;
- `scripts/materialize-legacy-public-aliases.py`;
- Search V1, Source Detail V2, Stitch and `template_migration` assets;
- `scripts/package-public-release.ps1` and any caller that still invokes an
  Alex/WordPress normalizer.

They must not be imported, invoked or copied as shell authority by the
Cloudflare release builder. They are not deleted in this change because a
historical asset can still be needed for rollback analysis or migration tests.

## Safe retirement sequence

1. Prove all active Cloudflare release callers use the canonical builder.
2. Add a fail-closed design-authority check to CI and release verification.
3. Remove active calls to the legacy normalizers in a separately reviewed
   compatibility change.
4. Move proven-unused assets into a clearly named historical archive.
5. Delete only after repository search, tests and rollback documentation prove
   there is no dependency.

## Required release evidence

- `scripts/check-base2026-design-authority.py` passes;
- release-builder and Worker tests pass;
- the publication-boundary audit passes;
- desktop and 390px mobile screenshots match the protected shell;
- one header, one footer, one H1, no horizontal overflow and no console error;
- search, API, canonical, sitemap and a dynamic projected-source page pass;
- the immutable artifact receipt and Cloudflare version/rollback IDs are saved.

No release may be described as safe merely because its source templates look
correct. The built candidate and the deployed routes are the evidence.
