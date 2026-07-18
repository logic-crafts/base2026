# Base2026 Phase 0 P1 Preview — 2026-07-17

## Status

Local immutable preview complete. Production was not changed. No deploy, upload, corpus re-export, Meilisearch reindex, IndexNow submission, WordPress mutation, form submission, commit, or push occurred.

Final preview release: `base2026-phase0-p1-r6-preview-20260717-235500`.

Final preview ZIP SHA-256: `6ad17478944ffb14883b117dc4579b3c5099ad03fbf15ddec5760ee9ffd87087`.

Immutable input: `base2026-whole-corpus-stitch-v1-preview-r6-20260715-174000.zip`, SHA-256 `9e4d7277900649dd35a39d47838989ee8eaefe9b71a0b8d23731b3d39227eed3`.

In-package evidence:

- `BASE2026_PHASE0_P1_DERIVATION.json`
- `BASE2026_PHASE0_P1_VALIDATION.json`
- `SITEMAP_STATIC_ADMISSION.json`
- `SOURCE_DETAIL_V2_CANDIDATE_MANIFEST.json`

## Closed P1 contracts

Public dataset manifests now use `base2026.public-dataset-manifest/v1`. Their keys are allowlisted; `source_admission_ledger` and `source_db` are not public fields. The copies at `public-data/tiktok/manifest.json` and `web/static/manifest.json` are byte-identical.

The AI visibility page manifest now uses `base2026.public-page-manifest/v1`; its 65 page entries are normalized paths relative to `web/`, not machine-local absolute paths.

The inherited `SOURCE_DETAIL_V2_PACKAGE_VALIDATION.json` receipt now records only package-relative `candidate` and `web_root` values. A second, package-wide machine-local-path audit scans every JSON artifact in the ZIP: 18 files checked, zero issues. It deliberately permits public root-relative web routes while rejecting macOS/Linux machine roots, Windows drives, UNC paths, `file://`, private worktree/release/knowledge paths, admission-ledger filenames, and SQLite/DB paths. Findings remain pointer/reason-only.

The recursive validator reports only JSON pointer and stable reason code. Fixtures cover POSIX absolute paths, Windows drive paths, UNC/network paths, `file://`, private worktrees, `.hermes`, release/output paths, private knowledge-base paths, admission-ledger filenames, SQLite/DB paths, and allowed public URLs/counts. Rejected values are never echoed.

Sitemap admission is exact and fail-closed:

- 1,493 normal Source Detail routes included;
- 241 frozen non-source routes included;
- 199 public archive/noindex Source Detail routes excluded;
- 135 future/private routes excluded;
- 1,734 unique URLs in five sitemap children;
- every admitted URL must be indexable and have exactly one self-canonical;
- live validation rejects redirects and `X-Robots-Tag: noindex|none`, and requires the served byte hash to match the reviewed local page;
- unapproved indexable routes, missing approved routes, duplicate canonicals, missing canonicals, emitted future routes, and indexable archive routes fail the gate.

The previous 1,933-URL R6 sitemap fails the new check exactly because of 199 unexpected archive URLs. Regeneration and a second `--check-only` pass both return global exact admission.

## Reproducible derivation

Run from a clean checkout of the reviewed Phase 0 branch. Substitute only the immutable input and isolated output locations; the script itself pins the R6 ZIP hash.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/derive-base2026-phase0-p1-preview.py \
  --base-zip <exact-r6-zip> \
  --release-name base2026-phase0-p1-r6-preview-20260717-235500 \
  --output-dir <isolated-preview-output>
```

Independent in-package checks:

```bash
python3 scripts/validate-public-manifests.py \
  --dataset-manifest <release>/public-data/tiktok/manifest.json \
  --dataset-manifest <release>/web/static/manifest.json \
  --page-manifest <release>/web/manifest.json \
  --web-root <release>/web

python3 scripts/generate-base2026-sitemap.py \
  --web-root <release>/web \
  --source-detail-manifest <release>/SOURCE_DETAIL_V2_CANDIDATE_MANIFEST.json \
  --static-admission-manifest <release>/SITEMAP_STATIC_ADMISSION.json \
  --lastmod 2026-07-17 \
  --check-only
```

Expected outputs are `issue_count=0` for all three public manifests and `sitemap_urls=1734`, `normal_included=1493`, `archive_excluded=199`, `future_excluded=135`, `static_exact_admission=241`, `global_exact_admission=true` for the sitemap.

Final local verification:

- full Python suite: `121 passed`, including embedded-prefix rejection, inherited-receipt sanitation and package-wide JSON path-leak fixtures;
- PowerShell parser checks: package, deploy, live-gate and staging scripts pass;
- exact ZIP deploy preflight with `-PlanOnly -SkipPackage -SkipReindex`: `PLAN_ONLY_OK` after manifest, candidate/static hash and sitemap checks;
- deterministic repeat derivation: byte-identical ZIP SHA-256;
- `unzip -t`: no compressed-data errors;
- `git diff --check`: pass;
- publication-boundary audit: 41 public-safe candidates, zero needs-review, forbidden or secret findings.

The earlier local artifact `base2026-phase0-p1-r6-preview-20260717-230500` / `65605625...` is superseded and must not be reviewed or released: an independent audit found machine-local paths in its inherited Source Detail package-validation receipt. The final `235500` artifact closes that gap and is the only current Phase 0 Base candidate.

## Inventory caveat

The older 4,264-route inventory is not admission authority. It contains seven stale indexable rows: six duplicated `solutions/solutions/...` paths and one absent `meili.html`. The Phase 0 static allowlist therefore freezes the 241 non-source URLs actually admitted by the exact R6 sitemap; the 1,692 Source Detail records remain governed separately by the immutable candidate manifest.

This freeze preserves current non-source membership; it does not constitute owner approval for future indexability, canonical, redirect, pricing, or positioning changes.

## Next gate

Keep the preview isolated. Before any deployment discussion, require an independent review of the exact ZIP/hash, complete release tests, owner approval for the release boundary, and a separate explicit production authorization. Any code, contract, route membership, manifest, or ZIP hash drift invalidates this packet.
