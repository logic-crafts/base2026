# Base2026 CTPH / MoneyPage indexation plan — 2026-06-26

Status: first controlled batch submitted; moderate-aggressive master set recalculated and live-gated.

## What was created

- Seed URL list: `docs/project-memory/BASE2026_CTPH_MONEYPAGE_INDEXATION_SEED_URLS_2026_06_26.txt`
- Moderate-aggressive master URL list: `docs/project-memory/BASE2026_CTPH_MONEYPAGE_INDEXATION_MASTER_URLS_2026_06_26.txt`
- Moderate-aggressive strategy: `docs/project-memory/BASE2026_CTPH_MONEYPAGE_MODERATE_AGGRESSIVE_STRATEGY_2026_06_26.md`
- Live eligibility checks: `output/indexnow/base2026-ctph-money-first-batch-checks.csv`
- Master live eligibility checks: `output/indexnow/base2026-ctph-money-master-checks-20260626.csv`
- IndexNow dry-run payload: `output/indexnow/base2026-ctph-money-first-batch-indexnow-payload.json`
- Master IndexNow payload: `output/indexnow/base2026-ctph-money-master-payload-20260626.json`
- IndexNow key-ready payload: `output/indexnow/base2026-ctph-money-first-batch-indexnow-payload.with-key.json`
- IndexNow root key file: `/var/www/alex-yarosh/indexnow-241f253997100ebfc7416fbe9ea95422.txt` → live keyLocation: `https://aggressorbulkit.online/indexnow-241f253997100ebfc7416fbe9ea95422.txt`
- Optional `/knowledge/` key file source: `web/static/indexnow-241f253997100ebfc7416fbe9ea95422.txt`
- Working ledger: `docs/project-memory/BASE2026_CTPH_MONEYPAGE_INDEXATION_LEDGER_2026_06_26.csv`
- Master ledger: `docs/project-memory/BASE2026_CTPH_MONEYPAGE_INDEXATION_MASTER_LEDGER_2026_06_26.csv`

## Live gate result

- First controlled batch input URLs: 38
- First controlled batch eligible: 38
- Moderate-aggressive master input URLs: 50
- Moderate-aggressive master eligible: 50
- Failed gate in submitted master set: 0
- Excluded during planning: 18 extra topic candidates that were live but still `noindex`; they are intentionally not submitted until promoted.
- All submitted URLs returned `200`, no `noindex`, and self-canonical according to `scripts/prepare-indexnow-payload.py`.

## Batch composition

First controlled batch:

- ctph_hub: 1
- ctph_proof: 4
- money_page: 7
- proof_hub: 7
- source_evidence: 6
- topic_hub: 1
- topic_proof: 12

Moderate-aggressive master set:

- knowledge_hub: 1
- ctph_hub: 1
- ctph_proof: 4
- money_page: 7
- proof_hub: 6
- source_evidence: 18
- topic_hub: 1
- topic_proof: 12

## Execution rule

1. Google: submit sitemap / inspect priority URLs manually in GSC; do not automate request-indexing clicks and do not use Google Indexing API for normal pages.
2. Bing: use IndexNow only after the domain key file is hosted; submit only eligible changed URLs from the ledger.
3. Expansion: do not add city/niche pages to this batch until each has unique local evidence, passes duplicate/doorway QA, is self-canonical, and is intentionally switched from `noindex` to `index`.
4. Every future batch must be produced from the ledger + live gate, not from a raw generated URL dump.

## Current implementation state

The first controlled batch and the moderate-aggressive master set have both been submitted to IndexNow with the root key location after live verification.

Autopilot now uses the master list:

```bash
INPUT="docs/project-memory/BASE2026_CTPH_MONEYPAGE_INDEXATION_MASTER_URLS_2026_06_26.txt"
```

For future manual resubmission:

```bash
python3 scripts/prepare-indexnow-payload.py \
  --input docs/project-memory/BASE2026_CTPH_MONEYPAGE_INDEXATION_MASTER_URLS_2026_06_26.txt \
  --key "$INDEXNOW_KEY" \
  --key-location "https://aggressorbulkit.online/indexnow-$INDEXNOW_KEY.txt" \
  --out output/indexnow/base2026-ctph-money-master-payload-20260626.json \
  --checks-out output/indexnow/base2026-ctph-money-master-checks-20260626.csv
```

Then submit only if the checks still show `eligible_urls == input_urls`:

```bash
python3 scripts/prepare-indexnow-payload.py \
  --input docs/project-memory/BASE2026_CTPH_MONEYPAGE_INDEXATION_MASTER_URLS_2026_06_26.txt \
  --key "$INDEXNOW_KEY" \
  --key-location "https://aggressorbulkit.online/indexnow-$INDEXNOW_KEY.txt" \
  --submit
```
