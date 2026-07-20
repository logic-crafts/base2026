from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "package-public-hotfix-from-export.ps1"
DEPLOY_SCRIPT = ROOT / "scripts" / "deploy-public-vps.ps1"


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is not installed")
def test_v4_hotfix_package_fails_before_build_without_candidate() -> None:
    result = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(SCRIPT),
            "-ReleaseName",
            "contract-fixture-no-candidate",
            "-SourceDetailCandidate",
            "",
            "-SourceAdmissionClosureReceipt",
            "",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "SourceDetailCandidate is mandatory" in (result.stdout + result.stderr)
    assert not (ROOT / "output" / "release-build" / "contract-fixture-no-candidate").exists()


def test_deploy_preflight_uses_its_defined_native_exit_helper() -> None:
    source = DEPLOY_SCRIPT.read_text(encoding="utf-8")

    assert "Assert-NativeSuccess" not in source
    assert 'Assert-LastExitCode "validate-public-manifests-package-preflight"' in source
    assert 'Assert-LastExitCode "validate-sitemap-package-preflight"' in source


def test_hotfix_packager_uses_generic_closure_and_explicit_source_root() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "SourceDetailSourceRoot" in source
    assert "SourceAdmissionLedger" in source
    assert "ProtectedSearchRoot" in source
    assert "verify-base2026-search-preservation.py" in source
    assert "apply-base2026-product-truth-runtime.py" in source
    assert '"./web/static/purify.min.js"' in source
    assert "SEARCH_SEMANTIC_ORACLE.json" in source
    assert "all_future_private_identifiers_absent_from_all_public_export_files" in source
    assert "base2026.source-admission-public-closure/v2" in source
    assert "AllowLegacySourceAdmissionClosureReceipt" in source
    assert "public_export_manifest_sha256" in source
    assert "public_effect_verification_field" in source
    assert "--source-root $ResolvedSourceDetailSourceRoot" in source
    assert '$SourceAdmissionLedgerPath = Resolve-Path $SourceAdmissionLedger' in source
    assert '$CandidateSourceFiles = @(Get-ChildItem -Path $CandidateSources -Filter "tiktok-video-*.html" -File -Force)' in source
    assert '$CandidateSourceFiles | Copy-Item -Destination $ReleaseSources -Force' in source
    assert 'Get-ChildItem -Path $CandidateStatic -Recurse -File -Force' in source
    assert "Source export: $SourceExport" not in source


def test_hotfix_packager_normalizes_generator_pages_before_immutable_source_overlay() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    normalize = 'python3 ./scripts/apply-alex-design-system-v2.py --web-root $WebRoot'
    search_overlay = 'Copy-Item $SearchSource $SearchTarget -Force'
    overlay = '$CandidateSourceFiles | Copy-Item -Destination $ReleaseSources -Force'
    assert source.count(normalize) == 1
    assert source.index(normalize) < source.index(search_overlay) < source.index(overlay)


def test_release_cache_bust_preserves_immutable_source_detail_candidate_html() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert '$IsImmutableSourceDetail = $_.DirectoryName -eq $ReleaseSources' in source
    assert '$_.Name -like "tiktok-video-*.html"' in source
    assert "if (-not $IsImmutableSourceDetail)" in source
