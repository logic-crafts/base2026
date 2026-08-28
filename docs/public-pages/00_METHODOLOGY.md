# How this source library works

Base2026 turns public short-form expert videos into attributed source records that can be searched, read, compared, and cited.

The public layer is built for discovery and verification. It is not a video re-hosting platform, not a transcript dump, and not a replacement for creator channels.

---

## Source-first records

Each public record should preserve the creator handle, platform, original source URL, publication date when available, reviewed public source text, topics, and enough Base2026-authored context for a reader to understand why the record appears in search.

The original creator source remains the canonical place to watch the full video.

## Cloud processing and transcript handling

The private Cloudflare pipeline can use public platform metadata, bounded media acquisition, Workers AI transcription, deterministic validation, and source-review receipts.

Raw captions, raw ASR, downloaded media, provider responses, extraction logs, and private review packets stay private in the protected D1/R2 processing layer and expire under bounded retention rules.

Public pages may expose reviewed polished public source text when policy allows. That text is normalized for readability, split into useful paragraphs, and surrounded by attribution, original-source links, Base2026-authored summaries, topics, source-backed insight cards, methodology, and correction/removal paths.

The distinction is important: Base2026 does not publish raw caption dumps or unreviewed transcript files as standalone content. It publishes reviewed source records that help people search what experts said and understand the context.

## Public extraction rules

Insight cards should be tied to source evidence. Topic and comparison pages should help a reader understand patterns across creators without inventing claims or declaring a winner.

AI can help transcribe, classify, summarize, and select evidence, but an automatic public projection is accepted only when it passes the exact public schema, privacy, identity, evidence, and receipt gates. Public output must remain source-backed, attributed, bounded, and correction-friendly.

## Review and correction

Base2026 keeps visible correction and removal paths because source intelligence is only useful when attribution and context can be challenged.

Creators can request attribution fixes, excerpt corrections, record removal, or future source suppression through the correction/removal page.
