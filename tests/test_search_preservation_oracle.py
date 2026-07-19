from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify-base2026-search-preservation.py"


def run_oracle(tmp_path: Path, staged_html: str) -> tuple[subprocess.CompletedProcess[str], dict]:
    source = tmp_path / "source"
    staged = tmp_path / "staged"
    source.mkdir()
    staged.mkdir()
    (source / "index.html").write_text('<script src="./app.js?v=old"></script><main>Search</main>')
    (staged / "index.html").write_text(staged_html)
    (source / "app.js").write_text("window.search = true;\n")
    (staged / "app.js").write_text("window.search = true;\n")
    contract = tmp_path / "contract.json"
    contract.write_text(
        json.dumps({"schema": "base2026.search-protected-files/v1", "files": ["index.html", "app.js"]})
    )
    report = tmp_path / "report.json"
    result = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--contract",
            str(contract),
            "--source-root",
            str(source),
            "--staged-root",
            str(staged),
            "--report",
            str(report),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return result, json.loads(report.read_text())


def test_search_oracle_allows_only_html_cache_bust_value_change(tmp_path: Path) -> None:
    result, report = run_oracle(
        tmp_path,
        '<script src="./app.js?v=new-release"></script><main>Search</main>',
    )

    assert result.returncode == 0
    assert report["status"] == "PASS"
    assert report["source_oracle_sha256"] == report["staged_oracle_sha256"]


def test_search_oracle_rejects_semantic_html_change(tmp_path: Path) -> None:
    result, report = run_oracle(
        tmp_path,
        '<script src="./app.js?v=new-release"></script><main>Changed</main>',
    )

    assert result.returncode == 1
    assert report["status"] == "FAIL"
    assert report["errors"] == ["semantic_mismatch:index.html"]
