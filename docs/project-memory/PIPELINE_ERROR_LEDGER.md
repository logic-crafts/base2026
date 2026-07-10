# Base2026 Pipeline Error Ledger

Last updated: 2026-06-18

Purpose: keep repeated launch/intake mistakes out of chat memory and inside the repository operating contract.

## Canonical Release Pipeline

Use `scripts/base2026-release-gate.ps1` as the release command center.

For a TikTok data-changing release:

```powershell
pwsh ./scripts/base2026-release-gate.ps1 `
  -ReleaseName <release-name> `
  -BatchSet <hermes-polish-batch-set> `
  -RunAfterPolish `
  -Deploy
```

For a package-only dry launch:

```powershell
pwsh ./scripts/base2026-release-gate.ps1 `
  -ReleaseName <release-name> `
  -BatchSet <hermes-polish-batch-set> `
  -RunAfterPolish `
  -PackageOnly
```

The gate order is:

1. `git diff --check`
2. current-batch transcript polish status
3. `hermes-tiktok-refresh.ps1 -AfterPolish`
4. newest-source content readiness
5. publication boundary audit
6. GitHub metadata validation
7. public export policy
8. public release contract
9. package public release
10. optional VPS deploy, Meilisearch reindex, live SEO crawl, and mobile visual QA

For a controlled refresh after `social-discover.py` and `import-social-discovery-to-tiktok-csv.py --apply` already added the intended rows to the private queue, use:

```powershell
pwsh ./scripts/hermes-tiktok-refresh.ps1 `
  -SkipInventory `
  -BatchSet <hermes-polish-batch-set> `
  -TranscriptLimit <expected queued count> `
  -AsrLimit <expected queued count> `
  -PolishLimit <expected queued count>
