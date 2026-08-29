# Founder Profile Hero Release — 2026-08-28

## Outcome

The approved Alex Yarosh founder campaign hero is live at
`https://base2026.dev/founder`.

- Current public Worker: `1ad991e4-bc8f-4c34-a8d1-c77723377137`
- Immediate rollback: `35a2ee9e-1d95-45c4-b971-26f19183d732`
- Artifact tree SHA-256:
  `7a322dfb1316a10ef50c4a294f5ca1e38c6313c63e2e35995add84352fa80e19`
- Candidate file count: 4,237

## Exact public artifact delta from R5

1. `founder.html` changed.
2. `static/base2026-founder.css` added.
3. `static/assets/alex-yarosh-founder-step-wall.webp` added.

No homepage, header, footer, Evidence Brief, Worker API, D1 or private-pipeline
file changed in the release artifact.

## Candidate and live hashes

- Founder HTML:
  `d03b01a8a464adcdd7b09de4989f9655f9292283a45bb58e7a553f18b35a6539`
- Founder CSS:
  `43ec793f4e6eab25ea1f67a543b9b4bc14a20f2391d8c60435dbc89142f31e1`
- Founder WebP:
  `3922ebadf65f2b7ba928efa8ddec9b537276aa4353d297825675831a8a7e89a8`

Live readback matched all three candidate hashes.

## Unchanged R5 sentinels

- Homepage HTML:
  `cf384e7c890b76b7bc8b446a03d96e959af52fb41e914dee812569500f6750b3`
- Homepage CSS:
  `bec459945e06bc7e295d3e4d5d17b55a3264ac871717dc90ee85551e5df24f6f`
- Evidence Brief JS:
  `ef57559fe992fa467a6d82425dc9e0495789bfe47b777f343313ee64938f6a7d`

Each post-deploy hash exactly matched its pre-deploy R5 baseline.

## Verification

- Builder and homepage-motion tests: 18 passed.
- Public Worker tests: 43 passed.
- Typecheck, import dry-run, Wrangler dry-run and artifact policy: passed.
- Independent founder-release reviewer: GO.
- Live `/api/health`: `ok`, service `base2026`, search `d1-fts5`.
- Live Evidence Brief V1: `ready`.
- Live Evidence Brief V2: `full`, five findings.
- Public D1: 2,170 documents, 1,572 distinct sources, 48 applied projections,
  78 projected cards and zero public full transcripts.
- Live desktop/mobile homepage and `/founder`: passed without observed layout or
  request failures.

## Source boundary

The release contains only owner-approved public portfolio material. Private
owner-profile fields, resume/CV, rates, authorization wording, calendar data,
raw client evidence and private pipeline state were not included. No commit,
push, intake or private publication was performed in this release pass.
