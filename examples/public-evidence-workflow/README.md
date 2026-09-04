# Base2026 public evidence workflow

This small, dependency-free example turns a bounded list of public Base2026
IDs into two local files: a deterministic Markdown evidence note for review
and a canonical JSON note for downstream tooling.

It uses the public stateless MCP endpoint and calls only the read-only
`get_source` tool. It first verifies the modern MCP contract, then fetches one
exact public response for each supplied `source_id`, `item_id`, `video_id`, or
`post_id`. It keeps the original source URL, any Base2026 source-page URL,
returned excerpts/cards, and explicit unknowns when a bounded response does
not return a field. It does not log in, send secrets, upload media, read the
private pipeline, or call a write operation.

The run is capped at eight unique IDs. Duplicate IDs collapse before fetching;
records and JSON keys are sorted so the same public responses produce the same
outputs regardless of command-line order. No retrieval timestamp is inserted,
so repeatability is testable without pretending that a note is a permanent
snapshot.

## Run it

From the repository root:

```bash
python3 examples/public-evidence-workflow/evidence_pack.py \
  tiktok:tjrobertson52:7617209892734078221 \
  tiktok:webhivedigital:7647894353934847254 \
  --output /tmp/base2026-evidence-note
```

The command makes at most nine bounded public requests (one discovery request
plus one `get_source` request per unique ID) and writes:

```text
/tmp/base2026-evidence-note.json
/tmp/base2026-evidence-note.md
```

For a longer set, use one ID per line. Blank lines and lines beginning with
`#` are ignored, and the same eight-ID cap applies:

```bash
python3 examples/public-evidence-workflow/evidence_pack.py \
  --ids-file /path/to/public-ids.txt \
  --output /tmp/base2026-evidence-note
```

The JSON file is the machine-readable record. The Markdown file is a stable
review view with source links, bounded excerpts, applied public cards, and an
`Unknowns` section per requested ID. A `not_found` result is retained as an
explicit record; it is not silently dropped. Missing excerpts/cards are
reported as fields not returned by this bounded response, not as proof that no
such material exists.

## Expected output shape

The JSON document has schema `base2026.public-evidence-pack.v1` and includes:

- the endpoint and MCP protocol/server details;
- the normalized requested IDs and found/not-found summary;
- each complete public `get_source` `structuredContent` payload under
  `public_record`;
- source links and returned public passages/cards without private fields;
- per-record and aggregate unknowns;
- the public boundary and fixed limitations.

The script fails closed if the response is not JSON-RPC 2.0, does not prove
`public_read_only`, advertises a different source schema, or contains a
forbidden private/media/credential field. It does not retry a rate-limit or
transport error, so a failed run cannot be mistaken for a complete note.

## Test the workflow

The tests use only synthetic public-safe fixtures and a fake HTTP response;
they make no network request:

```bash
python3 -m unittest discover \
  -s examples/public-evidence-workflow \
  -p 'test_*.py' \
  -v
```

The fixtures deliberately cover one found record with a source link and an
applied card, plus one not-found record. The test suite also checks the modern
MCP headers, deterministic ordering, explicit unknowns, the eight-ID bound,
and fail-closed private-field detection.

## Public context and limitations

This is a retrieval and citation aid, not a truth or consensus engine. Counts,
passages and cards are bounded public responses and can change after a new
release. Keep the creator/source link attached when reusing an excerpt; the
Apache-2.0 license covers repository code, not creator content or platform
rights.

For a human starting point, use the live [Base2026 Evidence Search tool](https://base2026.dev/tools/evidence-search/).
For the separate methodology caveat about independent voices, see the live
[Source Diversity Check](https://base2026.dev/tools/source-diversity-check/).

The current public developer contract is documented in
[`docs/public-pages/10_MCP_FOR_AI_AGENTS.md`](../../docs/public-pages/10_MCP_FOR_AI_AGENTS.md).