```

Rule: do not run broad inventory when the intended work is a bounded post-import queue. `-SkipInventory` preserves the existing `videos.csv` queue and processes only already-queued rows.

## Errors We Already Hit

### Help flags accidentally ran real work

Observed: running a script with an assumed help flag still executed inventory/crawl work.

Fix:

- `scripts/hermes-tiktok-refresh.ps1 -Help` now exits before inventory/intake.
- Use `scripts/base2026-release-gate.ps1 -Help` for the canonical pipeline.

Rule: do not guess help flags on scripts that do not explicitly support them.

### Fresh public source shipped without intelligence layer

Observed: a 2026-06-17 `@webhivedigital` source had public text but no public topic or public insight card. Packaging correctly stopped at `check-public-content-readiness.py --latest 1 --fail`.

Fix:

- Create a strict source-backed candidate.
- Run `base2026-import-claim-candidates.py`.
- Run `base2026-review-insight-candidates.py`.
- Promote only exact-match `promotion_candidate` rows with `base2026-promote-insight-candidates.py`.
- Rebuild/export through AfterPolish before packaging.

Rule: never bypass this gate. A newest public source should not launch as plain transcript/source text without at least one reviewed public intelligence layer.

ay41 proof: the same gate blocked `tiktok-video-7652732487843581206` after the social bridge added it to the queue. The fix was not to bypass the gate; the fix was to add one exact-evidence reviewed insight for `Search Console / high-intent queries`, rerun `AfterPolish`, and then deploy through `base2026-release-gate.ps1`.

### Transcript polish uncertainty leaked too late

Observed: caption-polish batches can look good while a few rows still need source-audio review.

Fix:

- `tiktok-polish-status.py --batch-dir <batch>` must pass before `AfterPolish`.
- Use ASR/source-audio checks for uncertain entities, plugin names, and repeated/damaged text.
- Keep audio, ASR, and private QA under ignored local paths only.

Rule: current-batch polish is a hard gate. Historical debt must stay gated but must not block a fresh clean batch.

ay41 proof: QA JSON for the 3-source social-bridge batch had to pass without uncertainty language before `AfterPolish`. If a QA note says a transcript is uncertain, the row is not ready for public release even if the text looks readable.

### Deploy and data refresh were treated as separate mental flows

Observed: data refresh, public export, package, deploy, reindex, and live QA were easy to run out of order.

Fix:

- `base2026-release-gate.ps1` owns the end-to-end sequence.
- `hermes-tiktok-refresh.ps1` owns local intake/rebuild/export only.
- `deploy-public-vps.ps1` owns upload, symlink switch, nginx reload, and reindex.

Rule: do not run deploy directly for data-changing TikTok releases unless the release gate has already passed or the command is an explicit hotfix from a reviewed export.

### Social discovery got confused with TikTok intake

Observed: a platform-neutral discovery plan could easily become a direct write into the TikTok CSV, or accidentally invite Instagram rows into the TikTok-only intake lane.

Fix:

- `scripts/social-discover.py` writes only private JSONL under ignored `.planning/`.
- `scripts/import-social-discovery-to-tiktok-csv.py` is the only bridge from `.planning/social-discovered.jsonl` to `12_knowledge-base/sources/tiktok/videos.csv`.
- The bridge is dry-run by default and requires `--apply` to mutate the private local CSV.
- Every apply creates an ignored backup under `.planning/backups/`.

Rule: run discovery, then dry-run import, inspect counts, then apply. Never import non-TikTok rows into `videos.csv`, and never trigger public export/deploy from the importer.

### Check-only mode wrote to the private CSV

Observed: `scripts/hermes-tiktok-refresh.ps1 -CheckOnly` used to run `tiktok-backfill-inventory.ps1` before checking the flag. Because inventory writes `videos.csv`, a supposedly read-only check could add queued rows.

Fix:

- `scripts/hermes-tiktok-refresh.ps1 -CheckOnly` now runs `social-discover.py` to an ignored check-only JSONL path.
- It then runs `import-social-discovery-to-tiktok-csv.py` without `--apply`.
- It prints the current pending summary and exits before legacy inventory/caption/ASR/polish stages.

Rule: `-CheckOnly` and `-DryRun` must preserve the exact `videos.csv` hash before/after. Data-changing inventory/import must be explicit.

### Bounded creator refresh accidentally expanded into broad inventory

Observed: running `hermes-tiktok-refresh.ps1 -BatchSet ...` after a controlled one-row social import also ran legacy inventory with `PlaylistEnd=1000` across all configured creators, which expanded the private backlog by thousands of rows.

Fix:

- `scripts/hermes-tiktok-refresh.ps1` now has `-SkipInventory`.
- For post-import queue processing, run `-SkipInventory` with explicit `-TranscriptLimit`, `-AsrLimit`, and `-PolishLimit` sized to the intended queued slice.
- If broad inventory is accidentally run, restore the private CSV from the ignored `.planning/backups/` backup and re-apply only the intended social import.

Rule: after `social-discover.py` plus importer `--apply`, never run the normal refresh runner without `-SkipInventory` unless the task is explicitly to expand inventory across all configured creators.

### Source-review debt was managed from chat memory

Observed: after the AI Recommends pass, held videos were easy to discuss as loose counts (`47 needs review`, `23 ASR`, `61 held`) instead of a deterministic work queue.

Fix:

- `scripts/tiktok-source-review-queue.py` reads private local `videos.csv` and classifies `needs_source_review` rows by evidence availability.
- Local-caption rows are the first review lane.
- Audio-backed rows go through ASR retry before any public decision.
- Rows without local caption or audio stay private until a usable source is recovered.

Rule: before clearing any `needs_source_review` row, run `python3 scripts/tiktok-source-review-queue.py --limit 25` and work from the generated queue. Do not bulk-pass held rows based on polished text alone.

### QA pass did not clear private CSV source-review status

Observed: three local-caption rows were mechanically cleaned and approved with `scripts/tiktok-qa-review-apply.py`, but the public export still excluded them because private `videos.csv` kept `transcript_status=needs_source_review`.

Fix:

- Added `scripts/tiktok-clear-reviewed-source-rows.py`.
- The script is dry-run by default and accepts explicit `--video-id` values or a QA manifest.
- It clears only rows that are still `needs_source_review`, have QA JSON status `pass`, and have both clean and polished transcript files.
- On `--apply`, it backs up `videos.csv` under ignored `.planning/backups/`, sets `transcript_status=transcribed`, sets `review_status=source_review_pass`, and appends an audit note.

Rule: `tiktok-qa-review-apply.py` updates QA artifacts; `tiktok-clear-reviewed-source-rows.py` is the only allowed transition from reviewed `needs_source_review` back into the public export lane.

### 2026-07-03: QA-needs-review rows stalled production refresh

Observed: the July TikTok creator refresh had fresh polished rows, but production could not advance cleanly because mixed polish batches contained legitimate QA `needs_review` outputs. Treating `needs_review` as a hard pipeline failure prevented `AfterPolish`/release flow, while leaving those rows as `transcribed` let public export/readiness see fresh source-only rows.

Fix:

- Added `scripts/tiktok-apply-qa-gates.py` to apply QA outcomes back to private `videos.csv` before SQLite rebuild/export.
- `hermes-tiktok-refresh.ps1 -AfterPolish -BatchSet <batch>` now runs the QA gate before rebuild/export.
- `base2026-release-gate.ps1 -RunAfterPolish` allows mixed batches only at the pre-release polish-status step; `AfterPolish` then gates non-pass rows private. Missing polish output or invalid QA still fails.
- Added exact-evidence reviewed Source Intelligence cards for the newest publishable rows before deploy.

Proof: release `base2026-tiktok-fresh-qa-gated-20260703` deployed live. Recent window since 2026-07-01 resolved to 19 QA-pass/exportable rows and 29 private `needs_source_review` rows. Public export passed with `source_records=1609`, `passages=2183`, `public_insight_cards=1074`; newest-source readiness latest 3 had `blocked_source_only_records=0`. Live source pages `7657320786566450445`, `7657320834268204301`, and `7657749901186583816` return 200; held video `7658094847831723278` returns 404.

Rule: `needs_review` is a valid private outcome, not a production outcome. Every post-polish release must apply QA gates before `build-kb-sqlite.py`/`export-public-tiktok.py`; only QA-pass rows remain `transcribed` for public export.

## Current Policy

- Raw captions, raw ASR, audio/video, logs, local DBs, `.planning/`, `output/`, `public-data/`, and private reviewed-candidate archives are never GitHub source.
- Approved/reviewed public insight cards are durable through ignored replay archives and clean SQLite rebuild.
- New public text needs at least one source-backed topic or public insight before release.
- GitHub commit/push happens only after deploy/live QA and explicit user approval.
