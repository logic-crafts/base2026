# Base2026 Source Diversity Check — production release

Date: 2026-09-04  
Status: live and verified  
Public domain: `https://base2026.dev/`

## Outcome

The free Source Diversity Check is live at
`https://base2026.dev/tools/source-diversity-check/`. It accepts a bounded set
of admitted public Base2026 record/source IDs, uses only the existing public
read-only MCP `get_source` method, and reports:

- distinct selected records;
- distinct normalized original-source URLs;
- distinct attributed creators;
- missing/unavailable relationship metadata;
- inspectable Base2026 and original-source links;
- deterministic local Markdown and JSON exports.

The tool does not assign a truth, consensus, independence, authority or quality
score. A missing field is an unknown in the selected public response, not proof
that the underlying evidence does not exist.

## Source and release identity

- Tool source merge: PR46,
  `ad976a4ffd0d9ad324f504d214a9f3591abed2c5`.
- Public Evidence Pack merge: PR47,
  `0341b8911a3df42b51285816e3d3e07e615ed96e`.
- Deployed Worker: `da308428-5609-43ab-8b31-88deb124dc7b` at 100%.
- Immediate compatible rollback:
  `60613464-db66-4575-8963-e1c6e5e0ffd9`.
- Release artifact tree SHA-256:
  `0f225c3cfb86b4b89dc0325c70e81d289f79457fa2123f9407d7a7ae819e21c8`.
- Publication-gate schema: `base2026-cloudflare-publication-gate/v1`;
  four public data files, zero policy failure.

The deployment ran with the isolated `hello@base2026.dev` OAuth context for
Cloudflare account `ea334dfd5633085b22c258511b459e1a`. No credential or
IndexNow key value is recorded in Git.

## Verification

- Full public Worker tests: 634 passed.
- Focused tool/evidence-search/builder tests: 36 passed.
- TypeScript typecheck: passed.
- Wrangler dry-run: passed with the target-account D1 and rate-limit bindings.
- Public artifact policy: passed; tree hash matched the release receipt.
- Live HTTP 200: `/`, `/blog`, Evidence Search, Source Diversity Check, `/mcp`,
  source catalog page 2, `/my-research/`, blog sitemap, health and stats.
- Canonical: exact self-canonical tool URL.
- Hub sitemap: exact tool URL appears once.
- Live MCP canary: `get_source` returned one public record inside the declared
  read-only boundary.
- Browser canary: two existing IDs plus one nonexistent ID produced two
  resolved records plus one explicit unresolved record on 1440 px and 390 px.
- Browser errors: zero console/page errors; horizontal overflow zero.
- Local next-step control: selection and receipt text passed.
- `/my-research/`: HTTP 200, private/no-store, `noindex,nofollow`.
- `/api/auth/session`: fail-closed `MEMBER_AUTH_DISABLED` while member auth is
  intentionally disabled on the migrated account.

The static upload reported 4,212 changed assets because the rebuilt artifact
normalizes the already-present Cloudflare footer formatting across generated
HTML. The footer mark stayed singular; the artifact policy and live checks
passed. The upload did not write public D1. Live stats remained:

- documents: 2,259;
- distinct sources: 1,638;
- public evidence routes: 114;
- projected cards: 167;
- full public transcripts: 0.

## Discovery action and limits

The exact new canonical URL was submitted once to IndexNow after live HTTP,
robots, canonical and sitemap checks. The endpoint returned HTTP 200. This is a
crawl notification only; it is not proof of indexing, ranking, referral traffic
or a user action.

The public Evidence Pack under `examples/public-evidence-workflow/` is a
dependency-free, bounded, fail-closed Python example. It performs modern MCP
discovery plus at most eight `get_source` calls and emits deterministic local
Markdown/JSON. It includes public-safe synthetic fixtures and an explicit
not-found state; it does not authenticate, upload, write, read the private
pipeline or retain secrets.

## Next action

Use the verified GSC baseline of 257 impressions, zero clicks and average
position 14.9 for the 72-hour acquisition test. Publish one native worked
example from Evidence Pulse #001, then measure non-owner referrals,
`source_check_run`, successful completion and export/copy actions. In parallel,
build the deterministic Source-Backed Brief. Do not expand into thin
keyword-swapped pages or repeat IndexNow for unchanged URLs.
