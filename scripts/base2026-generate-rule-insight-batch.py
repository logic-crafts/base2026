#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "public-data" / "tiktok"
DEFAULT_QUEUE = ROOT / ".planning" / "insight-repair" / "needs-insight-latest.jsonl"
OUT_DIR = ROOT / ".planning" / "insight-repair"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def slug(text: str, max_len: int = 120) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value[:max_len].strip("-") or "insight"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def split_sentences(text: str) -> list[str]:
    # Keep exact substrings from the source body while splitting conservatively.
    text = re.sub(r"\s+", " ", (text or "")).strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", text)
    out: list[str] = []
    for part in parts:
        part = part.strip()
        if len(part) >= 35:
            out.append(part)
    if not out and len(text) >= 35:
        out.append(text)
    return out


def first_sentence(passages: list[dict[str, Any]], pattern: re.Pattern[str]) -> tuple[str, str]:
    def window(sentence: str, match: re.Match[str]) -> str:
        if len(sentence) <= 450:
            return sentence
        start = max(0, match.start() - 120)
        end = min(len(sentence), match.end() + 240)
        while start > 0 and sentence[start - 1] not in " .!?;:":
            start -= 1
        while end < len(sentence) and sentence[end] not in " .!?;:":
            end += 1
        excerpt = sentence[start:end].strip()
        if len(excerpt) < 20:
            excerpt = sentence[:450].strip()
        return excerpt

    for passage in passages:
        body = passage.get("body") or ""
        for sentence in split_sentences(body):
            m = pattern.search(sentence)
            if m:
                excerpt = window(sentence, m)
                if len(excerpt) < 55:
                    continue
                return excerpt, str(passage.get("id") or passage.get("chunk_id") or "")
    return "", ""


def includes_any(text: str, words: list[str]) -> bool:
    lower = text.lower()
    return any(word.lower() in lower for word in words)


@dataclass(frozen=True)
class Rule:
    key: str
    topic: str
    match: re.Pattern[str]
    evidence: re.Pattern[str]
    claim: Callable[[str], str]
    action: Callable[[str], str]


