# Base2026 Evidence Search plus member-auth integration receipt

Date: 2026-09-01
State: integrated local candidate; not committed, pushed, merged or deployed
Target: `/Users/alexyarosh/.codex/worktrees/58dd/base2026`
Branch: `codex/base2026-google-auth-20260831`
Baseline: `0e5804a8da31ad9d23e5e5b1dd0acc6af2f3f07e`

## Scope

The reviewed Evidence Search implementation from
`/Users/alexyarosh/.codex/worktrees/448b/base2026` was integrated into the
authoritative dirty member-auth candidate. The slice is additive and
anonymous/read-only: `/tools/evidence-search/` uses the existing public D1 FTS5
search, bounded public metadata, fragment query state, visible attribution and
original-link gaps, and an honest no-JS fallback. Future source-diversity and
brief-builder routes remain disabled and unimplemented.

The target's member-auth Worker, package/configuration, bindings, migrations,
member templates, shared header/footer and current reviewed v2 asset bundle were
preserved. No production Worker, D1, secret, OAuth, remote, Git or social
state was changed.

## Integrated source files and hashes

SHA-256 after integration:

| File | SHA-256 |
| --- | --- |
| `templates/base2026-evidence-search.html` | `2f72847be5ac2191e3b5e2b89ad65c9897077d3250e14c27f589519d85e39c8e` |
| `templates/base2026-evidence-search.css` | `5a3ed9e990d37c7823d2385ee57745a7263e4ea1c79ee8a29dc7b76bb63d63b0` |
| `templates/base2026-evidence-search.js` | `9c4c3377eccf0b655ddbf8816dccef4a7673279eb12f89cec2ab96dbb46efaea` |
| `tests/test_base2026_evidence_search_tool.py` | `966b2baf81aea1e09720ebeb7be42a51eedec667c0fd4eaab6c1dc42837d299a` |
| `scripts/build-base2026-cloudflare-release.py` | `22c2f281cfb6f1b0352f6647fa39aa9c09ec31071d9102ef2036eeb3e8afa1d2` |
| `scripts/audit-publication-boundary.py` | `378f87b0b8cc516b42e2bdd3c45aa6d562b2c8d7d670e0e05f7e84950ba80e59` |
| `tests/test_build_base2026_cloudflare_release.py` | `cccbed280b231ea2e13f0ab9f8d34a6e94ca5f02d3fc380aff69b743f687e37b` |
| `docs/project-memory/NEXT_ACTION.md` | `825ffb4b50b1eb71cfb696c69e81449830b653e5f3aa2c3df7f54f7676b382e0` |
| `docs/project-memory/PROMPT_LOG.md` | `e222b1be5e828242b13f8594a3cee72de35395f6dd773b7e1320b572da2ee75a` |

The source candidate's reviewed tree receipt was
`40d292499478b88228249f472e071d4393caf208285de6a9303dc030d135c622`.
The four source filenames were absent from the target before integration.

## Verification

- Focused Python gates: Evidence Search `3 passed`; builder `21 passed`;
  member UI `8 passed`.
- Full Python suite: `157 passed`.
- Public Worker suite: `614 passed` in 11 files.
- Member Worker suite: `13 passed` in 2 files.
- Worker TypeScript `npm run typecheck`: passed.
- Design-authority check: passed.
- Production-like build used the exact target member v2 source tree
  `1039f92aeae0195dee2dfb4c63bc905e41cee2fe41e60fe177b34785713fe361` from
  `output/cloudflare-migration/base2026-members-candidate-20260831-v2` with
  `--members-workspace`.
- Build output was kept outside the repository at
  `/tmp/base2026-evidence-member-build.FkM0W1/release` and reported 4,251
  served files, 90,591,220 bytes, tree SHA-256
  `8ab0277cb5c1a0cf2fbd6798b9ed4c191a3334f118e139dc2a1ac31671fb5f6a`.
  Receipt SHA-256:
  `4222c94c35aa6ee36f7ee0c42847970093f00c1289f09ccf4f4959ccaf965629`.
  Builder verification reported zero private-token, local-path, legacy-route,
  personal-shell/commercial, WordPress-form, canonical or sitemap findings and
  preserved all 15 binary files.
- Built Evidence Search page SHA-256:
  `6ab6019dd233e003ccc0b726dd9579817140150bcb0377bf9b958b833dc83a91`.
  Built Evidence Search CSS/JS hashes match the source hashes above.
- Source-candidate publication audit: 10 public-safe, zero review, zero
  forbidden, zero secret findings. Target audit after integration: 43
  public-safe, zero forbidden, zero secret findings; two pre-existing member UI
  paths remain `needs_review` (`tests/fixtures/member-ui-preview.mjs` and
  `tests/test_base2026_members_ui.py`). No Evidence Search path is in review.
- `git diff --check` passed. No commit, push, merge, deploy, IndexNow call,
  D1 write, remote mutation, social/editorial publication or live-route claim
  was made.

## Release status and next action

Production truth is unchanged: `/workspace/` remains the live public search and
`/tools/evidence-search/` remains HTTP 404. The integrated route is not approved
for publication. Coordinator review must resolve the two foreign member UI
publication-audit paths separately, then request explicit release authorization
before any public deployment or indexing submission.

Suggested commit message after separate owner authorization:
`feat: add bounded public Evidence Search tool`
