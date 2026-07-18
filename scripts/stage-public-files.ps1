param(
  [switch]$Apply,
  [switch]$SkipPreflight,
  [switch]$SkipLicenseCheck,
  [switch]$SkipRemoteCheck
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

function Resolve-RequiredCommand {
  param([string[]]$Names)
  foreach ($Name in $Names) {
    $Command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($Command) {
      return $Command.Source
    }
  }
  throw "Missing required command: $($Names -join ' or ')"
}

$Python = Resolve-RequiredCommand @("python", "python3")
$PowerShell = Resolve-RequiredCommand @("pwsh", "powershell")
$AuditScript = Join-Path $Root "scripts/audit-publication-boundary.py"

$StagePaths = @(
  ".env.example",
  ".gitignore",
  ".github",
  ".github/pull_request_template.md",
  ".github/ISSUE_TEMPLATE",
  "AGENTS.md",
  "README.md",
  "requirements-local-worker.txt",
  "SECURITY.md",
  "CONTRIBUTING.md",
  "CODE_OF_CONDUCT.md",
  "LICENSE",
  "contracts",
  "config/creator-profiles.json",
  "config/creators.example.json",
  "docs/DEPLOYMENT_LOG.md",
  "docs/GIT_PUBLICATION_AUDIT.md",
  "docs/GITHUB_LAUNCH_CHECKLIST.md",
  "docs/LICENSE_DECISION_NOTES.md",
  "docs/PUBLICATION_AUDIT_REPORT_2026_06_08.md",
  "docs/PUBLICATION_STAGING_PLAN.md",
  "docs/PUBLIC_TIKTOK_DEPLOYMENT.md",
  "docs/project-memory",
  "docs/public-pages",
  "docs/research",
  "docs/schemas",
  "scripts/apply-license.ps1",
  "scripts/audit-publication-boundary.py",
  "scripts/base2026-build-backfill-queue.py",
  "scripts/base2026-apply-chatgpt-review.py",
  "scripts/base2026-build-chatgpt-review-packet.py",
  "scripts/base2026-claim-extract-local.py",
  "scripts/base2026-controller.py",
  "scripts/base2026-daily-digest.py",
  "scripts/base2026-evidence-verify.py",
  "scripts/base2026-import-claim-candidates.py",
  "scripts/base2026-prepare-needs-human-review.py",
  "scripts/base2026-promote-insight-candidates.py",
  "scripts/base2026-resolve-candidate-decisions.py",
  "scripts/base2026-review-legacy-insights.py",
  "scripts/base2026-review-insight-candidates.py",
  "scripts/base2026-worker.py",
  "scripts/check-public-export-policy.py",
  "scripts/deploy-public-vps.ps1",
  "scripts/derive-base2026-phase0-p1-preview.py",
  "scripts/export-public-tiktok.py",
  "scripts/fetch-tiktok-avatars.py",
  "scripts/generate-base2026-sitemap.py",
  "scripts/generate-info-pages.py",
  "scripts/generate-public-pages.py",
  "scripts/build-kb-sqlite.py",
  "scripts/hermes-tiktok-refresh.ps1",
  "scripts/import-tiktok-staging-to-kb.py",
  "scripts/kb-audit.py",
  "scripts/meili-index-public.py",
  "scripts/mobile-visual-qa.mjs",
  "scripts/package-public-hotfix-from-export.ps1",
  "scripts/package-public-release.ps1",
  "scripts/preflight-github-launch.ps1",
  "scripts/public_manifest_contract.py",
  "scripts/register-hermes-tiktok-check-task.ps1",
  "scripts/server-patch-nginx-base2026.py",
  "scripts/stage-public-files.ps1",
  "scripts/tiktok-backfill-inventory.ps1",
  "scripts/tiktok-caption-browser-extract.mjs",
  "scripts/tiktok-clear-reviewed-source-rows.py",
  "scripts/tiktok-faithful-polish-local.py",
  "scripts/tiktok-normalize-polished-entities.py",
  "scripts/tiktok-process-transcripts.ps1",
  "scripts/tiktok-polish-audit.py",
  "scripts/tiktok-qa-triage.py",
  "scripts/tiktok-qa-review-apply.py",
  "scripts/tiktok-polish-runner.ps1",
  "scripts/tiktok-source-review-audit.py",
  "scripts/tiktok-ytdlp-metadata-extract.py",
  "scripts/repair-public-text-excerpts.py",
  "scripts/validate-github-metadata.py",
  "scripts/validate-public-text-excerpts.py",
  "scripts/validate-public-manifests.py",
  "tests/test_generate_base2026_sitemap.py",
  "tests/test_derive_base2026_phase0_p1_preview.py",
  "tests/test_package_public_hotfix_contract.py",
  "tests/test_public_manifest_contract.py",
  "tests/test_source_detail_v2_contract_gate.py",
  "web/ARCHITECTURE.md",
  "web/KNOWLEDGE_UI_GUIDE.md",
  "web/README.md",
  "web/UI_AUDIT.md",
  "web/server.py",
  "web/static"
)

if (-not $SkipPreflight) {
  $PreflightArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ".\scripts\preflight-github-launch.ps1")
  if ($SkipLicenseCheck) {
    $PreflightArgs += "-SkipLicenseCheck"
  }
  if ($SkipRemoteCheck) {
    $PreflightArgs += "-SkipRemoteCheck"
  }
  & $PowerShell @PreflightArgs
  if ($LASTEXITCODE -ne 0) {
    throw "preflight failed; refusing to stage files."
  }
}

