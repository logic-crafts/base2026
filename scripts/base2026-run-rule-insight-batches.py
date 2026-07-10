#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLANNING = ROOT / ".planning" / "insight-repair"
DB = ROOT / "12_knowledge-base" / "indexes" / "kb.sqlite"
QUEUE = PLANNING / "needs-insight-latest.jsonl"
SUMMARY = PLANNING / "repair-summary-latest.json"
PREFIX_RE = re.compile(r"repair-gpt55-20260707-(\d+)$")


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if check and proc.returncode != 0:
        print(json.dumps({
            "ok": False,
            "failed_cmd": cmd,
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-5000:],
            "stderr_tail": proc.stderr[-5000:],
        }, ensure_ascii=False, indent=2))
        raise SystemExit(proc.returncode)
    return proc


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def max_repair_number() -> int:
    max_n = 0
    con = sqlite3.connect(DB)
    try:
        for (claim_id,) in con.execute("select claim_id from claims where claim_id like 'repair-gpt55-20260707-%'"):
            m = PREFIX_RE.match(str(claim_id or ""))
            if m:
                max_n = max(max_n, int(m.group(1)))
    finally:
        con.close()
    return max_n


def queue_refresh() -> dict[str, Any]:
    run(["python3", "scripts/base2026-tiktok-repair-queue.py", "--write"])
    return load_json(SUMMARY)


def claim_ids_for_range(start: int, selected: int) -> list[str]:
    return [f"repair-gpt55-20260707-{i:03d}" for i in range(start, start + selected)]


def export_and_validate() -> None:
    run(["python3", "scripts/export-public-tiktok.py"])
    run(["python3", "scripts/check-public-export-policy.py", "public-data/tiktok"])
    run(["python3", "scripts/validate-public-release-contract.py"])


