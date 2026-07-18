param(
  [Parameter(Mandatory = $true)]
  [string]$ReleaseName,
  [Parameter(Mandatory = $true)]
  [string]$ExpectedZipSha256,
  [Parameter(Mandatory = $true)]
  [string]$BaseUrl,
  [Parameter(Mandatory = $true)]
  [string]$WebRoot,
  [Parameter(Mandatory = $true)]
  [string]$CandidateManifest,
  [Parameter(Mandatory = $true)]
  [string]$EvidenceDir
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Assert-LastExitCode([string]$Step) {
  if ($LASTEXITCODE -ne 0) {
    throw "$Step failed with exit code $LASTEXITCODE"
  }
}

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$WebRoot = [System.IO.Path]::GetFullPath($WebRoot)
$CandidateManifest = [System.IO.Path]::GetFullPath($CandidateManifest)
$EvidenceDir = [System.IO.Path]::GetFullPath($EvidenceDir)

if ($ReleaseName -notmatch '^[A-Za-z0-9._-]+$') {
  throw "Unsafe ReleaseName: $ReleaseName"
}
if ($ExpectedZipSha256 -notmatch '^[A-Fa-f0-9]{64}$') {
  throw "ExpectedZipSha256 must be exactly 64 hexadecimal characters."
}
if (-not (Test-Path -LiteralPath $WebRoot -PathType Container)) {
  throw "Web root not found: $WebRoot"
}
if (-not (Test-Path -LiteralPath $CandidateManifest -PathType Leaf)) {
  throw "Candidate manifest not found: $CandidateManifest"
}

Push-Location $RepoRoot
try {
  if (Test-Path -LiteralPath $EvidenceDir) {
    Remove-Item -LiteralPath $EvidenceDir -Recurse -Force
  }
  New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null
  $ContractDir = Join-Path $EvidenceDir "contract"
  $BrowserDir = Join-Path $EvidenceDir "browser"
  New-Item -ItemType Directory -Path $ContractDir, $BrowserDir -Force | Out-Null

  $ContractReport = Join-Path $ContractDir "report.json"
  & python3 ./scripts/source-detail-v2-contract-gate.py `
    --base-url $BaseUrl `
    --manifest $CandidateManifest `
    --web-root $WebRoot `
    --report $ContractReport `
    --workers 16
  Assert-LastExitCode "source-detail-v2 contract/sitemap/exact-byte gate"

  & node ./scripts/source-detail-v2-browser-gate.mjs `
    --base-url $BaseUrl `
    --manifest $CandidateManifest `
    --out $BrowserDir
  Assert-LastExitCode "source-detail-v2 desktop/mobile browser gate"

  $Contract = Get-Content -LiteralPath $ContractReport -Raw | ConvertFrom-Json
  $Browser = Get-Content -LiteralPath (Join-Path $BrowserDir "report.json") -Raw | ConvertFrom-Json
  if (-not $Contract.passed -or -not $Browser.passed) {
    throw "A gate report returned passed=false."
  }

  $GateReceipt = [ordered]@{
    schema = "base2026.source-detail-v2-live-gate-receipt/v1"
    completed_at = (Get-Date).ToUniversalTime().ToString("o")
    release_name = $ReleaseName
    zip_sha256 = $ExpectedZipSha256.ToLowerInvariant()
    base_url = $BaseUrl
    web_root = $WebRoot
    candidate_manifest = $CandidateManifest
    contract = [ordered]@{
      result = "PASS"
      exact_200_and_byte_hash = $Contract.coverage.exact_200_and_byte_hash
      rendered_routes = $Contract.coverage.rendered_routes
      future_private_404 = $Contract.coverage.future_private_404
      sitemap_urls = $Contract.coverage.sitemap_urls
      sitemap_exact_200_and_byte_hash = $Contract.coverage.sitemap_exact_200_and_byte_hash
      expected_route_digest = $Contract.route_hash_digests.expected
      actual_route_digest = $Contract.route_hash_digests.actual
    }
    browser = [ordered]@{
      result = "PASS"
      checks = @($Browser.results).Count
      failures = @($Browser.failures).Count
      viewports = @($Browser.viewports | ForEach-Object { $_.id })
      console_page_network_gate = $true
      screenshots = @($Browser.results | ForEach-Object { $_.screenshot })
    }
  }
  $GateReceiptPath = Join-Path $EvidenceDir "gate-receipt.json"
  $GateReceipt | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $GateReceiptPath -Encoding utf8

  $EvidenceHashes = Get-ChildItem -LiteralPath $EvidenceDir -File -Recurse |
    Where-Object { $_.Name -ne 'SHA256SUMS.json' } |
    Sort-Object FullName |
    ForEach-Object {
      [ordered]@{
        path = [System.IO.Path]::GetRelativePath($EvidenceDir, $_.FullName).Replace('\', '/')
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant()
        bytes = $_.Length
      }
    }
  $SumsPath = Join-Path $EvidenceDir "SHA256SUMS.json"
  [ordered]@{
    schema = "base2026.live-gate-evidence-sha256/v1"
    release_name = $ReleaseName
    files = @($EvidenceHashes)
  } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $SumsPath -Encoding utf8
  $SumsHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $SumsPath).Hash.ToLowerInvariant()

  Write-Host "gate=PASS"
  Write-Host "evidence=$EvidenceDir"
  Write-Host "evidence_sha256=$SumsHash"
} finally {
  Pop-Location
}
