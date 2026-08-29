# Base2026 Agent Operating Contract

## Rule 0: repo files are source of truth

Codex, Hermes, and any other agent must start from checked-in project files, not from chat memory.

Before any meaningful work, read:

- `docs/project-memory/CURRENT_STATUS.md`
- `docs/project-memory/PROJECT_STATE.md`
- `docs/project-memory/ACTIVE_PHASE.md`
- `docs/project-memory/NEXT_ACTION.md`
- `docs/project-memory/DECISIONS.md`
- `docs/project-memory/DATA_SOURCES.md`
- `docs/project-memory/STATUS_BOARD.csv`
- `docs/project-memory/PHASES.md`
- `docs/project-memory/PUBLICATION_BOUNDARY.md`

`CURRENT_STATUS.md`, `PROJECT_STATE.md`, `ACTIVE_PHASE.md`, and
`NEXT_ACTION.md` must stay compact and current. Preserve history in Git and
dated receipts; never turn these files back into chronological transcript
dumps with multiple competing "current" sections.

For deployment or automation tasks, also read:

- `docs/project-memory/DEPLOYMENT_RUNBOOK.md`
- `docs/project-memory/HERMES_RUNBOOK.md`

For any Cloudflare, TikTok pipeline, cloud acquisition, Workers AI, or
automatic-publication task, also read:

- `docs/BASE2026_CLOUDFLARE_PIPELINE_CANONICAL_OPERATING_MANUAL.md`

That manual is the canonical architecture and operating reference. Older
pipeline architecture notes are historical receipts. Recheck live Cloudflare
deployments and D1 state before using any dated counter or version ID.

For public UI tasks, also read:

- `docs/project-memory/VISUAL_SYSTEM_CONTRACT.md`

## Public/private boundary

Never commit or publish private research, raw source vaults, credentials, logs, generated release archives, local database files, audio/video files, or unreviewed raw captions.

Use `docs/GIT_PUBLICATION_AUDIT.md` and `docs/project-memory/PUBLICATION_BOUNDARY.md` before staging.

## Work protocol

One phase or tightly scoped task per session.

At task start:

- check `git status`
- confirm current active phase from `ACTIVE_PHASE.md`
- confirm forbidden actions
- identify expected output files

At task end:

- update `NEXT_ACTION.md`
- update `PROMPT_LOG.md`
- update `STATUS_BOARD.csv` when phase state changes
- update `DATA_SOURCES.md` when source status changes
- update `DECISIONS.md` only for real durable decisions
- report changed files and suggested commit message

Do not commit, push, deploy, or run intake automation unless the user asked for it in the current task.

## Reviewer role

Every implementation pass must include a reviewer pass:

- check whether task output matches the request
- check public/private leakage risk
- check whether docs point to correct files
- check whether next action is concrete
- if a mismatch exists, fix root cause before reporting done
