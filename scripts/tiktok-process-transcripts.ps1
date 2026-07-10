param(
  [string]$CreatorId = "",
  [string]$VideoId = "",
  [int]$Limit = 50,
  [switch]$AsrFallback,
  [switch]$IncludeSourceReview,
  [switch]$RefreshAudioFallback,
  [ValidateSet("", "local_caption_exists", "audio_available_retry_asr", "no_local_caption_or_audio")]
  [string]$SourceReviewReason = ""
)

$ErrorActionPreference = "Continue"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$TikTokRoot = Join-Path $Root "12_knowledge-base\sources\tiktok"
$VideosCsv = Join-Path $TikTokRoot "videos.csv"
$RawDir = Join-Path $TikTokRoot "transcripts\raw"
$CleanDir = Join-Path $TikTokRoot "transcripts\clean"
$AudioDir = Join-Path $TikTokRoot "transcripts\audio-fallback"
$AsrDir = Join-Path $TikTokRoot "transcripts\asr"
$RawOutputTemplate = ($RawDir -replace '\\', '/') + "/%(uploader_id)s/%(id)s.%(ext)s"
$AudioOutputTemplate = ($AudioDir -replace '\\', '/') + "/%(id)s.%(ext)s"
$WorkerPython = Join-Path $Root ".venv\bin\python"
if (-not (Test-Path -LiteralPath $WorkerPython)) {
  $PythonCommand = Get-Command python3 -ErrorAction SilentlyContinue
  if (-not $PythonCommand) { $PythonCommand = Get-Command python -ErrorAction SilentlyContinue }
  if (-not $PythonCommand) { throw "python3 or python is required for the local ASR worker." }
  $WorkerPython = $PythonCommand.Source
}
$WorkerScript = Join-Path $Root "scripts\base2026-worker.py"

New-Item -ItemType Directory -Force -Path $RawDir, $CleanDir, $AudioDir, $AsrDir | Out-Null

function Test-LocalCaptionExists {
  param([string]$Id)
  if (-not $Id) { return $false }
  return [bool](Get-ChildItem $RawDir -Recurse -File -Filter "$Id*.vtt" -ErrorAction SilentlyContinue | Select-Object -First 1)
}

function Test-AudioFallbackExists {
  param([string]$Id)
  if (-not $Id) { return $false }
  return [bool](Get-ChildItem $AudioDir -File -ErrorAction SilentlyContinue |
    Where-Object { $_.BaseName -eq $Id -and $_.Extension.ToLowerInvariant() -in @(".mp3", ".mp4", ".m4a", ".webm", ".wav") } |
    Select-Object -First 1)
}

function Test-SourceReviewReason {
  param(
    [object]$Row,
    [string]$Reason
  )
  if (-not $Reason) { return $true }
  if ($Row.transcript_status -ne "needs_source_review") { return $true }

  $id = $Row.video_id
  $hasCaption = Test-LocalCaptionExists -Id $id
  $hasAudio = Test-AudioFallbackExists -Id $id

  switch ($Reason) {
    "local_caption_exists" { return $hasCaption }
    "audio_available_retry_asr" { return (-not $hasCaption) -and $hasAudio }
    "no_local_caption_or_audio" { return (-not $hasCaption) -and (-not $hasAudio) }
    default { return $true }
  }
}

