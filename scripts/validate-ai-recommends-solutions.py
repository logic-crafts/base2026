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
    required_public_files = [args.data_root / "source_records.jsonl", args.data_root / "insight_cards.jsonl"]
    missing_public_files = [path.as_posix() for path in required_public_files if not path.is_file()]
    if missing_public_files:
        public_report = {
            "contract_version": payload.get("contract_version"),
            "errors": [
                "public evidence export is missing; pass --data-root for a verified release export",
                *[f"missing required public evidence file: {path}" for path in missing_public_files],
            ],
            "indexable_count": 0,
            "ok": False,
            "solution_count": len(payload.get("solutions") or []),
            "solutions": [],
        }
        rendered = json.dumps(public_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 2

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
