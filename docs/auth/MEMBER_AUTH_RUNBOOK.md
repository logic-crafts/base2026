# Google sign-in and My Research

This is an opt-in extension of the existing public Worker, not a new Worker,
domain or publication pipeline. The checked-in production configuration keeps
`MEMBER_AUTH_ENABLED=false` and has no `AUTH_DB` binding. Follow the exact
[dated handoff](../project-memory/HANDOFF_2026-08-31_GOOGLE_AUTH.md) for the
candidate's current test, authorization and release status.

## Boundary

- Public search, source pages, API access and existing publication remain open.
- Google supplies only `openid email profile`, with online access. Gmail,
  Drive, offline grants, implicit account linking and local passwords are absent.
- Better Auth owns OAuth state, PKCE, cookie signing and session verification.
  The application exposes only an explicit route allowlist.
- Identity, sessions, private collections, saved evidence references and notes
  belong in a dedicated private D1 database. `DB` is used only to read and
  validate an already-public evidence reference; member writes never target it.
- No automatic query history, private client uploads, Outreach-specific save,
  billing, email delivery or AI usage is included in this slice.
- Browser storage holds at most one short-lived pending evidence-save intent.
  It never holds credentials, provider tokens or session bearer tokens.

## Required bindings and secrets

| Name | Location and purpose |
| --- | --- |
| `AUTH_DB` | Dedicated private D1; `migrations-members/` only. |
| `DB` | Existing public source D1; evidence eligibility reads only. |
| `BETTER_AUTH_SECRET` | Worker secret, cryptographically random and at least 32 bytes. |
| `GOOGLE_CLIENT_ID` | Worker secret for the approved Google web OAuth client. |
| `GOOGLE_CLIENT_SECRET` | Worker secret; never a frontend variable. |
| `MEMBER_AUTH_ENABLED` | Explicit activation flag; only `true` enables auth. |
| `MEMBER_AUTH_LOCAL_DEV` | Local tests only. Must be absent or `false` in production. |

Keep the actual private database/account identifiers and secret files outside
public Git. Never put values in screenshots, chat, logs, examples or source.
Production may use a private deployment-config overlay with absolute code,
asset and migration paths. It must preserve every existing public binding and
route, add only the approved `AUTH_DB` binding, and explicitly enable members.
Do not substitute the synthetic local configuration for that overlay.

For the pinned Wrangler, run the private overlay from the Worker package and
pass `src/index.ts` explicitly to `deploy`. Its `tsconfig` is relative to the
private config directory; the explicit script keeps build resolution rooted
in the Worker package. Verify a dry run with an explicit absolute `--outfile`
before release. Omitting the script with an out-of-repository config changes
Wrangler's inferred build root; do not treat that different build as the
reviewed candidate.

## Local checks

From `cloudflare/base2026-worker/`:

```sh
npm ci --ignore-scripts
npm run typecheck
npx vitest run --config vitest.config.ts
npm run test:members
```

The separate member test configuration uses workerd and local native D1 with
synthetic Google credentials. It is not evidence of a real Google login.
Its migration directory must never be applied to the public source database.

From the repository root, run the builder/UI tests:

```sh
python3 -m pytest -q tests/test_build_base2026_cloudflare_release.py tests/test_base2026_members_ui.py
```

Build from the coordinator's exact approved current public asset tree, using
the canonical builder and `--members-workspace`. Use a new output directory.
Do not regenerate or replace the current search renderer from the retained
`web/static/` copy. The reviewed member overlay changes only the workspace
asset references and privacy page, and adds the private page plus its JS/CSS.

The optional browser-only fixture is launched with:

```sh
node tests/fixtures/member-ui-preview.mjs --assets /absolute/candidate/directory --port 8790
```

It listens only on loopback and displays an explicitly synthetic account.
It neither contacts Google nor writes D1. Its collections and notes disappear
when the process ends. Do not count its screenshots or saves as auth evidence.

## Google configuration and activation gate

1. Obtain the owner's physical passkey/MFA when required. Reuse the intended
   Google account; do not bypass the challenge or create a parallel identity.
   Inventory existing OAuth clients before changing one. A dedicated free
   project may be created within the confirmed scope when existing projects
   are unsuitable; do not attach billing, change IAM or delete old projects
   merely to reuse their quota.
2. At the browser's action-time confirmation boundary, identify the exact
   project/client change. Configure a web client callback of
   `https://base2026.dev/api/auth/callback/google`. Use only the three identity
   scopes. The canonical site and published privacy page must match the app.
3. Transfer credentials directly into a private, mode-600 file or an approved
   secret store, then into Worker secrets without printing their values.
   The pinned Wrangler supports additive `deploy --secrets-file`; use one
   authorized release with the reviewed code, assets and secret file rather
   than a separate secret update that deploys the previous code. Omitted
   existing secrets must remain preserved.
   Consent-screen audience/test-user/publication choices require an explicit
   owner decision if they have not already been approved.
4. Confirm the dedicated private D1 target. Apply the reviewed member
   migrations only there and verify that a second migration check is empty.
   Do not run an import or a public-source migration as part of auth setup.
5. Build the exact candidate, run typecheck, both Worker suites, builder/UI
   checks, independent security review and a Wrangler dry run with its exact
   assets/configuration. Check the bundle and complete binding parity.
6. Keep `observability.logs.invocation_logs=false` in the member-enabled
   deployment. Review any separate trace/Logpush destinations before exposing
   a callback: callback URLs contain authorization codes and state. Library
   logging is disabled; application errors must be fixed safe messages.
7. Send the coordinator exact source/diff, artifact hashes, private binding
   parity, tests, review and rollback receipt. No commit, push or deployment
   is implied by a local passing suite or by possession of credentials.
8. After explicit release authorization, verify real Google login → private
   save → revisit → logout → denied private access. Use two separate real test
   identities for cross-user isolation where authorized. Confirm no extra
   Google scopes, no cached private responses and no sensitive callback logs.

## Account controls and rollback

The private API supplies self-export, sign-out, all-session revocation and
explicit account deletion after a recent sign-in. Export must contain only
the current user's profile and research records, never auth internals. Deletion
must cascade through that user's private records without changing public data
or another user's records. Never perform a deletion acceptance check on an
unapproved real account.

An emergency feature stop disables member auth while preserving public search
and the private database. A code rollback must use the coordinator's compatible
current public Worker and asset receipt; never restore a pre-guide Worker over
guide-kind data. Do not drop the member database, remove migrations or erase
user data as a rollback shortcut. Session/secret rotation is a separate
authorized incident action, not an incidental deployment step.

OAuth state is not user-owned research history. It can carry the temporary
return URL and PKCE verifier, becomes unusable on expiry and is removed in
bounded expired-only cleanup during later authentication activity. Inactive
expired rows can remain until that activity occurs. Account deletion must
not delete another user's live sign-in state. The public privacy notice
distinguishes this lifecycle from immediate deletion of active account,
session, collection and note records. No background cleanup scheduler is
introduced by this feature.
