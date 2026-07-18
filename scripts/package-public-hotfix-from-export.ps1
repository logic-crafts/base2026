param(
  [string]$ReleaseName = "",
  [string]$SourceExportRoot = "./public-data/tiktok",
  [string]$MeiliUrl = "/knowledge-search",
  [string]$MeiliIndex = "base2026_public_tiktok",
  [string]$MeiliKey = "",
  [string]$SourceDetailCandidate = "",
  [string]$SourceAdmissionClosureReceipt = ""
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root
$StaticSitemapAdmission = Resolve-Path "./contracts/base2026-sitemap-static-routes.json"

function Assert-NativeSuccess {
  param([string]$Label)
  if ($LASTEXITCODE -ne 0) {
    throw "$Label failed with exit code $LASTEXITCODE."
  }
}

function Get-LineCount {
  param([string]$Path)
  return [int]((Get-Content -Path $Path | Measure-Object -Line).Lines)
}

if (-not $ReleaseName) {
  $ReleaseName = "base2026-public-hotfix-" + (Get-Date -Format "yyyyMMdd-HHmmss")
}
if ($ReleaseName -notmatch '^[A-Za-z0-9._-]+$') {
  throw "ReleaseName may contain only letters, numbers, dot, underscore, and dash."
}
if ([string]::IsNullOrWhiteSpace($SourceDetailCandidate)) {
  throw "SourceDetailCandidate is mandatory for the v4 data-preserving hotfix contract."
}
if ([string]::IsNullOrWhiteSpace($SourceAdmissionClosureReceipt)) {
  throw "SourceAdmissionClosureReceipt is mandatory for the v4 data-preserving hotfix contract."
}

$SourceExport = Resolve-Path $SourceExportRoot
$CacheBust = ($ReleaseName -replace '[^A-Za-z0-9._-]', '-')

$RequiredExportFiles = @("manifest.json", "documents.jsonl", "source_records.jsonl", "passages.jsonl", "creators.jsonl")
foreach ($File in $RequiredExportFiles) {
  if (-not (Test-Path (Join-Path $SourceExport $File))) {
    throw "Source export is missing ${File}: $SourceExport"
  }
}

$SourceCounts = @{}
foreach ($File in @("documents.jsonl", "source_records.jsonl", "passages.jsonl", "creators.jsonl", "insight_cards.jsonl")) {
  $Path = Join-Path $SourceExport $File
  if (Test-Path $Path) {
    $SourceCounts[$File] = Get-LineCount $Path
  }
}

$BuildRoot = Join-Path $Root "output\release-build\$ReleaseName"
$ExportRoot = Join-Path $BuildRoot "public-data\tiktok"
if (Test-Path $BuildRoot) {
  Remove-Item $BuildRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $ExportRoot | Out-Null
Copy-Item (Join-Path $SourceExport "*") $ExportRoot -Recurse -Force

python3 ./scripts/repair-public-text-excerpts.py --data $ExportRoot | Write-Output
Assert-NativeSuccess "repair-public-text-excerpts"
python3 ./scripts/check-public-export-policy.py $ExportRoot | Write-Output
Assert-NativeSuccess "check-public-export-policy"
python3 ./scripts/validate-public-text-excerpts.py --data $ExportRoot | Write-Output
Assert-NativeSuccess "validate-public-text-excerpts"

foreach ($File in $SourceCounts.Keys) {
  $Path = Join-Path $ExportRoot $File
  if (-not (Test-Path $Path)) {
    throw "Hotfix export dropped $File."
  }
  $NewCount = Get-LineCount $Path
  if ($NewCount -ne $SourceCounts[$File]) {
    throw "Hotfix export changed ${File} count: was $($SourceCounts[$File]), now $NewCount."
  }
}

python3 ./scripts/generate-info-pages.py --source ./docs/public-pages --out ./web/static | Write-Output
Assert-NativeSuccess "generate-info-pages"
if (Test-Path "./data/ai_visibility_pages_master.json") {
  python3 ./scripts/generate-ai-visibility-pages.py --input ./data/ai_visibility_pages_master.json --out ./web/static --indexable | Write-Output
  Assert-NativeSuccess "generate-ai-visibility-pages"
} elseif (Test-Path "./data/ai_visibility_pages_batch01.json") {
  python3 ./scripts/generate-ai-visibility-pages.py --input ./data/ai_visibility_pages_batch01.json --out ./web/static --indexable | Write-Output
  Assert-NativeSuccess "generate-ai-visibility-pages"
}

$ReleaseRoot = Join-Path $Root "output\releases\$ReleaseName"
$WebRoot = Join-Path $ReleaseRoot "web"
$StaticRoot = Join-Path $WebRoot "static"
$ScriptsRoot = Join-Path $ReleaseRoot "scripts"
$DataRoot = Join-Path $ReleaseRoot "public-data\tiktok"

if (Test-Path $ReleaseRoot) {
  Remove-Item $ReleaseRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $StaticRoot, $ScriptsRoot, $DataRoot | Out-Null

$Html = Get-Content -Path ".\web\static\meili.html" -Raw
$Html = $Html -replace 'href="(?:\./|/)static/styles\.css\?v=[^"]+"', "href=`"./static/styles.css?v=$CacheBust`""
$Html = $Html -replace 'src="(?:\./|/)static/meili\.js\?v=[^"]+"', "src=`"./static/meili.js?v=$CacheBust`""
$Html = $Html -replace 'src="(?:\./|/)static/cookie-consent\.js\?v=[^"]+"', "src=`"./static/cookie-consent.js?v=$CacheBust`""
$ConfigLines = @(
  '    <script>',
  "      window.BASE2026_MEILI_URL = `"$MeiliUrl`";",
  "      window.BASE2026_MEILI_INDEX = `"$MeiliIndex`";",
  "      window.BASE2026_ASSET_VERSION = `"$CacheBust`";"
)
if ($MeiliKey -ne "") {
  $ConfigLines += "      window.BASE2026_MEILI_KEY = `"$MeiliKey`";"
}
$ConfigLines += '    </script>'
$Config = $ConfigLines -join "`n"
$ConfigPattern = '(?s)\s*<script>\s*window\.BASE2026_MEILI_URL\s*=.*?</script>'
$Html = [regex]::Replace($Html, $ConfigPattern, "`n$Config", 1)
$Html | Set-Content -Path (Join-Path $WebRoot "index.html") -Encoding UTF8

Copy-Item "./web/static/styles.css" (Join-Path $StaticRoot "styles.css") -Force
Copy-Item "./web/static/alex-design-system-v2.css" (Join-Path $StaticRoot "alex-design-system-v2.css") -Force
Copy-Item "./web/static/base2026" (Join-Path $StaticRoot "base2026") -Recurse -Force
Copy-Item "./web/static/alex-v4-static-shell.js" (Join-Path $StaticRoot "alex-v4-static-shell.js") -Force
Copy-Item "./web/static/base2026-solution-journey.js" (Join-Path $StaticRoot "base2026-solution-journey.js") -Force
Copy-Item "./web/static/base2026-solution-journey.css" (Join-Path $StaticRoot "base2026-solution-journey.css") -Force
if (Test-Path "./web/static/base2026-solution-journey.json") {
  Copy-Item "./web/static/base2026-solution-journey.json" (Join-Path $StaticRoot "base2026-solution-journey.json") -Force
}
Copy-Item "./web/static/vendor" (Join-Path $StaticRoot "vendor") -Recurse -Force
Copy-Item "./web/static/meili.js" (Join-Path $StaticRoot "meili.js") -Force
Copy-Item "./web/static/cookie-consent.js" (Join-Path $StaticRoot "cookie-consent.js") -Force
Copy-Item "./web/static/share-actions.js" (Join-Path $StaticRoot "share-actions.js") -Force
if (Test-Path "./web/static/roadmap.js") {
  Copy-Item "./web/static/roadmap.js" (Join-Path $StaticRoot "roadmap.js") -Force
}
if (Test-Path "./web/static/assets") {
  Copy-Item "./web/static/assets" (Join-Path $StaticRoot "assets") -Recurse -Force
}
foreach ($ReadabilityAsset in @(
  @{ Source = "./web/static/llms.txt"; Target = (Join-Path $WebRoot "llms.txt") },
  @{ Source = "./web/static/data-dictionary.json"; Target = (Join-Path $WebRoot "data-dictionary.json") },
  @{ Source = "./web/static/api-index.json"; Target = (Join-Path $WebRoot "api-index.json") },
  @{ Source = "./web/static/llms-root.txt"; Target = (Join-Path $WebRoot "root-llms.txt") }
)) {
  if (Test-Path $ReadabilityAsset.Source) {
    Copy-Item $ReadabilityAsset.Source $ReadabilityAsset.Target -Force
  }
}
foreach ($TestPageAsset in @("roadmap-dataviz-test.html", "roadmap-dataviz-test.css", "roadmap-dataviz-test.js")) {
  if (Test-Path "./web/static/$TestPageAsset") {
    Copy-Item "./web/static/$TestPageAsset" (Join-Path $WebRoot $TestPageAsset) -Force
  }
}

$DocPages = @(
  "methodology.html",
  "api.html",
  "apply-research.html",
  "opt-out.html",
  "roadmap.html",
  "story.html",
  "privacy.html",
  "source-policy.html",
  "support.html",
  "site-structure.html"
)
foreach ($DocPage in $DocPages) {
  $DocHtml = Get-Content -Path "./web/static/$DocPage" -Raw
  $DocHtml = $DocHtml -replace 'href="(?:\./|/)static/styles\.css\?v=[^"]+"', "href=`"./static/styles.css?v=$CacheBust`""
  $DocHtml = $DocHtml -replace 'src="(?:\./|/)static/cookie-consent\.js\?v=[^"]+"', "src=`"./static/cookie-consent.js?v=$CacheBust`""
  $DocHtml | Set-Content -Path (Join-Path $WebRoot $DocPage) -Encoding UTF8
}

$SignalBriefPath = Join-Path $ExportRoot "topic_signal_briefs.jsonl"
python3 ./scripts/generate-topic-signal-briefs.py --data $ExportRoot --out $SignalBriefPath --max-topics 50 | Write-Output
Assert-NativeSuccess "generate-topic-signal-briefs"
$AnalyticsPath = Join-Path $ExportRoot "base2026_analytics.json"
python3 ./scripts/generate-base2026-analytics.py --data $ExportRoot --out $AnalyticsPath | Write-Output
Assert-NativeSuccess "generate-base2026-analytics"
$AnalyticsSummaryPath = Join-Path $ExportRoot "analytics_summary.json"
python3 ./scripts/generate-public-analytics.py --data $ExportRoot --out $AnalyticsSummaryPath | Write-Output
Assert-NativeSuccess "generate-public-analytics"

foreach ($StaticDataFile in @("documents.jsonl", "passages.jsonl", "insight_cards.jsonl", "manifest.json", "topic_signal_briefs.jsonl", "base2026_analytics.json", "analytics_summary.json")) {
  $StaticDataSource = Join-Path $ExportRoot $StaticDataFile
  if (Test-Path $StaticDataSource) {
    Copy-Item $StaticDataSource (Join-Path $StaticRoot $StaticDataFile) -Force
  } elseif (Test-Path "./web/static/$StaticDataFile") {
    Copy-Item "./web/static/$StaticDataFile" (Join-Path $StaticRoot $StaticDataFile) -Force
  }
}
Copy-Item "./scripts/meili-index-public.py" (Join-Path $ScriptsRoot "meili-index-public.py") -Force
Copy-Item (Join-Path $ExportRoot "*") $DataRoot -Recurse -Force
python3 ./scripts/generate-public-pages.py --data $ExportRoot --out $WebRoot | Write-Output
Assert-NativeSuccess "generate-public-pages"
if (Test-Path "./data/ai_visibility_pages_master.json") {
  python3 ./scripts/generate-ai-visibility-pages.py --input ./data/ai_visibility_pages_master.json --out $WebRoot --indexable | Write-Output
  Assert-NativeSuccess "generate-ai-visibility-pages-release"
} elseif (Test-Path "./data/ai_visibility_pages_batch01.json") {
  python3 ./scripts/generate-ai-visibility-pages.py --input ./data/ai_visibility_pages_batch01.json --out $WebRoot --indexable | Write-Output
  Assert-NativeSuccess "generate-ai-visibility-pages-release"
}
if (Test-Path "./data/base2026_ai_recommends_solutions_pilot.json") {
  $SolutionInput = "./data/base2026_ai_recommends_solutions_pilot.json"
  $SolutionReport = Join-Path $BuildRoot "ai-recommends-solutions-generation.json"
  $SolutionHtmlReport = Join-Path $BuildRoot "ai-recommends-solutions-html-qa.json"
  python3 ./scripts/validate-ai-recommends-solutions.py --input $SolutionInput --data-root $ExportRoot --report (Join-Path $BuildRoot "ai-recommends-solutions-validation.json") | Write-Output
  Assert-NativeSuccess "validate-ai-recommends-solutions"
  python3 ./scripts/generate-ai-recommends-solutions.py --input $SolutionInput --data-root $ExportRoot --out $WebRoot --report $SolutionReport | Write-Output
  Assert-NativeSuccess "generate-ai-recommends-solutions"
  Copy-Item (Join-Path $WebRoot "ai-recommends-solutions.js") (Join-Path $StaticRoot "ai-recommends-solutions.js") -Force
  Copy-Item "./web/static/alex-v4-static-shell.js" (Join-Path $StaticRoot "alex-v4-static-shell.js") -Force
  python3 ./scripts/validate-ai-recommends-html.py --out $WebRoot --generation-report $SolutionReport --report $SolutionHtmlReport | Write-Output
  Assert-NativeSuccess "validate-ai-recommends-html"
}

$ResolvedSourceDetailCandidate = Resolve-Path $SourceDetailCandidate
$CandidateManifest = Join-Path $ResolvedSourceDetailCandidate "candidate-manifest.json"
$CandidateSources = Join-Path $ResolvedSourceDetailCandidate "sources"
$CandidateStatic = Join-Path $ResolvedSourceDetailCandidate "static"
if (-not (Test-Path $CandidateManifest -PathType Leaf)) {
  throw "Source Detail V2 candidate manifest is missing: $CandidateManifest"
}
if (-not (Test-Path $CandidateSources -PathType Container)) {
  throw "Source Detail V2 candidate sources directory is missing: $CandidateSources"
}
if (-not (Test-Path $CandidateStatic -PathType Container)) {
  throw "Source Detail V2 candidate static directory is missing: $CandidateStatic"
}
$ResolvedSourceAdmissionClosureReceipt = Resolve-Path $SourceAdmissionClosureReceipt
$SourceAdmissionClosureReceiptJson = Get-Content $ResolvedSourceAdmissionClosureReceipt -Raw | ConvertFrom-Json
if ($SourceAdmissionClosureReceiptJson.status -ne "PASS") {
  throw "Source admission closure receipt is not PASS."
}
if (-not $SourceAdmissionClosureReceiptJson.verification.all_13_absent_from_all_public_export_files) {
  throw "Source admission closure receipt does not prove the new future/private records are absent from every public export artifact."
}
$SourceDetailCandidateManifestJson = Get-Content $CandidateManifest -Raw | ConvertFrom-Json
$SourceAdmissionLedgerPath = Resolve-Path "./12_knowledge-base/sources/tiktok/source-admission.jsonl"
$SourceAdmissionLedgerSha256 = (Get-FileHash -Algorithm SHA256 $SourceAdmissionLedgerPath).Hash.ToLowerInvariant()
if ($SourceAdmissionClosureReceiptJson.ledger_new_sha256 -ne $SourceAdmissionLedgerSha256) {
  throw "Source admission closure receipt is stale for the current ledger."
}
if ($SourceDetailCandidateManifestJson.expected.'200:normal_public_card' -ne $SourceAdmissionClosureReceiptJson.admission_counts.normal_public_card -or
    $SourceDetailCandidateManifestJson.expected.'200:provenance_archive_noindex' -ne $SourceAdmissionClosureReceiptJson.admission_counts.provenance_archive_noindex -or
    $SourceDetailCandidateManifestJson.expected.'404:future_private_backlog' -ne $SourceAdmissionClosureReceiptJson.admission_counts.future_private_backlog) {
  throw "Source Detail candidate counts are not bound to the source admission closure receipt."
}

python3 ./scripts/validate-source-detail-v2-full-candidate.py --candidate $ResolvedSourceDetailCandidate --source-root ./web/static | Write-Output
Assert-NativeSuccess "validate-source-detail-v2-full-candidate-before-package"

$ReleaseSources = Join-Path $WebRoot "sources"
$CandidateNames = @(Get-ChildItem -Path $CandidateSources -Filter "tiktok-video-*.html" -File | ForEach-Object { $_.Name } | Sort-Object)
$ReleaseNames = @(Get-ChildItem -Path $ReleaseSources -Filter "tiktok-video-*.html" -File | ForEach-Object { $_.Name } | Sort-Object)
$SourceNameDiff = @(Compare-Object -ReferenceObject $CandidateNames -DifferenceObject $ReleaseNames)
if ($SourceNameDiff.Count -ne 0) {
  $DiffPreview = ($SourceNameDiff | Select-Object -First 20 | Out-String)
  throw "Source Detail V2 candidate/release route membership differs before overlay:`n$DiffPreview"
}
Copy-Item (Join-Path $CandidateSources "tiktok-video-*.html") $ReleaseSources -Force

Get-ChildItem -Path $CandidateStatic -Recurse -File | ForEach-Object {
  $RelativeAsset = [System.IO.Path]::GetRelativePath($CandidateStatic, $_.FullName)
  $TargetAsset = Join-Path $StaticRoot $RelativeAsset
  New-Item -ItemType Directory -Force -Path (Split-Path $TargetAsset -Parent) | Out-Null
  Copy-Item $_.FullName $TargetAsset -Force
}
python3 ./scripts/apply-alex-design-system-v2.py --web-root $WebRoot | Write-Output
Assert-NativeSuccess "apply-alex-design-system-v2"
python3 ./scripts/check-public-content-readiness.py --data-root $ExportRoot --latest 1 --web-root $WebRoot --allow-generated-noindex --fail | Write-Output
Assert-NativeSuccess "check-public-content-readiness-generated"
Get-ChildItem -Path "./web/static" -Filter "indexnow-*.txt" -File -ErrorAction SilentlyContinue | ForEach-Object {
  $Target = Join-Path $WebRoot $_.Name
  Copy-Item $_.FullName $Target -Force
  chmod 0644 $Target
}
$SitemapArgs = @(
  "./scripts/generate-base2026-sitemap.py",
  "--web-root", $WebRoot,
  "--static-admission-manifest", $StaticSitemapAdmission,
  "--source-detail-manifest", $CandidateManifest
)
python3 @SitemapArgs | Write-Output
Assert-NativeSuccess "generate-base2026-sitemap"

$VersionedAssets = @(
  "styles.css",
  "alex-design-system-v2.css",
  "ai-recommends-solutions.js",
  "alex-v4-static-shell.js",
  "base2026-solution-journey.js",
  "base2026-solution-journey.css",
  "source-detail-v2.js",
  "meili.js",
  "cookie-consent.js",
  "share-actions.js",
  "roadmap.js"
)
Get-ChildItem -Path $WebRoot -Recurse -Filter "*.html" | ForEach-Object {
  $PageHtml = Get-Content -Path $_.FullName -Raw
  foreach ($Asset in $VersionedAssets) {
    $EscapedAsset = [regex]::Escape($Asset)
    $AssetPattern = "(?i)(href|src)=`"([^`"]*static/$EscapedAsset)\?v=[^`"]*`""
    $PageHtml = [regex]::Replace($PageHtml, $AssetPattern, {
      param($Match)
      $Match.Groups[1].Value + '="' + $Match.Groups[2].Value + "?v=$CacheBust" + '"'
    })
  }
  [System.IO.File]::WriteAllText(
    $_.FullName,
    $PageHtml,
    [System.Text.UTF8Encoding]::new($false)
  )
}

python3 ./scripts/validate-public-manifests.py `
  --dataset-manifest (Join-Path $ExportRoot "manifest.json") `
  --dataset-manifest (Join-Path $StaticRoot "manifest.json") `
  --dataset-manifest (Join-Path $DataRoot "manifest.json") `
  --page-manifest (Join-Path $WebRoot "manifest.json") `
  --web-root $WebRoot | Write-Output
Assert-NativeSuccess "validate-public-manifests"
python3 @SitemapArgs --check-only | Write-Output
Assert-NativeSuccess "validate-base2026-sitemap-contract"

$SourceDetailPackageReport = Join-Path $BuildRoot "source-detail-v2-package-validation.json"
python3 ./scripts/validate-source-detail-v2-release-package.py --candidate $ResolvedSourceDetailCandidate --web-root $WebRoot --report $SourceDetailPackageReport | Write-Output
Assert-NativeSuccess "validate-source-detail-v2-release-package"
Copy-Item (Join-Path $ResolvedSourceDetailCandidate "candidate-manifest.json") (Join-Path $ReleaseRoot "SOURCE_DETAIL_V2_CANDIDATE_MANIFEST.json") -Force
Copy-Item $SourceDetailPackageReport (Join-Path $ReleaseRoot "SOURCE_DETAIL_V2_PACKAGE_VALIDATION.json") -Force
Copy-Item $StaticSitemapAdmission (Join-Path $ReleaseRoot "SITEMAP_STATIC_ADMISSION.json") -Force

$Manifest = Get-Content (Join-Path $ExportRoot "manifest.json") -Raw
$CandidateManifestHash = (Get-FileHash -Algorithm SHA256 (Join-Path $ResolvedSourceDetailCandidate "candidate-manifest.json")).Hash.ToLowerInvariant()
$SourceDetailScope = @"
- Overlay the validated immutable Source Detail V2 candidate.
- Source Detail V2 candidate: $ResolvedSourceDetailCandidate
- Source Detail V2 candidate manifest SHA-256: $CandidateManifestHash
"@
$ReleaseInfo = @"
Base2026 Public TikTok Data-Preserving Hotfix Release
Release: $ReleaseName
Created: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Meili URL: $MeiliUrl
Meili index: $MeiliIndex
Source export: $SourceExport

Hotfix scope:
- Preserve existing public export membership and counts.
- Repair public excerpt text from reviewed public passages.
- Rebuild static pages and assets with current UI fixes.
$SourceDetailScope
Dataset manifest:
$Manifest

Server target:
/var/www/base2026-knowledge/releases/$ReleaseName

Public path:
/knowledge/
"@
$ReleaseInfo | Set-Content -Path (Join-Path $ReleaseRoot "RELEASE.txt") -Encoding UTF8

$SourceDetailPackageContract = [ordered]@{
  candidate_manifest_sha256 = $CandidateManifestHash
  route_manifest_sha256 = $SourceDetailCandidateManifestJson.route_manifest_sha256
  source_admission_ledger_sha256 = $SourceAdmissionLedgerSha256
  source_admission_closure_receipt_sha256 = (Get-FileHash -Algorithm SHA256 $ResolvedSourceAdmissionClosureReceipt).Hash.ToLowerInvariant()
  counts = [ordered]@{
    normal_public_card = [int]$SourceDetailCandidateManifestJson.expected.'200:normal_public_card'
    provenance_archive_noindex = [int]$SourceDetailCandidateManifestJson.expected.'200:provenance_archive_noindex'
    future_private_backlog = [int]$SourceDetailCandidateManifestJson.expected.'404:future_private_backlog'
  }
  public_effect_verified_absent = [bool]$SourceAdmissionClosureReceiptJson.verification.all_13_absent_from_all_public_export_files
  archive_sitemap_policy = "excluded"
  future_private_sitemap_policy = "excluded"
  source_sitemap_admission = "exact"
}
$PackageManifest = [ordered]@{
  schema = "base2026.public-hotfix-from-export/v4"
  release_name = $ReleaseName
  package_mode = "data-preserving-static-release"
  source_export_manifest_sha256 = (Get-FileHash -Algorithm SHA256 (Join-Path $ExportRoot "manifest.json")).Hash.ToLowerInvariant()
  source_detail = $SourceDetailPackageContract
  sitemap_contract = [ordered]@{
    schema = "base2026.sitemap-admission/v2"
    static_admission_manifest_sha256 = (Get-FileHash -Algorithm SHA256 $StaticSitemapAdmission).Hash.ToLowerInvariant()
    static_admission_policy = "frozen_exact_allowlist"
    source_admission_policy = "exact"
    archive_noindex_policy = "excluded"
    future_private_policy = "excluded"
    global_exact_admission = $true
  }
  required_contract_files = @(
    "SOURCE_DETAIL_V2_CANDIDATE_MANIFEST.json",
    "SITEMAP_STATIC_ADMISSION.json"
  )
  required_runtime_files = @(
    "web/index.html",
    "web/sources/index.html",
    "web/sitemap.xml",
    "web/static/styles.css",
    "web/static/alex-design-system-v2.css",
    "web/static/base2026/tokens.css",
    "web/static/base2026/shell.css",
    "web/static/base2026/components.css",
    "web/static/alex-v4-static-shell.js",
    "web/static/base2026-solution-journey.js",
    "web/static/base2026-solution-journey.css",
    "web/static/vendor/manrope-400.ttf",
    "web/static/vendor/manrope-500.ttf",
    "web/static/vendor/manrope-600.ttf",
    "web/static/vendor/manrope-700.ttf",
    "web/static/vendor/manrope-800.ttf",
    "web/static/vendor/geist-400.ttf",
    "web/static/vendor/geist-500.ttf",
    "web/static/vendor/geist-600.ttf",
    "web/static/vendor/geist-700.ttf",
    "web/static/vendor/geist-800.ttf",
    "web/static/vendor/geist-mono-400.ttf",
    "web/static/vendor/geist-mono-600.ttf",
    "web/static/vendor/geist-mono-700.ttf",
    "web/manifest.json",
    "web/static/manifest.json",
    "public-data/tiktok/manifest.json",
    "public-data/tiktok/source_records.jsonl"
  )
}
$PackageManifest | ConvertTo-Json -Depth 8 | Set-Content -Path (Join-Path $ReleaseRoot "manifest.json") -Encoding UTF8

$ZipPath = Join-Path $Root "output\releases\$ReleaseName.zip"
$ZipScript = @'
import sys
import zipfile
from pathlib import Path

release_root = Path(sys.argv[1])
zip_path = Path(sys.argv[2])
if zip_path.exists():
    zip_path.unlink()

with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in release_root.rglob("*"):
        if path.is_file():
            archive.write(path, path.relative_to(release_root).as_posix())
'@
$ZipScript | python3 - $ReleaseRoot $ZipPath
Assert-NativeSuccess "zip-public-hotfix-release"

Write-Output "release=$ReleaseName"
Write-Output "path=$ReleaseRoot"
Write-Output "zip=$ZipPath"
