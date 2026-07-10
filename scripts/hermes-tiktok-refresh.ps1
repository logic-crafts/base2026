param(
  [int]$PlaylistEnd = 1000,
  [string]$CutoffDate = "",
  [int]$TranscriptLimit = 100,
  [int]$AsrLimit = 20,
  [int]$PolishLimit = 30,
  [int]$BatchSize = 8,
  [string]$BatchSet = "",
  [string]$CreatorsConfig = "",
  [switch]$CheckOnly,
  [switch]$AfterPolish,
  [switch]$SkipInventory,
  [switch]$SkipAsr,
  [switch]$DryRun,
  [switch]$Package,
  [switch]$Deploy,
  [switch]$Help
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if ($Help) {
  Write-Output @"
Hermes TikTok refresh

Safe entry points:
  pwsh ./scripts/hermes-tiktok-refresh.ps1 -CheckOnly
  pwsh ./scripts/hermes-tiktok-refresh.ps1 -SkipInventory -BatchSet <batch-set>
  pwsh ./scripts/hermes-tiktok-refresh.ps1 -BatchSet <batch-set>
  pwsh ./scripts/hermes-tiktok-refresh.ps1 -AfterPolish -BatchSet <batch-set>

Rules:
  - -Help prints this message and exits without running inventory/intake.
  - Use -SkipInventory after an explicit social-discovery importer apply when only existing queued rows should be processed.
  - Run without -AfterPolish only to discover/process captions and create polish batches.
  - Run -AfterPolish only after the GPT/Codex polish output exists for that exact BatchSet.
  - Deployment belongs to scripts/base2026-release-gate.ps1, not this runner.
"@
  exit 0
}

$Planning = Join-Path $Root ".planning"
$Results = Join-Path $Planning "agent-results"
$Lock = Join-Path $Planning "hermes-tiktok-refresh.lock"
$State = Join-Path $Planning "hermes-tiktok-refresh-state.json"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Log = Join-Path $Results "hermes-tiktok-refresh-$Stamp.log"
if (-not $BatchSet) {
  $BatchSet = "hermes-polish-$Stamp"
}

$Python = (Get-Command python3 -ErrorAction SilentlyContinue)
if (-not $Python) { $Python = (Get-Command python -ErrorAction SilentlyContinue) }
if (-not $Python) { throw "Python runtime not found. Install python3 or add python to PATH." }
$PythonExe = $Python.Source

$PowerShell = (Get-Command pwsh -ErrorAction SilentlyContinue)
if (-not $PowerShell) { $PowerShell = (Get-Command powershell -ErrorAction SilentlyContinue) }
if (-not $PowerShell) { throw "PowerShell runtime not found. Install pwsh or add powershell to PATH." }
$PowerShellExe = $PowerShell.Source

New-Item -ItemType Directory -Force -Path $Planning, $Results | Out-Null

if (-not $CutoffDate) {
  $CutoffDate = (Get-Date).AddDays(-365).ToString("yyyy-MM-dd")
}

function Write-State {
  param(
    [string]$Status,
    [string]$Stage,
    [string]$Message = "",
    [bool]$Ok = $false
  )
  [pscustomobject]@{
    status = $Status
    stage = $Stage
    message = $Message
    ok = $Ok
    updated_at = (Get-Date).ToString("s")
    log = $Log
    batch_set = $BatchSet
    cutoff_date = $CutoffDate
    creators_config = $CreatorsConfig
  } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $State -Encoding UTF8
}

function Run-Step {
  param([string]$Stage, [scriptblock]$Command)
  Write-State -Status "running" -Stage $Stage
  "[$((Get-Date).ToString('s'))] $Stage" | Tee-Object -FilePath $Log -Append | Out-Null
  $global:LASTEXITCODE = 0
  & $Command 2>&1 | Tee-Object -FilePath $Log -Append
  if ((-not $?) -or ($LASTEXITCODE -ne 0)) { throw "Stage failed: $Stage" }
}

function Get-PendingSummary {
  $TikTokRoot = Join-Path $Root "12_knowledge-base\sources\tiktok"
  $VideosCsv = Join-Path $TikTokRoot "videos.csv"
  $CleanDir = Join-Path $TikTokRoot "transcripts\clean"
  $PolishedDir = Join-Path $TikTokRoot "transcripts\polished"
  $rows = @(Import-Csv $VideosCsv)
  $active = @($rows | Where-Object { $_.transcript_status -ne "out_of_scope_old" })
  $queued = @($active | Where-Object { $_.transcript_status -in @("queued", "pending", "") })
  $needsAsr = @($active | Where-Object { $_.transcript_status -eq "needs_asr" })
  $transcribed = @($active | Where-Object { $_.transcript_status -eq "transcribed" })
  $needsPolish = @($transcribed | Where-Object {
    (Test-Path (Join-Path $CleanDir "$($_.video_id).txt")) -and
    -not (Test-Path (Join-Path $PolishedDir "$($_.video_id).txt"))
  })
  [pscustomobject]@{
    total = $rows.Count
    active = $active.Count
    queued_transcript = $queued.Count
    needs_asr = $needsAsr.Count
    transcribed = $transcribed.Count
    needs_polish = $needsPolish.Count
  }
}

if (Test-Path $Lock) {
  Write-State -Status "locked" -Stage "lock" -Message "Existing refresh lock found: $Lock"
  throw "Existing refresh lock found: $Lock"
}

try {
  Set-Content -LiteralPath $Lock -Value $PID -Encoding ASCII
  Write-State -Status "running" -Stage "start" -Message "Hermes TikTok refresh started."

  if ($CheckOnly -or $DryRun) {
    $DiscoveryOut = Join-Path $Planning "social-discovered-checkonly-$Stamp.jsonl"
    $ImportReport = Join-Path $Planning "social-discovery-import-checkonly-$Stamp.json"

    Run-Step "discovery-preview" {
      $discoverArgs = @(
        "--out", $DiscoveryOut,
        "--limit-per-creator", $PlaylistEnd
      )
      if ($CreatorsConfig) {
        $discoverArgs = @("--config", $CreatorsConfig) + $discoverArgs
      }
      & $PythonExe (Join-Path $Root "scripts\social-discover.py") @discoverArgs
    }

    Run-Step "import-preview" {
      & $PythonExe (Join-Path $Root "scripts\import-social-discovery-to-tiktok-csv.py") --input $DiscoveryOut --report $ImportReport
    }

    $summary = Get-PendingSummary
    $summary | Format-List | Tee-Object -FilePath $Log -Append
    Write-State -Status "completed" -Stage "check" -Message "Check-only completed without writing videos.csv." -Ok $true
    exit 0
  }

  if (-not $AfterPolish) {
    if ($SkipInventory) {
      "SkipInventory mode: preserving existing videos.csv queue; no inventory/discovery writes." | Tee-Object -FilePath $Log -Append
      $summary = Get-PendingSummary
      $summary | Format-List | Tee-Object -FilePath $Log -Append
    }
    else {
      Run-Step "inventory" {
        if ($CreatorsConfig) {
          & (Join-Path $Root "scripts\tiktok-backfill-inventory.ps1") -PlaylistEnd $PlaylistEnd -CutoffDate $CutoffDate -CreatorsConfig $CreatorsConfig
        }
        else {
          & (Join-Path $Root "scripts\tiktok-backfill-inventory.ps1") -PlaylistEnd $PlaylistEnd -CutoffDate $CutoffDate
        }
      }

      $summary = Get-PendingSummary
      $summary | Format-List | Tee-Object -FilePath $Log -Append
    }
  }
  else {
    "AfterPolish mode: skipping inventory/caption intake; rebuilding from existing reviewed polish outputs only." | Tee-Object -FilePath $Log -Append
  }

  if (-not $AfterPolish) {
    Run-Step "captions" {
      & (Join-Path $Root "scripts\tiktok-process-transcripts.ps1") -Limit $TranscriptLimit
    }

    if (-not $SkipAsr) {
      Run-Step "asr" {
        & (Join-Path $Root "scripts\tiktok-process-transcripts.ps1") -Limit $AsrLimit -AsrFallback
      }
    }

    Run-Step "polish-batches" {
      & (Join-Path $Root "scripts\tiktok-create-polish-batches.ps1") -BatchSize $BatchSize -Limit $PolishLimit -BatchSet $BatchSet
    }

    $BatchDir = Join-Path $Root "12_knowledge-base\sources\tiktok\transcript-polish-batches\$BatchSet"
    $BatchCount = @(Get-ChildItem -LiteralPath $BatchDir -File -Filter "batch-*.md" -ErrorAction SilentlyContinue).Count
    if ($BatchCount -gt 0) {
      Write-State -Status "waiting_for_hermes" -Stage "polish" -Message "Hermes must process $BatchCount polish batch file(s): $BatchDir" -Ok $true
      "Hermes polish batch dir: $BatchDir" | Tee-Object -FilePath $Log -Append
      "After Hermes writes polished outputs, run this script with -AfterPolish." | Tee-Object -FilePath $Log -Append
      exit 0
    }
  }

  Run-Step "polish-status" {
    $statusArgs = @("--json")
    if ($AfterPolish) {
      # `needs_review` is a valid gated outcome after GPT/Codex polish; it must not abort
      # the local rebuild/export refresh. Missing polished outputs still exit non-zero.
      $statusArgs += @("--allow-needs-review")
    }
    if ($AfterPolish -and $BatchSet) {
      $statusArgs += @("--batch-dir", (Join-Path $Root "12_knowledge-base\sources\tiktok\transcript-polish-batches\$BatchSet"))
    }
    & $PythonExe (Join-Path $Root "scripts\tiktok-polish-status.py") @statusArgs
  }
  if ($AfterPolish -and $BatchSet) {
    Run-Step "apply-qa-gates" {
      $BatchDir = Join-Path $Root "12_knowledge-base\sources\tiktok\transcript-polish-batches\$BatchSet"
      & $PythonExe (Join-Path $Root "scripts\tiktok-apply-qa-gates.py") --batch-dir $BatchDir --apply
    }
  }
  Run-Step "rebuild-sqlite" {
    & $PythonExe (Join-Path $Root "scripts\build-kb-sqlite.py")
  }
  Run-Step "audit" {
    & $PythonExe (Join-Path $Root "scripts\kb-audit.py")
  }
  Run-Step "export-public-tiktok" {
    $ExportRoot = Join-Path $Root "output\hermes-public-export\$Stamp\tiktok"
    $PublicDataRoot = Join-Path $Root "public-data\tiktok"
    if (Test-Path $ExportRoot) {
      Remove-Item $ExportRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $ExportRoot | Out-Null
    & $PythonExe (Join-Path $Root "scripts\export-public-tiktok.py") --out $ExportRoot
    & $PythonExe (Join-Path $Root "scripts\check-public-export-policy.py") $ExportRoot
    & $PythonExe (Join-Path $Root "scripts\validate-public-release-contract.py") --export-dir $ExportRoot --baseline-export-dir $PublicDataRoot --enforce-count-floor
    if (Test-Path $PublicDataRoot) {
      Remove-Item $PublicDataRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $PublicDataRoot | Out-Null
    Copy-Item (Join-Path $ExportRoot "*") $PublicDataRoot -Recurse -Force
  }

  Run-Step "refresh-editorial-queues" {
    $InsightRepairRoot = Join-Path $Planning "insight-repair"
    & $PythonExe (Join-Path $Root "scripts\base2026-tiktok-repair-queue.py") --out-dir $InsightRepairRoot --write
    & $PythonExe (Join-Path $Root "scripts\base2026-solution-backlog-portfolio.py") `
      --queue (Join-Path $InsightRepairRoot "needs-insight-latest.jsonl") `
      --repair-summary (Join-Path $InsightRepairRoot "repair-summary-latest.json") `
      --out-jsonl (Join-Path $Planning "tiktok-pipeline-v2\needs-insight-portfolio.jsonl") `
      --out-summary (Join-Path $Planning "tiktok-pipeline-v2\needs-insight-portfolio-summary.json") `
      --out-markdown (Join-Path $Planning "tiktok-pipeline-v2\NEEDS_INSIGHT_PORTFOLIO.md")
  }

  if ($Package -or $Deploy) {
    Run-Step "package-public-release" {
      & $PowerShellExe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root "scripts\package-public-release.ps1") -ReleaseName "base2026-public-hermes-$Stamp"
    }
  }

  if ($Deploy) {
    throw "Deploy gate not automated in this runner yet. Use existing VPS deploy flow after reviewing audit/package."
  }

  Write-State -Status "completed" -Stage "done" -Message "Hermes TikTok refresh completed locally." -Ok $true
}
catch {
  Write-State -Status "failed" -Stage "exception" -Message $_.Exception.Message -Ok $false
  throw
}
finally {
  Remove-Item -LiteralPath $Lock -ErrorAction SilentlyContinue
}
