param(
  [string]$ReleaseName = "",
  [string]$MeiliUrl = "/knowledge-search",
  [string]$MeiliIndex = "base2026_public_tiktok",
  [string]$MeiliKey = ""
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

function Assert-NativeSuccess {
  param([string]$Label)
  if ($LASTEXITCODE -ne 0) {
    throw "$Label failed with exit code $LASTEXITCODE."
  }
}

if (-not $ReleaseName) {
  $ReleaseName = "base2026-public-" + (Get-Date -Format "yyyyMMdd-HHmmss")
}
$CacheBust = ($ReleaseName -replace '[^A-Za-z0-9._-]', '-')

$BuildRoot = Join-Path $Root "output\release-build\$ReleaseName"
$ExportRoot = Join-Path $BuildRoot "public-data\tiktok"
if (Test-Path $BuildRoot) {
  Remove-Item $BuildRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $ExportRoot | Out-Null

$ExportArgs = @("./scripts/export-public-tiktok.py", "--out", $ExportRoot)
python3 @ExportArgs | Write-Output
Assert-NativeSuccess "export-public-tiktok"
python3 ./scripts/check-public-export-policy.py $ExportRoot | Write-Output
Assert-NativeSuccess "check-public-export-policy"
python3 ./scripts/validate-public-text-excerpts.py --data $ExportRoot | Write-Output
Assert-NativeSuccess "validate-public-text-excerpts"
python3 ./scripts/validate-public-release-contract.py --export-dir $ExportRoot --baseline-export-dir ./public-data/tiktok --enforce-count-floor | Write-Output
Assert-NativeSuccess "validate-public-release-contract"
python3 ./scripts/check-public-content-readiness.py --data-root $ExportRoot --latest 1 | Write-Output
Assert-NativeSuccess "check-public-content-readiness-audit"
$SignalBriefPath = Join-Path $ExportRoot "topic_signal_briefs.jsonl"
python3 ./scripts/generate-topic-signal-briefs.py --data $ExportRoot --out $SignalBriefPath --max-topics 50 | Write-Output
Assert-NativeSuccess "generate-topic-signal-briefs"
$AnalyticsPath = Join-Path $ExportRoot "base2026_analytics.json"
python3 ./scripts/generate-base2026-analytics.py --data $ExportRoot --out $AnalyticsPath | Write-Output
Assert-NativeSuccess "generate-base2026-analytics"
$AnalyticsSummaryPath = Join-Path $ExportRoot "analytics_summary.json"
python3 ./scripts/generate-public-analytics.py --data $ExportRoot --out $AnalyticsSummaryPath | Write-Output
Assert-NativeSuccess "generate-public-analytics"
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
foreach ($StaticDataFile in @("documents.jsonl", "passages.jsonl", "insight_cards.jsonl", "manifest.json", "topic_signal_briefs.jsonl", "base2026_analytics.json", "analytics_summary.json")) {
  Copy-Item (Join-Path $ExportRoot $StaticDataFile) (Join-Path $StaticRoot $StaticDataFile) -Force
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
  Copy-Item (Join-Path $WebRoot "ai-recommends-solutions.css") (Join-Path $StaticRoot "ai-recommends-solutions.css") -Force
  Copy-Item (Join-Path $WebRoot "alex-v4-static-shell.css") (Join-Path $StaticRoot "alex-v4-static-shell.css") -Force
  Copy-Item (Join-Path $WebRoot "alex-v4-static-shell.js") (Join-Path $StaticRoot "alex-v4-static-shell.js") -Force
  python3 ./scripts/validate-ai-recommends-html.py --out $WebRoot --generation-report $SolutionReport --report $SolutionHtmlReport | Write-Output
  Assert-NativeSuccess "validate-ai-recommends-html"
}
Get-ChildItem -Path "./web/static" -Filter "indexnow-*.txt" -File -ErrorAction SilentlyContinue | ForEach-Object {
  $Target = Join-Path $WebRoot $_.Name
  Copy-Item $_.FullName $Target -Force
  chmod 0644 $Target
}
python3 ./scripts/check-public-content-readiness.py --data-root $ExportRoot --latest 1 --web-root $WebRoot --allow-generated-noindex --fail | Write-Output
Assert-NativeSuccess "check-public-content-readiness-generated"
python3 ./scripts/generate-base2026-sitemap.py --web-root $WebRoot | Write-Output
Assert-NativeSuccess "generate-base2026-sitemap"

# Normalize generated asset cache-busts after every generator has written HTML.
# Source/topic pages use ../static/... paths, while root pages use ./static/...
# paths; the public package must give all of them the current release version.
$VersionedAssets = @(
  "styles.css",
  "ai-recommends-solutions.css",
  "alex-v4-static-shell.css",
  "alex-v4-static-shell.js",
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
  $PageHtml | Set-Content -Path $_.FullName -Encoding UTF8
}

$Manifest = Get-Content (Join-Path $ExportRoot "manifest.json") -Raw
$ReleaseInfo = @"
Base2026 Public TikTok Release
Release: $ReleaseName
Created: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Meili URL: $MeiliUrl
Meili index: $MeiliIndex

Dataset manifest:
$Manifest

Server target:
/var/www/base2026-knowledge/releases/$ReleaseName

Public path:
/knowledge/
"@
$ReleaseInfo | Set-Content -Path (Join-Path $ReleaseRoot "RELEASE.txt") -Encoding UTF8

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
Assert-NativeSuccess "zip-public-release"

Write-Output "release=$ReleaseName"
Write-Output "path=$ReleaseRoot"
Write-Output "zip=$ZipPath"
