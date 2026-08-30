# Base2026 technical production release — 2026-08-30

Status: deployed and verified on the public site, not a local-only candidate.

## Scope and authority

The owner requested completion of the prepared work, including the actual
technical site deployment. The prior exclusion of additional articles/social
posts remains separate. This release changed only the public Worker and its
reviewed static artifact. No new article/post, indexing submission, D1 import,
private Worker, DNS, credential or account mutation occurred.

The dirty canonical checkout and parallel profile/pipeline work were not
staged, cleaned or rolled back. Execution used the existing isolated growth
worktree on `codex/base2026-technical-release-20260830`.

## Exact release

| Item | Verified value |
| --- | --- |
| Public URL | `https://base2026.dev/` |
| Worker | `base2026` |
| Deployed version, 100% traffic | `eeeabd1b-7454-4ec5-9ac3-6b35d3bb3fa3` |
| Deployment time | `2026-08-30T14:12:16.120044Z` |
| Immediate rollback | `3e06c10b-9fa4-40aa-ad14-913a11b85f30` |
| Deployed source commit | `0ced3a5c03554d1316397c5cbeceeb697a4d5c05` |
| Artifact tree SHA-256 | `02dc9883597dfab6215cb10b2082c19c804fda21bbbc3e71fe882a2d273a3065` |
| Artifact | 4,237 artifact files; 85,211,638 bytes; 4,239 files including excluded build metadata |
| Build receipt SHA-256 | `ea6939375f1f0ed5c7b57c5c48a2b241a5dccc848c9ae2317510cf870e21cb30` |
| Post-release protocol receipt SHA-256 | `e5fc82a1ed0557cec3352adfb7f4abcad4882fce02b3430fe56cd20d3732c617` |

The reviewed candidate was explicitly selected with `--assets`; no ignored
default output directory was used. Wrangler uploaded four changed static
payloads: hub sitemap, roadmap HTML, roadmap JS and API index. Worker code and
routing/header configuration were deployed in the same checked release.

## What is now live

- The noindex Workspace is absent from the hub sitemap, which has 18 URLs.
- Static and projected `/sources/*` requests run Worker-first. Trailing-slash
  variants return 308 to extensionless URLs while preserving query strings.
- Baseline security headers apply to APIs, XML, dynamic pages and redirects.
- Public JSONL has NDJSON content type and exactly
  `public, max-age=300, s-maxage=3600`, without conflicting `no-cache` values.
- API discovery points human search clients to `/workspace/`.
- The tracked roadmap with Cloudflare, public dataset and API functionality is
  included in the release. The old VPS/local-first fallback is absent.
- Rebuilding preserves the Workspace Project Story link to `/about` instead
  of rewriting it to the Workspace itself. Old generated builder receipts and
  `.assetsignore` are excluded from source records, preventing self-reference.

## Verification

Before deployment: 41 selected Python tests, 47 public Worker tests,
typecheck, exact import dry-run (2,095 emitted records; 33 batches), artifact
policy and explicit-assets Wrangler dry-run passed. Publication audit found no
forbidden file or secret. Public D1 had no pending schema migrations; the
projection module and binding contract were unchanged.

Independent post-deployment readback at 14:14 UTC passed:

- All required routes returned 200; sitemap index had six children and the
  dynamic sitemap had 50 source URLs.
- Static and projected source redirects, query preservation, self-canonicals,
  security headers, cache policy, API index and roadmap checks passed.
- Evidence Brief V1 for `AI search`: 200, ready, six evidence records.
- Evidence Brief V2 for `AI search`: 200, full, five attributable findings.
- Read-only search POST: 200, a valid public source result and
  `full_transcript_public=false`.
- Public JSONL parsed cleanly with zero nonempty sensitive-key findings.
- Homepage, founder, Workspace, common CSS, founder CSS and all four public
  JSONL files were byte-identical before and after deployment. No old design
  or replacement corpus was introduced.

Root Chrome verification: homepage at 1,440px and 390px had no horizontal
overflow. A real homepage question returned two source-linked findings. The
mobile roadmap rendered current Cloudflare content at 390px without overflow
or the stale VPS text, and its Phase 2 selector displayed the cloud pipeline
milestones. The Workspace `schema` query rendered 20 first-page results with
no overflow and kept Project Story linked to `/about`. No browser page errors
were recorded. Browser evidence stays outside Git.

Public D1 was read again after deployment: 2,175 documents, 1,574 distinct
videos, 50 applied projections, 83 cards and zero public full transcripts.
The verification query reported `rows_written=0` and `changed_db=false`.
This is a technical release, not an intake increase.

## Reproduction and rollback

Generated artifacts and raw machine receipts are not public repository files.
The local reviewed candidate is
`/tmp/base2026-technical-release-20260830-web-r2`; the protocol receipt is
`/tmp/base2026-technical-live-qa-20260830-postrelease.json`. These scratch
paths are disposable; the source commit, artifact hashes and safe verified
summary above are the durable release record.

For a future authorized deployment, rebuild an explicit reviewed candidate,
rerun tests and policy, and select it with `wrangler deploy --assets`.
Recheck the current deployment list before rollback rather than blindly using
a dated ID. This release's immediate rollback is the version listed above;
no database rollback or import is required by this release.

## Remaining scope

No technical closeout candidate from this pass awaits deployment. Next is
observation of search-engine recrawl and existing referral traffic. Private
pipeline and GSC/Bing detailed receipts remain dated 2026-08-29 and were not
reverified here. Third-party dataset mirrors remain rights-gated; Golem's
separate deployment-access blocker and additional editorial publication are
not presented as completed by this release.
