from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "check-cloudflare-public-artifact-policy.py"
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("check_cloudflare_public_artifact_policy", MODULE_PATH)
assert SPEC and SPEC.loader
gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gate
SPEC.loader.exec_module(gate)


def test_artifact_gate_accepts_only_publishable_insight_rows(tmp_path: Path) -> None:
    path = tmp_path / "insight_cards.jsonl"
    public = {
        "id": "insight:public",
        "public": True,
        "needs_review": False,
        "public_policy": "reviewed_insight",
    }
    path.write_text(json.dumps(public) + "\n", encoding="utf-8")
    assert gate.count_jsonl(path) == 1

    held = dict(public, public=False, needs_review=True, public_policy="needs_review")
    path.write_text(json.dumps(held) + "\n", encoding="utf-8")
    with pytest.raises(gate.ArtifactGateError, match="is not public"):
        gate.count_jsonl(path)


def test_artifact_gate_rejects_public_review_contradiction(tmp_path: Path) -> None:
    path = tmp_path / "insight_cards.jsonl"
    contradictory = {
        "id": "insight:contradictory",
        "public": True,
        "needs_review": True,
        "public_policy": "reviewed_insight",
    }
    path.write_text(json.dumps(contradictory) + "\n", encoding="utf-8")
    with pytest.raises(gate.ArtifactGateError, match="still needs review"):
        gate.count_jsonl(path)