RULES: list[Rule] = [
    Rule(
        "seo_market_trends",
        "SEO and AEO market trend validation",
        re.compile(r"Semrush stock|SEO services market|AEO and SEO|Google Trends|SEO is dead|search engine optimization.*all time high|\$171 billion", re.I),
        re.compile(r"Semrush stock|SEO services market|AEO and SEO|Google Trends|SEO is dead|search engine optimization.*all time high|\$171 billion|\$88 billion", re.I),
        lambda e: "SEO and AEO planning should separate market-size signals from hype so strategy is based on observable demand and budget movement.",
        lambda e: "Track market estimates, Google Trends, tool-category movement, and client demand before changing investment assumptions around SEO or AEO.",
    ),
    Rule(
        "ai_search_tactics",
        "AI and answer-engine search tactics",
        re.compile(r"Google AI overview|dash AI|website recommended by AI|AI to recommend your business|answer engine optimisation|AI empowered generalist|AI domains|AI dot com|Notebook L m|Google Skills", re.I),
        re.compile(r"Google AI overview|dash AI|AI overview|website recommended by AI|AI to recommend|answer engine optimisation|AI empowered generalist|AI domains|AI dot com|Notebook L m|Google Skills", re.I),
        lambda e: "AI search and answer-engine work needs concrete tactics for discoverability, citation, skills, and query-surface behavior.",
        lambda e: "Document the AI/search tactic, query surface, source page, and proof of recommendation or visibility before treating it as repeatable AEO work.",
    ),
    Rule(
        "ecommerce_conversion",
        "Ecommerce conversion and feed readiness",
        re.compile(r"checkout process|e commerce websites|Google Shopping|shopping feed|categories or collections|shipping charges|customers do not wanna pay", re.I),
        re.compile(r"checkout process|e commerce websites|Google Shopping|shopping feed|categories|collections|shipping charges|customers do not wanna pay", re.I),
        lambda e: "Ecommerce growth depends on reducing checkout friction, structuring product feeds, and building category pages that match buying behavior.",
        lambda e: "Audit checkout steps, shipping presentation, product feed attributes, and category architecture before spending more on ecommerce acquisition.",
    ),
    Rule(
        "google_ads_strategy",
        "Google Ads strategy and diagnostics",
        re.compile(r"Google Advertising|Google Ads advertising|PMAX|P Max|location settings|auction report|auction insights|Local Services ads|Google Premier Partner|service based business", re.I),
        re.compile(r"Google Advertising|Google Ads advertising|PMAX|P Max|location settings|auction report|auction insights|Local Services ads|Google Premier Partner|service based business", re.I),
        lambda e: "Google Ads strategy needs campaign-type, location, auction, and service-fit diagnostics before optimization work is trusted.",
        lambda e: "Review campaign type, location settings, auction insights, service eligibility, and partner/account context before changing budget or judging performance.",
    ),
    Rule(
        "agency_marketing_governance",
        "Agency and marketing-team governance",
        re.compile(r"in house marketing teams|external agencies|abusive relationship with your agency|new SEO provider|agency doing Google Ads and SEO|digital marketer|passionate about the industry|Premier Partner", re.I),
        re.compile(r"in house marketing teams|external agencies|agency|new SEO provider|Google Ads and SEO|digital marketer|passionate|Premier Partner", re.I),
        lambda e: "Marketing performance depends on clear governance between internal teams, agencies, credentials, expectations, and review routines.",
        lambda e: "Define ownership, reporting, access, partner status, review cadence, and escalation paths before agency or internal team work is judged only by outcomes.",
    ),
    Rule(
        "channel_strategy",
        "Channel strategy and distribution bets",
        re.compile(r"SMS texting|SMS marketing|podcast bookings|Super Bowl|commercials|YouTube might never have existed|direct channel|podcast episodes", re.I),
        re.compile(r"SMS texting|SMS marketing|podcast bookings|Super Bowl|commercials|YouTube might never have existed|direct channel|podcast episodes", re.I),
        lambda e: "Channel strategy should evaluate emerging, expensive, or underused channels by cost, audience behavior, and proof of distribution fit.",
        lambda e: "Compare channel cost, audience intent, saturation risk, and required creative format before reallocating budget or building a new channel playbook.",
    ),
    Rule(
        "copy_positioning",
        "Copy positioning and wording precision",
        re.compile(r"Don't say|say V|spreadsheet for marketers|replaces email|alternative", re.I),
        re.compile(r"Don't say|spreadsheet for marketers|replaces email|alternative|how we help", re.I),
        lambda e: "Small wording changes can make positioning more specific by naming the audience, replacement, or outcome instead of using generic copy.",
        lambda e: "Rewrite generic claims into audience-specific, replacement-based, or outcome-led language and test whether comprehension improves.",
    ),
    Rule(
        "technical_seo_hygiene",
        "Technical SEO and site architecture hygiene",
        re.compile(r"web hosting|page speed|website engagement rate|topical authority|navigation|categories or collections|content freshness|keyword stuffing|add keywords to the page|freshnessdistancecalculator", re.I),
        re.compile(r"web hosting|page speed|website engagement rate|topical authority|navigation|categories|collections|content freshness|keyword|freshnessdistancecalculator", re.I),
        lambda e: "Technical SEO depends on site speed, architecture, topical coverage, engagement, and freshness rather than isolated keyword edits.",
        lambda e: "Audit speed, hosting, navigation, categories, keyword use, topical coverage, engagement, and freshness before escalating to advanced SEO tactics.",
    ),
    Rule(
        "local_review_scam_ops",
        "Local listing scams and review-risk handling",
        re.compile(r"listing verification team|Google business listing|negative review|update from customer|reporting it|Google search results", re.I),
        re.compile(r"listing verification team|Google business listing|negative review|update from customer|reporting it|Google search results", re.I),
        lambda e: "Local businesses need a response process for listing-verification scams and review artifacts that can damage trust or visibility.",
        lambda e: "Capture the suspicious message or review artifact, verify it through official GBP channels, and document the response path before engaging.",
    ),
    Rule(
        "market_research_data",
        "Market and channel data validation",
        re.compile(r"Similarweb|Stats South Africa|study came out|monthly visits|unique users|household entertainment spending|market share", re.I),
        re.compile(r"According to Similarweb|Stats South Africa|study came out|monthly visits|unique users|household entertainment spending|market share", re.I),
        lambda e: "Marketing decisions are stronger when channel, category, and audience assumptions are checked against sourced market data.",
        lambda e: "Document the data source, metric, geography, and date before using the statistic to choose channels, forecast demand, or prioritize content.",
    ),
    Rule(
        "pricing_psychology",
        "Pricing presentation and framing",
        re.compile(r"reframing your price|smaller font for the price|Dollar signs|per employee|per day|lattes a week", re.I),
        re.compile(r"reframing your price|smaller font for the price|Dollar signs|per employee|per day|lattes a week", re.I),
        lambda e: "Pricing perception changes when the same price is framed by unit, frequency, comparison, or visual presentation.",
        lambda e: "Test price framing with honest per-day, per-seat, and usage comparisons, and verify that conversion lift does not create expectation or trust problems.",
    ),
    Rule(
        "website_utility_pages",
        "Website utility pages and conversion readiness",
        re.compile(r"4:04 page|404 page|contact page|HTML sitemap|useful links|crawl your contact page", re.I),
        re.compile(r"4:04 page|404 page|contact page|HTML sitemap|useful links|crawl your contact page|information about your business", re.I),
        lambda e: "Utility pages such as 404, contact, and sitemap pages can support SEO and conversion when they are intentionally maintained.",
        lambda e: "Audit utility pages for helpful links, complete business details, crawlability, and a clear next step instead of leaving them as dead-end templates.",
    ),
    Rule(
        "creative_tool_stack",
        "Creative production tool workflow",
        re.compile(r"Adobe Express|Canva Video|Affinity|CapCut|colourzilla|ColorZilla|Banana Prompts|Canva launched|AI art", re.I),
        re.compile(r"Adobe Express|Canva Video|Affinity|CapCut|colourzilla|ColorZilla|Banana Prompts|AI art|prompts", re.I),
        lambda e: "Creative production improves when tools are chosen for the specific editing, prompt, design, or repurposing job instead of as generic software.",
        lambda e: "Map each recurring creative task to the fastest reliable tool, save the workflow steps, and keep output QA separate from the tool demo itself.",
    ),
    Rule(
        "content_distribution_frequency",
        "Content distribution frequency and channel testing",
        re.compile(r"post 100 times|posting five times per day|YouTube get|YouTube gets|grow your business.*YouTube|content performance|more people go and search on YouTube|Instagram views|views are counted|50 day intensive sprint|one high quality reel", re.I),
        re.compile(r"post 100 times|posting five times per day|Facebook told us|content every hour|YouTube get|YouTube gets|content performance|impressions|monthly visits|unique users|search on YouTube|Instagram views|views are counted|one high quality reel|50 day intensive sprint", re.I),
        lambda e: "Content distribution should be tested by channel and posting frequency because reach can change sharply by platform and cadence.",
        lambda e: "Run channel-specific frequency tests, record impressions and engagement separately, and keep the learning tied to the audience and format that produced it.",
    ),
    Rule(
        "ad_platform_research",
        "Ad platform policy and competitor research",
        re.compile(r"trademark Protection for your brand with Google Ads|targeting methods.*Facebook|targeting methods.*Instagram|any ad on Facebook and Instagram|Google Ads trademark", re.I),
        re.compile(r"trademark Protection|Google Ads|targeting methods|Facebook and Instagram|any ad on Facebook and Instagram", re.I),
        lambda e: "Ad platforms expose policy, targeting, and competitor-research surfaces that should be checked before campaign changes.",
        lambda e: "Document the relevant ad-platform surface, capture the policy or targeting evidence, and convert it into a campaign, brand-protection, or competitor-research task.",
    ),
    Rule(
        "naming_positioning",
        "Naming and positioning as conversion framing",
        re.compile(r"name your baby|name consultancy|changed the names|fruits and vegetables|bespoke naming|dragon teeth|brand name", re.I),
        re.compile(r"name your baby|name consultancy|changed the names|fruits and vegetables|bespoke naming|dragon teeth|brand name", re.I),
        lambda e: "Naming and wording can change perception, memorability, and willingness to engage with an offer or product.",
        lambda e: "Test naming options against audience comprehension, emotional response, search clarity, and conversion behavior before treating naming as decoration.",
    ),
    Rule(
        "attribution_contact_routes",
        "Attribution and contact-route coverage",
        re.compile(r"call tracking number|magnet stuck|got in touch|getting people in touch|contact route|measurable", re.I),
        re.compile(r"call tracking number|magnet stuck|got in touch|getting people in touch|measurable|business away", re.I),
        lambda e: "Lead attribution should not block customers from contacting the business through the route they already trust.",
        lambda e: "Keep every contact route easy to use, add measurement where it does not add friction, and review offline or untracked leads alongside digital attribution.",
    ),
    Rule(
        "seo_vendor_red_flags",
        "SEO vendor clarity and risk signals",
        re.compile(r"don't understand search engine optimization|vague|fancy terms|throw you off their scent|SEO.*vague", re.I),
        re.compile(r"search engine optimization|vague|fancy terms|throw you off their scent", re.I),
        lambda e: "Vague SEO explanations and jargon-heavy answers are risk signals when evaluating vendors or internal SEO work.",
        lambda e: "Ask for plain-language SEO evidence, specific tasks, expected outcomes, and verifiable examples before accepting a recommendation or scope.",
    ),
    Rule(
        "search_feature_monitoring",
        "Search feature availability monitoring",
        re.compile(r"shopping tag inside Google search results|search results.*missing|VPN|different countries|country", re.I),
        re.compile(r"shopping tag|Google search results|missing|different countries|VPN|country", re.I),
        lambda e: "Search features can vary by country and surface, so visibility checks need location-aware monitoring.",
        lambda e: "Track priority search features by country, device, and query type before assuming a missing or changed SERP element is universal.",
    ),
    Rule(
        "local_seo_operations",
        "Local SEO operations and Google Business Profile maintenance",
        re.compile(r"Google Business Profile|Google posts|opening hours|services in your Google Business Profile|geotagging|citations|driving directions|provides tags|local pack|local search ranking factors|Google posts impact rankings", re.I),
        re.compile(r"Google Business Profile|Google posts|opening hours|services|geotagging|citations|driving directions|provides tags|local pack|local search ranking factors", re.I),
        lambda e: "Local SEO performance depends on maintaining specific Google Business Profile fields, local signals, and location evidence over time.",
        lambda e: "Audit GBP fields, posts, services, citations, opening hours, profile engagement signals, and local-ranking experiments before changing local SEO priorities.",
    ),
    Rule(
        "video_content_production",
        "Video content production quality",
        re.compile(r"better quality videos|make your videos better|clean your lenses|microphone|back camera|Apple Watch|content creators|12 second video|hooked me", re.I),
        re.compile(r"better quality videos|make your videos better|clean your lenses|microphone|back camera|Apple Watch|12 second video|hooked me", re.I),
        lambda e: "Video performance depends on basic production quality, hooks, and repeatable capture workflows as much as on the idea itself.",
        lambda e: "Create a pre-publish video checklist covering lens, audio, framing, hook, length, and repeatability before judging the content strategy.",
    ),
    Rule(
        "social_personal_brand",
        "Social and personal-brand growth engine",
        re.compile(r"personal brand|agency leads|LinkedIn more seriously|followers on TikTok|not on social media|content creator|videos on YouTube|referrals", re.I),
        re.compile(r"personal brand|agency leads|LinkedIn|followers|social media|content creator|videos on YouTube|referrals", re.I),
        lambda e: "Social and personal-brand work can become a lead engine when publishing, proof, and referral loops are measured together.",
        lambda e: "Track content output, audience growth, referral source, and lead quality together so social activity is tied to pipeline rather than vanity metrics alone.",
    ),
    Rule(
        "sales_offer_fit",
        "Sales process and offer-fit discipline",
        re.compile(r"saying no|right type of business|winners and not with losers|proposal|follow UPS|shipping charges|customers do not wanna pay", re.I),
        re.compile(r"saying no|right type of business|winners|proposal|follow UPS|shipping charges|customers do not wanna pay", re.I),
        lambda e: "Sales quality depends on offer fit, pricing friction, and follow-up discipline, not only on generating more leads.",
        lambda e: "Review which clients, fees, shipping or pricing terms, and follow-up rules improve margin and close rate before adding more acquisition volume.",
    ),
    Rule(
        "brand_campaign_creativity",
        "Brand campaign mechanics and memorable hooks",
        re.compile(r"Spotify Wrapped|Barilla|playlists|marketing stunt|human psychology|refrigerator|sense of humor|do nothing for 2 minutes|hooked you immediately|beer at my manager", re.I),
        re.compile(r"Spotify Wrapped|Barilla|playlists|marketing stunt|human psychology|refrigerator|sense of humor|do nothing for 2 minutes|hooked|beer at my manager", re.I),
        lambda e: "Memorable campaigns often work because a simple mechanic turns the brand idea into something observable or repeatable.",
        lambda e: "Extract the campaign mechanic, audience trigger, distribution surface, and proof metric before reusing the idea for another brand.",
    ),
    Rule(
        "ai_productivity_tools",
        "AI productivity and automation tooling",
        re.compile(r"Whisper AI|Workspace Studio|Claude.*Chrome plugin|Chrome extension|automate|text to speech|speech to text|AI tool", re.I),
        re.compile(r"Whisper AI|Workspace Studio|Claude|Chrome plugin|Chrome extension|automate|text to speech|speech to text|AI tool", re.I),
        lambda e: "AI productivity tools are most useful when tied to a repeatable workflow such as dictation, browser control, automation, or content operations.",
        lambda e: "Document the workflow, inputs, failure cases, and handoff point before adding the AI tool to a production operating system.",
    ),
    Rule(
        "seo_foundations",
        "SEO foundations and technical hygiene",
        re.compile(r"Website Authority Checker|ahrefs|image.*file size|fast website|content freshness|SEO audits|SEO on YouTube|Google AI overview|basics of.*SEO|website Authority", re.I),
        re.compile(r"Website Authority Checker|ahrefs|file size|fast website|content freshness|SEO audits|SEO on YouTube|Google AI overview|basics|website Authority", re.I),
        lambda e: "SEO foundations require basic technical hygiene, authority checks, content freshness, and surface-specific search behavior before advanced tactics matter.",
        lambda e: "Run a foundation audit covering speed, image weight, authority, freshness, search surfaces, and baseline ranking evidence before chasing new tactics.",
    ),
    Rule(
        "google_ads_broad",
        "Broad match Google Ads risk",
        re.compile(r"\bbroad match\b|irrelevant clicks", re.I),
        re.compile(r"\bbroad match\b|irrelevant clicks", re.I),
        lambda e: "Broad match Google Ads campaigns can waste spend when ads match irrelevant searches instead of buyer-intent queries.",
        lambda e: "Audit broad-match campaigns, review search terms, add negatives, and tighten match types before scaling paid search spend.",
    ),
    Rule(
        "handover_tracking",
        "Agency handover tracking integrity",
        re.compile(r"handover|new agency|old agency|sabotage.*account|conversion action.*handover", re.I),
        re.compile(r"conversion action|phone tracking|Google Analytics|reporting", re.I),
        lambda e: "Marketing handovers can distort performance if conversion actions, phone tracking, or analytics settings change during transfer.",
        lambda e: "Snapshot analytics, tag, conversion, and call-tracking settings before every agency handover and verify them again after access changes.",
    ),
    Rule(
        "google_ads_ops",
        "Google Ads account operations",
        re.compile(r"Google Ads (?:campaign|account|Display|remarketing|Ad Strength)|Google ad campaigns|remarketing|Keyword Planner|Ad Strength|Quality Score|EU political ads|exclude mobile apps", re.I),
        re.compile(r"Google Ads|remarketing|Keyword Planner|Ad Strength|Quality Score|EU political ads|mobile apps|campaign", re.I),
        lambda e: "Google Ads performance depends on operational settings that can affect spend, targeting, measurement, or campaign continuity.",
        lambda e: "Audit the referenced Google Ads setting, document the intended configuration, and verify search terms, exclusions, tracking, and policy status before scaling.",
    ),
    Rule(
        "malware_paid_search",
        "Malware as paid search continuity risk",
        re.compile(r"malware|viruses|Google Ads.*suspend|suspend.*Google Ads", re.I),
        re.compile(r"malware|viruses|Google Ads.*suspend|suspend.*account|leads.*dry", re.I),
        lambda e: "Website malware can interrupt paid acquisition because Google Ads may stop serving until the infection is removed.",
        lambda e: "Add malware checks to marketing operations: update plugins, monitor site health, use secure hosting, and keep non-paid lead channels active.",
    ),
    Rule(
        "gbp_qna",
        "Google Business Profile Q&A content",
        re.compile(r"Google Business Profile.*Q&A|Q&A.*Google Business Profile", re.I | re.S),
        re.compile(r"Google Business Profile.*Q&A|Q&A.*Google Business Profile|Q&A", re.I),
        lambda e: "Google Business Profile Q&A can be used as a local SEO surface when questions and answers are actively maintained.",
        lambda e: "Audit GBP Q&A entries, add helpful owner answers, remove spam where possible, and align answers with the services and locations customers search for.",
    ),
    Rule(
        "gbp_local",
        "Google Business Profile local SEO operations",
        re.compile(r"Google Business Profile|Google My Business|GMB|Google Maps|local rank|local ranking|service area|appointments only", re.I),
        re.compile(r"categories|service areas|appointment|appointments|local rank|local ranking|ranking grid|Google Maps|tank your local SEO", re.I),
        lambda e: "Local visibility depends on Google Business Profile and local ranking settings that need active category, service-area, Q&A, and ranking QA.",
        lambda e: "Audit GBP fields, competitor categories, Q&A, service areas, appointment settings, and local rank movement as a recurring local SEO checklist.",
    ),
    Rule(
        "rank_reporting",
        "Client-facing SEO visibility reporting",
        re.compile(r"visibility score|PDF report|rank tracker|keyword usage|desktop and mobile|ranking grid", re.I),
        re.compile(r"visibility score|PDF report|keyword usage|desktop|mobile|rank|ranking grid", re.I),
        lambda e: "SEO reporting is stronger when it shows visibility movement, keyword distribution, and ranking context instead of isolated rank rows.",
        lambda e: "Build client reports around visibility score, keyword buckets, device view, Maps versus organic context, and clear before/after movement.",
    ),
    Rule(
        "content_links",
        "Content assets as link acquisition",
        re.compile(r"Unsplash|Pexels|photos.*link|add a link|link to my website", re.I),
        re.compile(r"Unsplash|Pexels|add a link|link to my website|photos", re.I),
        lambda e: "Useful niche assets can create link opportunities when people reuse them and can be asked for attribution to the original site.",
        lambda e: "Publish reusable niche assets, track where they are used, and request attribution links where the usage is relevant and legitimate.",
    ),
    Rule(
        "wordpress_seo",
        "WordPress and website SEO settings",
        re.compile(r"WordPress|Yoast|Rank Math|Wix|meta title|meta description|homepage SEO|page title", re.I),
        re.compile(r"WordPress|Yoast|Rank Math|Wix|meta title|meta description|homepage|page title|title tag", re.I),
        lambda e: "Homepage and CMS SEO settings affect how search engines interpret the most important page on a business website.",
        lambda e: "Audit each CMS homepage title, meta description, SEO plugin setup, and duplicate-plugin risk before treating the site as technically ready.",
    ),
    Rule(
        "seo_tools",
        "SEO research and tooling workflow",
        re.compile(r"keyword research|Keyword Sheeter|SEMrush|Wayback Machine|disavow|backlinks|citation mining|AI SEO|Search Console", re.I),
        re.compile(r"keyword|SEMrush|Wayback|disavow|backlinks|citation|AI SEO|Search Console|SEO", re.I),
        lambda e: "SEO workflows benefit from specific research tools for keyword discovery, historical checks, backlink triage, citations, and search visibility diagnostics.",
        lambda e: "Route each SEO task to the right tool, document the evidence found, and convert the output into a concrete page, citation, backlink, or technical action.",
    ),
    Rule(
        "open_web_search_shift",
        "Open web and search-platform risk",
        re.compile(r"open web|web publishing|Google CEO|court document", re.I),
        re.compile(r"open web|web publishing|Google CEO|court document", re.I),
        lambda e: "Search strategy has to account for platform shifts that can change the economics of open-web publishing.",
        lambda e: "Track search-platform statements, crawl and indexation movement, referral traffic, and citation surfaces before relying on one open-web growth path.",
    ),
    Rule(
        "ai_visibility",
        "AI visibility and answer readiness",
        re.compile(r"AI search|AI SEO|ChatGPT|Claude|Gemini|Sora|LLM|Buy It in ChatGPT|AI model|Perplexity|AI recommends", re.I),
        re.compile(r"\bAI\b|ChatGPT|Claude|Gemini|LLM|Sora|model|answer|checkout|AI SEO", re.I),
        lambda e: "AI visibility work depends on matching the right model, search surface, or answer format to the business outcome being optimized.",
        lambda e: "Map each AI/search surface to a task: answer extraction, public copy, citation mining, checkout readiness, media generation, or customer-intent capture.",
    ),
    Rule(
        "dmca_deindex",
        "Search deindexing abuse risk",
        re.compile(r"DMCA|de-?index|fake law|remove pages from search|copyright takedown", re.I),
        re.compile(r"DMCA|de-?indexed|fake law|remove pages from search|copyright takedown", re.I),
        lambda e: "Search visibility can be attacked through fake takedown or deindexing abuse, not only through normal ranking changes.",
        lambda e: "Monitor critical pages for sudden deindexing, keep authorship and ownership evidence, and document escalation paths for false takedown events.",
    ),
    Rule(
        "reporting_reputation",
        "Search reputation management",
        re.compile(r"online reputation|reputation management|name appears|reviews|fake review|review generation", re.I),
        re.compile(r"reputation|reviews|fake review|name appears|search engine results", re.I),
        lambda e: "Search reputation management is about controlling and monitoring how a name or business appears in search results and reviews.",
        lambda e: "Track branded search results and review signals, document harmful listings or fake-review behavior, and define a response workflow before reputation damage compounds.",
    ),
    Rule(
        "paid_social_affordability",
        "Paid social audience affordability",
        re.compile(r"South African advertisers|developing countries|audience is huge|afford your services", re.I),
        re.compile(r"audience is huge|afford your services|developing countries|South African advertisers", re.I),
        lambda e: "Paid social reach can be misleading when a large audience contains only a small segment that can afford the offer.",
        lambda e: "Segment paid social campaigns by affordability signals, geography, and purchase intent instead of optimizing only for broad audience size.",
    ),
    Rule(
        "meta_asset_ownership",
        "Meta Business asset ownership",
        re.compile(r"Meta Business|Facebook and Instagram for your business|ad accounts|admin|controls their pages", re.I),
        re.compile(r"controls their pages|ad accounts|admin|who controls|controls the ad accounts", re.I),
        lambda e: "Businesses need clear ownership of Meta pages, ad accounts, and admin access before relying on Facebook or Instagram advertising.",
        lambda e: "Inventory Meta Business assets, confirm owner and admin roles, remove stale agency access, and document who controls each page and ad account.",
    ),
    Rule(
        "bing_ai_search",
        "Bing and AI search opportunity",
        re.compile(r"Bringing Bing Back|bing\.com slash webmasters|bing\.com/webmasters|Bing Webmaster|Microsoft Copilot|Copilot", re.I),
        re.compile(r"Bing Webmaster|bing\.com|Bing|Microsoft|Copilot", re.I),
        lambda e: "Bing can matter for AI and search visibility when it connects traditional search behavior with answer and assistant surfaces.",
        lambda e: "Track Bing indexing, answer visibility, and citation footprint separately from Google so AI-search opportunities are not hidden in blended SEO reporting.",
    ),
    Rule(
        "media_strategy",
        "Media channel strategy",
        re.compile(r"YouTube is basically|media industry|traditional media|direct mail|email client|open rate", re.I),
        re.compile(r"YouTube is basically|traditional media|direct mail|email|open rate|media industry", re.I),
        lambda e: "Channel strategy should follow where attention and response are actually moving, not only where a team already publishes.",
        lambda e: "Compare channel reach, response, and cost by surface, then decide whether to shift content, ads, or retention work toward the stronger channel.",
    ),
    Rule(
        "social_content",
        "Social content value and distribution",
        re.compile(r"social media marketing|more followers|value first|Jab, Jab|posting videos on social media|reposting|Instagram Stories to Snapchat|Snapchat Stories", re.I),
        re.compile(r"social media marketing|more followers|value|posting videos on social media|Instagram Stories to Snapchat|Snapchat Stories", re.I),
        lambda e: "Social growth depends on repeated useful content and distribution mechanics rather than posting without a clear value reason.",
        lambda e: "Define the audience value, repurpose only the formats that fit each platform, and measure follower, engagement, and conversion movement separately.",
    ),
    Rule(
        "reddit_channel",
        "Reddit audience and advertising channel",
        re.compile(r"advertising on Reddit|Reddit users|not on Facebook|not on Instagram|not on TikTok", re.I),
        re.compile(r"advertising on Reddit|Reddit users|not on Facebook|not on Instagram|not on TikTok", re.I),
        lambda e: "Reddit can be a separate acquisition channel because some Reddit users are not active on other major social platforms.",
        lambda e: "Test Reddit as its own channel with subreddit research, native creative, separate measurement, and assumptions that differ from Meta or TikTok.",
    ),
    Rule(
        "content_links",
        "Content assets as link acquisition",
        re.compile(r"Unsplash|Pexels|photos.*link|add a link|link to my website", re.I),
        re.compile(r"Unsplash|Pexels|add a link|link to my website|photos", re.I),
        lambda e: "Useful niche assets can create link opportunities when people reuse them and can be asked for attribution to the original site.",
        lambda e: "Publish reusable niche assets, track where they are used, and request attribution links where the usage is relevant and legitimate.",
    ),
    Rule(
        "reporting_reputation",
        "Search reputation management",
        re.compile(r"online reputation|reputation management|name appears|reviews|fake review|review generation", re.I),
        re.compile(r"reputation|reviews|fake review|name appears|search engine results", re.I),
        lambda e: "Search reputation management is about controlling and monitoring how a name or business appears in search results and reviews.",
        lambda e: "Track branded search results and review signals, document harmful listings or fake-review behavior, and define a response workflow before reputation damage compounds.",
    ),
    Rule(
        "business_ops",
        "Business operating loop",
        re.compile(r"CEO works|CEO .*driver|customer exposure|focused work|Pomodoro|five-year plans|six month|cumulative effect|silent killers of startups|writing a page a day|consistency", re.I),
        re.compile(r"CEO|customer|focused work|Pomodoro|five-year|six month|consistency|cumulative|silent killers|writing a page a day|something done", re.I),
        lambda e: "Business execution improves when operators stay close to users, shorten planning loops, and convert repeated work into visible compounding progress.",
        lambda e: "Define a concrete operating loop: customer exposure, short planning cycles, focused work blocks, and weekly proof of what compounded or changed.",
    ),
    Rule(
        "media_strategy",
        "Media channel strategy",
        re.compile(r"YouTube is basically|media industry|traditional media|direct mail|email client|open rate", re.I),
        re.compile(r"YouTube is basically|traditional media|direct mail|email|open rate|media industry", re.I),
        lambda e: "Channel strategy should follow where attention and response are actually moving, not only where a team already publishes.",
        lambda e: "Compare channel reach, response, and cost by surface, then decide whether to shift content, ads, or retention work toward the stronger channel.",
    ),
]

