from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from html import escape, unescape
from pathlib import Path
from urllib.parse import urlencode


STYLE_VERSION = "20260627-bing-cookie-compact-v1"
CONTACT_EMAIL = "offflinerpsy@gmail.com"
FONT_LINK = "https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500;600;700&family=Geist:wght@400;500;600;700;800&display=swap"
FAVICON_ASSET_PATH = "static/assets/alex-yarosh-favicon-32.png"
APPLE_TOUCH_ASSET_PATH = "static/assets/alex-yarosh-apple-touch.png"
SOCIAL_IMAGE_URL = "https://aggressorbulkit.online/knowledge/static/assets/alex-yarosh-avatar.png"
SOCIAL_IMAGE_ALT = "Alex Yarosh profile photo"
TWITTER_SITE = "@AleksejAros"
PROJECT_NAV_LINKS = [
    ("search", "Search", ""),
    ("analytics", "Analytics", "analytics.html"),
    ("api", "API", "api.html"),
    ("apply", "Apply Research", "apply-research.html"),
    ("solutions", "AI Recommends", "solutions/"),
    ("ai_visibility_pages", "AI Visibility Lab", "ai-visibility-pages/"),
    ("creators", "Creators", "creators/"),
    ("methodology", "Methodology", "methodology.html"),
]
PUBLISHED_TOPIC_IDS: set[str] = set()
FOOTER_LINKS = [
    ("Roadmap", "../roadmap.html"),
    ("Methodology", "../methodology.html"),
    ("Source policy", "../source-policy.html"),
    ("Privacy", "../privacy.html"),
    ("Support", "../support.html"),
    ("Creator Correction / Removal", "../opt-out.html"),
]


def favicon_links(relative_root: str) -> str:
    return "\n".join(
        [
            f'    <link rel="icon" type="image/png" sizes="32x32" href="{relative_root}/{FAVICON_ASSET_PATH}" />',
            f'    <link rel="apple-touch-icon" sizes="180x180" href="{relative_root}/{APPLE_TOUCH_ASSET_PATH}" />',
        ]
    )


def social_meta_tags(title: str, description: str, canonical: str, og_type: str = "website") -> str:
    url = canonical or "https://aggressorbulkit.online/knowledge/"
    return "\n".join(
        [
            f'    <meta property="og:type" content="{escape(og_type)}" />',
            '    <meta property="og:site_name" content="Base2026" />',
            '    <meta property="og:locale" content="en_US" />',
            f'    <meta property="og:title" content="{escape(title)}" />',
            f'    <meta property="og:description" content="{escape(description)}" />',
            f'    <meta property="og:url" content="{escape(url)}" />',
            f'    <meta property="og:image" content="{escape(SOCIAL_IMAGE_URL)}" />',
            f'    <meta property="og:image:alt" content="{escape(SOCIAL_IMAGE_ALT)}" />',
            '    <meta name="twitter:card" content="summary_large_image" />',
            f'    <meta name="twitter:site" content="{escape(TWITTER_SITE)}" />',
            f'    <meta name="twitter:title" content="{escape(title)}" />',
            f'    <meta name="twitter:description" content="{escape(description)}" />',
            f'    <meta name="twitter:image" content="{escape(SOCIAL_IMAGE_URL)}" />',
        ]
    )
INSIGHT_STOPWORDS = {
    "about",
    "above",
    "after",
    "again",
    "against",
    "also",
    "because",
    "been",
    "being",
    "between",
    "could",
    "does",
    "doing",
    "from",
    "have",
    "having",
    "into",
    "more",
    "most",
    "need",
    "only",
    "other",
    "same",
    "should",
    "source",
    "that",
    "their",
    "them",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "when",
    "where",
    "which",
    "while",
    "with",
    "would",
    "your",
}
INSIGHT_ANCHOR_TOKENS = {
    "access",
    "authority",
    "brand",
    "citation",
    "content",
    "creator",
    "ecommerce",
    "evidence",
    "freshness",
    "google",
    "government",
    "keyword",
    "link",
    "mention",
    "model",
    "page",
    "query",
    "recommendation",
    "retrieval",
    "risk",
    "search",
    "security",
    "seo",
    "signal",
    "source",
    "topic",
    "traffic",
    "visibility",
}


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def slug(value: str, fallback: str = "record") -> str:
    out = "-".join(re.findall(r"[a-z0-9]+", (value or "").lower()))
    return out[:120] or fallback


def compact(value: str, limit: int = 520) -> str:
    text = re.sub(r"\s+", " ", unescape(value or "")).strip()
    if not limit or len(text) <= limit:
        return text
    candidate = text[: max(limit - 3, 0)].rstrip()
    sentence_cut = max(candidate.rfind(". "), candidate.rfind("? "), candidate.rfind("! "))
    if sentence_cut >= max(80, int(limit * 0.55)):
        candidate = candidate[: sentence_cut + 1].rstrip()
    else:
        word_cut = candidate.rfind(" ")
        if word_cut >= max(40, int(limit * 0.65)):
            candidate = candidate[:word_cut].rstrip()
    return candidate.rstrip(" ,;:.") + "..."


def seo_title_with_suffix(value: str, suffix: str, limit: int = 65) -> str:
    return f"{compact(value, max(8, limit - len(suffix)))}{suffix}"[:limit]