function Add-RowNote {
  param(
    [object]$Row,
    [string]$Note
  )
  if (-not $Note) { return }
  $existing = @()
  if ($Row.notes) {
    $existing = @($Row.notes -split ';' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
  }
  if ($existing -notcontains $Note) {
    $Row.notes = (@($existing) + $Note) -join "; "
  }
}

function Convert-WorkerJson {
  param([object[]]$WorkerOutput)
  $text = (($WorkerOutput | Out-String) -replace '^\s+', '').Trim()
  if (-not $text) { return $null }
  $jsonStart = $text.IndexOf('{')
  if ($jsonStart -gt 0) {
    $text = $text.Substring($jsonStart)
  }
  try { return ($text | ConvertFrom-Json) } catch { return $null }
}

$rows = @(Import-Csv $VideosCsv)
$targetStatuses = if ($AsrFallback) { @("queued", "pending", "", "needs_asr") } else { @("queued", "pending", "") }
if ($AsrFallback -and $IncludeSourceReview) {
  $targetStatuses += "needs_source_review"
}
$targets = $rows | Where-Object {
  $_.transcript_status -in $targetStatuses -and
  ($CreatorId -eq "" -or $_.creator_id -eq $CreatorId) -and
  ($VideoId -eq "" -or $_.video_id -eq $VideoId) -and
  (Test-SourceReviewReason -Row $_ -Reason $SourceReviewReason)
} | Select-Object -First $Limit

$done = 0
$caption = 0
$needsAsr = 0
$asrDone = 0
$failed = 0
$asrTooLittle = 0
$asrNoUsable = 0
$asrNoAudio = 0
$asrWorkerParseFailed = 0

foreach ($row in $targets) {
  $id = $row.video_id
  $url = $row.url
  if (-not $id -or -not $url) { continue }

  & yt-dlp --quiet --no-warnings --skip-download --write-subs --write-auto-subs --sub-langs "en.*,eng.*" --sub-format vtt --output $RawOutputTemplate $url 2>$null
  $vtt = Get-ChildItem $RawDir -Recurse -File -Filter "$id*.vtt" -ErrorAction SilentlyContinue | Select-Object -First 1

  if ($vtt) {
    $lines = Get-Content -LiteralPath $vtt.FullName | Where-Object {
      $_ -and $_ -notmatch '^WEBVTT' -and $_ -notmatch '^Kind:' -and $_ -notmatch '^Language:' -and
      $_ -notmatch '^\d+$' -and $_ -notmatch '-->' -and $_ -notmatch '^NOTE'
    }
    $text = (($lines -join ' ') -replace '<[^>]+>', '' -replace '\s+', ' ').Trim()
    Set-Content -LiteralPath (Join-Path $CleanDir "$id.txt") -Value $text -Encoding UTF8
    $row.transcript_status = "transcribed"
    $row.caption_source = "caption"
    $row.evidence_path = $vtt.FullName.Replace($TikTokRoot + "\", "")
    $row.review_status = ""
    Add-RowNote -Row $row -Note "Captions downloaded via yt-dlp"
    $caption++
    $done++
    continue
  }

  if ($AsrFallback) {
    if ($RefreshAudioFallback -and $IncludeSourceReview -and $row.transcript_status -eq "needs_source_review") {
      Get-ChildItem $AudioDir -File -ErrorAction SilentlyContinue |
        Where-Object { $_.BaseName -eq $id } |
        Remove-Item -Force -ErrorAction SilentlyContinue
    }
    $media = Get-ChildItem $AudioDir -File -ErrorAction SilentlyContinue |
      Where-Object { $_.BaseName -eq $id -and $_.Extension.ToLowerInvariant() -in @(".mp3", ".mp4", ".m4a", ".webm", ".wav") } |
      Sort-Object LastWriteTime -Descending |
      Select-Object -First 1
    if (-not $media -or $RefreshAudioFallback) {
      & yt-dlp --quiet --no-warnings --force-overwrites -f "bv*[ext=mp4][vcodec^=h264]+ba/b[ext=mp4][vcodec^=h264]/download/best[ext=mp4]/best" -x --audio-format mp3 --audio-quality 5 --output $AudioOutputTemplate $url 2>$null
      $media = Get-ChildItem $AudioDir -File -ErrorAction SilentlyContinue |
        Where-Object { $_.BaseName -eq $id -and $_.Extension.ToLowerInvariant() -in @(".mp3", ".mp4", ".m4a", ".webm", ".wav") } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    }
    if ($media) {
      $workerJson = & $WorkerPython $WorkerScript transcribe $media.FullName --model small.en --language en --device cpu --compute-type int8 --vad-filter 2>$null
      $worker = Convert-WorkerJson -WorkerOutput $workerJson
      if (-not $worker) {
        $asrWorkerParseFailed++
      }
      if ($worker -and $worker.ok -and $worker.output -and (Test-Path -LiteralPath $worker.output)) {
        $asrRaw = Get-Content -LiteralPath $worker.output -Raw -Encoding UTF8
        $asrText = if ($null -eq $asrRaw) { "" } else { $asrRaw.Trim() }
        if ($asrText) {
          $txt = Join-Path $AsrDir "$id.txt"
          Set-Content -LiteralPath $txt -Value $asrText -Encoding UTF8
          Copy-Item $txt (Join-Path $CleanDir "$id.txt") -Force
          $metadataTarget = Join-Path $AsrDir "$id.asr.json"
          if ($worker.metadata_output -and (Test-Path -LiteralPath $worker.metadata_output)) {
            Copy-Item $worker.metadata_output $metadataTarget -Force
          }
          if ($worker.segments_output -and (Test-Path -LiteralPath $worker.segments_output)) {
            Copy-Item $worker.segments_output (Join-Path $AsrDir "$id.segments.json") -Force
          }
          $wordCount = [int]($worker.word_count)
          if ($wordCount -lt 12) {
            $row.transcript_status = "needs_source_review"
            $row.caption_source = "asr"
            $row.evidence_path = "transcripts\asr\$id.txt"
            $row.review_status = "needs_source_review"
            Add-RowNote -Row $row -Note "ASR produced too little usable text ($wordCount words); source review required"
            $asrTooLittle++
            $failed++
            continue
          }
          $row.transcript_status = "transcribed"
          $row.caption_source = "asr"
          $row.evidence_path = "transcripts\asr\$id.txt"
          $row.review_status = ""
          Add-RowNote -Row $row -Note "Caption download failed; faster-whisper ASR completed"
          $asrDone++
          $done++
          continue
        }
      }
      if ($worker -and $worker.output -and (Test-Path -LiteralPath $worker.output)) {
        Copy-Item $worker.output (Join-Path $AsrDir "$id.empty-asr.txt") -Force
      }
      $row.transcript_status = "needs_source_review"
      $row.caption_source = "asr"
      $row.evidence_path = ""
      $row.review_status = "needs_source_review"
      Add-RowNote -Row $row -Note "ASR fallback produced no usable transcript; source review required"
      $asrNoUsable++
      $failed++
      continue
    } else {
      $row.transcript_status = "needs_source_review"
      $row.caption_source = ""
      $row.evidence_path = ""
      $row.review_status = "needs_source_review"
      Add-RowNote -Row $row -Note "Caption download failed; audio fallback unavailable; source review required"
      $asrNoAudio++
      $failed++
      continue
    }
  }

  $row.transcript_status = "needs_asr"
  $row.caption_source = ""
  Add-RowNote -Row $row -Note "Caption download failed; ASR queued"
  $needsAsr++
}

$rows | Export-Csv $VideosCsv -NoTypeInformation -Encoding UTF8

[pscustomobject]@{
  selected = $targets.Count
  transcribed = $done
  captions = $caption
  asr = $asrDone
  needs_asr = $needsAsr
  failed = $failed
  asr_too_little = $asrTooLittle
  asr_no_usable = $asrNoUsable
  asr_no_audio = $asrNoAudio
  asr_worker_parse_failed = $asrWorkerParseFailed
} | Format-List

# yt-dlp/faster-whisper can return a non-zero native LASTEXITCODE for rows that this
# script has already converted into an explicit queue state (`needs_asr` or
# `needs_source_review`). The caller should treat those handled outcomes as a
# successful pipeline stage so ASR/polish gates can continue for publishable rows.
$global:LASTEXITCODE = 0
exit 0
