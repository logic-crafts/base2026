# Base2026 Public Dataset Growth Release — 2026-08-29

## Outcome

Base2026 now exposes a crawlable public dataset landing, public quickstart,
query example and versioned catalog at `https://base2026.dev/dataset`. The
release is merged, tagged, deployed and submitted once for discovery.

## Source and release receipts

- GitHub repository: `offflinerpsy/base2026`
- Pull request: `#23`
- Merge commit: `f900055333e27f06e4f864ba4695636f8cc3bc7e`
- Release/tag: `public-data-v2026.08.29`
- Worker version: `fadc6c25-1d9f-4805-aed2-614e1463a018`
- Previous rollback version: `79e3677f-3828-4355-8c59-8801458f0fb2`
- Artifact tree SHA-256:
  `9e56f5002e3f684adb639388e701ee8d44405db2a53b7a208a390c80db0b0101`
- Source tree SHA-256:
  `94a2187c75bfaac4b0a85126d2e32723b763958940ad41f12fc389a22f01adf7`

## Privacy correction

Independent review found that the former static `insight_cards.jsonl` mixed
1,939 reviewed public rows with 524 non-public/`needs_review` rows. The released
artifact contains only the 1,939 reviewed public rows. Builder and artifact
checks now reject a non-public, review-held or wrong-policy insight row. Full
transcripts remain excluded.

## Verification

- Python release and homepage contracts: 21 passed.
- Worker tests: 44 passed; typecheck passed.
- Deterministic D1 import dry-run: 2,095 rows in 33 batches.
- Wrangler Static Assets dry-run: 4,250 files.
- Artifact policy and Git publication audit: pass, zero forbidden paths,
  review holds or secret findings.
- Desktop and mobile browser QA: no overflow, console or request errors.
- Live `/dataset`: HTTP 200, self-canonical, `index,follow`, one H1 and Dataset
  JSON-LD.
- Live D1 stats remained 2,175 documents, 1,574 distinct videos, 50 evidence
  routes, 83 projection cards and zero full transcripts.
- IndexNow submission contained exactly `https://base2026.dev/dataset` and was
  accepted with HTTP 200.

## Earned-link coordination

Enigmavista publishes `https://enigmavista.ru/projects/base2026/` as a useful,
initial-HTML project case with one contextual Base2026 link. It is internally
linked, self-canonical, indexable and included in the XML sitemap. Worker
version `0b6b3966-312e-43c2-974e-4bc55afd78f3` released the case; version
`bc7ea229-e3bb-4060-acbf-dc24a0a43b75` added its public IndexNow verification
asset. The exact case URL received HTTP 202 from IndexNow.

Golem Roofing and Dreamwood/Aster publication work stays in their own tasks and
must not be reported live without separate readback receipts. The approved
pattern is one useful standalone transparency/research page, one natural
branded link, internal discovery, self-canonical and sitemap inclusion. No
footer/sitewide link network is allowed.

## Next action

Observe discovery and referrals. After verifying dataset rights and license
metadata, prepare free Hugging Face and Zenodo dataset cards plus one original
engineering launch article. Do not purchase ranking links; a paid publisher or
newsletter test requires explicit budget approval and measures referral reach.
