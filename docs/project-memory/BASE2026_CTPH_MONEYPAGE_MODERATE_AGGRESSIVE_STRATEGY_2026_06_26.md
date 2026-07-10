# Base2026 CTPH / MoneyPage moderate-aggressive indexation strategy — 2026-06-26

Status: strategy recalculated after rechecking Base2026 public data, new TikTok source records, live URL gates, and external guidance on IndexNow / Google pSEO risk.

## Position

Use a **moderately aggressive, evidence-first** indexation posture:

- Aggressive enough: expand from 38 to 50 submitted URLs immediately, including 12 fresh TikTok source-evidence pages from the latest 2026-06-24..26 data.
- Safe enough: do not submit noindex topic pages, weak city/niche pages, query/filter URLs, or generated pages without live proof and self-canonical checks.
- Google-safe: rely on sitemap + GSC monitoring/inspection; do not use Google Indexing API or automated request-indexing clicks for normal pages.
- Bing/AI-search aggressive: use IndexNow daily for the selected live-gated URL set.

## What was checked

- Base2026 public TikTok data under `public-data/tiktok/`.
- Latest source records captured/published around 2026-06-24..26.
- Existing CTPH/MoneyPage seed and IndexNow artifacts.
- Live URL gates through `scripts/prepare-indexnow-payload.py`.
- External guidance:
  - Google spam policies: avoid doorway/scaled-content-abuse patterns.
  - IndexNow docs: root key location is recommended; `200` and `202` are accepted states.
  - pSEO guidance: staged batches, noindex sparse pages, monitor indexing rate before scaling further.

## Decision

Rejected over-aggressive expansion of extra topic pages for now because the candidate topic URLs currently return `noindex` live. They stay out of submission until intentionally promoted.

Accepted expansion:

- Original controlled batch: 38 URLs.
- Fresh evidence expansion: 12 recent TikTok source pages.
- Master submitted set: 50 URLs.

## Quality gate

Every URL must pass:

1. expected host: `aggressorbulkit.online`;
2. no query-string crawl state;
3. HTTP `200`;
4. no `noindex`;
5. self-canonical;
6. belongs to allowed classes: money page, CTPH/proof hub, topic proof already indexable, source evidence.

## Files

- Master URL list: `docs/project-memory/BASE2026_CTPH_MONEYPAGE_INDEXATION_MASTER_URLS_2026_06_26.txt`
- Master ledger: `docs/project-memory/BASE2026_CTPH_MONEYPAGE_INDEXATION_MASTER_LEDGER_2026_06_26.csv`
- Master live checks: `output/indexnow/base2026-ctph-money-master-checks-20260626.csv`
- Master payload: `output/indexnow/base2026-ctph-money-master-payload-20260626.json`
- Autopilot script: `~/.hermes/scripts/base2026-indexnow-autopilot.sh`

## Next scaling rule

Do not jump from 50 to hundreds blindly. Next expansion should be another 25–75 URLs only after one of these is true:

- GSC/Bing indicators show healthy discovery/indexing for current batches; or
- a page class is upgraded from `noindex` to `index` with stronger evidence and internal links; or
- new source-evidence pages are published and pass the live gate.

City/niche pages remain excluded until each has unique local evidence and a real user-useful angle, not just variable substitution.
