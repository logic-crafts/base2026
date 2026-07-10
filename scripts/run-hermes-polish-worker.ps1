param(
  [string]$BatchSet = "",
  [string]$BatchDir = "",
  [string]$Model = "gpt-5.5",
  [string]$CodexPath = "",
  [switch]$DryRun,
  [switch]$DeterministicFallback,
  [switch]$RunAfterPolish
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$TikTokRoot = Join-Path $Root "12_knowledge-base\sources\tiktok"
$BatchRoot = Join-Path $TikTokRoot "transcript-polish-batches"
$Planning = Join-Path $Root ".planning"
$Results = Join-Path $Planning "agent-results"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"

if (-not $CodexPath) {
  if ($env:HERMES_CODEX_PATH) {
    $CodexPath = $env:HERMES_CODEX_PATH
  } else {
    $cmd = Get-Command codex.exe -ErrorAction SilentlyContinue
    if (-not $cmd) { $cmd = Get-Command codex -ErrorAction SilentlyContinue }
    if ($cmd) { $CodexPath = $cmd.Source }
  }
}

if (-not $BatchDir) {
  if (-not $BatchSet) { throw "Provide -BatchSet or -BatchDir." }
  $BatchDir = Join-Path $BatchRoot $BatchSet
}

$BatchDir = Resolve-Path $BatchDir
if (-not $DeterministicFallback -and -not (Test-Path -LiteralPath $CodexPath)) {
  throw "Codex worker not found. Set -CodexPath or HERMES_CODEX_PATH, or use -DeterministicFallback."
}

$batchFiles = @(Get-ChildItem -LiteralPath $BatchDir -Filter "batch-*.md" | Sort-Object Name)
if ($batchFiles.Count -eq 0) { throw "No batch-*.md files found in $BatchDir" }

if ($DeterministicFallback) {
  if ($DryRun) {
    [pscustomobject]@{
      ok = $true
      dry_run = $true
      mode = "deterministic_fallback"
      batch_dir = "$BatchDir"
      batch_files = $batchFiles.Count
      after_polish = [bool]$RunAfterPolish
    } | ConvertTo-Json -Depth 4
    exit 0
  }
  $localPolish = Join-Path $Root "scripts/tiktok-faithful-polish-local.py"
  $statusScript = Join-Path $Root "scripts/tiktok-polish-status.py"
  & python3 $localPolish --batch-dir $BatchDir --missing-only --limit 80 --apply
  if (-not $?) { throw "Deterministic polish failed." }
  & python3 $statusScript --batch-dir $BatchDir --json --allow-needs-review
  if (-not $?) { throw "Deterministic polish status failed." }
  if ($RunAfterPolish) {
    $refreshScript = Join-Path $Root "scripts/hermes-tiktok-refresh.ps1"
    & $refreshScript -AfterPolish -BatchSet $BatchSet
    if (-not $?) { throw "AfterPolish refresh failed." }
  }
  [pscustomobject]@{
    ok = $true
    mode = "deterministic_fallback"
    model = "none"
    batch_dir = "$BatchDir"
    batch_files = $batchFiles.Count
    after_polish = [bool]$RunAfterPolish
  } | ConvertTo-Json -Depth 4
  exit 0
}

New-Item -ItemType Directory -Force -Path $Planning, $Results | Out-Null

$taskPath = Join-Path $Planning "hermes-polish-worker-$Stamp.md"
$outPath = Join-Path $Results "hermes-polish-worker-$Stamp.txt"
$batchList = ($batchFiles | ForEach-Object { "- $($_.FullName)" }) -join "`n"

$prompt = @"
You are maintaining Base2026 public TikTok transcripts.

Work only inside:
$Root

Model policy:
- Use the requested model tier: $Model.
- Do not switch to a lower/local model for this quality lane.
- Do not read the whole repository.
- Read only the batch files listed below and the exact output files you create/update.

Batch files:
$batchList

Task:
For each video in the batch files, create/update:
- 12_knowledge-base/sources/tiktok/transcripts/polished/<video_id>.txt
- 12_knowledge-base/sources/tiktok/transcripts/polished-qa/<video_id>.json

Faithful polish rules:
- English only.
- Preserve spoken meaning and wording.
- Add punctuation, sentence boundaries, and paragraph breaks.
- Remove obvious caption duplication/artifacts only.
- Do not summarize.
- Do not add claims.
- Do not translate to Russian.
- If uncertain, preserve raw wording and mark QA status needs_review.

QA JSON:
{
  "video_id": "...",
  "status": "pass",
  "notes": [],
  "raw_word_count": 0,
  "polished_word_count": 0,
  "paragraph_count": 0,
  "model_tier": "$Model",
  "meaning_added": false
}

Final response:
- videos processed
- files written
- pass/needs_review counts
"@

Set-Content -LiteralPath $taskPath -Value $prompt -Encoding UTF8

if ($DryRun) {
  [pscustomobject]@{
    ok = $true
    dry_run = $true
    model = $Model
    task = $taskPath
    output = $outPath
    batch_dir = "$BatchDir"
    batch_files = $batchFiles.Count
  } | ConvertTo-Json -Depth 4
  exit 0
}

Get-Content -Raw $taskPath | & $CodexPath exec `
  --ignore-user-config `
  --ignore-rules `
  -m $Model `
  -C $Root `
  --sandbox workspace-write `
  -o $outPath `
  -

if (-not $?) { throw "Hermes polish worker failed." }

if ($RunAfterPolish) {
  $refreshScript = Join-Path $Root "scripts/hermes-tiktok-refresh.ps1"
  & $refreshScript -AfterPolish -BatchSet $BatchSet
  if (-not $?) { throw "AfterPolish refresh failed." }
}

[pscustomobject]@{
  ok = $true
  model = $Model
  task = $taskPath
  output = $outPath
  batch_dir = "$BatchDir"
  batch_files = $batchFiles.Count
} | ConvertTo-Json -Depth 4
