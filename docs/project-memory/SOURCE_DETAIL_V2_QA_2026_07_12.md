# Source Detail V2 — isolated QA record (2026-07-12)

## Scope

Deterministic, isolated full-family Source Detail V2 candidate from the frozen route manifest. This record does **not** approve integration, packaging, deploy, reindex, sitemap changes, or public output changes.

## Artifacts

- Input: `.planning/base2026-template-migration/inventory-20260712/route-inventory-manifest.jsonl`
- Candidate A: `.planning/source-detail-v2-full-candidate-20260712-final`
- Candidate B: `.planning/source-detail-v2-full-candidate-20260712-final-rerun`
- Validator reports: `.planning/source-detail-v2-validate-final.log`, `.planning/source-detail-v2-validate-final-rerun.log`
- Determinism receipt: `.planning/source-detail-v2-determinism-final.json`
- Live-vs-candidate footer evidence: `.planning/source-detail-v2-live-candidate-footer-matrix.json`

## Verified automated gates

| Gate | Result |
|---|---|
| Python compile + `git diff --check` | Passed |
| Isolated deterministic build | Passed twice |
| Candidate file-set equality | `1,712` / `1,712`; equal |
| Candidate SHA-256 equality | Equal; no path or content differences |
| Contract/provenance validation | `valid: true`, `errors: []` |
| State reconciliation | `1,493 normal_public_card`, `199 provenance_archive_noindex`, `122 future_404` |
| Candidate local asset validation | Passed after copying required shell icon assets into isolated `/static/assets` |

## Visual and footer result — FAIL CLOSED

A live WordPress vs candidate browser matrix was run at **1440, 1280, 390, and 320**. No horizontal overflow was found and the Source Detail main rail remained narrower than the header plate at the checked desktop viewport.

Footer parity did **not** pass:

1. Portable `scripts/alex_v4_static_shell.py` uses stale footer DOM (CTA/link set, TikTok/social state, Base2026 label, legal copy) relative to the current live WordPress footer.
2. Portable shell CSS adds a top `1px` footer border at desktop where current live has no footer top border.
3. Computed footer geometry/height differs across the target widths. The matrix records the exact values and selector-level styles.
4. The local `geo` WordPress theme source does not match current live footer content, so it is not a visual authority for this repair.

## Sol/X High decision

Independent Sol/X High review: **do not execute a broad site-wide migration or deploy yet.** Source Detail is the only bounded candidate; other template families lack route inventory/output mapping/readiness proof. A rollout would violate the user-required evidence gate.

## Required next repair — closed 2026-07-13

The fail-closed footer repair was completed against the current-live WordPress authority:

- frozen fixture: `templates/shared/alex-home-v4-footer.html`
- fixture SHA-256: `651aaccefbdfc1c77ed6947db988df14f23d100f8bbbbbc45b2c77a1719ae785`
- scoped shell footer/cascade repair: `scripts/alex_v4_static_shell.py`
- strict visual matrix: `.planning/source-detail-v2-footer-visual-final2/`
- reviewed viewports and states: live/normal/archive at `1440`, `1280`, `390`, and `320`
- matrix runner exit: `0`
- deterministic candidates O/P: `1,712` files each, no path or content differences
- visual result: **GO for the bounded Source Detail V2 shared-footer integration**

This closure does not itself authorize packaging or production mutation. Release still requires a dependency-closed isolated branch, an authoritative publication/worktree boundary, exact package verification, and an independent Sol/high permit.

## 2026-07-13 release-candidate gate

The isolated release worktree is:

- path: `/Users/alexyarosh/Projects/base2026-migration/DW/.worktrees/base2026-source-detail-v2-release`
- branch: `release/source-detail-v2-20260713`
- baseline: `e1cb6b80ad997d34b8d795d5a99e9a8f310f010e`

Fresh release candidates and boundary receipts are intentionally ignored build evidence under `.planning/`; they are not release payload. Final package/deploy/indexation/live-QA status must be appended only after the independent release verdict.
