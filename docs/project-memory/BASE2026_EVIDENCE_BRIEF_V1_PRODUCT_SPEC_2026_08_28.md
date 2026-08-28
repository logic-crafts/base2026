# Base2026 Evidence Brief Product V1 / API V2 Spec

Date: 2026-08-28
Status: implemented local release candidate; not a production-release receipt

## Decision

Base2026 V1 is **attributable expert-video evidence search** for SEO/GEO/AEO practitioners and small agencies.

Core action:

> Ask one professional question and receive a deterministic, source-backed Evidence Brief.

Public one-liner:

> Ask what SEO and AI-search practitioners actually said. Get a source-backed evidence brief in seconds.

The free public core is the product. No pricing, paid tier, signup gate, or broad roadmap is part of this pass. Cloudflare is below-fold credibility and operating economics, not the hero value proposition.

## V1 Scope

V1 answers questions from the publication-eligible public expert-video evidence corpus. It does not search private pipeline data, the private inbox, client data, raw transcripts, or the separate Outreach collection.

The Evidence Brief must be assembled from existing public source records, public passages, and admitted source-backed cards. It may not create a new unsupported claim to make a result sound complete.

The deployed unversioned `GET /api/evidence-brief` response is an existing
public compatibility contract (`d1-fts5-evidence-brief-v1`) and must remain
byte-shape compatible. The homepage product uses the additive
`GET/HEAD /api/evidence-brief/v2` contract below; releasing V2 must not replace
or silently change the unversioned endpoint.

## Exact Homepage Hero Copy

**Eyebrow**
`ATTRIBUTABLE EXPERT-VIDEO EVIDENCE`

**H1**
`Ask what SEO and AI-search practitioners actually said.`

**Subhead**
`Get a source-backed evidence brief in seconds. Every finding links to attributable evidence and the original source.`

**Input label**
`Your professional question`

**Input placeholder**
`e.g. How are practitioners measuring visibility in AI search?`

**Primary button**
`Get evidence brief`

**Suggested-query label**
`Try a question`

**Secondary text link**
`Browse the evidence library`

**Trust line**
`Free public research · Read-only · Sources stay attached`

Implementation authority for the root page is `templates/base2026-startup-homepage.html` through the existing release builder. Do not hand-edit the generated legacy homepage as the source of truth.

## Suggested Queries

Use these three bounded suggestions:

1. `How do experts measure AI search visibility?`
2. `How should schema support AI search?`
3. `How do practitioners prioritize content refreshes?`

Each suggestion is a real submit action, not decorative copy. It must populate the input, fire the selected-query event, and generate a brief through the same path as a custom question.

## Deterministic Retrieval Contract

For the same `normalized_question`, explicit filters, `corpus_version`, and `ranking_version`, V1 must return the same selected evidence, order, labels, and brief text. `generated_at` is a receipt and may change; the substantive brief may not.

Fixed V1 path:

1. Normalize Unicode, whitespace, case, question-framing stop words, and simple English plural suffixes without rewriting the underlying topic intent.
2. Search only the public Evidence index (`base2026_public_tiktok`) through the D1 FTS5 read-only path, requiring all remaining topic tokens and ranking with BM25.
3. Retrieve a bounded candidate set; exclude private, held, unreviewed, missing-source, and `full_transcript_public` material.
4. Group by public source record; retain the highest-ranked eligible evidence per source.
5. Select at most five findings, at most two per creator, with a stable source-ID tie-break.
6. Render only admitted public claims and exact/bounded public evidence excerpts. No free-form generative synthesis is required in V1.
7. Attach the Base2026 canonical record and original creator-source URL to every finding.
8. Return the corpus version, ranking version, coverage, and limitations with the result.

## Evidence Brief Response Contract

```json
{
  "brief_version": "base2026.evidence-brief.v2",
  "question": "string",
  "normalized_question": "string",
  "status": "full | limited | no_evidence",
  "corpus_version": "string",
  "ranking_version": "string",
  "generated_at": "ISO-8601 receipt time",
  "coverage": {
    "matched_records": 0,
    "selected_sources": 0,
    "distinct_creators": 0,
    "published_date_min": "YYYY-MM-DD | null",
    "published_date_max": "YYYY-MM-DD | null"
  },
  "findings": [
    {
      "claim": "admitted public claim",
      "evidence_excerpt": "exact bounded public excerpt",
      "creator_handle": "public handle",
      "published_date": "YYYY-MM-DD | null",
      "base2026_url": "canonical public record",
      "original_source_url": "public creator source",
      "evidence_start_seconds": "number | null",
      "evidence_end_seconds": "number | null",
      "topics": ["public topic"]
    }
  ],
  "repeated_signals": [],
  "limits": ["plain-language coverage limit"]
}
```

Display order:

1. question and status;
2. coverage strip;
3. up to five evidence findings;
4. repeated signals, when eligible;
5. limits and corpus date;
6. `Ask another question`, `Copy brief`, and source links.

## Claim Rules

An Evidence Brief **must**:

- make every claim traceable to at least one displayed evidence excerpt;
- identify the creator, date when available, Base2026 record, and original source;
- distinguish corpus coverage from industry coverage;
- show `limited` when only one eligible source or creator supports the answer;
- show `no_evidence` and the copy `Not enough public evidence in Base2026 for this question.` when there is no eligible finding;
- show a repeated signal only when the same canonical topic has eligible evidence from at least three distinct creators;
- disclose the corpus version and date range;
- preserve qualifications in the evidence rather than trimming them away.

An Evidence Brief **must not**:

- claim “the SEO industry says,” universal consensus, completeness, or real-time web coverage;
- turn practitioner statements into proven facts, causal claims, ranking guarantees, or personalized advice;
- infer disagreement from silence or label a winner;
- invent a bridge sentence, recommendation, statistic, quote, or source;
- imply creator endorsement, affiliation, or permission beyond the public source policy;
- expose raw captions, raw ASR, media, full private transcripts, prompts, provider output, private QA, or pipeline state;
- describe Cloudflare architecture as the primary user benefit;
- introduce pricing, a paid plan, lead capture, or a signup wall.

## Primary Conversion

Primary conversion: a user submits a suggested or custom professional question and receives `brief_rendered` with status `full` or `limited`.

No account, email, payment, or contact form is required. Opening an original source is the primary quality/verification action after conversion. Copy, share, refine, library browse, API docs, support, and partnership actions remain secondary.

## Future Events and Metrics

The local V1 candidate deliberately sends no product-analytics events and does not persist raw questions. The following is a future privacy-preserving measurement contract, not a release dependency for this minimal product slice.

Required events:

| Event | Fires when | Required properties |
| --- | --- | --- |
| `suggested_query_selected` | a suggestion is chosen | `suggested_query_id` |
| `brief_query_submitted` | a valid question is submitted | `input_mode`, `query_length_bucket`, `corpus_version`, `ranking_version` |
| `brief_rendered` | a `full` or `limited` brief is visible | `brief_status`, `source_count_bucket`, `creator_count_bucket`, `latency_ms` |
| `brief_no_evidence` | the no-evidence state is visible | `input_mode`, `query_length_bucket`, `corpus_version` |
| `brief_source_opened` | a Base2026 or original source link is opened | `destination_type`, `finding_position` |
| `brief_copied` | the brief is copied | `brief_status`, `source_count_bucket` |
| `brief_shared` | the share action is used | `brief_status`, `share_method` |
| `brief_refined` | the user changes and resubmits a question | `prior_brief_status`, `input_mode` |

Do not send raw question text, evidence excerpts, full URLs, creator handles, email, IP, user agent, client names, or other user-entered content to product analytics.

V1 metrics:

- **Successful brief rate:** `brief_rendered / brief_query_submitted`;
- **Zero-evidence rate:** `brief_no_evidence / brief_query_submitted`;
- **Source verification rate:** rendered-brief sessions with `brief_source_opened / brief_rendered`;
- **Reuse rate:** rendered-brief sessions with `brief_copied` or `brief_shared / brief_rendered`;
- **Refinement rate:** `brief_refined / brief_rendered`;
- **Latency:** median and P95 from submit to visible brief.

Set no numerical growth or latency target until a measured baseline exists. The phrase “in seconds” is a release gate: measure it before shipping the hero, and change the copy if the verified experience does not support it.

## Anti-Positioning

Base2026 is not:

- an AI chatbot or general answer engine;
- a generic SEO advice generator;
- a rank tracker, audit suite, CRM, lead database, or agency service;
- a transcript dump, bulk harvesting tool, or video re-host;
- an exhaustive survey or consensus oracle;
- a substitute for the original creator or source;
- a paid SaaS offer in V1.

## Public, Private, and Copyright Boundaries

Public briefs may use only publication-eligible creator attribution, public metadata, bounded evidence excerpts, reviewed public source text when policy allows, admitted Base2026 claims, public topics, canonical Base2026 URLs, and original-source links.

Raw captions, raw ASR, downloaded media, provider responses, prompts, private review packets, logs, credentials, private D1/R2 state, inbox submissions, client research, contact data, and user question text retained for analytics stay outside the public product.

The original creator remains the canonical source. Base2026 does not claim ownership, endorsement, or a blanket right to republish complete third-party works. Quotes/excerpts must stay bounded and contextual, paraphrases must remain attributable, and correction/removal/suppression paths must remain visible and effective. This product contract does not make a legal fair-use or licensing determination.

## Below-Fold Cloudflare Copy

Place this after the product demonstration or Evidence Brief example, never in the hero.

**Eyebrow**
`WHY THE CORE CAN STAY FREE`

**Heading**
`Bounded infrastructure, public evidence.`

**Body**
`Base2026 uses Cloudflare Workers and D1 to keep read-only retrieval fast and operating costs controlled. Private media, raw transcripts, and processing artifacts stay outside the public search surface; only publication-eligible evidence reaches a brief.`

## Release Acceptance

The Evidence Brief promise may ship only when:

- the deterministic fixture proves identical substantive output for identical inputs and versions;
- every displayed finding has both Base2026 and original-source links;
- limited and no-evidence states pass copy/claim review;
- no private or raw-transcript field appears in API, DOM, analytics, or logs intended for product measurement;
- all three suggested questions return an honest state against the release corpus;
- median/P95 latency is measured and the public speed claim is supportable;
- desktop/mobile, keyboard, public-boundary, and copyright/source-policy review pass.

## Known Risks

- The structured Evidence Brief API and homepage interaction exist only in the local candidate until an explicit public deploy is authorized and live-verified.
- Corpus coverage can make broad questions look more authoritative than the evidence supports; coverage and limits are mandatory.
- A changing live corpus can break determinism unless the response records a corpus watermark and ranking version.
- Final r4 remote-preview checks returned all three suggested V2 briefs in 237–268 ms on 2026-08-28; production latency must still be watched after release.
- Bounded excerpts, attribution, and correction/removal reduce risk but do not settle copyright questions.
- Storing raw professional questions can leak client or personal information; analytics must remain content-free.
