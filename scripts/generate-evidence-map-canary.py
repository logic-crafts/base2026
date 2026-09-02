#!/usr/bin/env python3
"""Build a small, gated Base2026 evidence-map canary.

The input is a public search export (the same JSON envelope returned by the
public D1 search API, or JSONL rows from that envelope).  This script never
reads the private knowledge base and never emits a full transcript.  It emits
only a managed HTML/CSS/sitemap overlay plus a compact eligibility ledger.

The output directory is an existing public release-root artifact, such as
``output/cloudflare-migration/source-web``.  Only files owned by this canary
are written, and an existing unmanaged file is a hard error.
"""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import html
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable
from urllib.parse import quote, urlsplit


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "data" / "base2026_evidence_map_canary.json"
HEADER_TEMPLATE = PROJECT_ROOT / "templates" / "base2026-startup-header.html"
FOOTER_TEMPLATE = PROJECT_ROOT / "templates" / "base2026-startup-footer.html"
CSS_TEMPLATE = PROJECT_ROOT / "templates" / "base2026-evidence-map.css"

CANARY_SCHEMA = "base2026.evidence-map-canary.v1"
CANARY_MARKER = "BASE2026_EVIDENCE_MAP_CANARY_V1"
INDEX_UID = "base2026_public_tiktok"
MAX_EVIDENCE_CARDS = 6
MIN_EVIDENCE_CARDS = 4
MIN_SOURCE_COUNT = 4
MIN_CREATOR_COUNT = 3
MIN_ANSWER_WORDS = 45
MIN_VISIBLE_WORDS = 260
MIN_SCORE = 80

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SOURCE_ID_RE = re.compile(r"^tiktok:[A-Za-z0-9._-]{2,256}:[0-9]{10,30}$")
VIDEO_ID_RE = re.compile(r"/video/([0-9]{10,30})(?:[/?#]|$)")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\w)\+?\d[\d .()\-]{8,}\d(?!\w)")
SECRET_RE = re.compile(
    r"\b(?:api[_ -]?key|access[_ -]?token|secret|bearer)\s*[:=]\s*[^\s,.;]+",
    re.IGNORECASE,
)
PRIVATE_RE = re.compile(
    r"\b(?:private|confidential|internal[- ]only|raw captions?|raw asr|full transcript|not for public)\b",
    re.IGNORECASE,
)
LOCAL_PATH_RE = re.compile(r"(?:/Users/|/home/|[A-Za-z]:\\|\.codex/worktrees/)")


class CanaryError(Exception):
    """Expected validation failure; the CLI converts this to exit code 2."""


def compact_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def word_count(value: str) -> int:
    return len(re.findall(r"[\w][\w'’-]*", value, flags=re.UNICODE))


def slugify(value: str) -> str:
    value = compact_text(value).casefold()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def truncate_words(value: str, max_chars: int) -> str:
    value = compact_text(value)
    if len(value) <= max_chars:
        return value
    clipped = value[: max_chars + 1].rsplit(" ", 1)[0].strip()
    return f"{clipped.rstrip('.,;:')}…"


def public_excerpt(value: Any) -> str:
    """Keep a bounded public segment and mark likely mid-sentence starts."""

    text = compact_text(value)
    if text and not text[0].isupper() and text[0] not in "\"'“([{0123456789":
        text = f"…{text}"
    return truncate_words(text, 300)


def json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [compact_text(item) for item in value if compact_text(item)]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return [value.strip()] if value.strip() else []
        return json_list(parsed)
    return []