def main() -> int:
    ap = argparse.ArgumentParser(description="Autonomous safe loop for Base2026 rule-assisted TikTok insight repair batches.")
    ap.add_argument("--start-batch", type=int, default=9)
    ap.add_argument("--max-batches", type=int, default=20)
    ap.add_argument("--target", type=int, default=48)
    ap.add_argument("--scan-limit", type=int, default=1400)
    ap.add_argument("--min-selected", type=int, default=1)
    args = ap.parse_args()

    run_summary: list[dict[str, Any]] = []
    summary_before = queue_refresh()
    batch_no = args.start_batch
    for i in range(args.max_batches):
        summary = load_json(SUMMARY)
        queued_before = int(summary["insight"]["queued_needs_insight"])
        if queued_before <= 0:
            break
        start = max_repair_number() + 1
        label = f"batch{batch_no}-auto-rule"
        cand = PLANNING / f"claim-candidates-gpt55-{label}-{args.target}-20260707.jsonl"
        gen_report = PLANNING / f"claim-candidates-gpt55-{label}-{args.target}-20260707.report.json"
        precheck = PLANNING / f"claim-candidates-gpt55-{label}-{args.target}-20260707.pre-strict-check.json"
        strictcheck = PLANNING / f"claim-candidates-gpt55-{label}-{args.target}-20260707.strict-check.json"
        review_json = PLANNING / f"pending-review-{label}-{args.target}-20260707.json"
        review_md = PLANNING / f"pending-review-{label}-{args.target}-20260707.md"
        ids_path = PLANNING / f"{label}-promotion-ids.txt"

        gen = run([
            "python3", "scripts/base2026-generate-rule-insight-batch.py",
            "--queue", str(QUEUE),
            "--batch", label,
            "--start-number", str(start),
            "--target", str(args.target),
            "--scan-limit", str(args.scan_limit),
            "--out", str(cand),
            "--report", str(gen_report),
        ], check=False)
        if gen.returncode != 0 and not cand.exists():
            print(json.dumps({"ok": False, "stage": "generate", "stdout": gen.stdout[-2000:], "stderr": gen.stderr[-2000:]}, ensure_ascii=False, indent=2))
            return gen.returncode
        gen_payload = load_json(gen_report)
        selected = int(gen_payload.get("selected") or 0)
        if selected < args.min_selected:
            run_summary.append({"batch": label, "selected": selected, "queued_before": queued_before, "status": "no_more_generator_matches"})
            break

        # Strict pre-check: exits nonzero on any failure.
        run(["python3", "scripts/base2026-check-insight-batch.py", "--candidates", str(cand), "--queue", str(QUEUE), "--out-json", str(precheck)])
        pre = load_json(precheck)
        if not pre.get("ok") or int(pre.get("accepted") or 0) != selected:
            print(json.dumps({"ok": False, "stage": "precheck_mismatch", "batch": label, "precheck": pre}, ensure_ascii=False, indent=2))
            return 2

        run(["python3", "scripts/base2026-import-claim-candidates.py", "--input", str(cand), "--default-archive"])
        run(["python3", "scripts/base2026-import-claim-candidates.py", "--input", str(cand), "--default-archive", "--apply"])
        run(["python3", "scripts/base2026-review-insight-candidates.py", "--out-json", str(review_json), "--out-md", str(review_md)])
        run(["python3", "scripts/base2026-check-insight-batch.py", "--candidates", str(cand), "--queue", str(QUEUE), "--review-report", str(review_json), "--out-json", str(strictcheck)])
        strict = load_json(strictcheck)
        if not strict.get("ok") or int(strict.get("accepted") or 0) != selected:
            print(json.dumps({"ok": False, "stage": "strict_review_mismatch", "batch": label, "strict": strict}, ensure_ascii=False, indent=2))
            return 3

        review = load_json(review_json)
        expected_ids = set(claim_ids_for_range(start, selected))
        rows = [r for r in review.get("candidates", []) if r.get("claim_id") in expected_ids]
        ids = [
            r["claim_id"] for r in rows
            if r.get("recommended_status") == "promotion_candidate"
            and r.get("evidence_match_method") == "exact"
            and not r.get("soft_warnings")
            and not r.get("hard_failures")
        ]
        ids_path.write_text(",".join(ids), encoding="utf-8")
        if len(ids) != selected:
            bad = [r for r in rows if r.get("claim_id") not in set(ids)]
            print(json.dumps({"ok": False, "stage": "review_selection_mismatch", "batch": label, "selected": selected, "ids": len(ids), "bad": bad}, ensure_ascii=False, indent=2))
            return 4

        ids_arg = ",".join(ids)
        run(["python3", "scripts/base2026-promote-insight-candidates.py", "--review-report", str(review_json), "--claim-ids", ids_arg])
        run(["python3", "scripts/base2026-promote-insight-candidates.py", "--review-report", str(review_json), "--claim-ids", ids_arg, "--apply"])
        export_and_validate()
        summary_after = queue_refresh()
        queued_after = int(summary_after["insight"]["queued_needs_insight"])
        run_summary.append({
            "batch": label,
            "start": start,
            "selected": selected,
            "queued_before": queued_before,
            "queued_after": queued_after,
            "sources_without_any_insight": summary_after["insight"].get("sources_without_any_insight"),
            "public_insight_cards": summary_after["insight"].get("sources_with_public_insight"),
            "rule_counts": gen_payload.get("rule_counts"),
            "status": "applied",
        })
        batch_no += 1

    final_summary = load_json(SUMMARY)
    print(json.dumps({
        "ok": True,
        "started_queued_needs_insight": summary_before["insight"].get("queued_needs_insight"),
        "final_queued_needs_insight": final_summary["insight"].get("queued_needs_insight"),
        "final_sources_without_any_insight": final_summary["insight"].get("sources_without_any_insight"),
        "final_sources_without_public_insight": final_summary["insight"].get("sources_without_public_insight"),
        "batches": run_summary,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
