from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "refresh-source-detail-route-inventory.py"


def load_module():
    spec = importlib.util.spec_from_file_location("refresh_source_detail_inventory", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_accepted_candidate_manifest_can_seed_current_ledger_refresh(tmp_path: Path) -> None:
    module = load_module()
    manifest = tmp_path / "candidate-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema": "base2026.source-detail-v2-full-candidate/v1",
                "rendered": [
                    {"route": "sources/tiktok-video-100.html", "admission_state": "normal_public_card"},
                    {
                        "route": "sources/tiktok-video-200.html",
                        "admission_state": "provenance_archive_noindex",
                    },
                ],
                "future_private_not_emitted": ["sources/tiktok-video-300.html"],
            }
        ),
        encoding="utf-8",
    )
    rows = module.read_base_rows(manifest)
    assert [(row["route"], row["expected_status"]) for row in rows] == [
        ("sources/tiktok-video-100.html", 200),
        ("sources/tiktok-video-200.html", 200),
        ("sources/tiktok-video-300.html", 404),
    ]
