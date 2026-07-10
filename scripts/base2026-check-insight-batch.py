#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUEUE = ROOT / ".planning/insight-repair/needs-insight-latest.jsonl"
DEFAULT_PASSAGES = ROOT / "public-data/tiktok/passages.jsonl"
DEFAULT_SOURCE_RECORDS = ROOT / "public-data/tiktok/source_records.jsonl"
DEFAULT_INSIGHTS = ROOT / "public-data/tiktok/insight_cards.jsonl"

GENERIC_RE = re.compile(
    r"\b("
    r"leverage|utilize|unlock|game[- ]changer|boost your seo|explore the implications|"
    r"optimi[sz]e content|ai matters|seo is important|assess how|enhance your visibility|"
    r"drive growth|move the needle|thought leadership|best practices"
    r")\b",
    re.I,
)
ACTION_VERB_RE = re.compile(
    r"\b(audit|check|add|map|report|build|compare|update|rewrite|create|track|measure|set up|"
    r"record|extract|publish|document|flag|route|monitor|inventory|interview|test|separate|"
    r"require|use|choose|treat|start|keep|improve|run|define|allow|position|snapshot|design|decide|replace|segment)\b",
    re.I,
)
WEAK_EVIDENCE_RE = re.compile(
    r"^(?:"
    r"Do you want more followers on Instagram\??|"
    r"All you have to do is go to semrush\.com\.?|"
    r"Adobe is buying Semrush|"
    r"I do SEO audits for people all over the world\.?|"
    r"The white Spark local ranking grid software\.?|"
    r"The 2026 Local Ranking factors report is finally here\.?|"
    r"It's not built on WordPress or Shopify\.?|"
    r"Coming in at number four is the new kid on the block|"
    r"AI is quickly changing how companies hire\.?"
    r")",
    re.I,
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        raise FileNotFoundError(path)
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{i}: invalid JSON: {exc}") from exc
        if not isinstance(obj, dict):
            raise ValueError(f"{path}:{i}: expected object")
        rows.append(obj)
    return rows


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def fail(failures: dict[str, list[str]], claim_id: str, reason: str) -> None:
    failures[claim_id].append(reason)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Strict Base2026 TikTok insight-card batch acceptance checker. No writes unless --out-json is provided."
    )
    ap.add_argument("--candidates", required=True, type=Path, help="Candidate JSONL generated for one bounded batch")
    ap.add_argument("--review-report", type=Path, help="JSON report from base2026-review-insight-candidates.py")
    ap.add_argument("--queue", type=Path, default=DEFAULT_QUEUE, help="needs-insight queue snapshot used when selecting this batch")
    ap.add_argument("--passages", type=Path, default=DEFAULT_PASSAGES)
    ap.add_argument("--source-records", type=Path, default=DEFAULT_SOURCE_RECORDS)
    ap.add_argument("--insights", type=Path, default=DEFAULT_INSIGHTS)
    ap.add_argument("--out-json", type=Path, help="Optional path to write the checker report")
    ap.add_argument("--max-per-source", type=int, default=2)
    args = ap.parse_args()

    candidates = read_jsonl(args.candidates)
    queue = read_jsonl(args.queue)
    passages = read_jsonl(args.passages)
    source_records = read_jsonl(args.source_records)
    insights = read_jsonl(args.insights) if args.insights.exists() else []

    queue_by_source = {r.get("source_id"): r for r in queue if r.get("source_id")}
    source_by_id = {r.get("source_id"): r for r in source_records if r.get("source_id")}
    passages_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for p in passages:
        if p.get("source_id"):
            passages_by_source[p["source_id"]].append(p)

    candidate_ids = {str(r.get("claim_id") or "") for r in candidates}
    existing_public_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for card in insights:
        if card.get("claim_id") in candidate_ids:
            continue
        if card.get("public") and card.get("source_id"):
            existing_public_by_source[card["source_id"]].append(card)

    review_by_claim: dict[str, dict[str, Any]] = {}
    if args.review_report:
        report = json.loads(args.review_report.read_text(encoding="utf-8"))
        for row in report.get("candidates", []):
            if row.get("claim_id"):
                review_by_claim[row["claim_id"]] = row

    failures: dict[str, list[str]] = defaultdict(list)
    warnings: dict[str, list[str]] = defaultdict(list)

    seen_claims = Counter(str(r.get("claim_id") or "") for r in candidates)
    seen_sources = Counter(str(r.get("source_id") or "") for r in candidates)
    seen_source_topics = Counter((str(r.get("source_id") or ""), norm(str(r.get("topic_label") or r.get("topic") or ""))) for r in candidates)

    for row in candidates:
        claim_id = str(row.get("claim_id") or "")
        source_id = str(row.get("source_id") or "")
        if not claim_id:
            claim_id = f"<missing-claim-id:{len(failures)+1}>"
            fail(failures, claim_id, "missing_claim_id")
        if seen_claims[claim_id] > 1:
            fail(failures, claim_id, "duplicate_claim_id_in_batch")
        if not source_id:
            fail(failures, claim_id, "missing_source_id")
            continue

        q = queue_by_source.get(source_id)
        if not q:
            fail(failures, claim_id, "source_not_in_queue_snapshot")
        else:
            if q.get("queue_type") != "needs_insight":
                fail(failures, claim_id, f"queue_type_not_needs_insight:{q.get('queue_type')}")
            if int(q.get("passage_count") or 0) <= 0:
                fail(failures, claim_id, "queue_passage_count_zero")
            reasons = {str(x) for x in (q.get("reasons") or [])}
            if "reviewed_no_card" in reasons:
                fail(failures, claim_id, "queue_reason_reviewed_no_card")
            if q.get("recommended_action") and q.get("recommended_action") != "extract_exact_evidence_insight_cards":
                warnings[claim_id].append(f"unexpected_recommended_action:{q.get('recommended_action')}")

        src = source_by_id.get(source_id)
        if not src:
            fail(failures, claim_id, "source_record_missing")
        elif src.get("full_transcript_public") is True:
            fail(failures, claim_id, "source_full_transcript_public_true")

        claim = str(row.get("claim_text") or "").strip()
        action = str(row.get("suggested_action") or "").strip()
        evidence = str(row.get("evidence_excerpt") or "").strip()
        topic = str(row.get("topic_label") or row.get("topic") or "").strip()

        if not 35 <= len(claim) <= 220:
            fail(failures, claim_id, f"claim_length_out_of_range:{len(claim)}")
        if not 35 <= len(action) <= 280:
            fail(failures, claim_id, f"action_length_out_of_range:{len(action)}")
        if not 55 <= len(evidence) <= 900:
            fail(failures, claim_id, f"evidence_length_out_of_range:{len(evidence)}")
        if WEAK_EVIDENCE_RE.search(evidence):
            fail(failures, claim_id, "weak_evidence_snippet")
        rule_key = str(row.get("rule_key") or "")
        semantic_patterns = {
            "bing_ai_search": r"Bing Webmaster|bing\.com|Microsoft|Copilot|Bringing Bing Back",
            "dmca_deindex": r"DMCA|de-?index|remove pages|copyright",
            "reddit_channel": r"Reddit|not on Facebook|not on Instagram|not on TikTok",
            "business_ops": r"CEO|customer|focused work|Pomodoro|five-year|six month|consistency|cumulative|silent killers|writing a page a day|something done",
            "social_content": r"social media|followers|Instagram Stories|Snapchat Stories|value",
            "google_ads_ops": r"Google Ads|remarketing|Keyword Planner|Ad Strength|Quality Score|EU political ads|mobile apps|campaign",
            "gbp_local": r"Google Business Profile|Google My Business|Google Maps|local rank|local ranking|ranking grid|service area|categories|appointment",
            "wordpress_seo": r"WordPress|Yoast|Rank Math|Wix|meta title|meta description|homepage|page title|title tag|HTML sitemap|page descriptions",
            "ai_visibility": r"\bAI\b|AI SEO|AI search|ChatGPT|Claude|Gemini|LLM|Sora|OpenAI|Notebook|Perplexity|model|models|AI model|AI models|custom GPT|knowledge work|AI assistant|Grok|grocypedia|Open Claw",
            "media_strategy": r"direct mail|email|open rate|media industry|YouTube is basically",
            "rank_reporting": r"visibility score|PDF report|keyword usage|rank|ranking|address|desktop|mobile",
            "reporting_reputation": r"review|reviews|reputation|name appears|search engine results|geogrid|fake one-star",
            "seo_tools": r"keyword|SEMrush|Wayback|disavow|backlinks|citation|AI SEO|Search Console|SEO|crawl stats|unlinked brand",
            "market_research_data": r"Similarweb|Stats South Africa|study came out|monthly visits|unique users|household entertainment spending|market share",
            "pricing_psychology": r"reframing your price|smaller font for the price|Dollar signs|per employee|per day|lattes a week",
            "website_utility_pages": r"4:04 page|404 page|contact page|HTML sitemap|useful links|crawl your contact page|information about your business",
            "creative_tool_stack": r"Adobe Express|Canva Video|Affinity|CapCut|colourzilla|ColorZilla|Banana Prompts|AI art|prompts",
            "content_distribution_frequency": r"post 100 times|posting five times per day|Facebook told us|content every hour|YouTube get|YouTube gets|content performance|impressions|monthly visits|unique users|search on YouTube|Instagram views|views are counted|one high quality reel|50 day intensive sprint",
            "ad_platform_research": r"trademark Protection|Google Ads|targeting methods|Facebook and Instagram|any ad on Facebook and Instagram",
            "naming_positioning": r"name your baby|name consultancy|changed the names|fruits and vegetables|bespoke naming|dragon teeth|brand name",
            "attribution_contact_routes": r"call tracking number|magnet stuck|got in touch|getting people in touch|measurable|business away",
            "seo_vendor_red_flags": r"search engine optimization|vague|fancy terms|throw you off their scent",
            "search_feature_monitoring": r"shopping tag|Google search results|missing|different countries|VPN|country",
            "local_seo_operations": r"Google Business Profile|Google posts|opening hours|services|geotagging|citations|driving directions|provides tags|local pack|local search ranking factors",
            "video_content_production": r"better quality videos|make your videos better|clean your lenses|microphone|back camera|Apple Watch|12 second video|hooked me",
            "social_personal_brand": r"personal brand|agency leads|LinkedIn|followers|social media|content creator|videos on YouTube|referrals",
            "sales_offer_fit": r"saying no|right type of business|winners|proposal|follow UPS|shipping charges|customers do not wanna pay",
            "brand_campaign_creativity": r"Spotify Wrapped|Barilla|playlists|marketing stunt|human psychology|refrigerator|sense of humor|do nothing for 2 minutes|hooked|beer at my manager",
            "ai_productivity_tools": r"Whisper AI|Workspace Studio|Claude|Chrome plugin|Chrome extension|automate|text to speech|speech to text|AI tool",
            "seo_foundations": r"Website Authority Checker|ahrefs|file size|fast website|content freshness|SEO audits|SEO on YouTube|Google AI overview|basics|website Authority",
            "seo_market_trends": r"Semrush stock|SEO services market|AEO and SEO|Google Trends|SEO is dead|search engine optimization.*all time high|\$171 billion|\$88 billion",
            "ai_search_tactics": r"Google AI overview|dash AI|AI overview|website recommended by AI|AI to recommend|answer engine optimisation|AI empowered generalist|AI domains|AI dot com|Notebook L m|Google Skills",
            "ecommerce_conversion": r"checkout process|e commerce websites|Google Shopping|shopping feed|categories|collections|shipping charges|customers do not wanna pay",
            "google_ads_strategy": r"Google Advertising|Google Ads advertising|PMAX|P Max|location settings|auction report|auction insights|Local Services ads|Google Premier Partner|service based business",
            "agency_marketing_governance": r"in house marketing teams|external agencies|agency|new SEO provider|Google Ads and SEO|digital marketer|passionate|Premier Partner",
            "channel_strategy": r"SMS texting|SMS marketing|podcast bookings|Super Bowl|commercials|YouTube might never have existed|direct channel|podcast episodes",
            "copy_positioning": r"Don't say|spreadsheet for marketers|replaces email|alternative|how we help",
            "technical_seo_hygiene": r"web hosting|page speed|website engagement rate|topical authority|navigation|categories|collections|content freshness|keyword|freshnessdistancecalculator",
            "local_review_scam_ops": r"listing verification team|Google business listing|negative review|update from customer|reporting it|Google search results",
        }
        pat = semantic_patterns.get(rule_key)
        if pat and not re.search(pat, evidence, re.I):
            fail(failures, claim_id, f"semantic_evidence_mismatch:{rule_key}")
        if not 3 <= len(topic) <= 140:
            fail(failures, claim_id, f"topic_length_out_of_range:{len(topic)}")
        if GENERIC_RE.search(claim):
            fail(failures, claim_id, "generic_claim_language")
        if GENERIC_RE.search(action):
            fail(failures, claim_id, "generic_action_language")
        if not ACTION_VERB_RE.search(action):
            warnings[claim_id].append("action_missing_operational_verb")
        if row.get("evidence_source") not in (None, "passage"):
            fail(failures, claim_id, f"evidence_source_not_passage:{row.get('evidence_source')}")
        if row.get("public") is True:
            fail(failures, claim_id, "candidate_preimport_public_true")
        if row.get("needs_review") is True:
            fail(failures, claim_id, "candidate_needs_review_true")

        source_passages = passages_by_source.get(source_id, [])
        exact_matches = [p for p in source_passages if evidence and evidence in str(p.get("body") or "")]
        if not exact_matches:
            fail(failures, claim_id, "evidence_not_exact_public_passage_substring")
        else:
            for p in exact_matches:
                if p.get("public_policy") != "search_passage":
                    fail(failures, claim_id, f"passage_public_policy_not_search_passage:{p.get('public_policy')}")
                if p.get("full_transcript_public") is True:
                    fail(failures, claim_id, "passage_full_transcript_public_true")
                body = str(p.get("body") or "").strip()
                if len(body) and len(evidence) > max(500, int(0.70 * len(body))):
                    fail(failures, claim_id, "evidence_excerpt_too_much_of_passage")
            source_passage_id = row.get("source_passage_id")
            if source_passage_id and not any(source_passage_id in {p.get("id"), p.get("chunk_id")} for p in exact_matches):
                warnings[claim_id].append("source_passage_id_not_the_exact_match_passage")

        if seen_sources[source_id] + len(existing_public_by_source[source_id]) > args.max_per_source:
            fail(
                failures,
                claim_id,
                f"per_source_cap_exceeded:existing_public={len(existing_public_by_source[source_id])},batch={seen_sources[source_id]},max={args.max_per_source}",
            )
        topic_key = norm(topic)
        if seen_source_topics[(source_id, topic_key)] > 1:
            fail(failures, claim_id, "duplicate_topic_for_source_in_batch")
        existing_topics = {norm(str(c.get("topic") or c.get("topic_label") or "")) for c in existing_public_by_source[source_id]}
        existing_topic_ids = {norm(str(c.get("topic_id") or "")) for c in existing_public_by_source[source_id]}
        if topic_key and topic_key in existing_topics:
            fail(failures, claim_id, "duplicate_existing_public_topic_for_source")
        if row.get("topic_id") and norm(str(row.get("topic_id"))) in existing_topic_ids:
            fail(failures, claim_id, "duplicate_existing_public_topic_id_for_source")

        if review_by_claim:
            rr = review_by_claim.get(claim_id)
            if not rr:
                fail(failures, claim_id, "missing_from_review_report")
            else:
                if rr.get("recommended_status") != "promotion_candidate":
                    fail(failures, claim_id, f"review_not_promotion_candidate:{rr.get('recommended_status')}")
                if rr.get("evidence_match_method") != "exact":
                    fail(failures, claim_id, f"review_evidence_not_exact:{rr.get('evidence_match_method')}")
                if rr.get("hard_failures"):
                    fail(failures, claim_id, f"review_hard_failures:{rr.get('hard_failures')}")
                if rr.get("soft_warnings"):
                    fail(failures, claim_id, f"review_soft_warnings:{rr.get('soft_warnings')}")

    accepted = [str(r.get("claim_id")) for r in candidates if not failures.get(str(r.get("claim_id") or ""))]
    report = {
        "ok": not failures,
        "candidate_file": str(args.candidates),
        "queue_snapshot": str(args.queue),
        "review_report": str(args.review_report) if args.review_report else "",
        "rows": len(candidates),
        "accepted": len(accepted),
        "rejected": sum(1 for r in candidates if failures.get(str(r.get("claim_id") or ""))),
        "accepted_claim_ids": accepted,
        "failures": failures,
        "warnings": warnings,
        "checks": {
            "requires_exact_public_passage": True,
            "requires_queue_snapshot_needs_insight": True,
            "requires_review_exact_promotion_candidate_when_review_report_given": bool(args.review_report),
            "max_per_source": args.max_per_source,
        },
    }
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    print(text)
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(text + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
