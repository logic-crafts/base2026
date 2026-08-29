# Base2026 public dataset quickstart

Base2026 publishes a free, read-only expert-video evidence layer. Use the
static JSONL files for reproducible offline analysis and the Cloudflare D1
search endpoint for current ranking and newly projected public evidence.

- Landing page: <https://base2026.dev/dataset>
- Data dictionary: <https://base2026.dev/data-dictionary.json>
- API index: <https://base2026.dev/api-index.json>
- Current public totals: <https://base2026.dev/api/stats>

## Search in one request

```bash
curl -sS -X POST https://base2026.dev/api/search/multi-search \
  -H 'content-type: application/json' \
  --data '{"queries":[{"indexUid":"base2026_public_tiktok","q":"AI search visibility","limit":5}]}'
```

Or run the standard-library Python example:

```bash
python3 examples/query_public_evidence.py "schema for AI search" --limit 5
```

## Public distributions

- `https://base2026.dev/static/documents.jsonl`
- `https://base2026.dev/static/passages.jsonl`
- `https://base2026.dev/static/insight_cards.jsonl`
- `https://base2026.dev/static/topic_signal_briefs.jsonl`

Retain the date and counts from `static/manifest.json` when citing a static
snapshot. The live D1 index can contain later public-safe projections, so its
current totals are intentionally reported separately by `/api/stats`.

## Citation and rights

Prefer a canonical Base2026 source, topic or creator page and keep the original
creator/source link attached. The repository code is Apache-2.0; that code
license does not transfer ownership of creator content. Source corrections and
removals follow the public [source policy](https://base2026.dev/source-policy)
and [creator-rights path](https://base2026.dev/opt-out).

Raw media, raw captions, raw ASR, full private transcripts, credentials, logs,
client data and private pipeline artifacts are not part of the public dataset.
