from __future__ import annotations

import argparse
import json
from pathlib import Path

from base2026_ai_recommends_core import build_public_context, read_json, validate_payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Base2026 AI Recommends Solution records against public source evidence and the local page-value contract.")
    parser.add_argument("--input", type=Path, default=Path("data/base2026_ai_recommends_solutions_pilot.json"))
    parser.add_argument("--data-root", type=Path, default=Path("public-data/tiktok"))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    payload = read_json(args.input)
    context = build_public_context(args.data_root)
    report = validate_payload(payload, context)
    public_report = {key: value for key, value in report.items() if key != "_internal_reports"}
    rendered = json.dumps(public_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
