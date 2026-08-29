from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dataset_template_has_truthful_machine_and_human_contracts() -> None:
    html = (ROOT / "templates" / "base2026-dataset.html").read_text(encoding="utf-8")
    payloads = re.findall(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>', html, re.DOTALL
    )
    assert len(payloads) == 1
    schema = json.loads(payloads[0])
    dataset = next(item for item in schema["@graph"] if item["@type"] == "Dataset")
    assert dataset["isAccessibleForFree"] is True
    assert dataset["url"] == "https://base2026.dev/dataset"
    assert len(dataset["distribution"]) == 4
    assert all(item["contentUrl"].startswith("https://base2026.dev/static/") for item in dataset["distribution"])
    assert "Raw media" not in html
    assert "raw media" in html
    assert "full private transcripts" in html
    assert "creator/source rights" not in html


def test_public_dataset_catalog_matches_the_landing_page_contract() -> None:
    catalog = json.loads(
        (ROOT / "examples" / "base2026-public-dataset-catalog.json").read_text(
            encoding="utf-8"
        )
    )
    assert catalog["schema"] == "base2026.public-dataset-catalog/v1"
    assert catalog["landing_page"] == "https://base2026.dev/dataset"
    assert catalog["is_accessible_for_free"] is True
    assert len(catalog["distributions"]) == 4
    assert catalog["public_boundary"]["full_private_transcripts"] is False


def test_quickstart_uses_only_the_public_read_only_index() -> None:
    script = (ROOT / "examples" / "query_public_evidence.py").read_text(encoding="utf-8")
    assert "https://base2026.dev/api/search/multi-search" in script
    assert 'INDEX = "base2026_public_tiktok"' in script
    assert "Authorization" not in script
    assert "api_key" not in script.casefold()
    assert "POST" in script
