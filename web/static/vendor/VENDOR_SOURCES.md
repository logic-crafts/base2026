# Phase 1 Base P4 local browser dependencies

These files are pinned preview dependencies. They remove browser reliance on
third-party CDNs while preserving the accepted Base2026 visual system.

| Local asset | Pinned upstream source | License |
|---|---|---|
| `instant-meilisearch-1.0.0.min.js` | `https://cdn.jsdelivr.net/npm/@meilisearch/instant-meilisearch@1.0.0/dist/instant-meilisearch.umd.min.js` | MIT; `instant-meilisearch-MIT.txt` |
| `instantsearch-4.106.0.min.js` | `https://cdn.jsdelivr.net/npm/instantsearch.js@4.106.0` | MIT; `instantsearch-4.106.0-LICENSE.txt` |
| `instantsearch-reset-8.16.2.min.css` | `https://cdn.jsdelivr.net/npm/instantsearch.css@8.16.2/themes/reset-min.css` | MIT; `instantsearch-css-8.16.2-LICENSE.txt` |
| `geist-{400,500,600,700,800}.ttf` | Google Fonts Geist v5 URLs returned by the accepted stylesheet on 2026-07-17 | SIL Open Font License; `geist-OFL.txt` |
| `geist-mono-{400,500,600,700}.ttf` | Google Fonts Geist Mono v6 URLs returned by the accepted stylesheet on 2026-07-17 | SIL Open Font License; `geist-mono-OFL.txt` |
| `manrope-{400,500,600,700,800}.ttf` | Google Fonts Manrope v20 URLs returned by the accepted shell stylesheet on 2026-07-17 | SIL Open Font License; `manrope-OFL.txt` |

The release derivation records SHA-256 for every copied file. No browser
request to the upstream URLs is required or allowed by the preview gate.