def compact_words(value: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", unescape(value or "")).strip()
    if len(text) <= limit:
        return text
    candidate = text[:limit].rstrip(" ,;:.-")
    word_cut = candidate.rfind(" ")
    return candidate[:word_cut].rstrip(" ,;:.-") if word_cut >= max(8, limit // 2) else candidate


def format_count(value: object) -> str:
    try:
        return f"{int(value or 0):,}"
    except (TypeError, ValueError):
        return "0"


def clean_handle(value: str | None, fallback: str = "creator") -> str:
    handle = re.sub(r"\s+", "", str(value or "").strip()).lstrip("@")
    return handle or fallback


def display_handle(value: str | None, fallback: str = "creator") -> str:
    return f"@{clean_handle(value, fallback)}"


def paragraphize(value: str, limit: int = 900, sentences_per_paragraph: int = 2) -> str:
    text = compact(value, limit)
    if not text:
        return '<p class="empty-state">No public excerpt is available for this source yet.</p>'
    if len(text) > 80 and not re.search(r'[.!?…]"?$', text):
        text = text.rstrip(" ,;:.") + "..."
    sentences = re.split(r"(?<=[.!?])\s+", text)
    paragraphs: list[str] = []
    for index in range(0, len(sentences), sentences_per_paragraph):
        chunk = " ".join(part for part in sentences[index : index + sentences_per_paragraph] if part).strip()
        if chunk:
            paragraphs.append(f"<p>{escape(chunk)}</p>")
    return "".join(paragraphs) or f"<p>{escape(text)}</p>"


def readable_text_blocks(
    value: str,
    sentences_per_paragraph: int = 3,
    max_chars: int = 520,
    max_words: int = 74,
) -> list[str]:
    text = unescape(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return []
    source_blocks = [re.sub(r"[ \t]+", " ", block).strip() for block in re.split(r"\n{2,}", text)]
    source_blocks = [block for block in source_blocks if block]
    blocks: list[str] = []

    def push_word_chunks(text_value: str) -> None:
        words = compact(text_value, 0).split()
        for index in range(0, len(words), max_words):
            chunk = " ".join(words[index : index + max_words]).strip()
            if chunk:
                blocks.append(chunk)

    for source_block in source_blocks:
        block = compact(source_block, 0)
        if not block:
            continue
        sentences = re.findall(r"[^.!?…]+[.!?…]+(?=\s|$)|[^.!?…]+$", block) or [block]
        if len(sentences) <= 1 and len(block) > max_chars:
            push_word_chunks(block)
            continue
        current = ""
        sentence_count = 0
        for sentence in sentences:
            clean = compact(sentence, 0)
            if not clean:
                continue
            if len(clean) > max_chars:
                if current:
                    blocks.append(current)
                current = ""
                sentence_count = 0
                push_word_chunks(clean)
                continue
            next_value = compact(f"{current} {clean}", 0)
            if current and (len(next_value) > max_chars or sentence_count >= sentences_per_paragraph):
                blocks.append(current)
                current = clean
                sentence_count = 1
                continue
            current = next_value
            sentence_count += 1
        if current:
            blocks.append(current)
    return blocks


def paragraphize_full(value: str, sentences_per_paragraph: int = 3) -> str:
    blocks = readable_text_blocks(value, sentences_per_paragraph)
    if not blocks:
        return '<p class="empty-state">No public source text is available for this source yet.</p>'
    return "".join(f"<p>{escape(block)}</p>" for block in blocks)


def strip_evidence_markup(value: str) -> str:
    return compact(re.sub(r"<[^>]+>", " ", unescape(value or "")), 0)


def evidence_fingerprint(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", strip_evidence_markup(value).lower()).strip()


def same_evidence(first_value: str, second_value: str) -> bool:
    first = evidence_fingerprint(first_value)
    second = evidence_fingerprint(second_value)
    if not first or not second:
        return False
    short = first if len(first) <= len(second) else second
    long = second if len(first) <= len(second) else first
    if len(short) < 120:
        return first == second
    return long.startswith(short[:240]) or short.startswith(long[:240])


def evidence_starts_with(value: str, prefix: str) -> bool:
    text = evidence_fingerprint(value)
    lead = evidence_fingerprint(prefix)
    if not text or not lead or len(lead) < 40:
        return False
    return text.startswith(lead) or lead.startswith(text)


def evidence_contains_fragment(fragment_value: str, full_value: str) -> bool:
    fragment = evidence_fingerprint(fragment_value)
    full = evidence_fingerprint(full_value)
    if not fragment or not full:
        return False
    if len(fragment) < 80:
        return fragment == full
    return fragment in full or full in fragment


def is_fragmentary_evidence(value: str) -> bool:
    text = compact(strip_evidence_markup(value), 0)
    if not text:
        return False
    if is_clipped_evidence(text):
        return True
    first_word = re.sub(r"^[^A-Za-z0-9]+", "", text).split(" ", 1)[0]
    if first_word and first_word[0].islower():
        return True
    return bool(re.match(r"^(?:and|or|but|so|then|because|when|while|that|this|it|they|you|we)\b", text, re.I))


def insight_token_set(*values: str) -> set[str]:
    text = evidence_fingerprint(" ".join(value or "" for value in values))
    tokens: set[str] = set()
    for raw_token in text.split():
        token = raw_token
        if token in INSIGHT_STOPWORDS:
            continue
        if len(token) < 3 and token not in {"ai"}:
            continue
        for suffix in ("ing", "ed", "es", "s"):
            if len(token) > len(suffix) + 4 and token.endswith(suffix):
                token = token[: -len(suffix)]
                break
        if token and token not in INSIGHT_STOPWORDS:
            tokens.add(token)
    return tokens


def insight_signature(row: dict) -> set[str]:
    return insight_token_set(
        row.get("topic") or "",
        row.get("topic_id") or "",
        row.get("claim_text") or "",
        row.get("suggested_action") or "",
        row.get("evidence_excerpt") or "",
    )


def insight_rows_related(first: dict, second: dict) -> bool:
    first_topic = first.get("topic_id") or slug(first.get("topic") or "")
    second_topic = second.get("topic_id") or slug(second.get("topic") or "")
    if first_topic and first_topic == second_topic:
        return True
    first_tokens = insight_signature(first)
    second_tokens = insight_signature(second)
    if not first_tokens or not second_tokens:
        return False
    shared = first_tokens & second_tokens
    overlap = len(shared) / max(1, min(len(first_tokens), len(second_tokens)))
    if len(shared) >= 5 and overlap >= 0.18:
        return True
    if len(shared & INSIGHT_ANCHOR_TOKENS) >= 3 and len(shared) >= 4:
        return True
    first_topic_tokens = insight_token_set(first.get("topic") or first_topic)
    second_topic_tokens = insight_token_set(second.get("topic") or second_topic)
    return bool(first_topic_tokens & second_topic_tokens) and len(shared) >= 4


def group_insight_rows(rows: list[dict]) -> list[list[dict]]:
    groups: list[list[dict]] = []
    for row in rows:
        for group in groups:
            if any(insight_rows_related(row, existing) for existing in group):
                group.append(row)
                break
        else:
            groups.append([row])
    return groups


def sentence_excerpt(value: str, limit: int = 420, max_sentences: int = 3) -> str:
    text = strip_evidence_markup(value)
    if not text:
        return ""
    sentences = re.findall(r"[^.!?]+[.!?]+(?:\s|$)|[^.!?]+$", text) or [text]
    picked: list[str] = []
    length = 0
    for sentence in sentences:
        clean = compact(sentence, 0)
        if not clean:
            continue
        if len(picked) >= max_sentences:
            break
        if length and length + len(clean) > limit:
            break
        picked.append(clean)
        length += len(clean) + 1
    excerpt = compact(" ".join(picked), 0) or text
    if len(excerpt) <= limit:
        return excerpt
    clipped = excerpt[: max(limit - 3, 0)].rsplit(" ", 1)[0].strip()
    return f"{clipped or excerpt[: max(limit - 3, 0)].strip()}..."


def public_source_excerpt(source: dict, passages: list[dict]) -> str:
    for row in passages:
        body = unescape(row.get("body") or "").strip()
        if body:
            return body
    return unescape(source.get("excerpt") or "")


def source_evidence_text(source: dict, passages: list[dict], public_insights: list[dict]) -> str:
    for row in public_insights:
        evidence = expanded_insight_evidence(row, passages)
        if evidence:
            return evidence
    return public_source_excerpt(source, passages)


def is_clipped_evidence(value: str) -> bool:
    return bool(re.search(r"(?:\.{3}|\u2026)\s*$", compact(value, 0)))


def expanded_insight_evidence(row: dict, passages: list[dict]) -> str:
    evidence = strip_evidence_markup(row.get("evidence_excerpt") or "")
    if not evidence:
        return ""
    if not is_clipped_evidence(evidence):
        return evidence
    for passage in passages:
        body = passage.get("body") or passage.get("excerpt") or ""
        if body and same_evidence(evidence, body):
            return strip_evidence_markup(body)
    fallback = public_source_excerpt({}, passages)
    if fallback:
        return strip_evidence_markup(fallback)
    return re.sub(r"(?:\.{3}|\u2026)\s*$", ".", evidence).strip()


def source_public_text(source: dict, passages: list[dict]) -> str:
    text = unescape(source.get("public_source_text") or "").strip()
    if text:
        return text
    return public_source_excerpt(source, passages)


def source_intelligence_lead(source: dict, public_insights: list[dict]) -> str:
    if public_insights:
        claim = public_insights[0].get("claim_text") or public_insights[0].get("topic") or "reviewed public insight"
        return compact(f"Reviewed source-backed insight: {claim}", 220)
    return source.get("source_summary_short") or "Attributed source record from the searchable Base2026 video knowledge base."


def should_show_summary_long(summary_long: str, summary_short: str, public_text: str) -> bool:
    if not summary_long or summary_long == summary_short:
        return False
    if same_evidence(summary_long, public_text):
        return False
    if summary_short and (same_evidence(summary_long, summary_short) or evidence_starts_with(summary_long, summary_short)):
        return False
    return True


def evidence_qa_item(question: str, answer: str) -> str:
    question = compact(question, 160)
    answer = compact(answer, 640)
    if not question or len(answer) < 45:
        return ""
    return f"""
        <article class="evidence-qa-card">
          <h3>{escape(question)}</h3>
          <p>{escape(answer)}</p>
        </article>
    """


def evidence_qa_section(title: str, helper: str, rows: list[tuple[str, str]]) -> str:
    cards = [evidence_qa_item(question, answer) for question, answer in rows]
    cards = [card_html for card_html in cards if card_html]
    if len(cards) < 2:
        return ""
    return f"""
      <section class="content-section evidence-qa-section">
        {section_title(title, helper)}
        <div class="evidence-qa-grid">{"".join(cards[:4])}</div>
      </section>
    """


def source_answer_section(
    source: dict,
    public_insights: list[dict],
    passages: list[dict],
) -> str:
    if not public_insights:
        return ""
    handle = display_handle(source.get("creator_handle") or source.get("handle") or "creator")
    date = source.get("published_date") or source.get("published_at") or "undated"
    primary = public_insights[0]
    primary_claim = compact(primary.get("claim_text") or "", 260)
    primary_action = compact(primary.get("suggested_action") or "", 320)
    primary_evidence = compact(expanded_insight_evidence(primary, passages), 360)
    insight_topics = []
    seen_topics = set()
    for row in public_insights:
        label = compact(row.get("topic") or row.get("topic_label") or "", 80)
        key = label.casefold()
        if label and key not in seen_topics:
            insight_topics.append(label)
            seen_topics.add(key)
    rows = [
        (
            "What is this source mainly about?",
            primary_claim,
        ),
        (
            "What should an operator take from it?",
            primary_action,
        ),
        (
            "What public evidence supports the record?",
            primary_evidence,
        ),
        (
            "How is this source attributed?",
            f"Base2026 attributes this public source record to {handle}, published {date}, with the original platform link and correction/removal path kept on the page.",
        ),
    ]
    if insight_topics:
        rows.insert(
            2,
            (
                "Which topics does it connect to?",
                "This source is connected to " + ", ".join(insight_topics[:5]) + ".",
            ),
        )
    return evidence_qa_section(
        "Questions this source answers",
        "Short Base2026 answers generated only from reviewed Source Intelligence cards and attribution metadata.",
        rows,
    )


def topic_answer_section(
    topic: dict,
    public_insights: list[dict],
    related_sources: list[dict],
    creator_rows: list[dict],
    signal_brief: dict | None,
) -> str:
    topic_id = topic.get("topic_id") or slug(topic.get("topic") or "uncategorized")
    label = topic.get("topic") or topic_id.replace("-", " ").title()
    definition = topic.get("definition") or f"Source-backed creator evidence related to {label}."
    repeated_tactics = (signal_brief or {}).get("repeated_tactics") or []
    source_actions = (signal_brief or {}).get("source_backed_actions") or []
    creator_angles = (signal_brief or {}).get("creator_angles") or []
    top_claims = [compact(row.get("claim_text") or "", 220) for row in public_insights if row.get("claim_text")]
    tactic_answer = "; ".join(
        compact(row.get("label") or "", 170)
        for row in repeated_tactics[:3]
        if row.get("label")
    )
    if not tactic_answer and top_claims:
        tactic_answer = "; ".join(top_claims[:3])
    action_answer = "; ".join(
        compact(row.get("action") or "", 180)
        for row in source_actions[:3]
        if row.get("action")
    )
    creator_answer = "; ".join(
        f"{display_handle(row.get('creator_handle'))}: {compact(row.get('main_angle') or '', 150)}"
        for row in creator_angles[:3]
        if row.get("main_angle")
    )
    source_count = topic.get("source_count") or len(related_sources)
    creator_count = topic.get("creator_count") or len(creator_rows)
    insight_count = topic.get("public_insight_count") or len(public_insights)
    rows = [
        (f"What does {label} mean in this evidence set?", definition),
        (
            f"What do creators repeatedly say about {label}?",
            tactic_answer or f"Base2026 has public source records and insight cards connected to {label}, but repeated tactics are still being reviewed.",
        ),
        (
            "What should an SEO or AI visibility operator inspect first?",
            action_answer or (top_claims[0] if top_claims else definition),
        ),
        (
            "How strong is the public evidence?",
            f"This topic currently has {source_count} source records, {insight_count} public insight cards, and {creator_count} creators in the public Base2026 export.",
        ),
    ]
    if creator_answer:
        rows.insert(2, ("Which creator viewpoints are visible?", creator_answer))
    return evidence_qa_section(
        "Questions this topic answers",
        "Compact answers derived from public topic metadata, reviewed insight cards, and deterministic topic signal briefs.",
        rows,
    )


def icon_svg(name: str) -> str:
    icons = {
        "sparkle": '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 2.8l1.2 4.1a4.7 4.7 0 0 0 3.2 3.2l4.1 1.2-4.1 1.2a4.7 4.7 0 0 0-3.2 3.2L12 19.8l-1.2-4.1a4.7 4.7 0 0 0-3.2-3.2l-4.1-1.2 4.1-1.2a4.7 4.7 0 0 0 3.2-3.2L12 2.8z"/><path d="M18.5 15.8l.5 1.7a2 2 0 0 0 1.3 1.3l1.7.5-1.7.5a2 2 0 0 0-1.3 1.3l-.5 1.7-.5-1.7a2 2 0 0 0-1.3-1.3l-1.7-.5 1.7-.5a2 2 0 0 0 1.3-1.3l.5-1.7z"/></svg>',
        "share": '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M18 15.6a3.3 3.3 0 0 0-2.6 1.3l-6.1-3.5c.1-.4.1-.8 0-1.2l6-3.4A3.4 3.4 0 1 0 14.4 7l-6 3.4a3.4 3.4 0 1 0 0 4.8l6.1 3.5a3.4 3.4 0 1 0 3.5-3.1z"/></svg>',
        "link": '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M9.2 14.8a1 1 0 0 1 0-1.4l4.2-4.2a1 1 0 0 1 1.4 1.4l-4.2 4.2a1 1 0 0 1-1.4 0z"/><path d="M8.4 18.4a4.2 4.2 0 0 1-3-7.2l2.1-2.1a1 1 0 0 1 1.4 1.4l-2.1 2.1a2.2 2.2 0 1 0 3.1 3.1l2.1-2.1a1 1 0 0 1 1.4 1.4l-2.1 2.1a4.2 4.2 0 0 1-2.9 1.3z"/><path d="M15.8 13.2a1 1 0 0 1-.7-1.7l2.1-2.1a2.2 2.2 0 0 0-3.1-3.1L12 8.4A1 1 0 0 1 10.6 7l2.1-2.1a4.2 4.2 0 0 1 5.9 5.9l-2.1 2.1a1 1 0 0 1-.7.3z"/></svg>',
        "copy": '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M8 7a3 3 0 0 1 3-3h6a3 3 0 0 1 3 3v6a3 3 0 0 1-3 3h-6a3 3 0 0 1-3-3V7zm3-1a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V7a1 1 0 0 0-1-1h-6z"/><path d="M4 11a3 3 0 0 1 3-3 1 1 0 1 1 0 2 1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1 1 1 0 1 1 2 0 3 3 0 0 1-3 3H7a3 3 0 0 1-3-3v-6z"/></svg>',
        "print": '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M7 3h10a2 2 0 0 1 2 2v3h1a3 3 0 0 1 3 3v5a2 2 0 0 1-2 2h-2v1a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-1H3a2 2 0 0 1-2-2v-5a3 3 0 0 1 3-3h1V5a2 2 0 0 1 2-2zm0 5h10V5H7v3zm0 8v3h10v-3H7zm12 0h2v-5a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1v5h2v-1a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v1z"/></svg>',
        "calendar": '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M7 2a1 1 0 0 1 1 1v1h8V3a1 1 0 1 1 2 0v1h1a3 3 0 0 1 3 3v11a3 3 0 0 1-3 3H5a3 3 0 0 1-3-3V7a3 3 0 0 1 3-3h1V3a1 1 0 0 1 1-1zm13 8H4v8a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-8zM5 6a1 1 0 0 0-1 1v1h16V7a1 1 0 0 0-1-1H5z"/></svg>',
        "card": '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M4 5a3 3 0 0 1 3-3h10a3 3 0 0 1 3 3v14a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V5zm3-1a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V5a1 1 0 0 0-1-1H7zm2 4h6a1 1 0 1 1 0 2H9a1 1 0 0 1 0-2zm0 4h6a1 1 0 1 1 0 2H9a1 1 0 0 1 0-2zm0 4h3a1 1 0 1 1 0 2H9a1 1 0 0 1 0-2z"/></svg>',
        "topic": '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M4 5a3 3 0 0 1 3-3h3.6a3 3 0 0 1 2.1.9l8.4 8.4a3 3 0 0 1 0 4.2l-5.6 5.6a3 3 0 0 1-4.2 0l-8.4-8.4A3 3 0 0 1 2 10.6V7a3 3 0 0 1 2-2zm3-.9A1 1 0 0 0 6 5v5.6a1 1 0 0 0 .3.7l8.4 8.4a1 1 0 0 0 1.4 0l5.6-5.6a1 1 0 0 0 0-1.4L13.3 4.3a1 1 0 0 0-.7-.3H7z"/><path d="M8.5 8.8a1.3 1.3 0 1 1 0-2.6 1.3 1.3 0 0 1 0 2.6z"/></svg>',
    }
    return icons.get(name, "")


def tiktok_logo_svg() -> str:
    return (
        '<svg class="platform-logo platform-logo--tiktok" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
        '<path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/>'
        "</svg>"
    )


def platform_icon_only(platform: str | None = "tiktok") -> str:
    if "tiktok" in str(platform or "").lower():
        return f'<span class="platform-icon-only" title="TikTok source" aria-label="TikTok source">{tiktok_logo_svg()}</span>'
    return f'<span class="platform-text">{escape(platform or "source")}</span>'


def share_action_buttons(kind: str = "source") -> str:
    actions = [
        ("share", "share", "Share", f"Share {kind}"),
        ("copy-link", "link", "Copy link", f"Copy {kind} link"),
        ("copy-citation", "copy", "Copy citation", "Copy citation"),
        ("print", "print", "Save PDF", "Save as PDF"),
    ]
    return "".join(
        f'<button type="button" class="source-share-action" data-share-action="{escape(action)}" '
        f'aria-label="{escape(aria)}" title="{escape(title)}">{icon_svg(icon)}</button>'
        for action, icon, title, aria in actions
    )


def share_action_bar(label: str = "Share this page", kind: str = "page") -> str:
    return (
        f'<section class="share-actions share-actions--compact" data-share-root aria-label="{escape(label)}">'
        f'<span class="source-share-actions__label">{escape(label)}</span>'
        f'{share_action_buttons(kind)}'
        '<span class="share-actions__status source-share-actions__status" data-share-status aria-live="polite"></span>'
        '</section>'
    )


def source_share_action_bar(label: str = "Share source record", kind: str = "source record") -> str:
    return (
        f'<div class="source-share-actions" data-share-root aria-label="{escape(label)}">'
        f'<span class="source-share-actions__label">{escape(label)}</span>'
        f'{share_action_buttons(kind)}'
        '<span class="share-actions__status source-share-actions__status" data-share-status aria-live="polite"></span>'
        '</div>'
    )


def source_quick_meta(public_policy: str, insight_count: int, platform: str = "tiktok", language: str = "en") -> str:
    insight_item = (
        f'<span class="source-meta-inline" title="Public insight cards">{icon_svg("card")}<strong>{escape(str(insight_count))}</strong></span>'
        if insight_count
        else ""
    )
    return (
        '<div class="source-hero-quick-meta" aria-label="Source metadata">'
        f'<span class="source-meta-inline" title="Platform">{platform_icon_only(platform)}<span>{escape((platform or "source").replace("_", " ").title())}</span></span>'
        f'<span class="source-meta-inline" title="Public policy">{escape(public_policy)}</span>'
        f'<span class="source-meta-inline" title="Language">{escape(language or "en")}</span>'
        f'{insight_item}'
        '</div>'
    )


def inline_share_actions(label: str, kind: str = "page") -> str:
    return (
        f'<div class="source-share-actions source-share-actions--inline" data-share-root aria-label="{escape(label)}">'
        f'{share_action_buttons(kind)}'
        '<span class="share-actions__status source-share-actions__status" data-share-status aria-live="polite"></span>'
        '</div>'
    )


def info_hint(label: str, text: str) -> str:
    safe_label = escape(label)
    safe_text = escape(text)
    return (
        f'<span class="info-hint" tabindex="0" role="note" '
        f'aria-label="{safe_label}: {safe_text}" data-tooltip="{safe_text}">i</span>'
    )


def section_title(label: str, tooltip: str) -> str:
    return f'<div class="section-title-row"><h2>{escape(label)}</h2>{info_hint(label, tooltip)}</div>'


def root_href(relative_root: str, target: str) -> str:
    root = relative_root.rstrip("/")
    if not target:
        return f"{root}/"
    return f"{root}/{target.lstrip('/')}"


def base2026_dropdown(relative_root: str, current: str = "") -> str:
    links = []
    for key, label, target in PROJECT_NAV_LINKS:
        active = ' aria-current="page"' if key == current else ""
        links.append(f'<a href="{escape(root_href(relative_root, target))}"{active}>{escape(label)}</a>')
    return f"""
          <div class="site-header__base">
            <a class="site-header__link site-header__link--base2026" href="{escape(root_href(relative_root, ''))}" aria-haspopup="true">Base2026</a>
            <div class="site-header__base-menu" aria-label="Base2026 navigation">
              <span>Base2026 Library</span>
              {''.join(links)}
            </div>
          </div>
"""


def header_nav_links(relative_root: str, current: str = "") -> str:
    project_links = []
    for key, label, target in PROJECT_NAV_LINKS:
        active = ' aria-current="page"' if key == current else ""
        project_links.append(f'<a class="site-header__link" href="{escape(root_href(relative_root, target))}"{active}>{escape(label)}</a>')
    return (
        "".join(project_links)
        + '<span class="site-header__nav-divider" aria-hidden="true"></span>'
        + '<a class="site-header__link site-header__link--site" href="/services/">Services</a>'
        + '<a class="site-header__link site-header__link--site" href="/pricing/">Pricing</a>'
        + '<a class="site-header__link site-header__link--site" href="/about/">About</a>'
    )


def mobile_base2026_links(relative_root: str, current: str = "") -> str:
    links = []
    for key, label, target in PROJECT_NAV_LINKS:
        active = ' aria-current="page"' if key == current else ""
        links.append(f'<a href="{escape(root_href(relative_root, target))}"{active}>{escape(label)}</a>')
    return "".join(links)


def site_header(relative_root: str, current: str = "") -> str:
    return f"""
    <header class="site-header">
      <div class="site-header__bar">
        <a class="site-header__brand" href="/"><span class="site-header__avatar" aria-hidden="true"></span><span>Alex Yarosh</span></a>
        <nav class="site-header__nav" aria-label="Base2026 navigation">
          {header_nav_links(relative_root, current)}
        </nav>
        <a class="site-header__cta" href="/ai-visibility-audit/">Check My AI Visibility</a>
        <details class="site-header__mobile-menu">
          <summary aria-label="Open navigation"><span></span><span></span><span></span></summary>
          <div class="site-header__mobile-panel">
            <nav aria-label="Mobile navigation">
              <details class="site-header__mobile-base" open>
                <summary>Base2026</summary>
                <div>{mobile_base2026_links(relative_root, current)}</div>
              </details>
              <strong class="mobile-menu-label">Alex Yarosh</strong>
              <a href="/services/">Services</a>
              <a href="/pricing/">Pricing</a>
              <a href="/about/">About</a>
              <a class="site-header__mobile-cta" href="/ai-visibility-audit/">Check My AI Visibility</a>
            </nav>
          </div>
        </details>
      </div>
    </header>
"""


def base2026_breadcrumbs(relative_root: str, title: str) -> str:
    current = (title.split("|", 1)[0] or "Current page").strip()
    return f"""
      <nav class="breadcrumbs" aria-label="Breadcrumb">
        <a href="{escape(root_href(relative_root, ''))}">Base2026</a>
        <span aria-hidden="true">/</span>
        <span aria-current="page">{escape(current)}</span>
      </nav>
"""


def cookie_consent_markup(relative_root: str) -> str:
    return f"""
    <section class="cookie-banner" data-cookie-banner hidden aria-label="Cookie preferences">
      <div>
        <h2>Cookie preferences</h2>
        <p>We use necessary cookies to run the site and optional cookies to understand what pages are useful. You can accept all, reject non-essential cookies, or manage preferences.</p>
      </div>
      <div class="cookie-actions">
        <button type="button" class="ay-button" data-cookie-accept>Accept All</button>
        <button type="button" class="ay-button-secondary" data-cookie-reject>Reject Non-Essential</button>
        <button type="button" class="ay-button-secondary" data-cookie-manage>Manage Preferences</button>
      </div>
    </section>
    <dialog class="cookie-dialog" data-cookie-dialog aria-label="Manage cookie preferences">
      <form method="dialog">
        <div class="cookie-dialog-head">
          <p class="eyebrow">Privacy controls</p>
          <h2>Manage cookie preferences</h2>
          <p>Necessary cookies are always active because they keep the site working. Analytics and marketing cookies are optional and will only run if you allow them.</p>
        </div>
        <div class="cookie-options">
          <label><input type="checkbox" checked disabled> Necessary <span>Always on. Required for site operation, security, forms, and preference storage.</span></label>
          <label><input type="checkbox" data-cookie-analytics> Analytics <span>Optional. Not currently active. Reserved for privacy-friendly page usefulness analytics.</span></label>
          <label><input type="checkbox" data-cookie-marketing> Marketing <span>Optional. Not currently active. Reserved for future pixels only if explicitly enabled.</span></label>
        </div>
        <div class="cookie-actions">
          <button type="button" class="ay-button" data-cookie-save>Save Preferences</button>
          <button type="button" class="ay-button-secondary" data-cookie-close>Close</button>
        </div>
      </form>
    </dialog>
    <script src="{relative_root}/static/cookie-consent.js?v={STYLE_VERSION}" defer></script>
"""


def page_shell(
    title: str,
    body: str,
    relative_root: str = "..",
    robots: str = "index,follow",
    current: str = "",
    description: str = "",
    canonical_path: str = "",
    main_class: str = "app-shell content-page",
) -> str:
    description = compact(description or title, 180)
    canonical = f"https://aggressorbulkit.online/knowledge/{canonical_path.lstrip('/')}" if canonical_path else ""
    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": description,
        "url": canonical or "https://aggressorbulkit.online/knowledge/",
        "isPartOf": {
            "@type": "WebSite",
            "name": "Base2026",
            "url": "https://aggressorbulkit.online/knowledge/",
        },
    }
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content="{escape(description)}" />
    <meta name="robots" content="{escape(robots)}" />
    {f'<link rel="canonical" href="{escape(canonical)}" />' if canonical else ''}
{social_meta_tags(title, description, canonical)}
    <title>{escape(title)}</title>
    <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
{favicon_links(relative_root)}
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="{FONT_LINK}" rel="stylesheet" />
    <link rel="stylesheet" href="{relative_root}/static/styles.css?v={STYLE_VERSION}" />
  </head>
  <body>
    <a class="skip-link" href="#content">Skip to content</a>
    {site_header(relative_root, current)}
    <main id="content" class="{escape(main_class)}">
      {base2026_breadcrumbs(relative_root, title)}
      {body}
    </main>
    <footer class="site-footer">
      <div class="ay-wrap ay-footer-grid">
        <section>
          <p class="eyebrow">AI Search Visibility</p>
          <h2>Search visibility for local service businesses</h2>
          <p>We help local service businesses improve visibility across Google, ChatGPT, Gemini, Perplexity and AI-powered search through SEO, GEO, AEO, content, schema and trust signals.</p>
          <div class="ay-actions">
            <a class="ay-button" href="/ai-visibility-audit/">Get My Free Roadmap</a>
            <a class="ay-button-secondary" href="/pricing/">View Pricing</a>
            <a class="ay-button ay-button-base2026" href="/knowledge/">Base2026</a>
          </div>
          <div class="ay-footer-socials" aria-label="Social profiles">
            <p class="ay-footer-socials__label">Socials</p>
            <div class="ay-footer-socials__links">
              <a class="ay-social-link" href="https://x.com/AleksejAros" target="_blank" rel="me noopener noreferrer" aria-label="Alex Yarosh on X" title="X">
                <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M18.9 2h3.3l-7.2 8.2L23.5 22h-6.7l-5.2-6.8L5.6 22H2.3l7.7-8.8L1.9 2h6.8l4.7 6.2L18.9 2Zm-1.2 17.9h1.8L7.7 4H5.8l11.9 15.9Z"/></svg>
              </a>
              <span class="ay-social-link ay-social-link--disabled" aria-label="TikTok profile coming soon" title="TikTok profile coming soon">
                <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12.5 2c1.2 0 2.4 0 3.6-.1.1 1.5.6 2.9 1.7 4 1.1 1 2.5 1.5 4 1.7v3.8c-1.4 0-2.7-.3-4-.9-.5-.2-1-.5-1.5-.9v7.7c-.1 1.3-.5 2.6-1.3 3.7-1.2 1.8-3.3 3-5.5 3-1.3.1-2.7-.3-3.8-1-1.9-1.1-3.2-3.2-3.4-5.4v-1.4c.2-1.8 1-3.5 2.4-4.7 1.5-1.4 3.7-2 5.8-1.6v4.2c-.9-.3-2-.2-2.8.3-.6.4-1 1-1.3 1.7-.2.5-.1 1-.1 1.5.2 1.5 1.7 2.8 3.3 2.7 1 0 2-.6 2.6-1.5.2-.3.4-.6.4-1 .1-1.7.1-3.4.1-5.1V2Z"/></svg>
              </span>
              <a class="ay-social-link" href="https://github.com/offflinerpsy" target="_blank" rel="me noopener noreferrer" aria-label="Alex Yarosh on GitHub" title="GitHub">
                <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 .5A11.5 11.5 0 0 0 8.36 22.9c.58.11.8-.25.8-.56v-2.02c-3.25.71-3.94-1.38-3.94-1.38-.53-1.35-1.3-1.71-1.3-1.71-1.06-.73.08-.72.08-.72 1.18.08 1.8 1.21 1.8 1.21 1.04 1.79 2.74 1.27 3.41.97.11-.76.41-1.27.74-1.56-2.59-.29-5.31-1.3-5.31-5.76 0-1.27.45-2.31 1.2-3.13-.12-.29-.52-1.48.12-3.09 0 0 .98-.31 3.21 1.19A11.08 11.08 0 0 1 12 5.96c.99 0 1.98.13 2.91.39 2.22-1.5 3.2-1.19 3.2-1.19.64 1.61.24 2.8.12 3.09.75.82 1.2 1.86 1.2 3.13 0 4.47-2.73 5.46-5.33 5.75.42.36.79 1.08.79 2.17v3.04c0 .31.21.68.8.56A11.5 11.5 0 0 0 12 .5Z"/></svg>
              </a>
            </div>
          </div>
        </section>
        <nav aria-label="Footer services">
          <h3>Services</h3>
          <ul class="ay-footer-menu">
            <li><a href="/ai-visibility-diagnostic-audit/">AI Visibility Diagnostic Audit</a></li>
            <li><a href="/technical-seo-geo-foundation/">Technical SEO &amp; GEO Foundation</a></li>
            <li><a href="/answer-ready-service-pages/">Answer-Ready Service Pages</a></li>
            <li><a href="/entity-trust-source-intelligence/">Entity, Trust &amp; Source Intelligence</a></li>
            <li><a href="/services/#local-seo">Local SEO &amp; Citations</a></li>
            <li><a href="/services/#monitoring">AI Visibility Monitoring</a></li>
          </ul>
        </nav>
        <nav aria-label="Footer start here">
          <h3>Start Here</h3>
          <ul class="ay-footer-menu">
            <li><a href="/services/">Services</a></li>
            <li><a href="/pricing/">Pricing</a></li>
            <li><a href="/#how-it-works">Process / How It Works</a></li>
            <li><a href="/ai-visibility-audit/">Free AI Visibility Snapshot</a></li>
          </ul>
        </nav>
        <nav aria-label="Footer Base2026">
          <h3>Base2026 Pilot Project</h3>
          <p>Independent experimental startup product: a searchable knowledge base for short-form expert video.</p>
          <ul class="ay-footer-menu">
            <li><a href="{relative_root}/">Search Base2026</a></li>
            <li><a href="{relative_root}/analytics.html">Analytics</a></li>
            <li><a href="{relative_root}/api.html">API &amp; AI access</a></li>
            <li><a href="{relative_root}/apply-research.html">Apply research</a></li>
            <li><a href="{relative_root}/solutions/">AI Recommends Solutions</a></li>
            <li><a href="{relative_root}/ai-visibility-pages/">AI Visibility Lab</a></li>
            <li><a href="{relative_root}/ai-visibility-resources.html">AI Visibility Library</a></li>
            <li><a href="{relative_root}/roadmap.html">Roadmap</a></li>
            <li><a href="{relative_root}/topics/">Topics</a></li>
            <li><a href="{relative_root}/creators/">Creators</a></li>
            <li><a href="{relative_root}/story.html">Project Story</a></li>
            <li><a href="{relative_root}/methodology.html">Methodology</a></li>
            <li><a href="{relative_root}/support.html">Support</a></li>
          </ul>
        </nav>
        <nav aria-label="Footer legal and trust">
          <h3>Legal &amp; Trust</h3>
          <ul class="ay-footer-menu">
            <li><a href="/privacy-policy/">Privacy Policy</a></li>
            <li><button type="button" class="footer-link-button" data-cookie-preferences>Cookie Preferences</button></li>
            <li><a href="{relative_root}/source-policy.html">Source &amp; Content Policy</a></li>
            <li><a href="{relative_root}/opt-out.html">Creator Correction / Removal</a></li>
            <li><a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></li>
          </ul>
        </nav>
      </div>
      <div class="ay-footer-bottom">
        <span>&copy; 2026 Logic Crafts LLC, Kyrgyzstan. Base2026 was created by Alex Yarosh as an independent experimental startup product. It is not a marketing agency and not a marketing-services offering.</span>
      </div>
    </footer>
    <script src="{relative_root}/static/share-actions.js?v={STYLE_VERSION}" defer></script>
    {cookie_consent_markup(relative_root)}
  </body>
</html>
"""


def card(title: str, text: str, href: str | None = None, meta: str = "") -> str:
    link = f'<a class="button-link" href="{escape(href)}">Open</a>' if href else ""
    return f"""
      <article class="intelligence-card">
        <h3>{escape(title)}</h3>
        {f'<p class="meta">{escape(meta)}</p>' if meta else ''}
        <p>{escape(compact(text, 360))}</p>
        {link}
      </article>
    """


def source_insight_card(row_or_rows: dict | list[dict], passages: list[dict], public_text: str = "") -> str:
    rows = row_or_rows if isinstance(row_or_rows, list) else [row_or_rows]
    rows = [row for row in rows if row]
    if not rows:
        return ""
    primary = rows[0]
    claim_text = primary.get("claim_text") or primary.get("topic") or "Insight"

    topic_links: list[str] = []
    topic_labels: list[str] = []
    seen_topics: set[str] = set()
    for row in rows:
        topic_id = row.get("topic_id") or slug(row.get("topic") or "uncategorized")
        if topic_id in seen_topics:
            continue
        seen_topics.add(topic_id)
        topic_label = row.get("topic") or row.get("topic_id") or "Topic"
        topic_labels.append(topic_label)
        topic_links.append(
            f'<a class="topic-chip topic-tag" href="{escape(topic_href(topic_id))}">{escape(topic_label)}</a>'
        )
    meta = (
        f"{len(rows)} related signals · {' / '.join(topic_labels[:3])}"
        if len(rows) > 1
        else f"{topic_labels[0] if topic_labels else 'Topic'} · {primary.get('stance') or 'asserts'}"
    )

    actions: list[str] = []
    evidence_blocks: list[str] = []
    evidence_duplicate_count = 0
    seen_actions: list[str] = []
    seen_evidence: list[str] = []
    for row in rows:
        row_claim = row.get("claim_text") or row.get("topic") or "Insight"
        action = compact(row.get("suggested_action") or "", 0)
        if action and not same_evidence(action, row_claim) and not any(same_evidence(action, existing) for existing in seen_actions):
            seen_actions.append(action)
            actions.append(f"<li>{escape(action)}</li>")

        evidence = strip_evidence_markup(row.get("evidence_excerpt") or "")
        expanded_evidence = expanded_insight_evidence(row, passages)
        evidence_body = evidence or expanded_evidence
        if not evidence_body:
            continue
        evidence_is_source_fragment = (
            evidence_contains_fragment(evidence_body, public_text)
            or evidence_contains_fragment(evidence_body, row_claim)
        )
        evidence_is_duplicate = (
            same_evidence(evidence_body, public_text)
            or same_evidence(evidence_body, row_claim)
            or evidence_is_source_fragment
        )
        if evidence_is_duplicate:
            evidence_duplicate_count += 1
            continue
        if is_fragmentary_evidence(evidence_body):
            evidence_duplicate_count += 1
            continue
        if any(same_evidence(evidence_body, existing) for existing in seen_evidence):
            continue
        seen_evidence.append(evidence_body)
        evidence_preview = sentence_excerpt(evidence_body, 300, 2)
        evidence_blocks.append(f"<li>{paragraphize_full(evidence_preview or evidence_body)}</li>")

    action_html = f'<ul class="source-detail-insight__actions">{"".join(actions)}</ul>' if actions else ""
    evidence_html = ""
    if evidence_blocks:
        evidence_html = f"""
        <details class="source-detail-evidence">
          <summary>Show source evidence</summary>
          <div><ul class="source-detail-evidence-list">{"".join(evidence_blocks)}</ul></div>
        </details>
        """
    topics_html = (
        f'<div class="source-detail-topic-links" aria-label="Related topics">{"".join(topic_links)}</div>'
        if topic_links
        else ""
    )
    return f"""
      <article class="intelligence-card source-detail-insight">
        <h3>{escape(claim_text)}</h3>
        <p class="meta">{escape(meta)}</p>
        {action_html}
        {evidence_html}
        {topics_html}
      </article>
    """


def source_insight_cards(rows: list[dict], passages: list[dict], public_text: str = "") -> str:
    return "".join(source_insight_card(group, passages, public_text) for group in group_insight_rows(rows))


def source_intelligence_empty_state() -> str:
    return (
        '<p class="empty-state source-intelligence-empty">'
        "No reviewed Source Intelligence cards are published for this source yet. "
        "Base2026 only shows reviewed source-backed cards here; unreviewed candidates stay out of the public UI until evidence review."
        "</p>"
    )


def creator_index_card(handle: str, creator: dict, source_count: int, public_insight_count: int) -> str:
    visible_handle = display_handle(handle)
    avatar_html = creator_avatar_markup(visible_handle, creator.get("avatar_url") or "", relative_root="..")
    profile_href = f"{slug(handle)}.html"
    creator_url = creator.get("url") or ""
    external_link = (
        f'<a class="creator-index-card__source" href="{escape(creator_url)}" target="_blank" rel="noreferrer">TikTok profile</a>'
        if creator_url
        else ""
    )
    insight_label = "public insight" if public_insight_count == 1 else "public insights"
    source_label = "source record" if source_count == 1 else "source records"
    return f"""
      <article class="intelligence-card creator-index-card">
        <div class="creator-index-card__head">
          {avatar_html}
          <div>
            <h3>{escape(visible_handle)}</h3>
            <p class="meta">{escape(str(source_count))} {source_label} · {escape(str(public_insight_count))} {insight_label}</p>
          </div>
        </div>
        <p>Creator-level attribution profile with source records, public insight cards, topic distribution, and original-platform links.</p>
        <div class="creator-index-card__actions">
          <a class="button-link" href="{escape(profile_href)}">Open profile</a>
          {external_link}
        </div>
      </article>
    """


def is_truncated_metadata(value: str | None, status: str | None = "") -> bool:
    text = (value or "").strip()
    return bool(status == "truncated" or text.endswith("...") or text.endswith("…"))


def source_display_title(source: dict) -> str:
    handle = display_handle(source.get("creator_handle") or source.get("handle") or "Creator")
    title = source.get("title") or ""
    if title and not is_truncated_metadata(title, source.get("title_status")):
        return compact(title, 96)
    summary = compact(source.get("source_summary_short") or "", 96)
    if summary:
        return summary
    excerpt = compact(source.get("excerpt") or "", 96)
    if excerpt:
        return excerpt
    date = source.get("published_date") or source.get("published_at") or ""
    return f"{handle}{f' · {date}' if date else ''}"


def source_record_heading(source: dict) -> str:
    return display_handle(source.get("creator_handle") or source.get("handle") or "Creator")


def source_schema_name(source: dict) -> str:
    return f"{source_display_lead(source, 110)} — source {source_record_id(source)}"


def source_display_lead(source: dict, limit: int = 260) -> str:
    title = source.get("title") or ""
    if title and not is_truncated_metadata(title, source.get("title_status")):
        return compact(title, limit)
    return compact(
        source.get("source_summary_short")
        or source.get("excerpt")
        or source.get("source_id")
        or source.get("item_id")
        or "Source record",
        limit,
    )


def source_seo_topic(source: dict) -> str:
    labels = [label for label in (source.get("topic_labels") or []) if label]
    if labels:
        return labels[0]
    topics = [topic for topic in (source.get("topics") or []) if topic]
    if topics:
        return topics[0].replace("-", " ").title()
    return "creator evidence"


def source_record_id(source: dict) -> str:
    identity = " ".join(
        str(source.get(field) or "")
        for field in ("video_id", "item_id", "source_id", "source_url")
    )
    video_match = re.search(r"(?<!\d)(\d{10,30})(?!\d)", identity)
    return video_match.group(1)[-10:] if video_match else slug(identity, "source")[-10:]


def source_seo_title(source: dict, handle: str) -> str:
    topic = source_seo_topic(source)
    record_id = source_record_id(source)
    visible_handle = compact_words(handle, 18)
    suffix = f" · {record_id} | Base2026"
    topic_budget = max(8, 65 - len(visible_handle) - len(suffix) - 3)
    return f"{visible_handle} · {compact_words(topic, topic_budget)}{suffix}"[:65]


def source_seo_description(source: dict, handle: str) -> str:
    date = source.get("published_date") or source.get("published_at") or "undated"
    topic = source_seo_topic(source)
    record_id = source_record_id(source)
    excerpt = compact(source.get("source_summary_short") or source.get("excerpt") or "", 130)
    base = f"Base2026 source {record_id} by {handle}, published {date}: attributed public evidence about {topic}."
    if excerpt:
        return compact(f"{base} Excerpt: {excerpt}", 160)
    return compact(f"{base} Includes original-source attribution and correction controls.", 160)


def source_href(source: dict, prefix: str = "../sources") -> str:
    return f"{prefix}/{slug(source.get('item_id') or source.get('source_id'))}.html"


def source_has_public_evidence(source: dict, passages: list[dict] | None = None, insights: list[dict] | None = None) -> bool:
    if (source.get("public_source_text") or "").strip():
        return True
    if (source.get("excerpt") or "").strip():
        return True
    if passages:
        return True
    return any(row.get("public") for row in (insights or []))


def source_is_normal_public_card(source: dict) -> bool:
    state = source.get("admission_state")
    surface = source.get("public_surface")
    if state and state != "normal_public_card":
        return False
    if surface and surface != "main_search":
        return False
    return True


def is_indexable_source(source: dict, passages: list[dict] | None = None, insights: list[dict] | None = None) -> bool:
    """Require independent source-page value, not merely an excerpt.

    Weak/uncertain records remain available as attributed source archive pages with
    noindex,follow and may still contribute to stronger topic pages.
    """
    if not source_is_normal_public_card(source):
        return False
    public_insights = [row for row in (insights or []) if row.get("public")]
    topics = source.get("topics") or source.get("topic_labels") or []
    summary = (source.get("source_summary_short") or "").strip()
    source_url = (source.get("source_url") or "").strip()
    return bool(
        source_has_public_evidence(source, passages, public_insights)
        and passages
        and public_insights
        and topics
        and summary
        and source_url
        and source.get("full_transcript_public") is not True
    )


def creator_href(handle: str, prefix: str = "../creators") -> str:
    return f"{prefix}/{slug(handle)}.html"


def topic_href(topic_id: str, prefix: str = "../topics") -> str:
    topic_key = slug(topic_id, "uncategorized")
    if PUBLISHED_TOPIC_IDS and topic_key not in PUBLISHED_TOPIC_IDS:
        base = "../" if prefix.startswith("..") else "./"
        return workspace_href(base=base, topic=topic_id)
    return f"{prefix}/{topic_key}.html"


def workspace_href(base: str = "../", **params: str) -> str:
    query = urlencode({str(key): str(value).lstrip("@") for key, value in params.items() if value})
    return f"{base.rstrip('/')}/?{query}" if query else f"{base.rstrip('/')}/"


def topic_chips(topic_rows: list[tuple[str, str, int]], prefix: str = "../topics") -> str:
    chips = []
    for topic_id, label, count in topic_rows:
        suffix = f" · {count}" if count else ""
        chips.append(
            f'<a class="topic-chip topic-tag" href="{escape(topic_href(topic_id, prefix))}">{escape(label)}{escape(suffix)}</a>'
        )
    return "".join(chips)


def creator_avatar_markup(handle: str, avatar_url: str = "", relative_root: str = "..") -> str:
    label = clean_handle(handle)
    initial = (label[:1] or "B").upper()
    safe_avatar = avatar_url or ""
    if safe_avatar.startswith("/knowledge/static/"):
        safe_avatar = f"{relative_root.rstrip('/')}/static/{safe_avatar.split('/knowledge/static/', 1)[1]}"
    if safe_avatar:
        return (
            '<span class="avatar avatar--image creator-page-avatar">'
            f'<img src="{escape(safe_avatar)}" alt="@{escape(label)} TikTok profile avatar" loading="lazy" referrerpolicy="no-referrer" />'
            "</span>"
        )
    return f'<span class="avatar creator-page-avatar" aria-hidden="true">{escape(initial)}</span>'


def source_identity_markup(
    handle: str,
    avatar_html: str,
    date: str = "",
    platform: str = "tiktok",
    variant: str = "page",
) -> str:
    meta_items = []
    if date:
        meta_items.append(f'<span class="source-identity__date">{escape(date)}</span>')
    if platform and variant != "source":
        meta_items.append(platform_icon_only(platform))
    meta_html = "".join(meta_items)
    heading_tag = "p" if variant == "source" else "h1"
    return (
        f'<div class="source-identity source-identity--{escape(variant)}">'
        f'{avatar_html}'
        '<div class="source-identity__body">'
        '<div class="source-identity__line">'
        f'<{heading_tag} class="source-identity__handle">{escape(handle)}</{heading_tag}>'
        f'{meta_html}'
        '</div>'
        '</div>'
        '</div>'
    )


def is_indexable_topic(topic: dict) -> bool:
    return bool(topic.get("public")) and int(topic.get("public_insight_count") or 0) >= 2


def creator_page(handle: str, creator: dict, sources: list[dict], insights: list[dict]) -> str:
    visible_handle = display_handle(handle)
    safe_handle = escape(visible_handle)
    avatar_html = creator_avatar_markup(visible_handle, creator.get("avatar_url") or "")
    latest = [
        row
        for row in sorted(sources, key=lambda row: row.get("published_at") or "", reverse=True)
        if source_has_public_evidence(row)
    ][:12]
    public_insights = [row for row in insights if row.get("creator_handle") == handle and row.get("public")]
    topic_counts: dict[str, int] = defaultdict(int)
    topic_labels: dict[str, str] = {}
    for insight in public_insights:
        topic_id = insight.get("topic_id") or slug(insight.get("topic") or "uncategorized")
        topic_labels[topic_id] = insight.get("topic") or topic_id.replace("-", " ").title()
        topic_counts[topic_id] += 1
    topics = sorted(topic_counts.items(), key=lambda item: (-item[1], item[0]))[:12]
    topic_html = topic_chips([(topic_id, topic_labels.get(topic_id, topic_id), count) for topic_id, count in topics])
    latest_html = "".join(
        card(
            source_display_title(source),
            source.get("excerpt") or "",
            source_href(source),
            source.get("published_date") or source.get("published_at") or "",
        )
        for source in latest
    )
    schema = {
        "@context": "https://schema.org",
        "@type": "ProfilePage",
        "name": f"{visible_handle} source profile",
        "about": {
            "@type": "Person",
            "name": visible_handle,
            "sameAs": creator.get("url") or "",
        },
    }
    return page_shell(
        f"{handle} source profile | Base2026",
        f"""
      <section class="page-hero source-page-hero creator-page-hero">
        <div class="source-hero-main">
          <p class="eyebrow">Creator profile</p>
          {source_identity_markup(safe_handle, avatar_html, variant="creator")}
          <p class="lead">Attributed public source records from short-form expert videos. This page does not imply creator endorsement.</p>
          <div class="hero-actions">
            <a class="ay-button" href="{escape(workspace_href(creator=visible_handle))}">Open in Search Workspace</a>
            <a class="ay-button-secondary" href="{escape(creator.get('url') or '#')}" target="_blank" rel="noreferrer">Open creator profile</a>
            <a class="ay-button-secondary" href="../opt-out.html">Correction or opt-out</a>
          </div>
        </div>
        <div class="source-hero-tools">
          {source_share_action_bar("Share creator profile", "creator profile")}
          <div class="source-hero-meta" aria-label="Creator profile metadata">
            <span class="source-meta-chip"><strong>{len(sources)}</strong><span>records</span></span>
            <span class="source-meta-chip"><strong>{len(public_insights)}</strong><span>insights</span></span>
            <span class="source-meta-chip"><strong>{len(topics)}</strong><span>topics</span></span>
          </div>
        </div>
      </section>
      <section class="content-section">
        <h2>Top Topics</h2>
        <div class="topic-chip-list">{topic_html or '<p class="meta">No public topics yet.</p>'}</div>
      </section>
      <section class="content-section">
        <h2>Latest Source Records</h2>
        <div class="card-grid">{latest_html}</div>
      </section>
      <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
        """,
        current="creators",
        description=f"Attributed public source records from {visible_handle}. This Base2026 profile links every record back to the original creator source.",
        canonical_path=f"creators/{slug(handle)}.html",
    )


def source_page(source: dict, passages: list[dict], insights: list[dict]) -> str:
    source_id = source.get("source_id") or source.get("item_id") or "source"
    archive_source = not source_is_normal_public_card(source)
    handle = display_handle(source.get("creator_handle") or source.get("handle") or "Unknown creator")
    avatar_html = creator_avatar_markup(handle, source.get("avatar_url") or "")
    public_insights = [] if archive_source else [
        row for row in insights if row.get("source_id") == source_id and row.get("public")
    ]
    indexable_source = is_indexable_source(source, passages, public_insights)
    source_topic_rows = [
        (topic_id, label, 0)
        for topic_id, label in zip(source.get("topics") or [], source.get("topic_labels") or [])
    ]
    topic_html = topic_chips(source_topic_rows)
    compact_topic_html = topic_html
    public_text = source_public_text(source, passages)
    readable_excerpt = source_evidence_text(source, passages, public_insights)
    summary_short = source.get("source_summary_short") or source_intelligence_lead(source, public_insights)
    summary_long = source.get("source_summary_long") or readable_excerpt
    platform_name = source.get("platform") or source.get("source_type") or "tiktok"
    distinct_passages = [
        row
        for row in passages
        if (row.get("body") or "")
        and not same_evidence(row.get("body") or "", public_text)
        and not same_evidence(row.get("body") or "", readable_excerpt)
        and not evidence_contains_fragment(row.get("body") or "", public_text)
        and not evidence_contains_fragment(row.get("body") or "", readable_excerpt)
    ]
    passage_html = "".join(
        f"""
        <article class="passage-card">
          <div class="passage-card__meta">
            <span>{escape(handle)}</span>
            <span>{escape(source.get('published_date') or source.get('published_at') or 'No date')}</span>
          </div>
          <div class="passage-card__body">{paragraphize(sentence_excerpt(row.get("body") or "", 420, 3), 0, 2)}</div>
        </article>
        """
        for row in distinct_passages[:4]
    )
    show_summary_long = should_show_summary_long(summary_long, summary_short, public_text)
    insight_html = source_insight_cards(public_insights[:6], passages, public_text)
    source_intelligence_body = (
        f'<div class="card-grid">{insight_html}</div>'
        if insight_html
        else source_intelligence_empty_state()
    )
    hero_eyebrow = "Provenance archive" if archive_source else "Source record"
    if archive_source:
        hero_actions = f"""
            <a class="ay-button" href="{escape(source.get('source_url') or '#')}" target="_blank" rel="noreferrer">Open original</a>
            <a class="ay-button-secondary" href="../opt-out.html">Correction or opt-out</a>
        """
        intelligence_section = f"""
      <section class="content-section">
        {section_title("Archive status", "Reviewed source retained for provenance. Editorial review did not approve a transferable public Source Intelligence card.")}
        <p class="meta">This noindex archive record is excluded from Search Workspace, creator listings, topic evidence pages, and normal public-card counts.</p>
      </section>
        """
    else:
        hero_actions = f"""
            <a class="ay-button" href="{escape(workspace_href(source=source.get('item_id') or source_id))}">Open in Search Workspace</a>
            <a class="ay-button-secondary" href="{escape(source.get('source_url') or '#')}" target="_blank" rel="noreferrer">Open original</a>
            <a class="ay-button-secondary" href="{escape(workspace_href(creator=clean_handle(handle)))}">Creator</a>
        """
        intelligence_section = f"""
      <section class="content-section">
        {section_title("Source Intelligence", "Reviewed source-backed claims promoted from this evidence.")}
        {source_intelligence_body}
      </section>
      {source_answer_section(source, public_insights, passages)}
        """
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CreativeWork",
                "name": source_schema_name(source),
                "description": compact(summary_long or source.get("excerpt") or "", 260),
                "url": source.get("source_url") or "",
                "datePublished": source.get("published_date") or source.get("published_at") or "",
                "author": {
                    "@type": "Person",
                    "name": handle,
                    "sameAs": source.get("creator_url") or "",
                },
                "isBasedOn": source.get("source_url") or "",
                "about": source_seo_topic(source),
            },
        ],
    }
    return page_shell(
        source_seo_title(source, handle),
        f"""
      <section class="page-hero source-page-hero">
        <div class="source-hero-main">
          <p class="eyebrow">{escape(hero_eyebrow)}</p>
          {source_identity_markup(handle, avatar_html, source.get('published_date') or source.get('published_at') or 'No date', source.get('platform') or source.get('source_type') or 'tiktok', variant="source")}
          <h1 class="source-record-title">{escape(source_display_lead(source, 110))} — source {escape(source_record_id(source))}</h1>
          <p class="lead">{escape(summary_short)}</p>
          {f'<p class="source-detail-lead">{escape(summary_long)}</p>' if show_summary_long else ''}
          <div class="hero-actions">
            {hero_actions}
          </div>
        </div>
        <div class="source-hero-tools">
          <div class="source-hero-toolbar">
            {source_share_action_bar("Share source record")}
            {source_quick_meta("excerpt only", len(public_insights), platform_name, source.get("language") or "en")}
          </div>
          {f'<div class="source-hero-topic-tags" aria-label="Source topics">{compact_topic_html}</div>' if compact_topic_html else ''}
        </div>
      </section>
      <section class="content-section source-text-section">
        {section_title("Source Text", "Reviewed polished transcript/source text normalized for reading and search. Raw captions and private QA stay local.")}
        <div class="source-excerpt-text source-full-text">{paragraphize_full(public_text)}</div>
      </section>
      {intelligence_section}
      {f'''
      <section class="content-section">
        {section_title("Supporting Passages", "Distinct public passages that add context beyond the Source Text.")}
        <div class="passage-stack">{passage_html}</div>
      </section>
      ''' if passage_html else ''}
      <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
        """,
        robots="index,follow" if indexable_source else "noindex,follow",
        current="sources",
        description=source_seo_description(source, handle),
        canonical_path=f"sources/{slug(source.get('item_id') or source_id)}.html",
    )


def signal_source_href(source_ref: str) -> str:
    return source_href({"item_id": source_ref or ""})


def signal_list(items: list[str], empty: str) -> str:
    if not items:
        return f'<p class="meta">{escape(empty)}</p>'
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"


TOPIC_MONEY_BRIDGE_COPY: dict[str, dict[str, str]] = {
    "ai-citation-tracking": {
        "title": "Turn citation tracking into a source footprint audit",
        "body": "This topic shows why AI visibility work cannot stop at rankings. Use it to inspect which third-party pages, social surfaces, and evidence records can be found before a model recommends a brand.",
        "primary_label": "Audit your source footprint",
        "primary_href": "/ai-visibility-source-footprint/",
        "secondary_label": "Start with the AI Visibility Audit",
        "secondary_href": "/ai-visibility-audit/",
    },
    "ai-citations": {
        "title": "Map citations before chasing rankings",
        "body": "AI citation evidence is useful only when it becomes an operational map: where the brand appears, which sources support claims, and which gaps need trustworthy coverage.",
        "primary_label": "See the Source Footprint method",
        "primary_href": "/ai-visibility-source-footprint/",
        "secondary_label": "View diagnostic options",
        "secondary_href": "/pricing/",
    },
    "ai-search-reporting": {
        "title": "Reporting needs source-level visibility, not vanity charts",
        "body": "The practical next layer is a report that separates website performance, off-site source coverage, and citation-risk gaps so the business knows what to fix first.",
        "primary_label": "Check source footprint gaps",
        "primary_href": "/ai-visibility-source-footprint/",
        "secondary_label": "Request an AI Visibility Audit",
        "secondary_href": "/ai-visibility-audit/",
    },
    "brand-proof-pages": {
        "title": "Brand proof pages need external corroboration",
        "body": "A proof page is stronger when the surrounding source footprint supports the same claims across credible third-party and owned surfaces.",
        "primary_label": "Inspect source footprint gaps",
        "primary_href": "/ai-visibility-source-footprint/",
        "secondary_label": "See service architecture",
        "secondary_href": "/services/",
    },
    "youtube-ai-citations": {
        "title": "Video citations belong in the public source footprint",
        "body": "YouTube and short-form video can become part of what AI systems inspect. The next step is deciding which video evidence is trustworthy enough to support a brand story.",
        "primary_label": "Audit off-site source coverage",
        "primary_href": "/ai-visibility-source-footprint/",
        "secondary_label": "Run a diagnostic audit",
        "secondary_href": "/ai-visibility-diagnostic-audit/",
    },
}


def topic_answer_capsule_section(traffic: dict, label: str) -> str:
    capsule = traffic.get("answer_capsule") or {}
    heading = capsule.get("heading") or ""
    body = capsule.get("body") or ""
    if not heading and not body:
        return ""
    return f"""
      <section class="content-section topic-answer-capsule" aria-labelledby="topic-answer-capsule-title">
        <p class="eyebrow">Answer first</p>
        <h2 id="topic-answer-capsule-title">{escape(heading or label)}</h2>
        <p class="section-helper">{escape(body)}</p>
      </section>
    """


def topic_source_proof_section(traffic: dict, sources_by_id: dict[str, dict]) -> str:
    proof_ids = [str(value) for value in traffic.get("proof_source_ids") or [] if value]
    cards = []
    for source_id in proof_ids[:4]:
        source = sources_by_id.get(source_id) or {}
        if not source:
            continue
        cards.append(
            card(
                source_display_title(source),
                source.get("excerpt") or source.get("source_summary_short") or "",
                source_href(source),
                f"{display_handle(source.get('creator_handle'))} · {source.get('published_date') or source.get('published_at') or ''}",
            )
        )
    if not cards:
        return ""
    return f"""
      <section class="content-section topic-source-proof" aria-labelledby="topic-source-proof-title">
        <p class="eyebrow">Source proof</p>
        <h2 id="topic-source-proof-title">Evidence records behind this answer</h2>
        <p class="section-helper">Public Base2026 source records connected to this topic. Each card keeps attribution and the original-source path visible.</p>
        <div class="card-grid topic-source-proof__grid">{''.join(cards)}</div>
      </section>
    """


def topic_faq_section(traffic: dict, topic_id: str) -> tuple[str, str]:
    rows = [row for row in traffic.get("faq") or [] if row.get("question") and row.get("answer")]
    if not rows:
        return "", ""
    faq_items = "".join(
        f"""
        <article class="topic-faq__item">
          <h3>{escape(row.get('question') or '')}</h3>
          <p>{escape(row.get('answer') or '')}</p>
        </article>
        """
        for row in rows[:6]
    )
    html = f"""
      <section class="content-section topic-faq" aria-labelledby="topic-faq-title-{escape(slug(topic_id))}">
        <p class="eyebrow">FAQ</p>
        <h2 id="topic-faq-title-{escape(slug(topic_id))}">Questions buyers and operators ask</h2>
        <div class="topic-faq__grid">{faq_items}</div>
      </section>
    """
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": row.get("question") or "",
                "acceptedAnswer": {"@type": "Answer", "text": row.get("answer") or ""},
            }
            for row in rows[:6]
        ],
    }
    return html, f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>'


def topic_money_bridge_section(topic_id: str, traffic: dict | None = None) -> str:
    bridge = (traffic or {}).get("cta") or TOPIC_MONEY_BRIDGE_COPY.get(topic_id)
    if not bridge:
        return ""
    return f"""
      <section class="content-section topic-traffic-cta" aria-labelledby="source-footprint-bridge-{escape(slug(topic_id))}">
        <p class="eyebrow">Apply this evidence</p>
        <h2 id="source-footprint-bridge-{escape(slug(topic_id))}">{escape(bridge['title'])}</h2>
        <p class="section-helper">{escape(bridge['body'])}</p>
        <div class="hero-actions">
          <a class="ay-button" href="{escape(bridge['primary_href'])}">{escape(bridge['primary_label'])}</a>
          <a class="ay-button-secondary" href="{escape(bridge['secondary_href'])}">{escape(bridge['secondary_label'])}</a>
        </div>
      </section>
    """


def topic_signal_brief_section(brief: dict | None, topic_id: str, label: str) -> str:
    if not brief or brief.get("status") != "strong":
        return ""

    creator_angles = brief.get("creator_angles") or []
    repeated_tactics = brief.get("repeated_tactics") or []
    source_actions = brief.get("source_backed_actions") or []
    top_sources = brief.get("top_sources") or []
    monthly_activity = brief.get("monthly_activity") or []

    creator_html = "".join(
        f"""
        <li class="signal-row">
          <a href="{escape(creator_href(angle.get('creator_handle') or 'creator'))}">{escape(display_handle(angle.get('creator_handle')))}</a>
          <span>{escape(compact(angle.get('main_angle') or 'Source-backed creator angle.', 170))}</span>
        </li>
        """
        for angle in creator_angles[:4]
    )
    tactic_html = "".join(
        f"""
        <li>
          <strong>{escape(compact(row.get('label') or 'Repeated tactic', 130))}</strong>
          <span>{escape(format_count(row.get('supporting_source_count')))} sources · {escape(format_count(row.get('supporting_creator_count')))} creators</span>
        </li>
        """
        for row in repeated_tactics[:3]
    )
    action_html = "".join(
        f"""
        <li>
          <span>{escape(compact(row.get('action') or '', 160))}</span>
          {f'<a href="{escape(signal_source_href((row.get("source_ids") or [""])[0]))}">source</a>' if row.get("source_ids") else ''}
        </li>
        """
        for row in source_actions[:3]
        if row.get("action")
    )
    source_html = "".join(
        f"""
        <li class="signal-source-list__item">
          <a href="{escape(signal_source_href(row.get('item_id') or row.get('source_id') or ''))}">{escape(compact(row.get('title') or 'Source record', 110))}</a>
          <span>{escape(display_handle(row.get('creator_handle')))} · {escape(row.get('published_date') or 'No date')}</span>
        </li>
        """
        for row in top_sources[:4]
    )
    max_month_sources = max([int(row.get("source_count") or 0) for row in monthly_activity] or [1])
    momentum_html = "".join(
        f"""
        <li style="--signal-width: {max(8, min(100, round((int(row.get('source_count') or 0) / max_month_sources) * 100)))}%">
          <span>{escape(row.get('month') or '')}</span>
          <strong>{escape(format_count(row.get('source_count')))}</strong>
        </li>
        """
        for row in monthly_activity[-6:]
    )
    tools = brief.get("tools_mentioned") or []
    tools_html = "".join(f'<span class="signal-tool">{escape(tool)}</span>' for tool in tools[:8])

    return f"""
      <section class="content-section topic-signal-brief" aria-labelledby="topic-signal-title">
        <div class="signal-brief-head">
          <div>
            <p class="eyebrow">Topic Signal Brief</p>
            <h2 id="topic-signal-title">{escape(label)} signal map</h2>
            <p class="section-helper">A deterministic summary of repeated creator signals from public source records and reviewed public insight cards.</p>
          </div>
          <div class="signal-stat-row" aria-label="Signal strength">
            <span class="signal-stat"><strong>{escape(format_count(brief.get('source_count')))}</strong>sources</span>
            <span class="signal-stat"><strong>{escape(format_count(brief.get('creator_count')))}</strong>creators</span>
            <span class="signal-stat"><strong>{escape(format_count(brief.get('public_insight_count')))}</strong>insights</span>
          </div>
        </div>
        <div class="signal-grid">
          <section class="signal-block">
            <h3>Creator angles</h3>
            <ul>{creator_html or '<li class="meta">No creator angle summary available yet.</li>'}</ul>
          </section>
          <section class="signal-block">
            <h3>Repeated tactics</h3>
            <ul>{tactic_html or '<li class="meta">No repeated tactic crossed the support threshold yet.</li>'}</ul>
          </section>
          <section class="signal-block">
            <h3>Source-backed actions</h3>
            <ul>{action_html or '<li class="meta">No compact public action summary available yet.</li>'}</ul>
          </section>
          <section class="signal-block signal-block--sources">
            <h3>Evidence to inspect</h3>
            <ol class="signal-source-list">{source_html or '<li class="meta">No source list available yet.</li>'}</ol>
          </section>
        </div>
        <div class="signal-brief-footer">
          <div class="signal-momentum" aria-label="Monthly topic activity">
            <span>Recent source activity</span>
            <ol>{momentum_html or '<li><span>No date data</span><strong>0</strong></li>'}</ol>
          </div>
          {f'<div class="signal-tools" aria-label="Tools mentioned">{tools_html}</div>' if tools_html else ''}
          <div class="signal-brief-cta">
            <a class="button-link" href="{escape(workspace_href(topic=topic_id, q=label))}">Search this signal</a>
            <a class="button-link" href="../compare/{escape(slug(topic_id))}.html">Compare creators</a>
          </div>
        </div>
      </section>
    """


def topic_page(
    topic: dict,
    sources: list[dict],
    passages: list[dict],
    insights: list[dict],
    signal_briefs: dict[str, dict] | None = None,
    topic_traffic_pages: dict[str, dict] | None = None,
) -> str:
    topic_id = topic.get("topic_id") or slug(topic.get("topic") or "uncategorized")
    label = topic.get("topic") or topic_id.replace("-", " ").title()
    signal_brief = (signal_briefs or {}).get(topic_id)
    traffic = (topic_traffic_pages or {}).get(topic_id) or {}
    public_insights = [
        row for row in insights if row.get("public") and (row.get("topic_id") or "") == topic_id
    ]
    related_source_ids = {row.get("source_id") for row in public_insights if row.get("source_id")}
    related_sources = [row for row in sources if row.get("source_id") in related_source_ids]
    if not related_sources:
        related_sources = [
            row for row in sources if topic_id in (row.get("topics") or [])
        ][:12]
    sources_by_id = {}
    for row in sources:
        for key in (row.get("source_id"), row.get("item_id"), slug(row.get("item_id") or "")):
            if key:
                sources_by_id[str(key)] = row
    related_passages = [
        row for row in passages if topic_id in (row.get("topics") or [])
    ][:10]
    creator_rows = topic.get("top_creators") or []
    creator_html = "".join(
        f'<a class="topic-chip" href="{escape(creator_href(row.get("handle") or ""))}">{escape(display_handle(row.get("handle")))} · {escape(str(row.get("count") or 0))}</a>'
        for row in creator_rows
    )
    insight_html = "".join(
        card(
            row.get("claim_text") or label,
            row.get("evidence_excerpt") or "",
            source_href(row),
            f"{display_handle(row.get('creator_handle'))} · {row.get('stance') or 'asserts'}",
        )
        for row in public_insights[:12]
    )
    source_html = "".join(
        card(
            source_display_title(source),
            source.get("excerpt") or "",
            source_href(source),
            f"{display_handle(source.get('creator_handle'))} · {source.get('published_date') or source.get('published_at') or ''}",
        )
        for source in related_sources[:12]
    )
    passage_cards = []
    for row in related_passages[:6]:
        source = sources_by_id.get(row.get("source_id") or "", {})
        handle = display_handle(source.get("creator_handle") or row.get("creator_handle") or row.get("handle"))
        title = source_display_title(source) if source else "Source record"
        href = source_href(source) if source else "#"
        date = source.get("published_date") or source.get("published_at") or row.get("published_date") or "No date"
        passage_cards.append(
            f"""
            <article class="passage-card passage-card--linked">
              <div class="passage-card__meta">
                <a href="{escape(href)}">{escape(title)}</a>
                <span>{escape(handle)}</span>
                <span>{escape(date)}</span>
              </div>
              <div class="passage-card__body">{paragraphize(row.get('body') or '', 1100, 2)}</div>
            </article>
            """
        )
    passage_html = "".join(passage_cards)
    faq_html, faq_schema = topic_faq_section(traffic, topic_id)
    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": traffic.get("seo_title") or f"{label} creator evidence",
        "description": compact(traffic.get("meta_description") or topic.get("definition") or "", 260),
        "about": label,
    }
    if signal_brief:
        schema["mainEntity"] = {
            "@type": "ItemList",
            "name": f"{label} topic signal brief",
            "numberOfItems": int(signal_brief.get("public_insight_count") or 0),
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": index + 1,
                    "name": compact(row.get("label") or row.get("action") or "Source-backed signal", 120),
                }
                for index, row in enumerate(
                    (signal_brief.get("repeated_tactics") or [])[:3]
                    + (signal_brief.get("source_backed_actions") or [])[:3]
                )
            ],
        }
    seo_title = (
        compact(traffic.get("seo_title"), 65)
        if traffic.get("seo_title")
        else seo_title_with_suffix(label, " Evidence | Base2026")
    )
    seo_description = traffic.get("meta_description") or topic.get("definition") or f"Source-backed creator evidence and viewpoints related to {label}."
    return page_shell(
        seo_title,
        f"""
      <section class="page-hero topic-page-hero">
        <div class="topic-page-hero__main">
          <p class="eyebrow">Topic evidence page</p>
          <h1>{escape(label)}</h1>
          <p class="lead">{escape(topic.get('definition') or f'Source-backed creator statements and evidence excerpts related to {label}.')}</p>
          <div class="hero-actions">
            <a class="ay-button" href="{escape(workspace_href(topic=topic_id, q=label))}">Open in Search Workspace</a>
            <a class="ay-button-secondary" href="../compare/{escape(slug(topic_id))}.html">Compare creator viewpoints</a>
            <a class="ay-button-secondary" href="../methodology.html">Methodology</a>
          </div>
        </div>
        <aside class="topic-page-hero__tools" aria-label="Topic page controls and summary">
          {inline_share_actions("Share topic page", "topic page")}
          <div class="topic-stat-grid" aria-label="Topic evidence summary">
            <div><strong>{escape(str(topic.get('public_insight_count') or 0))}</strong><span>insight cards</span></div>
            <div><strong>{escape(str(topic.get('source_count') or len(related_sources)))}</strong><span>source records</span></div>
            <div><strong>{escape(str(topic.get('creator_count') or len(creator_rows)))}</strong><span>creators</span></div>
          </div>
        </aside>
      </section>
      {topic_answer_capsule_section(traffic, label)}
      {topic_signal_brief_section(signal_brief, topic_id, label)}
      {topic_answer_section(topic, public_insights, related_sources, creator_rows, signal_brief)}
      {topic_source_proof_section(traffic, sources_by_id)}
      {faq_html}
      {topic_money_bridge_section(topic_id, traffic)}
      <section class="content-section">
        <h2>Top Creators</h2>
        <div class="topic-chip-list">{creator_html or '<p class="meta">No creator distribution available yet.</p>'}</div>
      </section>
      <section class="content-section">
        <h2>Public Insight Cards</h2>
        <p class="meta">These are deterministic, source-backed cards from the offline export. They are not live AI answers.</p>
        <div class="card-grid">{insight_html or '<p class="meta">No public insight cards available yet.</p>'}</div>
      </section>
      <section class="content-section">
        <h2>Related Source Records</h2>
        <div class="card-grid">{source_html or '<p class="meta">No related source records available.</p>'}</div>
      </section>
      <section class="content-section">
        <h2>Evidence Passages</h2>
        <p class="section-helper">Short public snippets grouped with their source record, creator, and date.</p>
        <div class="passage-stack">{passage_html or '<p class="meta">No related passages available.</p>'}</div>
      </section>
      <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
      {faq_schema}
        """,
        robots="index,follow" if is_indexable_topic(topic) else "noindex,follow",
        current="topics",
        description=seo_description,
        canonical_path=f"topics/{slug(topic_id)}.html",
    )


def compare_page(topic: dict, insights: list[dict]) -> str:
    topic_id = topic.get("topic_id") or slug(topic.get("topic") or "uncategorized")
    label = topic.get("topic") or topic_id.replace("-", " ").title()
    public_insights = [
        row for row in insights if row.get("public") and (row.get("topic_id") or "") == topic_id
    ]
    by_creator: dict[str, list[dict]] = defaultdict(list)
    for insight in public_insights:
        by_creator[insight.get("creator_handle") or "Unknown creator"].append(insight)
    creator_blocks = []
    for handle, rows in sorted(by_creator.items(), key=lambda item: (-len(item[1]), item[0])):
        claim_rows = "".join(
            f"""
            <li>
              <p><strong>{escape(row.get('stance') or 'asserts')}</strong>: {escape(compact(row.get('claim_text') or '', 260))}</p>
              <p class="meta">{escape(compact(row.get('evidence_excerpt') or '', 260))}</p>
              <a class="button-link" href="{escape(source_href(row))}">Source page</a>
            </li>
            """
            for row in rows[:5]
        )
        creator_blocks.append(
            f"""
            <article class="comparison-group">
              <h3><a href="{escape(creator_href(handle))}">{escape(display_handle(handle))}</a></h3>
              <ul>{claim_rows}</ul>
            </article>
            """
        )
    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"{label} creator viewpoint comparison",
        "about": label,
    }
    return page_shell(
        seo_title_with_suffix(label, " | Creator Views | Base2026"),
        f"""
      <section class="page-hero">
        <p class="eyebrow">Creator viewpoint comparison</p>
        <h1>{escape(label)}</h1>
        <p class="lead">A deterministic grouping of public source-backed insight cards. This page compares what creators said without declaring a winner.</p>
        <div class="hero-actions">
          <a class="ay-button" href="{escape(workspace_href(compare=topic_id, topic=topic_id, q=label))}">Open in Search Workspace</a>
          <a class="ay-button-secondary" href="../topics/{escape(slug(topic_id))}.html">Topic page</a>
        </div>
      </section>
      <section class="content-section">
        <h2>Creator Viewpoints</h2>
        <div class="comparison-grid">{''.join(creator_blocks) or '<p class="meta">No public creator viewpoints available yet.</p>'}</div>
      </section>
      <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
        """,
        robots="index,follow" if is_indexable_topic(topic) else "noindex,follow",
        current="topics",
        description=f"Compare source-backed creator viewpoints about {label}. Every viewpoint links back to Base2026 source evidence.",
        canonical_path=f"compare/{slug(topic_id)}.html",
    )


def index_page(
    title: str,
    intro: str,
    cards: str,
    current: str = "",
    canonical_path: str | None = None,
    pagination: str = "",
) -> str:
    if canonical_path is None:
        canonical_path = {
            "creators": "creators/",
            "sources": "sources/",
            "topics": "topics/",
        }.get(current, "")
    return page_shell(
        title,
        f"""
      <section class="page-hero">
        <p class="eyebrow">Base2026 index</p>
        <h1>{escape(title)}</h1>
        <p class="lead">{escape(intro)}</p>
        <div class="hero-actions">
          <a class="ay-button" href="../">Back to search</a>
        </div>
      </section>
      <section class="content-section" aria-labelledby="{escape(slug(title, 'index'))}-list-heading">
        <h2 id="{escape(slug(title, 'index'))}-list-heading">Available {escape(title.lower())}</h2>
        <div class="card-grid">{cards}</div>
        {pagination}
      </section>
        """,
        current=current,
        description=intro,
        canonical_path=canonical_path,
    )


def source_index_pagination(page_number: int, page_count: int) -> str:
    if page_count <= 1:
        return ""
    links = []
    if page_number > 1:
        previous = "./" if page_number == 2 else f"page-{page_number - 1}.html"
        links.append(f'<a class="button-link" rel="prev" href="{previous}">Newer source records</a>')
    if page_number < page_count:
        links.append(f'<a class="button-link" rel="next" href="page-{page_number + 1}.html">Older source records</a>')
    return f'<nav class="source-index-pagination" aria-label="Source record pages">{"".join(links)}</nav>'


def analytics_stat(label: str, value: object, detail: str = "") -> str:
    return f"""
        <article class="analytics-stat">
          <strong>{escape(format_count(value))}</strong>
          <span>{escape(label)}</span>
          {f'<p>{escape(detail)}</p>' if detail else ''}
        </article>
    """


def analytics_page(analytics: dict) -> str:
    totals = analytics.get("totals") or {}
    top_topics = analytics.get("top_topics") or []
    top_creators = analytics.get("top_creators") or []
    years = analytics.get("sources_by_year") or []
    latest = analytics.get("latest_sources") or []

    topic_rows = []
    for row in top_topics[:24]:
        topic_id = row.get("topic_id") or ""
        href = topic_href(topic_id, prefix="./topics")
        signal = " · signal brief" if row.get("has_signal_brief") else ""
        topic_rows.append(
            f"""
            <tr>
              <td><a href="{escape(href)}">{escape(row.get("label") or topic_id)}</a></td>
              <td>{escape(format_count(row.get("source_count")))}</td>
              <td>{escape(format_count(row.get("creator_count")))}</td>
              <td>{escape(format_count(row.get("public_insight_count")))}</td>
              <td>{escape(format_count(row.get("signal_score")))}{escape(signal)}</td>
            </tr>
            """
        )

    creator_cards = []
    for row in top_creators[:12]:
        handle = row.get("handle") or "@creator"
        creator_cards.append(
            f"""
            <article class="analytics-creator-card">
              {creator_avatar_markup(handle, row.get("avatar_url") or "", relative_root=".")}
              <div>
                <h3>{escape(handle)}</h3>
                <p>{escape(format_count(row.get("source_count")))} sources · {escape(format_count(row.get("public_insight_count")))} insights · {escape(format_count(row.get("topic_count")))} topics</p>
                <a class="button-link" href="{escape(creator_href(handle, prefix='./creators'))}">Creator profile</a>
              </div>
            </article>
            """
        )

    year_items = "".join(
        f"<li><strong>{escape(str(row.get('year') or ''))}</strong><span>{escape(format_count(row.get('source_count')))} sources</span></li>"
        for row in years[:8]
    )
    latest_items = "".join(
        f"""
        <li>
          <a href="{escape(source_href(row, prefix='./sources'))}">{escape(compact(row.get('title') or 'Source record', 96))}</a>
          <span>{escape(row.get('creator_handle') or '')} · {escape(row.get('published_date') or '')}</span>
        </li>
        """
        for row in latest[:10]
    )

    body = f"""
      <section class="page-hero analytics-hero">
        <p class="eyebrow">Base2026 analytics</p>
        <h1>Signals across the public source library.</h1>
        <p class="lead">A compact public analytics layer for topics, creators, sources, and repeated SEO/GEO/AEO themes. It is generated from the same public release data used by search.</p>
        <div class="hero-actions">
          <a class="ay-button" href="./">Search the library</a>
          <a class="ay-button-secondary" href="./topics/">Topics</a>
        </div>
      </section>
      <section class="analytics-stat-grid" aria-label="Base2026 dataset totals">
        {analytics_stat("source records", totals.get("source_records"))}
        {analytics_stat("searchable passages", totals.get("passages"))}
        {analytics_stat("public insight cards", totals.get("public_insight_cards"))}
        {analytics_stat("public topics", totals.get("public_topics"), f"{format_count(totals.get('signal_briefs'))} signal briefs")}
      </section>
      <section class="content-section analytics-section">
        <div class="section-title-row"><h2>Topic signal ranking</h2>{info_hint("Topic signal ranking", "A deterministic score from public sources, creators, passages, public insight cards, and available signal briefs.")}</div>
        <div class="analytics-table-wrap">
          <table class="analytics-table">
            <thead><tr><th>Topic</th><th>Sources</th><th>Creators</th><th>Insights</th><th>Signal</th></tr></thead>
            <tbody>{''.join(topic_rows)}</tbody>
          </table>
        </div>
      </section>
      <section class="content-section analytics-section">
        <div class="section-title-row"><h2>Creators</h2>{info_hint("Creators", "Public creator-level coverage in this release.")}</div>
        <div class="analytics-creator-grid">{''.join(creator_cards)}</div>
      </section>
      <section class="analytics-two-up">
        <article class="content-section analytics-section">
          <div class="section-title-row"><h2>Years</h2>{info_hint("Years", "Public source records grouped by publication year.")}</div>
          <ul class="analytics-list">{year_items}</ul>
        </article>
        <article class="content-section analytics-section">
          <div class="section-title-row"><h2>Latest records</h2>{info_hint("Latest records", "Newest public source records in this release.")}</div>
          <ul class="analytics-list analytics-list--links">{latest_items}</ul>
        </article>
      </section>
    """
    return page_shell(
        "Base2026 Analytics",
        body,
        relative_root=".",
        current="analytics",
        description="Public analytics for Base2026 topics, creators, source records, passages and repeated SEO/GEO/AEO signals.",
        canonical_path="analytics.html",
    )


def traffic_resources_page(topic_traffic_pages: dict, topics: list[dict]) -> str:
    """Hub page for demand-led Base2026 traffic resources."""
    topics_by_id = {
        (row.get("topic_id") or slug(row.get("topic") or "")): row
        for row in topics
        if row.get("public")
    }
    clusters = [
        ("AI citations and reporting", "Prompt testing, AI citation tracking, GSC limits and source-footprint reporting.", ["ai-citation-tracking", "ai-citations", "ai-search-reporting", "chatgpt-query-research", "google-search-console-ai-visibility-reporting"]),
        ("Bing and Copilot citation readiness", "Bing-specific grounding, citation mechanics, crawl constraints, IndexNow-safe discovery and revenue visibility.", ["bing-ai-citations", "ai-visibility-citation-mechanics", "ai-search-crawl-constraints", "ai-search-google-index-overlap", "technical-seo-indexing", "technical-seo-site-crawling", "ai-search-revenue-visibility"]),
        ("AI source trust and entity footprint", "Trusted sources, brand/entity mentions, source citation SEO and source-footprint strategy for answer engines.", ["ai-search-source-trust", "ai-search-strategy-trusted-sources", "ai-visibility-source-strategy", "ai-visibility-tracking-brand-mentions", "brand-mentions-ai-visibility", "entity-mentions-ai-visibility", "entity-seo-branded-search", "source-citation-seo", "citations-and-ai-visibility"]),
        ("Local visibility and business proof", "Google Business Profile, local SEO, reviews and the proof surfaces local businesses need before AI systems can recommend them.", ["local-seo-google-business-profile", "google-business-profile", "local-seo", "review-strategy", "brand-proof-pages", "local-service-seo", "local-seo-gbp", "reviews-local-seo", "owned-branded-review-pages"]),
        ("Answer-ready commercial and service pages", "Commercial, transactional and local-service pages that answer buyer prompts and route readers toward a real next step.", ["ai-visibility-commercial-pages", "on-page-seo-for-ai-search", "ai-visibility-exact-answer-pages", "faq-pages-ai-search", "service-page-seo", "local-seo-service-area-pages", "local-seo-landing-pages", "bottom-of-funnel-seo-landing-pages", "transactional-seo-landing-page-structure", "landing-page-conversion"]),
        ("Content quality and answer-ready pages", "Answer-first content, freshness, AI-assisted content quality, disclosure and knowledge-base structure.", ["answer-first-content", "schema-ai-citations", "content-freshness", "content-strategy", "ai-content-quality", "ai-content-disclosure", "ai-knowledge-base"]),
        ("Technical SEO and crawl discovery", "Internal linking, on-page SEO, low-hanging Search Console opportunities, WordPress SEO plugin limits and indexation hygiene.", ["internal-linking", "on-page-seo", "search-console-low-hanging-fruit", "wordpress-seo-plugin-capabilities"]),
        ("Authority, lists and third-party source footprint", "Backlink quality, listicles, third-party recommendation surfaces and the source evidence that supports AI answers.", ["backlink-quality", "listicles-ai-recommendations", "self-promotional-listicles", "youtube-ai-citations", "core-update-analysis", "ecommerce-seo-collection-pages"]),
        ("AI crawler policy and risk controls", "Scaled-content risk, llms.txt limitations and crawler-policy contradictions that can weaken AI visibility infrastructure.", ["risk-avoid-scaled-content-abuse", "llms-txt-risk", "llms-txt-contradiction-ai-crawlers"]),
    ]

    def resource_card(topic_id: str) -> str:
        cfg = topic_traffic_pages.get(topic_id, {})
        topic = topics_by_id.get(topic_id, {})
        title = cfg.get("target_query") or topic.get("topic") or topic_id.replace("-", " ").title()
        desc = cfg.get("meta_description") or topic.get("definition") or "Base2026 source-backed traffic resource."
        proof_count = len(cfg.get("proof_source_ids") or [])
        faq_count = len(cfg.get("faq") or [])
        proof_label = f"{proof_count} source proofs" if proof_count != 1 else "1 source proof"
        return f"""
          <article class=\"traffic-resource-card\">
            <div>
              <p class=\"traffic-resource-card__meta\">{escape(proof_label)} · {faq_count} FAQs · indexable topic</p>
              <h3><a href=\"topics/{escape(slug(topic_id))}.html\">{escape(title)}</a></h3>
              <p>{escape(compact(desc, 220))}</p>
            </div>
            <a class=\"button-link\" href=\"topics/{escape(slug(topic_id))}.html\">Open resource</a>
          </article>
        """

    cluster_sections = []
    used: set[str] = set()
    for cluster_title, cluster_desc, ids in clusters:
        cards = []
        for topic_id in ids:
            if topic_id in topic_traffic_pages:
                used.add(topic_id)
                cards.append(resource_card(topic_id))
        if cards:
            cluster_sections.append(
                f"""
      <section class=\"content-section traffic-resource-cluster\" id=\"{escape(slug(cluster_title))}\">
        <div class=\"section-title-row\">
          <div>
            <p class=\"eyebrow\">Resource cluster</p>
            <h2>{escape(cluster_title)}</h2>
            <p>{escape(cluster_desc)}</p>
          </div>
        </div>
        <div class=\"traffic-resource-grid\">{''.join(cards)}</div>
      </section>
                """
            )
    remaining = [topic_id for topic_id in sorted(topic_traffic_pages) if topic_id not in used]
    if remaining:
        cluster_sections.append(
            f"""
      <section class=\"content-section traffic-resource-cluster\" id=\"more-resources\">
        <div class=\"section-title-row\">
          <div>
            <p class=\"eyebrow\">More resources</p>
            <h2>Additional demand-led pages</h2>
            <p>Other source-backed Base2026 resources in the traffic layer.</p>
          </div>
        </div>
        <div class=\"traffic-resource-grid\">{''.join(resource_card(topic_id) for topic_id in remaining)}</div>
      </section>
            """
        )

    body = f"""
      <section class=\"b26-about-hero ay-about-contact-hero\" aria-label=\"Alex Yarosh source library hero\">
        <div class=\"b26-about-hero-copy ay-about-contact-hero-copy\">
          <div class=\"b26-founder-quote ay-founder-quote\" role=\"presentation\"><span>AI VISIBILITY</span><span>NEEDS PROOF.</span><span>MAKE EVERY PAGE - <br class=\"b26-founder-mobile-break\">CITABLE.</span></div>
          <p class=\"b26-founder-support ay-founder-support\">Source-backed library for the visibility pages.</p>
        </div>
        <figure class=\"b26-hero-figure ay-hero-figure\">
          <img class=\"b26-hero-person ay-hero-person\" src=\"./static/assets/alex-yarosh-cutout-v115.png\" alt=\"Alex Yarosh\" loading=\"eager\" decoding=\"async\" width=\"1400\" height=\"1264\" />
        </figure>
      </section>
      <section class=\"content-section traffic-resource-intro\">
        <p class=\"eyebrow\">AI Visibility Library</p>
        <h1>Source-backed resources that support the AI Visibility Pages.</h1>
        <p class=\"lead\">This library is the deeper evidence layer behind the main AI Visibility Pages hub. It keeps crawlable topic clusters, proof references, FAQs and internal links organized without competing with the primary visitor path.</p>
        <div class=\"hero-actions\">
          <a class=\"ay-button\" href=\"/knowledge/ai-visibility-pages/\">Open AI Visibility Pages</a>
          <a class=\"ay-button-secondary\" href=\"/ai-visibility-audit/\">Get a free AI Visibility Snapshot</a>
        </div>
      </section>
      <section class=\"content-section traffic-resource-summary\">
        <div class=\"analytics-stat-grid\">
          {analytics_stat("library resources", len(topic_traffic_pages))}
          {analytics_stat("topic clusters", len(cluster_sections))}
          {analytics_stat("public evidence links", sum(len(v.get('proof_source_ids') or []) for v in topic_traffic_pages.values()))}
          {analytics_stat("FAQ answers", sum(len(v.get('faq') or []) for v in topic_traffic_pages.values()))}
        </div>
      </section>
      {''.join(cluster_sections)}
      <section class=\"content-section traffic-resource-cta\">
        <p class=\"eyebrow\">From library to money pages</p>
        <h2>Use the library as support, not the primary sales path.</h2>
        <p>The main route for visitors is the AI Visibility Pages hub. This library stays indexable and useful for crawlers, researchers and internal linking, then routes qualified readers into the diagnostic/audit path.</p>
        <div class=\"hero-actions\">
          <a class=\"ay-button\" href=\"/knowledge/ai-visibility-pages/\">Go to AI Visibility Pages</a>
          <a class=\"ay-button-secondary\" href=\"/ai-visibility-diagnostic-audit/\">Run diagnostic audit</a>
        </div>
      </section>
    """
    return page_shell(
        "AI Visibility Library | Base2026",
        body,
        relative_root=".",
        current="",
        description="A source-backed Base2026 library connecting AI visibility, AI citations, local SEO, content quality, technical SEO and crawler-policy resources behind the main AI Visibility Pages hub.",
        canonical_path="ai-visibility-resources.html",
        main_class="app-shell content-page doc-page ai-visibility-page",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate public creator/source pages from public JSONL.")
    parser.add_argument("--data", type=Path, default=Path("public-data/tiktok"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--topic-traffic-config", type=Path, default=Path("data/base2026_topic_traffic_pages.json"))
    args = parser.parse_args()

    data = args.data
    out = args.out
    topic_traffic_pages = read_json(args.topic_traffic_config)
    sources = read_jsonl(data / "source_records.jsonl")
    normal_sources = [source for source in sources if source_is_normal_public_card(source)]
    passages = read_jsonl(data / "passages.jsonl")
    insights = read_jsonl(data / "insight_cards.jsonl")
    topics = read_jsonl(data / "topics.jsonl")
    global PUBLISHED_TOPIC_IDS
    PUBLISHED_TOPIC_IDS = {
        slug(topic.get("topic_id") or topic.get("topic") or "uncategorized")
        for topic in topics
        if topic.get("public")
    }
    creators = read_jsonl(data / "creators.jsonl")
    signal_briefs = {
        row.get("topic_id") or "": row
        for row in read_jsonl(data / "topic_signal_briefs.jsonl")
        if row.get("topic_id")
    }
    analytics = {}
    analytics_path = data / "analytics_summary.json"
    if not analytics_path.exists():
        analytics_path = data / "base2026_analytics.json"
    if analytics_path.exists():
        analytics = json.loads(analytics_path.read_text(encoding="utf-8"))

    passages_by_source: dict[str, list[dict]] = defaultdict(list)
    for passage in passages:
        passages_by_source[passage.get("source_id") or ""].append(passage)

    insights_by_source: dict[str, list[dict]] = defaultdict(list)
    for insight in insights:
        insights_by_source[insight.get("source_id") or ""].append(insight)

    sources_by_handle: dict[str, list[dict]] = defaultdict(list)
    for source in normal_sources:
        sources_by_handle[source.get("creator_handle") or source.get("handle") or "Unknown"].append(source)

    creators_by_handle = {
        creator.get("handle") or creator.get("creator_handle") or creator.get("creator_id"): creator
        for creator in creators
    }

    creator_cards = []
    for handle, source_rows in sorted(sources_by_handle.items()):
        creator = creators_by_handle.get(handle, {"handle": handle, "url": ""})
        html = creator_page(handle, creator, source_rows, insights)
        path = out / "creators" / f"{slug(handle)}.html"
        write_text(path, html)
        public_insight_count = sum(
            1 for insight in insights if insight.get("creator_handle") == handle and insight.get("public")
        )
        creator_cards.append(creator_index_card(handle, creator, len(source_rows), public_insight_count))

    source_cards = []
    indexable_source_count = 0
    for source in sources:
        source_key = source.get("source_id") or ""
        source_passages = passages_by_source.get(source_key, [])
        source_insights = insights_by_source.get(source_key, [])
        page_name = f"{slug(source.get('item_id') or source_key)}.html"
        html = source_page(source, source_passages, source_insights)
        write_text(out / "sources" / page_name, html)
        if is_indexable_source(source, source_passages, source_insights):
            indexable_source_count += 1
            source_cards.append(
                card(
                    source_display_title(source),
                    source.get("excerpt") or "",
                    page_name,
                    display_handle(source.get("creator_handle") or source.get("handle")),
                )
            )

    topic_cards = []
    public_topics = [topic for topic in topics if topic.get("public")]
    public_topics.sort(
        key=lambda row: (-(int(row.get("public_insight_count") or 0)), row.get("topic") or "")
    )
    indexable_topics = [topic for topic in public_topics if is_indexable_topic(topic)]
    for topic in public_topics:
        topic_id = topic.get("topic_id") or slug(topic.get("topic") or "uncategorized")
        write_text(out / "topics" / f"{slug(topic_id)}.html", topic_page(topic, normal_sources, passages, insights, signal_briefs, topic_traffic_pages))
        write_text(out / "compare" / f"{slug(topic_id)}.html", compare_page(topic, insights))
    for topic in indexable_topics:
        topic_id = topic.get("topic_id") or slug(topic.get("topic") or "uncategorized")
        has_signal = topic_id in signal_briefs
        meta = f"{topic.get('public_insight_count') or 0} public insights · {topic.get('source_count') or 0} sources"
        if has_signal:
            meta = f"Signal brief · {meta}"
        topic_cards.append(
            card(
                topic.get("topic") or topic_id,
                topic.get("definition") or "",
                f"{slug(topic_id)}.html",
                meta,
            )
        )

    write_text(
        out / "creators" / "index.html",
        index_page("Creator Source Profiles", "Creator-level attribution pages for indexed public source records.", "".join(creator_cards), current="creators"),
    )
    source_page_size = 80
    source_page_count = max(1, (len(source_cards) + source_page_size - 1) // source_page_size)
    for page_number in range(1, source_page_count + 1):
        start = (page_number - 1) * source_page_size
        page_cards = "".join(source_cards[start : start + source_page_size])
        page_title = "Source Records" if page_number == 1 else f"Source Records — Page {page_number} | Base2026"
        canonical_path = "sources/" if page_number == 1 else f"sources/page-{page_number}.html"
        output_name = "index.html" if page_number == 1 else f"page-{page_number}.html"
        write_text(
            out / "sources" / output_name,
            index_page(
                page_title,
                "Excerpt-first source records with attribution and original links.",
                page_cards,
                current="sources",
                canonical_path=canonical_path,
                pagination=source_index_pagination(page_number, source_page_count),
            ),
        )
    write_text(
        out / "topics" / "index.html",
        index_page("Topic Evidence Pages", "Topic-level evidence pages with source-backed insights and creator comparison links.", "".join(topic_cards[:80]), current="topics"),
    )
    write_text(
        out / "compare" / "index.html",
        index_page(
            "Creator Viewpoint Comparisons",
            "Deterministic creator viewpoint groupings by topic. Every row links back to source evidence.",
            "".join(topic_cards[:80]),
            current="topics",
            canonical_path="compare/",
        ),
    )
    write_text(out / "analytics.html", analytics_page(analytics))
    write_text(out / "ai-visibility-resources.html", traffic_resources_page(topic_traffic_pages, topics))

    print(
        json.dumps(
            {
                "creators": len(sources_by_handle),
                "sources": len(sources),
                "normal_sources": len(normal_sources),
                "archive_sources": len(sources) - len(normal_sources),
                "indexable_sources": indexable_source_count,
                "topics": len(public_topics),
                "indexable_topics": len(indexable_topics),
                "compare_pages": len(public_topics),
                "out": str(out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
