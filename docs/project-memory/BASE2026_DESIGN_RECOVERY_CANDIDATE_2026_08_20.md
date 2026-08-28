# Base2026 independent design recovery candidate — 2026-08-20

## Status

`b26-independent-v1` is **live in production** as final r9 on Worker `48d8ea7e-f9db-464c-a173-265ab991fc24`. It was not committed, staged, pushed or submitted for indexation in this release operation.

## Production correction — r9

The r8 no-deploy language below is a historical candidate record. The owner subsequently authorized production deployment. Final r9 artifact `/tmp/base2026-b26v1-r9-candidate.SMKNLf` (4,230 files; 82,962,336 bytes; tree SHA-256 `0a5ea3f2b2f77ee59e1dba380d6f8acfe750b54f4fd13247b35eb8fc69e4e156`) is live on Worker version `48d8ea7e-f9db-464c-a173-265ab991fc24`.

The initial r8 live deployment was `3c12d5a3-5855-4971-b163-9d5b067e8031`. Live browser QA exposed one Roadmap mixed-content warning from the legacy `mailto:` contact form. The source authority was corrected in the release builder and info-page generator, r9 was rebuilt, 13 focused tests and `git diff --check` passed, and the final release was deployed. Final Roadmap mobile QA at 390 px records zero overflow, errors or warnings. Live D1 search and private Support form write/readback/delete also passed. No Git staging, commit or push was performed.

This candidate implements the recovery decision in `BASE2026_DESIGN_RECOVERY_AUDIT_2026_08_20.md`: one Base2026-only cool-blue research-product contract replaces the mixed startup/legacy presentation at the release boundary. It does not restore the retired Alex Personal shell, warm/orange palette, commercial calls to action, footer, or domain links.

## Final candidate correction — r8

The earlier `r1` paths and counts below are superseded records of an intermediate candidate and must not be used for review or release. The current local-only candidate is:

- Artifact: `/tmp/base2026-b26v1-r8-candidate.GaIPI2`
- Receipt: `/tmp/base2026-b26v1-r8-candidate.GaIPI2/.base2026-cloudflare-release-receipt.json`
- Build log: `/tmp/base2026-b26v1-r8-build.log`
- Screenshots: `/tmp/base2026-b26v1-r8-playwright/`
- Artifact: 4,230 files, 82,962,428 bytes, tree SHA-256 `6c896fe860f3d0e4203321bfbadc9073cdb77c50046e3ae658a0ee7c9bac9518`

Current verification is deliberately narrow and reproducible: 13 focused builder tests and `git diff --check` passed; the release receipt reports zero personal-shell, personal-route, personal-commercial, old-origin, private-token, broken-knowledge and decorative-sequence markers, with static manifest and binary preservation passing. A ten-route matrix confirmed the shared Base2026 header, footer and `base2026-core.css` on home, Workspace, index, info, roadmap, form, solution and source families. The served-artifact marker sweep found no Alex-commercial CTA/domain markers, warm/orange color tokens or solution-number selector. Local Playwright checked Home at 1440px and Workspace, Roadmap and a solution at 390px; each mobile route had `scrollWidth == clientWidth == 390` and the solution emitted no console errors.

The static Workspace preview emits expected 501 POST errors because `python -m http.server` cannot execute the Cloudflare Worker endpoint. This is explicitly not a D1/search regression claim. No Worker, form handler, D1 binding, Cloudflare configuration or production route was changed by this candidate.

## Source and candidate identity

- Clean implementation worktree: `/Users/alexyarosh/Projects/base2026-migration/DW/base2026-publication-20260820`
- Base commit: `de96c08f8f5e28f3ac0ce5236093b4f0b5c152e9`
- Clean branch: `codex/base2026-startup-publication-20260820`
- Candidate artifact: `/tmp/base2026-b26v1-candidate.oBN23y`
- Candidate release receipt: `/tmp/base2026-b26v1-candidate.oBN23y/.base2026-cloudflare-release-receipt.json`
- Artifact: 4,230 files, 82,740,948 bytes, tree SHA-256 `9617e22b26ab8b646fe0de6d1ebc7d062feb599ec0252d78af64deb2e449ba1f`
- Screenshot evidence: `/tmp/base2026-b26v1-candidate.oBN23y/screens/`

The canonical checkout remains dirty and was not used for product implementation. It is still on `codex/base2026-domain-migration-plan` at `e1cb6b80ad997d34b8d795d5a99e9a8f310f010e`.

## Implemented candidate scope

