param(
  [string]$SshHost = "geo",
  [string]$RemoteBase = "/var/www/base2026-knowledge",
  [string]$ReleaseName = ("base2026-" + (Get-Date -Format "yyyyMMdd-HHmmss")),
  [string]$ZipPath = "",
  [Parameter(Mandatory = $true)]
  [string]$ExpectedZipSha256,
  [string]$LiveBaseUrl = "https://aggressorbulkit.online/knowledge/",
  [Parameter(Mandatory = $true)]
  [string]$CandidateManifest,
  [string]$EvidenceDir = "",
  [switch]$SkipPackage,
  [switch]$SkipReindex,
  [switch]$PlanOnly
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Assert-LastExitCode([string]$Step) {
  if ($LASTEXITCODE -ne 0) {
    throw "$Step failed with exit code $LASTEXITCODE"
  }
}

function Resolve-RepoPath([string]$PathValue, [string]$RepoRoot) {
  if ([System.IO.Path]::IsPathRooted($PathValue)) {
    return [System.IO.Path]::GetFullPath($PathValue)
  }
  return [System.IO.Path]::GetFullPath((Join-Path $RepoRoot $PathValue))
}

function Invoke-RemoteRollback(
  [string]$HostName,
  [string]$BasePath,
  [string]$ExpectedRelease
) {
  $rollbackTemplate = @'
set -Eeuo pipefail
base='__BASE__'
expected_release="$base/releases/__RELEASE__"
current_link="$base/current"
previous_link="$base/previous"
current_target="$(readlink -f "$current_link" || true)"
previous_target="$(readlink -f "$previous_link" || true)"
test "$current_target" = "$expected_release"
test -n "$previous_target"
case "$previous_target" in
  "$base"/releases/*) ;;
  *) echo "Unsafe previous target: $previous_target" >&2; exit 71 ;;
esac
test -d "$previous_target"
rollback_tmp="$base/.current.rollback.$$"
cleanup() { rm -f "$rollback_tmp"; }
trap cleanup EXIT
ln -s "$previous_target" "$rollback_tmp"
mv -Tf "$rollback_tmp" "$current_link"
nginx -t
systemctl reload nginx
systemctl is-active --quiet nginx
test "$(readlink -f "$current_link")" = "$previous_target"
echo "BASE2026_ROLLBACK_COMPLETE=$previous_target"
'@
  $rollbackScript = $rollbackTemplate.Replace('__BASE__', $BasePath).Replace('__RELEASE__', $ExpectedRelease)
  $output = @($rollbackScript | & ssh $HostName "bash -s")
  $exitCode = $LASTEXITCODE
  $output | ForEach-Object { Write-Host $_ }
  if ($exitCode -ne 0) {
    throw "Automatic rollback failed with exit code $exitCode. Production state requires immediate inspection."
  }
  return $output
}

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $RepoRoot
try {
  if ($ReleaseName -notmatch '^[A-Za-z0-9._-]+$') {
    throw "ReleaseName contains unsafe characters: $ReleaseName"
  }
  if ($SshHost -notmatch '^[A-Za-z0-9._@:-]+$') {
    throw "SshHost contains unsafe characters: $SshHost"
  }
  if ($RemoteBase -notmatch '^/[A-Za-z0-9._/-]+$') {
    throw "RemoteBase contains unsafe characters: $RemoteBase"
  }
  if ($ExpectedZipSha256 -notmatch '^[A-Fa-f0-9]{64}$') {
    throw "ExpectedZipSha256 must be exactly 64 hexadecimal characters."
  }
  $ExpectedZipSha256 = $ExpectedZipSha256.ToLowerInvariant()

  if (-not $SkipReindex) {
    throw "This atomic static-release path requires -SkipReindex. Meilisearch changes must use a separately audited reversible data-release path."
  }

  if (-not $SkipPackage) {
    & pwsh ./scripts/package-public-hotfix.ps1 -ReleaseName $ReleaseName
    Assert-LastExitCode "package-public-hotfix"
  }

  if ([string]::IsNullOrWhiteSpace($ZipPath)) {
    $ZipPath = "output/releases/$ReleaseName.zip"
  }
  $ZipPath = Resolve-RepoPath $ZipPath $RepoRoot
  $CandidateManifest = Resolve-RepoPath $CandidateManifest $RepoRoot
  $ReleaseWebRoot = Resolve-RepoPath "output/releases/$ReleaseName/web" $RepoRoot
  if ([string]::IsNullOrWhiteSpace($EvidenceDir)) {
    $EvidenceDir = Resolve-RepoPath "output/releases/$ReleaseName-live-evidence" $RepoRoot
  } else {
    $EvidenceDir = Resolve-RepoPath $EvidenceDir $RepoRoot
  }

  if (-not (Test-Path -LiteralPath $ZipPath -PathType Leaf)) {
    throw "Release ZIP not found: $ZipPath"
  }
  if (-not (Test-Path -LiteralPath $ReleaseWebRoot -PathType Container)) {
    throw "Validated release web root not found: $ReleaseWebRoot"
  }
  if (-not (Test-Path -LiteralPath $CandidateManifest -PathType Leaf)) {
    throw "Candidate manifest not found: $CandidateManifest"
  }

  $ActualZipSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $ZipPath).Hash.ToLowerInvariant()
  if ($ActualZipSha256 -ne $ExpectedZipSha256) {
    throw "Immutable artifact mismatch. Expected $ExpectedZipSha256, got $ActualZipSha256. Upload was not attempted."
  }

  $CandidateManifestSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $CandidateManifest).Hash.ToLowerInvariant()
  $PackagePreflightDir = Join-Path ([System.IO.Path]::GetTempPath()) ("base2026-package-preflight-" + [guid]::NewGuid().ToString("N"))
  $RequiredPackageFiles = @(
    "manifest.json",
    "web/index.html",
    "web/sources/index.html",
    "web/sitemap.xml",
    "web/static/styles.css",
    "public-data/tiktok/manifest.json",
    "public-data/tiktok/source_records.jsonl"
  )
  try {
    New-Item -ItemType Directory -Path $PackagePreflightDir -Force | Out-Null
    Expand-Archive -LiteralPath $ZipPath -DestinationPath $PackagePreflightDir -Force
    foreach ($RequiredPackageFile in $RequiredPackageFiles) {
      if (-not (Test-Path -LiteralPath (Join-Path $PackagePreflightDir $RequiredPackageFile) -PathType Leaf)) {
        throw "Release ZIP does not contain required file: $RequiredPackageFile"
      }
    }
    $PackageManifest = Get-Content -LiteralPath (Join-Path $PackagePreflightDir "manifest.json") -Raw | ConvertFrom-Json
    if ($PackageManifest.schema -ne "base2026.public-hotfix-from-export/v3") {
      throw "Unsupported release package schema: $($PackageManifest.schema)"
    }
    if ($PackageManifest.release_name -ne $ReleaseName) {
      throw "Release manifest name mismatch. Expected $ReleaseName, got $($PackageManifest.release_name)"
    }
    if ($PackageManifest.source_detail.candidate_manifest_sha256 -ne $CandidateManifestSha256) {
      throw "Release package is not bound to the supplied Source Detail candidate manifest."
    }
    if (-not $PackageManifest.source_detail.public_effect_verified_absent) {
      throw "Release package does not contain a positive public-effect exclusion binding."
    }
    if ($PackageManifest.source_detail.archive_sitemap_policy -ne "included" -or $PackageManifest.source_detail.future_private_sitemap_policy -ne "excluded") {
      throw "Release package sitemap policy is not the current Source Detail contract."
    }
  } finally {
    Remove-Item -LiteralPath $PackagePreflightDir -Recurse -Force -ErrorAction SilentlyContinue
  }

  $plan = [ordered]@{
    schema = "base2026.atomic-public-deployment-plan/v1"
    release_name = $ReleaseName
    zip_path = $ZipPath
    zip_sha256 = $ActualZipSha256
    remote_base = $RemoteBase
    live_base_url = $LiveBaseUrl
    release_web_root = $ReleaseWebRoot
    candidate_manifest = $CandidateManifest
    candidate_manifest_sha256 = $CandidateManifestSha256
    evidence_dir = $EvidenceDir
    skip_reindex = $true
    wordpress_root_mutation = $false
    live_qa_required = $true
    automatic_rollback = $true
  }
  Write-Host ($plan | ConvertTo-Json -Depth 5)
  if ($PlanOnly) {
    Write-Host "PLAN_ONLY_OK"
    exit 0
  }

  $RemoteZip = "$RemoteBase/$ReleaseName.zip"
  & scp -- $ZipPath "${SshHost}:$RemoteZip"
  Assert-LastExitCode "scp release"

  $deployTemplate = @'
set -Eeuo pipefail
base='__BASE__'
release='__RELEASE__'
expected_sha='__SHA__'
zip_path="$base/$release.zip"
release_dir="$base/releases/$release"
staging_dir="$base/releases/.$release.staging.$$"
current_link="$base/current"
previous_link="$base/previous"
current_tmp="$base/.current.$release.$$"
previous_tmp="$base/.previous.$release.$$"
previous_target=""
switched=0

cleanup() {
  rm -rf "$staging_dir"
  rm -f "$current_tmp" "$previous_tmp"
}

rollback_on_error() {
  status=$?
  trap - ERR
  set +e
  if [ "$switched" -eq 1 ] && [ -n "$previous_target" ] && [ -d "$previous_target" ]; then
    rollback_tmp="$base/.current.error-rollback.$$"
    rm -f "$rollback_tmp"
    ln -s "$previous_target" "$rollback_tmp" && mv -Tf "$rollback_tmp" "$current_link"
    if nginx -t && systemctl reload nginx && systemctl is-active --quiet nginx; then
      echo "BASE2026_ERROR_ROLLBACK_COMPLETE=$previous_target" >&2
    else
      echo "BASE2026_ERROR_ROLLBACK_FAILED=$previous_target" >&2
    fi
  fi
  cleanup
  exit "$status"
}

trap cleanup EXIT
trap rollback_on_error ERR

test -f "$zip_path"
actual_sha="$(sha256sum "$zip_path" | cut -d ' ' -f 1)"
test "$actual_sha" = "$expected_sha"

test -L "$current_link"
previous_target="$(readlink -f "$current_link")"
test -n "$previous_target"
case "$previous_target" in
  "$base"/releases/*) ;;
  *) echo "Unsafe current target: $previous_target" >&2; exit 70 ;;
esac
test -d "$previous_target"
test ! -e "$release_dir"

mkdir -p "$base/releases" "$base/shared/data" "$base/shared/data/derived" "$base/shared/tmp"
rm -rf "$staging_dir"
mkdir -p "$staging_dir"
unzip -q "$zip_path" -d "$staging_dir"
test -f "$staging_dir/manifest.json"
test -f "$staging_dir/web/index.html"
test -f "$staging_dir/web/sources/index.html"
test -f "$staging_dir/web/sitemap.xml"
test -f "$staging_dir/web/static/styles.css"
test -f "$staging_dir/public-data/tiktok/manifest.json"
test -f "$staging_dir/public-data/tiktok/source_records.jsonl"
ln -sfn "$base/shared/data" "$staging_dir/data"
ln -sfn "$base/shared/tmp" "$staging_dir/tmp"
chown -R www-data:www-data "$staging_dir"
find "$staging_dir" -type d -exec chmod 755 {} +
find "$staging_dir" -type f -exec chmod 644 {} +
mv "$staging_dir" "$release_dir"

ln -s "$previous_target" "$previous_tmp"
mv -Tf "$previous_tmp" "$previous_link"
ln -s "$release_dir" "$current_tmp"
mv -Tf "$current_tmp" "$current_link"
switched=1

nginx -t
systemctl reload nginx
systemctl is-active --quiet nginx
test "$(readlink -f "$current_link")" = "$release_dir"
switched=0

echo "BASE2026_PREVIOUS_TARGET=$previous_target"
echo "BASE2026_CURRENT_TARGET=$release_dir"
echo "BASE2026_REMOTE_ZIP_SHA256=$actual_sha"
'@
  $RemoteDeployScript = $deployTemplate.Replace('__BASE__', $RemoteBase).Replace('__RELEASE__', $ReleaseName).Replace('__SHA__', $ExpectedZipSha256)
  $RemoteDeployOutput = @($RemoteDeployScript | & ssh $SshHost "bash -s")
  $RemoteDeployExit = $LASTEXITCODE
  $RemoteDeployOutput | ForEach-Object { Write-Host $_ }
  if ($RemoteDeployExit -ne 0) {
    throw "Remote atomic deployment failed with exit code $RemoteDeployExit. The remote error trap attempted rollback before exit."
  }

  $PreviousTarget = (($RemoteDeployOutput | Where-Object { $_ -like 'BASE2026_PREVIOUS_TARGET=*' } | Select-Object -Last 1) -replace '^BASE2026_PREVIOUS_TARGET=', '')
  $CurrentTarget = (($RemoteDeployOutput | Where-Object { $_ -like 'BASE2026_CURRENT_TARGET=*' } | Select-Object -Last 1) -replace '^BASE2026_CURRENT_TARGET=', '')
  if ([string]::IsNullOrWhiteSpace($PreviousTarget) -or [string]::IsNullOrWhiteSpace($CurrentTarget)) {
    try { Invoke-RemoteRollback $SshHost $RemoteBase $ReleaseName | Out-Null } catch { Write-Error $_ }
    throw "Remote deployment markers were incomplete; rollback was requested."
  }

  try {
    & pwsh ./scripts/invoke-source-detail-v2-live-gate.ps1 `
      -ReleaseName $ReleaseName `
      -ExpectedZipSha256 $ExpectedZipSha256 `
      -BaseUrl $LiveBaseUrl `
      -WebRoot $ReleaseWebRoot `
      -CandidateManifest $CandidateManifest `
      -EvidenceDir $EvidenceDir
    Assert-LastExitCode "mandatory source-detail-v2 live gate"

    $DeploymentReceipt = [ordered]@{
      schema = "base2026.atomic-public-deployment-receipt/v1"
      completed_at = (Get-Date).ToUniversalTime().ToString("o")
      release_name = $ReleaseName
      zip_path = $ZipPath
      zip_sha256 = $ExpectedZipSha256
      remote_base = $RemoteBase
      previous_target = $PreviousTarget
      current_target = $CurrentTarget
      live_base_url = $LiveBaseUrl
      evidence_dir = $EvidenceDir
      skip_reindex = $true
      wordpress_root_mutation = $false
      live_qa = "PASS"
      rollback_armed = $true
    }
    New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null
    $ReceiptPath = Join-Path $EvidenceDir "deployment-receipt.json"
    $DeploymentReceipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $ReceiptPath -Encoding utf8

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
      schema = "base2026.deployment-evidence-sha256/v1"
      release_name = $ReleaseName
      files = @($EvidenceHashes)
    } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $SumsPath -Encoding utf8
    $SumsSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $SumsPath).Hash.ToLowerInvariant()
  } catch {
    $GateError = $_
    try {
      Invoke-RemoteRollback $SshHost $RemoteBase $ReleaseName | Out-Null
    } catch {
      throw "Live QA/evidence failed: $($GateError.Exception.Message). Automatic rollback also failed: $($_.Exception.Message)"
    }
    throw "Live QA/evidence failed and automatic rollback completed: $($GateError.Exception.Message)"
  }

  Write-Host "deployed=$LiveBaseUrl"
  Write-Host "release=$ReleaseName"
  Write-Host "zip_sha256=$ExpectedZipSha256"
  Write-Host "evidence=$EvidenceDir"
  Write-Host "evidence_sha256=$SumsSha256"
  Write-Host "result=DEPLOYED_AND_LIVE_QA_PASS"
} finally {
  Pop-Location
}