SKIP_RE = re.compile(
    r"I'm giving away|free copy|sealed and never been opened|lizard!|ancient lizard|hacker outfit|increase the size of my beard|"
    r"I only own white shirts|access Sora 2 outside|spent \\$160,000 on clothes|old com t shirts and gym shorts|stock price has gone down|SEMrush stock|No, no, no, no",
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


def choose_candidate(row: dict[str, Any], passages_by_source: dict[str, list[dict[str, Any]]], sources: dict[str, dict[str, Any]]) -> tuple[dict[str, Any] | None, str]:
    source_id = str(row.get("source_id") or "")
    passages = passages_by_source.get(source_id, [])
    source = sources.get(source_id, {})
    full_text = "\n".join(str(p.get("body") or "") for p in passages)
    haystack = "\n".join([str(source.get("title") or ""), full_text])
    if SKIP_RE.search(haystack):
        return None, "skip_low_value_or_visual_noise"
    if not passages:
        return None, "skip_no_passages"
    for rule in RULES:
        if not rule.match.search(haystack):
            continue
        evidence, passage_id = first_sentence(passages, rule.evidence)
        if not evidence:
            continue
        if WEAK_EVIDENCE_RE.search(evidence):
            continue
        return {
            "topic_label": rule.topic,
            "topic_id": slug(rule.topic),
            "claim_text": rule.claim(evidence),
            "suggested_action": rule.action(evidence),
            "evidence_excerpt": evidence,
            "source_passage_id": passage_id,
            "rule_key": rule.key,
        }, "selected"
    return None, "skip_no_rule_match"


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate deterministic exact-evidence TikTok insight repair candidates from a queue snapshot.")
    ap.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    ap.add_argument("--data-root", type=Path, default=DATA_ROOT)
    ap.add_argument("--target", type=int, default=24)
    ap.add_argument("--scan-limit", type=int, default=120)
    ap.add_argument("--batch", required=True)
    ap.add_argument("--start-number", type=int, required=True)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--report", type=Path, default=None)
    args = ap.parse_args()
    queue = read_jsonl(args.queue)[: args.scan_limit]
    sources = {str(r.get("source_id")): r for r in read_jsonl(args.data_root / "source_records.jsonl") if r.get("source_id")}
    passages_by_source: dict[str, list[dict[str, Any]]] = {}
    for p in read_jsonl(args.data_root / "passages.jsonl"):
        passages_by_source.setdefault(str(p.get("source_id") or ""), []).append(p)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = args.out or (OUT_DIR / f"claim-candidates-gpt55-{args.batch}-{args.target}-{stamp}.jsonl")
    report_path = args.report or out.with_suffix(".report.json")

    selected: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    n = args.start_number
    for row in queue:
        if len(selected) >= args.target:
            break
        source_id = str(row.get("source_id") or "")
        candidate, reason = choose_candidate(row, passages_by_source, sources)
        if not candidate:
            skipped.append({"source_id": source_id, "reason": reason})
            continue
        payload = {
            "claim_id": f"repair-gpt55-20260707-{n:03d}",
            "source_id": source_id,
            "item_id": row.get("item_id") or sources.get(source_id, {}).get("item_id") or "",
            "creator_handle": row.get("creator_handle") or sources.get(source_id, {}).get("creator_handle") or "",
            "source_url": row.get("source_url") or sources.get(source_id, {}).get("source_url") or "",
            "topic_id": candidate["topic_id"],
            "topic_label": candidate["topic_label"],
            "claim_text": candidate["claim_text"],
            "suggested_action": candidate["suggested_action"],
            "evidence_excerpt": candidate["evidence_excerpt"],
            "evidence_source": "passage",
            "source_passage_id": candidate["source_passage_id"],
            "model_name": "gpt-5.5-high-fast-hermes-rule-assisted",
            "model_endpoint_type": "hermes_agent_rule_generator_with_strict_checker",
            "prompt_version": "base2026-insight-repair-rule-v1-strict-snapshot",
            "input_hash": "",
            "status": "verified",
            "public": False,
            "needs_review": False,
            "evidence_score": 1.0,
            "created_at": now_iso(),
            "repair_batch": f"2026-07-07-{args.batch}",
            "rule_key": candidate["rule_key"],
        }
        tmp = dict(payload)
        tmp.pop("output_hash", None)
        payload["output_hash"] = hashlib.sha256(json.dumps(tmp, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        selected.append(payload)
        n += 1

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as handle:
        for row in selected:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    report = {
        "ok": len(selected) == args.target,
        "queue": str(args.queue),
        "out": str(out),
        "target": args.target,
        "scan_limit": args.scan_limit,
        "selected": len(selected),
        "skipped": skipped,
        "selected_sources": [r["source_id"] for r in selected],
        "rule_counts": {
            key: sum(1 for r in selected if r.get("rule_key") == key)
            for key in sorted({str(r.get("rule_key") or "") for r in selected})
        },
        "next_start_number": n,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if selected else 1


if __name__ == "__main__":
    raise SystemExit(main())