- Added one independent Base2026 design contract in `templates/base2026-core.css`: cool blue/white palette, shared spacing, typography, controls, cards, responsive header/footer and legacy-component overrides.
- Replaced the startup header/footer with Base2026-only navigation and approved accessible GitHub/X icons.
- Rebuilt the startup homepage around the same Base2026 contract; retained useful product copy and routes, removed the inherited support-panel stripe, warm/orange visual authority, personal service CTA and decorative browser-like artifacts.
- Centralized shell application in `scripts/build-base2026-cloudflare-release.py` so generated pages are normalized at the release boundary rather than edited one by one.
- Corrected the Workspace rewrite to use the actual search document, preserve its runtime and add a root base URL. It also removes the stale malformed metadata fragment and retired commercial handoff from the staged search route.
- Applied the shared contract to the home, Workspace, topics, creators, methodology, roadmap, support, partner and representative source/detail route families.
- Removed decorative roadmap sequence numbers from `web/static/roadmap.js`. Semantic phase status remains.

Protected behavior was not intentionally changed: Cloudflare Worker routes, D1 search schema/bindings, form handlers and inbox D1, public source records, external attribution, canonical URLs, robots, sitemap, llms, legacy redirects and indexability.

## Candidate verification

### Source and build

- `python3 -m pytest -q tests/test_build_base2026_cloudflare_release.py`: 9 passed.
- Worker `npm run typecheck`: passed.
- Worker `npm test`: 10 passed.
- `node --check web/static/roadmap.js`: passed.
- `git diff --check`: passed.
- Safe explicit import dry run against candidate `passages.jsonl`: 2,095 rows read, 224 skipped, 3 rows emitted, no write.
- Wrangler static-assets dry run completed against the candidate; no upload occurred.
- Publication-boundary audit found 10 changed public-safe source candidates, 0 needs-review, 0 forbidden and 0 secret findings.

### Static contract

- Candidate release counters report zero old-canonical, broken-knowledge, local/private, personal-origin, personal-shell, personal-form and retired-personal-route findings; binary asset preservation passed.
- Candidate internal-link scan checked 181,087 resolved internal targets across 4,179 HTML documents with zero missing targets after honoring the Workspace base URL.
- Candidate `robots.txt`, `sitemap.xml` and `llms.txt` exist; root, Workspace, Topics, Creators, Methodology and Roadmap canonical URLs use `https://base2026.dev/`.

### Visual and interaction QA

The local candidate was inspected at 1440px and 390px for `/`, `/workspace/`, `/topics/`, `/creators/`, `/methodology.html`, `/roadmap.html`, `/support.html`, `/partner.html` and a representative source detail page.

- 18 route/viewport cases: one Base2026 header and one Base2026 footer, zero horizontal overflow, zero links to `aggressorbulkit.online`, zero unlabeled actionable controls and zero remaining warm-surface matches.
- No console errors or warnings were recorded in the final candidate matrix.
- Mobile navigation opened correctly and keyboard Tab reached its first Search link.

The candidate browser used a local mocked response only for visual exercise of the static Workspace because a static server cannot execute the Worker/D1 endpoint. This does **not** claim candidate D1 search or form write/readback evidence. Those remain live-release gates.

## Read-only live verification after candidate build

- `https://base2026.dev/`: HTTP 200.
- `https://base2026.dev/workspace/`: HTTP 200.
- Read-only live `POST /api/search/multi-search` for `schema`: one result set from `base2026_public_tiktok`, 40 estimated hits and one returned attributed public hit. No data was written.

This proves the existing live architecture remains healthy; it does not make the candidate live.

## Release boundary and rollback

The current live system remains Cloudflare Worker `237385ff-5984-44c8-8df3-b52873249296` with public D1 `base2026-public-search` (`ac034130-4169-43c2-9a17-4b72d05457b0`) and separate inbox D1 `base2026-inbox` (`542a77ef-da00-4522-8b7a-3d78fc646c72`). Preserved Worker rollback versions are `c5e88c7f-707b-4572-8d33-e369eecb2bb7` and `4389e513-c16a-4bcf-9f8c-b97ac55b7825`; VPS/Meilisearch rollback artifacts remain as recorded in `HANDOFF_2026-08-20_STARTUP_SEPARATION.md`.

## Remaining gates and next safe action

1. Owner reviews the candidate screenshots and confirms the design direction. This is a visual decision, not a release approval.
2. Only after a separate explicit production authorization: review the exact source diff, stage only the reviewed clean-worktree source paths, commit atomically, create a fresh release artifact, deploy, and collect fresh live HTTP, visual, D1-search and Support/Partner form receipts.
3. Retain the old Worker rollback versions and do not change DNS, canonical/robots/indexability, data or redirects as part of the visual release.

External GitHub CodeQL billing and legacy Pages deployment API failures are unrelated to this candidate and remain recorded in the startup-separation handoff.
