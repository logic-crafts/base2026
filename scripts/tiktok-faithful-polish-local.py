from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TIKTOK = ROOT / "12_knowledge-base" / "sources" / "tiktok"
VIDEOS_CSV = TIKTOK / "videos.csv"
CLEAN_DIR = TIKTOK / "transcripts" / "clean"
POLISHED_DIR = TIKTOK / "transcripts" / "polished"
QA_DIR = TIKTOK / "transcripts" / "polished-qa"
VIDEO_ID_RE = re.compile(r"^## Video\s+(\d+)\s*$", re.MULTILINE)


TERM_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\ba\s*i\b", re.IGNORECASE), "AI"),
    (re.compile(r"\ba\s*e\s*o\b", re.IGNORECASE), "AEO"),
    (re.compile(r"\bg\s*e\s*o\b", re.IGNORECASE), "GEO"),
    (re.compile(r"\bs\s*e\s*o\b", re.IGNORECASE), "SEO"),
    (re.compile(r"\bs\s+c\s+o\b", re.IGNORECASE), "SEO"),
    (re.compile(r"\bs\s+0\b", re.IGNORECASE), "SEO"),
    (re.compile(r"\ba\s+r\s+s\s+c\s+o\b", re.IGNORECASE), "AI SEO"),
    (re.compile(r"\ba\s+r\s+models\b", re.IGNORECASE), "AI models"),
    (re.compile(r"\bar\s+models\b", re.IGNORECASE), "AI models"),
    (re.compile(r"\ba\s+r\s+seo\b|\bar\s+seo\b", re.IGNORECASE), "AI SEO"),
    (re.compile(r"\ba\s+r\s+friendly\b|\bar\s+friendly\b", re.IGNORECASE), "AI-friendly"),
    (re.compile(r"\ba\s+r\s+era\b|\bar\s+era\b", re.IGNORECASE), "AI era"),
    (re.compile(r"\bl\s*l\s*m(?:s)?\b", re.IGNORECASE), lambda m: "LLMs" if m.group(0).lower().endswith("s") else "LLM"),
    (re.compile(r"\bchat\s*g\s*p\s*t\b", re.IGNORECASE), "ChatGPT"),
    (re.compile(r"\bchat\s*g\s*b\s*t\b", re.IGNORECASE), "ChatGPT"),
    (re.compile(r"\bchat[,\s]+g[,\s]+b\s*t\b", re.IGNORECASE), "ChatGPT"),
    (re.compile(r"\bchat\s+gpt\b", re.IGNORECASE), "ChatGPT"),
    (re.compile(r"\bchatgpt\.comslash", re.IGNORECASE), "ChatGPT.com/"),
    (re.compile(r"\bopen\s+ai\b", re.IGNORECASE), "OpenAI"),
    (re.compile(r"\bpaypal\b", re.IGNORECASE), "PayPal"),
    (re.compile(r"\bc\s+m\s+s\b", re.IGNORECASE), "CMS"),
    (re.compile(r"\bm\s+dash\b", re.IGNORECASE), "EmDash"),
    (re.compile(r"\bf\s*a\s*q\b", re.IGNORECASE), "FAQ"),
    (re.compile(r"\bh\s+ones\b", re.IGNORECASE), "H1s"),
    (re.compile(r"\bweb\s+core\s+vitals\b", re.IGNORECASE), "Core Web Vitals"),
    (re.compile(r"\bw\s*p\s+rocket\b", re.IGNORECASE), "WP Rocket"),
    (re.compile(r"\bsure\s+m\s*v\s*seven\b", re.IGNORECASE), "Shure MV7"),
    (re.compile(r"\bsr\s+m\s*v\s*7\b", re.IGNORECASE), "Shure MV7"),
    (re.compile(r"\blead\s+ferno\b", re.IGNORECASE), "Leadferno"),
    (re.compile(r"\bharry\s+ilyas\b", re.IGNORECASE), "Gary Illyes"),
    (re.compile(r"\bqwoted\b", re.IGNORECASE), "Qwoted"),
    (re.compile(r"\bn\s+a\s+n\b", re.IGNORECASE), "n8n"),
    (re.compile(r"\bschema\s+writer\s+dot\s+ai\b", re.IGNORECASE), "Schemawriter.ai"),
    (re.compile(r"\bcomment\s+browser\b", re.IGNORECASE), "Comet browser"),
    (re.compile(r"\bclaud\b", re.IGNORECASE), "Claude"),
    (re.compile(r"\bcompact\s+keywords\.com\b", re.IGNORECASE), "compactkeywords.com"),
    (re.compile(r"\bAI\s+podcast\s+Matcher\s+com\b", re.IGNORECASE), "AIPodcastMatcher.com"),
    (re.compile(r"\bAI\s+video\s+editor\s+descriptor\b", re.IGNORECASE), "AI video editor Descript"),
    (re.compile(r"\bcloud\s+projects\b", re.IGNORECASE), "Claude Projects"),
    (re.compile(r"\bsource\s+of\s+sources\.com\b", re.IGNORECASE), "sourceofsources.com"),
    (
        re.compile(r"\bWashington Post,\s*Tripadvisor,\s*MPR,\s*New York Times\b", re.IGNORECASE),
        "Washington Post, Tripadvisor, NPR, New York Times",
    ),
    (re.compile(r"\bnotebook\s+LM\b", re.IGNORECASE), "NotebookLM"),
    (re.compile(r"\bpowerpoint\b", re.IGNORECASE), "PowerPoint"),
    (re.compile(r"\bEli\s+Soren(?:s|c)on\b", re.IGNORECASE), "Eli Schwartz"),
    (re.compile(r"\br\s+slash\s+(?:min\s*max|mid\s+max)\s+marketing\b", re.IGNORECASE), "r/MinMaxMarketing"),
    (re.compile(r"\bmin\s+max\s+marketing\b", re.IGNORECASE), "MinMaxMarketing"),
    (re.compile(r"\bmid\s+max\s+marketing\b", re.IGNORECASE), "MinMaxMarketing"),
    (re.compile(r"\bgoogle\s+my\s+business\b", re.IGNORECASE), "Google My Business"),
    (re.compile(r"\bcopilot\b", re.IGNORECASE), "Copilot"),
    (re.compile(r"\bgemini\s+three\s+point\s+one\b", re.IGNORECASE), "Gemini 3.1"),
    (re.compile(r"\bgemini\s+four\b", re.IGNORECASE), "Gemini 4"),
    (re.compile(r"\bgemini\s+five\b", re.IGNORECASE), "Gemini 5"),
    (re.compile(r"\bgoogle\s+ads\b", re.IGNORECASE), "Google Ads"),
    (re.compile(r"\bgoogle\s+search\s+console\b", re.IGNORECASE), "Google Search Console"),
    (re.compile(r"\bgoogle\s+business\s+profile\b", re.IGNORECASE), "Google Business Profile"),
    (re.compile(r"\bperplexity\b", re.IGNORECASE), "Perplexity"),
    (re.compile(r"\bgemini\b", re.IGNORECASE), "Gemini"),
    (re.compile(r"\bclaude\b", re.IGNORECASE), "Claude"),
    (re.compile(r"\bgrok\b", re.IGNORECASE), "Grok"),
    (re.compile(r"\breddit\b", re.IGNORECASE), "Reddit"),
    (re.compile(r"\btiktok\b", re.IGNORECASE), "TikTok"),
    (re.compile(r"\byoutube\b", re.IGNORECASE), "YouTube"),
    (re.compile(r"\bshopify\b", re.IGNORECASE), "Shopify"),
]