def safe_json(value: Any) -> str:
    """Serialize JSON-LD without allowing a value to close the script tag."""

    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def escape(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def source_url_is_public(value: str) -> bool:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    if parsed.scheme != "https" or parsed.hostname not in {"www.tiktok.com", "tiktok.com"}:
        return False
    return bool(VIDEO_ID_RE.search(parsed.path))


def video_id_for(row: dict[str, Any]) -> str:
    video_id = compact_text(row.get("video_id"))
    if re.fullmatch(r"\d{10,30}", video_id):
        return video_id
    match = VIDEO_ID_RE.search(compact_text(row.get("source_url")))
    if match:
        return match.group(1)
    source_id = compact_text(row.get("source_id"))
    return source_id.rsplit(":", 1)[-1] if re.fullmatch(r"\d{10,30}", source_id.rsplit(":", 1)[-1]) else ""


def creator_for(row: dict[str, Any]) -> str:
    handle = compact_text(row.get("creator_handle") or row.get("handle"))
    if handle:
        return handle if handle.startswith("@") else f"@{handle}"
    source_id = compact_text(row.get("source_id"))
    if SOURCE_ID_RE.fullmatch(source_id):
        return f"@{source_id.split(':', 2)[1]}"
    return ""


def evidence_fingerprint(row: dict[str, Any]) -> str:
    material = "\x1f".join(
        [compact_text(row.get("body")).casefold(), compact_text(row.get("title")).casefold()]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def public_row_reasons(row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    source_id = compact_text(row.get("source_id"))
    if not SOURCE_ID_RE.fullmatch(source_id):
        reasons.append("INVALID_SOURCE_ID")
    if row.get("full_transcript_public") is True or compact_text(row.get("full_transcript_public")).casefold() == "true":
        reasons.append("FULL_TRANSCRIPT_PUBLIC")
    admission_state = compact_text(row.get("admission_state")).casefold()
    if any(marker in admission_state for marker in ("private", "archive", "noindex", "rollback")):
        reasons.append("NON_INDEXABLE_ADMISSION_STATE")
    source_url = compact_text(row.get("source_url"))
    if not source_url_is_public(source_url):
        reasons.append("MISSING_PUBLIC_TIKTOK_SOURCE")
    if not compact_text(row.get("body")):
        reasons.append("MISSING_PUBLIC_EXCERPT")
    if not compact_text(row.get("title")):
        reasons.append("MISSING_PUBLIC_TITLE")
    # A TikTok video URL necessarily contains a long numeric video ID.  Do not
    # mistake that identifier for a phone number; contact markers in the
    # public excerpt/title/handle are still rejected.
    for field in ("body", "title", "creator_handle"):
        value = compact_text(row.get(field))
        if EMAIL_RE.search(value) or PHONE_RE.search(value):
            reasons.append(f"PRIVATE_CONTACT_MARKER:{field}")
        if SECRET_RE.search(value) or PRIVATE_RE.search(value) or LOCAL_PATH_RE.search(value):
            reasons.append(f"PRIVATE_CONTENT_MARKER:{field}")
    topic_text = " ".join(json_list(row.get("topic_labels")))
    if SECRET_RE.search(topic_text) or PRIVATE_RE.search(topic_text) or LOCAL_PATH_RE.search(topic_text):
        reasons.append("PRIVATE_CONTENT_MARKER:topic_labels")
    source_url_value = compact_text(row.get("source_url"))
    if SECRET_RE.search(source_url_value) or LOCAL_PATH_RE.search(source_url_value):
        reasons.append("PRIVATE_CONTENT_MARKER:source_url")
    return sorted(set(reasons))


def read_json_or_jsonl(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix.casefold() == ".jsonl":
        values: list[Any] = []
        for line_number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                values.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise CanaryError(f"invalid JSONL in {path}:{line_number}: {exc}") from exc
        return values
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise CanaryError(f"invalid JSON in {path}: {exc}") from exc


def iter_export_values(value: Any) -> Iterable[tuple[dict[str, Any], int | None]]:
    """Yield public rows and an optional search-estimate from API envelopes."""

    if isinstance(value, list):
        for item in value:
            yield from iter_export_values(item)
        return
    if not isinstance(value, dict):
        return
    results = value.get("results")
    if isinstance(results, list):
        for result in results:
            if isinstance(result, dict):
                total = result.get("estimatedTotalHits")
                total_value = total if isinstance(total, int) else None
                hits = result.get("hits")
                if isinstance(hits, list):
                    for hit in hits:
                        if isinstance(hit, dict):
                            yield hit, total_value
        return
    hits = value.get("hits")
    if isinstance(hits, list):
        total = value.get("estimatedTotalHits")
        total_value = total if isinstance(total, int) else None
        for hit in hits:
            if isinstance(hit, dict):
                yield hit, total_value
        return
    if any(key in value for key in ("source_id", "body", "title")):
        yield value, None


def load_exports(paths: list[Path]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows_by_id: dict[str, dict[str, Any]] = {}
    receipts: list[dict[str, Any]] = []
    for path in paths:
        if not path.is_file():
            raise CanaryError(f"search export does not exist: {path}")
        count = 0
        estimate: int | None = None
        for row, maybe_estimate in iter_export_values(read_json_or_jsonl(path)):
            count += 1
            if maybe_estimate is not None:
                estimate = maybe_estimate
            row_id = compact_text(row.get("id"))
            if not row_id:
                row_id = hashlib.sha256(
                    json.dumps(row, ensure_ascii=False, sort_keys=True).encode("utf-8")
                ).hexdigest()
            rows_by_id.setdefault(row_id, row)
        receipts.append({"path": str(path), "rows": count, "estimated_total_hits": estimate})
    return list(rows_by_id.values()), receipts


def load_config(path: Path) -> dict[str, Any]:
    value = read_json_or_jsonl(path)
    if not isinstance(value, dict) or value.get("schema_version") != "base2026.evidence-map-canary-config.v1":
        raise CanaryError(f"unsupported evidence-map config schema: {path}")
    maps = value.get("maps")
    if not isinstance(maps, list) or not maps:
        raise CanaryError("evidence-map config must contain at least one map")
    seen: set[str] = set()
    for item in maps:
        if not isinstance(item, dict):
            raise CanaryError("each evidence-map config item must be an object")
        slug = compact_text(item.get("slug"))
        if not SLUG_RE.fullmatch(slug) or slug in seen:
            raise CanaryError(f"invalid or duplicate map slug: {slug!r}")
        seen.add(slug)
        for field in ("topic_id", "title", "meta_description", "target_intent", "answer", "scope"):
            if not compact_text(item.get(field)):
                raise CanaryError(f"map {slug} is missing {field}")
        if len(compact_text(item["meta_description"])) > 160:
            raise CanaryError(f"map {slug} meta_description exceeds 160 characters")
        actions = item.get("actions")
        if not isinstance(actions, list) or len(actions) < 3 or any(not compact_text(action) for action in actions):
            raise CanaryError(f"map {slug} needs at least three non-empty actions")
    return value


def topic_matches(row: dict[str, Any], topic_id: str) -> bool:
    topics = {slugify(item) for item in json_list(row.get("topics"))}
    labels = {slugify(item) for item in json_list(row.get("topic_labels"))}
    return topic_id in topics or topic_id in labels


def row_quality(row: dict[str, Any]) -> tuple[float, str, str]:
    body = compact_text(row.get("body"))
    title = compact_text(row.get("title"))
    source_url = compact_text(row.get("source_url"))
    published = compact_text(row.get("published_date"))[:10]
    quality = (
        min(len(body), 320) / 320
        + min(len(title), 220) / 220
        + (0.5 if source_url_is_public(source_url) else 0)
        + (0.25 if word_count(body) >= 12 else 0)
    )
    return quality, published, compact_text(row.get("id"))


def select_evidence(rows: list[dict[str, Any]], topic_id: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
    matching = [row for row in rows if topic_matches(row, topic_id)]
    rejected = 0
    available: list[dict[str, Any]] = []
    for row in matching:
        reasons = public_row_reasons(row)
        if reasons or len(compact_text(row.get("body"))) < 40 or len(compact_text(row.get("title"))) < 20:
            rejected += 1
            continue
        available.append(row)
    available.sort(key=row_quality, reverse=True)
    selected: list[dict[str, Any]] = []
    used_sources: set[str] = set()
    used_creators: set[str] = set()
    used_fingerprints: set[str] = set()
    while available and len(selected) < MAX_EVIDENCE_CARDS:
        candidates = [
            row
            for row in available
            if compact_text(row.get("source_id")) not in used_sources
            and evidence_fingerprint(row) not in used_fingerprints
        ]
        if not candidates:
            break
        chosen = max(
            candidates,
            key=lambda row: (
                int(creator_for(row) not in used_creators),
                int(compact_text(row.get("source_id")) not in used_sources),
                row_quality(row),
            ),
        )
        available.remove(chosen)
        selected.append(chosen)
        used_sources.add(compact_text(chosen.get("source_id")))
        used_creators.add(creator_for(chosen))
        used_fingerprints.add(evidence_fingerprint(chosen))
    return selected, {"matching_rows": len(matching), "rejected_rows": rejected, "usable_rows": len(available) + len(selected)}


def existing_canonical_urls(output_dir: Path) -> set[str]:
    canonical_re = re.compile(r'<link\s+[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', re.IGNORECASE)
    reverse_re = re.compile(r'<link\s+[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\']canonical["\']', re.IGNORECASE)
    urls: set[str] = set()
    if not output_dir.exists():
        return urls
    for path in output_dir.rglob("*.html"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if CANARY_MARKER in text:
            continue
        urls.update(canonical_re.findall(text))
        urls.update(reverse_re.findall(text))
    return urls


def is_managed(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        return CANARY_MARKER in path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False


def assert_writable_managed_path(path: Path) -> None:
    if path.exists() and not is_managed(path):
        raise CanaryError(f"refusing to overwrite unmanaged public file: {path}")


def write_managed(path: Path, payload: str) -> None:
    assert_writable_managed_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)


def internal_routes(candidate: dict[str, Any], eligible_slugs: list[str]) -> list[str]:
    routes = [
        "/evidence-maps",
        "/workspace/?q=" + quote(candidate["topic_id"], safe=""),
        "/methodology",
    ]
    routes.extend(f"/evidence-maps/{slug}" for slug in eligible_slugs if slug != candidate["slug"])
    return list(dict.fromkeys(routes))


def candidate_metrics(
    item: dict[str, Any],
    rows: list[dict[str, Any]],
    base_url: str,
    output_dir: Path,
    all_slugs: list[str],
) -> dict[str, Any]:
    selected, row_counts = select_evidence(rows, item["topic_id"])
    source_ids = sorted({compact_text(row.get("source_id")) for row in selected if compact_text(row.get("source_id"))})
    creators = sorted({creator_for(row) for row in selected if creator_for(row)})
    fingerprints = {evidence_fingerprint(row) for row in selected}
    evidence_count = len(fingerprints)
    evidence_ratio = round(evidence_count / len(selected), 3) if selected else 0
    answer = compact_text(item["answer"])
    scope = compact_text(item["scope"])
    actions = [compact_text(action) for action in item["actions"]]
    visible_words = word_count(
        " ".join(
            [answer, scope, *actions]
            + [truncate_words(compact_text(row.get("title")), 220) for row in selected]
            + [public_excerpt(row.get("body")) for row in selected]
        )
    )
    route = f"/evidence-maps/{item['slug']}"
    canonical = base_url.rstrip("/") + route
    target_path = output_dir / "evidence-maps" / f"{item['slug']}.html"
    existing_urls = existing_canonical_urls(output_dir)
    route_collision = target_path.exists() and not is_managed(target_path)
    canonical_unique = canonical not in existing_urls and not route_collision
    links = internal_routes({**item, "slug": item["slug"]}, all_slugs)
    unique_score = round(min(evidence_count / MAX_EVIDENCE_CARDS, 1) * 15 + evidence_ratio * 10)
    diversity_score = round(min(len(source_ids) / 6, 1) * 10 + min(len(creators) / 3, 1) * 10)
    utility_score = round(
        min(word_count(answer) / 55, 1) * 12
        + min(len(actions) / 3, 1) * 8
        + min(word_count(scope) / 20, 1) * 5
    )
    canonical_score = 15 if canonical_unique else 0
    link_score = 15 if len(links) >= 3 else round(len(links) / 3 * 15)
    score = unique_score + diversity_score + utility_score + canonical_score + link_score
    gates = {
        "unique_evidence": evidence_count >= MIN_EVIDENCE_CARDS and evidence_ratio >= 0.75,
        "source_diversity": len(source_ids) >= MIN_SOURCE_COUNT and len(creators) >= MIN_CREATOR_COUNT,
        "substantive_answer_utility": word_count(answer) >= MIN_ANSWER_WORDS and len(actions) >= 3 and visible_words >= MIN_VISIBLE_WORDS,
        "canonical_uniqueness": canonical_unique,
        "internal_link_support": len(links) >= 3,
        "public_safety": bool(selected) and all(not public_row_reasons(row) for row in selected),
    }
    reasons: list[str] = []
    if row_counts["matching_rows"] == 0:
        reasons.append("NO_PUBLIC_TOPIC_MATCHES")
    if evidence_count < MIN_EVIDENCE_CARDS or evidence_ratio < 0.75:
        reasons.append("INSUFFICIENT_UNIQUE_EVIDENCE")
    if len(source_ids) < MIN_SOURCE_COUNT or len(creators) < MIN_CREATOR_COUNT:
        reasons.append("INSUFFICIENT_SOURCE_DIVERSITY")
    if word_count(answer) < MIN_ANSWER_WORDS or len(actions) < 3 or visible_words < MIN_VISIBLE_WORDS:
        reasons.append("INSUFFICIENT_SUBSTANTIVE_UTILITY")
    if not canonical_unique:
        reasons.append("CANONICAL_ROUTE_COLLISION")
    if len(links) < 3:
        reasons.append("INSUFFICIENT_INTERNAL_LINK_SUPPORT")
    if not gates["public_safety"]:
        reasons.append("PUBLIC_SAFETY_GATE_FAILED")
    eligible = score >= MIN_SCORE and not reasons
    latest_date = max((compact_text(row.get("published_date"))[:10] for row in selected if DATE_RE.match(compact_text(row.get("published_date")))), default="")
    return {
        "slug": item["slug"],
        "topic_id": item["topic_id"],
        "title": item["title"],
        "target_intent": item["target_intent"],
        "route": route,
        "canonical": canonical,
        "score": score,
        "eligible": eligible,
        "gates": gates,
        "rejection_reasons": sorted(set(reasons)),
        "counts": {
            "matching_rows": row_counts["matching_rows"],
            "usable_rows": row_counts["usable_rows"],
            "rejected_rows": row_counts["rejected_rows"],
            "selected_evidence": len(selected),
            "unique_evidence": evidence_count,
            "unique_evidence_ratio": evidence_ratio,
            "source_ids": len(source_ids),
            "creators": len(creators),
            "visible_words": visible_words,
            "answer_words": word_count(answer),
            "internal_links": len(links),
        },
        "score_breakdown": {
            "unique_evidence": unique_score,
            "source_diversity": diversity_score,
            "substantive_answer_utility": utility_score,
            "canonical_uniqueness": canonical_score,
            "internal_link_support": link_score,
        },
        "source_ids": source_ids,
        "creator_handles": creators,
        "latest_source_date": latest_date,
        "selected_rows": selected,
        "config": item,
    }


def source_label(row: dict[str, Any]) -> str:
    labels = json_list(row.get("topic_labels"))
    topics = json_list(row.get("topics"))
    return labels[0] if labels else (topics[0] if topics else "Public source record")


def render_head(title: str, description: str, canonical: str, json_ld: dict[str, Any]) -> str:
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{escape(canonical)}">
<meta property="og:type" content="article">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{escape(canonical)}">
<meta property="og:image" content="https://base2026.dev/static/assets/base2026-ai-visibility-card.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Base2026 public-source intelligence">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{escape(title)}">
<meta name="twitter:description" content="{escape(description)}">
<meta name="twitter:image" content="https://base2026.dev/static/assets/base2026-ai-visibility-card.png">
<meta name="twitter:image:alt" content="Base2026 public-source intelligence">
<script type="application/ld+json">{safe_json(json_ld)}</script>
<link rel="stylesheet" href="/static/base2026-core.css?v=20260820-b26v1">
<link rel="stylesheet" href="/static/evidence-map-canary.css?v=20260901">"""


def render_document(title: str, description: str, canonical: str, json_ld: dict[str, Any], body: str, header: str, footer: str) -> str:
    return f"""<!doctype html>
<!-- {CANARY_MARKER} -->
<html lang="en">
<head>
{render_head(title, description, canonical, json_ld)}
</head>
<body class="b26-evidence-map-page">
{header}
{body}
{footer}
</body>
</html>
"""


def stat_grid(stats: list[tuple[str, str]]) -> str:
    return '<div class="b26-map-stat-grid">' + "".join(
        f'<div class="b26-map-stat"><strong>{escape(value)}</strong><span>{escape(label)}</span></div>'
        for value, label in stats
    ) + "</div>"


def render_hub(candidates: list[dict[str, Any]], as_of: str, base_url: str, header: str, footer: str) -> str:
    total_records = sum(item["counts"]["selected_evidence"] for item in candidates)
    total_creators = len({handle for item in candidates for handle in item["creator_handles"]})
    canonical = base_url.rstrip("/") + "/evidence-maps"
    item_list = [
        {
            "@type": "ListItem",
            "position": index,
            "name": item["title"],
            "url": base_url.rstrip("/") + item["route"],
        }
        for index, item in enumerate(candidates, 1)
    ]
    json_ld = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "@id": f"{canonical}#webpage",
        "url": canonical,
        "name": "Evidence maps | Base2026",
        "description": "Small, source-backed evidence maps built from public Base2026 search records.",
        "mainEntity": {"@type": "ItemList", "itemListElement": item_list},
        "publisher": {"@type": "Organization", "name": "Base2026", "url": base_url.rstrip("/") + "/"},
    }
    cards = "".join(
        f"""<a class="b26-map-card" href="{escape(item['route'])}">
  <p class="b26-map-kicker">{escape(item['topic_id'])}</p>
  <h3>{escape(item['title'])}</h3>
  <p>{escape(item['target_intent'])}</p>
  <p class="b26-map-meta">Score {item['score']}/100 · {item['counts']['selected_evidence']} records · {item['counts']['creators']} creators</p>
</a>"""
        for item in candidates
    )
    body = f"""<main data-b26-shell>
  <section class="b26-map-hero">
    <p class="b26-eyebrow">Canary · public D1 evidence</p>
    <h1>Evidence maps that stay useful.</h1>
    <p class="b26-map-lede">A small indexable corpus for questions that benefit from comparison: each map combines a clear answer, public source excerpts, attribution and a practical next step.</p>
    <div class="b26-map-actions">
      <a class="b26-button--primary" href="/workspace/">Search public evidence</a>
      <a class="b26-button--secondary" href="/methodology">Read the methodology</a>
    </div>
  </section>
  <section class="b26-map-section" aria-labelledby="canary-maps-title">
    <header><h2 id="canary-maps-title">Canary maps</h2><p>These pages passed the same admission gate for evidence uniqueness, source diversity, useful answer content, canonical uniqueness and internal-link support.</p></header>
    <div class="b26-map-grid">{cards}</div>
    {stat_grid([(str(len(candidates)), "eligible map pages"), (str(total_records), "selected public records"), (str(total_creators), "distinct creators"), (as_of, "snapshot date")])}
  </section>
  <section class="b26-map-section" aria-labelledby="rubric-title">
    <header><h2 id="rubric-title">Eligibility rubric</h2><p>One strong page is more useful than a large set of interchangeable keyword variants.</p></header>
    <div class="b26-map-rubric"><table><thead><tr><th>Gate</th><th>Admission rule</th><th>Weight</th></tr></thead><tbody>
      <tr><td>Unique evidence</td><td>At least four distinct public excerpts with a 0.75+ uniqueness ratio.</td><td>25</td></tr>
      <tr><td>Source diversity</td><td>At least four source IDs from at least three creator handles.</td><td>20</td></tr>
      <tr><td>Answer and utility</td><td>A direct answer, scope note, three actions and enough visible substance to stand alone.</td><td>25</td></tr>
      <tr><td>Canonical uniqueness</td><td>One extensionless route that does not collide with an existing public page.</td><td>15</td></tr>
      <tr><td>Internal support</td><td>Links to the hub, search workspace and methodology, plus related maps when available.</td><td>15</td></tr>
    </tbody></table></div>
  </section>
  <section class="b26-map-section b26-map-callout" aria-label="Public boundary">
    <p>Snapshot captured {escape(as_of)} from public D1 search exports. Pages contain short attributed excerpts only; they do not publish raw media, private material or a full transcript. Source posts remain the canonical source.</p>
  </section>
</main>"""
    return render_document("Evidence maps | Base2026", "Small, source-backed evidence maps built from public Base2026 search records.", canonical, json_ld, body, header, footer)


def render_map(item: dict[str, Any], eligible_slugs: list[str], as_of: str, base_url: str, header: str, footer: str) -> str:
    config = item["config"]
    canonical = item["canonical"]
    citations = [compact_text(row.get("source_url")) for row in item["selected_rows"] if source_url_is_public(compact_text(row.get("source_url")))]
    json_ld = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "@id": f"{canonical}#webpage",
        "url": canonical,
        "name": config["title"],
        "description": config["meta_description"],
        "about": config["target_intent"],
        "isBasedOn": citations,
        "citation": citations,
        "dateModified": as_of,
        "publisher": {"@type": "Organization", "name": "Base2026", "url": base_url.rstrip("/") + "/"},
    }
    evidence_cards = []
    for row in item["selected_rows"]:
        source_url = compact_text(row.get("source_url"))
        creator = creator_for(row)
        published = compact_text(row.get("published_date"))[:10]
        evidence_cards.append(
            f"""<article class="b26-map-record">
  <p class="b26-map-record-meta">{escape(creator)}{(' · ' + escape(published)) if published else ''} · {escape(source_label(row))}</p>
  <h3>{escape(truncate_words(compact_text(row.get('title')), 220))}</h3>
  <blockquote>{escape(public_excerpt(row.get('body')))}</blockquote>
  <p><a href="{escape(source_url)}" target="_blank" rel="nofollow noopener noreferrer">Open the original TikTok post</a></p>
</article>"""
        )
    related = [slug for slug in eligible_slugs if slug != item["slug"]]
    related_html = "".join(
        f'<a class="b26-map-card" href="/evidence-maps/{escape(slug)}"><p class="b26-map-kicker">Related evidence map</p><h3>{escape(slug.replace("-", " "))}</h3><p>Compare another public-source cluster in the canary.</p></a>'
        for slug in related
    )
    actions = "".join(f"<li>{escape(action)}</li>" for action in config["actions"])
    body = f"""<main data-b26-shell>
  <section class="b26-map-hero">
    <p class="b26-eyebrow">Evidence map · {escape(config['topic_id'])}</p>
    <h1>{escape(config['title'])}</h1>
    <p class="b26-map-lede">{escape(config['target_intent'])}</p>
    <div class="b26-map-actions">
      <a class="b26-button--primary" href="/evidence-maps">Back to evidence maps</a>
      <a class="b26-button--secondary" href="/workspace/?q={escape(quote(config['topic_id'], safe=''))}">Search this topic</a>
    </div>
  </section>
  <section class="b26-map-section" aria-labelledby="answer-title">
    <header><h2 id="answer-title">Answer first</h2></header>
    <div class="b26-map-callout"><p>{escape(config['answer'])}</p></div>
    <div class="b26-map-callout"><p><strong>How to read it:</strong> {escape(config['scope'])}</p></div>
  </section>
  <section class="b26-map-section" aria-labelledby="snapshot-title">
    <header><h2 id="snapshot-title">Evidence at a glance</h2><p>Counts describe the selected public records used for this page, not the size of the full database.</p></header>
    {stat_grid([(str(item['counts']['selected_evidence']), "selected excerpts"), (str(item['counts']['source_ids']), "source IDs"), (str(item['counts']['creators']), "creator handles"), (item['latest_source_date'] or as_of, "latest source date")])}
  </section>
  <section class="b26-map-section" aria-labelledby="actions-title">
    <header><h2 id="actions-title">A practical next pass</h2><p>Use the records as prompts for a bounded review, not as a promise of rankings or citations.</p></header>
    <ol class="b26-map-actions-list">{actions}</ol>
  </section>
  <section class="b26-map-section" aria-labelledby="records-title">
    <header><h2 id="records-title">Public evidence records</h2><p>Each item is a short public D1 excerpt with source attribution. A leading ellipsis marks a stored segment that begins mid-sentence. Read the original post for context and current platform details.</p></header>
    <div class="b26-map-records">{''.join(evidence_cards)}</div>
  </section>
  <section class="b26-map-section" aria-labelledby="boundary-title">
    <header><h2 id="boundary-title">Scope and boundary</h2></header>
    <div class="b26-map-callout"><p>This page was generated from a {escape(as_of)} public search export. It contains no raw media, private notes or full transcript. Base2026 is an evidence index; the original creator and post remain the canonical source. See <a href="/methodology">methodology</a>, <a href="/source-policy">source policy</a> and <a href="/opt-out">creator rights</a>.</p></div>
  </section>
  {f'<section class="b26-map-section" aria-labelledby="related-title"><header><h2 id="related-title">Related maps</h2></header><div class="b26-map-grid">{related_html}</div></section>' if related_html else ''}
</main>"""
    return render_document(f"{config['title']} | Base2026", config["meta_description"], canonical, json_ld, body, header, footer)


def render_sitemap(candidates: list[dict[str, Any]], as_of: str, base_url: str) -> str:
    urls = [base_url.rstrip("/") + "/evidence-maps"] + [base_url.rstrip("/") + item["route"] for item in candidates]
    body = "\n".join(f"  <url><loc>{escape(url)}</loc><lastmod>{escape(as_of)}</lastmod></url>" for url in urls)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- {CANARY_MARKER} -->
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}
</urlset>
"""


def update_sitemap_index(path: Path, shard_url: str, as_of: str) -> bool:
    if not path.is_file():
        raise CanaryError(f"sitemap index does not exist: {path}")
    text = path.read_text(encoding="utf-8")
    if "<sitemapindex" not in text or "</sitemapindex>" not in text:
        raise CanaryError(f"sitemap target is not a sitemap index: {path}")
    if shard_url in text:
        return False
    entry = f"  <sitemap><loc>{escape(shard_url)}</loc><lastmod>{escape(as_of)}</lastmod></sitemap>\n"
    updated = text.replace("</sitemapindex>", entry + "</sitemapindex>", 1)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(updated)
    return True


def build_canary(
    exports: list[Path],
    config_path: Path,
    output_dir: Path,
    base_url: str,
    as_of: str,
    sitemap_index: Path | None = None,
    min_score: int = MIN_SCORE,
) -> dict[str, Any]:
    if not DATE_RE.match(as_of):
        raise CanaryError(f"as_of must start with YYYY-MM-DD: {as_of}")
    config = load_config(config_path)
    rows, input_receipts = load_exports(exports)
    header = HEADER_TEMPLATE.read_text(encoding="utf-8").strip()
    footer = FOOTER_TEMPLATE.read_text(encoding="utf-8").strip()
    css = CSS_TEMPLATE.read_text(encoding="utf-8")
    output_dir.mkdir(parents=True, exist_ok=True)
    all_slugs = [compact_text(item["slug"]) for item in config["maps"]]
    candidates = [candidate_metrics(item, rows, base_url, output_dir, all_slugs) for item in config["maps"]]
    eligible = [item for item in candidates if item["score"] >= min_score and not item["rejection_reasons"]]
    eligible_slugs = [item["slug"] for item in eligible]
    if not eligible:
        raise CanaryError("no evidence-map candidate passed the eligibility gate")
    for item in eligible:
        page = render_map(item, eligible_slugs, as_of, base_url, header, footer)
        write_managed(output_dir / "evidence-maps" / f"{item['slug']}.html", page)
    write_managed(output_dir / "evidence-maps.html", render_hub(eligible, as_of, base_url, header, footer))
    write_managed(output_dir / "static" / "evidence-map-canary.css", css)
    shard_path = output_dir / "sitemaps" / "evidence-maps-canary.xml"
    write_managed(shard_path, render_sitemap(eligible, as_of, base_url))
    shard_url = base_url.rstrip("/") + "/sitemaps/evidence-maps-canary.xml"
    index_updated = False
    if sitemap_index is not None:
        index_updated = update_sitemap_index(sitemap_index, shard_url, as_of)
    ledger_candidates: list[dict[str, Any]] = []
    for item in candidates:
        ledger_item = {key: value for key, value in item.items() if key not in {"selected_rows", "config"}}
        ledger_candidates.append(ledger_item)
    ledger = {
        "schema_version": CANARY_SCHEMA,
        "managed_by": CANARY_MARKER,
        "canary_id": config.get("canary_id", as_of),
        "generated_at": as_of,
        "input": {
            "index_uid": INDEX_UID,
            "files": input_receipts,
            "unique_rows": len(rows),
            "estimated_total_hits_sum": sum(receipt["estimated_total_hits"] or 0 for receipt in input_receipts),
            "private_source_files_read": False,
        },
        "rubric": {
            "min_score": min_score,
            "weights": {"unique_evidence": 25, "source_diversity": 20, "substantive_answer_utility": 25, "canonical_uniqueness": 15, "internal_link_support": 15},
            "hard_requirements": {"selected_evidence": MIN_EVIDENCE_CARDS, "source_ids": MIN_SOURCE_COUNT, "creators": MIN_CREATOR_COUNT, "answer_words": MIN_ANSWER_WORDS, "visible_words": MIN_VISIBLE_WORDS, "unique_evidence_ratio": 0.75, "internal_links": 3},
        },
        "eligible_count": len(eligible),
        "rejected_count": len(candidates) - len(eligible),
        "candidates": ledger_candidates,
        "output": {"hub": "/evidence-maps", "sitemap_shard": shard_url, "sitemap_index_updated": index_updated},
    }
    write_managed(output_dir / "evidence-map-canary-ledger.json", json.dumps(ledger, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return ledger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a gated, public-safe Base2026 evidence-map canary.")
    parser.add_argument("--search-export", action="append", required=True, type=Path, help="Public search API JSON/JSONL export; repeat for multiple topic-facet exports.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, required=True, help="Existing public release-root artifact or a clean candidate directory.")
    parser.add_argument("--base-url", default="https://base2026.dev")
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument("--sitemap-index", type=Path, help="Optional existing sitemap index to link to the generated shard.")
    parser.add_argument("--min-score", type=int, default=MIN_SCORE)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        ledger = build_canary(args.search_export, args.config, args.output_dir, args.base_url, args.as_of, args.sitemap_index, args.min_score)
    except (CanaryError, OSError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({key: ledger[key] for key in ("canary_id", "eligible_count", "rejected_count", "output")}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
