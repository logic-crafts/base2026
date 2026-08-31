from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "base2026_editorial_catalog_builder", ROOT / "scripts/build-base2026-cloudflare-release.py"
)
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


def test_catalog_and_render_keep_existing_routes_and_script_safe_json() -> None:
    records = builder._editorial_catalog()
    assert len(records) == 2
    assert len({record["path"] for record in records}) == 2
    rendered = builder._render_editorial_index("<header>shell</header>", "<footer>shell</footer>").decode()
    assert rendered.count("<h1>") == 1
    assert rendered.count("<header>shell</header>") == 1
    assert rendered.count("<footer>shell</footer>") == 1
    assert "AI-generated editorial illustration" in rendered
    assert '"url": "https://base2026.dev/blog"' in rendered
    hostile = copy.deepcopy(records[0])
    hostile["title"] = 'An <img src=x onerror="oops"> & evidence note'
    card = builder._editorial_card(hostile, featured=True)
    assert '<img src=x' not in card
    assert "&lt;img" in card
    assert "&quot;oops&quot;" in card


@pytest.mark.parametrize("mutation", [
    lambda rows: rows[0].update(path="javascript:alert(1)"),
    lambda rows: rows[0].update(path="//example.com/post"),
    lambda rows: rows[0].update(id='x" onclick="bad'),
    lambda rows: rows[0].update(published_at="2026-02-30"),
    lambda rows: rows[0].update(updated_at="2020-01-01"),
    lambda rows: rows[0].update(author="Unreviewed byline"),
    lambda rows: rows[0]["hero"].update(path="/private/image.png"),
    lambda rows: rows[0]["hero"].update(ai_generated=False),
    lambda rows: rows.append(copy.deepcopy(rows[0])),
    lambda rows: rows[0].update(unapproved="field"),
])
def test_catalog_rejects_unsafe_or_inconsistent_metadata(tmp_path: Path, mutation) -> None:
    rows = builder._editorial_catalog()
    mutation(rows)
    candidate = tmp_path / "catalog.json"
    candidate.write_text(json.dumps(rows), encoding="utf-8")
    with pytest.raises(builder.ReleaseBuildError):
        builder._editorial_catalog(candidate)
