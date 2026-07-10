from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

GREEN_CLUSTERS = {
    "google-business-profile-visibility-audit",
    "search-console-high-impression-low-ctr",
    "measure-ai-search-visibility",
    "answer-ready-service-page-checklist",
    "content-refresh-prioritization",
}

CLUSTERS: dict[str, dict[str, Any]] = {
    "google-business-profile-visibility-audit": {
        "label": "Google Business Profile visibility",
        "patterns": [(5, r"\bgoogle business profile\b"), (4, r"\b(?:gmb|map pack|local pack)\b"), (2, r"\bgoogle maps\b")],
    },
    "search-console-high-impression-low-ctr": {
        "label": "Search Console CTR workflow",
        "patterns": [(5, r"\bgoogle search console\b"), (4, r"\bsearch console\b"), (2, r"\b(?:click.through rate|\bctr\b|high impressions?)\b")],
        "requires": r"\b(?:search console|click.through rate|\bctr\b|impressions?)\b",
    },
    "measure-ai-search-visibility": {
        "label": "AI search measurement",
        "patterns": [(5, r"\b(?:ai overviews?|ai search|generative ai|answer engines?)\b"), (3, r"\b(?:chatgpt|perplexity|gemini|llm)\b"), (2, r"\b(?:citation|referral|analytics|visibility|traffic|ranking)\b")],
        "requires": r"\b(?:ai overviews?|ai search|generative ai|chatgpt|perplexity|gemini|llm|answer engines?)\b.*\b(?:search|traffic|visibility|citation|ranking|referral|analytics)\b|\b(?:search|traffic|visibility|citation|ranking|referral|analytics)\b.*\b(?:ai overviews?|ai search|generative ai|chatgpt|perplexity|gemini|llm|answer engines?)\b",
    },
    "answer-ready-service-page-checklist": {
        "label": "Answer-ready service pages",
        "patterns": [(5, r"\b(?:service pages?|answer.ready)\b"), (4, r"\b(?:structured data|schema markup|semantic triples?|entity seo)\b"), (2, r"\b(?:landing pages?|faq)\b")],
    },
    "content-refresh-prioritization": {
        "label": "Content refresh prioritization",
        "patterns": [(5, r"\b(?:content refresh|content decay|declining content)\b"), (4, r"\b(?:outdated content|refresh old|update old|republish)\b"), (2, r"\bfreshness\b")],
    },
    "internal-linking-site-architecture": {
        "label": "Internal linking and site architecture",
        "patterns": [(5, r"\b(?:internal links?|site architecture|orphan pages?)\b"), (3, r"\b(?:topic hubs?|anchor text)\b"), (2, r"\bsitemaps?\b")],
    },
    "local-reviews-citations": {
        "label": "Local reviews and citations",
        "patterns": [(5, r"\b(?:google reviews?|local citations?|local seo)\b"), (3, r"\b(?:customer reviews?|\bnap\b|reputation)\b")],
    },
    "technical-indexation": {
        "label": "Technical SEO and indexation",
        "patterns": [(5, r"\b(?:robots\.txt|canonicals?|core web vitals|javascript seo|technical seo)\b"), (3, r"\b(?:crawlability|indexation|page speed)\b"), (2, r"\b(?:crawling|indexing)\b")],
    },
    "keyword-content-strategy": {
        "label": "Keyword and content strategy",
        "patterns": [(5, r"\b(?:keyword research|search intent|topical authority|content gaps?|programmatic seo)\b"), (3, r"\b(?:search volume|content strategy)\b")],
    },
    "link-authority-pr": {
        "label": "Link authority and digital PR",
        "patterns": [(5, r"\b(?:digital pr|link building)\b"), (4, r"\b(?:backlinks?|guest posts?)\b"), (2, r"\b(?:journalists?|domain authority)\b")],
    },
    "ai-agent-workflows": {
        "label": "AI agent workflows",
        "patterns": [(5, r"\bai agents?\b"), (4, r"\b(?:automation workflows?|locali[sz]ation agent)\b"), (2, r"\b(?:automation|automate|prompts?|workflows?)\b")],
    },
    "social-content-distribution": {
        "label": "Social content and distribution",
        "patterns": [(5, r"\b(?:social media|short.form video|video content)\b"), (3, r"\b(?:tiktok|instagram|linkedin|content hooks?)\b")],
    },
    "conversion-offer-ux": {
        "label": "Conversion, offer and UX",
        "patterns": [(5, r"\b(?:conversion rate|pricing page|sales funnel|lead generation)\b"), (3, r"\b(?:\bcta\b|checkout|\bcro\b)\b"), (2, r"\boffer\b")],
    },
    "email-lifecycle": {
        "label": "Email lifecycle",
        "patterns": [(5, r"\b(?:email marketing|email list|deliverability|cold email)\b"), (3, r"\bnewsletter\b")],
    },
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def score_clusters(text: str) -> list[tuple[str, int]]:
    normalized = " ".join(text.lower().split())
    results: list[tuple[str, int]] = []
    for slug, config in CLUSTERS.items():
        requirement = config.get("requires")
        if requirement and not re.search(requirement, normalized, re.IGNORECASE):
            continue
        score = sum(weight for weight, pattern in config["patterns"] if re.search(pattern, normalized, re.IGNORECASE))
        if score >= 4:
            results.append((slug, score))
    return sorted(results, key=lambda row: (-row[1], 0 if row[0] in GREEN_CLUSTERS else 1, row[0]))


def source_text(source_id: str, passages_by_source: dict[str, list[dict[str, Any]]], source_by_id: dict[str, dict[str, Any]]) -> str:
    source = source_by_id.get(source_id, {})
    parts = [str(source.get("title") or ""), str(source.get("excerpt") or "")]
    for passage in passages_by_source.get(source_id, []):
        parts.extend([str(passage.get("title") or ""), str(passage.get("body") or "")])
    return " ".join(parts)


def priority_score(row: dict[str, Any], lane: str, text: str, today: date) -> int:
    score = 10
    score += 50 if lane == "green_solution_cluster_review" else 25 if lane == "future_cluster_review" else 5
    published = str(row.get("published_at") or "")[:10]
    try:
        age = (today - date.fromisoformat(published)).days
        score += 20 if age <= 30 else 10 if age <= 90 else 0
    except ValueError:
        pass
    length = len(text)
    score += 10 if 200 <= length <= 4000 else 5 if length > 0 else 0
    if "local_not_live" in row.get("reasons", []):
        score += 5
    return min(score, 100)


def main() -> int:
    parser = argparse.ArgumentParser(description="Portfolio-triage Base2026 needs-insight sources without mutating KB data.")
    parser.add_argument("--queue", type=Path, default=Path(".planning/insight-repair/needs-insight-latest.jsonl"))
    parser.add_argument("--data-root", type=Path, default=Path("public-data/tiktok"))
    parser.add_argument("--repair-summary", type=Path, default=Path(".planning/insight-repair/repair-summary-latest.json"))
    parser.add_argument("--out-jsonl", type=Path, required=True)
    parser.add_argument("--out-summary", type=Path, required=True)
    parser.add_argument("--out-markdown", type=Path, required=True)
    args = parser.parse_args()

    queue = read_jsonl(args.queue)
    sources = read_jsonl(args.data_root / "source_records.jsonl")
    passages = read_jsonl(args.data_root / "passages.jsonl")
    insights = read_jsonl(args.data_root / "insight_cards.jsonl")
    source_by_id = {row["source_id"]: row for row in sources}
    passages_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for passage in passages:
        passages_by_source[passage["source_id"]].append(passage)

    support_sources: dict[str, set[str]] = defaultdict(set)
    support_creators: dict[str, set[str]] = defaultdict(set)
    for insight in insights:
        if not insight.get("public") or insight.get("needs_review"):
            continue
        text = " ".join(str(insight.get(key) or "") for key in ("topic", "claim_text", "actionable_takeaway", "tags"))
        matches = score_clusters(text)
        if matches:
            cluster = matches[0][0]
            support_sources[cluster].add(str(insight.get("source_id") or ""))
            support_creators[cluster].add(str(insight.get("creator_handle") or ""))

    today = datetime.now(timezone.utc).date()
    rows: list[dict[str, Any]] = []
    for item in queue:
        sid = str(item.get("source_id") or "")
        text = source_text(sid, passages_by_source, source_by_id)
        matches = score_clusters(text)
        cluster = matches[0][0] if matches else ""
        if not text.strip():
            lane = "manual_review_required"
            action = "recover_source_text_before_editorial_judgment"
        elif cluster in GREEN_CLUSTERS:
            lane = "green_solution_cluster_review"
            action = "sol_review_for_solution_evidence_source_only_or_reviewed_no_card"
        elif cluster:
            lane = "future_cluster_review"
            action = "sol_review_for_future_solution_source_only_or_reviewed_no_card"
        else:
            lane = "source_only_review"
            action = "sol_review_for_source_only_or_reviewed_no_card"
        score = priority_score(item, lane, text, today)
        tier = "P1" if score >= 75 else "P2" if score >= 50 else "P3"
        source = source_by_id.get(sid, {})
        rows.append({
            **item,
            "portfolio_lane": lane,
            "candidate_cluster": cluster or None,
            "candidate_cluster_label": CLUSTERS.get(cluster, {}).get("label") if cluster else None,
            "cluster_match_score": matches[0][1] if matches else 0,
            "alternative_clusters": [{"slug": slug, "score": value} for slug, value in matches[1:4]],
            "roi_score": score,
            "roi_tier": tier,
            "editorial_next_action": action,
            "automatic_publication_allowed": False,
            "source_title": source.get("title") or "",
            "source_text_chars": len(text),
        })

    rows.sort(key=lambda row: ({"P1": 0, "P2": 1, "P3": 2}[row["roi_tier"]], -row["roi_score"], str(row.get("published_at") or ""), row["source_id"]))
    lane_counts = Counter(row["portfolio_lane"] for row in rows)
    cluster_counts = Counter(row["candidate_cluster"] or "unclassified-source-only" for row in rows)
    tier_counts = Counter(row["roi_tier"] for row in rows)
    repair_summary = json.loads(args.repair_summary.read_text(encoding="utf-8"))
    cluster_ledger = []
    for slug, config in CLUSTERS.items():
        status = "green_release_candidate" if slug in GREEN_CLUSTERS else "amber_requires_product_contract"
        cluster_ledger.append({
            "slug": slug,
            "label": config["label"],
            "status": status,
            "needs_insight_backlog": cluster_counts.get(slug, 0),
            "reviewed_public_support_sources": len(support_sources.get(slug, set())),
            "reviewed_public_support_creators": len({x for x in support_creators.get(slug, set()) if x}),
        })
    cluster_ledger.sort(key=lambda row: (0 if row["status"].startswith("green") else 1, -row["needs_insight_backlog"], row["slug"]))

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "queue_path": str(args.queue),
        "queue_count": len(queue),
        "portfolio_row_count": len(rows),
        "all_queue_rows_classified": len(rows) == len(queue),
        "lane_counts": dict(sorted(lane_counts.items())),
        "tier_counts": dict(sorted(tier_counts.items())),
        "cluster_counts": dict(sorted(cluster_counts.items())),
        "existing_reviewed_no_card_sources": repair_summary.get("insight", {}).get("reviewed_no_card_sources", 0),
        "automatic_editorial_decisions": 0,
        "automatic_publications": 0,
        "cluster_ledger": cluster_ledger,
        "decision": "Keyword and corpus support select an editorial queue only. Sol/editorial review must choose solution contribution, source-only intelligence, reviewed-no-card, or source review.",
    }

    args.out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    args.out_jsonl.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    args.out_summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = [
        "# Base2026 needs-insight portfolio ledger",
        "",
        f"Generated: {summary['generated_at']}",
        f"Queue rows: {len(queue)}; classified: {len(rows)}; automatic editorial decisions: 0; automatic publications: 0.",
        "",
        "## Portfolio lanes",
        "",
    ]
    md.extend(f"- `{lane}`: {count}" for lane, count in sorted(lane_counts.items()))
    md.extend(["", "## Cluster readiness", "", "| Cluster | Status | Needs-insight backlog | Reviewed public sources | Creators |", "| --- | --- | ---: | ---: | ---: |"])
    for row in cluster_ledger:
        md.append(f"| {row['label']} | `{row['status']}` | {row['needs_insight_backlog']} | {row['reviewed_public_support_sources']} | {row['reviewed_public_support_creators']} |")
    md.extend([
        "",
        "## Guardrail",
        "",
        "This ledger does not create or promote claims. Keyword matching only chooses an editorial queue. Every row still requires semantic review, and `reviewed-no-card` is a valid outcome.",
    ])
    args.out_markdown.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["all_queue_rows_classified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
