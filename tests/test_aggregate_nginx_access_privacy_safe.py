from __future__ import annotations

import csv
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "aggregate_nginx_access_privacy_safe.py"


def load_module():
    spec = importlib.util.spec_from_file_location("privacy_safe_nginx_aggregate", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_aggregate_discards_queries_referrers_and_user_agents(tmp_path: Path) -> None:
    module = load_module()
    log = tmp_path / "access.log"
    log.write_text(
        '\n'.join(
            (
                '198.51.100.24 - - [20/Jul/2026:12:00:00 +0000] "GET /knowledge/topics/content-repurposing.html?q=private+query HTTP/1.1" 200 123 "https://www.google.com/search?q=secret" "Mozilla/5.0"',
                '198.51.100.88 - - [20/Jul/2026:12:01:00 +0000] "GET /pricing/?offer=diagnostic HTTP/1.1" 404 123 "https://www.perplexity.ai/search?q=hidden" "ExampleBot/1.0"',
            )
        ) + '\n',
        encoding="utf-8",
    )
    output = tmp_path / "aggregate.csv"

    counts, parsed, rejected = module.aggregate([log])
    module.write_counts(output, counts)

    assert (parsed, rejected) == (2, 0)
    rows = list(csv.DictReader(output.open(encoding="utf-8")))
    assert rows == [
        {
            "date_utc": "2026-07-20",
            "site_segment": "base",
            "route_family": "topics",
            "method_class": "page_like",
            "status_class": "2xx",
            "user_agent_class": "nonbot_heuristic",
            "referrer_class": "search",
            "requests": "1",
        },
        {
            "date_utc": "2026-07-20",
            "site_segment": "personal",
            "route_family": "pricing",
            "method_class": "page_like",
            "status_class": "4xx",
            "user_agent_class": "bot_heuristic",
            "referrer_class": "ai_assistant",
            "requests": "1",
        },
    ]
    serialized = output.read_text(encoding="utf-8")
    for forbidden in ("198.51.100.", "private+query", "secret", "hidden", "Mozilla", "ExampleBot", "?offer="):
        assert forbidden not in serialized