UNCERTAIN_RE = re.compile(
    r"\b(inaudible|unclear|unknown|clawbo|skema|wow wow)\b",
    re.IGNORECASE,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_rows() -> list[dict[str, str]]:
    if not VIDEOS_CSV.exists():
        return []
    with VIDEOS_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_batch_video_ids(batch_dir: Path | None) -> set[str]:
    if not batch_dir:
        return set()
    if not batch_dir.exists():
        return set()
    ids: set[str] = set()
    for path in sorted(batch_dir.glob("batch-*.md")):
        ids.update(VIDEO_ID_RE.findall(path.read_text(encoding="utf-8", errors="replace")))
    return ids


def normalize_whitespace(text: str) -> str:
    text = text.replace("\ufeff", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def apply_terms(text: str) -> tuple[str, Counter[str]]:
    counts: Counter[str] = Counter()
    out = text
    for pattern, replacement in TERM_REPLACEMENTS:
        def repl(match: re.Match[str]) -> str:
            counts[pattern.pattern] += 1
            return replacement(match) if callable(replacement) else replacement

        out = pattern.sub(repl, out)
    return out, counts


def sentence_split(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    pieces = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", text)
    return [piece.strip() for piece in pieces if piece.strip()]


def paragraphize(text: str, max_sentences: int = 4, max_chars: int = 620) -> str:
    sentences = sentence_split(text)
    if not sentences:
        return text
    paragraphs: list[str] = []
    current: list[str] = []
    current_len = 0
    for sentence in sentences:
        if current and (len(current) >= max_sentences or current_len + len(sentence) > max_chars):
            paragraphs.append(" ".join(current).strip())
            current = []
            current_len = 0
        current.append(sentence)
        current_len += len(sentence) + 1
    if current:
        paragraphs.append(" ".join(current).strip())
    return "\n\n".join(paragraphs)


def words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9']+", text.lower())


def preservation_score(raw: str, polished: str) -> float:
    raw_words = words(raw)
    polished_words = words(polished)
    if not raw_words:
        return 1.0 if not polished_words else 0.0
    counts: Counter[str] = Counter(raw_words)
    kept = 0
    for word in polished_words:
        if counts[word] > 0:
            counts[word] -= 1
            kept += 1
    return kept / max(len(raw_words), len(polished_words), 1)


def polish_text(raw: str) -> tuple[str, dict]:
    normalized = normalize_whitespace(raw)
    term_fixed, replacements = apply_terms(normalized)
    paragraphized = paragraphize(term_fixed)
    polished = normalize_whitespace(paragraphized)
    return polished, {
        "replacement_count": sum(replacements.values()),
        "replacement_patterns": dict(replacements),
        "raw_word_count": len(words(raw)),
        "polished_word_count": len(words(polished)),
        "paragraph_count": len([p for p in polished.split("\n\n") if p.strip()]),
        "preservation_score": round(preservation_score(raw, polished), 4),
    }


def qa_status(raw: str, polished: str, metrics: dict) -> tuple[str, list[str]]:
    notes: list[str] = [
        "Local faithful polish: whitespace, obvious acronym/entity casing, and paragraph breaks only.",
        "No summarization, no claims, no translation, no invented facts.",
    ]
    status = "pass"
    if metrics["raw_word_count"] < 12:
        status = "needs_review"
        notes.append("Transcript has too few words for reliable public use.")
    if metrics["preservation_score"] < 0.86:
        status = "needs_review"
        notes.append("Preservation score is below the local polish threshold.")
    if UNCERTAIN_RE.search(raw):
        status = "needs_review"
        notes.append("Raw transcript contains wording that may need audio/source review.")
    if polished and polished[-1] not in ".!?":
        status = "needs_review"
        notes.append("Transcript appears to end without terminal punctuation.")
    return status, notes


def process(args: argparse.Namespace) -> dict:
    batch_ids = read_batch_video_ids(args.batch_dir)
    target_ids = set(args.video_id or []) | batch_ids
    eligible_statuses = {"transcribed"}
    if args.include_source_review:
        eligible_statuses.add("needs_source_review")
    rows = [
        row for row in read_rows()
        if row.get("transcript_status") in eligible_statuses
        and (CLEAN_DIR / f"{row.get('video_id')}.txt").exists()
        and (not target_ids or row.get("video_id") in target_ids)
    ]
    rows.sort(key=lambda row: (row.get("published_at") or "", row.get("video_id") or ""), reverse=True)
    selected: list[dict[str, str]] = []
    for row in rows:
        video_id = row.get("video_id") or ""
        polished_path = POLISHED_DIR / f"{video_id}.txt"
        qa_path = QA_DIR / f"{video_id}.json"
        if args.missing_only and polished_path.exists() and qa_path.exists():
            continue
        selected.append(row)
    if args.limit > 0:
        selected = selected[: args.limit]

    stats = {
        "selected": len(selected),
        "written": 0,
        "pass": 0,
        "needs_review": 0,
        "failed": 0,
        "dry_run": not args.apply,
        "missing_only": args.missing_only,
        "batch_dir": str(args.batch_dir) if args.batch_dir else "",
        "target_video_ids": sorted(target_ids),
        "samples": [],
    }
    if args.apply:
        POLISHED_DIR.mkdir(parents=True, exist_ok=True)
        QA_DIR.mkdir(parents=True, exist_ok=True)

    for row in selected:
        video_id = row.get("video_id") or ""
        raw_path = CLEAN_DIR / f"{video_id}.txt"
        polished_path = POLISHED_DIR / f"{video_id}.txt"
        qa_path = QA_DIR / f"{video_id}.json"
        raw = raw_path.read_text(encoding="utf-8", errors="replace")
        polished, metrics = polish_text(raw)
        status, notes = qa_status(raw, polished, metrics)
        payload = {
            "video_id": video_id,
            "creator_id": row.get("creator_id") or "",
            "url": row.get("url") or "",
            "status": status,
            "notes": notes,
            "raw_path": str(raw_path.relative_to(ROOT)),
            "polished_path": str(polished_path.relative_to(ROOT)),
            "created_at": now_iso(),
            "model_tier": "local-deterministic",
            "meaning_added": False,
            **metrics,
        }
        if args.apply:
            with polished_path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(polished + "\n")
            with qa_path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
            stats["written"] += 1
        stats[status] += 1
        if len(stats["samples"]) < args.sample:
            stats["samples"].append(
                {
                    "video_id": video_id,
                    "status": status,
                    "raw_words": metrics["raw_word_count"],
                    "polished_words": metrics["polished_word_count"],
                    "paragraphs": metrics["paragraph_count"],
                    "preservation_score": metrics["preservation_score"],
                }
            )
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Conservatively polish TikTok transcripts without LLM rewrites.")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--sample", type=int, default=8)
    parser.add_argument("--missing-only", action="store_true", default=True)
    parser.add_argument("--all", dest="missing_only", action="store_false")
    parser.add_argument("--batch-dir", type=Path, default=None, help="Optional transcript-polish-batches/<set> dir; only videos listed in batch-*.md are eligible.")
    parser.add_argument("--video-id", action="append", default=[], help="Optional exact video_id filter. May be repeated.")
    parser.add_argument(
        "--include-source-review",
        action="store_true",
        help="Allow an explicit batch/video filter to recompute polished and QA files for needs_source_review rows; does not change videos.csv.",
    )
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(process(args), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
