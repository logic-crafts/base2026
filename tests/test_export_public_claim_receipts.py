import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "export-public-claim-receipts.py"
SPEC = importlib.util.spec_from_file_location("export_public_claim_receipts", SCRIPT)
exporter = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(exporter)


def readback():
    receipts = []
    for index in range(10):
        rank = index + 1
        handle = f"creator{index % 5}"
        video_id = str(7999999999999990000 + index)
        projection_id = format(index + 1, "x") * 40
        card_id = format(index + 3, "x") * 40
        search_id = format(index + 5, "x") * 40
        date = f"2026-08-{19 - index:02d}"
        receipt = {
            "schema_version": exporter.RECEIPT_SCHEMA,
            "receipt_id": "0" * 64,
            "canary_id": exporter.CANARY_ID,
            "selection_rank": rank,
            "source_id": f"tiktok:{handle}:{video_id}",
            "projection_id": projection_id,
            "card_id": card_id,
            "search_id": search_id,
            "card_ordinal": 0,
            "creator_handle": f"@{handle}",
            "creator_display_name": "",
            "creator_url": f"https://www.tiktok.com/@{handle}",
            "original_url": f"https://www.tiktok.com/@{handle}/video/{video_id}",
            "video_id": video_id,
            "base2026_url": f"https://base2026.dev/sources/tiktok-video-{video_id}",
            "published_at": date,
            "published_date": date,
            "claim_text": f"Internal-linking claim {index} is bounded and source-backed.",
            "suggested_action": f"Apply internal-linking action {index} with the source citation.",
            "topic_label": "internal-linking",
            "evidence_excerpt": f"The public source provides internal-linking evidence example {index}.",
            "evidence_start_seconds": 1,
            "evidence_end_seconds": 8,
            "public_projection_receipt_sha256": format(index + 7, "x") * 64,
            "policy_version": exporter.POLICY_VERSION,
        }
        immutable = dict(receipt)
        immutable.pop("receipt_id")
        receipt["receipt_id"] = exporter.sha256_text(exporter.canonical_json(immutable))
        receipts.append(receipt)
    ledger = exporter.sha256_text("".join(f"{exporter.canonical_json(item)}\n" for item in receipts))
    return {
        "schema_version": exporter.LEDGER_SCHEMA,
        "canary_id": exporter.CANARY_ID,
        "topic": exporter.TOPIC,
        "policy_version": exporter.POLICY_VERSION,
        "count": 10,
        "ledger_sha256": ledger,
        "generated_at": "2026-09-01T00:00:00.000Z",
        "receipts": receipts,
    }


def test_export_is_deterministic_and_matches_public_manifest_contract(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    result = exporter.export_readback(readback(), first)
    exporter.export_readback(readback(), second)
    assert (first / "claim_receipts.jsonl").read_bytes() == (second / "claim_receipts.jsonl").read_bytes()
    assert (first / "claim_receipts_manifest.json").read_bytes() == (second / "claim_receipts_manifest.json").read_bytes()
    manifest = json.loads((first / "claim_receipts_manifest.json").read_text())
    rows = (first / "claim_receipts.jsonl").read_text()
    assert manifest["ledger_sha256"] == result["ledger_sha256"]
    assert exporter.validate_readback(readback())[1] == manifest["ledger_sha256"]

    contract_path = ROOT / "scripts" / "public_manifest_contract.py"
    contract_spec = importlib.util.spec_from_file_location("public_manifest_contract", contract_path)
    contract = importlib.util.module_from_spec(contract_spec)
    assert contract_spec and contract_spec.loader
    contract_spec.loader.exec_module(contract)
    assert contract.validate_claim_receipt_sidecars(rows, manifest) == []


def test_export_rejects_partial_private_tampered_and_overwrite_inputs(tmp_path):
    payload = readback()
    with pytest.raises(exporter.ExportError):
        partial = dict(payload)
        partial["count"] = 9
        partial["receipts"] = partial["receipts"][:9]
        exporter.validate_readback(partial)

    with pytest.raises(exporter.ExportError):
        private = json.loads(json.dumps(payload))
        private["receipts"][0]["private_import_hash"] = "secret"
        exporter.validate_readback(private)

    with pytest.raises(exporter.ExportError):
        tampered = json.loads(json.dumps(payload))
        tampered["receipts"][0]["claim_text"] = "A changed public claim that is not in the digest."
        exporter.validate_readback(tampered)

    output = tmp_path / "output"
    exporter.export_readback(payload, output)
    with pytest.raises(exporter.ExportError):
        exporter.export_readback(payload, output)
