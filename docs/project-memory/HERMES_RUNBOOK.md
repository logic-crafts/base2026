# Hermes Runbook

## Current production boundary — 2026-08-23

Hermes/local LaunchAgents are no longer a production dependency for the daily
TikTok pipeline. Cloudflare owns scheduled discovery, capture, private storage,
Workers AI, durable reconciliation, automatic excerpt-card projection, and
verification. The local adapter is disabled and retained only as rollback
material. ChatGPT is manual owner-initiated fallback only.

For current runtime operations use
`docs/BASE2026_CLOUDFLARE_PIPELINE_CANONICAL_OPERATING_MANUAL.md`. The local
cycle below is historical/rollback guidance and must not be re-enabled merely
because it remains documented.

Hermes should become the maintainer automation agent for TikTok refresh.

## Intended cycle

1. Check configured creator accounts.
2. Detect new videos by source URL or video id.
3. Pull available captions.
4. Produce raw local intake record.
5. Run faithful English transcript polish.
6. Split transcript into readable paragraphs.
7. Build GPT/Codex source-only claim extraction packets when insight cards are missing.
8. Apply strict JSON review output back into private candidates.
9. Run deterministic evidence verification.
10. Import only reviewed/evidence-verified candidates as private/pending.
11. Update local public export only after review gates.
12. Reindex Meilisearch only if data changed.
13. Package and deploy only after QA gate.
14. Update `DATA_SOURCES.md`, `STATUS_BOARD.csv`, and `PROMPT_LOG.md`.

## Model routing

- Task A inventory/dedupe/status: no LLM or GPT-5.3.
- Task B captions/ASR routing: no LLM or GPT-5.3.
- Task C faithful transcript polish: Codex/GPT review lane; use ChatGPT 5.5 Medium when available for current manual quality work.
- Task D escalation QA: GPT-5.5 only for damaged captions, uncertain ASR, low preservation score, or QA `needs_review`.
- Task E insight-card extraction/review for launch-quality small batches: ChatGPT 5.5 Medium or Codex/GPT through generated packets, strict JSON, deterministic evidence verification after. Do not use local LLMs as the quality source for current public card copy.
- Task F rebuild/export/package: no LLM or GPT-5.3 for status text only.

## Rules

- Do not invent transcript content.
- Do not translate to Russian.
- Do not publish raw unreviewed captions.
- Do not publish generated insight-card candidates directly.
- Do not use browser ChatGPT as a scheduled hidden worker.
- Do not run uncontrolled infinite loops.
- Keep logs local and out of git.

## First safe milestone

Build dry-run mode:

- check creators
- report potential new videos
- do not write database
- do not deploy

## Platform-neutral discovery preview

Use `scripts/social-discover.py` for private discovery smoke tests before expanding beyond TikTok:

```bash
.venv/bin/python scripts/social-discover.py \
  --config config/tiktok-intake-queue.local.json \
  --creator build_in_public \
  --out .planning/social-discovered-smoke.jsonl \
  --limit-per-creator 3
```

This script writes normalized JSONL under ignored `.planning/`, reports adapter/count/failure status per creator, and does not write `videos.csv`, public export, deploy, or Meilisearch.

Bridge the private discovery spool into the TikTok queue only through a dry-run-first import:

```bash
.venv/bin/python scripts/import-social-discovery-to-tiktok-csv.py \
  --input .planning/social-discovered.jsonl \
  --report .planning/social-discovery-import-dry-run.json
```

Apply only after the report shows clean TikTok-only candidates:

```bash
.venv/bin/python scripts/import-social-discovery-to-tiktok-csv.py \
  --input .planning/social-discovered.jsonl \
  --apply \
  --report .planning/social-discovery-import-report.json
```

The importer dedupes by `video_id`, writes an ignored backup before changing `12_knowledge-base/sources/tiktok/videos.csv`, keeps old rows `out_of_scope_old`, and never triggers export, Meilisearch, deploy, or Git staging.

Capability source of truth:

```bash
.venv/bin/python scripts/base2026-worker.py doctor
```

Optional `gallery-dl`, `instaloader`, and `whisper.cpp`/`whisper-cpp` are reported as capabilities. Missing optional tools must not fail doctor; Instagram discovery is disabled/degraded until `gallery-dl` or `instaloader` is available.

## Current safe execution policy

`scripts/hermes-tiktok-refresh.ps1 -CheckOnly` is read-only. It runs `scripts/social-discover.py`, runs `scripts/import-social-discovery-to-tiktok-csv.py` without `--apply`, prints the current pending summary, and must preserve the exact `videos.csv` hash before/after.

Run local refresh without deploy first. If new caption transcripts are produced, create a small polish batch and hand only that batch to the Codex/GPT quality lane. For current launch work, prefer ChatGPT 5.5 Medium over local LLMs.

Use `scripts/run-hermes-polish-worker.ps1 -BatchSet <batch-set>` only when a dedicated GPT/Codex handoff is needed. The script writes the worker prompt and result under ignored `.planning/` paths and uses `codex exec --ignore-user-config --ignore-rules` to avoid loading the full project context.

Use `scripts/register-hermes-webui-task.ps1 -Start` to repair/start the local `Hermes WebUI` scheduled task. The task must execute PowerShell by absolute path and use the local Hermes WebUI launcher directory as working directory. Override defaults with `HERMES_PWSH_PATH`, `HERMES_WEBUI_LAUNCHER`, or `HERMES_WEBUI_WORKDIR` when needed.

For data-changing public releases, do not jump from Hermes directly to deployment. Use the canonical gate runner:

```powershell
pwsh ./scripts/base2026-release-gate.ps1 `
  -ReleaseName <release-name> `
  -BatchSet <batch-set> `
  -RunAfterPolish `
  -Deploy
```

The gate runner owns current-batch polish status, `AfterPolish`, newest-source content readiness, publication boundary, metadata, export policy, package, deploy, reindex, and live QA. See `docs/project-memory/PIPELINE_ERROR_LEDGER.md`.

## AfterPolish rule

`scripts/hermes-tiktok-refresh.ps1 -AfterPolish -BatchSet <batch-set>` must validate only the current batch via `scripts/tiktok-polish-status.py --batch-dir <batch-dir>`.

Do not block a fresh successful batch because older historical transcripts still have `needs_review`.

## ASR/source review rule

If captions fail and the downloaded fallback media has no audio stream, mark the video `needs_source_review`, not `needs_asr`. Do not retry Whisper forever when there is no audio track.
