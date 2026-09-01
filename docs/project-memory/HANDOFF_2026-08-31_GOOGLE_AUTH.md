# Google Login and My Research — isolated implementation

Status: frozen release candidate and Google setup prepared; independent security
delta review passed; awaiting coordinator integration ACK, not deployed.
Updated 2026-08-31.

## Boundary and baseline

- Branch: `codex/base2026-google-auth-20260831`.
- Source baseline: `0e5804a8da31ad9d23e5e5b1dd0acc6af2f3f07e`, independently
  matched to public `origin/main` before implementation. The initial August 28
  checkout was not used as a release input.
- Protected public Worker readback: `7522595a-13bf-4437-8955-fd14816b2569`.
- Reviewed static baseline: 4,245 served files, tree SHA-256
  `ed0a9371e0471d13006b62b250d458c7f3b3fdbcc8530fc938dd32c758fe46e2`.
  Independent per-file byte/hash verification passed with zero mismatches.
  Rebuilding this reviewed input with the current canonical builder reproduced
  the identical served tree, establishing a safe baseline for an opt-in overlay.
- Existing Worker baseline: TypeScript and 597 tests passed before changes.

The coordinator owns public Git and runtime release. No commit, push, merge,
remote database mutation or deployment has been performed by this workstream.
Other worktrees and their reviewed static artifact are read-only inputs.

## Small useful slice

Optional Google sign-in, private named collections, explicitly saved evidence
sources and short notes. Public discovery, source pages and articles stay open.
Save resumes its selected source after login. Export, account deletion, sign out
and session revocation belong to the slice, not a later security phase.

The prototype uses Better Auth with a separate private `AUTH_DB` binding in the
existing Worker. No new domain or public API-key requirement is assumed.
Identity scopes are limited to `openid`, `email` and `profile`, with online
access only. Existing public databases and the private publication pipeline
must not receive account data. Saved queries, Outreach-specific integration,
payments, newsletters, AI recommendations and automatic history are deferred.

## Owned implementation surfaces

- New member auth/research modules, private migrations and local-runtime tests
  under `cloudflare/base2026-worker/`.
- New My Research page and additive member scripts/styles under `templates/`.
- Narrow routing and opt-in integration in the existing public Worker and
  canonical static release builder. The served search renderer, shared shell,
  homepage and founder presentation remain protected.
- This handoff and scoped continuation/security documentation.

## Local asset candidate

The canonical opt-in builder produced tree
`1039f92aeae0195dee2dfb4c63bc905e41cee2fe41e60fe177b34785713fe361`
with 4,248 served files / 89,959,711 bytes. Independent per-file readback found
zero hash/size mismatches. Exactly two baseline files changed (`privacy.html`,
`workspace/index.html`), and three were added (`my-research/index.html`,
`static/base2026-members.css`, `static/base2026-members.js`). The other 4,243
served baseline files remain byte-identical. This is a local candidate only.

See [member setup and release gates](../auth/MEMBER_AUTH_RUNBOOK.md).

## Google configuration receipt

The owner completed the Google Console passkey on August 31. The intended
account was verified, but Google denied OAuth configuration access in the
initially selected existing project (`clientauthconfig.clients.get`,
`clientauthconfig.clients.list`, `oauthconfig.verification.get`). Searching
the accessible project selector for Base2026 returned no resources. No IAM
access request or mutation of that existing project was submitted.
The coordinator confirmed a dedicated free Base2026 project is in scope,
without billing, IAM or organization-policy changes. After the owner's current
instruction to proceed, it was created once: Google reported the creation task
finished and the new project was selected. The quota had 12 free slots; no old
project was deleted or reused. No billing or IAM change was performed.

The owner directly confirmed the identified support/contact and persistent
web-client setup step. Google confirmed `OAuth configuration created!` and
`OAuth client created`. Exactly one web client is listed. Saved client fields
were read back: origin `https://base2026.dev`, callback
`https://base2026.dev/api/auth/callback/google`. Credentials were transferred
without displaying their values to a mode-600 file outside public Git.

Google confirmed `Branding changes saved!`: the canonical homepage, public
privacy page and authorized domain match Base2026. The app is External and
Testing, with the intended owner as its only test user. Google confirmed
`Data access changes saved!`: only `openid` and the equivalent basic email
and profile scopes; zero sensitive or restricted scopes. Neither Google app
publication nor live product login is claimed.

## Verification and remaining release gate

Root reran typecheck, 612 public Worker/routing tests, 13 native workerd/D1
member tests and 28 combined builder/UI tests. The independent full security
review passed its exact pre-hardening snapshot with no critical/high finding.
The [independent delta review](../auth/SECURITY_DELTA_REVIEW_2026-08-31.md)
passed the final hardened candidate: all five findings are closed, with the
expired-state lifecycle residual explicitly documented. Its 25 checked hashes
match. The old 40 hashes remain historical and are not the final approval.

The private overlay hash is
`e1dcb230fce2a88e4d3c5c8eb850d4e9f74dd1a9ddbbd845b8fb918869b19390`.
Its exact member-enabled dry run passed: extracted Worker module SHA-256
`e59f97bf7a9d9aaf4f445f3c2a77068bcfeb18a51f81abd2e410a8755b9ff42b`,
2,099,671 bytes, reported 2,050.46 KiB / 374.07 KiB gzip. The auth database ID
is deliberately unresolved, and no secret values were supplied to that dry
run. Explicit `src/index.ts` from the Worker package is required with the
private overlay, as described in the runbook.

The synthetic local browser flow covered selected-source Save, collection
creation, note save and revisit, cancel/focus return, and 44px action targets.
Measured 390px and 1,440px layouts have no horizontal overflow; reduced-motion
CSS is respected. Saved viewport screenshots are private local QA artifacts.
Temporary browser viewport and media overrides were reset. This
fixture is not Google authentication or remote-D1 proof. Keyboard Tab/Escape
acceptance remains unverified because browser input did not reliably exercise
those actions; do not claim a keyboard pass from markup or click testing.

No production `AUTH_DB`, Worker auth secrets, remote migration or deployment
has been created. Actual Google login/session/save/logout proof is **not yet
obtained**. The coordinator explicitly retains the integration/release gate;
there is no owner action requested at this checkpoint.

The next gate is the coordinator's review of the frozen source/config hash
manifest, five-path asset delta, final security verdict, private overlay,
migration and rollback plan. After its integration ACK, provision only the dedicated private
database, apply the two member migrations, and perform one exact authorized
code/assets/secrets release before real Google E2E. The pinned Wrangler's
additive `--secrets-file` avoids a separate old-code secret deployment.

Preserve the public API, existing three public bindings, unchanged search
renderer/shell/design and current live D1 blog. New coordinator-owned
data-only articles are not reconstructible from the static tree or this Git
snapshot. Do not replay imports, pipelines or old article payloads. Private
account, browser and operational receipts stay outside public Git.

Suggested commit message after coordinator approval:
`feat(auth): add optional Google sign-in and private research collections`.