if ($Apply -and -not $SkipLicenseCheck -and -not (Test-Path -LiteralPath ".\LICENSE")) {
  throw "LICENSE is missing; refusing to stage for GitHub launch. Choose a license first or run an explicit audit-only dry run without -Apply."
}

& $Python $AuditScript
if ($LASTEXITCODE -ne 0) {
  throw "publication boundary audit failed; refusing to stage files."
}

$AuditJson = & $Python $AuditScript --json | ConvertFrom-Json
$ChangedFiles = @($AuditJson.public_safe_files)

function Convert-ToPosixPath {
  param([string]$Path)
  return ($Path -replace '\\', '/').TrimEnd('/')
}

function Test-PathCoveredByStageList {
  param([string]$ChangedPath)
  $NormalizedChanged = Convert-ToPosixPath $ChangedPath
  foreach ($StagePath in $StagePaths) {
    $NormalizedStage = Convert-ToPosixPath $StagePath
    if ($NormalizedChanged -eq $NormalizedStage -or $NormalizedChanged.StartsWith("$NormalizedStage/")) {
      return $true
    }
  }
  return $false
}

$Uncovered = @()
foreach ($ChangedPath in $ChangedFiles) {
  if (-not (Test-PathCoveredByStageList $ChangedPath)) {
    $Uncovered += $ChangedPath
  }
}

if ($Uncovered.Count -gt 0) {
  Write-Output "uncovered_public_safe_files=$($Uncovered.Count)"
  $Uncovered | ForEach-Object { Write-Output $_ }
  throw "stage allowlist does not cover every public-safe changed file."
}

$ExistingPaths = @()
foreach ($Path in $StagePaths) {
  if (Test-Path -LiteralPath $Path) {
    $ExistingPaths += $Path
  }
}

Write-Output "stage_path_count=$($ExistingPaths.Count)"
foreach ($Path in $ExistingPaths) {
  Write-Output $Path
}

if (-not $Apply) {
  Write-Output "dry_run=true"
  Write-Output "Run with -Apply to execute git add on the listed paths."
  if (-not (Test-Path -LiteralPath ".\LICENSE")) {
    Write-Output "license_missing=true"
    Write-Output "Actual staging for GitHub launch is blocked until LICENSE exists."
  }
  exit 0
}

git add -- $ExistingPaths
if ($LASTEXITCODE -ne 0) {
  throw "git add failed."
}

if ($StagePaths.Count -gt 0) {
  git add -u -- $StagePaths
  if ($LASTEXITCODE -ne 0) {
    throw "git add -u failed."
  }
}

git diff --cached --stat
git diff --cached --name-only
Write-Output "staged=true"
