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
