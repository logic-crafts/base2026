param(
  [string]$ReleaseName = "",
  [string]$BatchSet = "",
  [switch]$RunAfterPolish,
  [switch]$PackageOnly,
  [switch]$Deploy,
  [switch]$SkipLiveQa,
  [switch]$Help,
  [int]$LatestReadiness = 1
)

$ErrorActionPreference = "Stop"

function Show-Usage {
  Write-Output @"
Base2026 release gate

Purpose:
  Run the canonical public-release pipeline in a fixed order:
  polish gate -> rebuild/export gate -> publication boundary -> package -> optional deploy/reindex -> optional live QA.

Examples:
  pwsh ./scripts/base2026-release-gate.ps1 -ReleaseName base2026-example-ay00-20260618 -BatchSet hermes-polish-YYYYMMDD-HHMMSS -RunAfterPolish -PackageOnly
  pwsh ./scripts/base2026-release-gate.ps1 -ReleaseName base2026-example-ay00-20260618 -BatchSet hermes-polish-YYYYMMDD-HHMMSS -RunAfterPolish -Deploy

Rules:
  - Does not commit or push.
  - Does not bypass source/content readiness.
  - Does not publish raw captions, ASR, media, logs, DBs, or private review artifacts.
  - -Help prints this usage and exits without running the pipeline.
"@
}

if ($Help) {
  Show-Usage
  exit 0
}

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

function Assert-NativeSuccess {
  param([string]$Label)
  if ($LASTEXITCODE -ne 0) {
    throw "$Label failed with exit code $LASTEXITCODE."
  }
}

function Run-Step {
  param([string]$Label, [scriptblock]$Command)
  Write-Output ""
  Write-Output "==> $Label"
  $global:LASTEXITCODE = 0
  & $Command | Write-Output
  if ((-not $?) -or ($LASTEXITCODE -ne 0)) {
    throw "$Label failed."
  }
}

if (-not $ReleaseName) {
  $ReleaseName = "base2026-release-gate-" + (Get-Date -Format "yyyyMMdd-HHmmss")
}

if ($Deploy -and $PackageOnly) {
  throw "Choose either -Deploy or -PackageOnly, not both."
}

if ($RunAfterPolish -and -not $BatchSet) {
  throw "-RunAfterPolish requires -BatchSet so the polish gate is scoped to the current batch."
}

Run-Step "git diff whitespace check" {
  git diff --check
  Assert-NativeSuccess "git diff --check"
}

if ($BatchSet) {
  $BatchDir = Join-Path $Root "12_knowledge-base\sources\tiktok\transcript-polish-batches\$BatchSet"
  if (-not (Test-Path $BatchDir)) {
    throw "BatchSet not found: $BatchDir"
  }
  Run-Step "current batch polish status" {
    if ($RunAfterPolish) {
      # Mixed batches are allowed at this pre-release step: `needs_review` rows are
      # moved to the private source-review lane by hermes-tiktok-refresh -AfterPolish
      # before rebuild/export. Missing polish output or invalid JSON still fails.
      python3 ./scripts/tiktok-polish-status.py --batch-dir $BatchDir --json --allow-needs-review
    }
    else {
      python3 ./scripts/tiktok-polish-status.py --batch-dir $BatchDir --json
    }
    Assert-NativeSuccess "tiktok-polish-status"
  }
}

if ($RunAfterPolish) {
  Run-Step "AfterPolish rebuild/export" {
    pwsh -NoProfile -ExecutionPolicy Bypass -File ./scripts/hermes-tiktok-refresh.ps1 -AfterPolish -BatchSet $BatchSet
    Assert-NativeSuccess "hermes-tiktok-refresh AfterPolish"
  }
}

Run-Step "public content readiness" {
  python3 ./scripts/check-public-content-readiness.py --data-root ./public-data/tiktok --latest $LatestReadiness --fail
  Assert-NativeSuccess "check-public-content-readiness"
}

Run-Step "publication boundary" {
  python3 ./scripts/audit-publication-boundary.py
  Assert-NativeSuccess "audit-publication-boundary"
}

Run-Step "GitHub metadata" {
  python3 ./scripts/validate-github-metadata.py
  Assert-NativeSuccess "validate-github-metadata"
}

Run-Step "public export policy" {
  python3 ./scripts/check-public-export-policy.py ./public-data/tiktok
  Assert-NativeSuccess "check-public-export-policy"
}

Run-Step "public release contract" {
  python3 ./scripts/validate-public-release-contract.py --export-dir ./public-data/tiktok --baseline-export-dir ./public-data/tiktok --enforce-count-floor
  Assert-NativeSuccess "validate-public-release-contract"
}

Run-Step "package public release" {
  pwsh -NoProfile -ExecutionPolicy Bypass -File ./scripts/package-public-release.ps1 -ReleaseName $ReleaseName -MeiliUrl /knowledge-search
  Assert-NativeSuccess "package-public-release"
}

if ($Deploy) {
  Run-Step "deploy VPS and reindex" {
    pwsh -NoProfile -ExecutionPolicy Bypass -File ./scripts/deploy-public-vps.ps1 -ReleaseName $ReleaseName -SkipPackage
    Assert-NativeSuccess "deploy-public-vps"
  }

  if (-not $SkipLiveQa) {
    Run-Step "live SEO crawl gate" {
      node ./scripts/live-seo-crawl-gate.mjs --base-url https://aggressorbulkit.online --limit 250
      Assert-NativeSuccess "live-seo-crawl-gate"
    }
    Run-Step "mobile visual QA" {
      node ./scripts/mobile-visual-qa.mjs --base-url https://aggressorbulkit.online --viewports full --out "output/evidence/mobile-visual-qa-live-$ReleaseName"
      Assert-NativeSuccess "mobile-visual-qa"
    }
  }
}
elseif (-not $PackageOnly) {
  Write-Output ""
  Write-Output "Package created but not deployed. Add -Deploy to upload, switch current, reindex, and run live QA."
}

Write-Output ""
Write-Output "release_gate_ok=true"
Write-Output "release=$ReleaseName"
